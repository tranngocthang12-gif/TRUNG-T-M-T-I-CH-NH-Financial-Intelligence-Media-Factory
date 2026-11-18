"""L-05 hạn khóa công bố (ADR-0011). Đối kháng: công bố trước resolve_at, nộp sát hạn, chạy lại, ghi trễ, ngày công bố không rõ.
Không sửa F-37–F-42. Không đổi mẫu 194.
"""
import json, os, pathlib, shutil, subprocess, sys, tempfile, unittest
from datetime import datetime, timedelta

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from engine import ledger as engine_ledger  # noqa: E402
from tools import laws_checks, ledger_intake  # noqa: E402

Q = "CPI tháng 12/2026 có tăng từ 3,00% trở lên so với cùng kỳ theo nso.gov.vn không?"


def _just_after(created, seconds=60):
    return (datetime.fromisoformat(created.replace("Z", "+00:00")) + timedelta(seconds=seconds)).isoformat()


def _forecast(seat, question=Q, resolve_at="2026-12-31", lock="2026-12-20", p="0.4"):
    author = "Claude Project TTC" if seat == "A" else "Claude trần"
    f = {"seat": seat, "question": question, "resolution_source": "https://www.nso.gov.vn — thông cáo",
         "resolution_rule": "numeric_range", "resolve_at": resolve_at, "info_lock_at": lock, "p": p, "base_rate": "0.5",
         "invalidation_conditions": "Cơ quan thống kê đổi rổ hoặc năm gốc", "author_seat": author, "model_cutoff": "2026-06"}
    if seat == "B":
        f["prompt_hash"] = ledger_intake.control_b_hash(ROOT / "governance" / "CONTROL_B_PROMPT.md")
    return "\n\n".join(f"### {k}\n\n{v}" for k, v in f.items() if v is not None)


def _pub(ids, published_at, recorder="Owner"):
    f = {"notice": "PUBLICATION", "forecast_ids": ids, "published_at": published_at,
         "evidence_url": "https://www.nso.gov.vn/thong-cao", "quote": "Chỉ số giá tiêu dùng tháng đã được công bố.",
         "recorder": recorder}
    return "\n\n".join(f"### {k}\n\n{v}" for k, v in f.items())


class TimingLockTests(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        (self.tmp / "contracts").mkdir(); (self.tmp / "governance").mkdir(); (self.tmp / "ledger").mkdir()
        for c in ("forecast_issue.schema.json", "resolution.schema.json"):
            shutil.copy(ROOT / "contracts" / c, self.tmp / "contracts")
        for g in ("CONTROL_B_PROMPT.md", "control_b_prompts.jsonl"):
            shutil.copy(ROOT / "governance" / g, self.tmp / "governance")
        shutil.copytree(ROOT / "tools", self.tmp / "tools", ignore=shutil.ignore_patterns("__pycache__"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run(self, script, number, body, created, **env):
        e = {**os.environ, "ISSUE_NUMBER": str(number), "ISSUE_CREATED_AT": created, "ISSUE_BODY": body,
             "TTC_INTAKE_NOW": env.pop("TTC_INTAKE_NOW", _just_after(created)), **env}
        r = subprocess.run([sys.executable, str(self.tmp / "tools" / script)], env=e, capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr

    def test_lock_is_independent_of_resolve_at_and_cannot_be_reset(self):
        c, o = self._run("ledger_intake.py", 501, _forecast("A", lock=None), "2026-11-18T02:00:00Z")
        self.assertEqual(c, 2, o); self.assertIn("thiếu info_lock_at", o)
        c, o = self._run("ledger_intake.py", 502, _forecast("A", lock="2027-01-15"), "2026-11-18T02:00:00Z")
        self.assertEqual(c, 2, o); self.assertIn("không được sau resolve_at", o)
        c, o = self._run("ledger_intake.py", 503, _forecast("A", lock="2026-11-18"), "2026-11-18T02:00:00Z")
        self.assertEqual(c, 2, o); self.assertIn("info_lock_at phải sau ngày tạo", o)
        c, o = self._run("ledger_intake.py", 504, _forecast("A"), "2026-11-18T02:00:00Z")
        self.assertEqual(c, 0, o)
        moved = _forecast("B", p="0.7", lock="2026-12-28")
        c, o = self._run("ledger_intake.py", 505, moved, "2026-11-18T03:00:00Z")
        self.assertEqual(c, 2, o); self.assertIn("không được đặt lại", o)
        c, o = self._run("ledger_intake.py", 505, _forecast("B", p="0.7"), "2026-11-18T03:00:00Z")
        self.assertEqual(c, 0, o)
        # chạy lại không được đổi hạn khóa
        c, o = self._run("ledger_intake.py", 504, _forecast("A", lock="2026-12-25"), "2026-11-18T02:00:00Z")
        self.assertEqual(c, 2, o); self.assertIn("KHÔNG khớp thân Issue", o)
        c, o = self._run("ledger_intake.py", 504, _forecast("A"), "2026-11-18T02:00:00Z")
        self.assertEqual(c, 3, o)

    def test_near_lock_late_rerun_and_early_publication(self):
        early_q = "Bán lẻ tháng 12/2026 có tăng từ 9% trở lên so với cùng kỳ, theo giá hiện hành, không?"
        c, o = self._run("ledger_intake.py", 509, _forecast("A", question=early_q, lock="2026-12-20"), "2026-11-20T02:00:00Z")
        self.assertEqual(c, 0, o)
        # resolve_at còn xa; info_lock là 20/12. 19/12 23:40 giờ VN = 16:40 UTC → sát hạn khóa
        body = _forecast("A", question="IIP tháng 12/2026 có tăng từ 8% trở lên so với cùng kỳ không?", lock="2026-12-20")
        c, o = self._run("ledger_intake.py", 510, body, "2026-12-19T16:40:00Z", TTC_INTAKE_NOW="2026-12-19T16:41:00Z")
        self.assertEqual(c, 2, o); self.assertIn("info_lock_at", o); self.assertNotIn("quá sát ngày resolve_at", o)
        c, o = self._run("ledger_intake.py", 510, body, "2026-12-19T16:00:00Z", TTC_INTAKE_NOW="2026-12-19T16:01:00Z")
        self.assertEqual(c, 0, o)
        c, o = self._run("ledger_intake.py", 511, _forecast("B", question="IIP tháng 12/2026 có tăng từ 8% trở lên so với cùng kỳ không?", p="0.55"),
                         "2026-12-19T16:40:00Z", TTC_INTAKE_NOW="2026-12-19T17:20:00Z")
        self.assertEqual(c, 2, o); self.assertIn("info_lock_at", o)
        # kết quả công bố ngày 6/12, trước resolve_at 31/12 và trước cả Issue dự báo 19/12
        c, o = self._run("resolution_intake.py", 610, _pub("F-510", "2026-12-06T02:00:00Z"), "2026-12-19T18:00:00Z")
        self.assertEqual(c, 0, o)
        late_seat = _forecast("B", question="IIP tháng 12/2026 có tăng từ 8% trở lên so với cùng kỳ không?", p="0.55", lock="2026-12-20")
        c, o = self._run("ledger_intake.py", 512, late_seat, "2026-12-19T02:00:00Z")
        self.assertEqual(c, 2, o); self.assertIn("đã có bằng chứng", o)
        c, o = self._run("resolution_intake.py", 611, _pub("F-510", "2026-12-05T02:00:00Z"), "2026-12-19T19:00:00Z")
        self.assertEqual(c, 2, o); self.assertIn("đã có bằng chứng công bố", o)
        c, o = self._run("resolution_intake.py", 612, _pub("F-509", "2026-12-06"), "2026-12-19T19:00:00Z")
        self.assertEqual(c, 2, o); self.assertIn("không rõ thời điểm", o)
        c, o = self._run("resolution_intake.py", 613, _pub("F-509", "2026-12-21T00:00:00Z"), "2026-12-19T19:00:00Z")
        self.assertEqual(c, 2, o); self.assertIn("tương lai", o)
        rows = [json.loads(l) for l in (self.tmp / "ledger" / "predictions.jsonl").read_text(encoding="utf-8").splitlines()]
        pubs = [json.loads(l) for l in (self.tmp / "ledger" / "publication_evidence.jsonl").read_text(encoding="utf-8").splitlines()]
        by_id = {r["id"]: r for r in rows}
        self.assertEqual(ledger_intake.timing_verification_status(by_id["F-510"], pubs), "after_publication")
        self.assertFalse(ledger_intake.capability_test_eligible(by_id["F-510"], pubs))
        self.assertEqual(ledger_intake.timing_verification_status(by_id["F-509"], pubs), "self_declared_lock")
        self.assertFalse(ledger_intake.capability_test_eligible(by_id["F-509"], pubs))
        self.assertEqual(laws_checks.check_ledger_rows(self.tmp), [])
        self.assertEqual(engine_ledger.TARGET_DISAGREEMENTS, 194)

    def test_legacy_forecasts_stay_pinned_and_are_not_valid_without_proof(self):
        pred = ledger_intake.load_rows(ROOT / "ledger" / "predictions.jsonl")
        ids = [r["id"] for r in pred]
        self.assertEqual(ids, [f"F-{n}" for n in range(37, 43)])
        for r in pred:
            self.assertNotIn("info_lock_at", r)
            self.assertEqual(ledger_intake.timing_verification_status(r, []), "legacy_unproven")
            self.assertFalse(ledger_intake.capability_test_eligible(r, []))
            self.assertEqual(r["hash"], ledger_intake.LEGACY_TIMING_HASHES[r["id"]])
        proven = dict(pred[0])
        pubs = [{"question": proven["question"], "resolve_at": proven["resolve_at"], "published_at": "2026-12-06T02:00:00Z"}]
        self.assertEqual(ledger_intake.timing_verification_status(proven, pubs), "legacy_proven_by_evidence")
        self.assertTrue(ledger_intake.capability_test_eligible(proven, pubs))
        early = [{"question": proven["question"], "resolve_at": proven["resolve_at"], "published_at": "2026-11-18T01:00:00Z"}]
        self.assertEqual(ledger_intake.timing_verification_status(proven, early), "after_publication")
        unclear = [{"question": proven["question"], "resolve_at": proven["resolve_at"], "published_at": "2026-12-06"}]
        self.assertEqual(ledger_intake.timing_verification_status(proven, unclear), "unclear_publication")
        self.assertEqual(laws_checks.check_timing_legacy_pin(ROOT), [])
        self.assertEqual(laws_checks.check_ledger_rows(ROOT), [])
        tampered = self.tmp / "ledger" / "predictions.jsonl"
        shutil.copy(ROOT / "ledger" / "predictions.jsonl", tampered)
        text = tampered.read_text(encoding="utf-8").replace("3,50%", "3,51%", 1)
        tampered.write_text(text, encoding="utf-8")
        self.assertTrue(any("F-37" in e for e in laws_checks.check_timing_legacy_pin(self.tmp)))

    def test_self_declared_lock_is_not_proof_and_late_publication_still_blocks(self):
        """Nộp sau khi đã công bố nhưng trước info_lock_at tự khai, và bằng chứng công bố ghi muộn hơn Issue dự báo."""
        cal = {"calendar_id": "RC-NSO-11", "domains": ["nso.gov.vn"], "info_lock_at": "2026-12-20",
               "evidence_url": "https://www.nso.gov.vn/lich-cong-bo-thang-11",
               "quote": "Số tháng 11 được công bố ngày 20/12/2026.",
               "recorder": "Owner", "recorded_at": "2026-11-01T00:00:00Z"}
        (self.tmp / "governance" / "release_calendar.jsonl").write_text(json.dumps(cal) + "\n", encoding="utf-8")
        body = _forecast("A", question="CPI tháng 11 có tăng từ 3% trở lên so với cùng kỳ không?", lock="2026-12-20")
        cited = body + "\n\n### calendar_id\n\nRC-NSO-11"
        c, o = self._run("ledger_intake.py", 520, cited, "2026-12-07T02:00:00Z")
        self.assertEqual(c, 0, o)
        rows = [json.loads(l) for l in (self.tmp / "ledger" / "predictions.jsonl").read_text(encoding="utf-8").splitlines()]
        row = rows[-1]
        before = json.dumps(row, sort_keys=True)
        self.assertEqual(ledger_intake.timing_verification_status(row, [], [cal]), "eligible")
        # lịch không khớp ngày tự khai thì không nhận
        bad = _forecast("A", question="IIP tháng 11 có tăng từ 8% trở lên so với cùng kỳ không?", lock="2026-12-28")
        c, o = self._run("ledger_intake.py", 521, bad + "\n\n### calendar_id\n\nRC-NSO-11", "2026-12-07T03:00:00Z")
        self.assertEqual(c, 2, o); self.assertIn("không khớp lịch", o)
        # công bố thật ngày 6/12, Issue bằng chứng mở ngày 8/12 — sau dự báo 7/12, nên dòng dự báo không bị viết lại
        c, o = self._run("resolution_intake.py", 620, _pub("F-520", "2026-12-06T01:00:00Z"), "2026-12-08T02:00:00Z")
        self.assertEqual(c, 0, o)
        rows2 = [json.loads(l) for l in (self.tmp / "ledger" / "predictions.jsonl").read_text(encoding="utf-8").splitlines()]
        again = [r for r in rows2 if r["id"] == "F-520"][0]
        self.assertEqual(json.dumps(again, sort_keys=True), before)
        pubs = [json.loads(l) for l in (self.tmp / "ledger" / "publication_evidence.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(ledger_intake.timing_verification_status(again, pubs, [cal]), "after_publication")
        self.assertFalse(ledger_intake.capability_test_eligible(again, pubs, [cal]))
        self.assertEqual(ledger_intake.forecast_error(
            {k: v for k, v in again.items() if k not in ledger_intake.SYSTEM_FIELDS},
            again["issue_created_at"], [], [], live=False, pub_rows=pubs, calendar=[cal])[0], None)
        self.assertEqual(laws_checks.check_ledger_rows(self.tmp), [])
        same = dict(cal, calendar_id="RC-SAME", recorder="Claude Project TTC")
        late_cal = dict(cal, calendar_id="RC-LATE", recorded_at="2026-12-08T00:00:00Z")
        (self.tmp / "governance" / "release_calendar.jsonl").write_text(
            "\n".join(json.dumps(x, ensure_ascii=False) for x in (cal, same, late_cal)) + "\n", encoding="utf-8")
        c, o = self._run("ledger_intake.py", 522,
                         _forecast("A", question="Xuất khẩu tháng 11 có tăng từ 8% trở lên so với cùng kỳ không?", lock="2026-12-20")
                         + "\n\n### calendar_id\n\nRC-SAME", "2026-12-07T04:00:00Z")
        self.assertEqual(c, 2, o); self.assertIn("không độc lập", o)
        c, o = self._run("ledger_intake.py", 523,
                         _forecast("A", question="Nhập khẩu tháng 11 có tăng từ 8% trở lên so với cùng kỳ không?", lock="2026-12-20")
                         + "\n\n### calendar_id\n\nRC-LATE", "2026-12-07T05:00:00Z")
        self.assertEqual(c, 2, o); self.assertIn("không đứng trước", o)
        self.assertEqual(laws_checks.check_ledger_rows(self.tmp), [])


if __name__ == "__main__":
    unittest.main()
