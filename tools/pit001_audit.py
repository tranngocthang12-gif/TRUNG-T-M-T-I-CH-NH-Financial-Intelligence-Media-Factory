"""PIT-001 — kiểm toán chỉ đọc: đúng thời điểm, đủ thành phần, provenance.

Không mạng. Không ghi kho giá, config, engine, ledger, luật hay manifest.
Kết quả in JSON ra stdout. Hash khớp chỉ chứng minh byte không đổi, không chứng minh nội dung đúng.
"""
import ast, csv, gzip, hashlib, json, re, unicodedata
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


def check_decision_cutoff(docs, cfg):
    """Kiểm tra chính xác phút công bố so với phút ra quyết định theo giờ VN.
    Thiếu lịch quyết định đã đăng ký => INCONCLUSIVE, không lấy ngày hiệu lực thay thế.
    """
    if not docs:
        return finding("DECISION_TIME_OF_KNOWLEDGE", "UNKNOWN",
                       "Không có nguồn để đối chiếu thời điểm công bố.")
    cutoff = ((cfg or {}).get("research") or {}).get("decision_time_local")
    if not isinstance(cutoff, str) or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", cutoff):
        return finding("DECISION_TIME_OF_KNOWLEDGE", "INCONCLUSIVE",
                       "Chưa đăng ký giờ ra quyết định theo ngày giao dịch (research.decision_time_local). "
                       "So published_on <= effective_date không chứng minh có thể dùng ngay trong phiên.",
                       decision_time_local=None)
    bad, unknown, ok = [], [], []
    for doc in docs:
        published, effective = doc.get("published_at"), doc.get("effective_date")
        row = {"source_id": doc.get("source_id"), "published_at": published,
               "effective_date": effective}
        try:
            pub = datetime.fromisoformat(str(published).replace("Z", "+00:00"))
            if pub.tzinfo is None:
                raise ValueError("published_at thiếu timezone")
            decision = datetime.fromisoformat(f"{effective}T{cutoff}:00").replace(tzinfo=VN_TZ)
            row["decision_at_local"] = decision.isoformat()
            row["publication_at_local"] = pub.astimezone(VN_TZ).isoformat()
            (bad if pub > decision else ok).append(row)
        except (ValueError, TypeError):
            unknown.append(row)
    if bad:
        return finding("DECISION_TIME_OF_KNOWLEDGE", "FAIL",
                       "Có nguồn được công bố sau giờ ra quyết định; không thể dùng trong cùng phiên.",
                       late_publications=bad, undated=unknown, verified_before=len(ok))
    if unknown:
        return finding("DECISION_TIME_OF_KNOWLEDGE", "UNKNOWN",
                       "Ngày/giờ nguồn chưa đủ để so với giờ ra quyết định.",
                       undated=unknown, verified_before=len(ok))
    return finding("DECISION_TIME_OF_KNOWLEDGE", "PASS",
                   "Các bản tin trong manifest được công bố trước giờ quyết định giả định đã khai; "
                   "không xác nhận vintage cho toàn bộ giá và BCTC.",
                   checked=len(ok), decision_time_local=cutoff)

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
    if states is None or not states:
        return finding("MEMBERSHIP_BEFORE_FIRST_EVIDENCE", "UNKNOWN", "Chưa có mốc thành phần.")
    first = states[0][0]
    start = ((cfg or {}).get("data") or {}).get("start")
    if not start:
        return finding("MEMBERSHIP_BEFORE_FIRST_EVIDENCE", "UNKNOWN",
                       "Không có ngày đầu nghiên cứu để so với mốc bản gốc.")
    if start < first:
        return finding("MEMBERSHIP_BEFORE_FIRST_EVIDENCE", "UNKNOWN",
                       "Trước ngày hiệu lực của bản gốc đầu tiên, thành phần VN30 là UNKNOWN.",
                       first_evidence_date=first, research_start=start, applies=True)
    return finding("MEMBERSHIP_BEFORE_FIRST_EVIDENCE", "PASS",
                   "Khoảng nghiên cứu không yêu cầu thành phần trước mốc gốc đầu tiên. "
                   "Điều này chưa chứng minh tính liên tục giữa các kỳ.",
                   first_evidence_date=first, research_start=start, applies=False)

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


def _function_ast(src, name):
    """Chỉ xét AST thật; comment hoặc string literal không được tính là hành vi."""
    try:
        module = ast.parse(src)
    except SyntaxError:
        return None
    return next((n for n in module.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                 and n.name == name), None)


def _calls_adjust_build_events(fn):
    return any(
        isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr == "build_events"
        and isinstance(n.func.value, ast.Name)
        and n.func.value.id == "adjust"
        for n in ast.walk(fn)
    )


def research_chain_requires_verified_status(src: str):
    """Dấu hiệu cú pháp, KHÔNG phải chứng minh đã chặn các event chưa xác minh."""
    fn = _function_ast(src, "build_events")
    if fn is None:
        return None
    return any(isinstance(n, ast.Name) and n.id == "source_status"
               for n in ast.walk(fn))


def load_market_uses_verified_chain(src: str):
    """Trả về dấu hiệu gọi hàm verified; không bao giờ tự cấp PASS từ dấu hiệu này."""
    fn = _function_ast(src, "load_market")
    if fn is None:
        return None
    return any(isinstance(n, ast.Call) and (
        (isinstance(n.func, ast.Name) and n.func.id in ("verified_adjust", "verified_factors"))
        or (isinstance(n.func, ast.Attribute)
            and n.func.attr in ("verified_adjust", "verified_factors"))
    ) for n in ast.walk(fn))


def check_engine_mode(root, cfg):
    data_py = root / "engine" / "data.py"
    if not data_py.is_file():
        return finding("ENGINE_UNIVERSE_MODE", "UNKNOWN", "Không có engine/data.py để kiểm tra.")
    basis = (cfg or {}).get("universe_basis")
    fn = _function_ast(data_py.read_text(encoding="utf-8"), "load_market")
    if basis == "CURRENT":
        return finding("ENGINE_UNIVERSE_MODE", "FAIL",
                       "Cấu hình khai CURRENT: không thể chứng nhận chọn universe theo từng ngày.",
                       universe_basis=basis)
    if fn is None:
        return finding("ENGINE_UNIVERSE_MODE", "INCONCLUSIVE",
                       "Không phân tích được hàm load_market; không được tự chứng nhận HISTORICAL.",
                       universe_basis=basis)
    if basis == "HISTORICAL":
        return finding("ENGINE_UNIVERSE_MODE", "INCONCLUSIVE",
                       "HISTORICAL là một khai báo, không chứng minh engine dùng đúng tập thành viên "
                       "từng phiên. Cần kiểm thử hành vi replay với ngày vào/ra và thiếu nguồn.",
                       universe_basis=basis, behavioral_membership_test_verified=False)
    return finding("ENGINE_UNIVERSE_MODE", "INCONCLUSIVE",
                   "Không có bằng chứng hành vi chọn universe theo ngày.", universe_basis=basis)

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
    """Tập mã, các ngày thực có giá và khoảng ngày của kho (chỉ đọc)."""
    tickers, dates_by_ticker, market_dates = set(), {}, set()
    first = last = None
    rows, paths = 0, []
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
            if date:
                dates_by_ticker.setdefault(ticker, set()).add(date)
                market_dates.add(date)
                if first is None or date < first:
                    first = date
                if last is None or date > last:
                    last = date

    for path in candidates:
        paths.append(str(path.relative_to(root)))
        if path.suffix == ".gz":
            with gzip.open(path, "rt", encoding="utf-8", newline="") as f:
                consume(f)
        else:
            with path.open(encoding="utf-8", newline="") as f:
                consume(f)
    return {"tickers": tickers, "dates_by_ticker": dates_by_ticker, "market_dates": market_dates,
            "first": first, "last": last, "rows": rows, "paths": paths}


def check_ticker_presence(info, states):
    if info is None:
        return finding("TICKER_PRESENCE", "UNKNOWN", "Không thấy kho giá data/store.")
    if not states:
        return finding("TICKER_PRESENCE", "INCONCLUSIVE",
                       "Có kho giá nhưng thiếu rổ lịch sử để kiểm tra đủ mã.")
    needed = set().union(*(members for _, members in states))
    missing = sorted(needed - info["tickers"])
    extra = sorted(info["tickers"] - needed)
    details = {"price_first": info["first"], "price_last": info["last"],
               "price_rows": info["rows"], "price_tickers": sorted(info["tickers"]),
               "members_ever_in_csv": sorted(needed), "members_without_any_price_row": missing,
               "priced_but_never_in_pinned_baskets": extra, "paths": info["paths"]}
    if missing:
        return finding("TICKER_PRESENCE", "FAIL",
                       "Có mã từng nằm trong rổ ghim nhưng không có dòng giá.", **details)
    return finding("TICKER_PRESENCE", "PASS",
                   "Mỗi mã trong rổ đã ghim có ít nhất một dòng. KHÔNG chứng nhận đủ chuỗi giá.",
                   **details)


def check_price_window_coverage(info, states, cfg):
    """Độ phủ theo PHIÊN. Không có lịch phiên chính thức/vintage thì không thể PASS."""
    if info is None:
        return finding("PRICE_WINDOW_COVERAGE", "UNKNOWN", "Không thấy kho giá.")
    if not states:
        return finding("PRICE_WINDOW_COVERAGE", "INCONCLUSIVE",
                       "Chưa có thành phần lịch sử để ghép với chuỗi giá từng phiên.")
    horizon = int((cfg or {}).get("horizon_days") or 20)
    lookback = int(((cfg or {}).get("quality") or {}).get("feature_lookback") or 0)
    required = max(2, horizon + 1, lookback + 1)
    needed = set().union(*(m for _, m in states))
    absent = sorted(needed - info["tickers"])
    short = [{"ticker": t, "distinct_sessions": len(info["dates_by_ticker"].get(t, set()))}
             for t in sorted(needed)
             if len(info["dates_by_ticker"].get(t, set())) < required]
    # Các ngày được suy từ GIÁ ĐÃ CÓ, không phải lịch giao dịch chính thức.
    market_days = sorted(info["market_dates"])
    missing_by_period = []
    for k, (effective, members) in enumerate(states):
        end = states[k + 1][0] if k + 1 < len(states) else None
        dates = [d for d in market_days if d >= effective and (end is None or d < end)]
        for ticker in sorted(members):
            gaps = [d for d in dates if d not in info["dates_by_ticker"].get(ticker, set())]
            if gaps and len(missing_by_period) < 40:
                missing_by_period.append({"ticker": ticker, "effective_date": effective,
                                          "missing_session_count": len(gaps), "examples": gaps[:3]})
    details = {"horizon_days": horizon, "feature_lookback": lookback,
               "min_distinct_sessions_for_individual_ticker": required,
               "missing_tickers": absent, "short_series": short[:40],
               "missing_dates_on_observed_market_calendar": missing_by_period,
               "official_exchange_calendar_verified": False}
    if absent or short or missing_by_period:
        return finding("PRICE_WINDOW_COVERAGE", "FAIL",
                       "Thiếu mã, chuỗi quá ngắn hoặc thiếu ngày giá trong phiên có dữ liệu cho mã khác. "
                       "Chưa xét liệu lịch phiên suy từ kho có đầy đủ hay không.", **details)
    return finding("PRICE_WINDOW_COVERAGE", "INCONCLUSIVE",
                   "Các mã có đủ số phiên tối thiểu trong kho quan sát, nhưng chưa có lịch phiên "
                   "chính thức và dữ liệu giá/vintage được xác minh để kết luận độ phủ PIT.", **details)

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
    adjust_path, data_path = root / "engine" / "adjust.py", root / "engine" / "data.py"
    if not adjust_path.is_file() or not data_path.is_file():
        return finding("UNVERIFIED_EVENTS_IN_RESEARCH_CHAIN", "UNKNOWN",
                       "Thiếu engine/adjust.py hoặc engine/data.py.")
    adjust_src = adjust_path.read_text(encoding="utf-8")
    data_src = data_path.read_text(encoding="utf-8")
    build_fn = _function_ast(adjust_src, "build_events")
    market_fn = _function_ast(data_src, "load_market")
    if build_fn is None or market_fn is None:
        return finding("UNVERIFIED_EVENTS_IN_RESEARCH_CHAIN", "INCONCLUSIVE",
                       "Không thể đọc AST hàm build_events/load_market; không tự xác nhận cổng.")
    call = _calls_adjust_build_events(market_fn)
    mention = research_chain_requires_verified_status(adjust_src)
    verified_hint = load_market_uses_verified_chain(data_src)
    unverified_rows = (ca_finding.get("evidence") or {}).get("unverified") or []
    details = {"load_market_calls_adjust_build_events": call,
               "build_events_ast_mentions_source_status": mention,
               "load_market_ast_mentions_verified_function": verified_hint,
               "unverified_manual_rows": len(unverified_rows),
               "behavioral_proof_verified_gate": False}
    if call and not mention and unverified_rows:
        return finding("UNVERIFIED_EVENTS_IN_RESEARCH_CHAIN", "FAIL",
                       "Có sự kiện chưa xác minh, load_market gọi build_events, "
                       "nhưng hàm build_events không đọc source_status. "
                       "Không được cho vào verified-adjusted khi chưa có cổng hành vi.", **details)
    return finding("UNVERIFIED_EVENTS_IN_RESEARCH_CHAIN", "INCONCLUSIVE",
                   "Phân tích AST chỉ là dấu hiệu cú pháp; ngay cả khi source_status/verified_factors "
                   "xuất hiện trong mã, vẫn cần thử hành vi loại CAN_DOI_CHIEU trước khi cấp PASS.",
                   **details)

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
        news_has_date = bool(token and _news_effective_statement(raw, news["effective_date"]))
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


def _news_effective_statement(raw: str, effective_date: str):
    """Chỉ đọc lời công bố trong summary, không tìm ngày ở metadata/comment ngoài."""
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return False
    data = payload.get("data")
    if not isinstance(data, dict) or not isinstance(data.get("summary"), str):
        return False
    summary = re.sub(r"<[^>]+>", " ", data["summary"])
    summary = summary.replace("&nbsp;", " ")
    token = _dmy(effective_date)
    return token in summary and "hiệu lực" in summary.lower()


def check_news_effective_dates(root, docs):
    if not docs:
        return finding("NEWS_EFFECTIVE_DATE_TEXT", "UNKNOWN", "Không có manifest.")
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
            present = _news_effective_statement(path.read_text(encoding="utf-8"), effective)
            row["token"] = _dmy(effective)
            row["present_in_announcement_summary"] = present
            row["status"] = "PASS" if present else "FAIL"
        checked.append(row)
    if not checked:
        return finding("NEWS_EFFECTIVE_DATE_TEXT", "UNKNOWN", "Manifest không có JSON tin.")
    if any(row["status"] == "FAIL" for row in checked):
        return finding("NEWS_EFFECTIVE_DATE_TEXT", "FAIL",
                       "Có bản tin không chứng minh ngày hiệu lực trong lời công bố (summary).",
                       documents=checked)
    if any(row["status"] == "UNKNOWN" for row in checked):
        return finding("NEWS_EFFECTIVE_DATE_TEXT", "UNKNOWN",
                       "Có tin thiếu ngày hoặc không mở được.", documents=checked)
    return finding("NEWS_EFFECTIVE_DATE_TEXT", "PASS",
                   "Các bản tin đã ghim có ngày hiệu lực trong phần summary, không chỉ metadata.",
                   documents=checked)

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
    """Cổng fail-closed: thiếu bất kỳ kiểm tra bắt buộc nào => không READY."""
    st = _status_map(findings)
    critical = (
        "PROVENANCE_HASH", "PUBLICATION_BEFORE_USE", "DECISION_TIME_OF_KNOWLEDGE",
        "CSV_INTERNAL", "ADR0008_SCHEMA", "UNIVERSE_COVERAGE",
        "MEMBERSHIP_BEFORE_FIRST_EVIDENCE", "CONTINUITY_BETWEEN_REVIEWS",
        "ENGINE_UNIVERSE_MODE", "CONFIG_VS_EVIDENCED_BASKET",
        "TICKER_PRESENCE", "PRICE_WINDOW_COVERAGE",
        "CORPORATE_ACTION_VERIFICATION", "UNVERIFIED_EVENTS_IN_RESEARCH_CHAIN",
        "PDF_VN30_CONTENT", "HOSE_2510691_SCOPE", "NEWS_EFFECTIVE_DATE_TEXT",
        "MARKET_MICROSTRUCTURE_ASSUMPTIONS",
    )
    blocked = {k: st.get(k) for k in critical if st.get(k) == "FAIL"}
    unknown = {k: st.get(k) for k in critical
               if st.get(k) in ("INCONCLUSIVE", "UNKNOWN", None)}
    invalid = {k: st.get(k) for k in critical if st.get(k) not in (
        "PASS", "FAIL", "INCONCLUSIVE", "UNKNOWN")}
    if blocked or invalid:
        return "NOT_READY", ("Kiểm tra bắt buộc FAIL/không hợp lệ: "
                             + ", ".join(sorted(set(blocked) | set(invalid))))
    if unknown:
        return "INCONCLUSIVE", ("Chưa đủ chứng cứ để cấp READY: "
                                + ", ".join(sorted(unknown)))
    return "READY", "Tất cả kiểm tra bắt buộc đều PASS; không phải xác nhận alpha."

def audit(root) -> dict:
    """Đọc cây root; không mở tệp để ghi hay nâng chứng cứ."""
    root = Path(root)
    cfg = _load_config(root)
    docs, _ = load_manifest_docs(root)
    rows, _ = load_vn30_rows(root)
    csv_finding, states = check_csv(rows)
    price_info = _price_tickers(root)
    findings = [
        check_provenance(root, docs),
        check_publication_order(docs),
        check_decision_cutoff(docs, cfg),
        csv_finding,
        check_adr_schema(rows),
        check_coverage(cfg, states),
        check_before_first(cfg, states),
        check_continuity(docs, states),
        check_engine_mode(root, cfg),
        check_config_vs_basket(cfg, states),
        check_ticker_presence(price_info, states),
        check_price_window_coverage(price_info, states, cfg),
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
            "note": "Kiểm tra trên cây chỉ định; không phải bằng chứng alpha.",
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
