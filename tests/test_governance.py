"""Quản trị: luật nhận dự báo (L-05, nhóm B), cổng chấm PR (L-09), kiểm toán sổ (chỉ-ghi-thêm, đối chiếu Issue), đề thi (L-10),
công tắc an toàn, và soát các workflow. Mọi thứ chạy trong thư mục tạm; không chạm tệp nào của kho.
"""
import json, os, pathlib, re, shutil, subprocess, sys, tempfile, unittest
from datetime import date

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import laws_checks, ledger_audit, review_gate  # noqa: E402
from tools.ledger_intake import control_b_hash, parse_cutoff, parse_issue_form, vn_day  # noqa: E402

B_HASH = control_b_hash(ROOT / "governance" / "CONTROL_B_PROMPT.md")
WF = ROOT / ".github" / "workflows"


def _forecast(seat="A", question="CPI tháng 11/2026 so với cùng kỳ từ 5,00% trở lên?", **kw):
    f = {"seat": seat, "question": question, "resolution_source": "https://www.nso.gov.vn — thông cáo CPI",
         "resolution_rule": "numeric_range", "resolve_at": "2026-12-10", "p": "0.35", "base_rate": "0.5",
         "invalidation_conditions": "Cục Thống kê đổi rổ hàng", "author_seat": "Claude Project TTC" if seat == "A" else "Claude trần",
         "model_cutoff": "2026-06"}
    if seat == "B":
        f["prompt_hash"] = B_HASH
    f.update(kw)
    return "\n\n".join(f"### {k}\n\n{v}" for k, v in f.items() if v is not None)


class IntakeRuleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        (self.tmp / "contracts").mkdir(); (self.tmp / "governance").mkdir(); (self.tmp / "ledger").mkdir()
        shutil.copy(ROOT / "contracts" / "forecast_issue.schema.json", self.tmp / "contracts")
        shutil.copy(ROOT / "governance" / "CONTROL_B_PROMPT.md", self.tmp / "governance")
        shutil.copytree(ROOT / "tools", self.tmp / "tools", ignore=shutil.ignore_patterns("__pycache__"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _fc(self, number, body, created="2026-11-17T02:00:00Z", **env):
        e = {**os.environ, "ISSUE_NUMBER": str(number), "ISSUE_CREATED_AT": created, "ISSUE_BODY": body, **env}
        r = subprocess.run([sys.executable, str(self.tmp / "tools" / "ledger_intake.py")], env=e, capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr

    def _rows(self):
        p = self.tmp / "ledger" / "predictions.jsonl"
        return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []

    def test_l05_cutoff_and_dates(self):
        for cutoff, why in (("06/2026", "dạng"), ("tháng 6 năm 2026", "dạng"), ("2027-01", "tương lai"), ("2026-13", "dạng")):
            c, o = self._fc(1, _forecast(model_cutoff=cutoff))
            self.assertEqual(c, 2, o); self.assertIn("L-05", o); self.assertIn(why, o)
        c, o = self._fc(2, _forecast(resolve_at="10/12/2026"))
        self.assertEqual(c, 2, o); self.assertIn("YYYY-MM-DD", o)
        # cutoff 2026-11 = hết 30/11, sau ngày tạo 16/11 → từ chối: bảo đảm resolve_at luôn sau ngày cắt dữ liệu
        c, o = self._fc(3, _forecast(resolve_at="2026-11-20", model_cutoff="2026-11"), created="2026-11-16T02:00:00Z")
        self.assertEqual(c, 2, o); self.assertIn("tương lai", o)
        c, o = self._fc(5, _forecast(resolve_at="2026-11-20", model_cutoff="2026-11-10", question="Câu hỏi có cutoff theo ngày?"),
                        created="2026-11-16T02:00:00Z")
        self.assertEqual(c, 0, o)                                                # cutoff 10/11 ≤ tạo 16/11 < giải 20/11
        # ngày tính theo giờ Việt Nam: 16/11 20:00 UTC là 03:00 ngày 17/11 → resolve_at 17/11 không còn "sau ngày tạo"
        c, o = self._fc(4, _forecast(resolve_at="2026-11-17", model_cutoff="2026-06"), created="2026-11-16T20:00:00Z")
        self.assertEqual(c, 2, o); self.assertIn("L-05", o)
        self.assertEqual([r["id"] for r in self._rows()], ["F-5"])
        self.assertEqual(parse_cutoff("2026-06"), date(2026, 6, 30)); self.assertEqual(parse_cutoff("2026-12"), date(2026, 12, 31))
        self.assertEqual(parse_cutoff("2026-02-10"), date(2026, 2, 10)); self.assertIsNone(parse_cutoff("2026-02-31"))
        self.assertEqual(vn_day("2026-11-16T20:00:00Z"), date(2026, 11, 17))

    def test_form_parsing_duplicates_and_decimal_comma(self):
        c, o = self._fc(1, _forecast() + "\n\n### p\n\n0.95")
        self.assertEqual(c, 2, o); self.assertIn("hai tiêu đề", o)               # không đè p bằng tiêu đề chèn thêm
        c, o = self._fc(2, _forecast() + "\n\n### truong_la\n\nx")
        self.assertEqual(c, 2, o)                                                # trường lạ
        c, o = self._fc(3, _forecast(p="0,35", base_rate="0,5"))
        self.assertEqual(c, 0, o)
        self.assertEqual((self._rows()[0]["p"], self._rows()[0]["base_rate"]), (0.35, 0.5))
        with self.assertRaises(ValueError):
            parse_issue_form("### a\n\n1\n\n### a\n\n2")

    def test_control_group_prompt_hash(self):
        self.assertEqual(B_HASH, "d3b1d7c2712cc4428c2456f843c5118b0efc881d5459b290a0e9632b4b207c42")
        c, o = self._fc(1, _forecast("B", prompt_hash=None))
        self.assertEqual(c, 2, o); self.assertIn("prompt_hash", o)               # B thiếu hash
        c, o = self._fc(2, _forecast("B", prompt_hash="d3b1d7c2"))
        self.assertEqual(c, 2, o)                                                # hash cụt
        c, o = self._fc(3, _forecast("A", prompt_hash=B_HASH))
        self.assertEqual(c, 2, o)                                                # A không dùng prompt của B
        (self.tmp / "governance" / "CONTROL_B_PROMPT.md").write_text("```text\nPrompt đã bị sửa\n```\n", encoding="utf-8")
        c, o = self._fc(4, _forecast("B"))
        self.assertEqual(c, 2, o)                                                # prompt trên kho đổi → hash cũ không còn hợp lệ
        self.assertEqual(self._rows(), [])

    def test_one_forecast_per_seat_and_identical_spec(self):
        self.assertEqual(self._fc(1, _forecast("A"))[0], 0)
        c, o = self._fc(2, _forecast("A", p="0.6"))
        self.assertEqual(c, 2, o); self.assertIn("mỗi ghế một dự báo", o)
        c, o = self._fc(3, _forecast("B", resolution_rule="comparison"))
        self.assertEqual(c, 2, o); self.assertIn("cùng luật", o)
        c, o = self._fc(4, _forecast("B", resolution_source="https://vnexpress.net"))
        self.assertEqual(c, 2, o)
        c, o = self._fc(5, _forecast("B", resolve_at="2026-12-20"))
        self.assertEqual(c, 2, o); self.assertIn("cùng resolve_at", o)
        c, o = self._fc(6, _forecast("B", question="CPI   tháng 11/2026 so với cùng kỳ từ 5,00% TRỞ LÊN?"))   # khác khoảng trắng/hoa thường: cùng câu hỏi
        self.assertEqual(c, 0, o)
        c, o = self._fc(7, _forecast("B", question="Câu hỏi khác hẳn có ngưỡng 4,60%?"), created="2026-11-18T02:00:00Z")
        self.assertEqual(c, 0, o)
        self.assertEqual(self._fc(8, _forecast("A", question="Câu hỏi khác hẳn có ngưỡng 4,60%?"), created="2026-11-19T02:00:00Z")[0], 0)
        self.assertIn("Khác ngày", self._fc(9, _forecast("B", question="Câu thứ ba?", p="0.4"), created="2026-11-17T02:00:00Z")[1] +
                      self._fc(10, _forecast("A", question="Câu thứ ba?"), created="2026-11-19T02:00:00Z")[1])
        self.assertEqual(laws_checks.check_ledger_chain(self.tmp), [])

    def test_unicode_nfd_text_is_normalised(self):
        """Chữ Việt dạng tổ hợp (NFD) không được lọt luật so chuỗi: L-02, khóa câu hỏi, cổng chấm."""
        import unicodedata
        nfd = lambda t: unicodedata.normalize("NFD", t)
        self.assertEqual(laws_checks.recommendation_hit(nfd("VCB: nên mua trước khi công bố?")), "nên mua")
        c, o = self._fc(1, _forecast(question=nfd("VCB: nên mua trước khi công bố BCTC?")))
        self.assertEqual(c, 2, o); self.assertIn("L-02", o)
        self.assertEqual(self._fc(2, _forecast("A"))[0], 0)
        c, o = self._fc(3, _forecast("B", question=nfd("CPI tháng 11/2026 so với cùng kỳ từ 5,00% trở lên?")))
        self.assertEqual(c, 0, o)                                                # B dán dạng NFD vẫn là cùng câu hỏi với A
        rows = self._rows()
        self.assertEqual(rows[0]["question"], rows[1]["question"])
        ev = laws_checks.check_review_evidence([{"user": "chu-kho", "body": nfd("GỘP ĐƯỢC — commit 243eab8")}], "243eab8" + "0" * 33, "chu-kho")
        self.assertEqual(ev, [])
        self.assertIn("openai", laws_checks._providers(nfd("ghế Minh Trí")))

    def test_only_repo_owner_and_author_recorded(self):
        c, o = self._fc(1, _forecast(), ISSUE_AUTHOR="nguoi-la", REPO_OWNER="chu-kho")
        self.assertEqual(c, 2, o); self.assertIn("chủ kho", o)
        c, o = self._fc(2, _forecast(), ISSUE_AUTHOR="Chu-Kho", REPO_OWNER="chu-kho")
        self.assertEqual(c, 0, o)
        self.assertEqual(self._rows()[0]["issue_author"], "Chu-Kho")


class ReviewGateTests(unittest.TestCase):
    BODY = "## Ghế (L-09)\nauthored_by: Claude (Anthropic) — kiến trúc sư trưởng\nreviewed_by: ChatGPT (OpenAI)\n"
    SHA = "243eab82faad9b31b1b4171b7e8477ad015b7788"

    def _ev(self, comments, body=None, sha=None, owner="chu-kho"):
        return review_gate.evaluate(self.BODY if body is None else body, comments, sha or self.SHA, owner)

    def test_review_must_be_on_repo_for_the_exact_commit(self):
        ok = {"user": "chu-kho", "body": "GỘP ĐƯỢC — commit 243eab8\n\nKhông còn lỗi HIGH/MEDIUM."}
        self.assertEqual(self._ev([ok]), [])
        self.assertEqual(self._ev([{"user": "Chu-Kho", "body": "**GỘP ĐƯỢC**\n\nĐã kiểm commit `243eab82faad`."}]), [])
        self.assertTrue(self._ev([]))                                                        # chưa dán bản chấm
        self.assertTrue(self._ev([{"user": "nguoi-la", "body": ok["body"]}]))                # không phải chủ kho đăng
        self.assertTrue(self._ev([{"user": "chu-kho", "body": "SỬA TRƯỚC — commit 243eab8\n\nGỘP ĐƯỢC sau khi sửa."}]))   # dòng đầu không phải GỘP ĐƯỢC
        self.assertTrue(self._ev([{"user": "chu-kho", "body": "GỘP ĐƯỢC — commit 4327633"}]))  # bản chấm của commit cũ
        self.assertTrue(self._ev([ok], sha="f" * 40))                                        # đẩy commit mới → phải chấm lại
        self.assertTrue(self._ev([{"user": "chu-kho", "body": "<!-- GỘP ĐƯỢC 243eab8 -->\nđang xem"}]))   # giấu trong chú thích
        # thân PR sai thì không xét tới bản chấm
        errs = self._ev([ok], body="authored_by: Claude\nreviewed_by: Claude Sonnet\n")
        self.assertEqual(len(errs), 1); self.assertIn("cùng ghế", errs[0])
        self.assertIn("chưa có người chấm", self._ev([ok], body="authored_by: Claude\nreviewed_by: \n")[0])


class LedgerAuditTests(unittest.TestCase):
    def test_append_only_pure(self):
        f = ledger_audit.append_only_errors
        p = "ledger/predictions.jsonl"
        self.assertEqual(f({p: None}, {p: b"a\n"}), [])
        self.assertEqual(f({p: b"a\n"}, {p: b"a\nb\n"}), [])
        self.assertTrue(f({p: b"a\nb\n"}, {p: b"a\n"}))                       # xóa dòng cuối
        self.assertTrue(f({p: b"a\nb\n"}, {p: b"x\nb\nc\n"}))                 # sửa dòng đầu
        self.assertTrue(f({p: b"a\nb\n"}, {p: b"a\nz\nb\n"}))                 # chèn giữa
        self.assertTrue(f({p: b"a\n"}, {p: None}))                            # xóa tệp
        self.assertIn("dòng 2", f({p: b"a\nb\n"}, {p: b"a\nB\n"})[0])

    def test_append_only_against_real_git_history(self):
        tmp = pathlib.Path(tempfile.mkdtemp())
        try:
            def git(*a): return subprocess.run(["git", "-C", str(tmp), "-c", "user.name=t", "-c", "user.email=t@t", *a], capture_output=True, text=True)
            git("init", "-q"); (tmp / "ledger").mkdir(); (tmp / "tools").mkdir()
            shutil.copy(ROOT / "tools" / "ledger_audit.py", tmp / "tools"); shutil.copy(ROOT / "tools" / "laws_checks.py", tmp / "tools")
            led = tmp / "ledger" / "predictions.jsonl"
            led.write_text('{"id": "F-1"}\n{"id": "F-2"}\n', encoding="utf-8")
            git("add", "-A"); git("commit", "-qm", "base"); base = git("rev-parse", "HEAD").stdout.strip()
            run = lambda: subprocess.run([sys.executable, str(tmp / "tools" / "ledger_audit.py"), "--base", base], capture_output=True, text=True)
            led.write_text('{"id": "F-1"}\n{"id": "F-2"}\n{"id": "F-3"}\n', encoding="utf-8")
            self.assertEqual(run().returncode, 0, run().stdout)               # ghi thêm: đạt
            led.write_text('{"id": "F-1"}\n{"id": "F-3"}\n', encoding="utf-8")
            r = run(); self.assertEqual(r.returncode, 1); self.assertIn("chỉ-ghi-thêm", r.stdout)    # xóa F-2
            r = subprocess.run([sys.executable, str(tmp / "tools" / "ledger_audit.py"), "--base", "1" * 40], capture_output=True, text=True)
            self.assertEqual(r.returncode, 1); self.assertIn("không đọc được commit gốc", r.stdout)   # lịch sử bị viết lại
            r = subprocess.run([sys.executable, str(tmp / "tools" / "ledger_audit.py"), "--base", "0" * 40], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0)                                 # nhánh mới tạo: không có gốc
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_issue_crosscheck(self):
        f = ledger_audit.issue_crosscheck_errors
        pred = [{"id": "F-7", "issue_number": 7, "issue_created_at": "2026-11-17T02:00:00Z"}, {"id": "P-abc"}]
        res = [{"prediction_id": "F-7", "resolution_issue": 9, "resolution_issue_created_at": "2027-01-05T03:00:00Z"},
               {"prediction_id": "F-8", "resolution_issue": 9, "resolution_issue_created_at": "2027-01-05T03:00:00Z"},
               {"prediction_id": "P-abc"}]
        issues = {7: {"created_at": "2026-11-17T02:00:00Z", "user": "Chu-Kho", "is_pr": False},
                  9: {"created_at": "2027-01-05T03:00:00Z", "user": "chu-kho", "is_pr": False}}
        self.assertEqual(f(pred, res, issues, "chu-kho"), [])
        self.assertTrue(f(pred, res, {9: issues[9]}, "chu-kho"))                                   # Issue không tồn tại
        self.assertTrue(f(pred, res, {**issues, 7: {**issues[7], "created_at": "2026-11-01T00:00:00Z"}}, "chu-kho"))   # lùi ngày
        self.assertTrue(f(pred, res, {**issues, 7: {**issues[7], "user": "nguoi-la"}}, "chu-kho"))  # người khác mở
        self.assertTrue(f(pred, res, {**issues, 9: {**issues[9], "is_pr": True}}, "chu-kho"))      # trỏ vào PR
        self.assertEqual(len(f(pred, res, {7: issues[7]}, "chu-kho")), 1)                          # #9 chỉ báo một lần


class ExamAndSafetyTests(unittest.TestCase):
    def test_exams_only_after_release(self):
        tmp = pathlib.Path(tempfile.mkdtemp())
        try:
            (tmp / "contracts").mkdir(); (tmp / "academy" / "exams").mkdir(parents=True)
            shutil.copy(ROOT / "contracts" / "exam_item.schema.json", tmp / "contracts")
            item = {"exam_id": "EX-2026-001", "kind": 1, "question": "Nêu điều kiện ghi nhận doanh thu theo VAS 14", "competency": "doc_bctc",
                    "answer_key": None, "authored_by": "Claude", "held_out": False, "released_at": "2026-11-01", "grading": "CHAIN"}
            p = tmp / "academy" / "exams" / "de1.json"
            today = date(2026, 11, 17)
            def errs(**kw):
                p.write_text(json.dumps({**item, **kw}), encoding="utf-8")
                return laws_checks.check_exams(tmp, today)
            self.assertEqual(errs(), [])                                              # đã thi, đã phát hành
            self.assertTrue(any("tương lai" in e for e in errs(released_at="2027-03-01")))   # đề chưa thi nằm trong kho
            self.assertTrue(any("chưa có released_at" in e for e in errs(released_at=None)))
            self.assertTrue(errs(exam_id="de-so-1"))                                  # sai hợp đồng
            p.write_text("không phải json", encoding="utf-8")
            self.assertTrue(laws_checks.check_exams(tmp, today))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_safety_switch_flip_fails_validate(self):
        tmp = pathlib.Path(tempfile.mkdtemp()) / "repo"
        try:
            shutil.copytree(ROOT, tmp, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", "*.gz", "reports", "paper"))
            run = lambda: subprocess.run([sys.executable, str(tmp / "tools" / "validate.py")], capture_output=True, text=True, cwd=str(tmp))
            r = run(); self.assertEqual(r.returncode, 0, r.stdout[-1500:] + r.stderr[-1500:])
            s = tmp / "governance" / "SAFETY_STATE.yaml"
            s.write_text(s.read_text(encoding="utf-8").replace("live_trading_enabled: false", "live_trading_enabled: true"), encoding="utf-8")
            r = run(); self.assertEqual(r.returncode, 1); self.assertIn("AN TOÀN", r.stdout)
        finally:
            shutil.rmtree(tmp.parent, ignore_errors=True)


class WorkflowLintTests(unittest.TestCase):
    """Soát các workflow: lỗi ở đây không có test nào khác bắt được trước khi lên GitHub."""
    def setUp(self):
        self.wf = {p.name: (p.read_text(encoding="utf-8"), yaml.safe_load(p.read_text(encoding="utf-8"))) for p in sorted(WF.glob("*.yml"))}

    def test_no_user_controlled_value_inside_run(self):
        """Giá trị do người dùng nhập (thân/tiêu đề Issue, PR, kết quả bước trước) chỉ được đi qua env, không chèn vào lệnh."""
        bad = re.compile(r"\$\{\{\s*(github\.event\.(issue|pull_request|comment)\.(body|title)|steps\.[a-z_]+\.outputs\.result|github\.head_ref)")
        for name, (_, d) in self.wf.items():
            for job in d["jobs"].values():
                for step in job["steps"]:
                    self.assertIsNone(bad.search(step.get("run", "")), f"{name}: bước '{step.get('name')}' chèn giá trị người dùng vào lệnh")

    def test_intake_workflows_only_on_open_by_owner(self):
        for name in ("ledger_intake.yml", "resolution_intake.yml"):
            text, d = self.wf[name]
            on = d.get("on", d.get(True))                                     # YAML đọc khóa "on" thành True
            self.assertEqual(on["issues"]["types"], ["opened"], name)        # không nhận labeled/edited (L-05)
            cond = d["jobs"]["intake"]["if"]
            self.assertIn("github.event.issue.user.login == github.repository_owner", cond, name)
            self.assertIn("jsonschema", text, name)                           # intake cần jsonschema để kiểm hợp đồng
            self.assertNotIn("cancel-in-progress: true", text, name)
            self.assertIn("github.event.issue.number", d["concurrency"]["group"], name)   # không dùng nhóm chung (mất dự báo)
            env = [s for s in d["jobs"]["intake"]["steps"] if s.get("id") == "intake"][0]["env"]
            self.assertEqual(set(env), {"ISSUE_NUMBER", "ISSUE_CREATED_AT", "ISSUE_BODY", "ISSUE_AUTHOR", "REPO_OWNER"}, name)

    def test_tests_workflow_runs_every_test_file_and_audits(self):
        text, d = self.wf["tests.yml"]
        env = d["jobs"]["gate"]["env"]
        listed = set((env["UNITTEST"] + " " + env["SCRIPTS"]).split())
        on_disk = {p.stem for p in (ROOT / "tests").glob("test_*.py")}
        self.assertEqual(listed, on_disk)                                     # không test nào bị bỏ sót hoặc khai thừa
        self.assertIn("tools/ledger_audit.py", text)
        self.assertIn("git status --porcelain", text)
        self.assertNotIn("continue-on-error", text)

    def test_cycle_validates_before_and_after_and_rebases(self):
        text, d = self.wf["daily_cycle.yml"]
        runs = [s.get("run", "") for s in d["jobs"]["cycle"]["steps"]]
        i_engine = next(i for i, r in enumerate(runs) if "engine.run_cycle" in r)
        self.assertTrue(any("tools/validate.py" in r for r in runs[:i_engine]))
        self.assertTrue(any("tools/validate.py" in r for r in runs[i_engine + 1:]))     # kết quả trái luật thì không ghi
        self.assertIn("git pull -q --rebase origin main", text)
        on = d.get("on", d.get(True))
        self.assertEqual(on["schedule"][0]["cron"], "30 9 * * 5")            # hằng tuần, thứ Sáu (ARCHITECTURE §4.3)

    def test_review_gate_uses_base_branch_code_and_api(self):
        text, d = self.wf["review_gate.yml"]
        on = d.get("on", d.get(True))
        self.assertIn("pull_request_target", on); self.assertIn("pull_request", on)
        steps = d["jobs"]["l09"]["steps"]
        self.assertFalse(any("ref" in (s.get("with") or {}) for s in steps))  # không check out mã của PR ở pull_request_target
        self.assertIn("tools/review_gate.py", text)
        self.assertEqual(d["permissions"], {"contents": "read", "pull-requests": "read", "issues": "read"})


class DocsConsistencyTests(unittest.TestCase):
    def test_adr_maps_every_law_to_a_machine_check_that_exists(self):
        adr = (ROOT / "architecture" / "adr" / "ADR-0003-phan-dinh-va-van-hanh.md").read_text(encoding="utf-8")
        for n in range(1, 11):
            self.assertIn(f"| L-{n:02d} ", adr, f"ADR-0003 thiếu dòng đối chiếu L-{n:02d}")
        for path in set(re.findall(r"`((?:tools|engine|tests|\.github)/[A-Za-z0-9_./-]+\.(?:py|yml|md))`", adr)):
            self.assertTrue((ROOT / path).is_file(), f"ADR-0003 dẫn tệp không tồn tại: {path}")

    def test_laws_file_untouched_names_ten_laws(self):
        laws = (ROOT / "governance" / "LAWS.md").read_text(encoding="utf-8")
        for n in range(1, 11):
            self.assertIn(f"**L-{n:02d} ", laws)


if __name__ == "__main__":
    unittest.main()
