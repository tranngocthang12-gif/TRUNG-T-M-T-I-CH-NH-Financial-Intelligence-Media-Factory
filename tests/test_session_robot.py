"""F1a (QĐ-10, ADR-0016): robot chạy mỗi phiên HOSE; chế độ do DỮ LIỆU quyết định, không theo đồng hồ máy chạy.

- Workflow `daily_cycle.yml`: ba dòng lịch; bước chặn trước checkout (schedule → `effective_trials=auto`; dispatch chỉ `main`,
  `trials` chỉ 0 hoặc 1); bước chạy engine ánh xạ 0 → ops, 1 → research 1 lần thử, lịch → `--mode auto`; mọi `git commit`
  mang mã lượt chạy.
- `engine.run_cycle --mode auto|ops|research`: auto xét phiên mới nhất có giá so với ENGINE_STATE.as_of; ops không đăng ký,
  không chạy lần thử, không thăng hạng, không theo dõi suy giảm, không chuyên gia, không tải tin, không ghi bandit;
  research giữ nguyên đầu ra cũ, chỉ thêm hai khóa `mode` và `research_as_of` (và hậu tố chế độ ở dòng đầu báo cáo, mục 6).

Mọi lượt chạy engine diễn ra trong tiến trình con với TTC_HOME là thư mục tạm (kho giá tổng hợp), không đụng tệp của kho.
"""
import contextlib, datetime as _dt, gzip, hashlib, json, os, pathlib, shutil, subprocess, sys, tempfile, textwrap, time
import unittest
from unittest import mock

import pandas as pd
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from engine import run_cycle  # noqa: E402  (chỉ dùng select_mode và các kiểm tra đầu vào; không ghi tệp)
from engine.config import CFG  # noqa: E402

WF = ROOT / ".github" / "workflows" / "daily_cycle.yml"
FRI, SAT, MON_BEFORE, MON_AFTER, TUE_AFTER = "2023-01-27", "2023-01-28", "2023-01-23", "2023-02-27", "2023-02-28"
# engine.synthetic.make_store: bdate_range từ 2020-01-01 (thứ Tư). 803 phiên → kết thúc thứ Sáu 2023-01-27;
# 799 phiên → thứ Hai 2023-01-23; 826 phiên → thứ Tư 2023-03-01 (dùng với --as-of cho chuỗi nhiều phiên: MON_AFTER cách
# FRI 21 phiên ≥ paper.rebalance_days = 20, nên sổ giấy tới kỳ ra quyết định trong lượt ops).
STORES = {"fri": 803, "mon": 799, "long": 826}
RESEARCH_FILES = ("research/trials.csv", "research/trial_registry.jsonl", "state/bandit.json")

# Tiến trình con: đếm lần gọi các bước nghiên cứu bằng mock, có thể đặt đồng hồ máy chạy sang ngày khác,
# cố định registered_at của sổ đăng ký (để so từng byte giữa hai lượt chạy).
DRIVER = textwrap.dedent('''
    import contextlib, datetime as _dt, json, sys, time
    from unittest import mock
    import pandas as pd
    from engine import run_cycle, research, knowledge, meta, llm_review, experts, facts
    spec = json.loads(sys.argv[1])
    calls = {}
    def counted(mod, name, stub=None, passthrough=True):
        orig = getattr(mod, name)
        def f(*a, **k):
            calls[name] = calls.get(name, 0) + 1
            return orig(*a, **k) if passthrough else stub
        return mock.patch.object(mod, name, f)
    class FixedDT(_dt.datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 1, 2, 3, 4, 5, tzinfo=tz)
    with contextlib.ExitStack() as st:
        st.enter_context(mock.patch.object(research, "datetime", FixedDT))
        for mod, name in [(research, "register_trial"), (knowledge, "promote"), (knowledge, "decay"),
                          (knowledge, "write_candidate"), (knowledge, "live_predict"), (meta, "save")]:
            st.enter_context(counted(mod, name))
        st.enter_context(counted(llm_review, "review", None, False))
        st.enter_context(counted(experts, "run", {"ran": False, "reasons": ["stub test"]}, False))
        st.enter_context(counted(facts, "ingest_news", {"new_items": 0, "errors": []}, False))
        if spec.get("clock"):
            t = pd.Timestamp(spec["clock"])
            st.enter_context(mock.patch.object(pd.Timestamp, "today", classmethod(lambda cls, *a, **k: t)))
            st.enter_context(mock.patch.object(pd.Timestamp, "now", classmethod(lambda cls, *a, **k: t)))
            t0, real = time.time(), time.time
            st.enter_context(mock.patch.object(time, "time", lambda: t.timestamp() + (real() - t0)))
        if spec.get("no_mark"):
            st.enter_context(mock.patch.object(run_cycle, "_mark_mode", lambda *a, **k: None))
        try:
            if "cycle" in spec:
                r = run_cycle.cycle(**spec["cycle"])
                print("RESULT=" + json.dumps({"mode": r["mode"], "trials": len(r["trials"]), "as_of": r["as_of"]}))
            else:
                sys.argv = ["engine.run_cycle", *spec["argv"]]
                run_cycle.main()
        finally:                                   # kể cả khi main() dừng bằng SystemExit
            print("CALLS=" + json.dumps(calls, sort_keys=True), flush=True)
''')


def _env(home):
    drop = ("TTC_HOME", "TTC_REGISTRY_PUSH", "TTC_PROVENANCE_ONLINE", "GITHUB_TOKEN", "ANTHROPIC_API_KEY",
            "GITHUB_REPOSITORY", "GIT_DIR", "GIT_WORK_TREE")
    e = {k: v for k, v in os.environ.items() if k not in drop}
    e.update({"TTC_HOME": str(home), "PYTHONHASHSEED": "0"})   # thứ tự tập hợp cố định → số thực khớp từng byte
    return e


def _drive(home, spec):
    r = subprocess.run([sys.executable, "-c", DRIVER, json.dumps(spec)], cwd=str(ROOT), env=_env(home),
                       capture_output=True, text=True)
    out = r.stdout + r.stderr
    calls = {}
    for line in r.stdout.splitlines():
        if line.startswith("CALLS="):
            calls = json.loads(line[len("CALLS="):])
    return r.returncode, out, calls


def _cli(home, *args):
    r = subprocess.run([sys.executable, "-m", "engine.run_cycle", *args], cwd=str(ROOT), env=_env(home),
                       capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


def _research_snapshot(home):
    snap = {rel: _sha(home / rel) for rel in RESEARCH_FILES}
    cand = home / "knowledge" / "candidates"
    snap["knowledge/candidates/"] = sorted((p.name, _sha(p)) for p in cand.glob("*")) if cand.is_dir() else None
    return snap


def _state(home):
    return json.loads((home / "state" / "ENGINE_STATE.json").read_text(encoding="utf-8"))


def _csv_dates(home, rel):
    p = home / rel
    return pd.read_csv(p)["date"].astype(str).tolist() if p.is_file() else []


def _drop_key(x, key):
    if isinstance(x, dict):
        return {k: _drop_key(v, key) for k, v in x.items() if k != key}
    if isinstance(x, list):
        return [_drop_key(v, key) for v in x]
    return x


def _normalized_files(home):
    """{đường dẫn: nội dung} của mọi tệp đầu ra. Bỏ hai thứ theo đồng hồ, không phải đầu ra của vòng học: dấu thời gian
    trong đầu gzip (so nội dung đã giải nén) và mọi khóa `generated_at` của reports/scorecard.json (giờ sinh tệp)."""
    out = {}
    for p in sorted(home.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(home).as_posix()
        b = p.read_bytes()
        if rel.endswith(".gz"):
            b = gzip.decompress(b)
        if rel == "reports/scorecard.json":
            b = json.dumps(_drop_key(json.loads(b), "generated_at"), sort_keys=True, ensure_ascii=False).encode()
        out[rel] = b
    return out


@contextlib.contextmanager
def machine_clock(ts):
    """Đặt đồng hồ máy chạy (pandas, datetime, date, time) sang `ts` trong tiến trình này."""
    t = pd.Timestamp(ts)
    real_time, t0 = time.time, time.time()

    class FakeDateTime(_dt.datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(t.year, t.month, t.day, t.hour, t.minute, tzinfo=tz)

        @classmethod
        def today(cls):
            return cls(t.year, t.month, t.day, t.hour, t.minute)

    class FakeDate(_dt.date):
        @classmethod
        def today(cls):
            return cls(t.year, t.month, t.day)

    with mock.patch.object(pd.Timestamp, "today", classmethod(lambda cls, *a, **k: t)), \
            mock.patch.object(pd.Timestamp, "now", classmethod(lambda cls, *a, **k: t)), \
            mock.patch.object(_dt, "datetime", FakeDateTime), mock.patch.object(_dt, "date", FakeDate), \
            mock.patch.object(time, "time", lambda: t.timestamp() + (real_time() - t0)):
        yield


class SelectModeTests(unittest.TestCase):
    """Chọn chế độ chỉ từ dữ liệu: phiên mới nhất có giá (`newest`) và ENGINE_STATE.as_of (`last`)."""

    def test_six_trials_unchanged(self):
        self.assertEqual(int(CFG["research"]["trials_per_cycle"]), 6)

    def test_auto_monday_unprocessed_is_ops_even_when_machine_clock_says_friday(self):
        with machine_clock(f"{FRI} 16:30"):
            self.assertEqual(run_cycle.select_mode("auto", MON_BEFORE, "2023-01-20"), ("ops", 0))

    def test_auto_friday_unprocessed_is_research_six_trials_even_on_saturday_clock(self):
        for clock in (f"{SAT} 00:47", f"{SAT} 10:00", f"{MON_AFTER} 09:00", f"{FRI} 16:30"):
            with self.subTest(clock=clock), machine_clock(clock):
                self.assertEqual(run_cycle.select_mode("auto", FRI, "2023-01-26"), ("research", 6))
                self.assertEqual(run_cycle.select_mode("auto", FRI, None), ("research", 6))

    def test_auto_already_processed_does_nothing(self):
        with machine_clock(f"{SAT} 10:00"):
            self.assertIsNone(run_cycle.select_mode("auto", FRI, FRI))
            self.assertIsNone(run_cycle.select_mode("auto", MON_BEFORE, MON_BEFORE))
        with self.assertRaises(ValueError):                 # bản chấm vòng 1: auto không nhận --force
            run_cycle.select_mode("auto", FRI, FRI, force=True)

    def test_auto_never_goes_back_and_never_forces(self):
        """Bản chấm L-09 PR #88 vòng 1: phiên xử lý của auto chỉ tiến lên theo thời gian."""
        with self.assertRaises(ValueError):                 # giá lùi / --as-of về một thứ Sáu cũ
            run_cycle.select_mode("auto", "2023-01-20", FRI)
        with self.assertRaises(ValueError):
            run_cycle.select_mode("auto", MON_BEFORE, FRI)
        for last in (FRI, "2023-01-26", None):
            with self.subTest(last=last), self.assertRaises(ValueError):
                run_cycle.select_mode("auto", FRI, last, force=True)
        self.assertIsNone(run_cycle.select_mode("auto", FRI, "2023-01-27"))      # cùng phiên, khác cách viết vẫn bằng
        self.assertEqual(run_cycle.select_mode("auto", MON_AFTER, FRI), ("ops", 0))
        # chạy tay giữ chính sách hiện hành (Owner tự chịu: --force chỉ có ở chạy tay, workflow không truyền)
        self.assertEqual(run_cycle.select_mode("research", FRI, FRI, 1, force=True), ("research", 1))

    def test_manual_modes(self):
        self.assertEqual(run_cycle.select_mode("research", FRI, "2023-01-26", 1), ("research", 1))
        self.assertEqual(run_cycle.select_mode("research", MON_BEFORE, None, None), ("research", None))
        self.assertEqual(run_cycle.select_mode("ops", FRI, "2023-01-26", 0), ("ops", 0))
        self.assertEqual(run_cycle.select_mode("ops", FRI, "2023-01-26", None), ("ops", 0))
        self.assertIsNone(run_cycle.select_mode("research", FRI, FRI, 1))
        self.assertIsNone(run_cycle.select_mode("ops", FRI, FRI, 0))

    def test_rejects(self):
        with self.assertRaises(ValueError):
            run_cycle.select_mode("ops", FRI, None, 1)
        with self.assertRaises(ValueError):
            run_cycle.select_mode("auto", FRI, None, 6)
        with self.assertRaises(ValueError):
            run_cycle.select_mode("weekly", FRI, None)
        # cycle() chặn trước mọi lần đọc/ghi tệp. Tiến trình này có ROOT là kho thật: nếu chặn bị bỏ, lần đọc tệp đầu
        # tiên ném RuntimeError (test đỏ) thay vì chạy vòng học ghi vào kho.
        stop = RuntimeError("cycle() đọc tệp trước khi chặn chế độ/số lần thử")
        with mock.patch.object(run_cycle, "load_json", side_effect=stop), \
                mock.patch.object(run_cycle.data, "load_market", side_effect=stop):
            with self.assertRaises(ValueError):
                run_cycle.cycle(FRI, trials=1, mode="ops")
            with self.assertRaises(ValueError):
                run_cycle.cycle(FRI, mode="auto")


class WorkflowTests(unittest.TestCase):
    """Trích đúng script từ YAML và chạy với env giả lập; không cần GitHub."""

    @classmethod
    def setUpClass(cls):
        cls.text = WF.read_text(encoding="utf-8")
        cls.wf = yaml.safe_load(cls.text)
        cls.steps = cls.wf["jobs"]["cycle"]["steps"]

    def _step(self, prefix):
        hit = [s for s in self.steps if str(s.get("name", "")).startswith(prefix)]
        self.assertEqual(len(hit), 1, prefix)
        return hit[0]

    def test_three_schedules_and_name_kept(self):
        on = self.wf.get("on", self.wf.get(True))
        self.assertEqual([c["cron"] for c in on["schedule"]], ["30 9 * * 1-5", "17 13 * * 1-5", "47 16 * * 1-5"])
        self.assertEqual(self.wf["name"], "Vong hoc hang tuan")        # ledger_audit.yml bám theo tên này

    def test_guard_before_checkout(self):
        guard = self._step("Xac nhan so lan thu")
        self.assertIs(self.steps[0], guard)
        self.assertEqual(self.steps[1]["uses"], "actions/checkout@v4")
        cases = [
            ("schedule", "refs/heads/main", "", "effective_trials=auto"),
            ("workflow_dispatch", "refs/heads/main", "0", "effective_trials=0"),
            ("workflow_dispatch", "refs/heads/main", "1", "effective_trials=1"),
            ("workflow_dispatch", "refs/heads/main", "6", None),
            ("workflow_dispatch", "refs/heads/main", "", None),
            ("workflow_dispatch", "refs/heads/main", "01", None),
            ("workflow_dispatch", "refs/heads/feature", "0", None),
            ("workflow_dispatch", "refs/heads/feature", "1", None),
            ("push", "refs/heads/main", "1", None),
            ("pull_request", "refs/heads/main", "0", None),
        ]
        for event, ref, trials, expect in cases:
            with self.subTest(event=event, ref=ref, trials=trials):
                env = {**os.environ, "EVENT_NAME": event, "EVENT_REF": ref, "REQUESTED_TRIALS": trials}
                r = subprocess.run(["bash", "-e", "-c", guard["run"]], env=env, capture_output=True, text=True)
                if expect is None:
                    self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
                    self.assertNotIn("effective_trials=", r.stdout)
                else:
                    self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
                    self.assertIn(expect, r.stdout)

    def test_engine_step_maps_events_to_modes(self):
        step = self._step("Chay vong hoc")
        self.assertEqual(step["env"]["TTC_REGISTRY_PUSH"], "1")
        cases = [
            ("schedule", "", "-m engine.run_cycle --source live --mode auto"),
            ("workflow_dispatch", "0", "-m engine.run_cycle --source live --mode ops --trials 0"),
            ("workflow_dispatch", "1", "-m engine.run_cycle --source live --mode research --trials 1"),
            ("workflow_dispatch", "6", None),
            ("workflow_dispatch", "", None),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            fake = pathlib.Path(tmp) / "python"
            fake.write_text('#!/bin/sh\necho "$@" >> "$ARGS_LOG"\n', encoding="utf-8")
            fake.chmod(0o755)
            for event, trials, expect in cases:
                with self.subTest(event=event, trials=trials):
                    log = pathlib.Path(tmp) / f"args_{event}_{trials or 'empty'}.log"
                    env = {**os.environ, "PATH": f"{tmp}:{os.environ['PATH']}", "ARGS_LOG": str(log),
                           "EVENT_NAME": event, "TRIALS": trials}
                    r = subprocess.run(["bash", "-e", "-c", step["run"]], env=env, capture_output=True, text=True)
                    calls = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
                    if expect is None:
                        self.assertNotEqual(r.returncode, 0)
                        self.assertEqual(calls, [])
                    else:
                        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
                        self.assertEqual(calls, [expect])

    def test_every_commit_carries_run_id(self):
        commits = [l for s in self.steps for l in str(s.get("run", "")).splitlines() if "git commit" in l]
        self.assertEqual(len(commits), 2)
        for line in commits:
            self.assertTrue(line.rstrip().endswith('run ${GITHUB_RUN_ID}.${GITHUB_RUN_ATTEMPT}"'), line)
            self.assertNotIn("${{", line)


class SessionRobotEngineTests(unittest.TestCase):
    """Chạy engine thật trên kho giá tổng hợp trong TTC_HOME tạm."""

    @classmethod
    def setUpClass(cls):
        cls.base = pathlib.Path(tempfile.mkdtemp(prefix="ttc_f1a_"))
        for name, n in STORES.items():
            home = cls.base / f"store_{name}"
            home.mkdir()
            shutil.copy(ROOT / "config.yaml", home / "config.yaml")
            r = subprocess.run([sys.executable, "-c", f"from engine.synthetic import make_store; make_store(n_days={n})"],
                               cwd=str(ROOT), env=_env(home), capture_output=True, text=True)
            assert r.returncode == 0, r.stdout + r.stderr

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.base, ignore_errors=True)

    def _home(self, store):
        home = pathlib.Path(tempfile.mkdtemp(prefix="run_", dir=self.base))
        shutil.rmtree(home)
        shutil.copytree(self.base / f"store_{store}", home)
        return home

    def _first_line(self, home, as_of):
        return (home / "reports" / f"cycle_{as_of}.md").read_text(encoding="utf-8").split("\n")[0]

    def test_auto_monday_runs_ops_even_when_machine_clock_says_friday(self):
        home = self._home("mon")
        code, out, calls = _drive(home, {"argv": ["--source", "store", "--mode", "auto", "--no-llm"],
                                         "clock": f"{FRI} 16:30"})
        self.assertEqual(code, 0, out)
        st = _state(home)
        self.assertEqual((st["as_of"], st["mode"]), (MON_BEFORE, "ops"))
        self.assertNotIn("research_as_of", st)
        self.assertEqual(calls.get("register_trial", 0), 0)
        self.assertEqual(calls.get("live_predict"), 1)
        self.assertEqual(_research_snapshot(home), {**{rel: None for rel in RESEARCH_FILES}, "knowledge/candidates/": None})
        self.assertEqual(_csv_dates(home, "paper/nav.csv")[-1], MON_BEFORE)
        self.assertEqual(_csv_dates(home, "paper/decisions.csv")[-1], MON_BEFORE)
        self.assertTrue(self._first_line(home, MON_BEFORE).endswith(" — chế độ ops"))

    def test_auto_friday_unprocessed_runs_research_with_six_trials_on_saturday_clock_then_not_again(self):
        home = self._home("fri")
        code, out, calls = _drive(home, {"argv": ["--source", "store", "--mode", "auto", "--no-llm"],
                                         "clock": f"{SAT} 10:00"})
        self.assertEqual(code, 0, out)
        st = _state(home)
        self.assertEqual((st["as_of"], st["mode"], st["research_as_of"]), (FRI, "research", FRI))
        self.assertEqual(calls.get("register_trial"), 6)
        trials = pd.read_csv(home / "research" / "trials.csv")
        self.assertEqual(len(trials), 6)
        self.assertEqual(set(trials["cycle_date"].astype(str)), {FRI})
        self.assertTrue(self._first_line(home, FRI).endswith(" — chế độ research"))
        # Lượt dự phòng (20:17, 23:47 hay sau nửa đêm) gặp phiên thứ Sáu đã xử lý: không nghiên cứu lại.
        before, state_before = _research_snapshot(home), _state(home)
        code, out, calls = _drive(home, {"argv": ["--source", "store", "--mode", "auto", "--no-llm"],
                                         "clock": f"{SAT} 00:47"})
        self.assertEqual(code, 0, out)
        self.assertIn("đã xử lý", out)
        self.assertEqual(calls.get("register_trial", 0), 0)
        self.assertEqual(_research_snapshot(home), before)
        self.assertEqual((_state(home)["mode"], _state(home)["research_as_of"]),
                         (state_before["mode"], state_before["research_as_of"]))

    def test_friday_processed_by_manual_ops_means_no_research_that_week(self):
        home = self._home("fri")
        code, out = _cli(home, "--source", "store", "--mode", "ops", "--trials", "0", "--no-llm")
        self.assertEqual(code, 0, out)
        self.assertEqual((_state(home)["as_of"], _state(home)["mode"]), (FRI, "ops"))
        code, out, calls = _drive(home, {"argv": ["--source", "store", "--mode", "auto", "--no-llm"]})
        self.assertEqual(code, 0, out)
        self.assertIn("đã xử lý", out)
        self.assertEqual(calls.get("register_trial", 0), 0)
        self.assertFalse((home / "research" / "trials.csv").exists())

    def test_ops_leaves_research_files_byte_identical_and_still_runs_paper_book(self):
        home = self._home("long")
        code, out, calls = _drive(home, {"argv": ["--source", "store", "--mode", "auto", "--as-of", FRI, "--no-llm"]})
        self.assertEqual(code, 0, out)
        self.assertEqual(calls.get("register_trial"), 6)
        before = _research_snapshot(home)
        self.assertIsNotNone(before["research/trials.csv"])
        self.assertTrue(before["knowledge/candidates/"])
        # Gọi thư viện với trials mặc định (None), live=True, use_llm=True: chế độ ops vẫn không được nghiên cứu,
        # không gọi chuyên gia, không tải tin.
        code, out, calls = _drive(home, {"cycle": {"as_of": MON_AFTER, "mode": "ops", "live": True, "use_llm": True}})
        self.assertEqual(code, 0, out)
        for name in ("register_trial", "promote", "decay", "write_candidate", "save", "review", "run", "ingest_news"):
            self.assertEqual(calls.get(name, 0), 0, (name, calls))
        self.assertEqual(calls.get("live_predict"), 1)
        self.assertIn('RESULT=' + json.dumps({"mode": "ops", "trials": 0, "as_of": MON_AFTER}), out)
        self.assertEqual(_research_snapshot(home), before)
        st = _state(home)
        self.assertEqual((st["as_of"], st["mode"], st["research_as_of"]), (MON_AFTER, "ops", FRI))
        self.assertEqual(_csv_dates(home, "paper/nav.csv")[-2:], [FRI, MON_AFTER])
        self.assertEqual(_csv_dates(home, "paper/decisions.csv")[-2:], [FRI, MON_AFTER])   # tới kỳ tái cơ cấu
        self.assertTrue(self._first_line(home, MON_AFTER).endswith(" — chế độ ops"))
        # Đường dòng lệnh (lượt chạy tay trials=0).
        code, out, calls = _drive(home, {"argv": ["--source", "store", "--mode", "ops", "--trials", "0",
                                                  "--as-of", TUE_AFTER]})
        self.assertEqual(code, 0, out)
        self.assertEqual(calls.get("register_trial", 0), 0)
        self.assertEqual(_research_snapshot(home), before)
        self.assertEqual((_state(home)["as_of"], _state(home)["research_as_of"]), (TUE_AFTER, FRI))
        self.assertEqual(_csv_dates(home, "paper/nav.csv")[-1], TUE_AFTER)

    def test_research_output_unchanged_except_mode_keys_and_report_suffix(self):
        args = ["--source", "store", "--trials", "2", "--no-llm"]
        default, explicit, unmarked = self._home("fri"), self._home("fri"), self._home("fri")
        for home, spec in ((default, {"argv": args}), (explicit, {"argv": [*args, "--mode", "research"]}),
                           (unmarked, {"argv": args, "no_mark": True})):
            code, out, calls = _drive(home, spec)
            self.assertEqual(code, 0, out)
            self.assertEqual(calls.get("register_trial"), 2)
        a, b, c = _normalized_files(default), _normalized_files(explicit), _normalized_files(unmarked)
        self.assertEqual(a, b)                       # gọi mặc định = --mode research, từng byte
        self.assertEqual(set(a), set(c))
        differ = sorted(k for k in a if a[k] != c[k])
        self.assertEqual(differ, [f"reports/cycle_{FRI}.md", "state/ENGINE_STATE.json"])
        sa, sc = json.loads(a["state/ENGINE_STATE.json"]), json.loads(c["state/ENGINE_STATE.json"])
        self.assertEqual({k: sa.pop(k) for k in ("mode", "research_as_of")}, {"mode": "research", "research_as_of": FRI})
        self.assertEqual(sa, sc)
        ra, rc = a[f"reports/cycle_{FRI}.md"].decode().split("\n"), c[f"reports/cycle_{FRI}.md"].decode().split("\n")
        self.assertEqual(ra[0], rc[0] + " — chế độ research")
        self.assertEqual(ra[1:], rc[1:])

    def _all_files(self, home):
        return {p.relative_to(home).as_posix(): _sha(p) for p in sorted(home.rglob("*")) if p.is_file()}

    def test_auto_never_reprocesses_an_older_or_processed_session(self):
        """Bản chấm L-09 PR #88 vòng 1: sau lượt research phiên FRI, auto với --as-of về thứ Sáu cũ hơn, hay auto --force
        cùng phiên hoặc phiên sau, đều dừng: register_trial không được gọi và không tệp nào trong kho bị ghi."""
        home = self._home("long")
        code, out, calls = _drive(home, {"argv": ["--source", "store", "--mode", "auto", "--as-of", FRI, "--no-llm"]})
        self.assertEqual((code, calls.get("register_trial")), (0, 6), out)
        before = self._all_files(home)
        older = (pd.Timestamp(FRI) - pd.offsets.BDay(5)).strftime("%Y-%m-%d")          # thứ Sáu tuần trước
        self.assertEqual(pd.Timestamp(older).weekday(), 4)
        code, out, calls = _drive(home, {"argv": ["--source", "store", "--mode", "auto", "--as-of", older, "--no-llm"]})
        self.assertNotEqual(code, 0, out)
        self.assertIn("cũ hơn phiên đã xử lý", out)
        self.assertEqual(calls.get("register_trial", 0), 0)
        self.assertEqual(self._all_files(home), before)
        later = (pd.Timestamp(FRI) + pd.offsets.BDay(5)).strftime("%Y-%m-%d")           # thứ Sáu kế, chưa xử lý
        for as_of in (FRI, later):
            with self.subTest(as_of=as_of):
                code, out, calls = _drive(home, {"argv": ["--source", "store", "--mode", "auto", "--as-of", as_of,
                                                          "--force", "--no-llm"]})
                self.assertEqual(code, 2, out)
                self.assertEqual(calls.get("register_trial", 0), 0)
                self.assertEqual(self._all_files(home), before)

    def test_cli_rejects_bad_mode_and_trials_before_writing(self):
        for args in (["--mode", "ops", "--trials", "1"], ["--mode", "ops", "--trials", "6"],
                     ["--mode", "auto", "--trials", "6"], ["--mode", "auto", "--trials", "0"], ["--mode", "weekly"],
                     ["--mode", "auto", "--force"]):
            with self.subTest(args=args):
                home = self._home("fri")
                before = sorted(p.relative_to(home).as_posix() for p in home.rglob("*"))
                code, out = _cli(home, "--source", "store", "--no-llm", *args)
                self.assertEqual(code, 2, out)
                self.assertEqual(sorted(p.relative_to(home).as_posix() for p in home.rglob("*")), before)


if __name__ == "__main__":
    unittest.main()
