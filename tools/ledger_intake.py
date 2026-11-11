"""Nhận một dự báo từ GitHub Issue 'Forecast' và ghi vào ledger/predictions.jsonl (ARCHITECTURE v3.0 §4.1).
Chạy trong workflow ledger_intake.yml. Đầu vào qua biến môi trường:
  ISSUE_NUMBER, ISSUE_CREATED_AT (ISO, giờ máy chủ GitHub), ISSUE_BODY (thân Issue dạng form).
Đầu ra: in JSON {"ok": bool, "message": str}; thoát 0 khi ghi được, 2 khi từ chối (không ghi), 3 khi Issue đã có trong Ledger (bỏ qua), 1 khi lỗi.
Luật: thiếu resolution_source, resolve_at đã qua so với ngày tạo Issue, p ngoài [0.05, 0.95] → từ chối (L-05).
"""
import json, os, pathlib, re, sys, hashlib, math
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from tools.laws_checks import line_hash  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
LEDGER = ROOT / "ledger" / "predictions.jsonl"
SCHEMA = ROOT / "contracts" / "forecast_issue.schema.json"
NUMERIC = {"p", "base_rate"}
INTEGERS = {"horizon"}
ALLOWED = {"seat", "question", "resolution_source", "resolution_rule", "ticker", "horizon", "resolve_at", "p", "base_rate", "invalidation_conditions", "author_seat", "model_cutoff", "library_refs", "prompt_hash"}
VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def parse_issue_form(body: str) -> dict:
    """Thân Issue do GitHub sinh từ mẫu: '### <field>\n\n<value>' lặp lại."""
    out, cur = {}, None
    for line in body.splitlines():
        m = re.match(r"^###\s+(.+?)\s*$", line)
        if m:
            cur = m.group(1).strip().lower().replace(" ", "_")
            if cur not in ALLOWED or cur in out:
                raise ValueError("Unexpected or duplicate Issue form heading")
            out[cur] = ""
            continue
        if cur is not None:
            out[cur] = (out[cur] + "\n" + line).strip() if out[cur] else line.strip()
        elif line.strip():
            raise ValueError("Content outside Issue form")
    for k in list(out):
        v = out[k]
        if v in ("_No response_", "None", ""):
            out.pop(k)
        elif k in NUMERIC:
            try:
                n = float(v)
                out[k] = n if math.isfinite(n) else v
            except ValueError:
                pass
        elif k in INTEGERS and re.fullmatch(r"[0-9]+", v):
            out[k] = int(v)
    return out


def main() -> int:
    try:
        number = int(os.environ["ISSUE_NUMBER"])
        created = os.environ["ISSUE_CREATED_AT"]
        updated = os.environ["ISSUE_UPDATED_AT"]
        action = os.environ["ISSUE_ACTION"]
        body = os.environ.get("ISSUE_BODY", "")
        if action != "opened":
            raise ValueError("Only issues.opened is eligible")
        if number < 1 or not body.strip():
            raise ValueError("Missing Issue number or body")
        created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
        updated_dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        if not created_dt.utcoffset() == timedelta(0) or not updated_dt.utcoffset() == timedelta(0):
            raise ValueError("Issue timestamps must have UTC offset")
        if not created_dt <= updated_dt <= created_dt + timedelta(seconds=30):
            raise ValueError("Issue modified after opened event")
        if created_dt > now + timedelta(seconds=30):
            raise ValueError("Issue timestamp is in the future")
        data = parse_issue_form(body)
    except (ValueError, KeyError, TypeError) as e:
        print(json.dumps({"ok": False, "message": f"Rejected Issue: {e}"}, ensure_ascii=False))
        return 2
    try:
        import jsonschema
        jsonschema.validate(data, json.loads(SCHEMA.read_text(encoding="utf-8")))
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"ok": False, "message": f"Từ chối: không khớp forecast_issue.schema.json — {str(e).splitlines()[0]}"}, ensure_ascii=False))
        return 2
    created_day = created_dt.astimezone(VN_TZ).date()
    registered_day = now.astimezone(VN_TZ).date()
    if date.fromisoformat(data["resolve_at"]) <= max(created_day, registered_day):
        print(json.dumps({"ok": False, "message": "Từ chối (L-05): resolve_at phải sau ngày tạo Issue"}, ensure_ascii=False))
        return 2
    prev = "GENESIS"
    if LEDGER.is_file():
        lines = [l for l in LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()]
        # Fail closed before duplicate handling or append: do not extend
        # a ledger whose prior rows or chain have been corrupted.
        validated, previous = [], "GENESIS"
        try:
            for raw_line in lines:
                prior_row = json.loads(raw_line)
                if (prior_row.get("prev_hash") != previous
                        or prior_row.get("hash") != line_hash(prior_row)):
                    raise ValueError("Ledger hash chain integrity failure")
                previous = prior_row["hash"]
                validated.append(prior_row)
        except (ValueError, KeyError, TypeError) as exc:
            print(json.dumps({"ok": False, "message": f"Rejected: {exc}"}, ensure_ascii=False))
            return 2
        if any(row.get("issue_number") == number for row in validated):
            print(json.dumps({"ok": True, "duplicate": True, "message": f"Dự báo #{number} đã có trong Ledger, bỏ qua (không ghi trùng)"}, ensure_ascii=False))
            return 3
        prev = previous
    # Snapshot the full configured basket at acceptance, never derive from later price frames.
    import yaml
    config_path = ROOT / "config.yaml"
    if not config_path.is_file():
        print(json.dumps({"ok": False, "message": "Missing configured benchmark universe"}))
        return 2
    configured = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    basket = configured.get("universe") if isinstance(configured, dict) else None
    if not isinstance(basket, list):
        print(json.dumps({"ok": False, "message": "Invalid configured benchmark universe"}))
        return 2
    if (len(basket) < 2 or len(set(basket)) != len(basket)
            or not all(isinstance(t, str) and re.fullmatch(r"[A-Z0-9]{2,8}", t) for t in basket)):
        print(json.dumps({"ok": False, "message": "Invalid configured benchmark universe"}))
        return 2
    row = {"benchmark_universe": basket, "issue_number": number, "issue_created_at": created,
           "issue_updated_at": updated, "ingest_action": action,
           "registered_at": now.isoformat().replace("+00:00", "Z"),
           "raw_payload_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
           "record_format": "ttc-forecast-issue/v2", **data, "prev_hash": prev}
    row["hash"] = line_hash(row)
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps({"ok": True, "message": f"Đã ghi dự báo #{number} (seat {data['seat']}, p={data['p']}, resolve_at {data['resolve_at']}), hash {row['hash'][:12]}"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
