"""Ứng viên dự báo Sprint 0 không được ghi sổ và không hợp lệ với robot."""
import pathlib
import re
import unittest

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
PATH = ROOT / "reports/G1_DATA_SPRINT0_20261120/A2_CAU_HOI.yaml"
LEDGER_QUESTIONS = {
    "Theo công bố đầu tiên về tình hình kinh tế - xã hội tháng 11/2026 của cơ quan thống kê Việt Nam trên nso.gov.vn, CPI toàn quốc tháng 11/2026 có tăng từ 3,50% trở lên so với tháng 11/2025 không?",
    "Theo công bố đầu tiên về tình hình kinh tế - xã hội tháng 11/2026 trên nso.gov.vn, chỉ số sản xuất công nghiệp toàn quốc tháng 11/2026 có tăng từ 8,00% trở lên so với tháng 11/2025 không?",
    "Theo công bố đầu tiên về tình hình kinh tế - xã hội tháng 11/2026 trên nso.gov.vn, tổng mức bán lẻ hàng hóa và doanh thu dịch vụ tiêu dùng tháng 11/2026 có tăng từ 10,00% trở lên so với tháng 11/2025, theo giá hiện hành, không?",
}
DOMAINS = {"nso.gov.vn", "sbv.gov.vn", "mof.gov.vn", "hsx.vn"}
CAL = re.compile(r"^CAL-[A-Za-z0-9][A-Za-z0-9._-]{2,63}$")


class ForecastCandidates(unittest.TestCase):
    def test_twenty_seven_are_not_booked(self):
        doc = yaml.safe_load(PATH.read_text(encoding="utf-8"))
        self.assertEqual(doc["status"], "KHONG_GHI_SO")
        self.assertNotIn("p", doc)
        rows = doc["questions"]
        self.assertEqual(len(rows), 27)
        self.assertEqual([r["id"] for r in rows], [f"Q-{i:02d}" for i in range(1, 28)])
        for row in rows:
            self.assertNotIn("p", row)
            self.assertNotIn("info_lock_at", row)
            self.assertNotIn("resolve_at", row)
            self.assertIn(row["domain"], DOMAINS)
            self.assertRegex(row["calendar_id"], CAL)
            self.assertGreaterEqual(len(row["yes_if"]), 15)
            self.assertGreaterEqual(len(row["no_if"]), 10)
            self.assertGreaterEqual(len(row["void_if"]), 15)
            self.assertNotIn(row["question"], LEDGER_QUESTIONS)
        ledger = (ROOT / "ledger/predictions.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(ledger), 6)
        blob = "\n".join(ledger)
        for row in rows:
            self.assertNotIn(row["question"], blob)
            self.assertNotIn(row["calendar_id"], blob)


if __name__ == "__main__":
    unittest.main()
