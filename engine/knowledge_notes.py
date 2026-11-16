"""Kiểm máy Thư viện (L-01 Nguồn, L-04 Bản quyền/giấy phép, L-08 Hiệu lực văn bản, L-09 không tự gán trạng thái).
Cỗ máy học hiểu chuyển từ MINH TRÍ (tools/reading_notes.py), đổi "mã đoạn kinh" thành "địa chỉ tài liệu".

Quy ước trên đĩa (library/sources/README.md):
- library/sources/<doc_id>/text.md: văn bản thuần. Dòng "[p<N>]" mở trang N. Trong trang, đoạn cách nhau bởi dòng trống,
  đánh số 1, 2, … theo thứ tự. Dòng "[t<N>]" mở bảng N: các dòng bắt đầu bằng "|" ngay sau đó là bảng markdown;
  dòng đầu là tiêu đề, dòng "|---" bỏ qua, dòng dữ liệu đánh số 1, 2, … Bảng không tính là đoạn.
- library/SOURCE_MANIFEST.json "files"[<doc_id>]: sha256 + bytes của text.md, issuer, issued_on, accessed_on, source_url,
  data_source (tên trong governance/DATA_SOURCES.yaml, không được là nguồn "forbidden"), legal_status, license,
  kind, effective_from, effective_to, superseded_by.
- library/notes/<KN-id>.json: KNOWLEDGE_NOTE theo contracts/knowledge_note.schema.json.
- library/audits/<KN-id>.json: biên bản chấm {note_id, auditor, verdict: PASS|FAIL, date} — chỉ biên bản PASS của người
  khác read_by mới cho phép trạng thái ngoài DRAFT/OUTDATED (CITED chỉ do Auditor gán).

Địa chỉ: "<doc_id>:p<trang>:<đoạn>" hoặc "<doc_id>:t<bảng>:<dòng>". Trích dẫn (quote) phải nằm nguyên văn (so sau khi gộp
khoảng trắng) trong ít nhất một chỗ được trỏ tới.

Dùng: python -m engine.knowledge_notes          kiểm toàn thư viện, in lỗi/cảnh báo
      run_cycle gọi mark_outdated() để tự chuyển OUTDATED (L-08).
"""
import hashlib, json, pathlib, re, sys
from datetime import date

import yaml

from .config import REPO

LIB = "library"
MAX_NOTE_BYTES = 16_000
LEGAL_KINDS = {"LAW", "DECREE", "CIRCULAR", "DECISION", "STANDARD", "REGULATION"}
FREE_STATUS = {"DRAFT", "OUTDATED"}
ADDR_RE = re.compile(r"^([a-z0-9_-]+):(p|t)([0-9]+):([0-9]+)$")
MANIFEST_KEYS = ["sha256", "bytes", "issuer", "issued_on", "accessed_on", "source_url", "data_source", "legal_status",
                 "license", "kind", "effective_from", "effective_to", "superseded_by"]


def _norm(s):
    return re.sub(r"\s+", " ", str(s or "")).strip()


def parse_text(text):
    """→ (pages {N: [đoạn]}, tables {N: [dòng dữ liệu]})."""
    pages, tables = {}, {}
    page, para, table = None, [], None
    def flush():
        if page is not None and para:
            pages.setdefault(page, []).append(" ".join(para))
    for raw in text.splitlines():
        line = raw.strip()
        m = re.fullmatch(r"\[p([0-9]+)\]", line)
        if m:
            flush(); para, table = [], None
            page = int(m.group(1)); pages.setdefault(page, [])
            continue
        m = re.fullmatch(r"\[t([0-9]+)\]", line)
        if m:
            flush(); para = []
            table = int(m.group(1)); tables[table] = []
            continue
        if table is not None:
            if line.startswith("|"):
                tables[table].append(line)
                continue
            table = None
        if not line:
            flush(); para = []
        elif page is not None:
            para.append(line)
    flush()
    tables = {k: [r for r in v[1:] if not re.fullmatch(r"\|[\s:|-]+\|?", r)] for k, v in tables.items()}
    return pages, tables


def _segment(doc, kind, a, b):
    pages, tables = doc
    rows = (pages if kind == "p" else tables).get(a)
    return rows[b - 1] if rows and 1 <= b <= len(rows) else None


def load_manifest(root):
    p = pathlib.Path(root) / LIB / "SOURCE_MANIFEST.json"
    return (json.loads(p.read_text(encoding="utf-8")).get("files") or {}) if p.is_file() else {}


def _data_sources(root):
    p = pathlib.Path(root) / "governance" / "DATA_SOURCES.yaml"
    d = yaml.safe_load(p.read_text(encoding="utf-8")) if p.is_file() else {}
    return {s.get("name"): s.get("usage") for s in (d or {}).get("sources", [])}


def _date(v):
    try:
        return date.fromisoformat(str(v))
    except ValueError:
        return None

def _expired(entry, today):
    if entry.get("superseded_by"):
        return True
    to = _date(entry.get("effective_to")) if entry.get("effective_to") else None
    return bool(to) and to < today


def check_manifest(root):
    """L-01/L-04/L-08: mọi tài liệu trong library/sources đều được ghim, đúng sha256/bytes, đủ trường, nguồn được phép."""
    root = pathlib.Path(root)
    errs, docs = [], {}
    man, ds = load_manifest(root), _data_sources(root)
    src_dir = root / LIB / "sources"
    on_disk = {p.name for p in src_dir.iterdir() if p.is_dir()} if src_dir.is_dir() else set()
    for d in sorted(on_disk - set(man)):
        errs.append(f"L-01: library/sources/{d}/ chưa ghim trong SOURCE_MANIFEST.json")
    for doc_id, e in sorted(man.items()):
        miss = [k for k in MANIFEST_KEYS if k not in e]
        if miss:
            errs.append(f"L-01/L-04: manifest {doc_id} thiếu trường {miss}"); continue
        if not e.get("license"):
            errs.append(f"L-04: manifest {doc_id} chưa ghi license")
        if not e.get("legal_status"):
            errs.append(f"L-04: manifest {doc_id} chưa ghi legal_status")
        usage = ds.get(e.get("data_source"))
        if usage is None:
            errs.append(f"L-04: manifest {doc_id} data_source '{e.get('data_source')}' không có trong DATA_SOURCES.yaml")
        elif usage == "forbidden":
            errs.append(f"L-04: manifest {doc_id} lấy từ nguồn bị cấm '{e.get('data_source')}'")
        if str(e.get("kind", "")).upper() in LEGAL_KINDS and not e.get("effective_from"):
            errs.append(f"L-08: văn bản {doc_id} ({e.get('kind')}) thiếu effective_from")
        for k in ("issued_on", "accessed_on", "effective_from", "effective_to"):
            if e.get(k) and _date(e[k]) is None:
                errs.append(f"manifest {doc_id}: {k} không phải ngày YYYY-MM-DD")
        t = src_dir / doc_id / "text.md"
        if not t.is_file():
            errs.append(f"L-01: thiếu library/sources/{doc_id}/text.md"); continue
        b = t.read_bytes()
        if hashlib.sha256(b).hexdigest() != e.get("sha256") or len(b) != e.get("bytes"):
            errs.append(f"L-01: library/sources/{doc_id}/text.md lệch sha256/bytes đã ghim (tài liệu gốc không được sửa)")
            continue
        docs[doc_id] = parse_text(b.decode("utf-8"))
    return errs, docs, man


def _audit_pass(root, note):
    p = pathlib.Path(root) / LIB / "audits" / f"{note.get('id')}.json"
    if not p.is_file():
        return False
    a = json.loads(p.read_text(encoding="utf-8"))
    return (a.get("note_id") == note.get("id") and a.get("verdict") == "PASS"
            and _norm(a.get("auditor")).lower() not in ("", _norm(note.get("read_by")).lower()))


def check_note(root, path, docs, man, today):
    """→ (lỗi, cảnh báo) cho một ghi chú."""
    errs, warns = [], []
    rel = path.relative_to(root).as_posix()
    raw = path.read_bytes()
    if len(raw) >= MAX_NOTE_BYTES:
        errs.append(f"{rel}: ≥ {MAX_NOTE_BYTES} byte")
    try:
        note = json.loads(raw.decode("utf-8"))
    except ValueError as e:
        return [f"{rel}: JSON lỗi ({e})"], warns
    try:
        import jsonschema
        schema = json.loads((pathlib.Path(root) / "contracts" / "knowledge_note.schema.json").read_text(encoding="utf-8"))
        jsonschema.validate(note, schema)
    except ImportError:
        errs.append(f"{rel}: thiếu jsonschema để kiểm hợp đồng")
    except Exception as e:  # noqa: BLE001
        return [f"{rel}: không khớp knowledge_note.schema.json — {str(e).splitlines()[0]}"], warns
    nid = note["id"]
    if path.stem != nid:
        errs.append(f"{rel}: tên tệp phải là {nid}.json")
    for d in note["doc_ids"]:
        if d not in man:
            errs.append(f"{nid}: doc_id {d} không có trong SOURCE_MANIFEST.json (L-01)")
    legal = [d for d in note["doc_ids"] if str(man.get(d, {}).get("kind", "")).upper() in LEGAL_KINDS]
    if note["tier"] == 2 and legal and not note.get("effective_date"):
        errs.append(f"{nid}: ghi chú T2 về văn bản pháp luật/chuẩn mực phải có effective_date (L-08)")
    ids = [p["id"] for p in note["points"]]
    if len(ids) != len(set(ids)):
        errs.append(f"{nid}: id ý bị trùng")
    for p in note["points"]:
        segs = []
        for a in p["addresses"]:
            m = ADDR_RE.match(a)
            d, kind, x, y = m.group(1), m.group(2), int(m.group(3)), int(m.group(4))
            if d not in note["doc_ids"]:
                errs.append(f"{nid}/{p['id']}: địa chỉ {a} trỏ tới tài liệu ngoài doc_ids"); continue
            if d not in docs:
                continue                                   # lỗi manifest/sha đã báo ở check_manifest
            seg = _segment(docs[d], kind, x, y)
            if seg is None:
                errs.append(f"{nid}/{p['id']}: địa chỉ {a} không tồn tại trong library/sources/{d}/text.md")
            else:
                segs.append(seg)
        if segs and not any(_norm(p["quote"]) in _norm(s) for s in segs):
            errs.append(f"{nid}/{p['id']}: quote không nằm nguyên văn trong chỗ được trỏ tới (L-01)")
    for c in note.get("counts") or []:
        for a in c["addresses"]:
            if not ADDR_RE.match(a):
                errs.append(f"{nid}: counts địa chỉ sai dạng {a}")
    if note["status"] not in FREE_STATUS and not _audit_pass(root, note):
        errs.append(f"{nid}: status {note['status']} cần biên bản library/audits/{nid}.json PASS của người khác read_by (L-09)")
    expired = [d for d in note["doc_ids"] if d in man and _expired(man[d], today)]
    if expired and note["status"] != "OUTDATED":
        warns.append(f"{nid}: dựa trên văn bản hết hiệu lực {expired} — vòng học sẽ chuyển OUTDATED (L-08)")
    for k in ("review_by", "effective_date"):
        if note.get(k) and _date(note[k]) is None:
            errs.append(f"{nid}: {k} không phải ngày YYYY-MM-DD")
    rb = _date(note["review_by"])
    if rb and rb < today:
        warns.append(f"{nid}: quá hạn kiểm lại review_by {note['review_by']} (L-08)")
    return errs, warns


def check_library(root=REPO, today=None):
    """→ (lỗi, cảnh báo) cho toàn thư viện; validate.py gọi hàm này."""
    root = pathlib.Path(root)
    today = today or date.today()
    errs, docs, man = check_manifest(root)
    warns = []
    notes_dir = root / LIB / "notes"
    notes = sorted(notes_dir.glob("*.json")) if notes_dir.is_dir() else []
    for p in notes:
        e, w = check_note(root, p, docs, man, today)
        errs += e; warns += w
    index = (root / LIB / "INDEX.md").read_text(encoding="utf-8") if (root / LIB / "INDEX.md").is_file() else ""
    for p in notes:
        if p.stem not in index:
            warns.append(f"{p.stem}: chưa liệt kê trong library/INDEX.md")
    return errs, warns


def mark_outdated(root=REPO, today=None):
    """L-08: ghi chú dựa trên văn bản đã bị thay thế/hết hiệu lực tự chuyển OUTDATED. Trả về danh sách id đã chuyển."""
    root = pathlib.Path(root)
    today = today or date.today()
    man = load_manifest(root)
    changed = []
    notes_dir = root / LIB / "notes"
    for p in sorted(notes_dir.glob("*.json")) if notes_dir.is_dir() else []:
        try:
            note = json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            continue
        if note.get("status") == "OUTDATED":
            continue
        if any(d in man and _expired(man[d], today) for d in note.get("doc_ids", [])):
            note["status"] = "OUTDATED"
            p.write_text(json.dumps(note, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            changed.append(note.get("id"))
    return changed


if __name__ == "__main__":
    e, w = check_library()
    for x in w: print("CẢNH BÁO: " + x)
    for x in e: print("LỖI: " + x)
    print("OK — thư viện hợp lệ" if not e else f"{len(e)} lỗi")
    sys.exit(1 if e else 0)
