"""Nhận một phân định từ GitHub Issue 'Resolution' và ghi vào ledger/resolutions.jsonl (ARCHITECTURE v3.0 §4.1 bước 4, ADR-0003).
Chạy trong workflow resolution_intake.yml. Đầu vào qua biến môi trường:
  ISSUE_NUMBER, ISSUE_CREATED_AT (ISO, giờ máy chủ GitHub), ISSUE_BODY (thân Issue dạng form).
Đầu ra: in JSON {"ok": bool, "message": str}; thoát 0 khi ghi được, 2 khi từ chối (không ghi), 3 khi Issue này đã được ghi, 1 khi lỗi.
Luật:
- Một Issue phân định MỘT CÂU HỎI, và phân định cho MỌI dự báo Issue của câu hỏi đó (cùng question + resolve_at), dù
  forecast_ids chỉ liệt kê một phần: một câu hỏi chỉ có một sự thật, A và B nhận cùng outcome.
- Câu hỏi đã có bất kỳ dự báo nào được phân định thì không phân định lại (kể cả VOID).
- Không phân định trước resolve_at; ngoại lệ duy nhất: YES khi MỌI dự báo của câu hỏi có luật event_before_date (L-05).
- Người phân định khác nhà cung cấp với người viết: dự báo A và B đều do Claude (Anthropic) viết, nên resolver không được
  thuộc Anthropic theo bảng nhà cung cấp dùng chung tools/laws_checks.PROVIDERS (L-09).
- YES/NO phải có resolution_source và trích nguyên văn (quote); VOID phải có void_reason.
- Nội dung chứa từ khóa khuyến nghị mua bán → từ chối (L-02).
- Mỗi dòng ghi theo contracts/resolution.schema.json, nối hash chuỗi (prev_hash/hash) như predictions.jsonl.
"""
import json, os, pathlib, re, sys
from datetime import date, datetime

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from tools.laws_checks import line_hash, recommendation_hit, _providers  # noqa: E402
from tools.ledger_intake import parse_issue_form  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
PRED = ROOT / "ledger" / "predictions.jsonl"
RES = ROOT / "ledger" / "resolutions.jsonl"
SCHEMA = ROOT / "contracts" / "resolution.schema.json"
OUTCOMES = {"YES": 1, "NO": 0, "VOID": None}
AUTHOR_PROVIDER = "anthropic"            # ghế viết dự báo A và B


def _load(p):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.is_file() else []


def norm_question(q) -> str:
    return re.sub(r"\s+", " ", str(q or "")).strip().lower()


def qkey(p):
    return (norm_question(p.get("question")), str(p.get("resolve_at", "")))


def reject(msg) -> int:
    print(json.dumps({"ok": False, "message": f"Từ chối: {msg}"}, ensure_ascii=False))
    return 2


def main() -> int:
    number = int(os.environ["ISSUE_NUMBER"])
    created = os.environ["ISSUE_CREATED_AT"]
    data = parse_issue_form(os.environ.get("ISSUE_BODY", ""))
    created_day = datetime.fromisoformat(created.replace("Z", "+00:00")).date()

    res_rows = _load(RES)
    if any(r.get("resolution_issue") == number for r in res_rows):
        print(json.dumps({"ok": True, "duplicate": True, "message": f"Phân định #{number} đã có trong Ledger, bỏ qua"}, ensure_ascii=False))
        return 3

    ids = list(dict.fromkeys(re.findall(r"F-\d+", str(data.get("forecast_ids", "")))))
    if not ids:
        return reject("forecast_ids phải liệt kê mã dạng F-<số Issue>, ví dụ F-101, F-102")
    outcome_key = str(data.get("outcome", "")).strip().upper()
    if outcome_key not in OUTCOMES:
        return reject("outcome phải là YES, NO hoặc VOID")
    resolver = str(data.get("resolver", "")).strip()
    if not resolver:
        return reject("thiếu resolver (ai đã đọc nguồn và phân định)")
    if AUTHOR_PROVIDER in _providers(resolver):
        return reject(f"L-09: '{resolver}' cùng nhà cung cấp với ghế viết dự báo (Anthropic); người phân định phải là Owner hoặc ghế khác nhà")
    source, quote, void_reason = (str(data.get(k, "")).strip() for k in ("resolution_source", "quote", "void_reason"))
    if outcome_key == "VOID":
        if not void_reason:
            return reject("VOID phải có void_reason")
    elif not source or not quote:
        return reject("YES/NO phải có resolution_source và trích nguyên văn (quote) từ nguồn")
    hit = recommendation_hit(json.dumps(data, ensure_ascii=False))
    if hit:
        return reject(f"L-02: nội dung chứa từ khóa khuyến nghị '{hit}'")

    preds = {p.get("id"): p for p in _load(PRED) if "issue_number" in p}
    missing = [i for i in ids if i not in preds]
    if missing:
        return reject(f"không có dự báo Issue {missing} trong ledger/predictions.jsonl")
    keys = {qkey(preds[i]) for i in ids}
    if len(keys) != 1:
        return reject("các forecast_ids không cùng câu hỏi và cùng resolve_at; mỗi Issue Resolution chỉ phân định một câu hỏi")
    key = keys.pop()
    group = sorted((p for p in preds.values() if qkey(p) == key), key=lambda p: p.get("issue_number", 0))
    group_ids = [p["id"] for p in group]
    done = {r.get("prediction_id") for r in res_rows}
    already = [i for i in group_ids if i in done]
    if already:
        return reject(f"câu hỏi này đã được phân định ({', '.join(already)}); không phân định lại")
    resolve_at = date.fromisoformat(group[0]["resolve_at"])
    early_ok = outcome_key == "YES" and all(p.get("resolution_rule") == "event_before_date" for p in group)
    if created_day < resolve_at and not early_ok:
        return reject(f"L-05: chưa tới resolve_at {resolve_at.isoformat()} (chỉ YES được phân định sớm, và chỉ khi mọi dự báo của câu hỏi có luật event_before_date)")

    try:
        import jsonschema
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    except ImportError:
        jsonschema = schema = None
    prev = res_rows[-1]["hash"] if res_rows and "hash" in res_rows[-1] else "GENESIS"
    rows = []
    for i in group_ids:
        row = {"prediction_id": i, "resolved_at": created_day.isoformat(), "outcome": OUTCOMES[outcome_key],
               "resolution_issue": number, "resolution_issue_created_at": created, "resolver": resolver,
               "resolution_source": source, "quote": quote}
        if data.get("observed_value"):
            row["observed_value"] = str(data["observed_value"]).strip()
        if outcome_key == "VOID":
            row["void"] = void_reason
        if jsonschema is not None:
            try:
                jsonschema.validate(row, schema)
            except Exception as e:  # noqa: BLE001
                return reject(f"không khớp resolution.schema.json — {str(e).splitlines()[0]}")
        row["prev_hash"] = prev
        row["hash"] = line_hash(row)
        prev = row["hash"]
        rows.append(row)
    RES.parent.mkdir(parents=True, exist_ok=True)
    with RES.open("a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    extra = [i for i in group_ids if i not in ids]
    note = f" (gồm cả {', '.join(extra)} — cùng câu hỏi)" if extra else ""
    print(json.dumps({"ok": True, "message": f"Đã phân định {', '.join(group_ids)}: {outcome_key} (resolver: {resolver}){note}"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
