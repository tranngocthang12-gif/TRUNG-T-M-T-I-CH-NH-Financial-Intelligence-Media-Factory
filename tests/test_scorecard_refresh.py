"""Làm mới scorecard khi giá không đổi, và không phát hành bản STALE khi sổ đổi lúc ghi.

Không đổi Brier, hit_rate, directional_accuracy, observed_yes_rate, mẫu 194 hay right().
Chạy trên bản sao kho (TTC_HOME / cwd của tiến trình con). Không ghi Ledger thật.
"""
import json, os, pathlib, shutil, subprocess, sys, tempfile, textwrap, unittest
from datetime import datetime, timedelta

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from engine import ledger as engine_ledger  # noqa: E402
from tests._calendar_fixture import with_calendar  # noqa: E402
from tools import laws_checks  # noqa: E402

IGNORE = shutil.ignore_patterns(".git", "__pycache__", "*.pyc", "cycle_*.md")
FROZEN = (
    "research/trials.csv",
    "research/trial_registry.jsonl",
    "paper/state.json",
    "paper/nav.csv",
    "paper/decisions.csv",
    "state/model_registry.json",
    "state/MODEL_REGISTRY.yaml",
    "state/bandit.json",
    "state/ENGINE_STATE.json",
    "governance/SAFETY_STATE.yaml",
)


def _body():
    f = {"seat": "A", "question": "CPI tháng 11/2026 của thử làm mới scorecard có tăng từ 4,00% trở lên không?",
         "resolution_source": "Cục Thống kê (nso.gov.vn) — thông cáo CPI", "resolution_rule": "numeric_range",
         "resolve_at": "2026-12-31", "info_lock_at": "2026-12-20", "p": "0.35", "base_rate": "0.5",
         "invalidation_conditions": "Cục Thống kê đổi rổ hàng", "author_seat": "Claude Project TTC", "model_cutoff": "2026-06"}
    return "\n\n".join(f"### {k}\n\n{v}" for k, v in f.items())


class ScorecardRefreshTests(unittest.TestCase):
    def setUp(self):
        self.base = pathlib.Path(tempfile.mkdtemp())
        self.repo = self.base / "repo"
        shutil.copytree(ROOT, self.repo, ignore=IGNORE)
        self.env = {k: v for k, v in os.environ.items()
                    if k not in ("TTC_PROVENANCE_ONLINE", "GITHUB_REPOSITORY", "TTC_HOME", "GIT_DIR", "GIT_WORK_TREE")}
        self.legacy = [l for l in (ROOT / "ledger" / "predictions.jsonl").read_bytes().split(b"\n") if l.strip()][:6]

    def tearDown(self):
        shutil.rmtree(self.base, ignore_errors=True)

    def _py(self, code, extra_env=None):
        r = subprocess.run([sys.executable, "-c", textwrap.dedent(code)], cwd=str(self.repo),
                           env={**self.env, **(extra_env or {})}, capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr

    def _run_cycle(self, *args):
        r = subprocess.run([sys.executable, "-m", "engine.run_cycle", *args], cwd=str(self.repo), env=self.env,
                           capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr

    def _validate(self, *args):
        r = subprocess.run([sys.executable, str(self.repo / "tools" / "validate.py"), *args], cwd=str(self.repo),
                           env=self.env, capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr

    def _forecast(self, number=61, created="2026-11-19T02:00:00Z"):
        body = with_calendar(self.repo, _body())
        now = (datetime.fromisoformat(created.replace("Z", "+00:00")) + timedelta(seconds=60)).isoformat()
        e = {**self.env, "ISSUE_NUMBER": str(number), "ISSUE_CREATED_AT": created, "ISSUE_BODY": body, "TTC_INTAKE_NOW": now}
        r = subprocess.run([sys.executable, str(self.repo / "tools" / "ledger_intake.py")], env=e,
                           capture_output=True, text=True, cwd=str(self.repo))
        return r.returncode, r.stdout + r.stderr

    def _rows(self, rel="ledger/predictions.jsonl"):
        p = self.repo / rel
        return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.is_file() else []

    def _snap(self):
        out = {}
        for rel in FROZEN:
            p = self.repo / rel
            out[rel] = p.read_bytes() if p.is_file() else None
        return out

    def _as_of(self):
        d = laws_checks.price_data_as_of(self.repo)
        self.assertIsNotNone(d)
        return d

    def _scorecard(self):
        return json.loads((self.repo / "reports" / "scorecard.json").read_text(encoding="utf-8"))

    def test_price_unchanged_ledger_grows_refreshes_without_new_trial(self):
        as_of = self._as_of()
        st = json.loads((self.repo / "state" / "ENGINE_STATE.json").read_text(encoding="utf-8"))
        st["as_of"] = as_of
        (self.repo / "state" / "ENGINE_STATE.json").write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")
        n0 = len(self._rows())
        frozen = self._snap()
        pred_before = (self.repo / "ledger" / "predictions.jsonl").read_bytes()
        c, o = self._forecast()
        self.assertEqual(c, 0, o)
        self.assertEqual(len(self._rows()), n0 + 1)
        self.assertTrue((self.repo / "ledger" / "predictions.jsonl").read_bytes().startswith(pred_before.rstrip(b"\n")))
        got = [l for l in (self.repo / "ledger" / "predictions.jsonl").read_bytes().split(b"\n") if l.strip()][:6]
        self.assertEqual(got, self.legacy)
        self.assertEqual(laws_checks.scorecard_freshness(self.repo)[0], "STALE")
        c, o = self._validate()
        self.assertEqual(c, 0, o)
        self.assertIn("STALE", o)
        c, o = self._validate("--require-fresh-scorecard")
        self.assertNotEqual(c, 0, o)
        c, o = self._run_cycle("--source", "store", "--no-llm", "--trials", "7")
        self.assertEqual(c, 0, o)
        self.assertIn("Bỏ qua nghiên cứu", o)
        self.assertNotIn("thử nghiệm:", o)
        self.assertEqual(self._snap(), frozen)
        self.assertEqual(laws_checks.scorecard_freshness(self.repo), ("FRESH", []))
        sc = self._scorecard()
        self.assertEqual(sc["as_of"], as_of)
        self.assertEqual(sc["total_predictions"], n0 + 1)
        self.assertEqual(sc["freshness"]["sources"]["ledger/predictions.jsonl"]["rows"], n0 + 1)
        self.assertEqual(sc["issue_forecasts"]["scores"], {})
        self.assertFalse(sc["freshness"]["capability_scores_emitted"])
        self.assertTrue(str(sc["issue_forecasts"]["timing_verification_source"]).startswith("none"))
        self.assertEqual(self._validate("--require-fresh-scorecard")[0], 0)
        # Lần sau, cùng sổ và cùng ngày giá: không ghi đè scorecard.
        raw = (self.repo / "reports" / "scorecard.json").read_bytes()
        c, o = self._run_cycle("--scorecard-only", "--as-of", as_of, "--source", "live")
        self.assertEqual(c, 0, o)
        self.assertIn("không ghi lại", o)
        self.assertEqual((self.repo / "reports" / "scorecard.json").read_bytes(), raw)
        self.assertEqual(self._snap(), frozen)

    def test_drift_during_write_is_not_published_then_stable_refresh_matches(self):
        as_of = self._as_of()
        c, o = self._run_cycle("--scorecard-only", "--as-of", as_of, "--source", "store")
        self.assertEqual(c, 0, o)
        old = (self.repo / "reports" / "scorecard.json").read_bytes()
        before = laws_checks.scorecard_sources(self.repo)
        frozen = self._snap()
        code = """
            import pathlib
            from engine.config import ROOT
            from engine.run_cycle import refresh_scorecard_report
            p = ROOT / "ledger" / "predictions.jsonl"
            def hook(i):
                with p.open("a", encoding="utf-8") as f:
                    f.write("\\n")
            print(refresh_scorecard_report("AS_OF", attempts=3, while_writing=hook))
        """.replace("AS_OF", as_of)
        c, o = self._py(code)
        self.assertEqual(c, 0, o)
        self.assertIn("\n1\n", "\n" + o)
        self.assertIn("không ổn định", o)
        self.assertNotEqual((self.repo / "reports" / "scorecard.json").read_bytes(), old)
        self.assertNotEqual(laws_checks.scorecard_sources(self.repo), before)
        # Ba lần ghi xen không được trả 0. Sổ đã đứng yên: lần làm mới sau khớp sổ mới và qua hậu kiểm.
        c, o = self._run_cycle("--scorecard-only", "--as-of", as_of)
        self.assertEqual(c, 0, o)
        self.assertEqual(laws_checks.scorecard_freshness(self.repo), ("FRESH", []))
        self.assertEqual(self._validate("--require-fresh-scorecard")[0], 0, self._validate("--require-fresh-scorecard")[1])
        self.assertEqual(self._snap(), frozen)
        got = [l for l in (self.repo / "ledger" / "predictions.jsonl").read_bytes().split(b"\n") if l.strip()][:6]
        self.assertEqual(got, self.legacy)

    def test_one_mid_write_append_retries_then_matches_new_ledger(self):
        as_of = self._as_of()
        c, o = self._run_cycle("--scorecard-only", "--as-of", as_of)
        self.assertEqual(c, 0, o)
        n0 = len(self._rows())
        code = """
            import pathlib
            from engine.config import ROOT
            from engine.run_cycle import refresh_scorecard_report
            p = ROOT / "ledger" / "publication_evidence.jsonl"
            def hook(i):
                if i == 0:
                    with p.open("a", encoding="utf-8") as f:
                        f.write("\\n")
            print(refresh_scorecard_report("AS_OF", attempts=3, while_writing=hook))
        """.replace("AS_OF", as_of)
        c, o = self._py(code)
        self.assertEqual(c, 0, o)
        self.assertIn("\n0\n", "\n" + o)
        self.assertIn("sổ đổi trong lúc ghi", o)
        self.assertEqual(laws_checks.scorecard_freshness(self.repo), ("FRESH", []))
        sc = self._scorecard()
        self.assertEqual(sc["total_predictions"], n0)
        self.assertIsNotNone(sc["freshness"]["sources"]["ledger/publication_evidence.jsonl"]["sha256"])
        self.assertEqual(sc["issue_forecasts"]["scores"], {})

    def test_no_github_provenance_emits_no_capability_scores_and_invalid_blocks(self):
        as_of = self._as_of()
        # The copied production scorecard can already be FRESH. Force a
        # genuine offline refresh rather than returning the cached report.
        (self.repo / "reports" / "scorecard.json").unlink(missing_ok=True)
        c, o = self._py(
            """
            import os
            from engine.run_cycle import refresh_scorecard_report
            os.environ.pop("TTC_PROVENANCE_ONLINE", None)
            os.environ.pop("GITHUB_REPOSITORY", None)
            print(refresh_scorecard_report("AS_OF", attempts=2))
            """.replace("AS_OF", as_of),
            extra_env={"TTC_PROVENANCE_ONLINE": "1"},  # tiến trình con tự gỡ trước khi ghi
        )
        # extra_env bật cờ, mã trong -c gỡ trước scorecard(). Điểm năng lực vẫn không được phát.
        self.assertEqual(c, 0, o)
        self.assertIn("\n0\n", "\n" + o)
        sc = self._scorecard()
        self.assertEqual(sc["issue_forecasts"]["scores"], {})
        self.assertFalse(sc["freshness"]["capability_scores_emitted"])
        self.assertFalse(str(sc["issue_forecasts"]["timing_verification_source"]).startswith("github"))
        p = self.repo / "reports" / "scorecard.json"
        forged = json.loads(p.read_text(encoding="utf-8"))
        forged["issue_forecasts"]["scores"] = {"A": {"n": 1, "brier": 0.2}}
        forged["freshness"]["capability_scores_emitted"] = True
        forged["issue_forecasts"]["timing_verification_source"] = "none: test"
        p.write_text(json.dumps(forged, ensure_ascii=False), encoding="utf-8")
        self.assertEqual(laws_checks.scorecard_freshness(self.repo)[0], "INVALID")
        c, o = self._validate()
        self.assertEqual(c, 1, o)
        self.assertIn("scorecard INVALID", o)
        # STALE không chặn tiền kiểm; hậu kiểm thì chặn.
        good = self._run_cycle("--scorecard-only", "--as-of", as_of)
        self.assertEqual(good[0], 0, good[1])
        with (self.repo / "ledger" / "predictions.jsonl").open("a", encoding="utf-8") as f:
            f.write("\n")
        self.assertEqual(laws_checks.scorecard_freshness(self.repo)[0], "STALE")
        c, o = self._validate()
        self.assertEqual(c, 0, o)
        self.assertIn("STALE", o)
        self.assertIn("KHÔNG dùng để kết luận năng lực", o)
        c, o = self._validate("--require-fresh-scorecard")
        self.assertEqual(c, 1, o)

    def test_scores_without_github_source_are_not_released_by_refresh(self):
        as_of = self._as_of()
        # A fresh copied scorecard would short-circuit before the injected
        # invalid scorer runs. Remove only the disposable fixture report.
        (self.repo / "reports" / "scorecard.json").unlink(missing_ok=True)
        code = """
            import json
            from engine import ledger
            from engine.config import save_json
            from engine.run_cycle import refresh_scorecard_report
            real = ledger.scorecard
            def bad(as_of, verified=None):
                sc = real(as_of, verified)
                sc["issue_forecasts"]["scores"] = {"A": {"brier": 0.2}}
                sc["issue_forecasts"]["timing_verification_source"] = "none: test"
                sc["freshness"]["capability_scores_emitted"] = True
                sc["freshness"]["timing_verification_source"] = "none: test"
                save_json("reports/scorecard.json", sc)
                return sc
            ledger.scorecard = bad
            print(refresh_scorecard_report("AS_OF", attempts=1))
        """.replace("AS_OF", as_of)
        c, o = self._py(code)
        self.assertEqual(c, 0, o)
        self.assertIn("\n1\n", "\n" + o)
        self.assertIn("INVALID", o)
        self.assertNotIn("FRESH as_of", o)

    def test_workflow_refreshes_after_rebase_before_push(self):
        import yaml
        text = (ROOT / ".github" / "workflows" / "daily_cycle.yml").read_text(encoding="utf-8")
        wf = yaml.safe_load(text)
        runs = [str(s.get("run") or "") for s in wf["jobs"]["cycle"]["steps"]]
        i_cycle = next(i for i, r in enumerate(runs) if "engine.run_cycle" in r and "--scorecard-only" not in r)
        pre = [r for r in runs[:i_cycle] if "tools/validate.py" in r]
        self.assertTrue(pre and all("--require-fresh-scorecard" not in r for r in pre), pre)
        post = next(r for r in runs[i_cycle + 1:] if "tools/validate.py" in r and "git push" not in r)
        self.assertIn("--require-fresh-scorecard", post)
        push = next(r for r in runs if "git push" in r)
        pull = push.find("git pull -q --rebase origin main")
        refresh = push.find("python -m engine.run_cycle --scorecard-only")
        fresh = push.find("python tools/validate.py --require-fresh-scorecard")
        sent = push.find("git push")
        self.assertTrue(0 <= pull < refresh < fresh < sent, push)
        self.assertIn("for i in 1 2 3 4 5", push)
        self.assertTrue(push.rstrip().endswith("exit 1"))
        self.assertNotIn("--trials", push[refresh:fresh])
        self.assertIn('--trials "$TRIALS"', runs[i_cycle])
        self.assertIn("TTC_REGISTRY_PUSH", text)


class FormulaUntouchedTests(unittest.TestCase):
    def test_brier_direction_194_and_right_unchanged(self):
        src = (ROOT / "engine" / "ledger.py").read_text(encoding="utf-8")
        self.assertEqual(engine_ledger.TARGET_DISAGREEMENTS, 194)
        self.assertIn('def right(a): return (float(a["p"]) > 0.5) == (outcome[a["id"]] == 1)', src)
        self.assertIn("if abs(p - 0.5) <= 1e-12:", src)
        self.assertIn("brier = float(((p - o) ** 2).mean())", src)
        self.assertIn("hit_rate_meaning", src)
        self.assertIn("observed_yes_rate", src)
        # F-37–F-42: sáu dòng đầu không bị tệp test này đụng (so với chính nó).
        lines = [l for l in (ROOT / "ledger" / "predictions.jsonl").read_bytes().split(b"\n") if l.strip()]
        self.assertGreaterEqual(len(lines), 6)
        self.assertTrue(all(b'"id": "F-' in lines[i] or b'"id":"F-' in lines[i] for i in range(6)))


if __name__ == "__main__":
    unittest.main()
