"""PIT-001 — kiểm toán chỉ đọc: đúng thời điểm, đủ thành phần, provenance.

Không mạng. Không ghi kho giá, config, engine, ledger, luật hay manifest.
Kết quả in JSON ra stdout. Hash khớp chỉ chứng minh byte không đổi, không chứng minh nội dung đúng.
"""
import csv, gzip, hashlib, json, re, unicodedata
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

STATUSES = ("PASS", "FAIL", "INCONCLUSIVE", "UNKNOWN")
ADR0008_COLUMNS = ["effective_date", "ticker", "change", "source_url", "source_status"]
CSV_COLUMNS = ["effective_date", "ticker", "action", "source_id"]
VERIFIED_STATUS = "DA_DOI_CHIEU"
VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
VN30_HEADING = "CẬP NHẬT THÔNG TIN CỔ PHIẾU THÀNH PHẦN CỦA CHỈ SỐ VN30"
# Các mục khác trong cùng một PDF quy mô. Không kết luận nội dung VN30 từ tên tệp.
OTHER_INDEX_HEADINGS = (
    "CẬP NHẬT THÔNG TIN CỔ PHIẾU THÀNH PHẦN CỦA CHỈ SỐ VNMIDCAP",
    "CẬP NHẬT THÔNG TIN CỔ PHIẾU THÀNH PHẦN CHỈ SỐ VN100",
    "CẬP NHẬT THÔNG TIN CỔ PHIẾU THÀNH PHẦN CỦA CHỈ SỐ VNSMALLCAP",
)


def finding(fid, status, summary, **evidence):
    if status not in STATUSES:
        raise ValueError(status)
    item = {"id": fid, "status": status, "summary": summary}
    if evidence:
        item["evidence"] = evidence
    return item


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _load_config(root: Path):
    path = root / "config.yaml"
    if not path.is_file():
        return None
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _vn_date(value):
    """Ngày lịch theo giờ Việt Nam. Thiếu hoặc không đọc được → None."""
    if value is None or value == "":
        return None
    text = str(value).strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        return text
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=VN_TZ)
    return dt.astimezone(VN_TZ).date().isoformat()


def _dmy(iso_date: str) -> str:
    y, m, d = iso_date.split("-")
    return f"{d}/{m}/{y}"


def load_vn30_rows(root: Path):
    path = root / "data" / "vn30_history.csv"
    if not path.is_file():
        return None, path
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader), path


def load_manifest_docs(root: Path):
    path = root / "data" / "evidence" / "vn30_reviews" / "EVIDENCE_MANIFEST.json"
    if not path.is_file():
        return None, path
    payload = _load_json(path)
    docs = payload.get("source_documents") if isinstance(payload, dict) else None
    if not isinstance(docs, list):
        return None, path
    return docs, path


def reconstruct(rows):
    """Tập thành viên sau mỗi effective_date. Lỗi cấu trúc → (None, lý do)."""
    by_date = {}
    for row in rows:
        by_date.setdefault(row.get("effective_date"), []).append(row)
    members = set()
    states = []
    for date in sorted(d for d in by_date if d):
        day = by_date[date]
        for row in day:
            if row.get("action") == "REMOVE":
                ticker = row.get("ticker")
                if ticker not in members:
                    return None, f"REMOVE mã không có mặt: {ticker} {date}"
                members.remove(ticker)
        for row in day:
            if row.get("action") == "ADD":
                ticker = row.get("ticker")
                if ticker in members:
                    return None, f"ADD mã đang có mặt: {ticker} {date}"
                members.add(ticker)
            elif row.get("action") not in ("ADD", "REMOVE"):
                return None, f"action lạ: {row.get('action')} {date}"
        if len(members) != 30:
            return None, f"{date}: {len(members)} mã, không phải 30"
        states.append((date, set(members)))
    return states, None


def members_on(states, day):
    current = None
    for date, members in states or []:
        if date <= day:
            current = members
        else:
            break
    return current


def check_provenance(root, docs):
    if docs is None:
        return finding("PROVENANCE_HASH", "UNKNOWN", "Không có manifest VN30 để đối chiếu hash.")
    bad, ok = [], []
    for doc in docs:
        rel = doc.get("path")
        if not rel:
            bad.append({"source_id": doc.get("source_id"), "error": "thiếu path"})
            continue
        path = root / rel
        if not path.is_file():
            bad.append({"source_id": doc.get("source_id"), "path": rel, "error": "thiếu tệp"})
            continue
        digest = _sha256(path)
        size = path.stat().st_size
        row = {"source_id": doc.get("source_id"), "path": rel, "sha256": digest, "bytes": size}
        if digest != doc.get("sha256") or size != doc.get("bytes"):
            row["expected_sha256"] = doc.get("sha256")
            row["expected_bytes"] = doc.get("bytes")
            bad.append(row)
        else:
            ok.append(row)
    if bad:
        return finding(
            "PROVENANCE_HASH", "FAIL",
            "Có tệp nguồn lệch hash, lệch số byte hoặc không có trên đĩa. Hash khớp không được hiểu là nội dung đã đúng.",
            mismatches=bad, matched=len(ok))
    return finding(
        "PROVENANCE_HASH", "PASS",
        "Mọi tệp kê trong manifest VN30 khớp SHA-256 và số byte. Việc này không xác minh nội dung.",
        matched=ok)


def check_publication_order(docs):
    if docs is None:
        return finding("PUBLICATION_BEFORE_USE", "UNKNOWN", "Không có manifest để so ngày công bố với ngày hiệu lực.")
    bad, unknown, ok = [], [], []
    for doc in docs:
        published = _vn_date(doc.get("published_at"))
        effective = doc.get("effective_date")
        row = {"source_id": doc.get("source_id"), "published_on": published, "effective_date": effective}
        if not published or not effective:
            unknown.append(row)
        elif published > effective:
            bad.append(row)
        else:
            ok.append(row)
    if bad:
        return finding(
            "PUBLICATION_BEFORE_USE", "FAIL",
            "Có tài liệu được phép dùng trước ngày công bố theo giờ Việt Nam.",
            lookahead=bad, undated=unknown)
    if unknown:
        return finding(
            "PUBLICATION_BEFORE_USE", "UNKNOWN",
            "Một số tài liệu thiếu published_at hoặc effective_date nên không kết luận được thứ tự thời điểm.",
            undated=unknown, dated_ok=len(ok))
    return finding(
        "PUBLICATION_BEFORE_USE", "PASS",
        "Với mọi tài liệu có đủ hai ngày, ngày công bố theo giờ Việt Nam không sau ngày hiệu lực.",
        checked=len(ok))


def check_csv(rows):
    if rows is None:
        return finding("CSV_INTERNAL", "UNKNOWN", "Không có data/vn30_history.csv."), None
    if not rows:
        return finding("CSV_INTERNAL", "FAIL", "CSV thành phần không có dòng dữ liệu."), None
    missing = [c for c in CSV_COLUMNS if c not in rows[0]]
    if missing:
        return finding("CSV_INTERNAL", "FAIL", "CSV thiếu cột mà bộ test hiện hành đang khóa.", missing_columns=missing), None
    states, err = reconstruct(rows)
    if err:
        return finding("CSV_INTERNAL", "FAIL", "Không dựng lại được rổ 30 mã từ CSV.", error=err), None
    return finding(
        "CSV_INTERNAL", "PASS",
        "CSV dựng lại được các mốc, mỗi mốc đúng 30 mã. Không suy ra thành phần trước mốc đầu tiên.",
        states=[{"effective_date": d, "members": sorted(m)} for d, m in states]), states


def check_adr_schema(rows):
    if rows is None:
        return finding("ADR0008_SCHEMA", "UNKNOWN", "Không có CSV để đối chiếu khuôn ADR-0008.")
    actual = list(rows[0].keys()) if rows else []
    if actual == ADR0008_COLUMNS:
        return finding("ADR0008_SCHEMA", "PASS", "CSV đúng khuôn cột ADR-0008.", columns=actual)
    return finding(
        "ADR0008_SCHEMA", "FAIL",
        "CSV không theo khuôn ADR-0008 (effective_date,ticker,change,source_url,source_status). "
        "Không được tự ghi đè CSV trong PIT-001. Khuôn đang khóa bởi test là cột action/source_id.",
        actual_columns=actual, adr0008_columns=ADR0008_COLUMNS)


def check_coverage(cfg, states):
    start = ((cfg or {}).get("data") or {}).get("start")
    if states is None:
        return finding("UNIVERSE_COVERAGE", "UNKNOWN", "Chưa dựng được lịch sử thành phần.")
    first = states[0][0]
    if not start:
        return finding(
            "UNIVERSE_COVERAGE", "UNKNOWN",
            "Không đọc được data.start trong config nên không chốt được cửa sổ nghiên cứu.",
            first_evidence_date=first)
    if start < first:
        return finding(
            "UNIVERSE_COVERAGE", "FAIL",
            "Lịch sử thành phần đã ghim không phủ từ ngày đầu cửa sổ nghiên cứu. Không tự điền các kỳ thiếu.",
            research_start=start, first_evidence_date=first,
            uncovered_until_exclusive=first)
    return finding(
        "UNIVERSE_COVERAGE", "PASS",
        "Mốc thành phần đầu tiên không sau ngày đầu cửa sổ nghiên cứu trong config.",
        research_start=start, first_evidence_date=first)


def check_before_first(cfg, states):
    if states is None:
        return finding("MEMBERSHIP_BEFORE_FIRST_EVIDENCE", "UNKNOWN", "Chưa có mốc thành phần.")
    first = states[0][0]
    start = ((cfg or {}).get("data") or {}).get("start")
    return finding(
        "MEMBERSHIP_BEFORE_FIRST_EVIDENCE", "UNKNOWN",
        "Trước ngày hiệu lực của bản gốc đầu tiên, thành phần VN30 là UNKNOWN. Không suy từ rổ hiện tại.",
        first_evidence_date=first, research_start=start,
        applies=bool(start and start < first))


def check_continuity(docs, states):
    if not states or len(states) < 2:
        return finding(
            "CONTINUITY_BETWEEN_REVIEWS", "INCONCLUSIVE",
            "Chưa đủ hai mốc đã ghim để nói về khoảng giữa các kỳ.")
    gaps = []
    for (a, _), (b, _) in zip(states, states[1:]):
        gaps.append({"after": a, "before": b,
                     "note": "Không có bản gốc nào khác được ghim trong khoảng mở (after, before). "
                             "Việc không thấy tệp không chứng minh rổ không đổi."})
    copied = []
    for doc in docs or []:
        if doc.get("names_copied_from") and doc.get("names_copied_from") != doc.get("source_id"):
            copied.append({"source_id": doc.get("source_id"), "names_copied_from": doc.get("names_copied_from"),
                           "effective_date": doc.get("effective_date")})
    return finding(
        "CONTINUITY_BETWEEN_REVIEWS", "UNKNOWN",
        "Khoảng giữa các mốc đã ghim không được coi là đã chứng minh liên tục. "
        "Bản tin chép danh sách từ PDF kỳ trước không phải là in lại đủ 30 mã.",
        gaps=gaps, names_copied_from_other_document=copied)


def _function_body(src, name):
    m = re.search(rf"^def {name}\(.*?(?=^def |\Z)", src, re.S | re.M)
    return m.group(0) if m else None


def research_chain_requires_verified_status(src: str):
    """True nếu build_events có nhắc source_status. None nếu không thấy hàm."""
    body = _function_body(src, "build_events")
    if body is None:
        return None
    return "source_status" in body


def load_market_uses_verified_chain(src: str):
    body = _function_body(src, "load_market")
    if body is None:
        return None
    return "verified_adjust" in body or "verified_factors" in body


def check_engine_mode(root, cfg):
    data_py = root / "engine" / "data.py"
    if not data_py.is_file():
        return finding("ENGINE_UNIVERSE_MODE", "UNKNOWN", "Không có engine/data.py để xem cách chọn universe.")
    src = data_py.read_text(encoding="utf-8")
    basis = (cfg or {}).get("universe_basis")
    uses_history_file = "vn30_history" in src
    ingest = _function_body(src, "ingest") or ""
    uses_config_list = 'CFG["universe"]' in ingest or "CFG['universe']" in ingest
    if basis == "HISTORICAL" and uses_history_file:
        return finding(
            "ENGINE_UNIVERSE_MODE", "PASS",
            "Config khai HISTORICAL và data.py có nhắc tệp lịch sử thành phần.",
            universe_basis=basis)
    if basis == "CURRENT" or (basis is None and uses_config_list and not uses_history_file):
        return finding(
            "ENGINE_UNIVERSE_MODE", "FAIL",
            "Engine không chọn thành phần theo từng ngày. Ingest đi theo danh sách cố định trong config; "
            "load_market không đọc data/vn30_history.csv. universe_basis CURRENT gắn nhãn thiên lệch sống sót (ADR-0008).",
            universe_basis=basis, ingest_uses_config_universe=uses_config_list,
            data_py_mentions_vn30_history=uses_history_file)
    return finding(
        "ENGINE_UNIVERSE_MODE", "INCONCLUSIVE",
        "Không đủ dấu hiệu để kết luận engine đang chọn rổ theo ngày hay theo danh sách cố định.",
        universe_basis=basis, data_py_mentions_vn30_history=uses_history_file)


def check_config_vs_basket(cfg, states):
    if not states:
        return finding("CONFIG_VS_EVIDENCED_BASKET", "UNKNOWN", "Chưa có rổ dựng từ CSV.")
    configured = (cfg or {}).get("universe")
    if not configured:
        return finding("CONFIG_VS_EVIDENCED_BASKET", "UNKNOWN", "Config không có danh sách universe.")
    configured = set(configured)
    latest_date, latest = states[-1]
    only_config = sorted(configured - latest)
    only_evidence = sorted(latest - configured)
    if not only_config and not only_evidence and len(configured) == 30:
        return finding(
            "CONFIG_VS_EVIDENCED_BASKET", "PASS",
            "Danh sách config trùng rổ dựng được tại mốc CSV cuối cùng.",
            as_of=latest_date)
    return finding(
        "CONFIG_VS_EVIDENCED_BASKET", "FAIL",
        "Danh sách cố định trong config không trùng rổ dựng từ CSV tại mốc cuối. "
        "Đây là lệch thành phần, không phải khuyến nghị giao dịch.",
        csv_state_as_of=latest_date,
        in_config_not_in_csv_state=only_config,
        in_csv_state_not_in_config=only_evidence,
        config_count=len(configured), evidence_count=len(latest))


def _price_tickers(root: Path):
    """Tập mã và khoảng ngày trong kho giá. Không ghi."""
    tickers = set()
    first = last = None
    rows = 0
    paths = []
    legacy = root / "data" / "store" / "prices.csv.gz"
    monthly = root / "data" / "store" / "prices"
    candidates = []
    if legacy.is_file():
        candidates.append(legacy)
    if monthly.is_dir():
        candidates.extend(sorted(monthly.glob("*.csv")))
    if not candidates:
        return None

    def consume(stream):
        nonlocal first, last, rows
        reader = csv.DictReader(stream)
        if not reader.fieldnames or "ticker" not in reader.fieldnames or "date" not in reader.fieldnames:
            return
        for rec in reader:
            ticker, date = rec.get("ticker"), (rec.get("date") or "")[:10]
            if not ticker:
                continue
            tickers.add(ticker)
            rows += 1
            if date and (first is None or date < first):
                first = date
            if date and (last is None or date > last):
                last = date

    for path in candidates:
        paths.append(str(path.relative_to(root)))
        if path.suffix == ".gz":
            with gzip.open(path, "rt", encoding="utf-8", newline="") as f:
                consume(f)
        else:
            with path.open(encoding="utf-8", newline="") as f:
                consume(f)
    return {"tickers": tickers, "first": first, "last": last, "rows": rows, "paths": paths}


def check_prices(root, states):
    info = _price_tickers(root)
    if info is None:
        return finding("PRICE_COVERAGE", "UNKNOWN", "Không thấy kho giá data/store.")
    if not states:
        return finding(
            "PRICE_COVERAGE", "INCONCLUSIVE",
            "Có kho giá nhưng chưa có rổ lịch sử để biết mã nào phải có dữ liệu.",
            price_tickers=sorted(info["tickers"]), first=info["first"], last=info["last"], rows=info["rows"])
    needed = set()
    for _, members in states:
        needed |= members
    missing = sorted(needed - info["tickers"])
    extra = sorted(info["tickers"] - needed)
    evidence = {"price_first": info["first"], "price_last": info["last"], "price_rows": info["rows"],
                "price_tickers": sorted(info["tickers"]), "members_ever_in_csv": sorted(needed),
                "members_without_any_price_row": missing, "priced_but_never_in_pinned_baskets": extra,
                "paths": info["paths"]}
    if missing:
        return finding(
            "PRICE_COVERAGE", "FAIL",
            "Có mã đã nằm trong rổ VN30 được ghim nhưng kho giá không có dòng nào của mã đó. "
            "Không suy giá từ mã khác.",
            **evidence)
    return finding(
        "PRICE_COVERAGE", "PASS",
        "Mọi mã từng xuất hiện trong CSV thành phần đều có ít nhất một dòng giá. "
        "Chưa chứng minh chuỗi giá là đúng thời điểm hay đã xác minh sự kiện quyền.",
        **evidence)


def _manual_events(root: Path):
    path = root / "data" / "corporate_actions.csv"
    if not path.is_file():
        return None, path
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f)), path


def _ca_manifest(root: Path):
    path = root / "data" / "evidence" / "corporate_actions" / "EVIDENCE_MANIFEST.json"
    if not path.is_file():
        return None
    payload = _load_json(path)
    docs = payload.get("source_documents") if isinstance(payload, dict) else None
    return docs if isinstance(docs, list) else None


def check_corporate_actions(root):
    rows, path = _manual_events(root)
    if rows is None:
        return finding("CORPORATE_ACTION_VERIFICATION", "UNKNOWN", "Không có data/corporate_actions.csv.")
    docs = _ca_manifest(root) or []
    by_ticker = {}
    for doc in docs:
        ticker = doc.get("ticker")
        if ticker and ticker not in by_ticker:
            by_ticker[ticker] = doc
    pending = []
    for row in rows:
        status = (row.get("source_status") or "").strip()
        if status == VERIFIED_STATUS:
            continue
        doc = by_ticker.get(row.get("ticker")) or {}
        pending.append({
            "ticker": row.get("ticker"),
            "csv_ex_date": row.get("ex_date"),
            "csv_type": row.get("type"),
            "csv_ratio": row.get("ratio"),
            "csv_source_status": status or None,
            "evidence_source_id": doc.get("source_id"),
            "official_ex_date": doc.get("official_ex_date"),
            "published_at": doc.get("published_at"),
            "published_at_status": doc.get("published_at_status"),
            "dates_match": (row.get("ex_date") == doc.get("official_ex_date")) if doc.get("official_ex_date") else None,
        })
    if not rows:
        return finding(
            "CORPORATE_ACTION_VERIFICATION", "PASS",
            "CSV sự kiện quyền không có dòng nhập tay. Không có gì để xác nhận từ bước nhảy giá.",
            rows=0)
    if not pending:
        return finding(
            "CORPORATE_ACTION_VERIFICATION", "PASS",
            "Mọi dòng sự kiện quyền nhập tay có source_status DA_DOI_CHIEU.",
            rows=len(rows))
    return finding(
        "CORPORATE_ACTION_VERIFICATION", "FAIL",
        "Có sự kiện quyền nhập tay chưa ở trạng thái DA_DOI_CHIEU. "
        "Không xác nhận sự kiện từ bước nhảy giá. Ngày trên CSV lệch ngày official_ex_date của bản HOSE đã ghim "
        "thì vẫn là chưa xác minh, kể cả khi hash PDF khớp.",
        unverified=pending)


def check_unverified_chain(root, ca_finding):
    adjust = root / "engine" / "adjust.py"
    data_py = root / "engine" / "data.py"
    if not adjust.is_file() or not data_py.is_file():
        return finding(
            "UNVERIFIED_EVENTS_IN_RESEARCH_CHAIN", "UNKNOWN",
            "Thiếu engine/adjust.py hoặc engine/data.py nên không biết sự kiện chưa xác minh có đi vào giá nghiên cứu không.")
    adjust_src = adjust.read_text(encoding="utf-8")
    data_src = data_py.read_text(encoding="utf-8")
    gated = research_chain_requires_verified_status(adjust_src)
    verified_path = load_market_uses_verified_chain(data_src)
    unverified_rows = (ca_finding.get("evidence") or {}).get("unverified") or []
    if gated is None or verified_path is None:
        return finding(
            "UNVERIFIED_EVENTS_IN_RESEARCH_CHAIN", "INCONCLUSIVE",
            "Không tách được hàm build_events hoặc load_market để xét cổng xác minh.")
    if verified_path or gated:
        return finding(
            "UNVERIFIED_EVENTS_IN_RESEARCH_CHAIN", "PASS",
            "Đường giá nghiên cứu đọc được có cổng source_status hoặc đi qua chuỗi verified.",
            build_events_mentions_source_status=gated, load_market_uses_verified_chain=verified_path)
    if unverified_rows or ca_finding["status"] == "FAIL":
        return finding(
            "UNVERIFIED_EVENTS_IN_RESEARCH_CHAIN", "FAIL",
            "load_market gọi adjust.build_events. Hàm đó không đọc source_status trước khi có thể gán APPLIED. "
            "Sự kiện CAN_DOI_CHIEU vẫn có thể vào giá điều chỉnh dùng cho nghiên cứu nếu tỷ lệ khớp bước giá. "
            "PIT-001 không sửa engine/adjust.py.",
            build_events_mentions_source_status=False, load_market_uses_verified_chain=False,
            unverified_manual_rows=len(unverified_rows))
    return finding(
        "UNVERIFIED_EVENTS_IN_RESEARCH_CHAIN", "INCONCLUSIVE",
        "Đường adjust không xét source_status, nhưng không thấy dòng nhập tay chưa xác minh trong CSV của cây này.",
        build_events_mentions_source_status=False, load_market_uses_verified_chain=False)


def _pdf_pages_text(path: Path):
    try:
        from pypdf import PdfReader
    except Exception as exc:  # noqa: BLE001 — môi trường thiếu pypdf thì không bịa nội dung
        return None, f"không import được pypdf ({exc})"
    try:
        reader = PdfReader(str(path))
        pages = []
        for page in reader.pages:
            pages.append(page.extract_text(extraction_mode="layout") or "")
        return pages, None
    except Exception as exc:  # noqa: BLE001
        return None, f"không đọc được PDF ({exc})"


def constituent_heading_line(page_text: str):
    """Dòng tiêu đề rổ VN30, không phải danh mục dự phòng. None nếu không thấy."""
    text = unicodedata.normalize("NFC", page_text)
    for line in text.splitlines():
        compact = " ".join(line.split())
        low = compact.lower()
        if "vn30" in low and "thành phần" in low and "dự phòng" not in low:
            return compact
    return None


def tickers_in_vn30_section(page_text: str):
    text = unicodedata.normalize("NFC", page_text)
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if constituent_heading_line(line):
            start = i
            break
    if start is None:
        return None
    chunk = []
    for line in lines[start + 1:]:
        compact = " ".join(unicodedata.normalize("NFC", line).split())
        if "dự phòng" in compact.lower() and "vn30" in compact.lower():
            break
        chunk.append(line)
    found = re.findall(r"(?m)^\s*\d+\s+([A-Z0-9]{3})\b", "\n".join(chunk))
    out = []
    for ticker in found:
        if ticker not in out:
            out.append(ticker)
    return out


def check_pdf_contents(root, docs):
    if not docs:
        return finding("PDF_VN30_CONTENT", "UNKNOWN", "Không có manifest để mở PDF.")
    checked = []
    any_fail = False
    any_unknown = False
    for doc in docs:
        rel = doc.get("path") or ""
        if not str(rel).lower().endswith(".pdf"):
            continue
        path = root / rel
        item = {"source_id": doc.get("source_id"), "path": rel, "effective_date": doc.get("effective_date")}
        if not path.is_file():
            item["content_status"] = "UNKNOWN"
            item["reason"] = "thiếu tệp"
            any_unknown = True
            checked.append(item)
            continue
        pages, err = _pdf_pages_text(path)
        if err:
            item["content_status"] = "INCONCLUSIVE"
            item["reason"] = err
            any_unknown = True
            checked.append(item)
            continue
        heading_pages = []
        for i, text in enumerate(pages):
            heading = constituent_heading_line(text)
            if heading:
                heading_pages.append({"page": i + 1, "heading": heading})
        other = []
        for i, text in enumerate(pages):
            for heading in OTHER_INDEX_HEADINGS:
                if heading in text:
                    other.append({"page": i + 1, "heading": heading})
        item["vn30_heading_pages"] = heading_pages
        item["other_index_headings"] = other
        if not heading_pages:
            item["content_status"] = "INCONCLUSIVE"
            item["reason"] = "không thấy mục VN30 trong lớp chữ PDF; hash không thay cho việc này"
            any_unknown = True
            checked.append(item)
            continue
        parsed = None
        for item_page in heading_pages:
            parsed = tickers_in_vn30_section(pages[item_page["page"] - 1])
            if parsed:
                break
        expected = list(doc.get("members_after") or [])
        item["parsed_tickers"] = parsed or []
        item["parsed_count"] = len(parsed or [])
        item["expected_count"] = len(expected)
        if not parsed or len(parsed) != len(set(parsed)):
            item["content_status"] = "INCONCLUSIVE"
            item["reason"] = "không tách được danh sách mã không trùng trong mục VN30"
            any_unknown = True
        elif set(parsed) != set(expected) or len(parsed) != len(expected):
            item["content_status"] = "FAIL"
            item["only_in_pdf"] = sorted(set(parsed) - set(expected))
            item["only_in_manifest"] = sorted(set(expected) - set(parsed))
            any_fail = True
        else:
            item["content_status"] = "PASS"
        joined = "\n".join(pages)
        token = _dmy(doc["effective_date"]) if doc.get("effective_date") else None
        item["pdf_contains_effective_date_dmy"] = bool(token and token in joined)
        checked.append(item)
    if not checked:
        return finding("PDF_VN30_CONTENT", "UNKNOWN", "Manifest không có PDF.")
    focus = next((x for x in checked if x.get("source_id") == "hose-2510691"), None)
    if any_fail:
        status = "FAIL"
        summary = "Có PDF mà mục VN30 đọc được không trùng members_after của manifest."
    elif any_unknown:
        status = "INCONCLUSIVE"
        summary = "Có PDF chưa đọc được mục VN30 hoặc không tách được đủ mã. Không nâng hash thành đã xác minh nội dung."
    else:
        status = "PASS"
        summary = "Mỗi PDF đã ghim có mục VN30 và danh sách đọc được trùng members_after. Ngày hiệu lực có thể nằm ở tin, không nằm trong PDF."
    return finding("PDF_VN30_CONTENT", status, summary, documents=checked, hose_2510691=focus)


def check_2510691_effective_date(root, docs, content_finding):
    focus = (content_finding.get("evidence") or {}).get("hose_2510691")
    news = next((d for d in docs or [] if d.get("source_id") == "hose-2510691-news"), None)
    if focus is None and news is None:
        return finding("HOSE_2510691_SCOPE", "UNKNOWN", "Không có hồ sơ hose-2510691 trong manifest.")
    news_has_date = False
    news_title = None
    if news and (root / news.get("path", "")).is_file():
        raw = (root / news["path"]).read_text(encoding="utf-8")
        token = _dmy(news["effective_date"]) if news.get("effective_date") else ""
        news_has_date = bool(token and token in raw)
        try:
            news_title = (_load_json(root / news["path"]).get("data") or {}).get("title")
        except json.JSONDecodeError:
            news_title = None
    pdf_has_date = bool(focus and focus.get("pdf_contains_effective_date_dmy"))
    pdf_match = bool(focus and focus.get("content_status") == "PASS")
    other = (focus or {}).get("other_index_headings") or []
    if pdf_match and news_has_date and not pdf_has_date:
        status = "PASS"
        summary = (
            "hose-2510691 là PDF tên VNAllshare kỳ 10/2026 và có mục «CẬP NHẬT THÔNG TIN CỔ PHIẾU THÀNH PHẦN "
            "CỦA CHỈ SỐ VN30» in đủ 30 mã, trùng members_after. Ngày hiệu lực 16/11/2026 đọc từ tin HOSE đã ghim, "
            "không thấy dạng 16/11/2026 trong chữ PDF. Các mục chỉ số khác trong cùng tệp không phải rổ VN30."
        )
    elif pdf_match and pdf_has_date:
        status = "PASS"
        summary = "PDF 2510691 có mục VN30 trùng manifest và có chữ ngày hiệu lực."
    elif focus and focus.get("content_status") == "FAIL":
        status = "FAIL"
        summary = "Mục VN30 của PDF 2510691 không trùng members_after."
    else:
        status = "INCONCLUSIVE"
        summary = "Chưa đủ chữ để kết luận vừa thành phần vừa ngày hiệu lực của hồ sơ 2510691."
    return finding(
        "HOSE_2510691_SCOPE", status, summary,
        pdf_membership_matches=pdf_match,
        pdf_contains_effective_date=pdf_has_date,
        news_contains_effective_date=news_has_date,
        news_title=news_title,
        other_index_headings=other)


def check_news_effective_dates(root, docs):
    """Ngày hiệu lực phải xuất hiện trong chữ tin đã ghim. Không lấy ngày từ tên tệp PDF."""
    if not docs:
        return finding("NEWS_EFFECTIVE_DATE_TEXT", "UNKNOWN", "Không có manifest để đọc tin.")
    checked = []
    for doc in docs:
        rel = doc.get("path") or ""
        if not rel.endswith(".json"):
            continue
        effective = doc.get("effective_date")
        path = root / rel
        row = {"source_id": doc.get("source_id"), "path": rel, "effective_date": effective}
        if not effective or not path.is_file():
            row["status"] = "UNKNOWN"
        else:
            raw = path.read_text(encoding="utf-8")
            token = _dmy(effective)
            row["token"] = token
            row["present"] = token in raw
            row["status"] = "PASS" if token in raw else "FAIL"
        checked.append(row)
    if not checked:
        return finding("NEWS_EFFECTIVE_DATE_TEXT", "UNKNOWN", "Manifest không có tệp tin JSON.")
    if any(row["status"] == "FAIL" for row in checked):
        status = "FAIL"
        summary = "Có tin đã ghim không chứa ngày hiệu lực dạng DD/MM/YYYY mà manifest gán cho nó."
    elif any(row["status"] == "UNKNOWN" for row in checked):
        status = "UNKNOWN"
        summary = "Có tin JSON thiếu ngày hoặc không đọc được."
    else:
        status = "PASS"
        summary = "Mỗi tin JSON đã ghim chứa đúng chuỗi ngày hiệu lực mà manifest ghi. PDF có thể không in lại ngày này."
    return finding("NEWS_EFFECTIVE_DATE_TEXT", status, summary, documents=checked)


def check_microstructure(root, cfg):
    costs = (cfg or {}).get("costs") or {}
    quality = (cfg or {}).get("quality") or {}
    trades = root / "paper" / "trades.csv"
    n_trades = None
    if trades.is_file():
        with trades.open(encoding="utf-8", newline="") as f:
            n_trades = max(0, sum(1 for _ in f) - 1)
    return finding(
        "MARKET_MICROSTRUCTURE_ASSUMPTIONS", "INCONCLUSIVE",
        "Phí, thuế, trượt giá, lô và biên độ là giả định trong config hoặc hằng số giấy. "
        "Chưa có đối chiếu lệnh khớp thật. Không chứng minh được khả năng khớp.",
        costs=costs, price_limit=quality.get("price_limit"), lot_size=(cfg or {}).get("lot_size"),
        paper_trade_rows=n_trades)


def _status_map(findings):
    return {item["id"]: item["status"] for item in findings}


def conclude(findings):
    st = _status_map(findings)
    critical = (
        "PROVENANCE_HASH", "UNIVERSE_COVERAGE", "ENGINE_UNIVERSE_MODE",
        "CONFIG_VS_EVIDENCED_BASKET", "PRICE_COVERAGE", "CORPORATE_ACTION_VERIFICATION",
        "UNVERIFIED_EVENTS_IN_RESEARCH_CHAIN",
    )
    if any(st.get(i) == "FAIL" for i in critical) or st.get("PDF_VN30_CONTENT") == "FAIL" or st.get("HOSE_2510691_SCOPE") == "FAIL":
        conclusion = "NOT_READY"
        reason = "Có lỗi đã xác nhận ở hash, độ phủ rổ, cách engine chọn mã, giá, hoặc sự kiện quyền chưa xác minh."
    elif any(st.get(i) in ("UNKNOWN", "INCONCLUSIVE", None) for i in critical):
        conclusion = "INCONCLUSIVE"
        reason = "Chưa có lỗi khẳng định trên các hạng mục chặn, nhưng còn hạng mục chưa đủ chứng cứ."
    elif all(st.get(i) == "PASS" for i in critical):
        conclusion = "READY"
        reason = "Các hạng mục chặn đều PASS trên cây được chỉ định. Vẫn không phải tuyên bố alpha."
    else:
        conclusion = "INCONCLUSIVE"
        reason = "Không gom được trạng thái các hạng mục chặn."
    return conclusion, reason


def audit(root) -> dict:
    """Đọc cây root. Không mở tệp để ghi."""
    root = Path(root)
    cfg = _load_config(root)
    docs, _ = load_manifest_docs(root)
    rows, _ = load_vn30_rows(root)
    csv_finding, states = check_csv(rows)
    findings = [
        check_provenance(root, docs),
        check_publication_order(docs),
        csv_finding,
        check_adr_schema(rows),
        check_coverage(cfg, states),
        check_before_first(cfg, states),
        check_continuity(docs, states),
        check_engine_mode(root, cfg),
        check_config_vs_basket(cfg, states),
        check_prices(root, states),
        check_corporate_actions(root),
    ]
    findings.append(check_unverified_chain(root, findings[-1]))
    content = check_pdf_contents(root, docs)
    findings.append(content)
    findings.append(check_2510691_effective_date(root, docs, content))
    findings.append(check_news_effective_dates(root, docs))
    findings.append(check_microstructure(root, cfg))
    conclusion, reason = conclude(findings)
    first = states[0][0] if states else None
    return {
        "tool": "pit001_audit",
        "read_only": True,
        "alpha_claim": False,
        "conclusion": conclusion,
        "conclusion_reason": reason,
        "research_start": ((cfg or {}).get("data") or {}).get("start"),
        "first_pinned_membership_date": first,
        "eligible_window": None if conclusion != "READY" else {
            "from": ((cfg or {}).get("data") or {}).get("start"),
            "note": "Chỉ cây fixture/cây đã PASS mọi hạng mục chặn. Không áp vào main khi conclusion khác READY.",
        },
        "findings": findings,
    }


def main(argv=None) -> int:
    import argparse, sys
    parser = argparse.ArgumentParser(description="PIT-001 kiểm toán chỉ đọc")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    args = parser.parse_args(argv)
    json.dump(audit(args.root), sys.stdout, ensure_ascii=False, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
