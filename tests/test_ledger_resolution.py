"""Phân định dự báo Issue (tools/resolution_intake.py), chấm A–B (engine/ledger.issue_summary), sổ thử L-06 và Deflated Sharpe.
Mọi thứ chạy trong thư mục tạm và tiến trình con: không chạm tệp nào của kho.
"""
import csv, json, math, os, pathlib, shutil, subprocess, sys, tempfile, textwrap, unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import laws_checks  # noqa: E402


def _forecast(seat, question, p, resolve_at="2026-12-31", rule="comparison", author=None):
    f = {"seat": seat, "question": question, "resolution_source": "https://example.org/nguon",
         "resolution_rule": rule, "resolve_at": resolve_at, "p": str(p), "base_rate": "0.5",
         "invalidation_conditions": "Nguồn đổi định nghĩa chỉ tiêu",
         "author_seat": author or ("Claude Project TTC" if seat == "A" else "Claude trần"), "model_cutoff": "2026-06"}
    return "\n\n".join(f"### {k}\n\n{v}" for k, v in f.items())


def _resolution(ids, outcome, resolver="Owner", quote="Tỷ lệ nợ xấu 1,12%", source="https://example.org/bctc",
                void_reason="_No response_"):
    f = {"forecast_ids": ids, "outcome": outcome, "observed_value": "_No response_", "resolution_source": source,
         "quote": quote, "resolver": resolver, "void_reason": void_reason}
    return "\n\n".join(f"### {k}\n\n{v}" for k, v in f.items())


class ResolutionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        (self.tmp / "contracts").mkdir()
        for c in ("forecast_issue.schema.json", "resolution.schema.json"):
            shutil.copy(ROOT / "contracts" / c, self.tmp / "contracts")
        shutil.copytree(ROOT / "tools", self.tmp / "tools", ignore=shutil.ignore_patterns("__pycache__"))
        (self.tmp / "ledger").mkdir()
        q1, q2 = "Nợ nhóm 3-5 của VCB tại 31/12/2026 cao hơn tại 30/9/2026?", "NHNN đổi lãi suất tái cấp vốn trước 31/01/2027?"
        for n, seat, q, p, ra, rule in [(101, "A", q1, 0.30, "2026-12-31", "comparison"),
                                         (102, "B", q1, 0.60, "2026-12-31", "comparison"),
                                         (103, "A", q2, 0.70, "2027-01-31", "event_before_date"),
                                         (104, "B", q2, 0.80, "2027-01-31", "event_before_date")]:
            code, out = self._run("ledger_intake.py", n, _forecast(seat, q, p, ra, rule), "2026-11-17T02:00:00Z")
            self.assertEqual(code, 0, out)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run(self, script, number, body, created):
        env = {**os.environ, "ISSUE_NUMBER": str(number), "ISSUE_CREATED_AT": created, "ISSUE_BODY": body}
        r = subprocess.run([sys.executable, str(self.tmp / "tools" / script)], env=env, capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr

    def _res(self, number, body, created):
        return self._run("resolution_intake.py", number, body, created)

    def _rows(self):
        p = self.tmp / "ledger" / "resolutions.jsonl"
        return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []

    def test_rules_then_ab_scorecard(self):
        c, o = self._res(201, _resolution("F-101, F-102", "NO"), "2026-12-15T03:00:00Z")
        self.assertEqual(c, 2, o); self.assertIn("L-05", o)                      # phân định trước hạn
        for who in ("Claude Opus", "Opus 5.5", "Sonnet", "Anthropic Haiku"):     # cùng nhà với ghế viết, dù không có chữ "claude"
            c, o = self._res(202, _resolution("F-101, F-102", "NO", resolver=who), "2027-01-02T03:00:00Z")
            self.assertEqual(c, 2, o); self.assertIn("L-09", o)
        c, o = self._res(203, _resolution("F-101, F-103", "NO"), "2027-01-02T03:00:00Z")
        self.assertEqual(c, 2, o)                                                # hai câu hỏi khác nhau
        c, o = self._res(204, _resolution("F-101, F-102", "NO", quote="_No response_"), "2027-01-02T03:00:00Z")
        self.assertEqual(c, 2, o)                                                # YES/NO thiếu trích nguyên văn
        # Thêm một dự báo A thứ hai cùng câu hỏi 1 nhưng luật event_before_date: YES sớm phải bị chặn vì câu hỏi có
        # dự báo luật comparison (lỗi "chỉ nhìn targets[0]")
        q1 = "Nợ nhóm 3-5 của VCB tại 31/12/2026 cao hơn tại 30/9/2026?"
        self.assertEqual(self._run("ledger_intake.py", 105, _forecast("A", q1, 0.3, "2026-12-31", "event_before_date"),
                                   "2026-11-17T02:10:00Z")[0], 0)
        c, o = self._res(209, _resolution("F-105", "YES"), "2026-12-20T03:00:00Z")
        self.assertEqual(c, 2, o); self.assertIn("L-05", o)
        # Chỉ liệt kê F-101 nhưng câu hỏi có F-101, F-102, F-105 → ghi cả ba cùng một outcome (một câu hỏi một sự thật)
        c, o = self._res(205, _resolution("F-101", "NO"), "2027-01-02T03:00:00Z")
        self.assertEqual(c, 0, o); self.assertIn("F-102", o); self.assertIn("F-105", o)
        self.assertEqual(self._res(205, _resolution("F-101", "NO"), "2027-01-02T03:00:00Z")[0], 3)         # chạy lại
        c, o = self._res(206, _resolution("F-102", "YES"), "2027-01-03T03:00:00Z")
        self.assertEqual(c, 2, o); self.assertIn("không phân định lại", o)       # không gán sự thật thứ hai cho B
        c, o = self._res(207, _resolution("F-103, F-104", "VOID"), "2027-02-02T03:00:00Z")
        self.assertEqual(c, 2, o)                                                # VOID thiếu lý do
        c, o = self._res(208, _resolution("F-103, F-104", "YES"), "2026-12-20T03:00:00Z")
        self.assertEqual(c, 0, o)                                                # YES của event_before_date (cả câu hỏi) được sớm
        rows = self._rows()
        self.assertEqual([(r["prediction_id"], r["outcome"]) for r in rows],
                         [("F-101", 0), ("F-102", 0), ("F-105", 0), ("F-103", 1), ("F-104", 1)])
        self.assertTrue(all(r["resolver"] == "Owner" and r["quote"] for r in rows))
        self.assertEqual(laws_checks.check_ledger_chain(self.tmp), [])          # resolutions.jsonl có chuỗi hash
        rp = self.tmp / "ledger" / "resolutions.jsonl"
        rp.write_text(rp.read_text(encoding="utf-8").replace('"outcome": 0', '"outcome": 1', 1), encoding="utf-8")
        self.assertTrue(any("phân định" in e for e in laws_checks.check_ledger_chain(self.tmp)))   # sửa kết quả → đỏ
        rp.write_text(rp.read_text(encoding="utf-8").replace('"outcome": 1', '"outcome": 0', 1), encoding="utf-8")
        self.assertEqual(laws_checks.check_ledger_chain(self.tmp), [])

        env = {**os.environ, "TTC_HOME": str(self.tmp), "PYTHONPATH": str(ROOT)}
        code = textwrap.dedent("""
            import json
            from engine import ledger
            print(json.dumps(ledger.scorecard("2027-01-05")["issue_forecasts"], ensure_ascii=False))
        """)
        r = subprocess.run([sys.executable, "-c", code], cwd=str(ROOT), env=env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr[-2000:])
        sc = json.loads(r.stdout.strip().splitlines()[-1])
        self.assertEqual(sc["by_seat"]["A"], {"n": 3, "resolved": 3, "pending": 0})
        self.assertAlmostEqual(sc["scores"]["A"]["brier"], 0.09, places=4)       # ((0,3-0)² + (0,7-1)² + (0,3-0)²)/3 = 0,09
        self.assertAlmostEqual(sc["scores"]["B"]["brier"], 0.2, places=4)        # ((0,6-0)² + (0,8-1)²)/2
        ab = sc["ab"]
        # câu 1: A=[F-101, F-105], B=[F-102] → 1 cặp + 1 lẻ; câu 2: 1 cặp. Bất đồng chỉ ở câu 1 (0,3 vs 0,6).
        self.assertEqual((ab["pairs"], ab["unpaired"], ab["disagreements"], ab["disagreements_resolved"], ab["a_correct"]),
                         (2, 1, 1, 1, 1))
        self.assertEqual(ab["inconsistent_outcomes"], 0)
        self.assertEqual(ab["a_accuracy"], 1.0)
        self.assertEqual(ab["p_value_two_sided_vs_coin"], 1.0)                   # n=1: 2·P(X≥1)=1
        self.assertTrue(ab["verdict"].startswith("CHƯA ĐỦ MẪU (1/194"))
        self.assertEqual(laws_checks.check_ledger_chain(self.tmp), [])


    def test_resolver_must_be_recognised_and_differ_from_every_author(self):
        """L-09: resolver bắt đầu bằng tên ghế; không chung nhà cung cấp với bất kỳ ghế viết nào của câu hỏi."""
        q3 = "Tín dụng năm 2026 tăng từ 15% trở lên?"
        self.assertEqual(self._run("ledger_intake.py", 111, _forecast("A", q3, 0.7), "2026-11-17T02:20:00Z")[0], 0)
        self.assertEqual(self._run("ledger_intake.py", 112, _forecast("B", q3, 0.4, author="ChatGPT trần (OpenAI)"),
                                   "2026-11-17T02:21:00Z")[0], 0)
        when = "2027-01-05T03:00:00Z"
        for who in ("ai đó", "người phân định", "not_an_owner", "kế toán trưởng Owner"):       # không nhận ra ghế
            c, o = self._res(301, _resolution("F-111", "YES", resolver=who), when)
            self.assertEqual(c, 2, o); self.assertIn("L-09", o)
        for who in ("ChatGPT (OpenAI)", "GPT-5.5", "Claude", "Opus 5.5"):                       # trùng một ghế viết của câu hỏi
            c, o = self._res(302, _resolution("F-111", "YES", resolver=who), when)
            self.assertEqual(c, 2, o); self.assertIn("L-09", o)
        self.assertEqual(self._rows(), [])
        c, o = self._res(303, _resolution("F-111", "YES", resolver="Grok (xAI)"), when)         # khác cả hai ghế viết
        self.assertEqual(c, 0, o)
        # câu hỏi 1 chỉ có ghế viết Claude: ChatGPT phân định được
        c, o = self._res(304, _resolution("F-101", "NO", resolver="ChatGPT (OpenAI)"), when)
        self.assertEqual(c, 0, o)

    def test_owner_authored_forecast_cannot_be_resolved_by_owner(self):
        """L-09: Owner cũng là một ghế viết. Dự báo do Owner viết thì Owner không phân định."""
        q4 = "Tỷ giá trung tâm ngày 31/12/2026 từ 25.650 đồng trở lên?"
        self.assertEqual(self._run("ledger_intake.py", 121, _forecast("A", q4, 0.6, author="Owner (Trần Ngọc Thắng)"),
                                   "2026-11-17T02:30:00Z")[0], 0)
        when = "2027-01-05T03:00:00Z"
        for who in ("Owner", "Owner (Trần Ngọc Thắng)", "owner — kiểm lại", "Claude"):
            c, o = self._res(401, _resolution("F-121", "YES", resolver=who), when)
            self.assertEqual(c, 2, o); self.assertIn("L-09", o)
        self.assertEqual(self._rows(), [])
        c, o = self._res(402, _resolution("F-121", "YES", resolver="ChatGPT (OpenAI)"), when)
        self.assertEqual(c, 0, o)

    def test_unrecognised_author_seat_is_refused_at_intake_and_fails_closed_at_resolution(self):
        c, o = self._run("ledger_intake.py", 131, _forecast("A", "Câu hỏi thử có ghế viết lạ?", 0.6, author="ai đó"),
                         "2026-11-17T02:40:00Z")
        self.assertEqual(c, 2, o); self.assertIn("L-09", o)                   # không vào sổ
        # Dòng cũ (giả lập ghi trước khi có luật) có author_seat không nhận ra: phân định đóng lại, kể cả với Owner
        led = self.tmp / "ledger" / "predictions.jsonl"
        row = json.loads(led.read_text(encoding="utf-8").splitlines()[0])
        row.update(id="F-141", issue_number=141, question="Dòng cũ không rõ ghế viết?", author_seat="người viết")
        with led.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        for who in ("Owner", "ChatGPT (OpenAI)"):
            c, o = self._res(501, _resolution("F-141", "NO", resolver=who), "2027-01-05T03:00:00Z")
            self.assertEqual(c, 2, o); self.assertIn("không nhận ra ghế viết", o)
        self.assertEqual(self._rows(), [])


class TwoSidedTests(unittest.TestCase):
    def test_binom_two_sided_matches_sample_size_logic(self):
        sys.path.insert(0, str(ROOT))
        from engine import ledger
        # 109/194 đúng: một phía ≈ 0,049 nhưng hai phía ≈ 0,098 → KHÔNG có ý nghĩa (khớp cỡ mẫu 194 tính hai phía)
        self.assertGreater(ledger._binom_two_sided(109, 194), 0.05)
        self.assertLess(ledger._binom_two_sided(112, 194), 0.05)
        self.assertEqual(ledger._binom_two_sided(0, 0), 1.0)
        self.assertAlmostEqual(ledger._binom_two_sided(2, 4), 1.0)                # đúng nửa → p = 1


class TrialRegistryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        (self.tmp / "research").mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _engine(self, code):
        env = {**os.environ, "TTC_HOME": str(self.tmp), "PYTHONPATH": str(ROOT)}
        r = subprocess.run([sys.executable, "-c", textwrap.dedent(code)], cwd=str(ROOT), env=env,
                           capture_output=True, text=True)
        return r.returncode, r.stdout, r.stderr

    def test_register_before_run_and_check(self):
        code, out, err = self._engine("""
            import json
            from engine import research
            spec = {"features": ["mom_60", "lowvol_20"], "model": "ridge"}
            n = research.next_trial_number(None)
            h1 = research.register_trial(f"T{n:05d}", "2026-11-20", "random_subset", spec, research.threshold(n))
            n2 = research.next_trial_number(None)          # T00001 đăng ký nhưng chưa có kết quả → vẫn được đếm
            try:
                research.register_trial(f"T{n:05d}", "2026-11-20", "random_subset", spec, 3.0)
                dup = False
            except RuntimeError:
                dup = True
            print(json.dumps({"n": n, "n2": n2, "h1": h1, "dup": dup, "spec_id": research.spec_id(spec),
                              "thr": research.threshold(n)}))
        """)
        self.assertEqual(code, 0, err[-2000:])
        d = json.loads(out.strip().splitlines()[-1])
        self.assertEqual((d["n"], d["n2"], d["dup"]), (1, 2, True))
        self.assertEqual(laws_checks.check_trial_registry(self.tmp), [])
        cols = ["trial_id", "cycle_date", "spec_id", "threshold", "registry_hash"]
        old = {"trial_id": "T00000", "cycle_date": "2026-11-20", "spec_id": "M-old", "threshold": "3.6", "registry_hash": ""}
        new = {"trial_id": "T00001", "cycle_date": "2026-11-20", "spec_id": d["spec_id"], "threshold": repr(d["thr"]),
               "registry_hash": d["h1"]}
        with (self.tmp / "research" / "trials.csv").open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerow(old); w.writerow(new)
        self.assertEqual(laws_checks.check_trial_registry(self.tmp), [])        # lần thử cũ (mã trước sổ, kể cả cùng ngày) không bị đòi
        rogue = {"trial_id": "T00002", "cycle_date": "2026-11-20", "spec_id": "M-x", "threshold": "3.7", "registry_hash": ""}
        with (self.tmp / "research" / "trials.csv").open("a", encoding="utf-8", newline="") as f:
            csv.DictWriter(f, fieldnames=cols).writerow(rogue)
        self.assertTrue(any("T00002" in e for e in laws_checks.check_trial_registry(self.tmp)))
        reg = self.tmp / "research" / "trial_registry.jsonl"
        reg.write_text(reg.read_text(encoding="utf-8").replace("random_subset", "cross_family"), encoding="utf-8")
        self.assertTrue(any("hash" in e for e in laws_checks.check_trial_registry(self.tmp)))   # sửa sổ bị bắt

    def test_deflated_sharpe_penalises_many_trials(self):
        code, out, err = self._engine("""
            import json
            from engine import research
            one = research.deflated_sharpe(0.3, 60, 0.0, 3.0, 1, None)
            many = research.deflated_sharpe(0.3, 60, 0.0, 3.0, 210, 0.02)
            many_nohist = research.deflated_sharpe(0.3, 60, 0.0, 3.0, 210, None)     # sổ cũ không có Sharpe → vẫn phải trừ
            v_theory = research.sharpe_variance([], 0.3, 60)
            v_emp = research.sharpe_variance([0.1, -0.2, 0.05, 0.0, 0.3, -0.1, 0.2, 0.15, -0.05, 0.25], 0.3, 60)
            st = research.sharpe_stats([0.01, -0.005, 0.02, 0.0, 0.015, -0.01], 20)
            print(json.dumps({"one": one, "many": many, "many_nohist": many_nohist, "v_theory": v_theory, "v_emp": v_emp, "st": st}))
        """)
        self.assertEqual(code, 0, err[-2000:])
        d = json.loads(out.strip().splitlines()[-1])
        from statistics import NormalDist
        self.assertAlmostEqual(d["one"], NormalDist().cdf(0.3 * math.sqrt(59) / math.sqrt(1 + 0.5 * 0.09)), places=9)
        self.assertLess(d["many"], d["one"])
        self.assertLess(d["many_nohist"], d["one"])                               # không còn SR0 = 0 khi thiếu lịch sử Sharpe
        self.assertAlmostEqual(d["v_theory"], 1 / 59, places=9)
        self.assertGreater(d["v_emp"], 0)
        self.assertEqual(d["st"]["sr_T"], 6)
        self.assertAlmostEqual(d["st"]["sharpe_ann"], d["st"]["sharpe"] * math.sqrt(252 / 20), places=9)


if __name__ == "__main__":
    unittest.main()
