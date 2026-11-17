"""Kiểm máy cho governance/LAWS.md — gọi từ tools/validate.py, có test riêng. Bảng luật ↔ máy kiểm: ADR-0003.
L-02  không khuyến nghị: reports/, media/, ledger/ không chứa từ khóa khuyến nghị mua bán (intake kiểm thêm lúc nhận).
L-03  dữ liệu cá nhân: tệp chữ (md/yaml/json/jsonl/txt) không chứa số định danh/số tài khoản đi kèm nhãn (CCCD, CMND,
      căn cước, hộ chiếu, số tài khoản, STK, account number). Không quét library/sources/ (tài liệu gốc công khai đã ghim,
      chép nguyên văn theo L-01/L-04).
L-05  Ledger: ledger/predictions.jsonl và ledger/resolutions.jsonl đúng hash chuỗi (prev_hash/hash, dòng đầu "GENESIS").
      Hash chuỗi KHÔNG phải chữ ký: nó bắt sửa nhầm/sửa một phần. Chống viết lại có chủ ý là việc của tools/ledger_audit.py
      (chỉ-ghi-thêm so với commit trước; đối chiếu từng dòng với Issue thật trên GitHub) và ruleset cấm force-push.
      Mọi dòng của hai sổ phải đến từ Issue: đường ghi dự báo của engine đang ĐÓNG (config.yaml ledger.engine_forecasts),
      nên dòng không có issue_number / resolution_issue là lỗi, bất kể mang mã gì (check_ledger_rows, check_engine_gate).
L-06  sổ thử: research/trial_registry.jsonl đúng hash chuỗi; mã thử không trùng; mọi lần thử trong research/trials.csv từ
      mã thử đầu tiên của sổ trở đi có dòng đăng ký cùng trial_id, spec_id, ngưỡng, registry_hash; số dòng đăng ký ≥ số
      lần thử; feature/mô hình đăng ký nằm trong không gian giả thuyết đóng băng (config.yaml research.frozen_space).
      research/trials.csv đúng KHUÔN: tiêu đề là đúng 13 cột gốc hoặc đúng 17 cột (13 + 4 cột v3.0.2), mỗi dòng đủ số ô,
      viết đúng dạng chuẩn từng byte (trials_format_errors) — không cột lạ, không đổi thứ tự, không dòng lệch.
L-07  một kiến trúc: mỗi ARCHITECTURE_v*.md phải có dòng riêng trong architecture/ARCHIVE.md ghi SUPERSEDED.
L-09  người viết ≠ người chấm: thân PR (bỏ chú thích HTML) có đúng một dòng "authored_by:" và một dòng "reviewed_by:"; cả hai
      bắt đầu bằng tên ghế (Owner hoặc mô hình/nhà cung cấp); không chung ghế — cùng nhà cung cấp, hoặc cùng là Owner; và
      PR có bình luận của chủ kho mở đầu "GỘP ĐƯỢC" kèm 7 ký tự đầu SHA của commit đang chấm (bản chấm nằm trên kho,
      đổi mã thì phải chấm lại). recognised_seat()/same_provider() dùng chung cho người phân định và biên bản ghi chú.
L-10  đề thi: tệp trong academy/exams/ khớp exam_item.schema.json và released_at không ở tương lai (đề chỉ vào kho sau khi thi).
"""
import csv, io, hashlib, json, pathlib, re, unicodedata
from datetime import date, timedelta

RECOMMEND_PATTERNS = [r"mua ngay", r"n[êe]n mua", r"b[áa]n ngay", r"n[êe]n b[áa]n", r"gi[áa] m[ụu]c ti[êe]u",
                      r"target price", r"khuy[ếe]n ngh[ịi] mua", r"khuy[ếe]n ngh[ịi] b[áa]n", r"\bBUY\b", r"\bSELL\b"]
_RE = re.compile("|".join(RECOMMEND_PATTERNS), re.IGNORECASE)
SCAN_DIRS = ("reports", "media", "ledger")
SCAN_EXT = {".md", ".txt", ".jsonl", ".json", ".yaml", ".yml", ".csv"}
# Dấu nhận của robot phải được đăng trong khoảng này sau giờ tạo Issue. Một định nghĩa cho cả bên ghi (intake không ghi
# khi đã sát hạn) lẫn bên kiểm (tools/ledger_audit.py).
ATTEST_WINDOW = timedelta(hours=6)


def nfc(text) -> str:
    """Chuẩn hóa Unicode dựng sẵn (NFC). Chữ Việt dán từ nguồn khác nhau có thể ở dạng tổ hợp (NFD): 'nên' gõ kiểu NFD
    sẽ lọt mọi mẫu so chuỗi nếu không chuẩn hóa trước."""
    return unicodedata.normalize("NFC", text or "")


def recommendation_hit(text: str):
    """Trả về cụm từ khóa khuyến nghị đầu tiên tìm thấy (L-02), hoặc None."""
    m = _RE.search(nfc(text))
    return m.group(0) if m else None


def line_hash(payload: dict) -> str:
    """sha256 của dòng Ledger không kể trường 'hash' — ổn định theo khóa sắp xếp."""
    body = {k: v for k, v in payload.items() if k != "hash"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


PII_RE = re.compile(r"(CCCD|CMND|c[ăa]n c[ưu][ớo]c|h[ộo] chi[ếe]u|s[ốo] t[àa]i kho[ảa]n|\bSTK\b|account number|passport)"
                    r"[^\n0-9]{0,25}[0-9][0-9 .-]{5,}[0-9]", re.IGNORECASE)
PII_SKIP_DIRS = {".git", "node_modules", "__pycache__"}      # quét mọi thư mục; chỉ bỏ qua theo đuôi tệp (PII_EXT)
PII_EXT = {".md", ".txt", ".yaml", ".yml", ".json", ".jsonl"}


def check_personal_data(root) -> list[str]:
    root = pathlib.Path(root)
    errs = []
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root)
        if not p.is_file() or p.suffix.lower() not in PII_EXT or PII_SKIP_DIRS & set(rel.parts):
            continue
        if rel.parts[:2] == ("library", "sources"):       # tài liệu gốc công khai đã ghim, chép nguyên văn (L-01, L-04)
            continue
        try:
            text = nfc(p.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, OSError):
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if PII_RE.search(line):
                errs.append(f"L-03: {p.relative_to(root)}:{i} có số định danh/số tài khoản — không commit dữ liệu cá nhân")
                break
    return errs


def check_one_architecture(root) -> list[str]:
    root = pathlib.Path(root)
    errs = []
    arch_dir = root / "architecture"
    if not (arch_dir / "ARCHITECTURE.md").is_file():
        return errs                      # chưa hợp nhất: không áp L-07
    archive = (arch_dir / "ARCHIVE.md").read_text(encoding="utf-8") if (arch_dir / "ARCHIVE.md").is_file() else ""
    lines = archive.splitlines()
    for p in sorted(arch_dir.glob("ARCHITECTURE_v*.md")):
        if not any(p.name in ln and "SUPERSEDED" in ln for ln in lines):      # cùng MỘT dòng, không phải đâu đó trong tệp
            errs.append(f"L-07: {p.relative_to(root)} không có dòng riêng ghi SUPERSEDED trong architecture/ARCHIVE.md")
    return errs


def check_no_recommendation(root) -> list[str]:
    root = pathlib.Path(root)
    errs = []
    for d in SCAN_DIRS:
        base = root / d
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*")):
            if not p.is_file() or p.suffix.lower() not in SCAN_EXT:
                continue
            try:
                text = nfc(p.read_text(encoding="utf-8", errors="ignore"))
            except OSError:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                m = _RE.search(line)
                if m:
                    errs.append(f"L-02: {p.relative_to(root)}:{i} chứa từ khóa khuyến nghị '{m.group(0)}'")
                    break
    return errs


def _no_constant(name):
    raise ValueError(name)


def _chain_errors(path, label) -> list[str]:
    errs, prev = [], "GENESIS"
    for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            row = json.loads(raw, parse_constant=_no_constant)      # NaN/Infinity không phải JSON chuẩn
            if not isinstance(row, dict):
                raise ValueError("không phải object")
        except ValueError:
            errs.append(f"{label}: dòng {n} không phải JSON chuẩn (hoặc chứa NaN/Infinity)"); break
        if row.get("prev_hash") != prev:
            errs.append(f"{label}: dòng {n} prev_hash không khớp dòng trước"); break
        if row.get("hash") != line_hash(row):
            errs.append(f"{label}: dòng {n} hash không khớp nội dung"); break
        prev = row["hash"]
    return errs


def check_ledger_chain(root) -> list[str]:
    errs = []
    for name, label in (("predictions.jsonl", "Ledger"), ("resolutions.jsonl", "Ledger phân định")):
        path = pathlib.Path(root) / "ledger" / name
        if path.is_file():
            errs += _chain_errors(path, label)
    return errs


def check_ledger_rows(root) -> list[str]:
    """L-05: chạy LẠI luật nhận dự báo và luật phân định trên MỌI dòng của sổ (tools/ledger_intake.ledger_errors =
    ledger_intake.replay + resolution_intake.replay). Không loại dòng nào được miễn: đường ghi dự báo của engine đang đóng
    nên dòng thiếu issue_number hay thiếu resolution_issue là lỗi, bất kể mang mã "P-…" hay có đủ trường. Hash chuỗi chỉ
    cho biết sổ nhất quán; kiểm này cho biết từng dòng đúng luật, kể cả dòng được ghi vòng qua intake. Hai robot nhận gọi
    đúng hàm này trên trạng thái SAU KHI GHI trước khi đẩy (không ghi thứ mà kiểm lại sẽ đánh đỏ). Việc dòng có ĐÚNG LÚC
    hay không do tools/ledger_audit.py đối chiếu với GitHub."""
    root = pathlib.Path(root)
    pred_p, res_p = root / "ledger" / "predictions.jsonl", root / "ledger" / "resolutions.jsonl"
    def rows(path):
        out = []
        for raw in (path.read_text(encoding="utf-8").splitlines() if path.is_file() else []):
            if raw.strip():
                try:
                    r = json.loads(raw, parse_constant=_no_constant)
                except ValueError:
                    return None                                  # check_ledger_chain đã báo dòng hỏng
                if isinstance(r, dict):
                    out.append(r)
        return out
    pred, res = rows(pred_p), rows(res_p)
    if pred is None or res is None:
        return []
    if not pred and not res:
        return []
    try:
        import jsonschema  # noqa: F401
    except ImportError:
        return ["L-05: thiếu thư viện jsonschema nên không kiểm lại được các dòng trong sổ (pip install jsonschema)"]
    try:
        from tools import ledger_intake                         # nạp muộn: mô-đun này nhập lại laws_checks
        return ledger_intake.ledger_errors(pred, res)
    except Exception as e:  # noqa: BLE001
        return [f"L-05: không chạy lại được luật nhận trên sổ ({str(e).splitlines()[0]})"]


def _config(root):
    """config.yaml của kho → dict; {} nếu không có tệp; None nếu có tệp mà không đọc được."""
    p = pathlib.Path(root) / "config.yaml"
    if not p.is_file():
        return {}
    try:
        import yaml
        cfg = yaml.safe_load(p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None
    return cfg if isinstance(cfg, dict) else None


ENGINE_GATE_CLOSED = "closed"


def check_engine_gate(root) -> list[str]:
    """L-05 (ADR-0003 quyết định 11): đường ghi dự báo của engine (chuyên gia LLM) ĐÓNG. Dòng engine không có Issue, không
    có dấu nhận, không có bằng chứng nào ngoài tệp về việc AI ghi và ghi LÚC NÀO — nên khi chưa có cơ chế xuất xứ thì sổ
    không nhận dòng nào như thế. Bản này chỉ chấp nhận ledger.engine_forecasts = closed (hoặc không khai = đóng). Mở lại
    phải qua ADR mới kèm cơ chế xuất xứ và sửa chính hàm này — đổi một chữ trong config.yaml không mở được."""
    cfg = _config(root)
    if cfg is None:
        return ["L-05: không đọc được config.yaml nên không xác định được trạng thái đường ghi dự báo của engine"]
    led = cfg.get("ledger")
    val = led.get("engine_forecasts") if isinstance(led, dict) else None
    if val is None or val == ENGINE_GATE_CLOSED:
        return []
    return [f"L-05: config.yaml ledger.engine_forecasts = {val!r} — bản này chỉ chấp nhận '{ENGINE_GATE_CLOSED}': dòng dự báo của "
            "engine chưa có cơ chế bằng chứng xuất xứ (ai ghi, lúc nào); mở lại phải qua ADR mới (ADR-0003 quyết định 11)"]


def _frozen_space(root):
    """research.frozen_space trong config.yaml: {features: [...], models: [...]}; None nếu chưa khai."""
    cfg = _config(root)
    if not cfg:
        return None
    fs = (cfg.get("research") or {}).get("frozen_space")
    return {"features": set(fs.get("features") or []), "models": set(fs.get("models") or [])} if fs else None


def _legacy_pin(root):
    """research.legacy_pin trong config.yaml: {results, last_trial_id, sha256}; None nếu chưa khai."""
    cfg = _config(root)
    if not cfg:
        return None
    pin = (cfg.get("research") or {}).get("legacy_pin")
    return pin if isinstance(pin, dict) else None


def _pin_errors(pin, trials) -> list[str]:
    if not pin:
        return []
    n = pin.get("results")
    if isinstance(n, bool) or not isinstance(n, int) or n < 0:
        return ["L-06: research.legacy_pin.results trong config.yaml không hợp lệ"]
    if len(trials) < n:
        return [f"L-06: trials.csv có {len(trials)} kết quả, ít hơn {n} kết quả đã ghim trong config.yaml — kết quả cũ bị xóa"]
    if trials_digest(trials[:n]) != pin.get("sha256") or (n and trials[n - 1].get("trial_id") != pin.get("last_trial_id")):
        return [f"L-06: {n} kết quả thử đầu tiên của trials.csv không khớp sha256 đã ghim trong config.yaml (research.legacy_pin) — "
                "kết quả lịch sử bị sửa, xóa hoặc chèn"]
    return []


TRIAL_LEGACY_COLS = ("trial_id", "cycle_date", "method", "spec_id", "features", "model", "ic_mean", "ic_t", "net_ann",
                     "fold_pos", "threshold", "status", "regimes")
TRIAL_NEW_COLS = ("sharpe", "sharpe_ann", "dsr", "registry_hash")     # thêm từ v3.0.2, đứng sau 13 cột gốc
TRIAL_HEADERS = (list(TRIAL_LEGACY_COLS), list(TRIAL_LEGACY_COLS) + list(TRIAL_NEW_COLS))   # hai tiêu đề hợp lệ, không có thứ ba
LEGACY_ANCHOR = "LEGACY-ANCHOR"


def trials_format_errors(text) -> list[str]:
    """L-06: KHUÔN của research/trials.csv. Tệp này chỉ do vòng học ghi thêm ở mức văn bản (engine/research.
    append_trial_results); bất kỳ kiểu viết nào khác — dù đọc ra cùng giá trị ô — đều có thể làm lần ghi kế tiếp hỏng
    hoặc làm lệch nghĩa các cột, nên bị từ chối:
    - tiêu đề phải là ĐÚNG 13 cột gốc hoặc ĐÚNG 17 cột (13 + sharpe, sharpe_ann, dsr, registry_hash), đúng thứ tự;
    - mỗi dòng có đúng số ô của tiêu đề; không dòng trống; không ô nào chứa xuống dòng;
    - từng byte của tệp trùng dạng chuẩn do csv.writer viết ra (xuống dòng LF, chỉ đặt ngoặc kép khi cần, không BOM,
      không ký tự CR, có xuống dòng cuối tệp)."""
    if not text:
        return []
    try:
        rows = list(csv.reader(io.StringIO(text, newline="")))
    except csv.Error as e:
        return [f"L-06: research/trials.csv không đọc được như CSV ({e})"]
    if not rows or rows[0] not in TRIAL_HEADERS:
        return ["L-06: tiêu đề research/trials.csv phải là đúng 13 cột gốc hoặc đúng 17 cột (13 cột gốc + sharpe, sharpe_ann, "
                "dsr, registry_hash), đúng thứ tự — không thêm, bớt, đổi tên hay đổi chỗ cột"]
    n = len(rows[0])
    for i, r in enumerate(rows[1:], 2):
        if len(r) != n:
            return [f"L-06: research/trials.csv dòng {i} có {len(r)} ô, tiêu đề có {n} cột — mỗi kết quả phải đủ đúng số ô"]
        if any("\n" in c or "\r" in c for c in r):
            return [f"L-06: research/trials.csv dòng {i} có ô chứa ký tự xuống dòng"]
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerows(rows)
    if buf.getvalue() != text:
        return ["L-06: research/trials.csv không ở dạng chuẩn từng byte (xuống dòng \\n, không BOM, không \\r, ngoặc kép chỉ khi "
                "cần, có xuống dòng cuối tệp) — tệp chỉ do vòng học ghi thêm, không sửa tay hay ghi lại bằng công cụ khác"]
    return []


def read_trials(text):
    """Đọc research/trials.csv (chuỗi) → (tiêu đề, danh sách dict theo cột). Giữ nguyên chuỗi từng ô, không đổi kiểu."""
    rows = list(csv.reader(io.StringIO(text or "")))
    if not rows:
        return [], []
    head = rows[0]
    return head, [dict(zip(head, r)) for r in rows[1:] if r]


def trials_digest(rows) -> str:
    """sha256 của các kết quả thử theo đúng chuỗi từng ô (13 cột gốc). Engine chỉ GHI THÊM dòng vào trials.csv và không
    viết lại dòng cũ (research.append_trial_results), nên chuỗi ô cũ không bao giờ đổi."""
    h = hashlib.sha256()
    for r in rows:
        h.update("\x1f".join(str(r.get(c, "")) for c in TRIAL_LEGACY_COLS).encode("utf-8") + b"\n")
    return h.hexdigest()


def check_trial_registry(root) -> list[str]:
    """L-06. Sổ đăng ký mở đầu bằng một DÒNG NEO LỊCH SỬ (engine ghi lúc tạo sổ): số kết quả đã có trước khi có sổ và
    sha256 của chúng. Thêm một GHIM TĨNH trong config.yaml (research.legacy_pin) cho 210 kết quả đầu, có hiệu lực ngay cả
    khi chưa có sổ. Từ đó: (a) các kết quả lịch sử bị sửa, xóa, chèn → lỗi; (b) MỌI kết quả sau dòng neo phải có dòng
    đăng ký khớp mã, spec, ngưỡng và hash — không còn ngoại lệ "registry_hash rỗng"; (c) mã thử trong sổ không trùng,
    tăng dần, nằm sau mã lịch sử cuối. Khi chưa có sổ, kết quả không được mang registry_hash; việc THÊM kết quả khi chưa
    có sổ do tools/ledger_audit.py chặn (so với commit gốc)."""
    root = pathlib.Path(root)
    reg_path, trials_path = root / "research" / "trial_registry.jsonl", root / "research" / "trials.csv"
    try:
        trials_text = trials_path.read_bytes().decode("utf-8") if trials_path.is_file() else ""
    except UnicodeDecodeError:
        return ["L-06: research/trials.csv không phải UTF-8"]
    fmt = trials_format_errors(trials_text)
    if fmt:
        return fmt                                      # khuôn sai thì tên cột không còn tin được: dừng ở đây, đã là lỗi
    _, trials = read_trials(trials_text)
    reg_text = reg_path.read_text(encoding="utf-8") if reg_path.is_file() else ""
    pin = _legacy_pin(root)
    pin_errs = _pin_errors(pin, trials)                 # ghim tĩnh trong config.yaml: có hiệu lực cả khi chưa có sổ đăng ký
    def filled(rows):
        """Kết quả LỊCH SỬ (có trước sổ đăng ký) không có 4 cột mới: ô nào ở đó khác rỗng là số liệu chèn về sau —
        cột sharpe của các lần thử cũ đi vào phương sai Sharpe của Deflated Sharpe cho mọi lần thử mới."""
        bad = [t.get("trial_id") for t in rows if any((t.get(c) or "") != "" for c in TRIAL_NEW_COLS)]
        return ([f"L-06: {len(bad)} kết quả lịch sử trong trials.csv (từ {bad[0]}) có giá trị ở cột sharpe/sharpe_ann/dsr/"
                 "registry_hash — kết quả có trước sổ đăng ký phải để trống bốn cột đó"] if bad else [])
    if not reg_text.strip():
        return pin_errs + filled(trials)                # chưa có sổ: mọi kết quả đang có đều là lịch sử
    errs = pin_errs + _chain_errors(reg_path, "L-06 sổ đăng ký")
    if errs:
        return errs
    reg = [json.loads(l) for l in reg_text.splitlines() if l.strip()]
    anchor = reg[0]
    if anchor.get("kind") != "legacy_anchor" or anchor.get("trial_id") != LEGACY_ANCHOR:
        return ["L-06: sổ đăng ký phải mở đầu bằng dòng neo lịch sử (kind=legacy_anchor) do engine ghi lúc tạo sổ"]
    n = anchor.get("results")
    if isinstance(n, bool) or not isinstance(n, int) or n < 0:
        return ["L-06: dòng neo lịch sử ghi số kết quả không hợp lệ"]
    if pin and isinstance(pin.get("results"), int) and n < pin["results"]:
        return [f"L-06: dòng neo lịch sử khai {n} kết quả, ít hơn {pin['results']} kết quả đã ghim trong config.yaml"]
    if len(trials) < n:
        errs.append(f"L-06: trials.csv có {len(trials)} kết quả, ít hơn {n} kết quả lịch sử đã neo — kết quả cũ bị xóa")
    elif trials_digest(trials[:n]) != anchor.get("legacy_sha256"):
        errs.append(f"L-06: {n} kết quả lịch sử trong trials.csv không khớp sha256 đã neo — kết quả cũ bị sửa, xóa hoặc chèn")
    errs += filled(trials[:n])
    regs = reg[1:]
    for r in regs:
        if r.get("kind") == "legacy_anchor" or r.get("trial_id") == LEGACY_ANCHOR:
            errs.append("L-06: sổ đăng ký có hơn một dòng neo lịch sử")
    regs = [r for r in regs if r.get("kind") != "legacy_anchor"]
    ids = [str(r.get("trial_id")) for r in regs]
    for d in sorted({i for i in ids if ids.count(i) > 1}):
        errs.append(f"L-06: sổ đăng ký có mã thử trùng {d}")
    last_legacy = str(anchor.get("last_trial_id") or "")
    prev = last_legacy
    for i in ids:
        if not re.fullmatch(r"T[0-9]{5,}", i) or i <= prev:
            errs.append(f"L-06: mã thử {i} trong sổ đăng ký không tăng dần sau {prev or 'đầu sổ'}"); break
        prev = i
    frozen = _frozen_space(root)
    if frozen:
        for r in regs:
            extra = [f for f in str(r.get("features", "")).split(";") if f and f not in frozen["features"]]
            if extra or r.get("model") not in frozen["models"]:
                errs.append(f"L-06: {r.get('trial_id')} nằm ngoài không gian giả thuyết đóng băng "
                            f"(feature lạ {extra}, mô hình {r.get('model')}) — giả thuyết mới phải qua ADR")
    by_id = {r.get("trial_id"): r for r in regs}
    new = trials[n:]
    tids = [t.get("trial_id") for t in new]
    for d in sorted({i for i in tids if tids.count(i) > 1}):
        errs.append(f"L-06: trials.csv có hai kết quả cho cùng mã thử {d}")
    for t in new:
        r = by_id.get(t.get("trial_id"))
        if r is None:
            errs.append(f"L-06: {t.get('trial_id')} ({t.get('cycle_date')}) có kết quả nhưng không có dòng đăng ký trước"); continue
        if r.get("spec_id") != t.get("spec_id"):
            errs.append(f"L-06: {t['trial_id']} spec_id lệch sổ đăng ký")
        try:
            if abs(float(r.get("threshold")) - float(t.get("threshold"))) > 1e-9:
                errs.append(f"L-06: {t['trial_id']} ngưỡng lệch sổ đăng ký")
        except (TypeError, ValueError):
            errs.append(f"L-06: {t['trial_id']} ngưỡng không đọc được")
        if (t.get("registry_hash") or "") != r.get("hash"):
            errs.append(f"L-06: {t['trial_id']} registry_hash không khớp dòng đăng ký")
    return errs


PROVIDERS = {"anthropic": ("claude", "anthropic", "opus", "sonnet", "haiku", "fable", "mythos"),
             "openai": ("chatgpt", "openai", "gpt", "codex", "o1", "o3", "o4", "copilot", "minh tri", "minh trí"),
             "xai": ("grok", "xai"), "google": ("gemini", "google", "bard", "notebooklm"),
             "meta": ("llama", "meta ai"), "deepseek": ("deepseek",), "mistral": ("mistral",),
             "perplexity": ("perplexity",), "alibaba": ("qwen",), "moonshot": ("kimi",)}
_PROVIDER_RE = {k: re.compile(r"(?<![a-z0-9])(" + "|".join(re.escape(x) for x in keys) + r")(?![a-z0-9])")
                for k, keys in PROVIDERS.items()}


def _providers(text: str) -> set:
    """Nhà cung cấp mô hình được nhắc tới trong một chuỗi tên ghế (so khớp theo từ, không theo chuỗi con)."""
    t = nfc(text).lower()
    return {k for k, rx in _PROVIDER_RE.items() if rx.search(t)}


_OWNER_LOOSE_RE = re.compile(r"(?<![a-z0-9])owner(?![a-z0-9])")      # dò lỏng ở mọi vị trí, như _providers (chiều chặn)


def _seats(text: str) -> set:
    """Các ghế được nhắc tới: nhà cung cấp mô hình + ghế người "owner". Owner là MỘT ghế: 'Owner', 'Owner (tên)',
    'Owner — vòng 3' đều là cùng một ghế."""
    t = nfc(text).lower()
    return _providers(t) | ({"owner"} if _OWNER_LOOSE_RE.search(t) else set())


def same_provider(a: str, b: str) -> bool:
    """L-09: hai chuỗi cùng tên, hoặc có chung một ghế (cùng nhà cung cấp mô hình, hoặc cùng là Owner)."""
    if (a or "").strip().lower() == (b or "").strip().lower():
        return True
    return bool(_seats(a) & _seats(b))


# Nhận ghế chấm hợp lệ: chuỗi phải BẮT ĐẦU bằng "owner" hoặc một tên trong PROVIDERS, và ngay sau đó không được là
# ký tự chữ/số/gạch dưới (mọi bảng chữ, vì \w là Unicode); riêng "owner" còn không được nối bằng gạch ngang.
# Neo đầu chuỗi nên "not_an_owner", "éowner", "an owner", "not_a_grok" đều không được nhận.
# (Chặn cùng nhà cung cấp thì ngược lại: _providers() dò lỏng ở mọi vị trí để không lọt.)
_REVIEWER_START_RE = re.compile(
    r"^(?:owner(?![\w-])|(?:" + "|".join(re.escape(x) for x in sorted({k for ks in PROVIDERS.values() for k in ks},
                                                                    key=len, reverse=True)) + r")(?!\w))")


def recognised_seat(text: str) -> bool:
    """Chuỗi BẮT ĐẦU bằng tên ghế: 'Owner' hoặc tên mô hình/nhà cung cấp trong PROVIDERS. Dùng chung cho mọi chỗ L-09
    cần biết AI là ai (người viết, người chấm PR, người phân định dự báo, người đọc và người chấm ghi chú): ghế không
    nhận ra được thì không so được nhà cung cấp, nên không được chấp nhận."""
    return bool(_REVIEWER_START_RE.match(nfc(text).strip().lower()))


def check_pr_review(body: str) -> list[str]:
    """L-09 cho một PR: đọc hai dòng 'authored_by:' và 'reviewed_by:' trong thân PR."""
    fields, seen = {}, {}
    body = re.sub(r"<!--.*?-->", "", nfc(body), flags=re.S)       # chú thích của mẫu PR không phải nội dung
    for line in body.splitlines():
        m = re.match(r"^\s*[-*]?\s*(authored_by|reviewed_by)\s*:\s*(.*?)\s*$", line, re.IGNORECASE)
        if m:
            k = m.group(1).lower()
            seen[k] = seen.get(k, 0) + 1
            fields[k] = m.group(2).strip().strip("`")
    dup = [k for k, n in seen.items() if n > 1]
    if dup:
        return [f"L-09: thân PR có nhiều hơn một dòng {dup} — mỗi trường chỉ được một dòng"]
    a, r = fields.get("authored_by", ""), fields.get("reviewed_by", "")
    if not a:
        return ["L-09: thân PR thiếu dòng 'authored_by: <ghế/mô hình>'"]
    if not recognised_seat(a):
        return [f"L-09: authored_by '{a}' phải BẮT ĐẦU bằng tên ghế viết: 'Owner', hoặc tên mô hình/nhà cung cấp "
                "(ví dụ 'Claude (Anthropic)', 'ChatGPT (OpenAI)') — không nhận ra ghế viết thì không so được với ghế chấm"]
    if not r:
        return ["L-09: chưa có người chấm — điền 'reviewed_by: <ghế khác nhà cung cấp>' sau khi chấm xong"]
    if same_provider(a, r):
        return [f"L-09: người viết và người chấm cùng ghế (cùng nhà cung cấp, hoặc cùng là Owner): '{a}' / '{r}'"]
    if not recognised_seat(r):
        return [f"L-09: reviewed_by '{r}' phải BẮT ĐẦU bằng tên ghế chấm: 'Owner', hoặc tên mô hình/nhà cung cấp "
                "(ví dụ 'ChatGPT (OpenAI)', 'Grok (xAI)', 'Gemini (Google)')"]
    return []


VERDICT_OK = "GỘP ĐƯỢC"
_VERDICT_LINE_RE = re.compile(r"GỘP ĐƯỢC\s*[—–:-]?\s*(?:commit\s+)?([0-9a-f]{7,40})\.?", re.I)


def check_review_evidence(comments, head_sha: str, owner_login: str) -> list[str]:
    """L-09 + GitHub-first: bản chấm phải nằm trên kho. Cần ít nhất một bình luận PR do chủ kho đăng mà DÒNG ĐẦU (không rỗng)
    là đúng "GỘP ĐƯỢC — commit <SHA>" và không có chữ nào khác, với SHA (7–40 ký tự) là đầu SHA của commit đang đứng đầu PR.
    Dòng đầu kiểu "GỘP ĐƯỢC nếu sửa…", hay SHA chỉ xuất hiện ở đoạn dưới, không được tính. Đẩy commit mới → phải chấm lại.
    comments: danh sách {"user": login, "body": str}."""
    head = (head_sha or "").lower()
    if len(head) < 7:
        return ["L-09: không xác định được SHA đầu PR để đối chiếu bản chấm"]
    for c in comments or []:
        if (c.get("user") or "").lower() != (owner_login or "").lower():
            continue
        body = re.sub(r"<!--.*?-->", "", nfc(c.get("body")), flags=re.S)
        first = next((ln for ln in body.splitlines() if ln.strip()), "")
        first = re.sub(r"[*_#>`]", "", first).strip()                       # bỏ ký hiệu markdown (đậm, tiêu đề, trích)
        m = _VERDICT_LINE_RE.fullmatch(first)
        if m and head.startswith(m.group(1).lower()):
            return []
    return [f"L-09: chưa có bình luận của chủ kho dán bản chấm có dòng đầu đúng dạng '{VERDICT_OK} — commit {head[:7]}' "
            "(SHA của commit đang chấm; đổi mã thì phải chấm lại bản mới)"]


def check_exams(root, today=None) -> list[str]:
    """L-10: đề thi giữ ngoài kho tới khi thi. Tệp trong academy/exams/ phải khớp exam_item.schema.json và
    released_at không ở tương lai."""
    root = pathlib.Path(root)
    today = today or date.today()
    d = root / "academy" / "exams"
    if not d.is_dir():
        return []
    errs = []
    try:
        import jsonschema
        schema = json.loads((root / "contracts" / "exam_item.schema.json").read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        jsonschema = schema = None
    if jsonschema is None and any(d.rglob("*.json")):
        return ["L-10: thiếu jsonschema hoặc exam_item.schema.json nên không kiểm được đề thi trong kho"]
    for p in sorted(d.rglob("*.json")):
        rel = p.relative_to(root).as_posix()
        try:
            item = json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            errs.append(f"L-10: {rel} không phải JSON"); continue
        if jsonschema is not None:
            try:
                jsonschema.validate(item, schema)
            except Exception as e:  # noqa: BLE001
                errs.append(f"L-10: {rel} không khớp exam_item.schema.json — {str(e).splitlines()[0]}"); continue
        if item.get("released_at") in (None, ""):
            errs.append(f"L-10: {rel} chưa có released_at — đề chưa phát hành không được nằm trong kho"); continue
        try:
            rel_at = date.fromisoformat(str(item.get("released_at"))[:10])
        except ValueError:
            errs.append(f"L-10: {rel} released_at không phải ngày YYYY-MM-DD"); continue
        if rel_at > today:
            errs.append(f"L-10: {rel} có released_at {rel_at} ở tương lai — đề chưa thi không được nằm trong kho")
    return errs


def run_all(root) -> list[str]:
    return (check_one_architecture(root) + check_no_recommendation(root) + check_ledger_chain(root) + check_ledger_rows(root)
            + check_engine_gate(root) + check_trial_registry(root) + check_personal_data(root) + check_exams(root))
