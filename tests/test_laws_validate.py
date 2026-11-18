"""Test cho tools/laws_checks.py và tools/ledger_intake.py (L-02, L-05, L-07, hash chuỗi)."""
import json, os, pathlib, shutil, subprocess, sys, tempfile, unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import laws_checks  # noqa: E402


def _tmp_repo():
    tmp = pathlib.Path(tempfile.mkdtemp())
    (tmp / "architecture").mkdir(); (tmp / "reports").mkdir(); (tmp / "ledger").mkdir(); (tmp / "contracts").mkdir(); (tmp / "tools").mkdir()
    for c in ("forecast_issue.schema.json", "resolution.schema.json"):
        shutil.copy(ROOT / "contracts" / c, tmp / "contracts")
    for t in ("laws_checks.py", "ledger_intake.py", "resolution_intake.py"):   # robot nhận tự chạy lại luật của CẢ hai sổ trước khi ghi
        shutil.copy(ROOT / "tools" / t, tmp / "tools")
    (tmp / "tools" / "__init__.py").write_text("", encoding="utf-8")
    return tmp


class ReviewGateTests(unittest.TestCase):
    def test_l09_pr_review_fields(self):
        f = laws_checks.check_pr_review
        self.assertTrue(f("Mô tả không có trường"))
        self.assertTrue(f("authored_by: Claude (Anthropic)\nreviewed_by:"))
        self.assertTrue(f("authored_by: Claude Opus\nreviewed_by: Claude Sonnet"))      # cùng nhà
        self.assertTrue(f("authored_by: ChatGPT\nreviewed_by: GPT-5 Codex"))            # cùng nhà
        self.assertTrue(f("authored_by: Claude\nreviewed_by: Opus"))                 # cùng nhà, tên khác
        self.assertTrue(f("authored_by: Claude\nreviewed_by: Haiku 5.5"))
        self.assertTrue(f("authored_by: Claude\nreviewed_by: ai đó"))                 # không nhận ra nhà cung cấp
        self.assertEqual(f("authored_by: Claude (Anthropic)\nreviewed_by: Grok (xAI)"), [])
        self.assertEqual(f("authored_by: Claude (Anthropic)\nreviewed_by: Owner"), [])
        self.assertEqual(f("authored_by: Claude (Anthropic)\nreviewed_by: Owner (Trần Ngọc Thắng)"), [])
        for bad in ("not-an-owner", "downer", "not_an_owner", "éowner", "an owner", "Trần Ngọc Thắng (Owner)",
                    "owner_bot", "owner-bot", "ownerx", "not_a_grok", "xgrok", "ai đó"):
            self.assertTrue(f(f"authored_by: Claude\nreviewed_by: {bad}"), bad)      # phải BẮT ĐẦU bằng tên ghế
        for good in ("Owner", "owner", "Owner (Trần Ngọc Thắng)", "Owner — vòng 3", "ChatGPT (OpenAI)", "Grok (xAI)",
                     "GPT-5.5 Thinking", "Gemini 3 Pro", "grok"):
            self.assertEqual(f(f"authored_by: Claude (Anthropic)\nreviewed_by: {good}"), [], good)
        self.assertEqual(f("authored_by: ChatGPT\nreviewed_by: claude-opus-5-5"), [])
        # Owner là MỘT ghế: Owner viết thì Owner không tự chấm, dù ghi thêm tên hay ghi chú
        for rb in ("Owner", "Owner (Trần Ngọc Thắng)", "Owner — vòng 3", "owner"):
            self.assertTrue(f(f"authored_by: Owner\nreviewed_by: {rb}"), rb)
            self.assertTrue(f(f"authored_by: Owner (Trần Ngọc Thắng) và Claude\nreviewed_by: {rb}"), rb)
        self.assertTrue(f("authored_by: Claude và Owner\nreviewed_by: ChatGPT + Claude"))   # người chấm có chung một ghế với người viết
        self.assertEqual(f("authored_by: Owner\nreviewed_by: ChatGPT (OpenAI)"), [])
        self.assertEqual(f("authored_by: ChatGPT (OpenAI)\nreviewed_by: Owner (Trần Ngọc Thắng)"), [])
        # ghế viết không nhận ra được thì không so được với ghế chấm
        for ab in ("kiến trúc sư trưởng", "ai đó", "not_a_claude", "ghe-thi-cong"):
            self.assertTrue(f(f"authored_by: {ab}\nreviewed_by: Claude"), ab)
        self.assertTrue(laws_checks.recognised_seat("Claude (Anthropic) — kiến trúc sư trưởng"))
        self.assertFalse(laws_checks.recognised_seat("kiến trúc sư trưởng Claude"))
        # chú thích HTML của mẫu PR (có chữ "authored_by: …") không phải nội dung: mẫu thật + hai dòng điền → đạt
        tpl = (ROOT / ".github" / "pull_request_template.md").read_text(encoding="utf-8")
        self.assertIn("thiếu dòng", f(tpl)[0])                                  # mẫu chưa điền: thiếu authored_by, KHÔNG phải "trùng dòng"
        filled = tpl.replace("authored_by: \n", "authored_by: Claude (Anthropic)\n", 1).replace("reviewed_by: \n", "reviewed_by: Grok (xAI)\n", 1)
        self.assertEqual(f(filled), [], f(filled))
        self.assertTrue(f("<!-- authored_by: Claude\nreviewed_by: Grok -->\nKhông có trường thật"))
        # mỗi trường một dòng: không chèn dòng thứ hai để đè
        self.assertTrue(f("authored_by: Claude\nauthored_by: ChatGPT\nreviewed_by: Claude"))
        self.assertTrue(f("authored_by: Claude\nreviewed_by: Claude\nreviewed_by: Grok"))
        self.assertTrue(laws_checks.same_provider("Owner", "Owner (kiểm lại)"))
        self.assertFalse(laws_checks.same_provider("Owner", "Grok (xAI)"))
        self.assertEqual(f("- authored_by: `ChatGPT`\n- reviewed_by: `Claude`"), [])


class LawsChecksTests(unittest.TestCase):
    def setUp(self):
        self.tmp = _tmp_repo()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_l07_requires_archive_listing(self):
        a = self.tmp / "architecture"
        (a / "ARCHITECTURE.md").write_text("# v3", encoding="utf-8")
        (a / "ARCHITECTURE_v2.0.md").write_text("old", encoding="utf-8")
        self.assertTrue(laws_checks.check_one_architecture(self.tmp))          # chưa có ARCHIVE.md → lỗi
        (a / "ARCHIVE.md").write_text("| ARCHITECTURE_v2.0.md | SUPERSEDED |", encoding="utf-8")
        self.assertEqual(laws_checks.check_one_architecture(self.tmp), [])
        (a / "ARCHITECTURE_v9.9.md").write_text("new", encoding="utf-8")     # bản mới không được liệt kê → lỗi
        self.assertTrue(laws_checks.check_one_architecture(self.tmp))
        # tên tệp nhắc ở một dòng, chữ SUPERSEDED ở dòng khác → vẫn lỗi (phải cùng một dòng)
        (a / "ARCHIVE.md").write_text("| ARCHITECTURE_v2.0.md | SUPERSEDED |\nXem thêm ARCHITECTURE_v9.9.md (đang soạn)", encoding="utf-8")
        errs = laws_checks.check_one_architecture(self.tmp)
        self.assertEqual(len(errs), 1); self.assertIn("v9.9", errs[0])

    def test_l02_flags_recommendation_keywords(self):
        (self.tmp / "reports" / "x.md").write_text("Phân tích biên lợi nhuận.", encoding="utf-8")
        self.assertEqual(laws_checks.check_no_recommendation(self.tmp), [])
        (self.tmp / "reports" / "y.md").write_text("Khuyến nghị MUA với giá mục tiêu 50.000", encoding="utf-8")
        errs = laws_checks.check_no_recommendation(self.tmp)
        self.assertEqual(len(errs), 1); self.assertIn("y.md", errs[0])

    def _row(self, prev, **kw):
        row = {"issue_number": 1, "seat": "A", "p": 0.6, "prev_hash": prev, **kw}
        row["hash"] = laws_checks.line_hash(row)
        return row

    def test_ledger_chain_detects_tampering(self):
        led = self.tmp / "ledger" / "predictions.jsonl"
        r1 = self._row("GENESIS"); r2 = self._row(r1["hash"], issue_number=2)
        led.write_text("\n".join(json.dumps(r) for r in (r1, r2)) + "\n", encoding="utf-8")
        self.assertEqual(laws_checks.check_ledger_chain(self.tmp), [])
        r1["p"] = 0.9                                                           # sửa dòng cũ, giữ hash cũ
        led.write_text("\n".join(json.dumps(r) for r in (r1, r2)) + "\n", encoding="utf-8")
        self.assertTrue(laws_checks.check_ledger_chain(self.tmp))

    def _run_intake(self, body, created="2026-10-22T10:00:00Z", number=7):
        env = {**os.environ, "ISSUE_NUMBER": str(number), "ISSUE_CREATED_AT": created, "ISSUE_BODY": body,
               "TTC_INTAKE_NOW": created.replace(":00:00Z", ":01:00Z")}        # robot chạy một phút sau khi Issue mở
        p = subprocess.run([sys.executable, str(self.tmp / "tools" / "ledger_intake.py")], env=env, cwd=self.tmp,
                           capture_output=True, text=True)
        return p.returncode, (json.loads(p.stdout.strip().splitlines()[-1]) if p.stdout.strip() else {})

    BODY = ("### seat\n\nA\n\n### question\n\nNợ nhóm 3–5 của ngân hàng X tại 31/12/2026 cao hơn 30/9/2026?\n\n"
            "### resolution_source\n\nhttps://example.vn/bctc\n\n### resolution_rule\n\ncomparison\n\n### resolve_at\n\n{resolve}\n\n"
            "### info_lock_at\n\n{resolve}\n\n"
            "### p\n\n0.6\n\n### base_rate\n\n0.5\n\n### invalidation_conditions\n\nBCTC bị điều chỉnh hồi tố\n\n"
            "### author_seat\n\nClaude Project TTC\n\n### model_cutoff\n\n2026-06\n\n### library_refs\n\n_No response_\n\n### prompt_hash\n\n_No response_\n")

    def test_intake_writes_chain_and_rejects_past_date(self):
        code, out = self._run_intake(self.BODY.format(resolve="2027-02-15"))
        self.assertEqual(code, 0, out); self.assertTrue(out["ok"])
        body8 = self.BODY.format(resolve="2027-03-01").replace("ngân hàng X", "ngân hàng Y")
        code, out = self._run_intake(body8, number=8)
        self.assertEqual(code, 0, out)
        self.assertEqual(laws_checks.check_ledger_chain(self.tmp), [])
        lines = (self.tmp / "ledger" / "predictions.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(json.loads(lines[1])["prev_hash"], json.loads(lines[0])["hash"])
        code, out = self._run_intake(body8, number=8)                                       # cùng Issue ghi lần hai → bỏ qua
        self.assertEqual(code, 3); self.assertTrue(out.get("duplicate"))
        self.assertEqual(len((self.tmp / "ledger" / "predictions.jsonl").read_text(encoding="utf-8").splitlines()), 2)
        body9 = self.BODY.replace("ngân hàng X", "ngân hàng Z")
        code, out = self._run_intake(body9.format(resolve="2026-10-01"), number=9)         # ngày đã qua → L-05
        self.assertEqual(code, 2); self.assertFalse(out["ok"])
        code, out = self._run_intake(body9.format(resolve="2027-01-01").replace("0.6", "0.99"), number=10)  # p ngoài khoảng
        self.assertEqual(code, 2)
        self.assertEqual(len((self.tmp / "ledger" / "predictions.jsonl").read_text(encoding="utf-8").splitlines()), 2)


if __name__ == "__main__":
    unittest.main()
