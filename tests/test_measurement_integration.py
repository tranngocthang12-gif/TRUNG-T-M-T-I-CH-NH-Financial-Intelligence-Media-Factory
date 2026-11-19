"""Kiểm thử tích hợp đo lường và vận hành (lệnh Owner 19/11/2026, TEST-1 … TEST-8).

Mọi bước chạy trên BẢN SAO cả kho trong thư mục tạm (robot nhận Issue, validate.py, engine.ledger.scorecard), không ghi Issue
thử vào Ledger thật và không sửa tệp nào của kho. Thiết kế đang kiểm:
- Ledger là nguồn có thẩm quyền; reports/scorecard.json là bản dẫn xuất, mang khối freshness (số dòng + sha256 của từng sổ,
  ngày dữ liệu giá, commit nguồn).
- Robot ghi Forecast/Resolution → scorecard cũ thành STALE. STALE KHÔNG làm validate.py tiền kiểm thất bại (nếu không, vòng học
  không bao giờ chạy để sinh bản mới), nhưng validate.py --require-fresh-scorecard (hậu kiểm vòng học) thất bại.
- Điểm năng lực chỉ phát hành khi xuất xứ do GitHub xác nhận; scorecard có điểm mà nguồn khác GitHub là INVALID và luôn chặn.
- Dự báo mới thiếu trường (kể cả nhiều trường một lúc) bị từ chối mã 2, không traceback, không ghi sổ.
"""
import gzip, json, os, pathlib, shutil, subprocess, sys, tempfile, textwrap, unittest
from datetime import datetime, timedelta

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from engine import ledger as engine_ledger  # noqa: E402
from tests._calendar_fixture import with_calendar  # noqa: E402
from tools import laws_checks, ledger_intake  # noqa: E402

IGNORE = shutil.ignore_patterns(".git", "__pycache__", "*.pyc", "cycle_*.md")
LEGACY_LINES = [l for l in (ROOT / "ledger" / "predictions.jsonl").read_bytes().split(b"\n") if l.strip()][:6]


def _just_after(created, seconds=60):
    return (datetime.fromisoformat(created.replace("Z", "+00:00")) + timedelta(seconds=seconds)).isoformat()


def _body(**kw):
    f = {"seat": "A", "question": "CPI tháng 11/2026 của thử nghiệm tích hợp có tăng từ 4,00% trở lên không?",
         "resolution_source": "Cục Thống kê (nso.gov.vn) — thông cáo CPI", "resolution_rule": "numeric_range",
         "resolve_at": "2026-12-31", "info_lock_at": "2026-12-20", "p": "0.35", "base_rate": "0.5",
         "invalidation_conditions": "Cục Thống kê đổi rổ hàng", "author_seat": "Claude Project TTC", "model_cutoff": "2026-06"}
    f.update(kw)
    return "\n\n".join(f"### {k}\n\n{v}" for k, v in f.items() if v is not None)


def _resolution(ids, outcome, resolver="Owner"):
    f = {"forecast_ids": ids, "outcome": outcome, "observed_value": "_No response_",
         "resolution_source": "https://www.nso.gov.vn/thong-cao-cpi.pdf", "quote": "CPI tháng 11 tăng 3,2% so với cùng kỳ",
         "resolver": resolver, "void_reason": "_No response_"}
    return "\n\n".join(f"### {k}\n\n{v}" for k, v in f.items())


class _Repo(unittest.TestCase):
    """Một bản sao kho cho mỗi test."""

    def setUp(self):
        self.base = pathlib.Path(tempfile.mkdtemp())
        self.repo = self.base / "repo"
        shutil.copytree(ROOT, self.repo, ignore=IGNORE)
        self.env = {k: v for k, v in os.environ.items() if k not in ("TTC_PROVENANCE_ONLINE", "GITHUB_REPOSITORY", "TTC_HOME")}

    def tearDown(self):
        shutil.rmtree(self.base, ignore_errors=True)

    # --- các đường chạy thật, trên bản sao ---
    def intake(self, script, number, body, created):
        e = {**self.env, "ISSUE_NUMBER": str(number), "ISSUE_CREATED_AT": created, "ISSUE_BODY": body,
             "TTC_INTAKE_NOW": _just_after(created)}
        r = subprocess.run([sys.executable, str(self.repo / "tools" / script)], env=e, capture_output=True, text=True,
                           cwd=str(self.repo))
        return r.returncode, r.stdout + r.stderr

    def forecast(self, number, created="2026-11-19T02:00:00Z", calendar=True, **kw):
        body = _body(**kw)
        if calendar:
            body = with_calendar(self.repo, body)        # lịch ghim QUA robot trong bản sao, Issue lịch mở trước
        return self.intake("ledger_intake.py", number, body, created)

    def validate(self, *args):
        r = subprocess.run([sys.executable, str(self.repo / "tools" / "validate.py"), *args], env=self.env,
                           capture_output=True, text=True, cwd=str(self.repo))
        return r.returncode, r.stdout + r.stderr

    def cycle_scorecard(self, as_of="2026-11-20", **env):
        """Bước sinh scorecard của vòng học (engine.run_cycle gọi đúng hàm này), chạy với TTC_HOME = bản sao."""
        code = f"from engine import ledger; ledger.scorecard({as_of!r})"
        r = subprocess.run([sys.executable, "-c", code], env={**self.env, "TTC_HOME": str(self.repo), **env},
                           capture_output=True, text=True, cwd=str(self.repo))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return json.loads((self.repo / "reports" / "scorecard.json").read_text(encoding="utf-8"))

    def rows(self, rel="ledger/predictions.jsonl"):
        p = self.repo / rel
        return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.is_file() else []

    def status(self):
        return laws_checks.scorecard_freshness(self.repo)


class Test1ForecastDoesNotBlockLearningLoop(_Repo):
    def test_forecast_makes_scorecard_stale_but_precheck_passes_and_cycle_refreshes_it(self):
        self.cycle_scorecard()                                              # vòng học trước: scorecard khớp sổ
        self.assertEqual(self.status()[0], "FRESH", self.status())
        self.assertEqual(self.validate("--require-fresh-scorecard")[0], 0)
        n0 = len(self.rows())
        c, o = self.forecast(61)
        self.assertEqual(c, 0, o)                                           # robot nhận
        self.assertEqual(len(self.rows()), n0 + 1)                          # Ledger tăng
        st, why = self.status()
        self.assertEqual(st, "STALE")
        self.assertTrue(any("ledger/predictions.jsonl" in w for w in why), why)
        c, o = self.validate()                                              # tiền kiểm của daily_cycle.yml
        self.assertEqual(c, 0, o)
        self.assertIn("STALE", o)
        self.assertIn("KHÔNG dùng để kết luận năng lực", o)
        c, o = self.validate("--require-fresh-scorecard")                   # hậu kiểm: bản cũ không được ghi lên main
        self.assertEqual(c, 1, o)
        sc = self.cycle_scorecard()                                         # vòng học chạy
        self.assertEqual(self.status(), ("FRESH", []))
        self.assertEqual(sc["freshness"]["sources"]["ledger/predictions.jsonl"]["rows"], n0 + 1)
        self.assertEqual(self.validate("--require-fresh-scorecard")[0], 0)


class Test2ResolutionRefreshCycle(_Repo):
    def test_resolution_makes_scorecard_stale_then_cycle_updates_it(self):
        c, o = self.forecast(61, resolve_at="2026-11-25", info_lock_at="2026-11-25")
        self.assertEqual(c, 0, o)
        sc = self.cycle_scorecard("2026-11-24")
        self.assertEqual(sc["issue_forecasts"]["counts"]["resolved"], 0)
        self.assertEqual(self.status()[0], "FRESH")
        c, o = self.intake("resolution_intake.py", 70, _resolution("F-61", "NO"), "2026-11-25T03:00:00Z")
        self.assertEqual(c, 0, o)
        self.assertEqual(len(self.rows("ledger/resolutions.jsonl")), 1)      # Ledger phân định tăng
        st, why = self.status()
        self.assertEqual(st, "STALE")
        self.assertTrue(any(w.startswith("ledger/resolutions.jsonl") for w in why), why)
        self.assertEqual(self.validate()[0], 0)                             # không chặn vòng học
        sc = self.cycle_scorecard("2026-11-26")
        self.assertEqual(self.status(), ("FRESH", []))
        self.assertEqual(sc["issue_forecasts"]["counts"]["resolved"], 1)
        self.assertEqual(sc["freshness"]["sources"]["ledger/resolutions.jsonl"]["rows"], 1)
        # TEST-6 trên cùng sổ: không có xác nhận GitHub → không có điểm năng lực, nhưng số thô vẫn có để kiểm toán
        self.assertEqual(sc["issue_forecasts"]["scores"], {})
        self.assertFalse(sc["freshness"]["capability_scores_emitted"])
        raw = sc["issue_forecasts"]["raw_audit"]["scores"]["A"]
        self.assertEqual((raw["n"], raw["observed_yes_rate"], raw["directional_accuracy"]), (1, 0.0, 1.0))   # p=0,35, NO
        self.assertEqual(raw["brier"], 0.1225)
        self.assertIn("KHÔNG PHẢI BẰNG CHỨNG NĂNG LỰC", sc["issue_forecasts"]["raw_audit"]["label"])
        self.assertEqual(self.validate("--require-fresh-scorecard")[0], 0)


class Test3MalformedForecastIsRejected(_Repo):
    CASES = {
        "thiếu p": dict(p=None),
        "thiếu resolve_at": dict(resolve_at=None),
        "thiếu cả hai trường lịch": dict(info_lock_at=None),
        "thiếu p, base_rate và hai trường lịch": dict(p=None, base_rate=None, info_lock_at=None),
        "thiếu author_seat, model_cutoff, resolve_at và hai trường lịch": dict(author_seat=None, model_cutoff=None,
                                                                             resolve_at=None, info_lock_at=None),
        "p không phải số": dict(p="cao"),
        "p ngoài khoảng": dict(p="1.5"),
        "p là NaN": dict(p="NaN"),
        "info_lock_at sai dạng": dict(info_lock_at="20/12/2026"),
        "seat lạ": dict(seat="C"),
    }

    def test_every_malformed_issue_exits_2_without_traceback_or_write(self):
        led = self.repo / "ledger" / "predictions.jsonl"
        before = led.read_bytes()
        for i, (name, kw) in enumerate(self.CASES.items(), 1):
            with self.subTest(name):
                # không qua with_calendar: chỉ thân Issue người dùng gửi
                c, o = self.intake("ledger_intake.py", 100 + i, _body(**kw), "2026-11-19T02:00:00Z")
                self.assertEqual(c, 2, o)
                self.assertNotIn("Traceback", o)
                self.assertFalse(json.loads(o.strip().splitlines()[-1])["ok"])
                self.assertEqual(led.read_bytes(), before)

    def test_all_missing_fields_are_named_before_any_field_is_read(self):
        data = ledger_intake.parse_issue_form(_body(p=None, resolve_at=None, info_lock_at=None))
        msg, _ = ledger_intake.forecast_error(data, "2026-11-19T02:00:00Z", [], [], calendar=[])
        for k in ("p", "resolve_at", "info_lock_at", "calendar_id"):
            self.assertIn(k, msg)
        self.assertIn("thiếu trường bắt buộc", msg)

    def test_legacy_mode_is_not_a_bypass_for_new_forecasts(self):
        data = ledger_intake.parse_issue_form(_body(info_lock_at=None))
        for num in (61, 43, None):
            msg, _ = ledger_intake.forecast_error(data, "2026-11-19T02:00:00Z", [], [], legacy_timing=True, number=num,
                                                  calendar=[])
            self.assertIn("F-37–F-42", msg)
        self.assertIn("calendar_id", ledger_intake.required_forecast_fields(legacy=False))
        self.assertIn("info_lock_at", ledger_intake.required_forecast_fields(legacy=False))
        # Xóa tệp contract mới trong bản sao: robot vẫn đòi hai trường lịch (không nới luật khi thiếu tệp)
        (self.repo / "contracts" / "forecast_issue_new.schema.json").unlink()
        c, o = self.intake("ledger_intake.py", 120, _body(info_lock_at=None), "2026-11-19T02:00:00Z")
        self.assertEqual(c, 2, o)
        self.assertIn("info_lock_at", o)


class Test4LegacyReplay(_Repo):
    def test_f37_to_f42_replay_unchanged_and_cannot_be_retagged(self):
        pred = ledger_intake.load_rows(ROOT / "ledger" / "predictions.jsonl")
        legacy = [r for r in pred if r["id"] in ledger_intake.LEGACY_TIMING_IDS]
        self.assertEqual([r["id"] for r in legacy], [f"F-{n}" for n in range(37, 43)])
        self.assertTrue(all(ledger_intake.is_legacy_timing_row(r) for r in legacy))
        self.assertEqual(ledger_intake.ledger_errors(pred, ledger_intake.load_rows(ROOT / "ledger" / "resolutions.jsonl"),
                                                     calendar=[]), [])
        # Sau cả luồng nhận mới trên bản sao, sáu dòng đầu vẫn trùng từng byte với kho thật
        self.assertEqual(self.forecast(61)[0], 0)
        lines = [l for l in (self.repo / "ledger" / "predictions.jsonl").read_bytes().split(b"\n") if l.strip()]
        self.assertEqual(lines[:6], LEGACY_LINES)
        # Gắn calendar_id hồi tố vào F-37, giữ hash cũ: luật chuyển tiếp từ chối, và hash chuỗi không còn khớp nội dung
        forged = dict(legacy[0], calendar_id="CAL-HOI-TO")
        self.assertTrue(any("calendar_id" in e for e in ledger_intake.replay([forged], [], calendar=[])))
        self.assertNotEqual(laws_checks.line_hash({k: v for k, v in forged.items() if k != "hash"}), forged["hash"])
        # Tính lại hash cho khớp: không còn là dòng ghim → bị đòi contract mới (info_lock_at)
        rehashed = {k: v for k, v in forged.items() if k != "hash"}
        rehashed["hash"] = laws_checks.line_hash(rehashed)
        self.assertFalse(ledger_intake.is_legacy_timing_row(rehashed))
        self.assertTrue(any("info_lock_at" in e for e in ledger_intake.replay([rehashed], [], calendar=[])))


class Test5MonthlyPriceStore(_Repo):
    def _month(self, rows):
        d = self.repo / "data" / "store" / "prices"
        d.mkdir(parents=True, exist_ok=True)
        f = d / "2026-11.csv"
        head = "" if f.exists() else "date,ticker,open,high,low,close,volume,observed_at,source\n"
        with f.open("a", encoding="utf-8") as fh:
            fh.write(head + "".join(rows))

    def test_data_date_reads_monthly_files_not_only_the_frozen_store(self):
        gz = self.repo / "data" / "store" / "prices.csv.gz"
        frozen = gz.read_bytes()
        with gzip.open(gz, "rt", encoding="utf-8") as f:
            last_frozen = max(line.split(",", 1)[0] for line in list(f)[1:] if line.strip())
        self.assertEqual(last_frozen, "2026-11-16")                         # kho cũ dừng 16/11/2026
        self.assertEqual(laws_checks.price_data_as_of(self.repo), "2026-11-16")
        self.cycle_scorecard("2026-11-20")
        self.assertEqual(self.status()[0], "FRESH")
        self._month(["2026-11-20,VCB,90000,91000,89500,90500,1000000,2026-11-20 16:00:00,yahoo\n",
                     "khong-phai-ngay,VCB,1,1,1,1,1,2026-11-20 16:00:00,yahoo\n",            # dòng hỏng bị bỏ qua
                     "2026-11-27,VCB,90000,91000,89500,90500,1000000,2026-11-27 16:00:00,yahoo\n"])  # sau as_of
        self.assertEqual(laws_checks.price_data_as_of(self.repo, "2026-11-20"), "2026-11-20")
        self.assertEqual(laws_checks.price_data_as_of(self.repo), "2026-11-27")
        st, why = self.status()
        self.assertEqual(st, "STALE")
        self.assertTrue(any("data_as_of" in w and "2026-11-20" in w for w in why), why)
        # Engine chỉ ghi dòng hợp lệ (save_store); gỡ dòng hỏng của test trước khi chạy pipeline thật
        f = self.repo / "data" / "store" / "prices" / "2026-11.csv"
        f.write_text("".join(l for l in f.read_text(encoding="utf-8").splitlines(True) if not l.startswith("khong")), encoding="utf-8")
        sc = self.cycle_scorecard("2026-11-20")
        self.assertEqual(sc["freshness"]["data_as_of"], "2026-11-20")      # ngày quan sát, không phải giờ sinh báo cáo
        self.assertEqual(self.status(), ("FRESH", []))
        self.assertEqual(gz.read_bytes(), frozen)                           # không viết lại kho cũ
        # Pipeline đọc cùng hai nguồn (engine.data.load_store, ADR-0006)
        r = subprocess.run([sys.executable, "-c", "from engine.data import load_store; print(load_store()['date'].max().date())"],
                           env={**self.env, "TTC_HOME": str(self.repo)}, capture_output=True, text=True, cwd=str(self.repo))
        self.assertEqual(r.stdout.strip(), "2026-11-27", r.stderr)


class Test6ProvenanceGatesCapability(_Repo):
    def test_no_github_provenance_means_no_capability_scores(self):
        sc = self.cycle_scorecard(TTC_PROVENANCE_ONLINE="1")               # bật đối chiếu nhưng không có GITHUB_REPOSITORY
        self.assertTrue(sc["issue_forecasts"]["timing_verification_source"].startswith("none"))
        self.assertEqual(sc["issue_forecasts"]["scores"], {})
        self.assertEqual(self.status()[0], "FRESH")
        # Ai đó chèn điểm năng lực vào scorecard khi nguồn không phải GitHub → INVALID, chặn cả tiền kiểm
        p = self.repo / "reports" / "scorecard.json"
        forged = json.loads(p.read_text(encoding="utf-8"))
        forged["issue_forecasts"]["scores"] = {"A": {"n": 6, "brier": 0.1}}
        forged["freshness"]["capability_scores_emitted"] = True
        p.write_text(json.dumps(forged, ensure_ascii=False), encoding="utf-8")
        st, why = self.status()
        self.assertEqual(st, "INVALID")
        self.assertTrue(any("GitHub" in w for w in why), why)
        c, o = self.validate()
        self.assertEqual(c, 1, o)
        self.assertIn("scorecard INVALID", o)
        # Nguồn GitHub thật (github_api) thì điểm được phép có mặt
        forged["issue_forecasts"]["timing_verification_source"] = "github_api"
        p.write_text(json.dumps(forged, ensure_ascii=False), encoding="utf-8")
        self.assertEqual(self.status()[0], "FRESH")


class Test7MetricsDoNotRegress(unittest.TestCase):
    """Phỏng theo DirectionalAccuracyTests của PR #49: số đã biết trước, tính tay."""
    CAL = (lambda r: {**r, "hash": laws_checks.line_hash(r)})(
        {"calendar_id": "CAL-TEST", "domains": ["nso.gov.vn"], "info_lock_at": "2026-12-20",
         "evidence_url": "https://www.nso.gov.vn/lich", "quote": "Số tháng 11 được công bố ngày 20/12/2026.",
         "recorder": "Owner", "issue_number": 900001, "issue_created_at": "2026-11-01T00:00:00Z", "prev_hash": "GENESIS"})

    @staticmethod
    def _row(num, p, seat="A", q=None):
        return {"id": f"F-{num}", "issue_number": num, "issue_created_at": "2026-11-17T02:00:00Z", "seat": seat,
                "question": q or f"Câu hướng số {num} có đủ mười ký tự không?", "resolve_at": "2026-12-31", "p": p,
                "base_rate": 0.5, "info_lock_at": "2026-12-20", "resolution_source": "nso.gov.vn", "calendar_id": "CAL-TEST",
                "author_seat": "Claude Project TTC" if seat == "A" else "Claude trần"}

    def test_brier_calibration_direction_and_fixed_194_sample(self):
        cases = [(0.8, 1), (0.2, 0), (0.9, 0), (0.1, 1), (0.5, 1), (0.5, 0)]
        preds = [self._row(3000 + i, p) for i, (p, _) in enumerate(cases)]
        res = [{"prediction_id": f"F-{3000 + i}", "outcome": o, "resolution_issue": 83000 + i} for i, (_, o) in enumerate(cases)]
        out = engine_ledger.issue_summary(preds, res, [], [self.CAL], {p["id"] for p in preds}, "injected")
        a = out["scores"]["A"]
        self.assertEqual(a["brier"], 0.3667)                                 # (2×0,04 + 2×0,81 + 2×0,25) / 6 — công thức cũ
        self.assertEqual(a["brier_coin"], 0.25)
        self.assertEqual(a["observed_yes_rate"], 0.5)                        # 3 YES / 6
        self.assertEqual(a["hit_rate"], 0.5)                                 # khóa cũ: đúng số cũ
        self.assertEqual((a["directional_correct"], a["directional_n"], a["directional_abstain"], a["directional_accuracy"]),
                         (2, 4, 2, 0.5))                                     # p = 0,5 không vào mẫu số
        self.assertEqual(a["calibration"]["0.5-0.6"], {"n": 2, "mean_p": 0.5, "observed_yes_rate": 0.5, "hit_rate": 0.5})
        self.assertIn("TỰ KHAI", a["baseline_note"])
        # Mẫu 194 và right() của phép thử A–B không đổi; p = 0,5 không tạo bất đồng
        self.assertEqual(engine_ledger.TARGET_DISAGREEMENTS, 194)
        q = "Cặp bất đồng thật có bị đổi luật 194 không?"
        preds += [self._row(3100, 0.2, "A", q), self._row(3101, 0.8, "B", q)]
        res += [{"prediction_id": "F-3100", "outcome": 0, "resolution_issue": 83100},
                {"prediction_id": "F-3101", "outcome": 0, "resolution_issue": 83101}]
        out2 = engine_ledger.issue_summary(preds, res, [], [self.CAL], {p["id"] for p in preds}, "injected")
        self.assertEqual((out2["ab"]["a_correct"], out2["ab"]["disagreements_resolved"], out2["ab"]["fixed_sample"]["n"]), (1, 1, 1))
        self.assertEqual(out2["ab"]["target_disagreements"], 194)
        self.assertTrue(out2["ab"]["verdict"].startswith("CHƯA ĐỦ MẪU"))
        # Không có xác nhận xuất xứ (verified rỗng) → không có điểm năng lực, số thô vẫn đủ
        out3 = engine_ledger.issue_summary(preds, res, [], [self.CAL], set(), "none: test")
        self.assertEqual(out3["scores"], {})
        self.assertEqual(out3["raw_audit"]["scores"]["A"]["brier"], out2["raw_audit"]["scores"]["A"]["brier"])


class Test8Workflows(unittest.TestCase):
    def test_precheck_is_non_blocking_postcheck_is_strict_and_ci_runs_this_file(self):
        import yaml
        wf = yaml.safe_load((ROOT / ".github" / "workflows" / "daily_cycle.yml").read_text(encoding="utf-8"))
        runs = [str(s.get("run", "")) for s in wf["jobs"]["cycle"]["steps"]]
        i_cycle = next(i for i, r in enumerate(runs) if "engine.run_cycle" in r)
        i_commit = next(i for i, r in enumerate(runs) if "git commit" in r)
        pre = [r for r in runs[:i_cycle] if "tools/validate.py" in r]
        post = [r for r in runs[i_cycle + 1:i_commit] if "tools/validate.py" in r]
        self.assertTrue(pre and all("--require-fresh-scorecard" not in r for r in pre), pre)
        self.assertTrue(post and all("--require-fresh-scorecard" in r for r in post), post)
        tests = yaml.safe_load((ROOT / ".github" / "workflows" / "tests.yml").read_text(encoding="utf-8"))
        self.assertIn("test_measurement_integration", tests["jobs"]["gate"]["env"]["UNITTEST"].split())
        steps = [str(s.get("run", "")) for s in tests["jobs"]["gate"]["steps"]]
        self.assertTrue(any(r.strip() == "python tools/validate.py" for r in steps))   # CI trên main không đỏ vì STALE
        self.assertIn("check_scorecard_integrity(root)", (ROOT / "tools" / "laws_checks.py").read_text(encoding="utf-8").split("def run_all")[1])


if __name__ == "__main__":
    unittest.main()
