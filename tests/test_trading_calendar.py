"""Lịch phiên HOSE 2026–2027 (LỆNH D2a). Không mạng. Không ghi kho.

Ngày nghỉ (is_session=0, ngoài thứ Bảy/Chủ nhật) chỉ được ghi khi một tin HOSE đã ghim nguyên byte ghi ngày đó. Năm 2027
chưa có thông báo nghỉ: các ngày quanh ngày lễ giữ is_session=1 với source_id CHUA_CO_THONG_BAO, không đoán ngày nghỉ.
"""
import csv
import datetime as dt
import hashlib
import json
import pathlib
import shutil
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
CSV = ROOT / "data" / "trading_calendar.csv"
EVIDENCE = ROOT / "data" / "evidence" / "calendar"
MANIFEST = EVIDENCE / "CALENDAR_EVIDENCE_MANIFEST.json"
FIRST, LAST = dt.date(2026, 1, 1), dt.date(2027, 12, 31)
SPECIAL = {"WEEKEND", "HOSE_DEFAULT", "CHUA_CO_THONG_BAO"}

# Số phiên từng tháng, đếm từ data/trading_calendar.csv đã đối chiếu với ba tin HOSE. Đổi lịch thì phải sửa bảng này.
SESSIONS = {
    "2026-01": 20, "2026-02": 15, "2026-03": 22, "2026-04": 20, "2026-05": 20, "2026-06": 22,
    "2026-07": 23, "2026-08": 20, "2026-09": 20, "2026-10": 22, "2026-11": 20, "2026-12": 23,
    "2027-01": 21, "2027-02": 20, "2027-03": 23, "2027-04": 22, "2027-05": 21, "2027-06": 22,
    "2027-07": 22, "2027-08": 22, "2027-09": 22, "2027-10": 21, "2027-11": 22, "2027-12": 23,
}
# Ngày nghỉ giao dịch thứ Hai–thứ Sáu năm 2026 theo tin HOSE (đọc tay từ JSON tin và PDF đính kèm, không từ báo chí).
HOLIDAYS_2026 = {
    "2026-01-01": "hose-2426350", "2026-01-02": "hose-2426350",
    "2026-02-16": "hose-2437411", "2026-02-17": "hose-2437411", "2026-02-18": "hose-2437411",
    "2026-02-19": "hose-2437411", "2026-02-20": "hose-2437411", "2026-04-27": "hose-2437411",
    "2026-04-30": "hose-2437411", "2026-05-01": "hose-2437411", "2026-08-31": "hose-2437411",
    "2026-09-01": "hose-2437411", "2026-09-02": "hose-2437411", "2026-11-24": "hose-2513531",
}


def rows(path=CSV):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.reader(f))


def manifest(path=MANIFEST):
    return json.loads(path.read_text(encoding="utf-8"))


def file_errors(root, man):
    """Lỗi sha256/số byte của mọi tệp chứng cứ kê trong manifest, cộng tệp có trên đĩa mà manifest không kê."""
    errors, listed = [], set()
    for doc in man["source_documents"]:
        for f in doc["files"]:
            listed.add(f["path"])
            p = pathlib.Path(root) / f["path"]
            if not p.is_file():
                errors.append(f"thiếu tệp {f['path']}")
                continue
            blob = p.read_bytes()
            if len(blob) != f["bytes"]:
                errors.append(f"{f['path']} bytes {len(blob)} != {f['bytes']}")
            if hashlib.sha256(blob).hexdigest() != f["sha256"]:
                errors.append(f"{f['path']} sha256 lệch")
    base = pathlib.Path(root) / "data" / "evidence" / "calendar"
    for p in base.rglob("*"):
        rel = str(p.relative_to(root))
        if p.is_file() and p.name != MANIFEST.name and rel not in listed:
            errors.append(f"tệp không có trong manifest: {rel}")
    return errors


def calendar_errors(table, man):
    """Kiểm khuôn tệp và mọi dòng theo luật D2a. Trả danh sách lỗi."""
    errors = []
    if not table or table[0] != ["date", "is_session", "source_id"]:
        return ["dòng đầu phải là date,is_session,source_id"]
    body = table[1:]
    want = [str(FIRST + dt.timedelta(days=i)) for i in range((LAST - FIRST).days + 1)]
    if [r[0] for r in body] != want:
        errors.append("cột date phải là mọi ngày từ 2026-01-01 tới 2027-12-31, mỗi ngày một dòng, tăng dần")
    pinned = {d["source_id"]: d for d in man["source_documents"]}
    declared = {day for d in man["source_documents"] for days in d["declares"].values() for day in days}
    flagged = {x["date"] for x in man["chua_co_thong_bao"]["dates"]}
    for r in body:
        if len(r) != 3 or r[1] not in ("0", "1"):
            errors.append(f"{r}: phải có 3 cột và is_session là 0 hoặc 1")
            continue
        day, ses, src = r[0], r[1], r[2]
        weekend = dt.date.fromisoformat(day).weekday() >= 5
        if weekend and (ses, src) != ("0", "WEEKEND"):
            errors.append(f"{day}: thứ Bảy/Chủ nhật phải là 0,WEEKEND")
        if not weekend and src == "WEEKEND":
            errors.append(f"{day}: ngày thường không được ghi WEEKEND")
        if not weekend and ses == "0":
            if src not in pinned:
                errors.append(f"{day}: ngày nghỉ phải trỏ tới tin HOSE đã ghim, đang ghi {src}")
            elif day not in {x for days in pinned[src]["declares"].values() for x in days}:
                errors.append(f"{day}: tin {src} không ghi ngày này là ngày nghỉ")
        if not weekend and ses == "1":
            if src not in ("HOSE_DEFAULT", "CHUA_CO_THONG_BAO"):
                errors.append(f"{day}: phiên giao dịch phải ghi HOSE_DEFAULT hoặc CHUA_CO_THONG_BAO")
            if day in declared:
                errors.append(f"{day}: tin HOSE ghi nghỉ nhưng lịch ghi có phiên")
            if (src == "CHUA_CO_THONG_BAO") != (day in flagged):
                errors.append(f"{day}: CHUA_CO_THONG_BAO phải đúng danh sách chua_co_thong_bao.dates của manifest")
    return errors


class TradingCalendarTests(unittest.TestCase):
    def test_file_format_and_rules(self):
        self.assertEqual(calendar_errors(rows(), manifest()), [])

    def test_every_holiday_points_to_a_pinned_notice(self):
        man = manifest()
        holidays = {r[0]: r[2] for r in rows()[1:] if r[1] == "0" and r[2] != "WEEKEND"}
        self.assertEqual(holidays, HOLIDAYS_2026)
        self.assertEqual({h["date"]: h["source_id"] for h in man["holidays"]}, HOLIDAYS_2026)
        pinned = {d["source_id"]: d for d in man["source_documents"]}
        for day, src in holidays.items():
            doc = pinned[src]
            news = next(f for f in doc["files"] if f["role"] == "tin")
            data = json.loads((ROOT / news["path"]).read_bytes())["data"]
            self.assertEqual(f"hose-{data['id']}", src)
            self.assertIn("lịch nghỉ giao dịch", data["title"])
            self.assertTrue(data["title"].startswith("HOSE:"), src)
            # Ngày đầu và ngày cuối của mỗi đợt nghỉ manifest khai phải in (dd/mm/yyyy) trong chính nội dung tin đã ghim;
            # tin ghi đợt nghỉ dạng "từ … đến hết …", nên ngày giữa đợt không in.
            for days in doc["declares"].values():
                for end in (days[0], days[-1]):
                    self.assertIn(dt.date.fromisoformat(end).strftime("%d/%m/%Y"), data["summary"], (end, src))
                span = (dt.date.fromisoformat(days[-1]) - dt.date.fromisoformat(days[0])).days + 1
                self.assertEqual(span, len(days), (src, days))

    def test_evidence_files_sha256(self):
        self.assertEqual(file_errors(ROOT, manifest()), [])

    def test_sessions_per_month(self):
        got = {}
        for day, ses, _ in rows()[1:]:
            got[day[:7]] = got.get(day[:7], 0) + int(ses)
        self.assertEqual(got, SESSIONS)

    def test_2027_has_no_holiday_and_unannounced_days_are_flagged(self):
        body = rows()[1:]
        self.assertFalse([r for r in body if r[0] >= "2027" and r[1] == "0" and r[2] != "WEEKEND"])
        flagged = [r for r in body if r[2] == "CHUA_CO_THONG_BAO"]
        self.assertTrue(flagged)
        self.assertTrue(all(r[1] == "1" for r in flagged))
        days = {r[0] for r in flagged}
        for must in ("2027-01-01", "2027-02-05", "2027-02-08", "2027-04-16", "2027-04-30", "2027-09-02", "2027-11-24"):
            self.assertIn(must, days)

    def test_rule_violations_are_caught(self):
        man, table = manifest(), rows()
        cases = {
            "ngay_nghi_khong_co_tin": ("2026-03-02", "0", "hose-9999999"),
            "ngay_nghi_tin_khong_ghi": ("2026-03-02", "0", "hose-2437411"),
            "bo_ngay_nghi_hose": ("2026-02-17", "1", "HOSE_DEFAULT"),
            "cuoi_tuan_co_phien": ("2026-01-03", "1", "HOSE_DEFAULT"),
            "nhan_la": ("2026-03-02", "1", "BAO_CHI"),
            "doan_nghi_2027": ("2027-02-08", "0", "CHUA_CO_THONG_BAO"),
            "bo_co_2027": ("2027-02-08", "1", "HOSE_DEFAULT"),
        }
        for name, (day, ses, src) in cases.items():
            bad = [list(r) for r in table]
            i = next(k for k, r in enumerate(bad) if r[0] == day)
            bad[i] = [day, ses, src]
            self.assertTrue(calendar_errors(bad, man), name)
        missing = [list(r) for r in table if r[0] != "2026-06-15"]
        self.assertTrue(calendar_errors(missing, man))
        self.assertTrue(calendar_errors([["ngay", "phien", "nguon"]] + table[1:], man))

    def test_flipping_one_byte_in_a_temp_copy_fails_and_repo_untouched(self):
        before = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            shutil.copytree(EVIDENCE, root / "data" / "evidence" / "calendar")
            man = manifest(root / "data" / "evidence" / "calendar" / MANIFEST.name)
            self.assertEqual(file_errors(root, man), [])
            pdf = root / next(f["path"] for d in man["source_documents"] for f in d["files"] if f["path"].endswith(".pdf"))
            blob = bytearray(pdf.read_bytes())
            blob[200] ^= 0x01
            pdf.write_bytes(blob)
            (root / "data" / "evidence" / "calendar" / "la.json").write_text("{}", encoding="utf-8")
            errors = file_errors(root, man)
            self.assertTrue(any("sha256" in e for e in errors))
            self.assertTrue(any("không có trong manifest" in e for e in errors))
        self.assertEqual(before, subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT))


if __name__ == "__main__":
    unittest.main()
