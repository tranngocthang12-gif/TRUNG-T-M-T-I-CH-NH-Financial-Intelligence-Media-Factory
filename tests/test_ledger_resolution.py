"""Phân định dự báo Issue (tools/resolution_intake.py), chấm A–B (engine/ledger.issue_summary), sổ thử L-06 và Deflated Sharpe.
Mọi thứ chạy trong thư mục tạm và tiến trình con: không chạm tệp nào của kho.
"""
import csv, json, math, os, pathlib, shutil, subprocess, sys, tempfile, textwrap, unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import laws_checks  # noqa: E402


def _forecast(seat, question, p, resolve_at="2026-12-31", rule="comparison"):
    f = {"seat": seat, "question": question, "resolution_source": "https://example.org/nguon",
         "resolution_rule": rule, "resolve_at": resolve_at, "p": str(p), "base_rate": "0.5",
         "invalidation_conditions": "Nguồn đổi định nghĩa chỉ tiêu",
         "author_seat": "Claude Project TTC" if seat == "A" else "Claude trần", "model_cutoff": "2026-06"}
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
        shutil.copy(ROOT / "contracts" / "forecast_issue.schema.json", self.tmp / "contracts")
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
        c, o = self._res(202, _resolution("F-101, F-102", "NO", resolver="Claude Opus"), "2027-01-02T03:00:00Z")
        self.assertEqual(c, 2, o); self.assertIn("L-09", o)                      # người viết cùng nhà
        c, o = self._res(203, _resolution("F-101, F-103", "NO"), "2027-01-02T03:00:00Z")
        self.assertEqual(c, 2, o)                                                # hai câu hỏi khác nhau
        c, o = self._res(204, _resolution("F-101, F-102", "NO", quote="_No response_"), "2027-01-02T03:00:00Z")
        self.assertEqual(c, 2, o)                                                # YES/NO thiếu trích nguyên văn
        c, o = self._res(205, _resolution("F-101, F-102", "NO"), "2027-01-02T03:00:00Z")
        self.assertEqual(c, 0, o)
        self.assertEqual(self._res(205, _resolution("F-101, F-102", "NO"), "2027-01-02T03:00:00Z")[0], 3)   # chạy lại
        c, o = self._res(206, _resolution("F-101", "YES"), "2027-01-03T03:00:00Z")
        self.assertEqual(c, 2, o)                                                # đã phân định rồi
        c, o = self._res(207, _resolution("F-103, F-104", "VOID"), "2027-02-02T03:00:00Z")
        self.assertEqual(c, 2, o)                                                # VOID thiếu lý do
        c, o = self._res(208, _resolution("F-103, F-104", "YES"), "2026-12-20T03:00:00Z")
        self.assertEqual(c, 0, o)                                                # YES của event_before_date được sớm
        rows = self._rows()
        self.assertEqual([(r["prediction_id"], r["outcome"]) for r in rows],
                         [("F-101", 0), ("F-102", 0), ("F-103", 1), ("F-104", 1)])
        self.assertTrue(all(r["resolver"] == "Owner" and r["quote"] for r in rows))

        env = {**os.environ, "TTC_HOME": str(self.tmp), "PYTHONPATH": str(ROOT)}
        code = textwrap.dedent("""
            import json
            from engine import ledger
            print(json.dumps(ledger.scorecard("2027-01-05")["issue_forecasts"], ensure_ascii=False))
        """)
        r = subprocess.run([sys.executable, "-c", code], cwd=str(ROOT), env=env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr[-2000:])
        sc = json.loads(r.stdout.strip().splitlines()[-1])
        self.assertEqual(sc["by_seat"]["A"], {"n": 2, "resolved": 2, "pending": 0})
        self.assertAlmostEqual(sc["scores"]["A"]["brier"], 0.09, places=4)       # ((0,3-0)² + (0,7-1)²)/2
        self.assertAlmostEqual(sc["scores"]["B"]["brier"], 0.2, places=4)        # ((0,6-0)² + (0,8-1)²)/2
        ab = sc["ab"]
        self.assertEqual((ab["pairs"], ab["disagreements"], ab["disagreements_resolved"], ab["a_correct"]), (2, 1, 1, 1))
        self.assertEqual(ab["a_accuracy"], 1.0)
        self.assertEqual(ab["p_value_a_better_than_coin"], 0.5)
        self.assertTrue(ab["verdict"].startswith("CHƯA ĐỦ MẪU (1/194"))
        self.assertEqual(laws_checks.check_ledger_chain(self.tmp), [])


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
            st = research.sharpe_stats([0.01, -0.005, 0.02, 0.0, 0.015, -0.01], 20)
            print(json.dumps({"one": one, "many": many, "st": st}))
        """)
        self.assertEqual(code, 0, err[-2000:])
        d = json.loads(out.strip().splitlines()[-1])
        from statistics import NormalDist
        self.assertAlmostEqual(d["one"], NormalDist().cdf(0.3 * math.sqrt(59) / math.sqrt(1 + 0.5 * 0.09)), places=9)
        self.assertLess(d["many"], d["one"])
        self.assertEqual(d["st"]["sr_T"], 6)
        self.assertAlmostEqual(d["st"]["sharpe_ann"], d["st"]["sharpe"] * math.sqrt(252 / 20), places=9)


if __name__ == "__main__":
    unittest.main()
