"""Quản trị: luật nhận dự báo (L-05, nhóm B), cổng chấm PR (L-09), kiểm toán sổ (chỉ-ghi-thêm, đối chiếu Issue), đề thi (L-10),
công tắc an toàn, và soát các workflow. Mọi thứ chạy trong thư mục tạm; không chạm tệp nào của kho.
"""
import json, os, pathlib, re, shutil, subprocess, sys, tempfile, unittest
from datetime import date, datetime, timedelta, timezone

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import laws_checks, ledger_audit, review_gate  # noqa: E402
from tools.ledger_intake import control_b_hash, dumps, parse_cutoff, parse_issue_form, parse_number, promised_domains, vn_day  # noqa: E402

B_HASH = control_b_hash(ROOT / "governance" / "CONTROL_B_PROMPT.md")
WF = ROOT / ".github" / "workflows"


def _just_after(created, seconds=60):
    """Giờ robot chạy trong test (TTC_INTAKE_NOW): mặc định một phút sau khi Issue mở, như khi workflow chạy thật."""
    return (datetime.fromisoformat(created.replace("Z", "+00:00")) + timedelta(seconds=seconds)).isoformat()


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
        for c in ("forecast_issue.schema.json", "resolution.schema.json"):       # robot nhận tự chạy lại luật của CẢ hai sổ trước khi ghi
            shutil.copy(ROOT / "contracts" / c, self.tmp / "contracts")
        for g in ("CONTROL_B_PROMPT.md", "control_b_prompts.jsonl"):
            shutil.copy(ROOT / "governance" / g, self.tmp / "governance")
        shutil.copytree(ROOT / "tools", self.tmp / "tools", ignore=shutil.ignore_patterns("__pycache__"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _fc(self, number, body, created="2026-11-17T02:00:00Z", **env):
        e = {**os.environ, "ISSUE_NUMBER": str(number), "ISSUE_CREATED_AT": created, "ISSUE_BODY": body,
             "TTC_INTAKE_NOW": _just_after(created), **env}
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

    def test_numbers_must_be_finite_plain_decimals(self):
        """float() của Python nhận 'NaN', 'inf', '1e309', '1_0', chữ số Ả Rập; NaN lọt cả minimum/maximum của JSON Schema và
        json.dumps ghi ra 'NaN' — không phải JSON. Không giá trị nào trong số đó được vào sổ."""
        for i, bad in enumerate(("NaN", "nan", "Infinity", "-Infinity", "inf", "1e309", "1e-1", "0_5", "٠.٥", "0.35%", "-0.5", "9" * 400), 1):
            for field in ("p", "base_rate"):
                c, o = self._fc(i, _forecast(**{field: bad}))
                self.assertEqual(c, 2, f"{field}={bad}: {o}")
        self.assertEqual(self._rows(), [])
        self.assertFalse((self.tmp / "ledger" / "predictions.jsonl").exists())
        self.assertIsNone(parse_number("NaN")); self.assertIsNone(parse_number("1e309")); self.assertEqual(parse_number("0,35"), 0.35)
        with self.assertRaises(ValueError):
            dumps({"p": float("nan")})                                           # tầng cuối: không bao giờ ghi NaN ra sổ
        # sổ đã có dòng chứa NaN (ghi tay) → kiểm chuỗi báo lỗi thay vì đọc như số
        led = self.tmp / "ledger" / "predictions.jsonl"
        led.write_text('{"hash": "x", "p": NaN, "prev_hash": "GENESIS"}\n', encoding="utf-8")
        self.assertTrue(any("JSON chuẩn" in e for e in laws_checks.check_ledger_chain(self.tmp)))

    def test_strict_dates_and_promised_source_domain(self):
        for i, ra in enumerate(("20261210", "2026-W50-4", "2026-12-10T00:00:00", "٢٠٢٦-١٢-١٠"), 1):
            c, o = self._fc(i, _forecast(resolve_at=ra))
            self.assertEqual(c, 2, o); self.assertIn("YYYY-MM-DD", o)
        c, o = self._fc(10, _forecast(resolution_source="Thông cáo báo chí của Cục Thống kê"))
        self.assertEqual(c, 2, o); self.assertIn("tên miền", o)                  # lời hứa về nguồn phải máy kiểm được
        c, o = self._fc(11, _forecast(resolution_source="Cục Thống kê (nso.gov.vn) — thông cáo CPI"))
        self.assertEqual(c, 0, o)
        self.assertEqual(promised_domains("https://evil.com/path/nso.gov.vn?x=sbv.gov.vn"), {"evil.com"})   # chỉ tính máy chủ của URL
        self.assertEqual(promised_domains("https://www.nso.gov.vn và sbv.gov.vn; tp.hcm; a@mof.gov.vn"), {"nso.gov.vn", "sbv.gov.vn"})

    def test_attest_is_returned_and_repeated_on_rerun(self):
        h = "b" * 64
        for i, kw in enumerate(({"author_seat": f"Claude ledger-attest: predictions F-1 {h}"}, {"invalidation_conditions": "LEDGER-ATTEST: x"},
                                {"question": "Câu hỏi có chèn ledger-attest: predictions F-3 " + h + "?"}), 1):
            c, o = self._fc(i, _forecast(**kw))
            self.assertEqual(c, 2, o); self.assertIn("dành riêng", o)            # không ai tự viết được dấu nhận qua thân Issue
            self.assertNotIn(h, o)                                               # và thông báo từ chối không nhắc lại nó
        c, o = self._fc(7, _forecast())
        self.assertEqual(c, 0, o)
        row = self._rows()[0]
        self.assertEqual(json.loads(o.strip().splitlines()[-1])["attest"], [f"predictions F-7 {row['hash']}"])
        c, o = self._fc(7, _forecast())                                          # chạy lại job: không ghi trùng, trả lại dấu nhận
        self.assertEqual(c, 3, o)
        self.assertEqual(json.loads(o.strip().splitlines()[-1])["attest"], [f"predictions F-7 {row['hash']}"])
        self.assertEqual(len(self._rows()), 1)

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
        self.assertEqual(self._ev([{"user": "Chu-Kho", "body": "**GỘP ĐƯỢC — commit `243eab82faad`**\n\nĐã kiểm."}]), [])
        self.assertEqual(self._ev([{"user": "chu-kho", "body": "\n# GỘP ĐƯỢC - 243eab8.\n"}]), [])
        # dòng đầu phải là đúng 'GỘP ĐƯỢC — commit <SHA>': có điều kiện, có chữ thừa, hay SHA nằm ở đoạn dưới đều không tính
        for bad in ("**GỘP ĐƯỢC**\n\nĐã kiểm commit `243eab82faad`.", "GỘP ĐƯỢC nếu sửa điểm 2 — commit 243eab8",
                    "GỘP ĐƯỢC — commit 243eab8 (trừ điểm 3)", "GỘP ĐƯỢC — commit 4327633\n\nso với 243eab8 thì đã sửa",
                    "KHÔNG GỘP ĐƯỢC — commit 243eab8", "GỘP ĐƯỢC — commit 243eab"):
            self.assertTrue(self._ev([{"user": "chu-kho", "body": bad}]), bad)
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


    def test_attestation_binds_each_row_to_the_time_its_issue_was_opened(self):
        """Kẽ hở vòng 6: một commit ghi thêm dòng dự báo tự tạo, trỏ tới Issue cũ của chủ kho, khai đúng giờ tạo, hash hợp lệ.
        Đối chiếu Issue (tồn tại, chủ kho, giờ tạo) không bắt được. Dấu nhận thì bắt: Issue đó không có bình luận của
        github-actions[bot] đăng lúc Issue mở chứa hash của dòng."""
        f = ledger_audit.attestation_errors
        h1, h2, hr = "a" * 64, "b" * 64, "c" * 64
        pred = [{"id": "F-7", "issue_number": 7, "issue_created_at": "2026-11-17T02:00:00Z", "hash": h1, "resolve_at": "2026-12-10"},
                {"id": "P-abc", "hash": "z"}]
        res = [{"prediction_id": "F-7", "resolution_issue": 9, "resolution_issue_created_at": "2027-01-05T03:00:00Z", "hash": hr},
               {"prediction_id": "P-abc"}]
        issues = {7: {"created_at": "2026-11-17T02:00:00Z", "user": "chu-kho", "is_pr": False},
                  8: {"created_at": "2026-10-29T19:15:04Z", "user": "chu-kho", "is_pr": False},
                  9: {"created_at": "2027-01-05T03:00:00Z", "user": "chu-kho", "is_pr": False}}
        bot = lambda at, body, upd=None, user="github-actions[bot]": {"user": user, "created_at": at, "updated_at": upd or at, "body": body}
        c7 = bot("2026-11-17T02:01:10Z", f"✅ Đã ghi dự báo #7\n\n`ledger-attest: predictions F-7 {h1}`")
        c9 = bot("2027-01-05T03:00:50Z", f"✅ Đã phân định\n`ledger-attest: resolutions F-7 {hr}`")
        ok = {7: [c7], 9: [c9]}
        self.assertEqual(f(pred, res, issues, ok), [])
        # dòng giả mượn giờ của Issue #8 (mở 29/10): không có dấu nhận
        forged = pred + [{"id": "F-8", "issue_number": 8, "issue_created_at": "2026-10-29T19:15:04Z", "hash": h2, "resolve_at": "2026-11-10"}]
        errs = f(forged, res, issues, ok)
        self.assertEqual(len(errs), 1); self.assertIn("Issue #8", errs[0])
        # …kể cả khi nay mới cho bot đăng dấu nhận (giờ đăng do GitHub ghi, cách giờ mở Issue quá 6 giờ)
        late = {**ok, 8: [bot("2027-01-20T00:00:00Z", f"✅\n`ledger-attest: predictions F-8 {h2}`")]}
        self.assertIn("quá 6 giờ", f(forged, res, issues, late)[0])
        self.assertIn("quá 6 giờ", f(pred, res, issues, {**ok, 7: [bot("2026-11-17T08:00:01Z", c7["body"])]})[0])
        self.assertEqual(f(pred, res, issues, {**ok, 7: [bot("2026-11-17T07:59:59Z", c7["body"])]}), [])
        # dự báo mở 23:30 ngày 9/12 (giờ VN), resolve_at 10/12: dấu nhận đăng 00:10 ngày 10/12 là đã sang ngày phân định
        eve = [{"id": "F-7", "issue_number": 7, "issue_created_at": "2026-12-09T16:30:00Z", "hash": h1, "resolve_at": "2026-12-10"}]
        iss = {7: {"created_at": "2026-12-09T16:30:00Z", "user": "chu-kho", "is_pr": False}}
        self.assertEqual(f(eve, [], iss, {7: [bot("2026-12-09T16:31:00Z", c7["body"])]}), [])
        self.assertIn("không trước ngày resolve_at", f(eve, [], iss, {7: [bot("2026-12-09T17:10:00Z", c7["body"])]})[0])
        # bot đăng HAI hash cho cùng mã (đặt trước hai nội dung để về sau chọn một) → không dòng nào được nhận
        two = {**ok, 7: [c7, bot("2026-11-17T02:02:00Z", f"✅\n`ledger-attest: predictions F-7 {h2}`")]}
        self.assertIn("hash khác cho cùng mã", f(pred, res, issues, two)[0])
        one = {**ok, 7: [bot("2026-11-17T02:01:10Z", f"✅ x\n`ledger-attest: predictions F-7 {h1}`\n`ledger-attest: predictions F-7 {h2}`")]}
        self.assertIn("hash khác cho cùng mã", f(pred, res, issues, one)[0])
        # dấu nhận lọt vào bình luận ❌ (thông báo từ chối nhắc lại chữ người dùng nhập) không được tính
        self.assertIn("không phải thông báo ✅", f(pred, res, issues, {**ok, 7: [bot("2026-11-17T02:01:10Z", f"❌ Từ chối: author_seat 'ledger-attest: predictions F-7 {h1}'")]})[0])
        # …hay chủ kho tự đăng, hay sửa bình luận cũ của bot để chèn hash mới, hay dấu nhận của dòng khác/hash khác
        self.assertIn("không phải github-actions[bot]", f(pred, res, issues, {**ok, 7: [bot("2026-11-17T02:01:10Z", c7["body"], user="chu-kho")]})[0])
        self.assertIn("đã bị sửa", f(pred, res, issues, {**ok, 7: [bot("2026-11-17T02:01:10Z", c7["body"], upd="2027-01-20T00:00:00Z")]})[0])
        self.assertTrue(f(pred, res, issues, {**ok, 7: [bot("2026-11-17T02:01:10Z", f"✅\n`ledger-attest: predictions F-7 {h2}`")]}))
        self.assertTrue(f(pred, res, issues, {**ok, 7: [bot("2026-11-17T02:01:10Z", f"✅\n`ledger-attest: predictions F-7 {h1[:12]}`")]}))
        self.assertTrue(f(pred, res, issues, {**ok, 7: [bot("2026-11-17T02:01:10Z", f"✅\n`ledger-attest: resolutions F-7 {h1}`")]}))   # sai sổ
        self.assertTrue(f(pred, res, issues, {**ok, 7: [bot("2026-11-17T02:01:10Z", f"✅\n`ledger-attest: predictions F-70 {h1}`")]}))  # sai mã
        self.assertTrue(f(pred, res, issues, {**ok, 7: [bot("2026-11-17T01:59:00Z", c7["body"])]}))    # đăng TRƯỚC khi Issue mở
        self.assertTrue(f(pred, res, issues, {7: [c7]}))                                              # phân định thiếu dấu nhận
        # vòng 7 điểm 4: không có khoảng miễn kiểm — Issue vừa mở mà dòng chưa có dấu nhận vẫn là lỗi, không phải cảnh báo
        self.assertTrue(f(pred, [], issues, {}))
        self.assertFalse(hasattr(ledger_audit, "ATTEST_GRACE"))

    def test_recovery_without_rewriting_the_ledger(self):
        """Vòng 8 điểm 1 (phần "cơ chế phục hồi không phá tính chỉ-ghi-thêm"). Sổ không sửa được, nên một dòng đã ghi mà thiếu
        bằng chứng phải có đường xử lý bằng cách GHI THÊM:
        - dòng phân định: dấu nhận không có hạn 6 giờ → chạy lại job phân định lúc nào cũng bổ sung được;
        - dòng dự báo: quá hạn 6 giờ thì không bổ sung được nữa (đó chính là thứ chặn mượn giờ Issue cũ) → hủy câu hỏi bằng VOID;
          dự báo đã VOID bằng dòng phân định có dấu nhận thì không bao giờ được chấm, nên không bị đòi dấu nhận nữa."""
        f = ledger_audit.attestation_errors
        h1, h2, hv1, hv2 = "a" * 64, "b" * 64, "c" * 64, "d" * 64
        pred = [{"id": "F-7", "issue_number": 7, "issue_created_at": "2026-11-17T02:00:00Z", "hash": h1, "resolve_at": "2026-12-10"},
                {"id": "F-8", "issue_number": 8, "issue_created_at": "2026-11-17T02:05:00Z", "hash": h2, "resolve_at": "2026-12-10"}]
        void = [{"prediction_id": "F-7", "resolution_issue": 9, "resolution_issue_created_at": "2026-11-18T03:00:00Z", "hash": hv1, "outcome": None, "void": "F-8 thiếu dấu nhận"},
                {"prediction_id": "F-8", "resolution_issue": 9, "resolution_issue_created_at": "2026-11-18T03:00:00Z", "hash": hv2, "outcome": None, "void": "F-8 thiếu dấu nhận"}]
        issues = {n: {"created_at": at, "user": "chu-kho", "is_pr": False}
                  for n, at in ((7, "2026-11-17T02:00:00Z"), (8, "2026-11-17T02:05:00Z"), (9, "2026-11-18T03:00:00Z"))}
        bot = lambda at, body: {"user": "github-actions[bot]", "created_at": at, "updated_at": at, "body": body}
        c7 = bot("2026-11-17T02:01:00Z", f"✅\n`ledger-attest: predictions F-7 {h1}`")
        c9 = bot("2026-11-18T03:01:00Z", f"✅ Đã phân định\n`ledger-attest: resolutions F-7 {hv1}`\n`ledger-attest: resolutions F-8 {hv2}`")
        # F-8 đã nằm trong sổ nhưng bình luận ✅ không đăng được; quá 6 giờ, chạy lại job chỉ cho dấu nhận muộn → vẫn lỗi
        errs = f(pred, [], issues, {7: [c7]})
        self.assertEqual(len(errs), 1); self.assertIn("Issue #8", errs[0]); self.assertIn("VOID", errs[0])   # lỗi chỉ đường phục hồi
        late8 = bot("2026-11-17T09:00:00Z", f"✅ Dự báo #8 đã có trong Ledger\n`ledger-attest: predictions F-8 {h2}`")
        self.assertIn("quá 6 giờ", f(pred, [], issues, {7: [c7], 8: [late8]})[0])
        # hủy câu hỏi bằng VOID (ghi thêm, có dấu nhận) + dấu nhận muộn của robot cho F-8 → sổ xanh lại; in ra, không im lặng
        notes = []
        self.assertEqual(ledger_audit.attestation_failures(pred, void, issues, {7: [c7], 8: [late8], 9: [c9]}, notes), [])
        self.assertTrue(len(notes) == 1 and "F-8" in notes[0] and "VOID" in notes[0] and "Issue #9" in notes[0], notes)
        # VOID không gỡ được cho dòng KHÔNG có dấu nhận nào của robot (dòng ghi tay), hay dấu nhận do người khác đăng, bị sửa,
        # đăng trước khi Issue mở, hoặc robot đăng hai hash
        for c8 in ([], [{**late8, "user": "chu-kho"}], [{**late8, "updated_at": "2026-11-18T00:00:00Z"}],
                   [bot("2026-11-17T02:04:00Z", late8["body"])], [late8, bot("2026-11-17T09:01:00Z", f"✅\n`ledger-attest: predictions F-8 {h1}`")],
                   [bot("2026-11-17T09:00:00Z", f"❌ Từ chối 'ledger-attest: predictions F-8 {h2}'")]):
            errs = f(pred, void, issues, {7: [c7], 8: c8, 9: [c9]})
            self.assertEqual(len(errs), 1, c8); self.assertIn("dự báo F-8", errs[0])
        # …và chỉ khi chính dòng VOID có dấu nhận hợp lệ, và chỉ VOID: kết quả YES/NO không gỡ được lỗi dấu nhận của dự báo
        errs = f(pred, void, issues, {7: [c7], 8: [late8]})
        self.assertEqual(len(errs), 3, errs)                                     # F-8 và hai dòng VOID
        self.assertEqual(len(f(pred, void, issues, {7: [c7], 8: [late8], 9: [bot("2026-11-18T03:01:00Z", f"✅\n`ledger-attest: resolutions F-7 {hv1}`")]})), 2)
        yes = [{**r, "outcome": 1} for r in void]
        errs = f(pred, yes, issues, {7: [c7], 8: [late8], 9: [c9]})
        self.assertEqual(len(errs), 1); self.assertIn("dự báo F-8", errs[0])
        self.assertEqual(len(f(pred, [{k: v for k, v in r.items() if k != "outcome"} for r in void], issues, {7: [c7], 8: [late8], 9: [c9]})), 1)
        # một dự báo có dấu nhận đúng hạn thì VOID không sinh ghi chú nào
        notes = []
        c8 = bot("2026-11-17T02:06:00Z", f"✅\n`ledger-attest: predictions F-8 {h2}`")
        self.assertEqual(ledger_audit.attestation_failures(pred, void, issues, {7: [c7], 8: [c8], 9: [c9]}, notes), []); self.assertEqual(notes, [])
        # dòng phân định: dấu nhận đăng muộn (job chạy lại sau một tháng) vẫn hợp lệ; đăng TRƯỚC giờ tạo Issue, bị sửa, sai hash thì không
        month = bot("2026-12-20T00:00:00Z", c9["body"])
        self.assertEqual(f(pred[:1], void[:1], issues, {7: [c7], 9: [month]}), [])
        self.assertIn("trước cả giờ tạo Issue", f(pred[:1], void[:1], issues, {7: [c7], 9: [bot("2026-11-18T02:59:00Z", c9["body"])]})[0])
        self.assertIn("đã bị sửa", f(pred[:1], void[:1], issues, {7: [c7], 9: [{**month, "updated_at": "2026-12-21T00:00:00Z"}]})[0])
        self.assertIn("hash khác cho cùng mã", f(pred[:1], void[:1], issues, {7: [c7], 9: [month, bot("2026-12-20T00:01:00Z", f"✅\n`ledger-attest: resolutions F-7 {h2}`")]})[0])
        # đối chiếu Issue thật không được nới: dự báo đã VOID vẫn phải trỏ tới Issue có thật, đúng giờ tạo
        self.assertTrue(ledger_audit.issue_crosscheck_errors(pred, void, {7: issues[7], 9: issues[9]}, "chu-kho"))
        # phía ghi: VOID cũng phải chờ tới resolve_at (vòng 9: VOID trước hạn là đường chọn mẫu) — test_ledger_resolution
        src = (ROOT / "tools" / "resolution_intake.py").read_text(encoding="utf-8")
        self.assertIn('early_ok = outcome_key == "YES" and all(', src)
        self.assertNotIn('outcome_key == "VOID" or', src)

    def test_audit_rereads_attestations_while_another_robot_is_between_push_and_comment(self):
        """Vòng 8 điểm 4: robot nhận đẩy commit TRƯỚC rồi mới đăng bình luận ✅. Kiểm toán chạy sau khi robot A xong nhưng đọc
        cả main, nên thấy dòng của robot B vừa đẩy mà chưa có dấu nhận → báo đỏ giả. Nay: đọc lại bình luận trong khoảng chờ
        hữu hạn; hết lượt vẫn thiếu thì vẫn là lỗi (không phải khoảng miễn kiểm)."""
        f = ledger_audit.attestation_errors_with_retry
        h1, h2 = "a" * 64, "b" * 64
        pred = [{"id": "F-7", "issue_number": 7, "issue_created_at": "2026-11-17T02:00:00Z", "hash": h1, "resolve_at": "2026-12-10"},
                {"id": "F-8", "issue_number": 8, "issue_created_at": "2026-11-17T02:00:20Z", "hash": h2, "resolve_at": "2026-12-10"}]
        issues = {7: {"created_at": "2026-11-17T02:00:00Z", "user": "chu-kho", "is_pr": False},
                  8: {"created_at": "2026-11-17T02:00:20Z", "user": "chu-kho", "is_pr": False}}
        bot = lambda at, body: {"user": "github-actions[bot]", "created_at": at, "updated_at": at, "body": body}
        c7 = bot("2026-11-17T02:01:10Z", f"✅ Đã ghi dự báo #7\n\n`ledger-attest: predictions F-7 {h1}`")
        c8 = bot("2026-11-17T02:01:40Z", f"✅ Đã ghi dự báo #8\n\n`ledger-attest: predictions F-8 {h2}`")
        now = datetime(2026, 11, 17, 2, 1, 30, tzinfo=timezone.utc)
        seq, calls, slept = [{7: [c7]}, {7: [c7], 8: [c8]}], [], []
        def fetch():
            calls.append(1); return seq[min(len(calls), len(seq)) - 1]
        run = lambda **kw: f(pred, [], issues, fetch, **{"tries": 6, "wait": 30, "sleep": slept.append, "now": now, **kw})
        # robot A (#7) đã xong; robot B (#8) đã đẩy commit, chưa đăng bình luận: lượt đọc 1 thiếu, lượt 2 đã có → không báo đỏ
        self.assertEqual(run(), [])
        self.assertEqual((len(calls), slept), (2, [30]))
        self.assertEqual(len(ledger_audit.attestation_errors(pred, [], issues, seq[0])), 1)        # một lượt đọc: lỗi
        # dấu nhận không bao giờ tới: chờ có giới hạn, hết lượt vẫn là LỖI
        calls.clear(); slept.clear(); seq[:] = [{7: [c7]}]
        errs = run()
        self.assertEqual(len(errs), 1); self.assertIn("Issue #8", errs[0])
        self.assertEqual((len(calls), slept), (6, [30] * 5))
        # Issue đã quá hạn 6 giờ: dấu nhận có tới cũng không hợp lệ → không chờ, báo lỗi ngay
        calls.clear(); slept.clear()
        self.assertEqual(len(run(now=datetime(2026, 11, 17, 9, 0, 0, tzinfo=timezone.utc))), 1)
        self.assertEqual((len(calls), slept), (1, []))
        # tries=1 là một lượt đọc; sổ đủ dấu nhận cũng chỉ đọc một lượt
        calls.clear(); self.assertEqual(len(run(tries=1)), 1); self.assertEqual((len(calls), slept), (1, []))
        calls.clear(); seq[:] = [{7: [c7], 8: [c8]}]
        self.assertEqual(run(), []); self.assertEqual((len(calls), slept), (1, []))
        # lỗi không do chờ (robot đăng hash khác cho cùng mã) vẫn là lỗi sau khi đọc lại đủ lượt
        calls.clear(); seq[:] = [{7: [c7], 8: [c8, bot("2026-11-17T02:01:50Z", f"✅\n`ledger-attest: predictions F-8 {h1}`")]}]
        self.assertIn("hash khác cho cùng mã", run()[0]); self.assertEqual(len(calls), 6)
        # vòng 9 điểm 4: dấu nhận của dòng PHÂN ĐỊNH không có hạn 6 giờ, nên kiểm toán phải đọc lại cho nó dù Issue mở từ hôm
        # trước (job phân định vừa được chạy lại: commit đã đẩy, bình luận chưa đăng). Dự báo thì giữ hạn 6 giờ và trước resolve_at.
        hr = "c" * 64
        res = [{"prediction_id": "F-7", "resolution_issue": 9, "resolution_issue_created_at": "2026-12-10T03:00:00Z", "hash": hr, "outcome": 0}]
        old_issues = {**issues, 9: {"created_at": "2026-12-10T03:00:00Z", "user": "chu-kho", "is_pr": False}}
        c9 = bot("2026-12-11T05:00:40Z", f"✅ Đã phân định\n`ledger-attest: resolutions F-7 {hr}`")
        next_day = datetime(2026, 12, 11, 5, 0, 30, tzinfo=timezone.utc)         # 26 giờ sau khi Issue phân định mở
        calls.clear(); slept.clear(); seq[:] = [{7: [c7], 8: [c8]}, {7: [c7], 8: [c8], 9: [c9]}]
        self.assertEqual(f(pred, res, old_issues, fetch, tries=6, wait=30, sleep=slept.append, now=next_day), [])
        self.assertEqual((len(calls), slept), (2, [30]))                         # lượt 1 thiếu, lượt 2 có → không đỏ giả
        calls.clear(); slept.clear(); seq[:] = [{7: [c7], 8: [c8]}]
        errs = f(pred, res, old_issues, fetch, tries=6, wait=30, sleep=slept.append, now=next_day)
        self.assertEqual(len(errs), 1); self.assertIn("phân định F-7", errs[0])  # không bao giờ tới → vẫn là lỗi, sau đúng 6 lượt
        self.assertEqual((len(calls), slept), (6, [30] * 5))
        # dự báo: Issue còn trong 6 giờ nhưng đã sang ngày resolve_at → dấu nhận không thể hợp lệ nữa → không chờ
        eve = [{"id": "F-7", "issue_number": 7, "issue_created_at": "2026-12-09T16:00:00Z", "hash": h1, "resolve_at": "2026-12-10"}]
        eve_issues = {7: {"created_at": "2026-12-09T16:00:00Z", "user": "chu-kho", "is_pr": False}}
        calls.clear(); slept.clear(); seq[:] = [{}]
        self.assertEqual(len(f(eve, [], eve_issues, fetch, tries=6, wait=30, sleep=slept.append, now=datetime(2026, 12, 9, 17, 30, tzinfo=timezone.utc))), 1)
        self.assertEqual((len(calls), slept), (1, []))
        calls.clear(); slept.clear()
        self.assertEqual(len(f(eve, [], eve_issues, fetch, tries=3, wait=30, sleep=slept.append, now=datetime(2026, 12, 9, 16, 30, tzinfo=timezone.utc))), 1)
        self.assertEqual((len(calls), slept), (3, [30, 30]))                     # 23:30 ngày 9/12: còn kịp → có chờ
        # main() dùng bản có đọc lại; tổng thời gian chờ mặc định hữu hạn và ngắn hơn hạn chạy của job kiểm toán
        src = (ROOT / "tools" / "ledger_audit.py").read_text(encoding="utf-8")
        self.assertIn("errs += attestation_errors_with_retry(pred, res, issues, lambda: fetch_comments(repo, token)", src.split("def main")[1])
        # vòng 10: khoảng chờ của kiểm toán phải PHỦ HẾT chuỗi thử lại của bước đăng dấu nhận. Hai workflow nhận thử 5 lần, chờ
        # 20, 40, 60, 80 giây (200 giây); bản trước kiểm toán chỉ đọc lại trong 150 giây → dấu nhận hợp lệ tới ở lần thử thứ năm
        # của robot bị báo đỏ giả. Hai bộ số phải đi cùng nhau: đổi một bên mà quên bên kia thì test này đỏ.
        la = ledger_audit
        for wf in ("ledger_intake.yml", "resolution_intake.yml"):
            text = (WF / wf).read_text(encoding="utf-8")
            self.assertIn(f"if (i >= {la.POST_TRIES}) throw e;", text, wf)
            self.assertIn(f"setTimeout(done, {la.POST_BACKOFF * 1000} * i)", text, wf)
        self.assertEqual(la.POST_SPAN, 200)
        wait = (la.ATTEST_TRIES - 1) * la.ATTEST_WAIT
        self.assertGreaterEqual(wait, la.POST_SPAN + 120)                         # dư ít nhất 2 phút cho các lần gọi API hỏng
        # mô phỏng: bình luận của robot B chỉ xuất hiện 230 giây sau lượt đọc đầu (lần thử thứ năm, sau 200 giây chờ)
        clock = [0.0]
        late8 = bot("2026-11-17T02:05:20Z", f"✅ Đã ghi dự báo #8\n\n`ledger-attest: predictions F-8 {h2}`")
        late9 = bot("2026-12-11T05:04:20Z", f"✅ Đã phân định\n`ledger-attest: resolutions F-7 {hr}`")
        tick = lambda sec: clock.__setitem__(0, clock[0] + sec)
        def slow_fetch(extra, base=None):
            return lambda: {**(base or {7: [c7]}), **(extra if clock[0] >= 230 else {})}
        clock[0] = 0.0
        self.assertEqual(f(pred, [], issues, slow_fetch({8: [late8]}), sleep=tick, now=now), [])               # dự báo mới: không đỏ giả
        self.assertGreaterEqual(clock[0], 230); self.assertLessEqual(clock[0], wait)
        clock[0] = 0.0
        self.assertEqual(len(f(pred, [], issues, slow_fetch({8: [late8]}), tries=6, wait=30, sleep=tick, now=now)), 1)   # cửa chờ cũ (150 giây): đỏ giả
        clock[0] = 0.0
        self.assertEqual(f(pred, res, old_issues, slow_fetch({9: [late9]}, {7: [c7], 8: [c8]}), sleep=tick, now=next_day), [])   # phân định Issue cũ: cũng vậy
        self.assertGreaterEqual(clock[0], 230)
        clock[0] = 0.0
        errs = f(pred, [], issues, slow_fetch({}), sleep=tick, now=now)           # không bao giờ tới: vẫn là LỖI, sau khoảng chờ hữu hạn
        self.assertEqual(len(errs), 1); self.assertEqual(clock[0], wait)
        self.assertGreaterEqual(la.ATTEST_TRIES, 2)
        for wf, job in (("ledger_audit.yml", "audit"), ("tests.yml", "gate")):
            self.assertLess(wait, yaml.safe_load((WF / wf).read_text(encoding="utf-8"))["jobs"][job]["timeout-minutes"] * 60 / 2, wf)
        self.assertFalse(hasattr(ledger_audit, "ATTEST_GRACE"))

    def test_audit_runs_after_every_bot_write(self):
        """Vòng 7 điểm 4: commit do GITHUB_TOKEN đẩy không kích hoạt 'push', nên phải có workflow riêng chạy kiểm toán sau khi
        robot ghi sổ và sau vòng học."""
        text = (WF / "ledger_audit.yml").read_text(encoding="utf-8")
        d = yaml.safe_load(text)
        on = d.get("on") or d.get(True)
        names = {yaml.safe_load((WF / n).read_text(encoding="utf-8"))["name"] for n in ("ledger_intake.yml", "resolution_intake.yml", "daily_cycle.yml")}
        self.assertEqual(set(on["workflow_run"]["workflows"]), names)            # đúng tên ba workflow ghi sổ
        self.assertEqual(on["workflow_run"]["types"], ["completed"])
        self.assertIn("schedule", on)
        steps = d["jobs"]["audit"]["steps"]
        self.assertEqual(steps[0]["with"]["fetch-depth"], 0)
        self.assertEqual(steps[0]["with"]["ref"], "main")
        runs = [s_.get("run", "") for s_ in steps]
        self.assertTrue(any("tools/validate.py" in r for r in runs))
        audit = next(s_ for s_ in steps if "ledger_audit.py" in s_.get("run", ""))
        self.assertIn('--base "$BASE_SHA" --github', audit["run"])
        self.assertEqual(audit["env"]["BASE_SHA"], "${{ github.event.workflow_run.head_sha }}")   # commit trước khi robot ghi
        self.assertIn("--before='26 hours ago'", audit["run"])                  # chạy theo lịch: so với main của hôm trước
        self.assertEqual(d["permissions"], {"contents": "read", "issues": "read"})
        gate = yaml.safe_load((WF / "tests.yml").read_text(encoding="utf-8"))["jobs"]["gate"]["steps"]
        self.assertTrue(any("ledger_audit.py" in s_.get("run", "") for s_ in gate))

    def test_workflow_comment_carries_the_attestation(self):
        for name in ("ledger_intake.yml", "resolution_intake.yml"):
            text = (WF / name).read_text(encoding="utf-8")
            self.assertIn('"ledger-attest: " + a', text, name)
            self.assertIn("retries: 3", text, name)
            self.assertIn("for (let i = 1; ; i++)", text, name)                  # vòng 8: dòng đã lên main thì dấu nhận phải được đăng —
            self.assertIn("if (i >= 5) throw e;", text, name)                    # thử lại có giới hạn, vẫn hỏng thì job đỏ
            push, comment = text.index("git push -q origin HEAD:main"), text.index("issues.createComment")
            self.assertLess(push, comment, name)                                 # ghi trước, dấu nhận sau (hash phủ cả chuỗi đã ghi)
            self.assertIn('process.env.CODE === "3"', text, name)                # chạy lại job vẫn bổ sung được dấu nhận
            self.assertIn('.replace(/ledger-attest/gi, "ledger_attest")', text, name)   # thông báo không mang được dấu nhận giả
            self.assertIn("r.ok && Array.isArray(r.attest)", text, name)         # bình luận ❌ không bao giờ có dấu nhận


class LedgerReplayTests(unittest.TestCase):
    """CI chạy lại luật nhận trên mọi dòng Issue đã có trong sổ (laws_checks.check_ledger_rows)."""
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        (self.tmp / "contracts").mkdir(); (self.tmp / "governance").mkdir(); (self.tmp / "ledger").mkdir()
        for c in ("forecast_issue.schema.json", "resolution.schema.json"):
            shutil.copy(ROOT / "contracts" / c, self.tmp / "contracts")
        for g in ("CONTROL_B_PROMPT.md", "control_b_prompts.jsonl"):
            shutil.copy(ROOT / "governance" / g, self.tmp / "governance")
        shutil.copytree(ROOT / "tools", self.tmp / "tools", ignore=shutil.ignore_patterns("__pycache__"))
        self.led = self.tmp / "ledger" / "predictions.jsonl"
        for n, seat in ((1, "A"), (2, "B")):
            e = {**os.environ, "ISSUE_NUMBER": str(n), "ISSUE_CREATED_AT": "2026-11-17T02:00:00Z", "ISSUE_BODY": _forecast(seat),
                 "TTC_INTAKE_NOW": _just_after("2026-11-17T02:00:00Z")}
            r = subprocess.run([sys.executable, str(self.tmp / "tools" / "ledger_intake.py")], env=e, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout)
        self.good = self.led.read_text(encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _append(self, **kw):
        """Ghi thêm một dòng tự tạo với hash chuỗi HỢP LỆ (như một commit ghi vòng qua intake)."""
        rows = [json.loads(l) for l in self.good.splitlines()]
        row = {k: v for k, v in rows[0].items() if k not in ("hash", "prev_hash")}
        row.update({"question": "Câu hỏi tự chèn có ngưỡng 4,60%?", "id": "F-50", "issue_number": 50, **kw})
        row = {k: v for k, v in row.items() if v is not None}
        row["prev_hash"] = rows[-1]["hash"]; row["hash"] = laws_checks.line_hash(row)
        self.led.write_text(self.good + json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        self.assertEqual(laws_checks.check_ledger_chain(self.tmp), [])           # hash chuỗi không bắt được gì
        return laws_checks.check_ledger_rows(self.tmp)

    def test_rows_written_around_intake_are_rechecked(self):
        self.assertEqual(laws_checks.check_ledger_rows(self.tmp), [])            # sổ ghi qua intake: đạt
        self.assertEqual(self._append(), [])                                     # dòng tự chèn nhưng đúng mọi luật nhận → kiểm lại
        # không bắt được; việc nó có đúng LÚC không là phần của dấu nhận (LedgerAuditTests)
        for kw, why in (({"resolve_at": "2026-11-17"}, "resolve_at phải sau"), ({"model_cutoff": "2027-01"}, "tương lai"),
                        ({"p": 0.99}, "schema"), ({"p": "0.5"}, "schema"), ({"author_seat": "ai đó"}, "author_seat"),
                        ({"seat": "B"}, "prompt_hash"), ({"prompt_hash": B_HASH}, "seat A"), ({"truong_la": "x"}, "schema"),
                        ({"resolution_source": "một nguồn nào đó"}, "tên miền"), ({"id": "F-51"}, "không khớp issue_number"),
                        ({"issue_number": 1, "id": "F-1"}, "hai dòng"), ({"issue_created_at": "hôm qua"}, "không đọc được"),
                        ({"question": "CPI tháng 11/2026 so với cùng kỳ từ 5,00% trở lên?"}, "mỗi ghế một dự báo"),
                        ({"question": "CPI tháng 11/2026 so với cùng kỳ từ 5,00% trở lên?", "resolve_at": "2026-12-20"}, "cùng resolve_at"),
                        ({"question": "VCB: nên mua trước khi công bố báo cáo?"}, "L-02"), ({"issue_number": "50"}, "số Issue")):
            errs = self._append(**kw)
            self.assertTrue(errs and any(why in e for e in errs), f"{kw}: {errs}")

    def test_validate_runs_the_replay(self):
        self.assertIn("check_ledger_rows(root)", (ROOT / "tools" / "laws_checks.py").read_text(encoding="utf-8").split("def run_all")[1])
        self.assertTrue(self._append(resolve_at="2026-11-17"))
        self.assertTrue(any("không qua luật nhận" in e for e in laws_checks.run_all(self.tmp)))


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
        for name, (_, d) in self.wf.items():
            for job in d["jobs"].values():
                for step in job["steps"]:
                    # không biểu thức ${{ }} nào nằm trong lệnh shell hay trong mã github-script: mọi giá trị đi qua env
                    self.assertNotIn("${{", step.get("run", ""), f"{name}: bước '{step.get('name')}' chèn giá trị vào lệnh")
                    self.assertNotIn("${{", (step.get("with") or {}).get("script", ""), f"{name}: bước '{step.get('name')}'")

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
        engine = d["jobs"]["cycle"]["steps"][i_engine]
        self.assertEqual(engine["env"].get("TTC_REGISTRY_PUSH"), "1")        # L-06: đăng ký lên main trước khi chạy backtest
        self.assertIn('--trials "$TRIALS"', engine["run"])
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
