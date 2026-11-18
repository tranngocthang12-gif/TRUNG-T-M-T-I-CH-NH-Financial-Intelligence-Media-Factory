"""L-05 hạn khóa công bố (ADR-0011 + lệnh sửa PR #45). Đối kháng: thiếu/sai lịch, lịch ghi lùi thời gian, sửa lịch đã ghim,
nộp sau công bố, bằng chứng công bố ghi muộn, điểm năng lực bị làm đẹp bằng dự báo không hợp lệ, mẫu 194 bị thay,
F-37–F-42 bị sửa, và luồng robot hợp lệ vẫn chạy.
Mọi thứ chạy trong thư mục tạm và tiến trình con: không chạm tệp nào của kho.
"""
import json, os, pathlib, shutil, subprocess, sys, tempfile, unittest
from datetime import datetime, timedelta

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from engine import ledger as engine_ledger  # noqa: E402
from tools import laws_checks, ledger_audit, ledger_intake  # noqa: E402
from tests._calendar_fixture import calendar_body, run_calendar, with_calendar  # noqa: E402

Q = "CPI tháng 12/2026 có tăng từ 3,00% trở lên so với cùng kỳ theo nso.gov.vn không?"
OWNER = "chu-kho"
BOT = "github-actions[bot]"


def _just_after(created, seconds=60):
    return (datetime.fromisoformat(created.replace("Z", "+00:00")) + timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")


def _forecast(seat, question=Q, resolve_at="2026-12-31", lock="2026-12-20", p="0.4", calendar_id=None, source=None):
    author = "Claude Project TTC" if seat == "A" else "Claude trần"
    f = {"seat": seat, "question": question, "resolution_source": source or "https://www.nso.gov.vn — thông cáo",
         "resolution_rule": "numeric_range", "resolve_at": resolve_at, "info_lock_at": lock, "p": p, "base_rate": "0.5",
         "invalidation_conditions": "Cơ quan thống kê đổi rổ hoặc năm gốc", "author_seat": author, "model_cutoff": "2026-06",
         "calendar_id": calendar_id}
    if seat == "B":
        f["prompt_hash"] = ledger_intake.control_b_hash(ROOT / "governance" / "CONTROL_B_PROMPT.md")
    return "\n\n".join(f"### {k}\n\n{v}" for k, v in f.items() if v is not None)


def _pub(ids, published_at, recorder="Owner"):
    f = {"notice": "PUBLICATION", "forecast_ids": ids, "published_at": published_at,
         "evidence_url": "https://www.nso.gov.vn/thong-cao", "quote": "Chỉ số giá tiêu dùng tháng đã được công bố.",
         "recorder": recorder}
    return "\n\n".join(f"### {k}\n\n{v}" for k, v in f.items())


def _resolution(ids, outcome, quote="CPI tháng 12/2026 tăng 3,20% so với cùng kỳ"):
    f = {"forecast_ids": ids, "outcome": outcome, "observed_value": "_No response_",
         "resolution_source": "https://www.nso.gov.vn/thong-cao.pdf", "quote": quote, "resolver": "Owner", "void_reason": "_No response_"}
    return "\n\n".join(f"### {k}\n\n{v}" for k, v in f.items())


class _Repo(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        (self.tmp / "contracts").mkdir(); (self.tmp / "governance").mkdir(); (self.tmp / "ledger").mkdir()
        for c in ("forecast_issue.schema.json", "resolution.schema.json"):
            shutil.copy(ROOT / "contracts" / c, self.tmp / "contracts")
        for g in ("CONTROL_B_PROMPT.md", "control_b_prompts.jsonl"):
            shutil.copy(ROOT / "governance" / g, self.tmp / "governance")
        shutil.copytree(ROOT / "tools", self.tmp / "tools", ignore=shutil.ignore_patterns("__pycache__"))
        self.gh_issues, self.gh_comments = {}, {}          # bản sao "GitHub" của test: số Issue, giờ mở, người mở, bình luận bot

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run(self, script, number, body, created, **env):
        """Một lần chạy robot. Như workflow thật: Issue có trên GitHub (giờ mở do máy chủ cấp), robot đăng ✅ kèm dấu nhận."""
        now = env.pop("TTC_INTAKE_NOW", _just_after(created))
        e = {**os.environ, "ISSUE_NUMBER": str(number), "ISSUE_CREATED_AT": created, "ISSUE_BODY": body, "TTC_INTAKE_NOW": now, **env}
        r = subprocess.run([sys.executable, str(self.tmp / "tools" / script)], env=e, capture_output=True, text=True)
        out = r.stdout + r.stderr
        self.gh_issues[number] = {"created_at": created, "user": OWNER, "is_pr": False}
        try:
            res = json.loads(r.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            res = {}
        if res.get("ok") and res.get("attest"):
            body = "✅ " + str(res.get("message")) + "\n\n" + "\n".join("`ledger-attest: " + a + "`" for a in res["attest"])
            self.gh_comments.setdefault(number, []).append({"user": BOT, "created_at": now.replace("+00:00", "Z"),
                                                            "updated_at": now.replace("+00:00", "Z"), "body": body})
        return r.returncode, out

    def _pin(self, number, cid, lock="2026-12-20", created="2026-11-01T02:00:00Z", domains=("nso.gov.vn",), **kw):
        env = {k: kw.pop(k) for k in list(kw) if k.isupper()}
        return self._run("resolution_intake.py", number, calendar_body(cid, list(domains), lock, **kw), created, **env)

    def _rows(self, rel):
        p = self.tmp / rel
        return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.is_file() else []

    def _verified(self):
        return ledger_audit.provenance_verified_ids(self._rows("ledger/predictions.jsonl"), self._rows("governance/release_calendar.jsonl"),
                                                    self._rows("ledger/publication_evidence.jsonl"), self.gh_issues, self.gh_comments, OWNER)


class CalendarRequiredTests(_Repo):
    def test_forecast_without_calendar_id_is_rejected(self):
        c, o = self._run("ledger_intake.py", 501, _forecast("A"), "2026-11-18T02:00:00Z")
        self.assertEqual(c, 2, o); self.assertIn("thiếu calendar_id", o)
        self.assertEqual(self._rows("ledger/predictions.jsonl"), [])

    def test_unknown_or_mismatched_calendar_is_rejected(self):
        self.assertEqual(self._pin(401, "CAL-NSO-2026-12")[0], 0)
        self.assertEqual(self._pin(402, "CAL-SBV-2026-12", domains=("sbv.gov.vn",))[0], 0)
        c, o = self._run("ledger_intake.py", 501, _forecast("A", calendar_id="CAL-KHONG-CO"), "2026-11-18T02:00:00Z")
        self.assertEqual(c, 2, o); self.assertIn("không trỏ tới đúng một dòng lịch", o)
        c, o = self._run("ledger_intake.py", 502, _forecast("A", calendar_id="CAL-SBV-2026-12"), "2026-11-18T02:00:00Z")
        self.assertEqual(c, 2, o); self.assertIn("không cùng tên miền", o)            # lịch của nguồn khác nguồn phân định
        c, o = self._run("ledger_intake.py", 503, _forecast("A", lock="2026-12-28", calendar_id="CAL-NSO-2026-12"), "2026-11-18T02:00:00Z")
        self.assertEqual(c, 2, o); self.assertIn("không khớp lịch", o)                # ngày tự khai khác lịch
        c, o = self._run("ledger_intake.py", 504, _forecast("A", calendar_id="CAL-NSO-2026-12"), "2026-11-18T02:00:00Z")
        self.assertEqual(c, 0, o)
        self.assertEqual(laws_checks.check_ledger_rows(self.tmp), [])

    def test_calendar_issue_rules(self):
        c, o = self._run("resolution_intake.py", 401, calendar_body("CAL-X", ["nso.gov.vn"], "2026-12-20"), "2026-11-01T02:00:00Z")
        self.assertEqual(c, 2, o); self.assertIn("calendar_id phải có dạng", o)
        c, o = self._pin(402, "CAL-NSO-QUA-KHU", lock="2026-10-31")
        self.assertEqual(c, 2, o); self.assertIn("đã qua", o)
        c, o = self._pin(403, "CAL-NSO-URL", url="https://nso.gov.vn.evil.com/lich")
        self.assertEqual(c, 2, o); self.assertIn("evidence_url không thuộc", o)
        c, o = self._pin(404, "CAL-NSO-QUOTE", quote="ngắn")
        self.assertEqual(c, 2, o); self.assertIn("quote", o)
        c, o = self._pin(405, "CAL-NSO-AI", recorder="ai đó")
        self.assertEqual(c, 2, o); self.assertIn("recorder", o)
        fake_time = calendar_body("CAL-NSO-GIO", ["nso.gov.vn"], "2026-12-20") + "\n\n### recorded_at\n\n2026-10-01T00:00:00Z"
        c, o = self._run("resolution_intake.py", 406, fake_time, "2026-11-01T02:00:00Z")
        self.assertEqual(c, 2, o); self.assertIn("trường lạ", o)                      # không có trường thời gian tự khai
        c, o = self._pin(407, "CAL-NSO-OK")
        self.assertEqual(c, 0, o)
        c, o = self._pin(407, "CAL-NSO-OK")
        self.assertEqual(c, 3, o)                                                      # chạy lại: không ghi trùng
        c, o = self._pin(408, "CAL-NSO-OK", lock="2026-12-27")
        self.assertEqual(c, 2, o); self.assertIn("không ghi đè", o)                    # đổi ngày của lịch đã ghim
        c, o = self._pin(409, "CAL-NSO-MUON", created="2026-11-01T02:00:00Z", TTC_INTAKE_NOW="2026-11-01T09:00:00Z")
        self.assertEqual(c, 2, o)                                                      # chạy lại job quá 6 giờ: không ghi
        self.assertEqual([r["calendar_id"] for r in self._rows("governance/release_calendar.jsonl")], ["CAL-NSO-OK"])
        self.assertEqual(laws_checks.check_ledger_rows(self.tmp), [])
        self.assertEqual(laws_checks.check_ledger_chain(self.tmp), [])


class BackdatedCalendarTests(_Repo):
    def test_calendar_pinned_after_the_forecast_issue_is_not_accepted(self):
        """Lịch ghim SAU Issue dự báo (robot ghi giờ thật) → robot nhận từ chối; dù dòng lịch có giờ tạo Issue ghi sớm hơn."""
        c, o = self._pin(450, "CAL-NSO-SAU", created="2026-11-18T05:00:00Z")
        self.assertEqual(c, 0, o)
        c, o = self._run("ledger_intake.py", 449, _forecast("A", calendar_id="CAL-NSO-SAU"), "2026-11-18T02:00:00Z")
        self.assertEqual(c, 2, o); self.assertIn("không mở trước Issue dự báo", o)

    def test_backdated_calendar_row_in_a_commit_fails_the_github_audit(self):
        """Ghi tay (commit/PR) một dòng lịch khai giờ tạo Issue sớm hơn: chuỗi hash hợp lệ, luật offline đạt, nhưng kiểm toán
        GitHub thấy Issue thật mở sau, hoặc không có dấu nhận của bot → không xác nhận, CI đỏ, không vào kiểm định."""
        self.assertEqual(self._pin(401, "CAL-NSO-THAT")[0], 0)
        cal = self._rows("governance/release_calendar.jsonl")
        forged = {"calendar_id": "CAL-NSO-GIA", "domains": ["nso.gov.vn"], "info_lock_at": "2026-12-20",
                  "evidence_url": "https://www.nso.gov.vn/lich", "quote": "Số liệu tháng 11 công bố ngày 20/12/2026.",
                  "recorder": "Owner", "issue_number": 402, "issue_created_at": "2026-11-01T03:00:00Z", "prev_hash": cal[-1]["hash"]}
        forged["hash"] = laws_checks.line_hash(forged)
        (self.tmp / "governance" / "release_calendar.jsonl").open("a", encoding="utf-8").write(ledger_intake.dumps(forged) + "\n")
        self.assertEqual(laws_checks.check_ledger_chain(self.tmp), [])
        self.assertEqual(laws_checks.check_ledger_rows(self.tmp), [])           # offline không phân biệt được: phải nhờ GitHub
        c, o = self._run("ledger_intake.py", 520, _forecast("A", calendar_id="CAL-NSO-GIA"), "2026-11-18T02:00:00Z")
        self.assertEqual(c, 0, o)
        # Thực tế trên GitHub: Issue #402 mở 19/11 (sau dự báo) và robot chưa từng ghim nó — không có dấu nhận
        self.gh_issues[402] = {"created_at": "2026-11-19T00:00:00Z", "user": OWNER, "is_pr": False}
        verified, errs = self._verified()
        self.assertNotIn("F-520", verified)
        self.assertTrue(any("CAL-NSO-GIA" in e and "giờ tạo" in e for e in errs), errs)
        self.assertTrue(any("F-520" in e for e in errs), errs)
        st = ledger_intake.timing_verification_status(self._rows("ledger/predictions.jsonl")[-1], [],
                                                      self._rows("governance/release_calendar.jsonl"), verified)
        self.assertEqual(st, "provenance_unverified")

    def test_calendar_issue_older_but_attested_after_the_forecast_is_not_proof(self):
        """Issue lịch mở sớm nhưng robot chỉ ghim (đăng dấu nhận) sau khi Issue dự báo đã mở: không chứng minh lịch có trước."""
        self.assertEqual(self._pin(401, "CAL-NSO-MUON", created="2026-11-18T01:00:00Z",
                                   TTC_INTAKE_NOW="2026-11-18T03:30:00Z")[0], 0)
        c, o = self._run("ledger_intake.py", 520, _forecast("A", calendar_id="CAL-NSO-MUON"), "2026-11-18T02:00:00Z")
        self.assertEqual(c, 0, o)                                                      # offline: giờ mở Issue lịch đứng trước
        verified, errs = self._verified()
        self.assertNotIn("F-520", verified)
        self.assertTrue(any("không có trước Issue dự báo" in e for e in errs), errs)

    def test_edit_delete_or_overwrite_of_a_pinned_calendar_is_caught(self):
        self.assertEqual(self._pin(401, "CAL-NSO-A")[0], 0)
        self.assertEqual(self._pin(402, "CAL-NSO-B", lock="2026-12-27")[0], 0)
        path = self.tmp / "governance" / "release_calendar.jsonl"
        good = path.read_text(encoding="utf-8")
        path.write_text(good.replace('"info_lock_at": "2026-12-20"', '"info_lock_at": "2026-12-29"', 1), encoding="utf-8")
        self.assertTrue(any("Lịch công bố" in e for e in laws_checks.check_ledger_chain(self.tmp)))      # sửa ngày
        lines = good.splitlines(keepends=True)
        path.write_text(lines[1], encoding="utf-8")
        self.assertTrue(any("Lịch công bố" in e for e in laws_checks.check_ledger_chain(self.tmp)))      # xóa dòng đầu
        # sửa rồi tính lại cả chuỗi hash: chuỗi đạt, nhưng chỉ-ghi-thêm so với commit gốc và dấu nhận của bot đều đỏ
        rows = [json.loads(l) for l in lines]
        rows[0]["info_lock_at"] = "2026-12-29"; prev = "GENESIS"
        for r in rows:
            r["prev_hash"] = prev; r["hash"] = laws_checks.line_hash(r); prev = r["hash"]
        rewritten = "".join(ledger_intake.dumps(r) + "\n" for r in rows)
        path.write_text(rewritten, encoding="utf-8")
        self.assertEqual(laws_checks.check_ledger_chain(self.tmp), [])
        self.assertIn("governance/release_calendar.jsonl", ledger_audit.APPEND_ONLY)
        rel = "governance/release_calendar.jsonl"
        self.assertTrue(ledger_audit.append_only_errors({rel: good.encode("utf-8")}, {rel: rewritten.encode("utf-8")}))
        self.assertTrue(ledger_audit.append_only_errors({rel: good.encode("utf-8")}, {rel: None}))      # xóa cả tệp
        _, errs = self._verified()
        self.assertTrue(any("CAL-NSO-A" in e for e in errs), errs)                    # hash mới không có dấu nhận của bot


class PublicationTimingTests(_Repo):
    def setUp(self):
        super().setUp()
        self.assertEqual(self._pin(401, "CAL-NSO-12")[0], 0)

    def test_forecast_after_publication_but_before_the_declared_lock(self):
        """Lịch nói 20/12, kết quả thật công bố 06/12. Dự báo nộp 07/12 (trước hạn khóa của lịch)."""
        q1 = "CPI tháng 11 có tăng từ 3% trở lên so với cùng kỳ không?"
        c, o = self._run("ledger_intake.py", 510, _forecast("A", question=q1, calendar_id="CAL-NSO-12"), "2026-12-01T02:00:00Z")
        self.assertEqual(c, 0, o)
        c, o = self._run("resolution_intake.py", 610, _pub("F-510", "2026-12-06T02:00:00Z"), "2026-12-06T05:00:00Z")
        self.assertEqual(c, 0, o)
        c, o = self._run("ledger_intake.py", 511, _forecast("B", question=q1, p="0.55", calendar_id="CAL-NSO-12"), "2026-12-07T02:00:00Z")
        self.assertEqual(c, 2, o); self.assertIn("đã có bằng chứng", o)               # có bằng chứng trong sổ: robot từ chối
        # chưa có bằng chứng trong sổ lúc nộp: robot nhận, nhưng khi bằng chứng tới thì dòng đó không bao giờ là năng lực
        q2 = "IIP tháng 11 có tăng từ 8% trở lên so với cùng kỳ không?"
        c, o = self._run("ledger_intake.py", 512, _forecast("A", question=q2, calendar_id="CAL-NSO-12"), "2026-12-07T02:00:00Z")
        self.assertEqual(c, 0, o)
        before = json.dumps(self._rows("ledger/predictions.jsonl")[-1], sort_keys=True)
        c, o = self._run("resolution_intake.py", 612, _pub("F-512", "2026-12-06T02:00:00Z"), "2026-12-08T02:00:00Z")
        self.assertEqual(c, 0, o)
        row = [r for r in self._rows("ledger/predictions.jsonl") if r["id"] == "F-512"][0]
        self.assertEqual(json.dumps(row, sort_keys=True), before)                    # dòng bất biến
        verified, errs = self._verified()
        self.assertEqual(errs, [])
        self.assertIn("F-512", verified)                                             # xuất xứ lịch đạt…
        pubs = self._rows("ledger/publication_evidence.jsonl")
        cal = self._rows("governance/release_calendar.jsonl")
        self.assertEqual(ledger_intake.timing_verification_status(row, pubs, cal, verified), "after_publication")   # …nhưng bị loại
        self.assertFalse(ledger_intake.capability_test_eligible(row, pubs, cal, verified))
        self.assertEqual(laws_checks.check_ledger_rows(self.tmp), [])

    def test_late_recorded_evidence_can_only_move_publication_earlier(self):
        q = "Bán lẻ tháng 11 có tăng từ 9% trở lên so với cùng kỳ không?"
        c, o = self._run("ledger_intake.py", 520, _forecast("A", question=q, calendar_id="CAL-NSO-12"), "2026-12-03T02:00:00Z")
        self.assertEqual(c, 0, o)
        c, o = self._run("resolution_intake.py", 620, _pub("F-520", "2026-12-06T02:00:00Z"), "2026-12-06T05:00:00Z")
        self.assertEqual(c, 0, o)
        verified, _ = self._verified()
        cal = self._rows("governance/release_calendar.jsonl")
        row = self._rows("ledger/predictions.jsonl")[-1]
        self.assertEqual(ledger_intake.timing_verification_status(row, self._rows("ledger/publication_evidence.jsonl"), cal, verified),
                         "eligible")
        # phát hiện sau: số đã lộ từ 02/12 (trước dự báo 03/12). Bằng chứng sớm hơn được ghi thêm; muộn hơn thì không.
        c, o = self._run("resolution_intake.py", 621, _pub("F-520", "2026-12-07T02:00:00Z"), "2026-12-09T02:00:00Z")
        self.assertEqual(c, 2, o); self.assertIn("SỚM HƠN", o)
        c, o = self._run("resolution_intake.py", 622, _pub("F-520", "2026-12-02T02:00:00Z"), "2026-12-10T02:00:00Z")
        self.assertEqual(c, 0, o)
        pubs = self._rows("ledger/publication_evidence.jsonl")
        self.assertEqual(len(pubs), 2)
        self.assertEqual(ledger_intake.timing_verification_status(row, pubs, cal, verified), "after_publication")
        self.assertEqual(self._rows("ledger/predictions.jsonl")[-1], row)            # dòng dự báo không bị viết lại
        self.assertEqual(laws_checks.check_ledger_rows(self.tmp), [])
        self.assertEqual(laws_checks.check_ledger_chain(self.tmp), [])

    def test_unclear_publication_and_future_publication_are_refused(self):
        c, o = self._run("ledger_intake.py", 530, _forecast("A", calendar_id="CAL-NSO-12"), "2026-12-01T02:00:00Z")
        self.assertEqual(c, 0, o)
        c, o = self._run("resolution_intake.py", 630, _pub("F-530", "2026-12-06"), "2026-12-07T02:00:00Z")
        self.assertEqual(c, 2, o); self.assertIn("không rõ thời điểm", o)
        c, o = self._run("resolution_intake.py", 631, _pub("F-530", "2026-12-21T00:00:00Z"), "2026-12-07T02:00:00Z")
        self.assertEqual(c, 2, o); self.assertIn("tương lai", o)

    def test_lock_is_independent_of_resolve_at_and_cannot_be_reset(self):
        self.assertEqual(self._pin(402, "CAL-NSO-28", lock="2026-12-28")[0], 0)
        self.assertEqual(self._pin(403, "CAL-NSO-0115", lock="2027-01-15")[0], 0)
        c, o = self._run("ledger_intake.py", 501, _forecast("A", lock=None, calendar_id="CAL-NSO-12"), "2026-11-18T02:00:00Z")
        self.assertEqual(c, 2, o); self.assertIn("thiếu info_lock_at", o)
        c, o = self._run("ledger_intake.py", 502, _forecast("A", lock="2027-01-15", calendar_id="CAL-NSO-0115"), "2026-11-18T02:00:00Z")
        self.assertEqual(c, 2, o); self.assertIn("không được sau resolve_at", o)
        c, o = self._run("ledger_intake.py", 504, _forecast("A", calendar_id="CAL-NSO-12"), "2026-11-18T02:00:00Z")
        self.assertEqual(c, 0, o)
        c, o = self._run("ledger_intake.py", 505, _forecast("B", p="0.7", lock="2026-12-28", calendar_id="CAL-NSO-28"), "2026-11-18T03:00:00Z")
        self.assertEqual(c, 2, o); self.assertIn("không được đặt lại", o)
        c, o = self._run("ledger_intake.py", 505, _forecast("B", p="0.7", calendar_id="CAL-NSO-12"), "2026-11-18T03:00:00Z")
        self.assertEqual(c, 0, o)
        c, o = self._run("ledger_intake.py", 504, _forecast("A", lock="2026-12-28", calendar_id="CAL-NSO-28"), "2026-11-18T02:00:00Z")
        self.assertEqual(c, 2, o); self.assertIn("KHÔNG khớp thân Issue", o)          # chạy lại không đổi được hạn khóa
        # sát hạn khóa: 19/12 23:40 giờ VN = 16:40 UTC
        body = _forecast("A", question="IIP tháng 12/2026 có tăng từ 8% trở lên so với cùng kỳ không?", calendar_id="CAL-NSO-12")
        c, o = self._run("ledger_intake.py", 510, body, "2026-12-19T16:40:00Z", TTC_INTAKE_NOW="2026-12-19T16:41:00Z")
        self.assertEqual(c, 2, o); self.assertIn("info_lock_at", o)


class CapabilityScoreTests(unittest.TestCase):
    """Lỗi 3: Brier, hit_rate, hiệu chuẩn và số A–B năng lực chỉ tính trên dự báo hợp lệ; số thô tách riêng, có nhãn."""
    CAL = (lambda r: {**r, "hash": laws_checks.line_hash(r)})(
        {"calendar_id": "CAL-TEST", "domains": ["nso.gov.vn"], "info_lock_at": "2026-12-20",
         "evidence_url": "https://www.nso.gov.vn/lich", "quote": "Số tháng 11 được công bố ngày 20/12/2026.",
         "recorder": "Owner", "issue_number": 900001, "issue_created_at": "2026-11-01T00:00:00Z", "prev_hash": "GENESIS"})

    def _pairs(self, n, start, a_right, a_p=0.7, b_p=0.3, day="2026-11-17T02:00:00Z"):
        preds, res = [], []
        for i in range(n):
            q = f"Câu hỏi {start}-{i}?"
            for seat, p, num in (("A", a_p, start + 2 * i), ("B", b_p, start + 2 * i + 1)):
                preds.append({"id": f"F-{num}", "issue_number": num, "issue_created_at": day, "seat": seat, "question": q,
                              "resolve_at": "2026-12-31", "p": p, "base_rate": 0.5, "info_lock_at": "2026-12-20",
                              "resolution_source": "nso.gov.vn", "calendar_id": "CAL-TEST",
                              "author_seat": "Claude Project TTC" if seat == "A" else "Claude trần"})
                res.append({"prediction_id": f"F-{num}", "outcome": 1 if i < a_right else 0, "resolution_issue": 90000 + num})
        return preds, res

    def test_invalid_forecasts_do_not_beautify_brier_or_hit_rate(self):
        good_p, good_r = self._pairs(4, 1000, a_right=1)                          # hợp lệ: A đúng 1/4
        late_p, late_r = self._pairs(6, 2000, a_right=6, a_p=0.95, b_p=0.05)      # không hợp lệ: A "đúng" 6/6 với p 0,95
        verified = {p["id"] for p in good_p + late_p}
        pubs = [{"question": p["question"], "resolve_at": "2026-12-31", "published_at": "2026-11-10T00:00:00Z"}
                for p in late_p if p["seat"] == "A"]                               # đã công bố trước khi dự báo
        out = engine_ledger.issue_summary(good_p + late_p, good_r + late_r, pubs, [self.CAL], verified, "injected")
        only_good = engine_ledger.issue_summary(good_p, good_r, [], [self.CAL], verified, "injected")
        self.assertEqual(out["scores"], only_good["scores"])                        # điểm năng lực không đổi
        self.assertEqual((out["ab"]["a_correct"], out["ab"]["disagreements_resolved"], out["ab"]["a_accuracy"]),
                         (only_good["ab"]["a_correct"], only_good["ab"]["disagreements_resolved"], only_good["ab"]["a_accuracy"]))
        self.assertEqual(out["counts"], {"recorded": 20, "timing_valid": 8, "resolved": 20, "resolved_timing_valid": 8,
                                         "by_timing_status": {"after_publication": 12, "eligible": 8}})
        self.assertLess(out["raw_audit"]["scores"]["A"]["brier"], out["scores"]["A"]["brier"])     # số thô "đẹp" hơn…
        self.assertIn("KHÔNG PHẢI BẰNG CHỨNG NĂNG LỰC", out["raw_audit"]["label"])                   # …và được gắn nhãn
        self.assertEqual(out["raw_audit"]["ab_running"]["a_correct"], 7)
        self.assertEqual(out["void"]["by_seat"]["A"]["brier_void_worst"], only_good["void"]["by_seat"]["A"]["brier_void_worst"])
        # không có xác nhận xuất xứ (chạy ngoài GitHub): không có điểm năng lực nào
        none = engine_ledger.issue_summary(good_p, good_r, [], [self.CAL], None, None)
        self.assertEqual(none["scores"], {})
        self.assertEqual(none["counts"]["timing_valid"], 0)
        self.assertEqual(none["timing_verification_source"], "none")
        self.assertEqual(none["raw_audit"]["scores"]["A"]["n"], 4)

    def test_fixed_sample_is_not_replaced_by_later_pairs(self):
        first_p, first_r = self._pairs(194, 10000, a_right=120)
        later_p, later_r = self._pairs(40, 50000, a_right=40)
        verified = {p["id"] for p in first_p + later_p} - {first_p[0]["id"]}    # một cặp trong mẫu chưa xác nhận xuất xứ
        out = engine_ledger.issue_summary(first_p + later_p, first_r + later_r, [], [self.CAL], verified, "injected")
        ab = out["ab"]
        self.assertEqual(ab["fixed_sample"]["n"], 194)
        self.assertTrue(ab["verdict"].startswith("CHƯA ĐỦ ĐIỀU KIỆN KẾT LUẬN"))
        self.assertEqual(ab["timing"], {"blocked_pairs": 1, "reasons": {"provenance_unverified": 1}, "sample_replaced": False,
                                        "fixed_sample_counts_are_capability": False})
        self.assertIsNone(ab["fixed_sample"]["p_value_void_as_a_wrong"])
        self.assertEqual(engine_ledger.TARGET_DISAGREEMENTS, 194)
        full = engine_ledger.issue_summary(first_p + later_p, first_r + later_r, [], [self.CAL],
                                           {p["id"] for p in first_p + later_p}, "injected")
        self.assertEqual(full["ab"]["verdict"], "A HƠN B CÓ Ý NGHĨA")
        self.assertTrue(full["ab"]["timing"]["fixed_sample_counts_are_capability"])


class DirectionalAccuracyTests(unittest.TestCase):
    """hit_rate cũ = mean(outcome). Tách observed_yes_rate và directional_accuracy. Không đổi Brier hay right() của mẫu 194."""
    CAL = (lambda r: {**r, "hash": laws_checks.line_hash(r)})(
        {"calendar_id": "CAL-TEST", "domains": ["nso.gov.vn"], "info_lock_at": "2026-12-20",
         "evidence_url": "https://www.nso.gov.vn/lich", "quote": "Số tháng 11 được công bố ngày 20/12/2026.",
         "recorder": "Owner", "issue_number": 900001, "issue_created_at": "2026-11-01T00:00:00Z", "prev_hash": "GENESIS"})

    def test_yes_no_and_neutral_are_not_collapsed_into_hit_rate(self):
        cases = [("yes-right", 0.8, 1), ("no-right", 0.2, 0), ("yes-wrong", 0.9, 0),
                 ("no-wrong", 0.1, 1), ("neutral-yes", 0.5, 1), ("neutral-no", 0.5, 0)]
        preds, res = [], []
        for i, (name, p, outcome) in enumerate(cases):
            num = 3000 + i
            q = f"Câu hướng {name} có đủ mười ký tự không?"
            preds.append({"id": f"F-{num}", "issue_number": num, "issue_created_at": "2026-11-17T02:00:00Z", "seat": "A",
                          "question": q, "resolve_at": "2026-12-31", "p": p, "base_rate": 0.5, "info_lock_at": "2026-12-20",
                          "resolution_source": "nso.gov.vn", "calendar_id": "CAL-TEST", "author_seat": "Claude Project TTC"})
            res.append({"prediction_id": f"F-{num}", "outcome": outcome, "resolution_issue": 80000 + num})
        verified = {p["id"] for p in preds}
        out = engine_ledger.issue_summary(preds, res, [], [self.CAL], verified, "injected")
        a = out["scores"]["A"]
        self.assertEqual(a["observed_yes_rate"], 0.5)            # 3 YES / 6 dòng
        self.assertEqual(a["hit_rate"], a["observed_yes_rate"])
        self.assertEqual(a["hit_rate_meaning"], "observed_yes_rate")
        self.assertEqual((a["directional_correct"], a["directional_n"], a["neutral_excluded"], a["directional_accuracy"]),
                         (2, 4, 2, 0.5))
        self.assertEqual(a["brier"], 0.3667)                     # (2×0,04 + 2×0,81 + 2×0,25) / 6
        bin_ = a["calibration"]["0.5-0.6"]
        self.assertEqual((bin_["n"], bin_["hit_rate"]), (2, 0.5))  # tỷ lệ YES trong ô, không phải accuracy
        self.assertEqual(a["calibration_hit_rate_meaning"], "observed_yes_rate_in_bin")
        self.assertEqual(engine_ledger.TARGET_DISAGREEMENTS, 194)
        # p = 0,5 không tạo bất đồng (tích hai phía = 0), nên không đụng mẫu 194. Một bất đồng thật vẫn chấm đúng chiều.
        q = "Cặp bất đồng thật có bị đổi luật 194 không?"
        for seat, p, num in (("A", 0.2, 3100), ("B", 0.8, 3101)):
            preds.append({"id": f"F-{num}", "issue_number": num, "issue_created_at": "2026-11-17T02:00:00Z", "seat": seat,
                          "question": q, "resolve_at": "2026-12-31", "p": p, "base_rate": 0.5, "info_lock_at": "2026-12-20",
                          "resolution_source": "nso.gov.vn", "calendar_id": "CAL-TEST",
                          "author_seat": "Claude Project TTC" if seat == "A" else "Claude trần"})
            res.append({"prediction_id": f"F-{num}", "outcome": 0, "resolution_issue": 82000 + num})
        out2 = engine_ledger.issue_summary(preds, res, [], [self.CAL], {p["id"] for p in preds}, "injected")
        self.assertEqual(out2["ab"]["a_correct"], 1)
        self.assertEqual(out2["ab"]["disagreements_resolved"], 1)


class ForecastSchemaTests(unittest.TestCase):
    def test_schema_requires_lock_fields_and_legacy_rows_still_replay(self):
        import jsonschema
        schema = json.loads((ROOT / "contracts" / "forecast_issue.schema.json").read_text(encoding="utf-8"))
        self.assertIn("info_lock_at", schema["required"])
        self.assertIn("calendar_id", schema["required"])
        body = {"seat": "A", "question": "Câu hỏi đủ dài để qua schema?", "resolution_source": "nso.gov.vn",
                "resolution_rule": "comparison", "resolve_at": "2026-12-31", "p": 0.4, "base_rate": 0.5,
                "invalidation_conditions": "đổi rổ", "author_seat": "Grok (xAI)", "model_cutoff": "2026-06"}
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(body, schema)
        legacy_schema = ledger_intake.schema_for_forecast(schema, legacy=True)
        self.assertNotIn("info_lock_at", legacy_schema["required"])
        self.assertNotIn("calendar_id", legacy_schema["required"])
        errs = ledger_intake.ledger_errors(ledger_intake.load_rows(ROOT / "ledger" / "predictions.jsonl"),
                                           ledger_intake.load_rows(ROOT / "ledger" / "resolutions.jsonl"))
        self.assertEqual(errs, [])


class LegacyTests(unittest.TestCase):
    def test_legacy_forecasts_stay_pinned_and_are_not_valid_without_proof(self):
        pred = ledger_intake.load_rows(ROOT / "ledger" / "predictions.jsonl")
        legacy = [r for r in pred if r["id"] in ledger_intake.LEGACY_TIMING_IDS]
        self.assertEqual([r["id"] for r in legacy], [f"F-{n}" for n in range(37, 43)])
        for r in legacy:
            self.assertNotIn("info_lock_at", r); self.assertNotIn("calendar_id", r)
            self.assertEqual(r["hash"], ledger_intake.LEGACY_TIMING_HASHES[r["id"]])
            self.assertTrue(ledger_intake.is_legacy_timing_row(r))
            self.assertEqual(ledger_intake.timing_verification_status(r, []), "legacy_unproven")
            self.assertFalse(ledger_intake.capability_test_eligible(r, [], None, {r["id"]}))
        proven = dict(legacy[0])
        pubs = [{"question": proven["question"], "resolve_at": proven["resolve_at"], "published_at": "2026-12-06T02:00:00Z"}]
        self.assertEqual(ledger_intake.timing_verification_status(proven, pubs), "provenance_unverified")
        self.assertEqual(ledger_intake.timing_verification_status(proven, pubs, None, {proven["id"]}), "legacy_proven_by_evidence")
        early = [{"question": proven["question"], "resolve_at": proven["resolve_at"], "published_at": "2026-11-18T01:00:00Z"}]
        self.assertEqual(ledger_intake.timing_verification_status(proven, early, None, {proven["id"]}), "after_publication")
        unclear = [{"question": proven["question"], "resolve_at": proven["resolve_at"], "published_at": "2026-12-06"}]
        self.assertEqual(ledger_intake.timing_verification_status(proven, unclear), "unclear_publication")
        self.assertEqual(laws_checks.check_timing_legacy_pin(ROOT), [])
        self.assertEqual(laws_checks.check_ledger_rows(ROOT), [])
        tmp = pathlib.Path(tempfile.mkdtemp())
        try:
            (tmp / "ledger").mkdir()
            tampered = tmp / "ledger" / "predictions.jsonl"
            shutil.copy(ROOT / "ledger" / "predictions.jsonl", tampered)
            tampered.write_text(tampered.read_text(encoding="utf-8").replace("3,50%", "3,51%", 1), encoding="utf-8")
            self.assertTrue(any("F-37" in e for e in laws_checks.check_timing_legacy_pin(tmp)))
            # gắn calendar_id hồi tố (tính lại hash): lệch hash đã ghim, và mất quyền chuyển tiếp
            rows = ledger_intake.load_rows(ROOT / "ledger" / "predictions.jsonl")
            rows[0]["calendar_id"] = "CAL-HOI-TO"; rows[0]["hash"] = laws_checks.line_hash(rows[0])
            self.assertFalse(ledger_intake.is_legacy_timing_row(rows[0]))
            tampered.write_text("".join(ledger_intake.dumps(r) + "\n" for r in rows), encoding="utf-8")
            self.assertTrue(any("F-37" in e for e in laws_checks.check_timing_legacy_pin(tmp)))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        # dòng khác mượn mã F-37 không được miễn lịch
        imposter = {**legacy[0], "hash": "0" * 64}
        self.assertFalse(ledger_intake.is_legacy_timing_row(imposter))


class RobotFlowTests(_Repo):
    def test_valid_robot_flow_still_records_forecasts_and_resolutions(self):
        """Lịch → dự báo A/B → bằng chứng công bố (sau dự báo) → phân định: mọi bước ghi được, sổ sạch, kiểm toán GitHub
        xác nhận xuất xứ, và cặp được tính là hợp lệ."""
        self.assertEqual(self._pin(401, "CAL-NSO-12")[0], 0)
        c, o = self._run("ledger_intake.py", 501, _forecast("A", calendar_id="CAL-NSO-12"), "2026-11-18T02:00:00Z")
        self.assertEqual(c, 0, o)
        c, o = self._run("ledger_intake.py", 502, _forecast("B", p="0.6", calendar_id="CAL-NSO-12"), "2026-11-18T03:00:00Z")
        self.assertEqual(c, 0, o)
        c, o = self._run("resolution_intake.py", 601, _pub("F-501", "2026-12-20T02:00:00Z"), "2026-12-20T05:00:00Z")
        self.assertEqual(c, 0, o)
        c, o = self._run("resolution_intake.py", 701, _resolution("F-501", "YES"), "2027-01-02T02:00:00Z")
        self.assertEqual(c, 0, o)
        self.assertEqual(laws_checks.check_ledger_rows(self.tmp), [])
        self.assertEqual(laws_checks.check_ledger_chain(self.tmp), [])
        verified, errs = self._verified()
        self.assertEqual(errs, [])
        self.assertEqual(verified, {"F-501", "F-502"})
        preds, res = self._rows("ledger/predictions.jsonl"), self._rows("ledger/resolutions.jsonl")
        out = engine_ledger.issue_summary(preds, res, self._rows("ledger/publication_evidence.jsonl"),
                                          self._rows("governance/release_calendar.jsonl"), verified, "github_api")
        self.assertEqual(out["counts"]["timing_valid"], 2)
        self.assertEqual(out["ab"]["disagreements_resolved"], 1)
        self.assertEqual(out["ab"]["a_correct"], 0)                                    # A=0,4 nói NO, kết quả YES
        self.assertEqual(sorted(out["scores"]), ["A", "B"])

    def test_fixture_helper_pins_through_the_robot(self):
        body = with_calendar(self.tmp, _forecast("A"))
        self.assertIn("### calendar_id", body)
        cal = self._rows("governance/release_calendar.jsonl")
        self.assertEqual(len(cal), 1); self.assertIsInstance(cal[0]["issue_number"], int)
        self.assertEqual(run_calendar(self.tmp, cal[0]["issue_number"],
                                      calendar_body(cal[0]["calendar_id"], cal[0]["domains"], cal[0]["info_lock_at"]))[0], 3)


if __name__ == "__main__":
    unittest.main()
