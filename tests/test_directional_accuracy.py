"""Tỷ lệ đúng hướng khác tỷ lệ YES. Contract dự báo mới bắt info_lock_at và calendar_id.
F-37–F-42 vẫn kiểm lại bằng contract cũ. Brier và mẫu 194 không đổi.
"""
import json, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from engine.ledger import TARGET_DISAGREEMENTS, _freshness, _seat_scores, directional_call_stats  # noqa: E402
from tools import ledger_intake  # noqa: E402


class DirectionTests(unittest.TestCase):
    def test_two_correct_calls_are_not_a_fifty_percent_hit_rate(self):
        # YES với p=0,9 và kết quả YES; NO với p=0,1 (xác suất NO = 0,9) và kết quả NO.
        stats = directional_call_stats([0.9, 0.1], [1, 0])
        self.assertEqual(stats["observed_yes_rate"], 0.5)
        self.assertEqual(stats["directional_accuracy"], 1.0)
        self.assertEqual(stats["directional_n"], 2)
        self.assertEqual(stats["directional_abstain"], 0)
        # Tương thích: khóa cũ hit_rate giữ ĐÚNG giá trị cũ (tỷ lệ YES), có nhãn nghĩa; không phải tỷ lệ đúng (= 1,0 ở đây)
        self.assertEqual(stats["hit_rate"], stats["observed_yes_rate"])
        self.assertIn("KHÔNG phải tỷ lệ dự báo đúng", stats["hit_rate_meaning"])

    def test_two_wrong_calls_are_zero_even_though_half_the_outcomes_are_yes(self):
        stats = directional_call_stats([0.9, 0.1], [0, 1])
        self.assertEqual(stats["directional_accuracy"], 0.0)
        self.assertEqual(stats["observed_yes_rate"], 0.5)

    def test_probability_one_half_is_not_a_direction(self):
        stats = directional_call_stats([0.5, 0.9], [0, 1])
        self.assertEqual(stats["directional_abstain"], 1)
        self.assertEqual(stats["directional_n"], 1)
        self.assertEqual(stats["directional_accuracy"], 1.0)
        only = directional_call_stats([0.5], [1])
        self.assertIsNone(only["directional_accuracy"])
        self.assertEqual(only["directional_n"], 0)
        self.assertEqual(only["observed_yes_rate"], 1.0)

    def test_sign_flip_in_one_cell_changes_accuracy_not_the_brier_formula(self):
        rows = [{"id": "F-1", "p": 0.9, "base_rate": 0.4}, {"id": "F-2", "p": 0.1, "base_rate": 0.4}]
        right = _seat_scores(rows, {"F-1": 1, "F-2": 0})
        wrong = _seat_scores(rows, {"F-1": 0, "F-2": 1})
        self.assertEqual(right["brier"], 0.01)
        self.assertEqual(wrong["brier"], 0.81)
        self.assertEqual(right["directional_accuracy"], 1.0)
        self.assertEqual(wrong["directional_accuracy"], 0.0)
        self.assertEqual(right["observed_yes_rate"], wrong["observed_yes_rate"])
        self.assertEqual(right["brier_base_rate"], wrong["brier_base_rate"])
        self.assertEqual(right["hit_rate"], right["observed_yes_rate"])            # bí danh cũ, cùng số với trước PR
        self.assertEqual(right["calibration"]["0.9-1.0"]["observed_yes_rate"], right["calibration"]["0.9-1.0"]["hit_rate"])
        self.assertEqual(TARGET_DISAGREEMENTS, 194)
        self.assertIn("không phải baseline độc lập", right["baseline_note"])

    def test_freshness_names_the_commit_the_ledgers_and_the_data_date(self):
        fresh = _freshness("2026-11-19", {"scores": {}, "timing_verification_source": "none: test"})
        self.assertEqual(fresh["report_as_of"], "2026-11-19")
        self.assertRegex(fresh["generated_at"], r"^\d{4}-\d{2}-\d{2}T")
        self.assertTrue(fresh["source_commit"] is None or len(fresh["source_commit"]) >= 7)
        pred = fresh["sources"]["ledger/predictions.jsonl"]
        self.assertEqual(pred["rows"], len([l for l in (ROOT / "ledger" / "predictions.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]))
        self.assertRegex(pred["sha256"], r"^[0-9a-f]{64}$")
        self.assertIn("ledger/resolutions.jsonl", fresh["sources"])
        self.assertFalse(fresh["capability_scores_emitted"])
        self.assertIn("STALE", fresh["note"])


class NewForecastContractTests(unittest.TestCase):
    def test_new_schema_requires_the_lock_and_the_old_schema_does_not(self):
        old = json.loads((ROOT / "contracts" / "forecast_issue.schema.json").read_text(encoding="utf-8"))
        new = json.loads((ROOT / "contracts" / "forecast_issue_new.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(set(new["properties"]), set(old["properties"]))
        self.assertEqual(set(new["required"]), set(old["required"]) | {"info_lock_at", "calendar_id"})
        self.assertNotIn("info_lock_at", old["required"])
        self.assertNotIn("calendar_id", old["required"])
        self.assertIn("calendar_id", ledger_intake._schema(legacy=False)["required"])
        self.assertNotIn("calendar_id", ledger_intake._schema(legacy=True)["required"])

    def test_missing_calendar_is_rejected_and_legacy_rows_are_not_rewritten(self):
        data = {"seat": "A", "question": "CPI tháng 12/2026 có tăng từ 3% trở lên không?",
                "resolution_source": "nso.gov.vn", "resolution_rule": "numeric_range", "resolve_at": "2026-12-31",
                "p": 0.4, "base_rate": 0.5, "invalidation_conditions": "Cơ quan thống kê đổi rổ",
                "author_seat": "Claude Project TTC", "model_cutoff": "2026-06", "info_lock_at": "2026-12-20"}
        msg, _ = ledger_intake.forecast_error(data, "2026-11-18T02:00:00Z", [], [])
        self.assertIn("thiếu calendar_id", msg)
        data.pop("info_lock_at")
        data["calendar_id"] = "CAL-NSO-2026-12"
        msg, _ = ledger_intake.forecast_error(data, "2026-11-18T02:00:00Z", [], [])
        self.assertIn("thiếu info_lock_at", msg)
        pred = ledger_intake.load_rows(ROOT / "ledger" / "predictions.jsonl")
        legacy = [r for r in pred if r["id"] in ledger_intake.LEGACY_TIMING_IDS]
        self.assertEqual([r["id"] for r in legacy], [f"F-{n}" for n in range(37, 43)])
        raw = (ROOT / "ledger" / "predictions.jsonl").read_bytes()
        errs = ledger_intake.replay(legacy, [], calendar=[])
        self.assertEqual((ROOT / "ledger" / "predictions.jsonl").read_bytes(), raw)
        self.assertFalse(any("info_lock_at" in e or "calendar_id" in e or "schema" in e for e in errs), errs)


if __name__ == "__main__":
    unittest.main()
