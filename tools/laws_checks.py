"""Kiểm máy cho governance/LAWS.md — gọi từ tools/validate.py, có test riêng.
L-07  một kiến trúc: ARCHITECTURE_v*.md phải được liệt kê SUPERSEDED trong architecture/ARCHIVE.md.
L-02  không khuyến nghị: reports/, media/, ledger/ không chứa từ khóa khuyến nghị mua bán.
L-05/Ledger  hash chuỗi: ledger/predictions.jsonl và ledger/resolutions.jsonl mỗi dòng có sha256 và prev_hash khớp dòng trước
      (dòng đầu "GENESIS"); sửa một kết quả đã ghi làm CI đỏ.
L-03  dữ liệu cá nhân: tệp chữ (md/yaml/json/jsonl/txt) ngoài dữ liệu giá không chứa số định danh/số tài khoản đi kèm
      nhãn (CCCD, CMND, căn cước, hộ chiếu, số tài khoản, STK, account number).
L-09  người viết ≠ người chấm: thân PR có "authored_by:" và "reviewed_by:"; reviewed_by không rỗng, không cùng nhà cung cấp
      với authored_by (workflow review_gate.yml gọi check_pr_review).
L-06  sổ thử: research/trial_registry.jsonl đúng hash chuỗi; mọi lần thử trong research/trials.csv từ mã thử đầu tiên
      của sổ trở đi đều có dòng đăng ký cùng trial_id, spec_id, ngưỡng, registry_hash; số dòng đăng ký ≥ số lần thử đó.
"""
import csv, hashlib, json, pathlib, re

RECOMMEND_PATTERNS = [r"mua ngay", r"n[êe]n mua", r"b[áa]n ngay", r"n[êe]n b[áa]n", r"gi[áa] m[ụu]c ti[êe]u",
                      r"target price", r"khuy[ếe]n ngh[ịi] mua", r"khuy[ếe]n ngh[ịi] b[áa]n", r"\bBUY\b", r"\bSELL\b"]
_RE = re.compile("|".join(RECOMMEND_PATTERNS), re.IGNORECASE)
SCAN_DIRS = ("reports", "media", "ledger")
SCAN_EXT = {".md", ".txt", ".jsonl", ".json", ".yaml", ".yml", ".csv"}


def recommendation_hit(text: str):
    """Trả về cụm từ khóa khuyến nghị đầu tiên tìm thấy (L-02), hoặc None."""
    m = _RE.search(text or "")
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
        if not p.is_file() or p.suffix.lower() not in PII_EXT or PII_SKIP_DIRS & set(p.relative_to(root).parts):
            continue
        try:
            text = p.read_text(encoding="utf-8")
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
    for p in sorted(arch_dir.glob("ARCHITECTURE_v*.md")):
        if p.name not in archive or "SUPERSEDED" not in archive:
            errs.append(f"L-07: {p.relative_to(root)} không được liệt kê SUPERSEDED trong architecture/ARCHIVE.md")
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
                text = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                m = _RE.search(line)
                if m:
                    errs.append(f"L-02: {p.relative_to(root)}:{i} chứa từ khóa khuyến nghị '{m.group(0)}'")
                    break
    return errs


def _chain_errors(path, label) -> list[str]:
    errs, prev = [], "GENESIS"
    for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except ValueError:
            errs.append(f"{label}: dòng {n} không phải JSON"); break
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
    start = min(r["trial_id"] for r in reg)          # mã thử đánh số liên tục T00001…; sổ bắt đầu từ mã này
    by_id = {r["trial_id"]: r for r in reg}
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
             "openai": ("chatgpt", "openai", "gpt", "codex", "o1", "o3", "o4", "minh tri", "minh trí"),
             "xai": ("grok", "xai"), "google": ("gemini", "google", "bard"),
             "meta": ("llama", "meta ai"), "deepseek": ("deepseek",), "mistral": ("mistral",)}
_PROVIDER_RE = {k: re.compile(r"(?<![a-z0-9])(" + "|".join(re.escape(x) for x in keys) + r")(?![a-z0-9])")
                for k, keys in PROVIDERS.items()}


def _providers(text: str) -> set:
    """Nhà cung cấp mô hình được nhắc tới trong một chuỗi tên ghế (so khớp theo từ, không theo chuỗi con)."""
    t = (text or "").lower()
    return {k for k, rx in _PROVIDER_RE.items() if rx.search(t)}


def same_provider(a: str, b: str) -> bool:
    """L-09: hai ghế cùng nhà cung cấp, hoặc cùng tên. Ghế người (Owner) không có nhà cung cấp."""
    if (a or "").strip().lower() == (b or "").strip().lower():
        return True
    return bool(_providers(a) & _providers(b))


# Nhận ghế chấm hợp lệ: chuỗi phải BẮT ĐẦU bằng "owner" hoặc một tên trong PROVIDERS, và ngay sau đó không được là
# ký tự chữ/số/gạch dưới (mọi bảng chữ, vì \w là Unicode); riêng "owner" còn không được nối bằng gạch ngang.
# Neo đầu chuỗi nên "not_an_owner", "éowner", "an owner", "not_a_grok" đều không được nhận.
# (Chặn cùng nhà cung cấp thì ngược lại: _providers() dò lỏng ở mọi vị trí để không lọt.)
_REVIEWER_START_RE = re.compile(
    r"^(?:owner(?![\w-])|(?:" + "|".join(re.escape(x) for x in sorted({k for ks in PROVIDERS.values() for k in ks},
                                                                    key=len, reverse=True)) + r")(?!\w))")


def check_pr_review(body: str) -> list[str]:
    """L-09 cho một PR: đọc hai dòng 'authored_by:' và 'reviewed_by:' trong thân PR."""
    fields = {}
    for line in (body or "").splitlines():
        m = re.match(r"^\s*[-*]?\s*(authored_by|reviewed_by)\s*:\s*(.*?)\s*$", line, re.IGNORECASE)
        if m:
            fields[m.group(1).lower()] = m.group(2).strip().strip("`")
    a, r = fields.get("authored_by", ""), fields.get("reviewed_by", "")
    if not a:
        return ["L-09: thân PR thiếu dòng 'authored_by: <ghế/mô hình>'"]
    if not r:
        return ["L-09: chưa có người chấm — điền 'reviewed_by: <ghế khác nhà cung cấp>' sau khi chấm xong"]
    if same_provider(a, r):
        return [f"L-09: người viết và người chấm cùng nhà cung cấp hoặc cùng tên ('{a}' / '{r}')"]
    if not _REVIEWER_START_RE.match(r.strip().lower()):
        return [f"L-09: reviewed_by '{r}' phải BẮT ĐẦU bằng tên ghế chấm: 'Owner', hoặc tên mô hình/nhà cung cấp "
                "(ví dụ 'ChatGPT (OpenAI)', 'Grok (xAI)', 'Gemini (Google)')"]
    return []


def run_all(root) -> list[str]:
    return (check_one_architecture(root) + check_no_recommendation(root) + check_ledger_chain(root)
            + check_trial_registry(root) + check_personal_data(root))
