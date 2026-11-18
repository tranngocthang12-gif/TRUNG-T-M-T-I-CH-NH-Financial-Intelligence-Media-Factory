"""Dụng cụ dùng chung cho test: ghim lịch công bố QUA ĐÚNG ĐƯỜNG ROBOT (Issue [Calendar] → tools/resolution_intake.py)
trong thư mục kho tạm, rồi gắn calendar_id vào thân Issue dự báo.

Từ lệnh sửa PR #45 (lỗi 1–2): dự báo mới bắt buộc trích một dòng governance/release_calendar.jsonl do robot ghi, Issue lịch
mở trước Issue dự báo (giờ và số Issue do GitHub cấp). Các test cũ không kiểm thời điểm dùng hàm with_calendar() để có một
lịch hợp lệ; test đối kháng về lịch nằm ở tests/test_timing_lock.py và không dùng đường tắt này.

Tệp này không bắt đầu bằng test_ nên không phải một tệp test riêng (tests.yml chỉ đòi mọi tests/test_*.py nằm trong CI).
"""
import json, os, pathlib, re, subprocess, sys
from datetime import datetime, timedelta

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.laws_checks import same_provider  # noqa: E402
from tools.ledger_intake import parse_issue_form, promised_domains  # noqa: E402

CAL_CREATED = "2026-01-05T00:00:00Z"          # Issue lịch mở trước mọi Issue dự báo trong test


def calendar_body(cid, domains, lock, recorder="Owner", url=None, quote="Lịch phổ biến thông tin thống kê: số liệu được công bố vào ngày đã định."):
    url = url or f"https://{sorted(domains)[0]}/lich-pho-bien-thong-tin"
    f = {"notice": "CALENDAR", "calendar_id": cid, "domains": ", ".join(sorted(domains)), "info_lock_at": lock,
         "evidence_url": url, "quote": quote, "recorder": recorder}
    return "\n\n".join(f"### {k}\n\n{v}" for k, v in f.items())


def run_calendar(tmp, number, body, created=CAL_CREATED, now=None):
    now = now or (datetime.fromisoformat(created.replace("Z", "+00:00")) + timedelta(seconds=60)).isoformat()
    e = {**os.environ, "ISSUE_NUMBER": str(number), "ISSUE_CREATED_AT": created, "ISSUE_BODY": body, "TTC_INTAKE_NOW": now}
    r = subprocess.run([sys.executable, str(pathlib.Path(tmp) / "tools" / "resolution_intake.py")], env=e,
                       capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def _calendar_rows(tmp):
    p = pathlib.Path(tmp) / "governance" / "release_calendar.jsonl"
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.is_file() else []


def calendar_id_for(lock, domains, recorder="Owner"):
    return "CAL-T-" + re.sub(r"[^A-Za-z0-9._-]", "-", f"{lock}-{sorted(domains)[0]}-{recorder.split()[0]}")[:60]


def ensure_calendar(tmp, lock, domains, recorder="Owner"):
    """Ghim (qua robot) một lịch test cho (lock, domains, recorder) nếu chưa có. Trả về calendar_id."""
    cid = calendar_id_for(lock, domains, recorder)
    rows = _calendar_rows(tmp)
    if not any(r.get("calendar_id") == cid for r in rows):
        number = 900001 + len(rows)       # số Issue lịch trong test: không đụng số Issue dự báo/phân định (thứ tự số do kiểm toán GitHub xét)
        code, out = run_calendar(tmp, number, calendar_body(cid, domains, lock, recorder=recorder))
        if code != 0:
            raise AssertionError(f"không ghim được lịch test {cid}: {out}")
    return cid


def _recorder_for(author_seat):
    return "Gemini (Google)" if same_provider("Owner", str(author_seat or "")) else "Owner"


def with_calendar(tmp, body):
    """Thân Issue dự báo đã có calendar_id trỏ tới một lịch robot đã ghim (tạo lịch nếu chưa có). Thân không có
    info_lock_at, hoặc đã trích một lịch không phải lịch test CAL-T-…, thì trả nguyên (để test đối kháng tự quyết)."""
    try:
        data = parse_issue_form(body)
    except ValueError:
        return body
    lock = str(data.get("info_lock_at") or "")
    domains = sorted(promised_domains(data.get("resolution_source")))
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", lock) or not domains:
        return body
    recorder = _recorder_for(data.get("author_seat"))
    if "calendar_id" in data:
        if str(data["calendar_id"]) == calendar_id_for(lock, domains, recorder):
            ensure_calendar(tmp, lock, domains, recorder)
        return body
    return body + f"\n\n### calendar_id\n\n{ensure_calendar(tmp, lock, domains, recorder)}"


def verified_ids(tmp_or_rows):
    """Giả lập kết quả kiểm toán GitHub (tools/ledger_audit.provenance_verified_ids) cho test: mọi dự báo trong sổ tạm."""
    if isinstance(tmp_or_rows, (str, pathlib.Path)):
        p = pathlib.Path(tmp_or_rows) / "ledger" / "predictions.jsonl"
        rows = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.is_file() else []
    else:
        rows = tmp_or_rows
    return sorted(r["id"] for r in rows if r.get("id"))
