"""Phân định dự báo Issue (tools/resolution_intake.py), chấm A–B (engine/ledger.issue_summary), sổ thử L-06 và Deflated Sharpe.
Mọi thứ chạy trong thư mục tạm và tiến trình con: không chạm tệp nào của kho.
"""
import csv, json, math, os, pathlib, shutil, subprocess, sys, tempfile, textwrap, unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import laws_checks  # noqa: E402
from tools.ledger_intake import control_b_hash  # noqa: E402

B_HASH = control_b_hash(ROOT / "governance" / "CONTROL_B_PROMPT.md")
Q1 = "Nợ nhóm 3-5 của VCB tại 31/12/2026 cao hơn tại 30/9/2026?"
Q2 = "NHNN đổi lãi suất tái cấp vốn trước 31/01/2027?"


def _forecast(seat, question, p, resolve_at="2026-12-31", rule="comparison", author=None, source="https://www.nso.gov.vn — thông cáo"):
    f = {"seat": seat, "question": question, "resolution_source": source,
         "resolution_rule": rule, "resolve_at": resolve_at, "p": str(p), "base_rate": "0.5",
         "invalidation_conditions": "Nguồn đổi định nghĩa chỉ tiêu",
         "author_seat": author or ("Claude Project TTC" if seat == "A" else "Claude trần"), "model_cutoff": "2026-06"}
    if seat == "B":
        f["prompt_hash"] = B_HASH
    return "\n\n".join(f"### {k}\n\n{v}" for k, v in f.items())


def _resolution(ids, outcome, resolver="Owner", quote="Tỷ lệ nợ xấu 1,12% tại 31/12/2026",
                source="https://www.nso.gov.vn/thong-cao.pdf", void_reason="_No response_"):
    f = {"forecast_ids": ids, "outcome": outcome, "observed_value": "_No response_", "resolution_source": source,
         "quote": quote, "resolver": resolver, "void_reason": void_reason}
    return "\n\n".join(f"### {k}\n\n{v}" for k, v in f.items())


class _Base(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        (self.tmp / "contracts").mkdir(); (self.tmp / "governance").mkdir(); (self.tmp / "ledger").mkdir()
        for c in ("forecast_issue.schema.json", "resolution.schema.json"):
            shutil.copy(ROOT / "contracts" / c, self.tmp / "contracts")
        shutil.copy(ROOT / "governance" / "CONTROL_B_PROMPT.md", self.tmp / "governance")
        shutil.copytree(ROOT / "tools", self.tmp / "tools", ignore=shutil.ignore_patterns("__pycache__"))
        for n, seat, q, p, ra, rule in [(101, "A", Q1, 0.30, "2026-12-31", "comparison"),
                                         (102, "B", Q1, 0.60, "2026-12-31", "comparison"),
                                         (103, "A", Q2, 0.70, "2027-01-31", "event_before_date"),
                                         (104, "B", Q2, 0.80, "2027-01-31", "event_before_date")]:
            self._fc(n, _forecast(seat, q, p, ra, rule))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run(self, script, number, body, created, **env):
        e = {**os.environ, "ISSUE_NUMBER": str(number), "ISSUE_CREATED_AT": created, "ISSUE_BODY": body, **env}
        r = subprocess.run([sys.executable, str(self.tmp / "tools" / script)], env=e, capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr

    def _fc(self, number, body, created="2026-11-17T02:00:00Z", expect=0):
        c, o = self._run("ledger_intake.py", number, body, created)
        self.assertEqual(c, expect, o)
        return o

    def _res(self, number, body, created):
        return self._run("resolution_intake.py", number, body, created)

    def _rows(self, name="resolutions.jsonl"):
        p = self.tmp / "ledger" / name
        return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []

    def _raw_prediction(self, **kw):
        """Chèn thẳng một dòng dự báo (giả lập dòng cũ ghi trước khi có luật) — không qua intake."""
        led = self.tmp / "ledger" / "predictions.jsonl"
        row = dict(self._rows("predictions.jsonl")[0]); row.update(kw)
        with led.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def _summary(self, as_of="2027-02-05"):
        env = {**os.environ, "TTC_HOME": str(self.tmp), "PYTHONPATH": str(ROOT)}
        code = textwrap.dedent(f"""
            import json
            from engine import ledger
            print(json.dumps(ledger.scorecard("{as_of}")["issue_forecasts"], ensure_ascii=False))
        """)
        r = subprocess.run([sys.executable, "-c", code], cwd=str(ROOT), env=env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr[-2000:])
        return json.loads(r.stdout.strip().splitlines()[-1])


class ResolutionRuleTests(_Base):
    def test_rules_then_ab_scorecard(self):
        when = "2027-01-02T03:00:00Z"
        c, o = self._res(201, _resolution("F-101, F-102", "NO"), "2026-12-15T03:00:00Z")
        self.assertEqual(c, 2, o); self.assertIn("L-05", o)                      # phân định trước hạn
        c, o = self._res(203, _resolution("F-101, F-103", "NO"), when)
        self.assertEqual(c, 2, o)                                                # hai câu hỏi khác nhau
        c, o = self._res(204, _resolution("F-101, F-102", "NO", quote="_No response_"), when)
        self.assertEqual(c, 2, o)                                                # YES/NO thiếu trích nguyên văn
        c, o = self._res(210, _resolution("F-101", "NO", source="https://vnexpress.net/bai-bao"), when)
        self.assertEqual(c, 2, o); self.assertIn("tên miền", o)                  # đổi nguồn sau khi biết kết quả
        c, o = self._res(211, _resolution("F-101", "NO", source="https://nso.gov.vn.evil.com/x"), when)
        self.assertEqual(c, 2, o)                                                # tên miền giả dạng
        c, o = self._res(212, _resolution("F-101", "NO") + "\n\n### outcome\n\nYES", when)
        self.assertEqual(c, 2, o); self.assertIn("hai tiêu đề", o)               # chèn tiêu đề thứ hai để đè
        c, o = self._run("resolution_intake.py", 213, _resolution("F-101", "NO"), when, ISSUE_AUTHOR="nguoi-la", REPO_OWNER="chu-kho")
        self.assertEqual(c, 2, o); self.assertIn("chủ kho", o)                   # không phải chủ kho mở
        # Chỉ liệt kê F-101 nhưng câu hỏi có F-101 và F-102 → ghi cả hai cùng một outcome (một câu hỏi một sự thật)
        c, o = self._res(205, _resolution("F-101", "NO"), when)
        self.assertEqual(c, 0, o); self.assertIn("F-102", o)
        self.assertEqual(self._res(205, _resolution("F-101", "NO"), when)[0], 3)                  # chạy lại cùng Issue
        c, o = self._res(206, _resolution("F-102", "YES"), "2027-01-03T03:00:00Z")
        self.assertEqual(c, 2, o); self.assertIn("không phân định lại", o)       # không gán sự thật thứ hai cho B
        c, o = self._res(207, _resolution("F-103, F-104", "VOID"), "2027-02-02T03:00:00Z")
        self.assertEqual(c, 2, o)                                                # VOID thiếu lý do
        c, o = self._res(208, _resolution("F-103, F-104", "YES"), "2026-12-20T03:00:00Z")
        self.assertEqual(c, 0, o)                                                # YES khi cả câu hỏi là event_before_date: được sớm
        rows = self._rows()
        self.assertEqual([(r["prediction_id"], r["outcome"]) for r in rows],
                         [("F-101", 0), ("F-102", 0), ("F-103", 1), ("F-104", 1)])
        self.assertTrue(all(r["resolver"] == "Owner" and r["quote"] for r in rows))
        self.assertEqual(laws_checks.check_ledger_rows(self.tmp), [])            # chạy lại luật trên sổ vừa ghi: đạt
        self.assertEqual(laws_checks.check_ledger_chain(self.tmp), [])           # resolutions.jsonl có chuỗi hash
        rp = self.tmp / "ledger" / "resolutions.jsonl"
        rp.write_text(rp.read_text(encoding="utf-8").replace('"outcome": 0', '"outcome": 1', 1), encoding="utf-8")
        self.assertTrue(any("phân định" in e for e in laws_checks.check_ledger_chain(self.tmp)))   # sửa kết quả → đỏ
        rp.write_text(rp.read_text(encoding="utf-8").replace('"outcome": 1', '"outcome": 0', 1), encoding="utf-8")

        sc = self._summary()
        self.assertEqual(sc["by_seat"]["A"], {"n": 2, "resolved": 2, "void": 0, "pending": 0})
        self.assertAlmostEqual(sc["scores"]["A"]["brier"], 0.09, places=4)       # ((0,3-0)² + (0,7-1)²)/2
        self.assertAlmostEqual(sc["scores"]["B"]["brier"], 0.2, places=4)        # ((0,6-0)² + (0,8-1)²)/2
        self.assertAlmostEqual(sc["scores"]["A"]["brier_coin"], 0.25, places=4)
        ab = sc["ab"]
        self.assertEqual((ab["pairs"], ab["unpaired"], ab["not_same_day"], ab["disagreements"]), (2, 0, 0, 1))
        self.assertEqual((ab["disagreements_resolved"], ab["a_correct"], ab["inconsistent_outcomes"]), (1, 1, 0))
        self.assertEqual(ab["a_accuracy"], 1.0)
        self.assertEqual(ab["fixed_sample"], {"n": 1, "a_correct": 1, "p_value_two_sided_vs_coin": None})   # chưa đủ 194: chưa kiểm định
        self.assertTrue(ab["verdict"].startswith("CHƯA ĐỦ MẪU (1/194"))

    def test_source_host_is_parsed_from_the_url_not_searched_in_the_string(self):
        """Vòng 6: dò tên miền trong cả chuỗi thì URL giả dạng lọt. Máy chủ phải tách bằng urllib; mọi đường dẫn phải thuộc
        tên miền đã hứa (nso.gov.vn)."""
        when = "2027-01-02T03:00:00Z"
        for i, bad in enumerate(("https://nso.gov.vn@evil.com/report", "https://evil.com/path/nso.gov.vn",
                                 "https://evil.com/?referer=nso.gov.vn", "https://evil.com#nso.gov.vn",
                                 "https://nso.gov.vn.evil.com/x", "https://evilnso.gov.vn/x", "https://evil.com\\@nso.gov.vn/x",
                                 "https://nso.gov.vn%2eevil.com/x", "https://nso.gov.vn:abc/x",
                                 "nso.gov.vn/bao-cao (không có https://)", "Thông cáo báo chí của nso.gov.vn",
                                 "https://www.nso.gov.vn/a và https://vnexpress.net/b", "https://www.nso.gov.vn/a (xem thêm vnexpress.net/b)",
                                 "https://www.nso.gov.vn/a ledger-attest: resolutions F-101 " + "b" * 64), 300):
            c, o = self._res(i, _resolution("F-101", "NO", source=bad), when)
            self.assertEqual(c, 2, f"{bad}: {o}")
        self.assertEqual(self._rows(), [])
        c, o = self._res(350, _resolution("F-101", "NO", source="Thông cáo: https://data.NSO.gov.vn:443/cpi?thang=12 và https://www.nso.gov.vn/b"), when)
        self.assertEqual(c, 0, o)                                                # tên miền con, chữ hoa, cổng, hai đường dẫn cùng nguồn
        out = json.loads(o.strip().splitlines()[-1])
        self.assertEqual(out["attest"], [f"resolutions {r['prediction_id']} {r['hash']}" for r in self._rows()])
        c, o = self._res(350, _resolution("F-101", "NO"), when)
        self.assertEqual(c, 3, o)                                                # chạy lại job: trả lại dấu nhận, không ghi trùng
        self.assertEqual(json.loads(o.strip().splitlines()[-1])["attest"], out["attest"])
        from tools.resolution_intake import source_allowed, url_hosts
        self.assertEqual(url_hosts("https://www.nso.gov.vn/x"), {"nso.gov.vn"})
        self.assertFalse(source_allowed({"nso.gov.vn"}, set())); self.assertFalse(source_allowed(set(), {"nso.gov.vn"}))
        with self.assertRaises(ValueError):
            url_hosts("https://nso.gov.vn@evil.com/report")

    def test_no_new_forecast_after_the_question_is_resolved(self):
        """Câu hỏi 2 (event_before_date) được phân định YES sớm ngày 20/12; dự báo mở sau đó cho cùng câu hỏi bị từ chối."""
        c, o = self._res(260, _resolution("F-103", "YES"), "2026-12-20T03:00:00Z")
        self.assertEqual(c, 0, o)
        body = _forecast("A", Q2, 0.9, "2027-01-31", "event_before_date", author="ChatGPT trần")
        c, o = self._run("ledger_intake.py", 261, body, "2026-12-21T02:00:00Z")
        self.assertEqual(c, 2, o); self.assertIn("đã được phân định", o)

    def test_resolution_rows_written_around_intake_are_rechecked(self):
        when = "2027-01-02T03:00:00Z"
        self.assertEqual(self._res(270, _resolution("F-101", "NO"), when)[0], 0)
        rp = self.tmp / "ledger" / "resolutions.jsonl"
        good = rp.read_text(encoding="utf-8")
        rows = [json.loads(l) for l in good.splitlines()]
        self.assertEqual(laws_checks.check_ledger_rows(self.tmp), [])
        def forged(edit, base=rows, drop=0):
            """Viết lại các dòng phân định với hash chuỗi HỢP LỆ (như một commit ghi vòng qua intake)."""
            out, prev = [], "GENESIS"
            for r in base[:len(base) - drop]:
                r = {k: v for k, v in r.items() if k not in ("hash", "prev_hash")}
                edit(r)
                r["prev_hash"] = prev; r["hash"] = laws_checks.line_hash(r); prev = r["hash"]
                out.append(json.dumps(r, ensure_ascii=False, sort_keys=True))
            rp.write_text("\n".join(out) + "\n", encoding="utf-8")
            self.assertEqual(laws_checks.check_ledger_chain(self.tmp), [])       # hash chuỗi không bắt được gì
            return laws_checks.check_ledger_rows(self.tmp)
        for edit, why in ((lambda r: r.update(resolver="Claude"), "chung ghế"),
                          (lambda r: r.update(resolution_issue_created_at="2026-12-15T03:00:00Z", resolved_at="2026-12-15"), "chưa tới resolve_at"),
                          (lambda r: r.update(resolution_source="https://vnexpress.net/bai"), "tên miền đã hứa"),
                          (lambda r: r.update(resolution_source="https://nso.gov.vn@evil.com/x"), "nguồn phân định"),
                          (lambda r: r.update(quote=""), "trích nguyên văn"),
                          (lambda r: r.update(resolved_at="2026-12-01"), "không khớp kết quả chạy lại"),
                          (lambda r: r.update(outcome=1) if r["prediction_id"] == "F-102" else None, "không khớp kết quả chạy lại"),
                          (lambda r: r.update(prediction_id="F-999"), "không có dự báo")):
            errs = forged(edit)
            self.assertTrue(errs and any(why in e for e in errs), f"{why}: {errs}")
        self.assertTrue(any("không khớp" in e for e in forged(lambda r: None, drop=1)))   # chỉ phân định A, bỏ B
        rp.write_text(good, encoding="utf-8")
        self.assertEqual(laws_checks.check_ledger_rows(self.tmp), [])

    def test_resolution_day_is_vietnam_time(self):
        """resolve_at 31/12/2026: 30/12 22:00 UTC là 05:00 ngày 31/12 giờ VN → được; 30/12 16:00 UTC (23:00 VN 30/12) → chưa."""
        c, o = self._res(220, _resolution("F-101", "NO"), "2026-12-30T16:00:00Z")
        self.assertEqual(c, 2, o); self.assertIn("L-05", o)
        c, o = self._res(221, _resolution("F-101", "NO"), "2026-12-30T22:00:00Z")
        self.assertEqual(c, 0, o)
        self.assertEqual(self._rows()[0]["resolved_at"], "2026-12-31")

    def test_void_is_counted_separately(self):
        c, o = self._res(230, _resolution("F-101", "VOID", void_reason="Nguồn đã hứa không công bố chỉ tiêu này"), "2027-01-05T03:00:00Z")
        self.assertEqual(c, 0, o)
        sc = self._summary()
        self.assertEqual(sc["by_seat"]["A"], {"n": 2, "resolved": 0, "void": 1, "pending": 1})
        self.assertEqual(sc["ab"]["disagreements_resolved"], 0)
        c, o = self._res(231, _resolution("F-102", "NO"), "2027-01-06T03:00:00Z")
        self.assertEqual(c, 2, o)                                                # VOID cũng khóa câu hỏi

    def test_early_yes_needs_every_forecast_to_be_event_rule(self):
        """Dòng cũ (không qua intake) cùng câu hỏi 2 nhưng luật comparison → YES sớm bị chặn cho cả câu hỏi."""
        self._raw_prediction(id="F-150", issue_number=150, question=Q2, resolve_at="2027-01-31", resolution_rule="comparison")
        c, o = self._res(240, _resolution("F-103", "YES"), "2026-12-20T03:00:00Z")
        self.assertEqual(c, 2, o); self.assertIn("L-05", o)


class ResolverSeatTests(_Base):
    def test_resolver_must_be_recognised_and_differ_from_every_author(self):
        q3 = "Tín dụng năm 2026 tăng từ 15% trở lên?"
        self._fc(111, _forecast("A", q3, 0.7))
        self._fc(112, _forecast("B", q3, 0.4, author="ChatGPT trần (OpenAI)"))
        when = "2027-01-05T03:00:00Z"
        for who in ("ai đó", "người phân định", "not_an_owner", "kế toán trưởng Owner"):       # không nhận ra ghế
            c, o = self._res(301, _resolution("F-111", "YES", resolver=who), when)
            self.assertEqual(c, 2, o); self.assertIn("L-09", o)
        for who in ("ChatGPT (OpenAI)", "GPT-5.5", "Claude", "Claude Opus", "Opus 5.5", "Sonnet", "Anthropic Haiku"):
            c, o = self._res(302, _resolution("F-111", "YES", resolver=who), when)              # trùng một ghế viết của câu hỏi
            self.assertEqual(c, 2, o); self.assertIn("L-09", o)
        self.assertEqual(self._rows(), [])
        c, o = self._res(303, _resolution("F-111", "YES", resolver="Grok (xAI)"), when)         # khác cả hai ghế viết
        self.assertEqual(c, 0, o)
        c, o = self._res(304, _resolution("F-101", "NO", resolver="ChatGPT (OpenAI)"), when)    # câu 1 chỉ có Claude viết
        self.assertEqual(c, 0, o)

    def test_owner_authored_forecast_cannot_be_resolved_by_owner(self):
        q4 = "Tỷ giá trung tâm ngày 31/12/2026 từ 25.650 đồng trở lên?"
        self._fc(121, _forecast("A", q4, 0.6, author="Owner (Trần Ngọc Thắng)"))
        when = "2027-01-05T03:00:00Z"
        for who in ("Owner", "Owner (Trần Ngọc Thắng)", "owner — kiểm lại", "Claude"):
            c, o = self._res(401, _resolution("F-121", "YES", resolver=who), when)
            self.assertEqual(c, 2, o); self.assertIn("L-09", o)
        self.assertEqual(self._rows(), [])
        c, o = self._res(402, _resolution("F-121", "YES", resolver="ChatGPT (OpenAI)"), when)
        self.assertEqual(c, 0, o)

    def test_unrecognised_author_seat_fails_closed(self):
        self._fc(131, _forecast("A", "Câu hỏi thử có ghế viết lạ?", 0.6, author="ai đó"), expect=2)
        self._raw_prediction(id="F-141", issue_number=141, question="Dòng cũ không rõ ghế viết?", author_seat="người viết")
        for who in ("Owner", "ChatGPT (OpenAI)"):
            c, o = self._res(501, _resolution("F-141", "NO", resolver=who), "2027-01-05T03:00:00Z")
            self.assertEqual(c, 2, o); self.assertIn("không nhận ra ghế viết", o)
        self.assertEqual(self._rows(), [])


class ScoringTests(_Base):
    def _fake(self, n_pairs, a_right, start=1000, a_day="2026-11-17T02:00:00Z", b_day="2026-11-17T03:00:00Z"):
        """Ghi thẳng n cặp bất đồng đã phân định (A=0,7; B=0,3), A đúng ở a_right cặp đầu."""
        preds, res = [], []
        for i in range(n_pairs):
            q = f"Câu hỏi giả lập số {i}?"
            for seat, p, num, day in (("A", 0.7, start + 2 * i, a_day), ("B", 0.3, start + 2 * i + 1, b_day)):
                preds.append({"id": f"F-{num}", "issue_number": num, "issue_created_at": day, "seat": seat, "question": q,
                              "resolve_at": "2026-12-31", "p": p, "base_rate": 0.5})
                res.append({"prediction_id": f"F-{num}", "outcome": 1 if i < a_right else 0})
        return preds, res

    def _score(self, preds, res):
        env = {**os.environ, "TTC_HOME": str(self.tmp), "PYTHONPATH": str(ROOT)}
        (self.tmp / "p.json").write_text(json.dumps([preds, res]), encoding="utf-8")
        code = "import json;from engine import ledger;p,r=json.load(open(r'%s'));print(json.dumps(ledger.issue_summary(p,r),ensure_ascii=False))" % (self.tmp / "p.json")
        r = subprocess.run([sys.executable, "-c", code], cwd=str(ROOT), env=env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr[-2000:])
        return json.loads(r.stdout.strip().splitlines()[-1])

    def test_fixed_sample_test_uses_only_first_194(self):
        """Phán quyết chốt ở 194 bất đồng đầu tiên: 109/194 (hai phía p≈0,098) → chưa thấy khác biệt, dù sau đó A đúng thêm 100 lần."""
        preds, res = self._fake(194, 109)
        ab = self._score(preds, res)["ab"]
        self.assertEqual(ab["fixed_sample"]["n"], 194)
        self.assertGreater(ab["fixed_sample"]["p_value_two_sided_vs_coin"], 0.05)
        self.assertEqual(ab["verdict"], "CHƯA THẤY KHÁC BIỆT A–B")
        more_p, more_r = self._fake(100, 100, start=5000)
        ab2 = self._score(preds + more_p, res + more_r)["ab"]
        self.assertEqual(ab2["fixed_sample"], ab["fixed_sample"])                # mẫu chốt không đổi
        self.assertEqual(ab2["verdict"], "CHƯA THẤY KHÁC BIỆT A–B")
        self.assertEqual(ab2["disagreements_resolved"], 294)                     # số chạy vẫn báo đủ
        win_p, win_r = self._fake(194, 112)
        self.assertEqual(self._score(win_p, win_r)["ab"]["verdict"], "A HƠN B CÓ Ý NGHĨA")
        lose_p, lose_r = self._fake(194, 82)
        self.assertEqual(self._score(lose_p, lose_r)["ab"]["verdict"], "B HƠN A CÓ Ý NGHĨA")

    def test_pairs_need_same_day_and_both_outcomes(self):
        preds, res = self._fake(3, 3, b_day="2026-11-18T03:00:00Z")              # B ghi hôm sau → không thành cặp
        ab = self._score(preds, res)["ab"]
        self.assertEqual((ab["pairs"], ab["not_same_day"], ab["disagreements_resolved"]), (0, 3, 0))
        preds, res = self._fake(2, 2)
        res[1]["outcome"] = 0                                                    # A=1, B=0 cho cùng câu hỏi: dữ liệu hỏng
        ab = self._score(preds, [r for r in res if r["prediction_id"] != "F-1003"])["ab"]   # cặp thứ hai: B chưa phân định
        self.assertEqual((ab["pairs"], ab["disagreements_resolved"], ab["inconsistent_outcomes"]), (2, 0, 1))
        self.assertIn("warning_inconsistent", ab)

    def test_malformed_rows_do_not_crash_scoring(self):
        preds, res = self._fake(1, 1)
        preds += [{"issue_number": 9, "id": "F-9", "seat": "A", "p": "không phải số", "question": "x", "resolve_at": "2026-12-31"},
                  {"issue_number": 10, "seat": "C", "p": 0.5}, {"issue_number": 11}]
        out = self._score(preds, res)
        self.assertEqual(out["malformed"], 3)
        self.assertEqual(out["ab"]["pairs"], 1)

    def test_low_disagreement_warning_only_after_60_pairs(self):
        preds, res = [], []
        for i in range(60):
            for seat, num in (("A", 2000 + 2 * i), ("B", 2001 + 2 * i)):
                preds.append({"id": f"F-{num}", "issue_number": num, "issue_created_at": "2026-11-17T02:00:00Z", "seat": seat,
                              "question": f"q{i}", "resolve_at": "2026-12-31", "p": 0.6, "base_rate": 0.5})
        self.assertIn("warning", self._score(preds, res)["ab"])
        self.assertNotIn("warning", self._score(preds[:118], res)["ab"])         # 59 cặp: chưa cảnh báo

    def test_binom_two_sided(self):
        from engine import ledger
        self.assertGreater(ledger._binom_two_sided(109, 194), 0.05)             # một phía ≈ 0,049 nhưng hai phía ≈ 0,098
        self.assertLess(ledger._binom_two_sided(112, 194), 0.05)
        self.assertEqual(ledger._binom_two_sided(0, 0), 1.0)
        self.assertAlmostEqual(ledger._binom_two_sided(2, 4), 1.0)


class TrialRegistryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        (self.tmp / "research").mkdir()
        shutil.copy(ROOT / "config.yaml", self.tmp / "config.yaml")

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
            def refused(tid, sp):
                try:
                    research.register_trial(tid, "2026-11-20", "random_subset", sp, 3.0); return False
                except RuntimeError:
                    return True
            print(json.dumps({"n": n, "n2": n2, "h1": h1, "dup": refused(f"T{n:05d}", spec),
                              "new_feature": refused("T00009", {"features": ["mom_60", "feature_moi"], "model": "ridge"}),
                              "new_model": refused("T00010", {"features": ["mom_60"], "model": "transformer"}),
                              "spec_id": research.spec_id(spec), "thr": research.threshold(n)}))
        """)
        self.assertEqual(code, 0, err[-2000:])
        d = json.loads(out.strip().splitlines()[-1])
        self.assertEqual((d["n"], d["n2"], d["dup"]), (1, 2, True))
        self.assertTrue(d["new_feature"] and d["new_model"])                    # ngoài không gian đóng băng → engine từ chối
        self.assertEqual(laws_checks.check_trial_registry(self.tmp), [])
        cols = ["trial_id", "cycle_date", "spec_id", "threshold", "registry_hash"]
        old = {"trial_id": "T00000", "cycle_date": "2026-11-20", "spec_id": "M-old", "threshold": "3.6", "registry_hash": ""}
        new = {"trial_id": "T00001", "cycle_date": "2026-11-20", "spec_id": d["spec_id"], "threshold": repr(d["thr"]),
               "registry_hash": d["h1"]}
        tp = self.tmp / "research" / "trials.csv"
        with tp.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerow(old); w.writerow(new)
        self.assertEqual(laws_checks.check_trial_registry(self.tmp), [])        # lần thử cũ (mã trước sổ, kể cả cùng ngày) không bị đòi
        with tp.open("a", encoding="utf-8", newline="") as f:
            csv.DictWriter(f, fieldnames=cols).writerow(new)                    # hai kết quả cho một lần đăng ký
        self.assertTrue(any("hai kết quả" in e for e in laws_checks.check_trial_registry(self.tmp)))
        with tp.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerow(new)
            w.writerow({"trial_id": "T00002", "cycle_date": "2026-11-20", "spec_id": "M-x", "threshold": "3.7", "registry_hash": ""})
        self.assertTrue(any("T00002" in e for e in laws_checks.check_trial_registry(self.tmp)))   # chạy không đăng ký
        reg = self.tmp / "research" / "trial_registry.jsonl"
        good = reg.read_text(encoding="utf-8")
        reg.write_text(good.replace("random_subset", "cross_family"), encoding="utf-8")
        self.assertTrue(any("hash" in e for e in laws_checks.check_trial_registry(self.tmp)))     # sửa sổ bị bắt
        # dòng đăng ký ngoài không gian đóng băng, hash hợp lệ (viết tay) → kiểm máy vẫn bắt
        row = json.loads(good.splitlines()[0])
        row.update(trial_id="T00003", features="mom_60;feature_moi", prev_hash=row["hash"]); row["hash"] = laws_checks.line_hash(row)
        reg.write_text(good + json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        self.assertTrue(any("đóng băng" in e for e in laws_checks.check_trial_registry(self.tmp)))

    def test_registration_is_on_main_before_the_backtest_and_survives_a_crash(self):
        """Vòng 6: register_trial chỉ ghi vào thư mục làm việc; vòng học hỏng sau đó thì mất, lần sau dùng lại T00001.
        Với TTC_REGISTRY_PUSH=1 dòng đăng ký được đẩy lên main trước khi backtest chạy; đẩy không được thì không chạy."""
        origin = self.tmp / "origin.git"
        def git(cwd, *a):
            r = subprocess.run(["git", "-C", str(cwd), "-c", "user.name=t", "-c", "user.email=t@t", *a], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, f"git {a}: {r.stderr}")
            return r.stdout.strip()
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True, capture_output=True)
        def clone(name):
            subprocess.run(["git", "clone", "-q", f"file://{origin}", str(self.tmp / name)], check=True, capture_output=True)
            return self.tmp / name
        seed = clone("seed")
        shutil.copy(ROOT / "config.yaml", seed / "config.yaml"); (seed / "research").mkdir(); (seed / "data.txt").write_text("v1\n")
        (seed / "research" / "trials.csv").write_text("trial_id\n", encoding="utf-8")
        git(seed, "add", "-A"); git(seed, "commit", "-qm", "seed"); git(seed, "push", "-q", "origin", "HEAD:main")
        script = """
            import json, sys
            from engine import research
            spec = {"features": ["mom_60"], "model": "ridge"}
            n = research.next_trial_number(None)
            research.register_trial(f"T{n:05d}", "2026-11-20", "random_subset", spec, research.threshold(n))
            print(json.dumps({"n": n}))
            sys.exit(7)        # vòng học hỏng NGAY SAU khi đăng ký: không có kết quả, không có commit cuối
        """
        def cycle(home, **env):
            e = {**os.environ, "TTC_HOME": str(home), "PYTHONPATH": str(ROOT), "TTC_REGISTRY_PUSH": "1",
                 "TTC_REGISTRY_PUSH_TRIES": "2", "TTC_REGISTRY_PUSH_WAIT": "0", **env}
            return subprocess.run([sys.executable, "-c", textwrap.dedent(script)], cwd=str(ROOT), env=e, capture_output=True, text=True)
        on_main = lambda: [json.loads(l)["trial_id"] for l in git(origin, "show", "main:research/trial_registry.jsonl").splitlines()]

        run1 = clone("run1"); (run1 / "data.txt").write_text("đang chạy dở\n")      # thư mục làm việc bẩn như lúc vòng học chạy
        r = cycle(run1)
        self.assertEqual(r.returncode, 7, r.stderr[-1500:])
        self.assertEqual(on_main(), ["T00001"])                                     # đăng ký đã nằm trên main dù vòng học hỏng
        self.assertIn("M data.txt", git(run1, "status", "--porcelain"))             # không đụng thư mục làm việc của vòng học
        shutil.rmtree(run1)                                                         # máy chạy bị thu hồi

        run2 = clone("run2")
        r = cycle(run2)
        self.assertEqual(json.loads(r.stdout.strip().splitlines()[-1])["n"], 2, r.stdout + r.stderr[-800:])   # không dùng lại T00001
        self.assertEqual(on_main(), ["T00001", "T00002"])
        # trong lúc vòng 2 chạy, workflow nhận dự báo đẩy một commit khác lên main; vòng 2 xong: commit, rebase, đẩy — như daily_cycle.yml
        git(seed, "pull", "-q", "origin", "main"); (seed / "other.txt").write_text("x"); git(seed, "add", "-A")
        git(seed, "commit", "-qm", "ledger: forecast #1"); git(seed, "push", "-q", "origin", "HEAD:main")
        (run2 / "data.txt").write_text("v2\n"); git(run2, "add", "-A"); git(run2, "commit", "-qm", "Vong hoc")
        git(run2, "pull", "-q", "--rebase", "origin", "main"); git(run2, "push", "-q", "origin", "HEAD:main")
        self.assertEqual(on_main(), ["T00001", "T00002"])                           # không nhân đôi dòng sau rebase
        self.assertEqual(laws_checks.check_trial_registry(run2), [])                # T00001 không có kết quả: hợp lệ, vẫn được đếm

        run3 = clone("run3")
        git(run3, "remote", "set-url", "origin", str(self.tmp / "khong-co-kho-nay.git"))
        r = cycle(run3)
        self.assertEqual(r.returncode, 1, r.stdout)                                 # không đẩy được → báo lỗi, backtest không chạy
        self.assertIn("không chạy backtest", r.stderr)
        self.assertEqual(on_main(), ["T00001", "T00002"])
        # hai vòng học chạy chồng nhau: main có dòng mà bản đang chạy không có → dừng, không ghi đè
        run4 = clone("run4"); run5 = clone("run5")
        self.assertEqual(cycle(run4).returncode, 7)
        r = cycle(run5)
        self.assertEqual(r.returncode, 1, r.stdout); self.assertIn("không phải tiền tố", r.stderr)
        self.assertEqual(on_main(), ["T00001", "T00002", "T00003"])

    def test_frozen_space_matches_engine_code(self):
        """Danh sách đóng băng trong config phải đúng bằng feature/mô hình engine đang có: thêm feature trong mã mà không sửa
        config (và ADR) thì test đỏ."""
        code, out, err = self._engine("""
            import json
            from engine.features import FEATURES
            from engine.research import MODELS
            from engine.config import CFG
            fs = CFG["research"]["frozen_space"]
            print(json.dumps([sorted(FEATURES) == sorted(fs["features"]), sorted(MODELS) == sorted(fs["models"])]))
        """)
        self.assertEqual(code, 0, err[-2000:])
        self.assertEqual(json.loads(out.strip().splitlines()[-1]), [True, True])

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
