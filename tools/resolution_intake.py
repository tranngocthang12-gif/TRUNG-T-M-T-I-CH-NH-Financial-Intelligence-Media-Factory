"""Nhận một phân định từ GitHub Issue 'Resolution' và ghi vào ledger/resolutions.jsonl (ARCHITECTURE v3.0 §4.1 bước 4, ADR-0003).
Chạy trong workflow resolution_intake.yml. Đầu vào qua biến môi trường:
  ISSUE_NUMBER, ISSUE_CREATED_AT (ISO, giờ máy chủ GitHub), ISSUE_BODY (thân Issue dạng form).
Đầu ra: in JSON {"ok": bool, "message": str}; thoát 0 khi ghi được, 2 khi từ chối (không ghi), 3 khi Issue này đã được ghi, 1 khi lỗi.
Luật:
- Một Issue phân định một câu hỏi: mọi forecast_ids phải là dự báo Issue có trong Ledger, cùng câu hỏi, cùng resolve_at.
- Không phân định trước resolve_at; ngoại lệ duy nhất: YES với luật event_before_date (sự kiện đã xảy ra) (L-05).
- Dự báo đã có phân định thì không phân định lại.
- Người phân định khác nhà cung cấp với người viết: dự báo A và B đều do Claude viết, nên resolver không được là Claude (L-09).
- YES/NO phải có resolution_source và trích nguyên văn (quote) từ nguồn; VOID phải có void_reason.
- Nội dung chứa từ khóa khuyến nghị mua bán → từ chối (L-02).
"""
import json, os, pathlib, re, sys
from datetime import date, datetime

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from tools.laws_checks import recommendation_hit  # noqa: E402
from tools.ledger_intake import parse_issue_form  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
PRED = ROOT / "ledger" / "predictions.jsonl"
RES = ROOT / "ledger" / "resolutions.jsonl"
OUTCOMES = {"YES": 1, "NO": 0, "VOID": None}


def _load(p):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.is_file() else []


def norm_question(q) -> str:
    return re.sub(r"\s+", " ", str(q or "")).strip().lower()


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

    ids = re.findall(r"F-\d+", str(data.get("forecast_ids", "")))
    if not ids:
        return reject("forecast_ids phải liệt kê mã dạng F-<số Issue>, ví dụ F-101, F-102")
    ids = list(dict.fromkeys(ids))
    outcome_key = str(data.get("outcome", "")).strip().upper()
    if outcome_key not in OUTCOMES:
        return reject("outcome phải là YES, NO hoặc VOID")
    resolver = str(data.get("resolver", "")).strip()
    if not resolver:
        return reject("thiếu resolver (ai đã đọc nguồn và phân định)")
    if "claude" in resolver.lower():
        return reject("L-09: dự báo A và B do Claude viết nên Claude không được phân định; người phân định phải là Owner hoặc ghế khác nhà cung cấp")
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
    targets = [preds[i] for i in ids]
    if len({norm_question(p.get("question")) for p in targets}) != 1 or len({p.get("resolve_at") for p in targets}) != 1:
        return reject("các forecast_ids không cùng câu hỏi và cùng resolve_at; mỗi Issue Resolution chỉ phân định một câu hỏi")
    done = {r.get("prediction_id") for r in res_rows}
    already = [i for i in ids if i in done]
    if already:
        return reject(f"{already} đã được phân định trước đó")
    resolve_at = date.fromisoformat(targets[0]["resolve_at"])
    early_ok = outcome_key == "YES" and targets[0].get("resolution_rule") == "event_before_date"
    if created_day < resolve_at and not early_ok:
        return reject(f"L-05: chưa tới resolve_at {resolve_at.isoformat()} (chỉ YES của event_before_date được phân định sớm)")

    rows = []
    for i in ids:
        row = {"prediction_id": i, "resolved_at": created_day.isoformat(), "outcome": OUTCOMES[outcome_key],
               "resolution_issue": number, "resolution_issue_created_at": created, "resolver": resolver,
               "resolution_source": source, "quote": quote}
        if data.get("observed_value"):
            row["observed_value"] = str(data["observed_value"]).strip()
        if outcome_key == "VOID":
            row["void"] = void_reason
        rows.append(row)
    RES.parent.mkdir(parents=True, exist_ok=True)
    with RES.open("a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps({"ok": True, "message": f"Đã phân định {', '.join(ids)}: {outcome_key} (resolver: {resolver})"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
