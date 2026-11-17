"""Kiểm máy cho governance/LAWS.md — gọi từ tools/validate.py, có test riêng. Bảng luật ↔ máy kiểm: ADR-0003.
L-02  không khuyến nghị: reports/, media/, ledger/ không chứa từ khóa khuyến nghị mua bán (intake kiểm thêm lúc nhận).
L-03  dữ liệu cá nhân: tệp chữ (md/yaml/json/jsonl/txt) không chứa số định danh/số tài khoản đi kèm nhãn (CCCD, CMND,
      căn cước, hộ chiếu, số tài khoản, STK, account number). Không quét library/sources/ (tài liệu gốc công khai đã ghim,
      chép nguyên văn theo L-01/L-04).
L-05  Ledger: ledger/predictions.jsonl và ledger/resolutions.jsonl đúng hash chuỗi (prev_hash/hash, dòng đầu "GENESIS").
      Hash chuỗi KHÔNG phải chữ ký: nó bắt sửa nhầm/sửa một phần. Chống viết lại có chủ ý là việc của tools/ledger_audit.py
      (chỉ-ghi-thêm so với commit trước; đối chiếu từng dòng với Issue thật trên GitHub) và ruleset cấm force-push.
L-06  sổ thử: research/trial_registry.jsonl đúng hash chuỗi; mã thử không trùng; mọi lần thử trong research/trials.csv từ
      mã thử đầu tiên của sổ trở đi có dòng đăng ký cùng trial_id, spec_id, ngưỡng, registry_hash; số dòng đăng ký ≥ số
      lần thử; feature/mô hình đăng ký nằm trong không gian giả thuyết đóng băng (config.yaml research.frozen_space).
L-07  một kiến trúc: mỗi ARCHITECTURE_v*.md phải có dòng riêng trong architecture/ARCHIVE.md ghi SUPERSEDED.
L-09  người viết ≠ người chấm: thân PR (bỏ chú thích HTML) có đúng một dòng "authored_by:" và một dòng "reviewed_by:"; cả hai
      bắt đầu bằng tên ghế (Owner hoặc mô hình/nhà cung cấp); không chung ghế — cùng nhà cung cấp, hoặc cùng là Owner; và
      PR có bình luận của chủ kho mở đầu "GỘP ĐƯỢC" kèm 7 ký tự đầu SHA của commit đang chấm (bản chấm nằm trên kho,
      đổi mã thì phải chấm lại). recognised_seat()/same_provider() dùng chung cho người phân định và biên bản ghi chú.
L-10  đề thi: tệp trong academy/exams/ khớp exam_item.schema.json và released_at không ở tương lai (đề chỉ vào kho sau khi thi).
"""
import csv, hashlib, json, pathlib, re, unicodedata
from datetime import date

RECOMMEND_PATTERNS = [r"mua ngay", r"n[êe]n mua", r"b[áa]n ngay", r"n[êe]n b[áa]n", r"gi[áa] m[ụu]c ti[êe]u",
                      r"target price", r"khuy[ếe]n ngh[ịi] mua", r"khuy[ếe]n ngh[ịi] b[áa]n", r"\bBUY\b", r"\bSELL\b"]
_RE = re.compile("|".join(RECOMMEND_PATTERNS), re.IGNORECASE)
SCAN_DIRS = ("reports", "media", "ledger")
SCAN_EXT = {".md", ".txt", ".jsonl", ".json", ".yaml", ".yml", ".csv"}


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
    """L-05: chạy LẠI luật nhận dự báo và luật phân định trên mọi dòng Issue đã có trong sổ (tools/ledger_intake.replay,
    tools/resolution_intake.replay). Hash chuỗi chỉ cho biết sổ nhất quán; kiểm này cho biết từng dòng đúng luật, kể cả
    dòng được ghi vòng qua intake. Việc dòng có ĐÚNG LÚC hay không do tools/ledger_audit.py đối chiếu với GitHub."""
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
    if not any("issue_number" in r for r in pred) and not any(r.get("resolution_issue") is not None for r in res):
        return []
    try:
        import jsonschema  # noqa: F401
    except ImportError:
        return ["L-05: thiếu thư viện jsonschema nên không kiểm lại được các dòng Issue trong sổ (pip install jsonschema)"]
    try:
        from tools import ledger_intake, resolution_intake      # nạp muộn: hai mô-đun này nhập lại laws_checks
        return ledger_intake.replay(pred, res) + resolution_intake.replay(pred, res)
    except Exception as e:  # noqa: BLE001
        return [f"L-05: không chạy lại được luật nhận trên sổ ({str(e).splitlines()[0]})"]


def _frozen_space(root):
    """research.frozen_space trong config.yaml: {features: [...], models: [...]}; None nếu chưa khai."""
    try:
        import yaml
        cfg = yaml.safe_load((pathlib.Path(root) / "config.yaml").read_text(encoding="utf-8")) or {}
    except Exception:  # noqa: BLE001
        return None
    fs = (cfg.get("research") or {}).get("frozen_space")
    return {"features": set(fs.get("features") or []), "models": set(fs.get("models") or [])} if fs else None


def check_trial_registry(root) -> list[str]:
    root = pathlib.Path(root)
    reg_path, trials_path = root / "research" / "trial_registry.jsonl", root / "research" / "trials.csv"
    trials = list(csv.DictReader(trials_path.open(encoding="utf-8"))) if trials_path.is_file() else []
    if not reg_path.is_file():
        bad = [t["trial_id"] for t in trials if (t.get("registry_hash") or "").strip()]
        return [f"L-06: trials.csv có {len(bad)} lần thử mang registry_hash nhưng thiếu research/trial_registry.jsonl"] if bad else []
    errs = _chain_errors(reg_path, "L-06 sổ đăng ký")
    reg = [json.loads(l) for l in reg_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    if errs or not reg:
        return errs
    ids = [r.get("trial_id") for r in reg]
    for d in sorted({i for i in ids if ids.count(i) > 1}):
        errs.append(f"L-06: sổ đăng ký có mã thử trùng {d}")
    frozen = _frozen_space(root)
    if frozen:
        for r in reg:
            extra = [f for f in str(r.get("features", "")).split(";") if f and f not in frozen["features"]]
            if extra or r.get("model") not in frozen["models"]:
                errs.append(f"L-06: {r.get('trial_id')} nằm ngoài không gian giả thuyết đóng băng "
                            f"(feature lạ {extra}, mô hình {r.get('model')}) — giả thuyết mới phải qua ADR")
    start = min(r["trial_id"] for r in reg)          # mã thử đánh số liên tục T00001…; sổ bắt đầu từ mã này
    by_id = {r["trial_id"]: r for r in reg}
    tids = [t.get("trial_id") for t in trials if t.get("trial_id", "") >= start]
    for d in sorted({i for i in tids if tids.count(i) > 1}):
        errs.append(f"L-06: trials.csv có hai kết quả cho cùng mã thử {d}")
    since = [t for t in trials if t.get("trial_id", "") >= start]
    for t in since:
        r = by_id.get(t["trial_id"])
        if r is None:
            errs.append(f"L-06: {t['trial_id']} ({t.get('cycle_date')}) có kết quả nhưng không có dòng đăng ký trước"); continue
        if r.get("spec_id") != t.get("spec_id"):
            errs.append(f"L-06: {t['trial_id']} spec_id lệch sổ đăng ký")
        try:
            if abs(float(r.get("threshold")) - float(t.get("threshold"))) > 1e-9:
                errs.append(f"L-06: {t['trial_id']} ngưỡng lệch sổ đăng ký")
        except (TypeError, ValueError):
            errs.append(f"L-06: {t['trial_id']} ngưỡng không đọc được")
        if (t.get("registry_hash") or "") != r.get("hash"):
            errs.append(f"L-06: {t['trial_id']} registry_hash không khớp dòng đăng ký")
    if len(reg) < len(since):
        errs.append(f"L-06: {len(since)} lần thử từ {start} nhưng sổ đăng ký chỉ có {len(reg)} dòng")
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
            + check_trial_registry(root) + check_personal_data(root) + check_exams(root))
