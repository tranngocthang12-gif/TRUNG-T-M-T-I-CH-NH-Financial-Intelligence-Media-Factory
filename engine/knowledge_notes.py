"""Kiểm máy Thư viện (L-01 Nguồn, L-04 Bản quyền/giấy phép, L-08 Hiệu lực văn bản, L-09 không tự gán trạng thái).
Cỗ máy học hiểu chuyển từ MINH TRÍ (tools/reading_notes.py), đổi "mã đoạn kinh" thành "địa chỉ tài liệu".

Quy ước trên đĩa (library/sources/README.md):
- library/sources/<doc_id>/text.md: văn bản thuần. Dòng "[p<N>]" mở trang N. Trong trang, đoạn cách nhau bởi dòng trống,
  đánh số 1, 2, … theo thứ tự. Dòng "[t<N>]" mở bảng N: các dòng bắt đầu bằng "|" ngay sau đó là bảng markdown;
  dòng đầu là tiêu đề, dòng "|---" bỏ qua, dòng dữ liệu đánh số 1, 2, … Bảng không tính là đoạn.
- library/SOURCE_MANIFEST.json "files"[<doc_id>]: sha256 + bytes của text.md (không phải của PDF), issuer, issued_on, accessed_on, source_url,
  data_source (tên trong governance/DATA_SOURCES.yaml, không được là nguồn "forbidden"), legal_status, license,
  kind, effective_from, effective_to, superseded_by. Mọi dòng phải ghim original_sha256, original_bytes,
  original_path, text_sha256, text_bytes — text_* phải trùng sha256/bytes, original_* phải khác và trỏ tới tệp
  trong cùng thư mục, không phải text.md. Bỏ các trường đó không qua cổng nguồn (ADR-0012). Hash từng trang tính
  trên cả trang, gồm bảng. Hash đó không phải biên bản đã đối chiếu PDF: SOURCED và ghi chú CITED/TESTED/PROVEN
  cần thêm pdf_check của một ghế. BCTC (kind FINANCIAL_STATEMENT, ADR-0008) thêm period_end (ngày khóa
  sổ của kỳ) và published_on (ngày CÔNG BỐ công khai — ngày đầu tiên thị trường biết số liệu); số liệu chỉ được dùng từ
  published_on (usable_on), không phải từ period_end.
- library/notes/<KN-id>.json: KNOWLEDGE_NOTE theo contracts/knowledge_note.schema.json.
- library/audits/<KN-id>.json: biên bản chấm {note_id, auditor, verdict: PASS|FAIL, date, note_sha256}.
  note_sha256 = note_digest() của ghi chú (mọi trường trừ status) → sửa ghi chú sau khi chấm thì biên bản hết hiệu lực.
  auditor và read_by đều bắt đầu bằng tên ghế (Owner hoặc mô hình/nhà cung cấp) và không chung ghế (L-09).
  Trạng thái: DRAFT, OUTDATED tự do; CITED cần biên bản PASS; DISPUTED cần biên bản FAIL; TESTED/PROVEN chưa có cơ chế
  gán (Học viện chưa vận hành) → bị từ chối, đóng khi không chắc.

Địa chỉ: "<doc_id>:p<trang>:<đoạn>" hoặc "<doc_id>:t<bảng>:<dòng>". Trích dẫn (quote) phải nằm nguyên văn (so sau khi gộp
khoảng trắng) trong ít nhất một chỗ được trỏ tới.

Dùng: python -m engine.knowledge_notes          kiểm toàn thư viện, in lỗi/cảnh báo
      run_cycle gọi mark_outdated() để tự chuyển OUTDATED (L-08).
"""
import hashlib, json, pathlib, re, sys
from datetime import date, datetime

import yaml

from .config import REPO

if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
from tools.laws_checks import nfc, recognised_seat, same_provider  # noqa: E402

LIB = "library"
MAX_NOTE_BYTES = 16_000
MIN_QUOTE_CHARS = 15                      # trích ngắn hơn thế chỉ hợp lệ khi là nguyên cả đoạn/dòng được trỏ tới
LEGAL_KINDS = {"LAW", "DECREE", "CIRCULAR", "DECISION", "STANDARD", "REGULATION"}
FINANCIAL_KINDS = {"FINANCIAL_STATEMENT"}     # ADR-0008: số liệu dùng theo ngày công bố
FREE_STATUS = {"DRAFT", "OUTDATED"}
USABLE_NOTE_STATUS = {"CITED", "TESTED", "PROVEN"}   # dùng cho câu trả lời / quyết định; DISPUTED không phải trạng thái dùng được
AUDIT_VERDICT_FOR = {"CITED": "PASS", "DISPUTED": "FAIL"}     # TESTED/PROVEN: do mã Học viện gán — chưa có → từ chối
ADDR_RE = re.compile(r"^([a-z0-9_-]+):(p|t)([0-9]+):([0-9]+)$")
MANIFEST_KEYS = ["sha256", "bytes", "issuer", "issued_on", "accessed_on", "source_url", "data_source", "legal_status",
                 "license", "kind", "effective_from", "effective_to", "superseded_by"]
# sha256/bytes luôn là text.md. Mọi dòng manifest phải ghim tệp gốc (ADR-0012, sửa sau phản biện).
# Không còn đường vòng "bỏ original_* thì qua cổng". Manifest trên main đang rỗng nên không có dòng cũ cần miễn.
ORIGINAL_KEYS = ("original_sha256", "original_bytes", "original_path", "text_sha256", "text_bytes")
KNOWN_ORIGINALS = {
    "luat_ke_toan_88_2015": {
        "original_sha256": "1fd9336a3a6f4d90676db5889bdb409af9c75c96c9c256143197908a7bfcca50",
        "original_bytes": 2_566_253,
        "pages": 35,
    },
}


def _norm(s):
    """Chuẩn hóa để so nguyên văn: Unicode NFC (văn bản rút từ PDF hay ở dạng tổ hợp) và gộp khoảng trắng. Không đổi chữ."""
    return re.sub(r"\s+", " ", nfc(str(s or ""))).strip()


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

def usable_from(entry):
    """Ngày sớm nhất được dùng nội dung tài liệu (ADR-0008): BCTC → published_on; tài liệu khác → issued_on."""
    if str(entry.get("kind", "")).upper() in FINANCIAL_KINDS:
        return _date(entry.get("published_on"))
    return _date(entry.get("issued_on"))

def usable_on(man, doc_id, day):
    """True nếu tại ngày `day` thị trường đã biết nội dung tài liệu doc_id. Mọi nơi dùng số liệu BCTC cho một ngày phải qua
    hàm này: dự báo, đề thi, backtest. Thiếu ngày công bố → False (đóng khi không chắc)."""
    d = usable_from(man.get(doc_id, {}))
    if d is None:
        return False
    # A wrong or missing historical cutoff must never become an unlimited future date.
    if isinstance(day, datetime):
        day = day.date()
    elif not isinstance(day, date):
        day = _date(day)
    return day is not None and d <= day

def _expired(entry, today):
    if entry.get("superseded_by"):
        return True
    to = _date(entry.get("effective_to")) if entry.get("effective_to") else None
    return bool(to) and to < today


def claims_original(entry) -> bool:
    """True khi dòng manifest khai bất kỳ trường tệp gốc hoặc biên bản đối chiếu trang."""
    if not isinstance(entry, dict):
        return False
    return any(k in entry for k in ORIGINAL_KEYS) or "crosscheck" in entry


def _sha256_hex(v) -> bool:
    return isinstance(v, str) and re.fullmatch(r"[0-9a-f]{64}", v) is not None


def _pos_int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool) and v > 0


def original_file(root, doc_id, rel):
    """→ (Path|None, lỗi|None). Đường dẫn tương đối, trong library/sources/<doc_id>/, không phải text.md."""
    rel = str(rel or "").strip().replace("\\", "/")
    if not rel or rel.startswith("/") or rel.startswith("~"):
        return None, "đường dẫn tệp gốc không được tuyệt đối"
    if ".." in pathlib.PurePosixPath(rel).parts:
        return None, "đường dẫn tệp gốc không được chứa .."
    prefix = f"library/sources/{doc_id}/"
    if not rel.startswith(prefix) or rel == prefix + "text.md" or rel.endswith("/text.md"):
        return None, "đường dẫn tệp gốc phải nằm trong library/sources/<doc_id>/ và không được là text.md"
    root = pathlib.Path(root).resolve()
    path = (root / rel).resolve()
    try:
        path.relative_to((root / LIB / "sources" / doc_id).resolve())
    except ValueError:
        return None, "đường dẫn tệp gốc thoát khỏi thư mục tài liệu"
    return path, None


def page_surface(text: str) -> dict:
    """Mọi dòng nội dung của từng trang, theo thứ tự, kể cả tiêu đề và từng dòng bảng.
    Dòng [pN]/[tN] chỉ là mốc. Không bỏ ô bảng. Không đổi số, dấu âm hay chữ phủ định."""
    pages = {}
    page = None
    for raw in str(text or "").splitlines():
        line = nfc(raw).strip()
        m = re.fullmatch(r"\[p([0-9]+)\]", line)
        if m:
            page = int(m.group(1))
            pages.setdefault(page, [])
            continue
        if re.fullmatch(r"\[t[0-9]+\]", line):
            continue
        if page is None or line == "":
            continue
        pages[page].append(line)
    return pages


def page_fingerprint(lines):
    """sha256 của cả trang. `lines` phải là page_surface, không phải danh sách đoạn sau khi tách bảng.
    NFC từng dòng. Không gộp chữ, không bỏ dấu trừ, không bỏ từ phủ định."""
    body = "\n".join(nfc(str(x)).strip() for x in (lines or []) if str(x).strip())
    words = body.split()
    head = " ".join(words[:8])
    tail = " ".join(words[-8:]) if words else ""
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    return body, digest, head, tail


def page_crosscheck(text: str) -> dict:
    """Tầng máy: hash từng trang của chính text.md, gồm đoạn, tiêu đề và bảng.
    Không điền pdf_check. Hàm này không chứng nhận bản chép đã khớp PDF."""
    surface = page_surface(text)
    rows = []
    for n in sorted(surface):
        _body, digest, head, tail = page_fingerprint(surface[n])
        rows.append({"page": n, "sha256": digest, "head": head, "tail": tail})
    return {"method": "page-by-page", "pages": rows}


def _page_hash_errors(entry, text, doc_id=None) -> list[str]:
    """Tầng 1: hash cả trang khớp text.md, đủ trang 1..N. Không xét người đã nhìn PDF."""
    if not isinstance(text, str):
        return ["không có text.md để tính hash cả trang, gồm bảng"]
    surface = page_surface(text)
    if not _page_set_ok(surface, len(surface)):
        return ["thiếu trang hoặc đánh số trang không liền từ 1"]
    cc = entry.get("crosscheck") if isinstance(entry, dict) else None
    if not isinstance(cc, dict) or cc.get("method") != "page-by-page" or not isinstance(cc.get("pages"), list):
        return ["chưa có biên bản đối chiếu từng trang; không được chỉ khai pages_checked"]
    ev = cc["pages"]
    order = [e.get("page") for e in ev if isinstance(e, dict)]
    if order != list(range(1, len(surface) + 1)) or len(ev) != len(surface):
        return ["biên bản không khớp đủ từng trang theo thứ tự 1..N — thiếu trang hoặc đánh số sai"]
    errs = []
    for e in ev:
        if not isinstance(e, dict):
            errs.append("một dòng biên bản trang không phải đối tượng")
            continue
        _body, digest, head, tail = page_fingerprint(surface.get(e.get("page")) or [])
        if e.get("sha256") != digest or e.get("head") != head or e.get("tail") != tail:
            errs.append(f"trang {e.get('page')} không khớp sha256/head/tail của cả trang (gồm bảng) — reviewer không kiểm được")
    known = KNOWN_ORIGINALS.get(doc_id or "")
    if known and len(surface) != known["pages"]:
        errs.append(f"chưa đối chiếu đủ {known['pages']} trang của bản gốc đã công bố")
    return errs


def pdf_witness_errors(entry, text) -> list[str]:
    """Tầng 2: một ghế khai đã đối chiếu text.md với PDF. Máy không đọc ảnh trang.
    Thiếu biên bản này thì hash tự sinh không được dùng làm chứng nhận."""
    cc = entry.get("crosscheck") if isinstance(entry, dict) else None
    w = cc.get("pdf_check") if isinstance(cc, dict) else None
    if not isinstance(w, dict):
        return ["hash từng trang tự tính từ text.md không phải bằng chứng đã đối chiếu PDF; thiếu pdf_check"]
    if w.get("result") != "MATCH":
        return ["pdf_check.result phải là MATCH sau khi đối chiếu text.md với PDF"]
    if not recognised_seat(str(w.get("checker") or "")):
        return ["pdf_check.checker phải bắt đầu bằng tên ghế đã đối chiếu PDF"]
    if len(str(w.get("evidence") or "").strip()) < 15:
        return ["pdf_check.evidence thiếu mô tả đối chiếu để reviewer kiểm"]
    if not isinstance(text, str):
        return ["pdf_check không gắn được vì thiếu text.md"]
    text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if w.get("text_sha256") != text_hash or w.get("text_sha256") != entry.get("text_sha256"):
        return ["pdf_check không gắn với đúng bản text.md hiện tại — biên bản cũ không còn hiệu lực khi bản chép đổi"]
    if w.get("original_sha256") != entry.get("original_sha256"):
        return ["pdf_check không gắn với đúng tệp PDF đã ghim"]
    n = len(page_surface(text))
    if w.get("pages_checked") != list(range(1, n + 1)):
        return ["pdf_check.pages_checked phải là danh sách đủ trang 1..N đã đối chiếu, không phải một số đếm"]
    return []


def transcription_errors(entry, pages, doc_id=None, text=None, require_witness=True) -> list[str]:
    """Lỗi nếu chưa chứng minh chép đúng từng trang. Số pages_checked một mình không đủ.
    require_witness=False: chỉ tầng hash máy (cổng ghim). True: thêm pdf_check (SOURCED và ghi chú dùng được)."""
    if not isinstance(entry, dict) or not claims_original(entry):
        return ["thiếu ghim tệp gốc"]
    if entry.get("original_sha256") in (entry.get("sha256"), entry.get("text_sha256")):
        return ["hash text.md không được dùng làm hash tệp gốc"]
    errs = _page_hash_errors(entry, text, doc_id)
    if pages is not None and isinstance(text, str) and set(pages) != set(page_surface(text)) and not errs:
        errs.append("tập trang đã tách không khớp các trang dùng để tính hash")
    if require_witness:
        for msg in pdf_witness_errors(entry, text):
            if msg not in errs:
                errs.append(msg)
    return errs


def transcription_verified(entry, pages, doc_id=None, text=None) -> bool:
    return transcription_errors(entry, pages, doc_id, text, require_witness=True) == []


def _page_set_ok(pages, total) -> bool:
    return isinstance(pages, dict) and _pos_int(total) and set(pages) == set(range(1, total + 1))


def may_mark_sourced(entry, pages, doc_id=None, text=None) -> bool:
    """True chỉ khi tệp gốc được ghim riêng, hash cả trang (gồm bảng) khớp, và có pdf_check gắn đúng hai hash.
    page_crosscheck() tự sinh không đủ. Hàm không đọc đĩa."""
    if not isinstance(text, str) or not transcription_verified(entry, pages, doc_id, text):
        return False
    known = KNOWN_ORIGINALS.get(doc_id or "")
    if known and (entry.get("original_sha256") != known["original_sha256"] or entry.get("original_bytes") != known["original_bytes"]):
        return False
    return True


def origin_binding_errors(root, doc_id, entry, text_bytes) -> list[str]:
    """Mọi tài liệu trong manifest phải ghim tệp gốc. Không khai original_* là lỗi, không phải đường vòng."""
    prefix = f"L-01: {doc_id}"
    if not claims_original(entry):
        return [f"{prefix}: thiếu ghim tệp gốc (original_sha256, original_bytes, original_path, text_sha256, text_bytes); "
                "bỏ các trường này không còn được coi là qua cổng nguồn"]
    errs = []
    missing = [k for k in ORIGINAL_KEYS if entry.get(k) in (None, "")]
    if missing:
        return [f"{prefix}: khai nguồn gốc thì phải có đủ original_sha256, original_bytes, original_path, "
                f"text_sha256, text_bytes; đang thiếu {missing}"]
    if not _sha256_hex(entry.get("text_sha256")) or not _pos_int(entry.get("text_bytes")):
        errs.append(f"{prefix}: text_sha256 phải là 64 hex thường và text_bytes là số nguyên dương — hash của text.md, không phải PDF")
    elif entry.get("text_sha256") != entry.get("sha256") or entry.get("text_bytes") != entry.get("bytes"):
        errs.append(f"{prefix}: text_sha256/text_bytes phải trùng sha256/bytes của text.md")
    text_hash = hashlib.sha256(text_bytes).hexdigest()
    if entry.get("text_sha256") != text_hash or entry.get("text_bytes") != len(text_bytes):
        errs.append(f"{prefix}: text.md lệch text_sha256/text_bytes (không dùng hash này cho tệp gốc)")
    if not _sha256_hex(entry.get("original_sha256")) or not _pos_int(entry.get("original_bytes")):
        errs.append(f"{prefix}: original_sha256 phải là 64 hex thường và original_bytes là số nguyên dương")
    if entry.get("original_sha256") in (entry.get("sha256"), entry.get("text_sha256"), text_hash):
        errs.append(f"{prefix}: hash text.md không được dùng làm hash tệp gốc")
    known = KNOWN_ORIGINALS.get(doc_id)
    if known and (entry.get("original_sha256") != known["original_sha256"] or entry.get("original_bytes") != known["original_bytes"]):
        errs.append(f"{prefix}: không khớp bản gốc đã công bố (SHA-256 {known['original_sha256']}, "
                    f"{known['original_bytes']} byte, {known['pages']} trang)")
    path, why = original_file(root, doc_id, entry.get("original_path"))
    if why:
        errs.append(f"{prefix}: {why}")
    elif not path.is_file():
        errs.append(f"{prefix}: thiếu tệp gốc {entry.get('original_path')}")
    else:
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != entry.get("original_sha256") or len(raw) != entry.get("original_bytes"):
            errs.append(f"{prefix}: tệp gốc lệch original_sha256/original_bytes (đã đổi nội dung hoặc sửa metadata)")
        if raw == text_bytes:
            errs.append(f"{prefix}: tệp gốc trùng byte text.md — không phải hai ghim riêng")
    cc = entry.get("crosscheck", None)
    if "crosscheck" in entry:
        if not isinstance(cc, dict):
            errs.append(f"{prefix}: crosscheck phải là đối tượng method, pages_checked, pages_total")
        else:
            checked, total = cc.get("pages_checked"), cc.get("pages_total")
            if cc.get("method") not in (None, "page-by-page"):
                errs.append(f"{prefix}: crosscheck.method chỉ được là page-by-page")
            if checked is not None and not _pos_int(checked):
                errs.append(f"{prefix}: crosscheck.pages_checked phải là số nguyên dương")
            if total is not None and not _pos_int(total):
                errs.append(f"{prefix}: crosscheck.pages_total phải là số nguyên dương")
            if _pos_int(checked) and _pos_int(total) and checked != total:
                errs.append(f"{prefix}: pages_checked {checked} khác pages_total {total} — chưa đối chiếu đủ trang")
            if known and total not in (None, known["pages"]):
                errs.append(f"{prefix}: pages_total phải là {known['pages']} — chưa đối chiếu đủ {known['pages']} trang thì không ghi nhận")
            if _pos_int(total):
                try:
                    decoded = text_bytes.decode("utf-8")
                    pages, _tables = parse_text(decoded)
                except UnicodeError:
                    decoded, pages = None, {}
                if not _page_set_ok(pages, total):
                    errs.append(f"{prefix}: text.md không có đủ trang 1..{total} để đối chiếu")
            else:
                try:
                    decoded = text_bytes.decode("utf-8")
                    pages, _tables = parse_text(decoded)
                except UnicodeError:
                    decoded, pages = None, {}
            for msg in transcription_errors(entry, pages, doc_id, decoded, require_witness=False):
                if msg == "thiếu ghim tệp gốc":
                    continue
                line = f"{prefix}: {msg}"
                if line not in errs:
                    errs.append(line)
    return errs


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
        for k in ("issued_on", "accessed_on", "effective_from", "effective_to", "period_end", "published_on"):
            if e.get(k) and _date(e[k]) is None:
                errs.append(f"manifest {doc_id}: {k} không phải ngày YYYY-MM-DD")
        if str(e.get("kind", "")).upper() in FINANCIAL_KINDS:
            pe, pub, acc = _date(e.get("period_end")), _date(e.get("published_on")), _date(e.get("accessed_on"))
            if pe is None or pub is None:
                errs.append(f"ADR-0008: BCTC {doc_id} phải có period_end và published_on (ngày công bố) dạng YYYY-MM-DD")
            elif pub < pe:
                errs.append(f"ADR-0008: BCTC {doc_id} có published_on {pub} trước period_end {pe}")
            elif acc is not None and pub > acc:
                errs.append(f"ADR-0008: BCTC {doc_id} có published_on {pub} sau ngày truy cập {acc}")
        t = src_dir / doc_id / "text.md"
        if not t.is_file():
            errs.append(f"L-01: thiếu library/sources/{doc_id}/text.md"); continue
        b = t.read_bytes()
        if hashlib.sha256(b).hexdigest() != e.get("sha256") or len(b) != e.get("bytes"):
            errs.append(f"L-01: library/sources/{doc_id}/text.md lệch sha256/bytes đã ghim (tài liệu gốc không được sửa)")
            continue
        errs.extend(origin_binding_errors(root, doc_id, e, b))
        try:
            docs[doc_id] = parse_text(b.decode("utf-8"))
        except UnicodeError:
            errs.append(f"L-01: library/sources/{doc_id}/text.md không phải UTF-8")
    return errs, docs, man


def note_digest(note: dict) -> str:
    """sha256 của ghi chú không kể trường status (status đổi theo biên bản chấm và theo L-08)."""
    body = {k: v for k, v in note.items() if k != "status"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def audit_problem(root, note):
    """None nếu trạng thái của ghi chú được một biên bản chấm hợp lệ cho phép; ngược lại trả về lý do (chuỗi)."""
    want = AUDIT_VERDICT_FOR.get(note.get("status"))
    if want is None:
        return f"status {note.get('status')} chưa có cơ chế gán bằng mã (Học viện chưa vận hành)"
    p = pathlib.Path(root) / LIB / "audits" / f"{note.get('id')}.json"
    if not p.is_file():
        return f"status {note['status']} cần biên bản library/audits/{note.get('id')}.json"
    try:
        a = json.loads(p.read_text(encoding="utf-8"))
    except ValueError:
        return "biên bản chấm không phải JSON"
    auditor, reader = _norm(a.get("auditor")), _norm(note.get("read_by"))
    if a.get("note_id") != note.get("id"):
        return "biên bản chấm ghi note_id khác"
    if a.get("verdict") != want:
        return f"status {note['status']} cần biên bản verdict {want}, biên bản ghi {a.get('verdict')}"
    if a.get("note_sha256") != note_digest(note):
        return "biên bản chấm không khớp nội dung hiện tại của ghi chú (note_sha256) — sửa ghi chú thì phải chấm lại"
    if not (recognised_seat(auditor) and recognised_seat(reader)):
        return "auditor và read_by phải bắt đầu bằng tên ghế (Owner hoặc mô hình/nhà cung cấp)"
    if same_provider(auditor, reader):
        return "người chấm chung ghế với người đọc (cùng nhà cung cấp, hoặc cùng là Owner)"
    return None


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
    fin = [d for d in note["doc_ids"] if str(man.get(d, {}).get("kind", "")).upper() in FINANCIAL_KINDS]
    if fin:
        eff = _date(note.get("effective_date")) if note.get("effective_date") else None
        if eff is None:
            errs.append(f"{nid}: ghi chú trích BCTC phải có effective_date ≥ ngày công bố của BCTC (ADR-0008)")
        else:
            early = [d for d in fin if not usable_on(man, d, eff)]
            if early:
                errs.append(f"{nid}: effective_date {eff} trước ngày công bố của {early} — số liệu BCTC chỉ dùng từ ngày "
                            "công bố (ADR-0008)")
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
        q = _norm(p["quote"])
        if segs and not any(q in _norm(s) for s in segs):
            errs.append(f"{nid}/{p['id']}: quote không nằm nguyên văn trong chỗ được trỏ tới (L-01)")
        elif segs and len(q) < MIN_QUOTE_CHARS and not any(q == _norm(s) for s in segs):
            errs.append(f"{nid}/{p['id']}: quote dưới {MIN_QUOTE_CHARS} ký tự không đủ để kiểm nguyên văn (L-01)")
        if p["kind"] == "CROSS_TEXT_SYNTHESIS" and len(set(p["addresses"])) < 2:
            errs.append(f"{nid}/{p['id']}: CROSS_TEXT_SYNTHESIS phải dẫn ít nhất hai địa chỉ")
    def addr_exists(a, where):
        m = ADDR_RE.match(a)
        if not m:
            errs.append(f"{nid}: {where} địa chỉ sai dạng {a}"); return
        d, kind, x, y = m.group(1), m.group(2), int(m.group(3)), int(m.group(4))
        if d not in note["doc_ids"]:
            errs.append(f"{nid}: {where} địa chỉ {a} trỏ tới tài liệu ngoài doc_ids")
        elif d in docs and _segment(docs[d], kind, x, y) is None:
            errs.append(f"{nid}: {where} địa chỉ {a} không tồn tại trong library/sources/{d}/text.md")
    for c in note.get("counts") or []:
        for a in c["addresses"]:
            addr_exists(a, "counts")
    if note.get("counts") and not note["self_check"]["counts_from_source"]:
        errs.append(f"{nid}: có counts nhưng self_check.counts_from_source = false (số phải đếm từ nguồn)")
    for fl in note.get("reading_flags") or []:
        for a in fl["addresses"]:
            addr_exists(a, "reading_flags")
    if note["status"] not in FREE_STATUS:
        why = audit_problem(root, note)
        if why:
            errs.append(f"{nid}: {why} (L-09)")
    if note.get("status") in USABLE_NOTE_STATUS:
        for d in note.get("doc_ids") or []:
            src = pathlib.Path(root) / LIB / "sources" / d / "text.md"
            try:
                text = src.read_text(encoding="utf-8") if src.is_file() else None
            except UnicodeError:
                text = None
            pages = (docs.get(d) or ({}, {}))[0] if d in docs else None
            entry = man.get(d) or {}
            if pages is None or not transcription_verified(entry, pages, d, text):
                errs.append(f"{nid}: status {note['status']} không dùng được khi {d} chưa có tệp gốc đã kiểm "
                            "và biên bản đối chiếu PDF từng trang, gồm bảng (L-01)")
            else:
                checker = str(((entry.get("crosscheck") or {}).get("pdf_check") or {}).get("checker") or "")
                if same_provider(checker, note.get("read_by")):
                    errs.append(f"{nid}: ghế đối chiếu PDF trùng ghế đọc ghi chú — không phải cổng độc lập (L-09)")
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
    q = root / LIB / "reading_queue.yaml"
    if q.is_file():
        try:
            items = (yaml.safe_load(q.read_text(encoding="utf-8")) or {}).get("items") or []
        except Exception as e:  # noqa: BLE001
            items = []; errs.append(f"library/reading_queue.yaml đọc lỗi ({str(e).splitlines()[0]})")
        noted = set()
        for p in notes:
            try:
                noted |= set(json.loads(p.read_text(encoding="utf-8")).get("doc_ids") or [])
            except (ValueError, AttributeError):
                pass                                   # ghi chú hỏng đã được báo lỗi ở check_note
        for it in items:
            d, st = it.get("doc_id"), it.get("status")
            if st == "QUEUED" and d in man:
                warns.append(f"reading_queue: {d} đã ghim trong manifest nhưng hàng đợi còn QUEUED")
            if st not in (None, "QUEUED") and d not in man:
                warns.append(f"reading_queue: {d} ghi {st} nhưng chưa có trong SOURCE_MANIFEST.json")
            if st == "NOTE_WRITTEN" and d not in noted:
                warns.append(f"reading_queue: {d} ghi NOTE_WRITTEN nhưng chưa có ghi chú nào dẫn tài liệu này")
            if st == "SOURCED":
                src = root / LIB / "sources" / d / "text.md"
                try:
                    text = src.read_text(encoding="utf-8") if src.is_file() else None
                except UnicodeError:
                    text = None
                pages = (docs.get(d) or ({}, {}))[0]
                if not may_mark_sourced(man.get(d) or {}, pages, d, text):
                    errs.append(f"L-01: reading_queue {d} ghi SOURCED khi chưa đối chiếu đủ từng trang với tệp gốc "
                                "(hash khớp không phải bằng chứng chép đúng)")
                elif origin_binding_errors(root, d, man[d], (root / LIB / "sources" / d / "text.md").read_bytes()):
                    errs.append(f"L-01: reading_queue {d} ghi SOURCED nhưng tệp gốc hoặc metadata không khớp ghim")
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
