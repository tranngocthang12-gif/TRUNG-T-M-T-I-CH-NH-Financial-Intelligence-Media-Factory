"""Nhận một dự báo từ GitHub Issue 'Forecast' và ghi vào ledger/predictions.jsonl (ARCHITECTURE v3.0 §4.1).
Chạy trong workflow ledger_intake.yml. Đầu vào qua biến môi trường:
  ISSUE_NUMBER, ISSUE_CREATED_AT (ISO, giờ máy chủ GitHub), ISSUE_BODY (thân Issue dạng form).
Đầu ra: in JSON {"ok": bool, "message": str}; thoát 0 khi ghi được, 2 khi từ chối (không ghi), 3 khi Issue đã có trong Ledger (bỏ qua), 1 khi lỗi.
Luật: thiếu resolution_source, resolve_at đã qua so với ngày tạo Issue, p ngoài [0.05, 0.95] → từ chối (L-05).
"""
import json, os, pathlib, re, sys
from datetime import date, datetime

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from tools.laws_checks import line_hash  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
LEDGER = ROOT / "ledger" / "predictions.jsonl"
SCHEMA = ROOT / "contracts" / "forecast_issue.schema.json"
NUMERIC = {"p", "base_rate"}


def parse_issue_form(body: str) -> dict:
    """Thân Issue do GitHub sinh từ mẫu: '### <field>\n\n<value>' lặp lại."""
    out, cur = {}, None
    for line in body.splitlines():
        m = re.match(r"^###\s+(.+?)\s*$", line)
        if m:
            cur = m.group(1).strip().lower().replace(" ", "_")
            out[cur] = ""
            continue
        if cur is not None:
            out[cur] = (out[cur] + "\n" + line).strip() if out[cur] else line.strip()
    for k in list(out):
        v = out[k]
        if v in ("_No response_", "None", ""):
            out.pop(k)
        elif k in NUMERIC:
            try:
                out[k] = float(v)
            except ValueError:
                pass
    return out


def main() -> int:
    number = int(os.environ["ISSUE_NUMBER"])
    created = os.environ["ISSUE_CREATED_AT"]
    body = os.environ.get("ISSUE_BODY", "")
    data = parse_issue_form(body)
    try:
        import jsonschema
        jsonschema.validate(data, json.loads(SCHEMA.read_text(encoding="utf-8")))
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"ok": False, "message": f"Từ chối: không khớp forecast_issue.schema.json — {str(e).splitlines()[0]}"}, ensure_ascii=False))
        return 2
    created_day = datetime.fromisoformat(created.replace("Z", "+00:00")).date()
    if date.fromisoformat(data["resolve_at"]) <= created_day:
        print(json.dumps({"ok": False, "message": "Từ chối (L-05): resolve_at phải sau ngày tạo Issue"}, ensure_ascii=False))
        return 2
    prev = "GENESIS"
    if LEDGER.is_file():
        lines = [l for l in LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()]
        if any(json.loads(l).get("issue_number") == number for l in lines):
            print(json.dumps({"ok": True, "duplicate": True, "message": f"Dự báo #{number} đã có trong Ledger, bỏ qua (không ghi trùng)"}, ensure_ascii=False))
            return 3
        if lines:
            prev = json.loads(lines[-1])["hash"]
    row = {"issue_number": number, "issue_created_at": created, **data, "prev_hash": prev}
    row["hash"] = line_hash(row)
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps({"ok": True, "message": f"Đã ghi dự báo #{number} (seat {data['seat']}, p={data['p']}, resolve_at {data['resolve_at']}), hash {row['hash'][:12]}"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
