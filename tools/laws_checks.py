"""Kiểm máy cho governance/LAWS.md — gọi từ tools/validate.py, có test riêng.
L-07  một kiến trúc: ARCHITECTURE_v*.md phải được liệt kê SUPERSEDED trong architecture/ARCHIVE.md.
L-02  không khuyến nghị: reports/, media/, ledger/ không chứa từ khóa khuyến nghị mua bán.
L-05/Ledger  hash chuỗi: ledger/predictions.jsonl mỗi dòng có sha256 và prev_hash khớp dòng trước (dòng đầu "GENESIS").
"""
import hashlib, json, pathlib, re

RECOMMEND_PATTERNS = [r"mua ngay", r"n[êe]n mua", r"b[áa]n ngay", r"n[êe]n b[áa]n", r"gi[áa] m[ụu]c ti[êe]u",
                      r"target price", r"khuy[ếe]n ngh[ịi] mua", r"khuy[ếe]n ngh[ịi] b[áa]n", r"\bBUY\b", r"\bSELL\b"]
_RE = re.compile("|".join(RECOMMEND_PATTERNS), re.IGNORECASE)
SCAN_DIRS = ("reports", "media", "ledger")
SCAN_EXT = {".md", ".txt", ".jsonl", ".json", ".yaml", ".yml", ".csv"}


def line_hash(payload: dict) -> str:
    """sha256 của dòng Ledger không kể trường 'hash' — ổn định theo khóa sắp xếp."""
    body = {k: v for k, v in payload.items() if k != "hash"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


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


def check_ledger_chain(root) -> list[str]:
    root = pathlib.Path(root)
    path = root / "ledger" / "predictions.jsonl"
    if not path.is_file():
        return []
    errs, prev = [], "GENESIS"
    for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except ValueError:
            errs.append(f"Ledger: dòng {n} không phải JSON"); break
        if row.get("prev_hash") != prev:
            errs.append(f"Ledger: dòng {n} prev_hash không khớp dòng trước"); break
        if row.get("hash") != line_hash(row):
            errs.append(f"Ledger: dòng {n} hash không khớp nội dung"); break
        prev = row["hash"]
    return errs


def run_all(root) -> list[str]:
    return check_one_architecture(root) + check_no_recommendation(root) + check_ledger_chain(root)
