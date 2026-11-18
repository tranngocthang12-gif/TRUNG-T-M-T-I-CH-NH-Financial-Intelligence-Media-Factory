"""Phân định dự báo Issue (tools/resolution_intake.py), chấm A–B (engine/ledger.issue_summary), sổ thử L-06 và Deflated Sharpe.
Mọi thứ chạy trong thư mục tạm và tiến trình con: không chạm tệp nào của kho.
"""
import contextlib, csv, io, json, math, os, pathlib, shutil, subprocess, sys, tempfile, textwrap, unittest
from datetime import datetime, timedelta
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import laws_checks, ledger_intake, resolution_intake  # noqa: E402
from tools.ledger_intake import control_b_hash  # noqa: E402

B_HASH = control_b_hash(ROOT / "governance" / "CONTROL_B_PROMPT.md")
Q1 = "Nợ nhóm 3-5 của VCB tại 31/12/2026 cao hơn tại 30/9/2026?"
Q2 = "NHNN đổi lãi suất tái cấp vốn trước 31/01/2027?"
Q3 = "NHNN công bố giảm trần lãi suất huy động trước 28/02/2027?"


def _just_after(created, seconds=60):
    """Giờ robot chạy trong test (TTC_INTAKE_NOW): mặc định một phút sau khi Issue mở, như khi workflow chạy thật."""
    return (datetime.fromisoformat(created.replace("Z", "+00:00")) + timedelta(seconds=seconds)).isoformat()


def _forecast(seat, question, p, resolve_at="2026-12-31", rule="comparison", author=None, source="https://www.nso.gov.vn — thông cáo"):
    f = {"seat": seat, "question": question, "resolution_source": source,
         "resolution_rule": rule, "resolve_at": resolve_at, "p": str(p), "base_rate": "0.5",
         "invalidation_conditions": "Nguồn đổi định nghĩa chỉ tiêu",
         "author_seat": author or ("Claude Project TTC" if seat == "A" else "Claude trần"), "model_cutoff": "2026-06"}
    if "info_lock_at" not in f:
        f["info_lock_at"] = f["resolve_at"]
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
        for g in ("CONTROL_B_PROMPT.md", "control_b_prompts.jsonl"):
            shutil.copy(ROOT / "governance" / g, self.tmp / "governance")
        shutil.copytree(ROOT / "tools", self.tmp / "tools", ignore=shutil.ignore_patterns("__pycache__"))
        for n, seat, q, p, ra, rule in [(101, "A", Q1, 0.30, "2026-12-31", "comparison"),
                                         (102, "B", Q1, 0.60, "2026-12-31", "comparison"),
                                         (103, "A", Q2, 0.70, "2027-01-31", "event_before_date"),
                                         (104, "B", Q2, 0.80, "2027-01-31", "event_before_date")]:
            self._fc(n, _forecast(seat, q, p, ra, rule))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run(self, script, number, body, created, **env):
        e = {**os.environ, "ISSUE_NUMBER": str(number), "ISSUE_CREATED_AT": created, "ISSUE_BODY": body,
             "TTC_INTAKE_NOW": _just_after(created), **env}
        r = subprocess.run([sys.executable, str(self.tmp / "tools" / script)], env=e, capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr

    def _fc(self, number, body, created="2026-11-17T02:00:00Z", expect=0, **env):
        c, o = self._run("ledger_intake.py", number, body, created, **env)
        self.assertEqual(c, expect, o)
        return o

    def _res(self, number, body, created, **env):
        return self._run("resolution_intake.py", number, body, created, **env)

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
        self.assertEqual(ab["fixed_sample"], {"n": 1, "resolved": 1, "void": 0, "open": 0, "a_correct": 1,
                                              "p_value_void_as_a_wrong": None, "p_value_void_as_a_right": None})   # chưa đủ 194: chưa kiểm định
        self.assertTrue(ab["verdict"].startswith("CHƯA ĐỦ MẪU (1/194"))

    def test_source_host_is_parsed_from_the_url_not_searched_in_the_string(self):
        """Vòng 6: dò tên miền trong cả chuỗi thì URL giả dạng lọt. Máy chủ phải tách bằng urllib; mọi đường dẫn phải thuộc
        tên miền đã hứa (nso.gov.vn)."""
        when = "2027-01-02T03:00:00Z"
        for i, bad in enumerate(("https://nso.gov.vn@evil.com/report", "https://evil.com/path/nso.gov.vn",
                                 "https://evil.com/?referer=nso.gov.vn", "https://evil.com#nso.gov.vn",
                                 "https://nso.gov.vn.evil.com/x", "https://evilnso.gov.vn/x", "https://evil.com\\@nso.gov.vn/x",
                                 "https://nso.gov.vn%2eevil.com/x", "https://nso.gov.vn:abc/x",
                                 "http://www.nso.gov.vn/thong-cao.pdf", "HTTP://www.nso.gov.vn/a",   # vòng 9: ADR đòi https://, http:// bị từ chối
                                 "https://www.nso.gov.vn/a và http://www.nso.gov.vn/b",
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
        same = _resolution("F-101", "NO", source="Thông cáo: https://data.NSO.gov.vn:443/cpi?thang=12 và https://www.nso.gov.vn/b")
        c, o = self._res(350, same, when)
        self.assertEqual(c, 3, o)                                                # chạy lại job: trả lại dấu nhận, không ghi trùng
        self.assertEqual(json.loads(o.strip().splitlines()[-1])["attest"], out["attest"])
        c, o = self._res(350, same, when, TTC_INTAKE_NOW="2027-02-01T00:00:00Z")
        self.assertEqual(c, 3, o)                                                # …kể cả một tháng sau: dấu nhận phân định không có hạn 6 giờ
        # chạy lại job chỉ trả dấu nhận khi dòng trong sổ đúng là kết quả của luật trên thân Issue lúc mở
        for other in (_resolution("F-101", "NO"), _resolution("F-101", "YES", source=same.split("### resolution_source\n\n")[1].split("\n\n")[0]),
                      _resolution("F-101", "NO", resolver="ChatGPT (OpenAI)", source="https://www.nso.gov.vn/b")):
            c, o = self._res(350, other, when)
            self.assertEqual(c, 2, o); self.assertIn("KHÔNG khớp", o); self.assertNotIn("attest", json.loads(o.strip().splitlines()[-1]))
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

    def test_forged_resolution_without_resolution_issue_is_rejected_and_not_scored(self):
        """Vòng 7: bỏ trường resolution_issue thì dòng phân định được coi là 'dòng engine' — né chạy lại luật, né đối chiếu
        Issue, né dấu nhận, mà engine vẫn chấm. Nay: dòng thiếu resolution_issue chỉ được trỏ tới dự báo của engine."""
        rp = self.tmp / "ledger" / "resolutions.jsonl"
        def write(rows):
            out, prev = [], "GENESIS"
            for r in rows:
                r = {**r, "prev_hash": prev}; r["hash"] = laws_checks.line_hash(r); prev = r["hash"]
                out.append(json.dumps(r, ensure_ascii=False, sort_keys=True))
            rp.write_text("\n".join(out) + "\n", encoding="utf-8")
            self.assertEqual(laws_checks.check_ledger_chain(self.tmp), [])       # hash chuỗi hợp lệ
            return laws_checks.check_ledger_rows(self.tmp)
        forged = [{"prediction_id": i, "resolved_at": "2026-12-11", "outcome": 1, "resolver": "Owner",
                   "resolution_issue_created_at": "2026-12-11T03:00:00Z", "resolution_source": "https://www.nso.gov.vn/x", "quote": "số liệu"}
                  for i in ("F-101", "F-102")]
        errs = write(forged)
        self.assertEqual(len([e for e in errs if "không có resolution_issue" in e]), 2, errs)
        self.assertTrue(any("không qua" in e or "resolution_issue" in e for e in laws_checks.run_all(self.tmp)))   # validate.py đỏ
        # kiểm toán GitHub: dòng này không mang số Issue nào để đối chiếu — vì thế việc chặn phải nằm ở validate (trên) và
        # ở engine (dưới): engine không dùng dòng thiếu resolution_issue để chấm dự báo Issue
        env = {**os.environ, "TTC_HOME": str(self.tmp), "PYTHONPATH": str(ROOT)}
        code = ("import json;from engine import ledger as L;P=L._load(L.PRED);R=L._load(L.RES);"
                "print(json.dumps(L.issue_summary(P,R)['by_seat']))")
        r = subprocess.run([sys.executable, "-c", code], cwd=str(ROOT), env=env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr[-1500:])
        seats = json.loads(r.stdout.strip().splitlines()[-1])
        self.assertEqual((seats["A"]["resolved"], seats["B"]["resolved"]), (0, 0))   # điểm A–B không đổi vì dòng giả
        # vòng 8 điểm 2: không còn loại dòng "của engine" nào được miễn — dòng thiếu resolution_issue trỏ tới mã P-… (có hay
        # không có dự báo P-… tương ứng trong sổ) cũng là lỗi; phía dự báo, dòng thiếu issue_number là lỗi dù mang mã gì
        self.assertTrue(any("không có resolution_issue" in e for e in write([{"prediction_id": "P-khong-co", "resolved_at": "2026-12-11", "outcome": 1}])))
        rp.unlink()
        pp = self.tmp / "ledger" / "predictions.jsonl"
        good_pred = pp.read_text(encoding="utf-8")
        rows = [json.loads(l) for l in good_pred.splitlines()]
        for bad in ({"id": "F-999", "seat": "A", "question": "Câu chèn?", "resolve_at": "2026-12-31", "p": 0.9},
                    {"id": "P-def456", "seat": "A", "question": "x", "resolution_rule": {"ticker": "VCB", "horizon": 20}},
                    {"id": "P-ghi789", "question": "thiếu luật chấm"}):
            row = {**bad, "prev_hash": rows[-1]["hash"]}; row["hash"] = laws_checks.line_hash(row)
            pp.write_text(good_pred + json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
            self.assertEqual(laws_checks.check_ledger_chain(self.tmp), [])
            self.assertTrue(any("không có issue_number" in e for e in laws_checks.check_ledger_rows(self.tmp)), bad)

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


class IntakeOrderTests(_Base):
    """Vòng 8 điểm 1: robot nhận dự báo và robot phân định chạy độc lập; thứ tự chúng GHI có thể khác thứ tự MỞ Issue.
    Ở mọi thứ tự, sổ sau khi ghi phải qua kiểm lại (validate) — không có trạng thái hỏng vĩnh viễn — và Issue bị từ chối
    được làm lại bằng một Issue mới, không sửa sổ."""
    R_AT = "2026-12-10T03:01:00Z"

    def _a(self):
        self._fc(301, _forecast("A", Q3, 0.4, "2027-02-28", "event_before_date"), created="2026-12-01T02:00:00Z")

    def _b(self, created, expect=0, **env):
        return self._fc(302, _forecast("B", Q3, 0.6, "2027-02-28", "event_before_date"), created=created, expect=expect, **env)

    def _clean(self):
        self.assertEqual(laws_checks.check_ledger_rows(self.tmp), [])            # đúng hàm mà tools/validate.py chạy
        self.assertEqual(laws_checks.check_ledger_chain(self.tmp), [])

    def _resolved(self):
        return [(r["prediction_id"], r["resolution_issue"]) for r in self._rows()]

    def _ids(self):
        return [r["id"] for r in self._rows("predictions.jsonl")]

    def test_forecast_opened_first_but_written_after_the_resolution(self):
        """Kịch bản 1 của bản chấm: B mở 10:00, Issue phân định mở 10:01, robot phân định chạy xong TRƯỚC robot nhận B.
        Bản trước: B vẫn được ghi → kiểm lại đòi hai dòng phân định mà sổ chỉ có một → đỏ mãi."""
        self._a()
        c, o = self._res(401, _resolution("F-301", "YES"), self.R_AT)
        self.assertEqual(c, 0, o)
        o = self._b("2026-12-10T03:00:00Z", expect=2)
        self.assertIn("trước khi robot ghi được dự báo này", o)
        self.assertEqual(self._ids()[-1], "F-301")                               # B không vào sổ
        self.assertEqual(self._resolved(), [("F-301", 401)])
        self._clean()
        self._b("2026-12-10T03:00:00Z", expect=2)                                # chạy lại job: vẫn từ chối, sổ không đổi
        self._clean()

    def test_same_issues_written_in_the_order_they_were_opened(self):
        self._a(); self._b("2026-12-10T03:00:00Z")
        c, o = self._res(401, _resolution("F-301", "YES"), self.R_AT)
        self.assertEqual(c, 0, o)
        self.assertEqual(self._resolved(), [("F-301", 401), ("F-302", 401)])     # phân định phủ cả B
        self._clean()

    def test_forecast_opened_after_the_resolution_issue_but_written_first(self):
        """Kịch bản 2 của bản chấm: Issue phân định mở 10:00, B mở 10:01, robot nhận B chạy xong TRƯỚC robot phân định.
        Bản trước: phân định ghi kết quả cho cả B (dự báo mở sau Issue phân định) → kiểm lại đỏ mãi."""
        self._a(); self._b(self.R_AT)
        c, o = self._res(401, _resolution("F-301", "YES"), "2026-12-10T03:00:00Z")
        self.assertEqual(c, 2, o)
        self.assertIn("F-302", o); self.assertIn("Mở Issue Resolution mới", o)
        self.assertEqual(self._rows(), [])                                       # không ghi gì: không cho B kết quả, cũng không bỏ sót B
        self._clean()
        self.assertEqual(self._res(401, _resolution("F-301", "YES"), "2026-12-10T03:00:00Z")[0], 2)   # chạy lại job: vẫn vậy
        # đường phục hồi: Issue Resolution MỚI (mở sau cả hai dự báo) phân định cả câu hỏi; sổ không phải sửa dòng nào
        c, o = self._res(402, _resolution("F-301", "YES"), "2026-12-10T03:05:00Z")
        self.assertEqual(c, 0, o)
        self.assertEqual(self._resolved(), [("F-301", 402), ("F-302", 402)])
        self._clean()

    def test_resolution_opened_first_and_written_first(self):
        self._a()
        c, o = self._res(401, _resolution("F-301", "YES"), "2026-12-10T03:00:00Z")
        self.assertEqual(c, 0, o)
        o = self._b(self.R_AT, expect=2)
        self.assertIn("đã được phân định", o)
        self.assertEqual(self._resolved(), [("F-301", 401)])
        self._clean()

    def test_forecast_and_resolution_opened_in_the_same_second(self):
        self._a(); self._b(self.R_AT)
        c, o = self._res(401, _resolution("F-301", "YES"), self.R_AT)
        self.assertEqual(c, 2, o); self.assertIn("cùng lúc hoặc sau", o)
        self.assertEqual(self._rows(), [])
        self._clean()

    def _append_pred(self, number, seat, created):
        """Ghi thẳng một dòng dự báo đúng khuôn, hash chuỗi hợp lệ — như bản trước vòng 8 đã ghi."""
        rows = self._rows("predictions.jsonl")
        data = ledger_intake.parse_issue_form(_forecast(seat, Q3, 0.6, "2027-02-28", "event_before_date"))
        row = ledger_intake.build_row(data, number, created, "", rows[-1]["hash"])
        with (self.tmp / "ledger" / "predictions.jsonl").open("a", encoding="utf-8") as f:
            f.write(ledger_intake.dumps(row) + "\n")
        return row

    def test_the_two_broken_states_fail_the_replay(self):
        """Hai trạng thái mà bản trước ghi ra được đều bị kiểm lại đánh đỏ. Vì robot nay tự chạy đúng phép kiểm đó trên
        trạng thái sau khi ghi (post_write_errors), nó không còn ghi ra được chúng."""
        self._a()
        self.assertEqual(self._res(401, _resolution("F-301", "YES"), self.R_AT)[0], 0)
        before = (self._rows("predictions.jsonl"), self._rows())
        self._append_pred(302, "B", "2026-12-10T03:00:00Z")                      # trạng thái 1: B mở trước, ghi sau phân định
        errs = laws_checks.check_ledger_rows(self.tmp)
        self.assertTrue(any("Issue #401" in e and "không khớp kết quả chạy lại" in e for e in errs), errs)
        self.assertEqual(laws_checks.check_ledger_chain(self.tmp), [])           # hash chuỗi không thấy gì
        new = ledger_intake.post_write_errors(before[0], before[1], self._rows("predictions.jsonl"), self._rows())
        self.assertTrue(new and all("Issue #401" in e for e in new), new)
        # trạng thái 2: phân định (mở 03:00) ghi kết quả cho cả B (mở 03:01)
        rp = self.tmp / "ledger" / "resolutions.jsonl"
        pp = self.tmp / "ledger" / "predictions.jsonl"
        pp.write_text("".join(ledger_intake.dumps(r) + "\n" for r in before[0]), encoding="utf-8"); rp.unlink()
        self._append_pred(302, "B", self.R_AT)
        self.assertEqual(self._res(402, _resolution("F-301", "YES"), "2026-12-10T03:05:00Z")[0], 0)
        self._clean()
        out, prev = [], "GENESIS"
        for r in self._rows():
            r = {k: v for k, v in r.items() if k not in ("hash", "prev_hash")}
            r.update(resolution_issue_created_at="2026-12-10T03:00:00Z", prev_hash=prev)
            r["hash"] = laws_checks.line_hash(r); prev = r["hash"]; out.append(ledger_intake.dumps(r))
        rp.write_text("\n".join(out) + "\n", encoding="utf-8")
        errs = laws_checks.check_ledger_rows(self.tmp)
        self.assertTrue(any("cùng lúc hoặc sau" in e for e in errs), errs)       # luật phân định
        self.assertTrue(any("F-302" in e and "đã được phân định" in e for e in errs), errs)   # luật nhận dự báo

    def _in_process(self, module, number, body, created):
        """Chạy main() của robot ngay trong tiến trình test, trỏ vào sổ của thư mục tạm."""
        env = {"ISSUE_NUMBER": str(number), "ISSUE_CREATED_AT": created, "ISSUE_BODY": body, "TTC_INTAKE_NOW": _just_after(created),
               "ISSUE_AUTHOR": "", "REPO_OWNER": ""}
        led = self.tmp / "ledger"
        buf = io.StringIO()
        with mock.patch.object(ledger_intake, "LEDGER", led / "predictions.jsonl"), mock.patch.object(ledger_intake, "RES", led / "resolutions.jsonl"), \
             mock.patch.object(resolution_intake, "PRED", led / "predictions.jsonl"), mock.patch.object(resolution_intake, "RES", led / "resolutions.jsonl"), \
             mock.patch.dict(os.environ, env), contextlib.redirect_stdout(buf):
            code = module.main()
        return code, buf.getvalue()

    def test_robot_refuses_to_write_a_state_the_replay_would_reject(self):
        """Lưới an toàn (lớp 2): giả sử luật lúc ghi có lỗ (ở đây: bị thay bằng bản luôn cho qua, như bản trước vòng 8).
        Robot vẫn không ghi, vì trạng thái sau khi ghi không qua kiểm lại. Kết quả là lỗi hệ thống (mã 1), sổ không đổi."""
        self._a()
        self.assertEqual(self._res(401, _resolution("F-301", "YES"), self.R_AT)[0], 0)
        snap = lambda: ((self.tmp / "ledger" / "predictions.jsonl").read_bytes(), (self.tmp / "ledger" / "resolutions.jsonl").read_bytes())
        before = snap()
        body = _forecast("B", Q3, 0.6, "2027-02-28", "event_before_date")
        code, out = self._in_process(ledger_intake, 302, body, "2026-12-10T03:00:00Z")
        self.assertEqual(code, 2, out)                                           # luật lúc ghi (lớp 1) từ chối
        with mock.patch.object(ledger_intake, "forecast_error", lambda *a, **k: (None, "")):
            code, out = self._in_process(ledger_intake, 302, body, "2026-12-10T03:00:00Z")
        self.assertEqual(code, 1, out)                                           # lớp 1 bị vô hiệu → lớp 2 chặn
        self.assertIn("KHÔNG ghi", out); self.assertIn("Issue #401", out)
        self.assertEqual(snap(), before)
        # phía phân định: luật lúc ghi "quên" kiểm dự báo mở sau Issue phân định
        pp, rp = self.tmp / "ledger" / "predictions.jsonl", self.tmp / "ledger" / "resolutions.jsonl"
        rp.unlink(); self._b(self.R_AT)
        before = pp.read_bytes()
        real = resolution_intake.decide
        def lax(data, number, created, author, pred_rows, res_rows, schema=None):
            msg, rows, note = real(data, number, "2026-12-10T03:05:00Z", author, pred_rows, res_rows, schema)
            return msg, [{**r, "resolution_issue_created_at": created} for r in rows], note
        with mock.patch.object(resolution_intake, "decide", lax):
            code, out = self._in_process(resolution_intake, 401, _resolution("F-301", "YES"), "2026-12-10T03:00:00Z")
        self.assertEqual(code, 1, out)
        self.assertIn("KHÔNG ghi", out); self.assertIn("F-302", out)
        self.assertFalse(rp.exists()); self.assertEqual(pp.read_bytes(), before)
        code, out = self._in_process(resolution_intake, 401, _resolution("F-301", "YES"), "2026-12-10T03:00:00Z")
        self.assertEqual(code, 2, out)                                           # luật thật: từ chối có lý do

    def test_rerun_only_attests_rows_the_robot_itself_wrote(self):
        """Chạy lại job của một Issue ("mã 3") trả lại dấu nhận để workflow đăng bổ sung. Nếu trả cho BẤT KỲ dòng nào mang số
        Issue đó thì có đường gian lận: mở một Issue bị từ chối, ghi tay một dòng mang số Issue ấy, rồi chạy lại job để robot
        đăng dấu nhận cho dòng ghi tay. Nay robot so dòng trong sổ với dòng nó dựng từ thân Issue lúc mở."""
        bad = _forecast("A", "Câu hỏi bị từ chối lúc mở vì resolve_at đã qua?", 0.5, resolve_at="2026-11-01")
        at = "2026-11-18T02:00:00Z"
        self._fc(320, bad, created=at, expect=2)
        rows = self._rows("predictions.jsonl")
        forged = ledger_intake.build_row(ledger_intake.parse_issue_form(_forecast("A", "Câu hỏi ghi tay sau khi biết thêm tin?", 0.9)),
                                         320, at, "", rows[-1]["hash"])
        with (self.tmp / "ledger" / "predictions.jsonl").open("a", encoding="utf-8") as f:
            f.write(ledger_intake.dumps(forged) + "\n")
        self.assertEqual(laws_checks.check_ledger_rows(self.tmp), [])            # dòng ghi tay đúng mọi luật nhận: kiểm lại không thấy
        o = self._fc(320, bad, created=at, expect=2)                             # chạy lại job với thân Issue gốc
        self.assertIn("KHÔNG khớp thân Issue", o)
        self.assertNotIn("attest", json.loads(o.strip().splitlines()[-1]))       # không có dấu nhận nào được trả ra để đăng
        ok = _forecast("A", "Câu hỏi ghi đúng đường về lãi suất điều hành?", 0.5)
        o1 = self._fc(321, ok, created=at)
        o3 = self._fc(321, ok, created=at, expect=3)                             # dòng do robot ghi: chạy lại thì trả đúng dấu nhận cũ
        self.assertEqual(json.loads(o3.strip().splitlines()[-1])["attest"], json.loads(o1.strip().splitlines()[-1])["attest"])
        self._fc(321, ok.replace("0.5", "0.6", 1), created=at, expect=2)         # thân khác (không thể xảy ra khi chạy lại thật) → không cấp

    def test_void_waits_for_resolve_at_like_any_resolution(self):
        """Vòng 9 điểm 2: VOID trước hạn là đường chọn mẫu (hủy câu hỏi khi triển vọng của một ghế xấu đi) → không còn ghi được.
        Tới hạn thì VOID ghi được như trước, khóa câu hỏi, và dự báo VOID không tính vào tiến độ."""
        early = "2026-12-01T03:00:00Z"                                           # trước resolve_at 31/12/2026 của câu hỏi 1
        for outcome, kw in (("NO", {}), ("VOID", {"void_reason": "Triển vọng xấu đi, muốn bỏ câu hỏi"}),
                            ("VOID", {"void_reason": "Dòng F-102 không có dấu nhận hợp lệ"})):
            c, o = self._res(420, _resolution("F-101", outcome, **kw), early)
            self.assertEqual(c, 2, o); self.assertIn("L-05", o)
        c, o = self._res(424, _resolution("F-103", "VOID", void_reason="Muốn bỏ câu hỏi sự kiện"), early)
        self.assertEqual(c, 2, o); self.assertIn("L-05", o)                      # câu hỏi event_before_date: trước hạn chỉ YES, không VOID
        self.assertEqual(self._rows(), [])
        due = "2026-12-31T03:00:00Z"
        c, o = self._res(421, _resolution("F-101", "VOID"), due)
        self.assertEqual(c, 2, o); self.assertIn("void_reason", o)               # hủy phải có lý do
        c, o = self._res(422, _resolution("F-101", "VOID", void_reason="Nguồn đã hứa không công bố chỉ tiêu này"), due)
        self.assertEqual(c, 0, o)
        self.assertEqual([(r["prediction_id"], r["outcome"]) for r in self._rows()], [("F-101", None), ("F-102", None)])
        self._clean()
        self.assertEqual(self._res(423, _resolution("F-101", "NO"), "2027-01-02T03:00:00Z")[0], 2)   # đã hủy thì không phân định lại
        sc = self._summary()
        self.assertEqual(sc["by_seat"]["A"]["void"], 1); self.assertEqual(sc["ab"]["disagreements_resolved"], 0)   # không có điểm
        self.assertEqual((sc["ab"]["pairs"], sc["ab"]["disagreements"], sc["ab"]["disagreements_void"]), (2, 1, 1))   # vẫn là một cặp bất đồng, ghi rõ là VOID
        self.assertEqual(sc["void"]["by_seat"]["A"], {"void": 1, "closed": 1, "rate": 1.0, "brier_void_worst": 0.49})   # A=0,3 → 0,7²
        self.assertEqual(sc["void"]["disagreements"], {"void": 1, "closed": 1, "rate": 1.0})
        # tiến độ (tools/validate.py) không đếm dự báo đã VOID: chạy validate trên một bản sao kho mang sổ này
        repo = self.tmp / "repo"
        shutil.copytree(ROOT, repo, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", "*.gz", "reports", "paper"))
        for n in ("predictions.jsonl", "resolutions.jsonl"):
            shutil.copy(self.tmp / "ledger" / n, repo / "ledger" / n)
        r = subprocess.run([sys.executable, str(repo / "tools" / "validate.py")], capture_output=True, text=True, cwd=str(repo))
        self.assertIn("dự báo A+B trong Ledger 2/60 (không tính 2 dự báo đã VOID)", r.stdout, r.stdout[-1500:] + r.stderr[-500:])
        self.assertNotIn("L-05", r.stdout, r.stdout[-1500:])                    # và sổ này qua toàn bộ kiểm lại của validate

    def test_rerun_cannot_attest_a_seat_b_forecast_the_robot_rejected(self):
        """Vòng 9 điểm 1, đúng kịch bản trong bản chấm: Issue ghế B có prompt_hash sai (đủ 64 ký tự hex) bị robot từ chối; ghi
        tay vào sổ một dòng đúng từng chữ như form; chạy lại job trong hạn dấu nhận. Bản trước: robot cấp dấu nhận (chỉ so nội
        dung), kiểm lại chỉ đòi 64 hex → dự báo B không qua prompt chuẩn thành hợp lệ. Nay: (1) kiểm lại dùng CÙNG luật với lúc
        nhận — prompt_hash phải là phiên bản có hiệu lực ngày Issue mở — nên validate đỏ ở dòng đó; (2) đường chạy lại job
        không cấp dấu nhận cho dòng không qua phép tự kiểm của đường ghi."""
        wrong = "ab" * 32
        at = "2026-11-18T02:00:00Z"
        body = _forecast("B", "Câu hỏi của ghế B với prompt khác prompt chuẩn?", 0.5).replace(B_HASH, wrong)
        o = self._fc(340, body, created=at, expect=2)
        self.assertIn("prompt_hash", o)
        rows = self._rows("predictions.jsonl")
        forged = ledger_intake.build_row(ledger_intake.parse_issue_form(body), 340, at, "", rows[-1]["hash"])
        with (self.tmp / "ledger" / "predictions.jsonl").open("a", encoding="utf-8") as f:
            f.write(ledger_intake.dumps(forged) + "\n")
        self.assertEqual(laws_checks.check_ledger_chain(self.tmp), [])           # hash chuỗi hợp lệ
        errs = laws_checks.check_ledger_rows(self.tmp)
        self.assertTrue(any("F-340" in e and "prompt_hash" in e for e in errs), errs)   # (1) validate đỏ, không cần tới dấu nhận
        o = self._fc(340, body, created=at, expect=2)                            # (2) chạy lại job, thân Issue gốc, còn trong hạn
        self.assertIn("không qua luật nhận", o)
        self.assertNotIn("attest", json.loads(o.strip().splitlines()[-1]))       # không có dấu nhận nào được trả ra để đăng
        # cùng đường đó với một dự báo bị từ chối vì lý do KHÁC (câu hỏi đã có kết quả trước khi robot ghi được): dòng ghi tay
        # qua được luật nhận của riêng nó, nhưng làm dòng phân định không còn phủ đủ câu hỏi → cũng không xin được dấu nhận
        self._a()
        self.assertEqual(self._res(401, _resolution("F-301", "YES"), self.R_AT)[0], 0)
        late_body = _forecast("B", Q3, 0.6, "2027-02-28", "event_before_date")
        self._fc(302, late_body, created="2026-12-10T03:00:00Z", expect=2)       # mở trước Issue phân định, robot chạy sau → từ chối
        self._append_pred(302, "B", "2026-12-10T03:00:00Z")
        o = self._fc(302, late_body, created="2026-12-10T03:00:00Z", expect=2)
        self.assertIn("không qua luật nhận", o); self.assertIn("Issue #401", o)
        self.assertNotIn("attest", json.loads(o.strip().splitlines()[-1]))
        # phía phân định: Issue phân định bị từ chối (chưa tới hạn), ghi tay đúng các dòng mà luật sẽ sinh ra, chạy lại job
        early = _resolution("F-101", "NO")
        self.assertEqual(self._res(431, early, "2026-12-15T03:00:00Z")[0], 2)
        res = self._rows()
        rows = resolution_intake.chain([{"prediction_id": i, "resolved_at": "2026-12-15", "outcome": 0, "resolution_issue": 431,
                                         "resolution_issue_created_at": "2026-12-15T03:00:00Z", "resolver": "Owner",
                                         "resolution_source": "https://www.nso.gov.vn/thong-cao.pdf", "quote": "Tỷ lệ nợ xấu 1,12% tại 31/12/2026"}
                                        for i in ("F-101", "F-102")], res[-1]["hash"])
        with (self.tmp / "ledger" / "resolutions.jsonl").open("a", encoding="utf-8") as f:
            f.write("".join(ledger_intake.dumps(r) + "\n" for r in rows))
        c, o = self._res(431, early, "2026-12-15T03:00:00Z")
        self.assertEqual(c, 2, o); self.assertNotIn("attest", json.loads(o.strip().splitlines()[-1]))

    def test_seat_b_prompt_version_is_pinned_by_the_day_the_issue_was_opened(self):
        """Phiên bản prompt chuẩn của ghế B ghim theo ngày (governance/control_b_prompts.jsonl). Đổi prompt qua ADR = thêm một
        dòng phiên bản: dự báo B cũ vẫn qua kiểm lại với hash cũ, dự báo B mới phải mang hash mới."""
        gov = self.tmp / "governance"
        f = ledger_intake
        self.assertEqual(f.control_b_versions(ROOT / "governance" / "control_b_prompts.jsonl"), [(f.date(2026, 10, 22), B_HASH)])
        self.assertEqual(laws_checks.check_control_b_prompts(ROOT), [])          # kho thật: tệp ghim khớp khối prompt hiện hành
        self.assertIn("check_control_b_prompts(root)", (ROOT / "tools" / "laws_checks.py").read_text(encoding="utf-8").split("def run_all")[1])
        from tools import ledger_audit
        self.assertIn("governance/control_b_prompts.jsonl", ledger_audit.APPEND_ONLY)   # chỉ ghi thêm: không đổi được phiên bản quá khứ
        self.assertEqual(laws_checks.check_ledger_rows(self.tmp), [])            # F-102, F-104 (ghế B, mở 17/11) hợp lệ
        new_prompt = "```text\nPrompt chuẩn bản 2\n```\n"
        new_hash = f.control_b_hash(self._write(gov / "CONTROL_B_PROMPT.md", new_prompt))
        # đổi khối prompt mà chưa thêm dòng phiên bản: validate đỏ, robot ngừng nhận ghế B (kể cả hash cũ lẫn hash mới)
        self.assertTrue(any("không trùng phiên bản mới nhất" in e for e in laws_checks.check_control_b_prompts(self.tmp)))
        q = "Câu hỏi ghế B sau khi đổi prompt?"
        self.assertIn("không trùng phiên bản mới nhất", self._fc(350, _forecast("B", q, 0.5), created="2026-12-02T02:00:00Z", expect=2))
        self.assertIn("không trùng phiên bản mới nhất", self._fc(350, _forecast("B", q, 0.5).replace(B_HASH, new_hash), created="2026-12-02T02:00:00Z", expect=2))
        # thêm dòng phiên bản có hiệu lực từ 01/12/2026
        with (gov / "control_b_prompts.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"sha256": new_hash, "valid_from": "2026-12-01"}) + "\n")
        self.assertEqual(laws_checks.check_control_b_prompts(self.tmp), [])
        self.assertEqual(laws_checks.check_ledger_rows(self.tmp), [])            # dự báo B cũ (17/11, hash cũ) vẫn qua kiểm lại
        self._fc(350, _forecast("B", q, 0.5), created="2026-12-02T02:00:00Z", expect=2)                          # hash cũ, ngày mới → từ chối
        self._fc(351, _forecast("B", q, 0.5).replace(B_HASH, new_hash), created="2026-12-02T02:00:00Z")          # hash mới, ngày mới → nhận
        o = self._fc(352, _forecast("B", "Câu hỏi mở ngày 30/11 với prompt mới?", 0.5).replace(B_HASH, new_hash), created="2026-11-30T02:00:00Z", expect=2)
        self.assertIn(B_HASH, o)                                                 # ngày 30/11 phiên bản cũ còn hiệu lực
        self.assertEqual(laws_checks.check_ledger_rows(self.tmp), [])
        self.assertEqual(f.control_b_hash_on(f.date(2026, 10, 21), f.control_b_versions(gov / "control_b_prompts.jsonl")), None)
        # tệp ghim hỏng → không đọc; ngày không tăng, hash trùng, trường lạ đều là lỗi
        good = (gov / "control_b_prompts.jsonl").read_text(encoding="utf-8")
        for bad in (good + '{"sha256": "%s", "valid_from": "2026-11-01"}\n' % ("cd" * 32), good + good.splitlines()[0] + "\n",
                    good + '{"sha256": "xyz", "valid_from": "2027-01-01"}\n', good + '{"sha256": "%s", "valid_from": "2027-01-01", "x": 1}\n' % ("cd" * 32),
                    good + "không phải json\n", ""):
            (gov / "control_b_prompts.jsonl").write_text(bad, encoding="utf-8")
            self.assertTrue(laws_checks.check_control_b_prompts(self.tmp), bad[-60:])
        (gov / "control_b_prompts.jsonl").unlink()
        self.assertTrue(laws_checks.check_control_b_prompts(self.tmp))           # thiếu tệp ghim
        self._fc(353, _forecast("B", "Câu hỏi khi thiếu tệp ghim?", 0.5).replace(B_HASH, new_hash), created="2026-12-03T02:00:00Z", expect=2)

    def _write(self, path, text):
        path.write_text(text, encoding="utf-8")
        return path

    def test_an_old_error_does_not_lock_new_issues(self):
        """Tự kiểm so với trạng thái trước khi ghi: lỗi cũ đang chờ xử lý không khóa Issue mới; lỗi MỚI thì chặn."""
        self._raw_prediction(id="F-150", issue_number=150, question="Câu hỏi cũ sai luật?", resolve_at="2026-11-17")
        self.assertTrue(laws_checks.check_ledger_rows(self.tmp))                 # sổ đang có một lỗi cũ
        self._fc(303, _forecast("A", "Câu hỏi mới hoàn toàn về tỷ giá trung tâm cuối năm 2026?", 0.5))
        self.assertEqual(self._ids()[-1], "F-303")

    def test_robot_does_not_write_when_the_attestation_could_not_be_in_time(self):
        """Lớp 3: dấu nhận phải đăng trong 6 giờ sau khi Issue mở và trước ngày resolve_at. Job chạy lại muộn, hay Issue mở
        sát nửa đêm, nếu vẫn ghi sẽ để lại một dòng không bao giờ có dấu nhận hợp lệ (kiểm toán đỏ mãi)."""
        body = _forecast("A", "Câu hỏi mới về CPI tháng 12/2026 từ 4,00% trở lên?", 0.5)
        at = "2026-11-18T02:00:00Z"
        o = self._fc(310, body, created=at, expect=2, TTC_INTAKE_NOW="2026-11-18T07:31:00Z")
        self.assertIn("quá 5 giờ 30 phút", o); self.assertIn("Mở Issue mới", o)
        self.assertNotIn("F-310", self._ids())
        self._fc(310, body, created=at, TTC_INTAKE_NOW="2026-11-18T07:29:00Z")    # còn trong hạn: ghi
        # mở 23:35 ngày 30/12 (giờ VN), resolve_at 31/12: dấu nhận có thể rơi sang ngày 31 → không ghi; mở 23:20 thì kịp
        eve = _forecast("B", "Câu hỏi sát ngày về tỷ giá cuối năm 2026?", 0.5)
        o = self._fc(311, eve, created="2026-12-30T16:35:00Z", expect=2)
        self.assertIn("quá sát ngày resolve_at", o)
        self._fc(312, eve, created="2026-12-30T16:20:00Z")
        # phân định không có hạn đó (dấu nhận của dòng phân định không bị đòi trong 6 giờ): job chạy lại muộn vẫn ghi được
        c, o = self._res(410, _resolution("F-101", "NO"), "2027-01-02T03:00:00Z", TTC_INTAKE_NOW="2027-01-09T09:00:00Z")
        self.assertEqual(c, 0, o)
        f = ledger_intake.write_deadline_error
        t = lambda x: ledger_intake.ts(x)
        self.assertIsNone(f("2026-11-18T02:00:00Z", t("2026-11-18T02:01:00Z"), "2026-12-31"))
        self.assertIsNone(f("2026-11-18T02:00:00Z", t("2026-11-18T07:30:00Z")))
        self.assertTrue(f("2026-11-18T02:00:00Z", t("2026-11-18T07:30:01Z")))
        self.assertTrue(f("2026-12-30T16:00:00Z", t("2026-12-30T16:30:00Z"), "2026-12-31"))    # 23:30 + 30 phút = 00:00 ngày 31
        self.assertIsNone(f("2026-12-30T16:00:00Z", t("2026-12-30T16:29:00Z"), "2026-12-31"))
        self.assertEqual(ledger_intake.ATTEST_WINDOW, laws_checks.ATTEST_WINDOW)
        from tools import ledger_audit
        self.assertIs(ledger_audit.ATTEST_WINDOW, laws_checks.ATTEST_WINDOW)     # bên ghi và bên kiểm dùng chung một hạn
        self.assertLess(ledger_intake.WRITE_MARGIN, ledger_intake.ATTEST_WINDOW)
        with mock.patch.dict(os.environ, {"TTC_INTAKE_NOW": ""}):
            self.assertLess(abs((ledger_intake.now_utc() - datetime.now(ledger_intake.timezone.utc)).total_seconds()), 5)   # mặc định: đồng hồ thật


class IntakeWorkflowRaceTests(unittest.TestCase):
    """Vòng 8 điểm 1, ở mức workflow: chạy ĐÚNG đoạn lệnh của bước "intake" trong hai tệp workflow trên một kho git thật, và
    cho hai robot xen kẽ ở đúng chỗ hiểm — robot 1 đã quyết định và commit, robot 2 đẩy lên main trước, rồi robot 1 mới đẩy.
    Vì vòng lặp của workflow là "lấy main mới nhất → quyết định → đẩy; đẩy không được thì làm lại TỪ ĐẦU", quyết định của
    robot 1 được tính lại trên trạng thái có dòng của robot 2."""
    def setUp(self):
        import yaml
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.origin = self.tmp / "origin.git"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(self.origin)], check=True, capture_output=True)
        seed = self._clone("seed")
        (seed / "contracts").mkdir(); (seed / "governance").mkdir(); (seed / "ledger").mkdir()
        for c in ("forecast_issue.schema.json", "resolution.schema.json"):
            shutil.copy(ROOT / "contracts" / c, seed / "contracts")
        for g in ("CONTROL_B_PROMPT.md", "control_b_prompts.jsonl"):
            shutil.copy(ROOT / "governance" / g, seed / "governance")
        shutil.copytree(ROOT / "tools", seed / "tools", ignore=shutil.ignore_patterns("__pycache__"))
        (seed / "ledger" / ".gitkeep").write_text("")
        self._git(seed, "add", "-A"); self._git(seed, "commit", "-qm", "seed"); self._git(seed, "push", "-q", "origin", "HEAD:main")
        self.bin = self.tmp / "bin"; self.bin.mkdir()
        (self.bin / "python").write_text(f'#!/bin/sh\nexec "{sys.executable}" "$@"\n'); (self.bin / "sleep").write_text("#!/bin/sh\nexit 0\n")
        for f in self.bin.iterdir():
            f.chmod(0o755)
        self.run_script = {}
        for name in ("ledger_intake.yml", "resolution_intake.yml"):
            d = yaml.safe_load((ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8"))
            self.run_script[name] = next(s for s in d["jobs"]["intake"]["steps"] if s.get("id") == "intake")["run"]
        self.n = 0

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _git(self, cwd, *a):
        r = subprocess.run(["git", "-C", str(cwd), "-c", "user.name=t", "-c", "user.email=t@t", *a], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, f"git {a}: {r.stderr}")
        return r.stdout.strip()

    def _clone(self, name):
        subprocess.run(["git", "clone", "-q", f"file://{self.origin}", str(self.tmp / name)], check=True, capture_output=True)
        return self.tmp / name

    def _env(self, number, body, created, out):
        return {**os.environ, "PATH": f"{self.bin}{os.pathsep}{os.environ['PATH']}", "GITHUB_OUTPUT": str(out), "ISSUE_NUMBER": str(number),
                "ISSUE_CREATED_AT": created, "ISSUE_BODY": body, "ISSUE_AUTHOR": "chu-kho", "REPO_OWNER": "chu-kho",
                "TTC_INTAKE_NOW": _just_after(created)}

    def _robot(self, wf, number, body, created, between_commit_and_push=None):
        """Một lần chạy của workflow `wf` cho một Issue, trong bản sao kho riêng (như một máy chạy riêng). Nếu có
        between_commit_and_push = (wf2, number2, body2, created2): robot thứ hai chạy trọn vẹn và đẩy lên main đúng lúc robot
        này đã commit mà chưa đẩy (qua hook pre-push, một lần). Trả về (mã, thông báo) của robot này [và của robot thứ hai]."""
        self.n += 1
        clone, out = self._clone(f"run{self.n}"), self.tmp / f"out{self.n}.txt"
        other_out = None
        if between_commit_and_push:
            wf2, n2, body2, created2 = between_commit_and_push
            self.n += 1
            clone2, other_out, flag = self._clone(f"run{self.n}"), self.tmp / f"out{self.n}.txt", self.tmp / f"flag{self.n}"
            env2 = self._env(n2, body2, created2, other_out)
            driver = self.tmp / f"other{self.n}.py"
            driver.write_text("import json, subprocess, sys\n"
                              f"e = json.load(open({str(self.tmp / f'env{self.n}.json')!r}, encoding='utf-8'))\n"
                              f"subprocess.run(['bash', '-c', {self.run_script[wf2]!r}], cwd={str(clone2)!r}, env=e, capture_output=True)\n",
                              encoding="utf-8")
            (self.tmp / f"env{self.n}.json").write_text(json.dumps({k: v for k, v in env2.items() if not k.startswith("GIT_")}), encoding="utf-8")
            hook = clone / ".git" / "hooks" / "pre-push"
            hook.write_text(f'#!/bin/sh\n[ -f "{flag}" ] && exit 0\ntouch "{flag}"\nunset $(git rev-parse --local-env-vars)\n'
                            f'"{sys.executable}" "{driver}"\nexit 0\n')
            hook.chmod(0o755)
        r = subprocess.run(["bash", "-c", self.run_script[wf]], cwd=str(clone), env=self._env(number, body, created, out),
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr[-1500:])
        def read(path):
            kv = dict(l.split("=", 1) for l in path.read_text(encoding="utf-8").splitlines() if "=" in l)
            return kv["code"], json.loads(kv["result"])["message"]
        return read(out) + (read(other_out) if other_out else ())

    def _main(self):
        """Trạng thái main sau cùng: (mã các dự báo, [(mã dự báo, số Issue phân định)], lỗi kiểm lại, tiêu đề các commit ghi sổ)."""
        self.n += 1
        c = self._clone(f"check{self.n}")
        rows = lambda n: [json.loads(l) for l in (c / "ledger" / n).read_text(encoding="utf-8").splitlines() if l.strip()] if (c / "ledger" / n).exists() else []
        errs = laws_checks.check_ledger_rows(c) + laws_checks.check_ledger_chain(c)
        return ([r["id"] for r in rows("predictions.jsonl")], [(r["prediction_id"], r["resolution_issue"]) for r in rows("resolutions.jsonl")],
                errs, self._git(c, "log", "--format=%s", "--reverse").splitlines()[1:])

    A = ("ledger_intake.yml", 301, _forecast("A", Q3, 0.4, "2027-02-28", "event_before_date"), "2026-12-01T02:00:00Z")
    B_BODY = _forecast("B", Q3, 0.6, "2027-02-28", "event_before_date")
    R_BODY = _resolution("F-301", "YES")

    def test_resolution_lands_between_the_forecast_robots_commit_and_push(self):
        """B mở 03:00, Issue phân định mở 03:01. Robot nhận B đã quyết định "ghi" và commit; robot phân định đẩy trước."""
        self.assertEqual(self._robot(*self.A)[0], "0")
        code, msg, code2, msg2 = self._robot("ledger_intake.yml", 302, self.B_BODY, "2026-12-10T03:00:00Z",
                                             between_commit_and_push=("resolution_intake.yml", 401, self.R_BODY, "2026-12-10T03:01:00Z"))
        self.assertEqual(code2, "0", msg2)                                       # robot phân định ghi kết quả cho A
        self.assertEqual(code, "2", msg); self.assertIn("trước khi robot ghi được dự báo này", msg)   # robot nhận B làm lại từ đầu → từ chối
        preds, res, errs, log = self._main()
        self.assertEqual((preds, res, errs), (["F-301"], [("F-301", 401)], []))
        self.assertEqual(log, ["ledger: forecast #301", "ledger: resolution #401"])   # commit của B không bao giờ lên main

    def test_forecast_lands_between_the_resolution_robots_commit_and_push(self):
        """Issue phân định mở 03:00, B mở 03:01. Robot phân định đã quyết định "ghi cho A" và commit; robot nhận B đẩy trước."""
        self.assertEqual(self._robot(*self.A)[0], "0")
        code, msg, code2, msg2 = self._robot("resolution_intake.yml", 401, self.R_BODY, "2026-12-10T03:00:00Z",
                                             between_commit_and_push=("ledger_intake.yml", 302, self.B_BODY, "2026-12-10T03:01:00Z"))
        self.assertEqual(code2, "0", msg2)                                       # B vào sổ (lúc đó chưa có kết quả nào)
        self.assertEqual(code, "2", msg); self.assertIn("F-302", msg); self.assertIn("Mở Issue Resolution mới", msg)
        preds, res, errs, log = self._main()
        self.assertEqual((preds, res, errs), (["F-301", "F-302"], [], []))       # không dòng phân định nào bị ghi nửa chừng
        code, msg = self._robot("resolution_intake.yml", 402, self.R_BODY, "2026-12-10T03:05:00Z")   # phục hồi: Issue mới, không sửa sổ
        self.assertEqual(code, "0", msg)
        preds, res, errs, log = self._main()
        self.assertEqual((res, errs), ([("F-301", 402), ("F-302", 402)], []))
        self.assertEqual(log, ["ledger: forecast #301", "ledger: forecast #302", "ledger: resolution #402"])

    def test_two_unrelated_forecasts_racing_both_land_with_a_valid_chain(self):
        other = _forecast("A", "Câu hỏi khác hẳn về tăng trưởng tín dụng cuối năm 2026?", 0.5)
        code, msg, code2, msg2 = self._robot(*self.A, between_commit_and_push=("ledger_intake.yml", 305, other, "2026-12-01T02:00:30Z"))
        self.assertEqual((code, code2), ("0", "0"), msg + msg2)
        preds, res, errs, log = self._main()
        self.assertEqual((preds, errs), (["F-305", "F-301"], []))                # robot 1 nối chuỗi lại sau dòng của robot 2


class EngineGateTests(_Base):
    """Vòng 8 điểm 2: dòng "trông như của engine" (mã P-…) không còn được miễn kiểm; đường ghi dự báo của engine đóng."""
    CLOSE = """
        import json
        import numpy as np, pandas as pd
        from engine import ledger
        idx = pd.bdate_range("2026-01-02", periods=60)
        close = pd.DataFrame({"AAA": np.linspace(10, 13, 60), "BBB": np.linspace(10, 9, 60)}, index=idx)
    """

    def _engine(self, code, home=None):
        env = {**os.environ, "TTC_HOME": str(home or self.tmp), "PYTHONPATH": str(ROOT)}
        r = subprocess.run([sys.executable, "-c", textwrap.dedent(self.CLOSE) + textwrap.dedent(code)], cwd=str(ROOT), env=env,
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr[-3000:])
        return json.loads(r.stdout.strip().splitlines()[-1])

    def _put(self, name, rows, base):
        """Ghi thêm các dòng tự tạo với hash chuỗi HỢP LỆ vào một sổ."""
        p = self.tmp / "ledger" / name
        old = [json.loads(l) for l in base.splitlines() if l.strip()]
        prev, out = (old[-1]["hash"] if old else "GENESIS"), []
        for r in rows:
            r = {**r, "prev_hash": prev}; r["hash"] = laws_checks.line_hash(r); prev = r["hash"]
            out.append(json.dumps(r, ensure_ascii=False, sort_keys=True))
        p.write_text(base + "".join(o + "\n" for o in out), encoding="utf-8")
        self.assertEqual(laws_checks.check_ledger_chain(self.tmp), [])           # hash chuỗi hợp lệ: không bắt được gì

    def _open_config(self, dst):
        import yaml
        cfg = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
        cfg["ledger"]["engine_forecasts"] = "open"
        pathlib.Path(dst).write_text(yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False), encoding="utf-8")

    def test_fake_engine_rows_fail_validate_and_cannot_break_the_cycle(self):
        good = (self.tmp / "ledger" / "predictions.jsonl").read_text(encoding="utf-8")
        fake = {"id": "P-fake", "resolution_rule": {"ticker": "VCB"}}             # đúng dòng trong bản chấm: thiếu horizon, created_at, probability
        self._put("predictions.jsonl", [fake], good)
        errs = laws_checks.check_ledger_rows(self.tmp)
        self.assertTrue(any("'P-fake'" in e and "không có issue_number" in e for e in errs), errs)
        self.assertTrue(any("'P-fake'" in e for e in laws_checks.run_all(self.tmp)))   # validate.py đỏ — daily_cycle.yml chạy nó TRƯỚC vòng học
        cycle = (ROOT / ".github" / "workflows" / "daily_cycle.yml").read_text(encoding="utf-8")
        self.assertLess(cycle.index("python tools/validate.py"), cycle.index("engine.run_cycle"))
        # kể cả khi validate bị bỏ qua: vòng học không vỡ (bản trước: KeyError 'horizon'), không chấm, không tính điểm dòng giả
        out = self._engine("""
            res = ledger.resolve(close, "2026-03-20")
            sc = ledger.scorecard("2026-03-20")
            print(json.dumps({"res": len(res), "resolved": sc["resolved"], "procedures": sc["procedures"], "total": sc["issue_forecasts"]["total"]}))
        """)
        self.assertEqual(out, {"res": 0, "resolved": 0, "procedures": {}, "total": 4})
        # biến thể trong bản chấm: dòng P- ĐỦ trường, đúng từng chữ như engine viết, kèm kết quả "engine tự chấm" tùy chọn
        full = self._engine("""
            row = ledger._engine_row({"procedure": "news@v1", "claim": "x", "ticker": "AAA", "horizon": 5, "probability": 0.9}, "2026-01-05", 0.5)
            print(json.dumps(row))
        """)
        self.assertRegex(full["id"], r"^P-[0-9a-f]{12}$")
        self._put("predictions.jsonl", [full], good)
        self._put("resolutions.jsonl", [{"prediction_id": full["id"], "resolved_at": "2026-01-20", "entry_date": "2026-01-06",
                                         "exit_date": "2026-01-13", "excess_return": 0.05, "outcome": 1}], "")
        errs = laws_checks.check_ledger_rows(self.tmp)
        self.assertTrue(any("không có issue_number" in e for e in errs) and any("không có resolution_issue" in e for e in errs), errs)
        out = self._engine("""
            sc = ledger.scorecard("2026-03-20")
            print(json.dumps({"n": len(ledger.resolve(close, "2026-03-20")), "resolved": sc["resolved"], "procedures": sc["procedures"]}))
        """)
        self.assertEqual(out, {"n": 0, "resolved": 0, "procedures": {}})         # không vào Brier, không vào phán quyết thủ tục

    def test_gate_is_closed_in_the_repo_and_flipping_the_config_is_not_enough(self):
        import yaml
        self.assertEqual(yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))["ledger"]["engine_forecasts"], "closed")
        self.assertEqual(laws_checks.check_engine_gate(ROOT), [])
        self.assertIn("check_engine_gate(root)", (ROOT / "tools" / "laws_checks.py").read_text(encoding="utf-8").split("def run_all")[1])
        self.assertEqual(laws_checks.check_engine_gate(self.tmp), [])            # không có config: đóng
        cfg = self.tmp / "config.yaml"
        for text, ok in (("ledger:\n  engine_forecasts: closed\n", True), ("ledger:\n  horizons: [5]\n", True),
                         ("ledger:\n  engine_forecasts: open\n", False), ("ledger:\n  engine_forecasts: true\n", False),
                         ("ledger:\n  engine_forecasts: CLOSED\n", False), ("ledger: [\n", False)):
            cfg.write_text(text, encoding="utf-8")
            self.assertEqual(laws_checks.check_engine_gate(self.tmp) == [], ok, text)
        # đổi config thành open cũng không làm dòng P- qua được kiểm lại: muốn mở phải sửa mã kiểm (ADR mới)
        self._open_config(cfg)
        self.assertTrue(any("engine_forecasts" in e for e in laws_checks.run_all(self.tmp)))
        good = (self.tmp / "ledger" / "predictions.jsonl").read_text(encoding="utf-8")
        full = self._engine("""
            row = ledger._engine_row({"procedure": "news@v1", "claim": "x", "ticker": "AAA", "horizon": 5, "probability": 0.9}, "2026-01-05", 0.5)
            print(json.dumps(row))
        """)
        self._put("predictions.jsonl", [full], good)
        self.assertTrue(any("không có issue_number" in e for e in laws_checks.check_ledger_rows(self.tmp)))

    def test_engine_does_not_write_while_the_gate_is_closed(self):
        home = self.tmp / "home"; (home / "ledger").mkdir(parents=True)
        code = """
            pred = {"procedure": "test", "claim": "x", "ticker": "AAA", "horizon": 5, "probability": 0.6, "requires_evidence": False}
            ok, rej = ledger.record([pred], "2026-01-05", ["AAA", "BBB"], set(), close)
            from engine import experts
            ex = experts.run("2026-01-05", close)
            print(json.dumps({"open": ledger.forecasts_open(), "ok": len(ok), "rej": [r["audit_errors"][0] for r in rej], "ex": ex,
                              "res": len(ledger.resolve(close, "2026-03-20"))}, ensure_ascii=False))
        """
        out = self._engine(code, home)                                          # config của kho: đóng
        self.assertEqual((out["open"], out["ok"], out["res"]), (False, 0, 0))
        self.assertIn("engine_forecasts", out["rej"][0])
        self.assertFalse(out["ex"]["ran"]); self.assertIn("engine_forecasts", out["ex"]["reasons"][0])
        self.assertEqual(list((home / "ledger").iterdir()), [])                  # không tệp nào được tạo trong sổ
        # mã của đường ghi vẫn chạy được khi cổng mở (thư mục tạm) — và dòng nó viết ra đúng hợp đồng đầy đủ
        self._open_config(home / "config.yaml")
        out = self._engine("""
            pred = {"procedure": "test", "claim": "x", "ticker": "AAA", "horizon": 5, "probability": 0.6, "requires_evidence": False}
            ok, rej = ledger.record([pred], "2026-01-05", ["AAA", "BBB"], set(), close)
            row = ledger._load(ledger.PRED)[0]
            bad = []
            for edit in ({"id": "P-fake"}, {"probability": 2}, {"probability": None}, {"created_at": "hôm qua"}, {"seat": "A"},
                         {"resolution_rule": {"ticker": "AAA"}}, {"resolution_rule": {**row["resolution_rule"], "horizon": 7}},
                         {"resolution_rule": {**row["resolution_rule"], "horizon": True}}, {"extra": 1}, {"claim": ""},
                         {"issue_number": 5}, {"evidence_refs": "x"}):
                bad.append(ledger.engine_row_error({**row, **edit}) is not None)
            missing = [ledger.engine_row_error({k: v for k, v in row.items() if k != key}) is not None for key in ledger.ENGINE_KEYS]
            print(json.dumps({"ok": len(ok), "err": ledger.engine_row_error(row), "bad": bad, "missing": missing,
                              "res": len(ledger.resolve(close, "2026-03-20"))}))
        """, home)
        self.assertEqual((out["ok"], out["err"], out["res"]), (1, None, 1))
        self.assertTrue(all(out["bad"]) and all(out["missing"]), out)


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
    _CAL = {"calendar_id": "RC-TEST", "domains": ["nso.gov.vn"], "info_lock_at": "2026-12-20",
            "evidence_url": "https://www.nso.gov.vn/lich-cong-bo",
            "quote": "Lịch công bố số tháng 11 là ngày 20/12/2026.",
            "recorder": "Owner", "recorded_at": "2026-11-01T00:00:00Z"}

    def _fake(self, n_pairs, a_right, start=1000, a_day="2026-11-17T02:00:00Z", b_day="2026-11-17T03:00:00Z"):
        """Ghi thẳng n cặp bất đồng đã phân định (A=0,7; B=0,3), A đúng ở a_right cặp đầu.
        Mỗi dòng có lịch công bố độc lập khớp info_lock_at, nên phép kiểm định nhị thức vẫn chạy khi thời điểm đã chứng minh."""
        preds, res = [], []
        for i in range(n_pairs):
            q = f"Câu hỏi giả lập số {i}?"
            for seat, p, num, day in (("A", 0.7, start + 2 * i, a_day), ("B", 0.3, start + 2 * i + 1, b_day)):
                preds.append({"id": f"F-{num}", "issue_number": num, "issue_created_at": day, "seat": seat, "question": q,
                              "resolve_at": "2026-12-31", "p": p, "base_rate": 0.5, "info_lock_at": "2026-12-20",
                              "resolution_source": "nso.gov.vn", "calendar_id": "RC-TEST",
                              "author_seat": "Claude Project TTC" if seat == "A" else "Claude trần"})
                res.append({"prediction_id": f"F-{num}", "outcome": 1 if i < a_right else 0, "resolution_issue": 90000 + start + i})
        return preds, res

    def _score(self, preds, res, calendar=None, pubs=None):
        env = {**os.environ, "TTC_HOME": str(self.tmp), "PYTHONPATH": str(ROOT)}
        payload = {"p": preds, "r": res, "c": self._CAL if calendar is None else calendar, "pubs": pubs or []}
        if isinstance(payload["c"], dict):
            payload["c"] = [payload["c"]]
        (self.tmp / "p.json").write_text(json.dumps(payload), encoding="utf-8")
        code = ("import json;from engine import ledger;d=json.load(open(r'%s'));"
                "print(json.dumps(ledger.issue_summary(d['p'],d['r'],d['pubs'],d['c']),ensure_ascii=False))"
                ) % (self.tmp / "p.json")
        r = subprocess.run([sys.executable, "-c", code], cwd=str(ROOT), env=env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr[-2000:])
        return json.loads(r.stdout.strip().splitlines()[-1])

    def test_fixed_sample_test_uses_only_first_194(self):
        """Phán quyết chốt ở 194 bất đồng đầu tiên: 109/194 (hai phía p≈0,098) → chưa thấy khác biệt, dù sau đó A đúng thêm 100 lần."""
        preds, res = self._fake(194, 109)
        ab = self._score(preds, res)["ab"]
        self.assertEqual(ab["fixed_sample"]["n"], 194)
        self.assertGreater(ab["fixed_sample"]["p_value_void_as_a_wrong"], 0.05)
        self.assertEqual(ab["fixed_sample"]["p_value_void_as_a_right"], ab["fixed_sample"]["p_value_void_as_a_wrong"])   # không có VOID: một phép thử
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

    def test_unproven_or_late_publication_blocks_verdict_and_keeps_the_sample(self):
        """Cặp trong mẫu 194 không đủ thời điểm thì không có phán quyết năng lực, và không được rút cặp sau vào thay."""
        preds, res = self._fake(194, 112)
        bare = self._score(preds, res, calendar=[])["ab"]
        self.assertEqual(bare["fixed_sample"]["n"], 194)
        self.assertTrue(bare["verdict"].startswith("CHƯA ĐỦ ĐIỀU KIỆN KẾT LUẬN"))
        self.assertFalse(bare["timing"]["sample_replaced"])
        self.assertEqual(bare["timing"]["reasons"].get("self_declared_lock"), 194)
        late = {"question": preds[0]["question"], "resolve_at": "2026-12-31", "published_at": "2026-11-16T00:00:00Z",
                "issue_created_at": "2026-11-18T00:00:00Z"}
        poisoned = self._score(preds, res, pubs=[late])["ab"]
        self.assertEqual(poisoned["fixed_sample"]["n"], 194)
        self.assertEqual(poisoned["fixed_sample"]["a_correct"], 112)
        self.assertTrue(poisoned["verdict"].startswith("CHƯA ĐỦ ĐIỀU KIỆN KẾT LUẬN"))
        self.assertNotIn("A HƠN B", poisoned["verdict"])
        self.assertEqual(poisoned["timing"]["reasons"].get("after_publication"), 1)
        more_p, more_r = self._fake(30, 30, start=8000)
        still = self._score(preds + more_p, res + more_r, pubs=[late])["ab"]
        self.assertEqual(still["fixed_sample"]["n"], 194)
        self.assertEqual(still["fixed_sample"]["a_correct"], poisoned["fixed_sample"]["a_correct"])
        self.assertTrue(still["verdict"].startswith("CHƯA ĐỦ ĐIỀU KIỆN KẾT LUẬN"))

    def _void(self, res, pairs, start=1000):
        """Đổi kết quả của các cặp (theo số thứ tự cặp trong _fake) thành VOID cho cả A và B."""
        ids = {f"F-{start + 2 * i + d}" for i in pairs for d in (0, 1)}
        return [{**r, "outcome": None, "void": "hủy"} if r["prediction_id"] in ids else r for r in res]

    def test_void_pairs_count_against_whichever_verdict_is_being_tested(self):
        """Vòng 9 điểm 2: bỏ cặp VOID khỏi mẫu rồi lấy cặp đến sau bù vào là đường chọn mẫu — hủy đúng những câu hỏi A sắp sai
        là 'A hơn B' tự xuất hiện. Quy định trước: mẫu chốt là 194 cặp bất đồng đầu tiên theo thứ tự GHI dự báo (cặp VOID
        vẫn giữ chỗ), và mỗi cặp VOID tính theo hướng bất lợi cho kết luận đang xét."""
        # Thật ra A đúng 100/194 (không khác tung đồng xu). Hủy 30 cặp A sai, rồi ghi thêm 30 cặp A đúng.
        preds, res = self._fake(194, 100)
        more_p, more_r = self._fake(30, 30, start=5000)
        res_sel = self._void(res, range(100, 130))
        ab = self._score(preds + more_p, res_sel + more_r)["ab"]
        self.assertEqual(ab["fixed_sample"]["n"], 194)
        self.assertEqual((ab["fixed_sample"]["resolved"], ab["fixed_sample"]["void"], ab["fixed_sample"]["a_correct"]), (164, 30, 100))
        self.assertEqual(ab["verdict"], "CHƯA THẤY KHÁC BIỆT A–B")               # cặp đến sau không được bù vào chỗ cặp VOID
        self.assertEqual((ab["disagreements_resolved"], ab["disagreements_void"], ab["a_correct"]), (194, 30, 130))   # số chạy vẫn báo đủ
        self.assertIn("void_rule", ab)
        from engine import ledger
        self.assertLess(ledger._binom_two_sided(130, 194), 0.05)                 # cách "bỏ VOID, lấy cặp sau" sẽ cho A hơn B
        # Chiều ngược lại: A thật sự đúng 112/194 (A hơn B). Hủy 40 cặp A đúng không tạo ra được 'B hơn A', chỉ làm mất kết luận.
        preds, res = self._fake(194, 112)
        ab = self._score(preds, self._void(res, range(0, 40)))["ab"]
        self.assertEqual((ab["fixed_sample"]["a_correct"], ab["fixed_sample"]["void"]), (72, 40))
        self.assertEqual(ab["verdict"], "CHƯA THẤY KHÁC BIỆT A–B")
        self.assertLess(ledger._binom_two_sided(72, 154), 0.5)                   # (bỏ VOID khỏi mẫu thì A chỉ còn đúng 72/154)
        # Kết quả đủ mạnh vẫn đứng được khi có ít VOID; và p-value của hai phép thử được ghi riêng
        preds, res = self._fake(194, 130)
        ab = self._score(preds, self._void(res, range(0, 5)))["ab"]
        self.assertEqual(ab["verdict"], "A HƠN B CÓ Ý NGHĨA")
        self.assertEqual((ab["fixed_sample"]["a_correct"], ab["fixed_sample"]["void"]), (125, 5))
        self.assertAlmostEqual(ab["fixed_sample"]["p_value_void_as_a_wrong"], round(ledger._binom_two_sided(125, 194), 4))
        self.assertAlmostEqual(ab["fixed_sample"]["p_value_void_as_a_right"], round(ledger._binom_two_sided(130, 194), 4))
        preds, res = self._fake(194, 60)
        ab = self._score(preds, self._void(res, range(190, 194)))["ab"]
        self.assertEqual(ab["verdict"], "B HƠN A CÓ Ý NGHĨA")                    # A đúng 60, VOID 4 (tính là A đúng): 64/194 vẫn kém rõ
        # chưa ghi đủ 194 cặp thì chưa kiểm định; cặp VOID có được đếm vào số đã đóng
        preds, res = self._fake(100, 60)
        out = self._score(preds, self._void(res, range(0, 10)))
        self.assertTrue(out["ab"]["verdict"].startswith("CHƯA ĐỦ MẪU (100/194"))
        self.assertEqual(out["ab"]["fixed_sample"]["p_value_void_as_a_wrong"], None)
        # báo cáo tỷ lệ hủy theo ghế, theo cặp, theo cặp bất đồng
        self.assertEqual({k: out["void"]["by_seat"]["A"][k] for k in ("void", "closed", "rate")}, {"void": 10, "closed": 100, "rate": 0.1})
        self.assertEqual(out["void"]["pairs"], {"void": 10, "closed": 100, "rate": 0.1})
        self.assertEqual(out["void"]["disagreements"], {"void": 10, "closed": 100, "rate": 0.1})
        self.assertEqual(out["ab"]["pairs"], 100)                                # cặp VOID vẫn là cặp, vẫn tính vào tỷ lệ bất đồng
        report = (ROOT / "engine" / "run_cycle.py").read_text(encoding="utf-8")
        self.assertIn("VOID {disagreements_void}", report); self.assertIn('["void"]["by_seat"]', report)   # báo cáo vòng học in các số này

    def test_sample_is_fixed_when_forecasts_are_recorded_not_when_they_are_resolved(self):
        """Vòng 9 điểm 2 (tự rà): nếu mẫu là "194 cặp được phân định đầu tiên" thì không cần VOID cũng chọn được mẫu — cứ để
        yên không phân định những câu hỏi A sai, cặp đến sau sẽ bù vào. Mẫu chốt vì thế là 194 cặp bất đồng đầu tiên theo
        thứ tự GHI dự báo, và chỉ ra phán quyết khi cả 194 cặp đó đã đóng."""
        from engine import ledger
        preds, res = self._fake(194, 100)                                         # thật ra A đúng 100/194
        more_p, more_r = self._fake(30, 30, start=5000)                           # 30 cặp ghi SAU, A đúng cả
        skipped = {f"F-{1000 + 2 * i + d}" for i in range(100, 130) for d in (0, 1)}   # 30 cặp A sai: bỏ mặc, không phân định
        ab = self._score(preds + more_p, [r for r in res if r["prediction_id"] not in skipped] + more_r)["ab"]
        self.assertEqual(ab["disagreements_resolved"], 194)                       # đã có 194 cặp bất đồng được phân định, A đúng 130…
        self.assertEqual(ab["a_correct"], 130)
        self.assertLess(ledger._binom_two_sided(130, 194), 0.05)                  # …và "194 cặp phân định đầu tiên" sẽ cho A hơn B
        self.assertEqual(ab["fixed_sample"], {"n": 194, "resolved": 164, "void": 0, "open": 30, "a_correct": 100,
                                              "p_value_void_as_a_wrong": None, "p_value_void_as_a_right": None})
        self.assertTrue(ab["verdict"].startswith("CHƯA ĐỦ MẪU (164/194"), ab["verdict"])   # 30 cặp trong mẫu còn mở: chưa có phán quyết
        # Thứ tự phân định không đổi được mẫu: phân định các cặp ghi sau TRƯỚC, kết quả vẫn như khi phân định theo thứ tự ghi.
        full = self._score(preds + more_p, more_r + res)["ab"]
        self.assertEqual(full["fixed_sample"], self._score(preds + more_p, res + more_r)["ab"]["fixed_sample"])
        self.assertEqual((full["fixed_sample"]["a_correct"], full["fixed_sample"]["open"]), (100, 0))
        self.assertEqual(full["verdict"], "CHƯA THẤY KHÁC BIỆT A–B")

    def test_event_before_date_pairs_are_outside_the_ab_test(self):
        """ADR-0002: ghế A được tìm web, ghế B thì không. Với câu hỏi event_before_date, sự kiện có thể đã xảy ra trước khi
        hỏi, nên bất đồng đo việc tìm web chứ không đo thư viện: các cặp đó không vào mẫu chốt, nhưng vẫn là cặp, vẫn vào tỷ
        lệ bất đồng và được báo riêng."""
        preds, res = self._fake(194, 194)                                         # 194 cặp A đúng cả, nhưng toàn event_before_date
        for p in preds:
            p["resolution_rule"] = "event_before_date"
        ab = self._score(preds, res)["ab"]
        self.assertEqual((ab["pairs"], ab["disagreements"], ab["disagreements_out_of_scope"]), (194, 0, 194))
        self.assertEqual(ab["disagreement_rate"], 1.0)
        self.assertEqual(ab["disagreements_all"], 194)                         # ADR-0007: mẫu số của tỷ lệ, in rõ
        self.assertEqual((ab["fixed_sample"]["n"], ab["disagreements_resolved"]), (0, 0))
        self.assertTrue(ab["verdict"].startswith("CHƯA ĐỦ MẪU (0/194"), ab["verdict"])
        more_p, more_r = self._fake(194, 100, start=5000)                         # 194 cặp comparison: chỉ chúng vào mẫu
        ab = self._score(preds + more_p, res + more_r)["ab"]
        self.assertEqual((ab["fixed_sample"]["n"], ab["fixed_sample"]["a_correct"]), (194, 100))
        self.assertEqual(ab["verdict"], "CHƯA THẤY KHÁC BIỆT A–B")
        self.assertEqual(ab["disagreements_all"], ab["disagreements"] + ab["disagreements_out_of_scope"])
        self.assertEqual(ab["disagreement_rate"], round(ab["disagreements_all"] / ab["pairs"], 3))
        report = (ROOT / "engine" / "run_cycle.py").read_text(encoding="utf-8")
        self.assertIn("{disagreements_out_of_scope}", report)

    def test_brier_with_voids_counted_as_wrong_is_reported_per_seat(self):
        """ADR-0004: Brier theo ghế chỉ tính dự báo YES/NO, nên hủy có chọn lọc làm đẹp được nó. In thêm Brier trong đó mỗi
        dự báo VOID tính như kết quả ngược phía nó đứng."""
        preds, res = self._fake(4, 4)                                             # A=0,7 đúng cả 4; B=0,3 sai cả 4
        res = self._void(res, [3])                                                # cặp thứ tư bị hủy
        v = self._score(preds, res)["void"]["by_seat"]
        self.assertAlmostEqual(v["A"]["brier_void_worst"], round((3 * 0.3 ** 2 + 0.7 ** 2) / 4, 4))
        self.assertAlmostEqual(v["B"]["brier_void_worst"], round((3 * 0.7 ** 2 + 0.7 ** 2) / 4, 4))
        self.assertEqual((v["A"]["void"], v["A"]["closed"]), (1, 4))
        report = (ROOT / "engine" / "run_cycle.py").read_text(encoding="utf-8")
        self.assertIn("brier_void_worst", report)

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


def _config_without_pin(dst):
    """config.yaml của kho thật nhưng bỏ research.legacy_pin (ghim 210 kết quả của kho thật không áp cho kho giả lập)."""
    import yaml
    cfg = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    cfg["research"].pop("legacy_pin", None)
    pathlib.Path(dst).write_text(yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False), encoding="utf-8")


class TrialRegistryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        (self.tmp / "research").mkdir()
        _config_without_pin(self.tmp / "config.yaml")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _engine(self, code):
        env = {**os.environ, "TTC_HOME": str(self.tmp), "PYTHONPATH": str(ROOT)}
        r = subprocess.run([sys.executable, "-c", textwrap.dedent(code)], cwd=str(ROOT), env=env,
                           capture_output=True, text=True)
        return r.returncode, r.stdout, r.stderr

    LEGACY = ("trial_id,cycle_date,method,spec_id,features,model,ic_mean,ic_t,net_ann,fold_pos,threshold,status,regimes\n"
              'T00001,2026-09-28,mutate_best,M-a,lowvol_60;rev_5,ridge,-0.0146496299511184,-0.5685272773787465,-0.1493369139037447,'
              '0.4210526315789473,3.0,REJECTED,"{""UP"": {""n"": 5, ""t"": -1.2116751096431657}}"\n'
              'T00002,2026-09-28,random_subset,M-b,mom_60,gbm,0.01,0.3,-0.02,0.5,3.1,REJECTED,{}\n')

    def test_register_before_run_and_check(self):
        """L-06 sau vòng 7: sổ mở đầu bằng dòng neo lịch sử; kết quả cũ không sửa được; mọi kết quả mới phải có đăng ký."""
        tp = self.tmp / "research" / "trials.csv"
        tp.write_text(self.LEGACY, encoding="utf-8")
        self.assertEqual(laws_checks.check_trial_registry(self.tmp), [])        # chưa có sổ: hai kết quả lịch sử
        code, out, err = self._engine("""
            import json
            import pandas as pd
            from engine import research
            from engine.run_cycle import load_ledger
            spec = {"features": ["mom_60", "lowvol_20"], "model": "ridge"}
            df = load_ledger()
            n = research.next_trial_number(df)
            h1 = research.register_trial(f"T{n:05d}", "2026-11-20", "random_subset", spec, research.threshold(n))
            n2 = research.next_trial_number(df)            # T00003 đăng ký nhưng chưa có kết quả → vẫn được đếm
            h2 = research.register_trial(f"T{n2:05d}", "2026-11-20", "random_subset", spec, research.threshold(n2))
            def refused(tid, sp):
                try:
                    research.register_trial(tid, "2026-11-20", "random_subset", sp, 3.0); return False
                except RuntimeError:
                    return True
            row = {"trial_id": f"T{n2:05d}", "cycle_date": "2026-11-20", "method": "random_subset", "spec_id": research.spec_id(spec),
                   "features": "mom_60;lowvol_20", "model": "ridge", "ic_mean": 0.012345678901234567, "ic_t": 1.5, "net_ann": -0.01,
                   "fold_pos": 0.5, "threshold": research.threshold(n2), "status": "REJECTED", "regimes": json.dumps({"UP": {"n": 3}}),
                   "sharpe": 0.1, "sharpe_ann": 1.2, "dsr": float("nan"), "registry_hash": h2}
            research.append_trial_results([row])
            df2 = load_ledger()
            print(json.dumps({"n": n, "n2": n2, "dup": refused(f"T{n:05d}", spec),
                              "new_feature": refused("T00009", {"features": ["mom_60", "feature_moi"], "model": "ridge"}),
                              "new_model": refused("T00010", {"features": ["mom_60"], "model": "transformer"}),
                              "total": research.total_trials(df2), "next": research.next_trial_number(df2),
                              "abandoned": research.abandoned_trials(df2), "rows": len(df2), "cols": list(df2.columns)}))
        """)
        self.assertEqual(code, 0, err[-2500:])
        d = json.loads(out.strip().splitlines()[-1])
        self.assertEqual((d["n"], d["n2"], d["dup"]), (3, 4, True))              # dòng neo không bị đếm là một lần thử
        self.assertTrue(d["new_feature"] and d["new_model"])                    # ngoài không gian đóng băng → engine từ chối
        # vòng 7 điểm 3: tổng số lần thử gồm cả lần đăng ký rồi bỏ dở (T00003): 2 lịch sử + 1 bỏ dở + 1 có kết quả = 4
        self.assertEqual((d["total"], d["next"], d["abandoned"], d["rows"]), (4, 5, ["T00003"], 3))
        self.assertIn("n_total = research.total_trials(ledger_df)", (ROOT / "engine" / "run_cycle.py").read_text(encoding="utf-8"))
        self.assertEqual(d["cols"][-4:], ["sharpe", "sharpe_ann", "dsr", "registry_hash"])
        text = tp.read_text(encoding="utf-8")
        old_lines, new_lines = self.LEGACY.strip().split("\n"), text.strip().split("\n")
        self.assertEqual(new_lines[0], old_lines[0] + ",sharpe,sharpe_ann,dsr,registry_hash")
        self.assertEqual(new_lines[1:3], [l + ",,,," for l in old_lines[1:]])    # dòng cũ giữ nguyên từng ký tự, chỉ thêm ô rỗng
        reg = self.tmp / "research" / "trial_registry.jsonl"
        rows = [json.loads(l) for l in reg.read_text(encoding="utf-8").splitlines()]
        self.assertEqual([r["trial_id"] for r in rows], ["LEGACY-ANCHOR", "T00003", "T00004"])
        self.assertEqual((rows[0]["kind"], rows[0]["results"], rows[0]["last_trial_id"]), ("legacy_anchor", 2, "T00002"))
        self.assertEqual(laws_checks.check_trial_registry(self.tmp), [])        # T00003 không có kết quả: hợp lệ, vẫn được đếm
        good_t, good_r = text, reg.read_text(encoding="utf-8")
        def trials(t):
            tp.write_text(t, encoding="utf-8"); e = laws_checks.check_trial_registry(self.tmp); tp.write_text(good_t, encoding="utf-8"); return e
        # vòng 7 điểm 2: sửa, xóa, chèn kết quả lịch sử → lệch sha256 đã neo
        self.assertTrue(any("lịch sử" in e for e in trials(good_t.replace("-0.0146496299511184", "0.0946496299511184"))))
        self.assertTrue(any("lịch sử" in e for e in trials(good_t.replace("T00002,2026-09-28,random_subset,M-b", "T00002,2026-09-28,random_subset,M-z"))))
        self.assertTrue(any("lịch sử" in e for e in trials("\n".join([new_lines[0], new_lines[2], new_lines[1], new_lines[3]]) + "\n")))
        self.assertTrue(any("bị xóa" in e or "lịch sử" in e for e in trials("\n".join(new_lines[:2]) + "\n")))
        # kết quả mới không có đăng ký (registry_hash rỗng không còn là lý do miễn kiểm), hai kết quả một mã, lệch spec/ngưỡng/hash
        self.assertTrue(any("T00009" in e and "không có dòng đăng ký" in e for e in trials(good_t + "T00009,2026-11-20,x,M-x,mom_60,ridge,0,0,0,0,3.7,REJECTED,{},,,,\n")))
        self.assertTrue(any("hai kết quả" in e for e in trials(good_t + new_lines[3] + "\n")))
        self.assertTrue(any("spec_id lệch" in e for e in trials(good_t.replace(new_lines[3], new_lines[3].replace(",M-", ",M-zz", 1)))))
        self.assertTrue(any("registry_hash" in e for e in trials(good_t.replace(rows[2]["hash"], "0" * 64))))
        def registry(t):
            reg.write_text(t, encoding="utf-8"); e = laws_checks.check_trial_registry(self.tmp); reg.write_text(good_r, encoding="utf-8"); return e
        self.assertTrue(any("hash" in e for e in registry(good_r.replace("random_subset", "cross_family"))))     # sửa sổ bị bắt
        def chain(objs):
            out, prev = [], "GENESIS"
            for o in objs:
                o = {k: v for k, v in o.items() if k not in ("hash", "prev_hash")}; o["prev_hash"] = prev
                o["hash"] = laws_checks.line_hash(o); prev = o["hash"]; out.append(json.dumps(o, ensure_ascii=False, sort_keys=True))
            return "\n".join(out) + "\n"
        # các sổ viết tay có hash hợp lệ: bỏ dòng neo; neo khai ít kết quả hơn; dòng ngoài không gian đóng băng; mã không tăng dần
        self.assertTrue(any("dòng neo" in e for e in registry(chain(rows[1:]))))
        self.assertTrue(registry(chain([{**rows[0], "results": 1, "last_trial_id": "T00001"}] + rows[1:])))
        self.assertTrue(any("đóng băng" in e for e in registry(chain(rows + [{**rows[2], "trial_id": "T00005", "features": "mom_60;feature_moi"}]))))
        self.assertTrue(any("tăng dần" in e for e in registry(chain([rows[0], rows[2], rows[1]]))))
        self.assertTrue(any("hơn một dòng neo" in e for e in registry(chain(rows + [rows[0]]))))
        reg.unlink()                                                             # mất sổ: kết quả mang registry_hash/sharpe không còn chỗ dựa
        self.assertTrue(any("phải để trống bốn cột" in e for e in laws_checks.check_trial_registry(self.tmp)))

    def test_trials_csv_has_one_fixed_shape(self):
        """Vòng 8 điểm 3: thêm cột lạ và ô rỗng vào trials.csv không đổi sha256 của 13 cột gốc, không đổi ô cũ nào, không
        thêm kết quả — CI không báo, nhưng lần ghi kết quả kế tiếp của vòng học hỏng. Nay: tệp chỉ có một khuôn."""
        from tools import ledger_audit
        tp = self.tmp / "research" / "trials.csv"
        def check(t):
            tp.write_bytes(t.encode("utf-8")); return laws_checks.check_trial_registry(self.tmp)
        L = self.LEGACY
        lines = L.strip().split("\n")
        self.assertEqual(check(L), [])
        FULL = lines[0] + ",sharpe,sharpe_ann,dsr,registry_hash\n" + "".join(l + ",,,,\n" for l in lines[1:])
        self.assertEqual(check(FULL), [])                                        # đúng 17 cột sau lần ghi đầu của v3.0.2
        note = lines[0] + ",note\n" + "".join(l + ",\n" for l in lines[1:])      # đúng kịch bản trong bản chấm
        self.assertEqual(laws_checks.trials_digest(laws_checks.read_trials(note)[1]), laws_checks.trials_digest(laws_checks.read_trials(L)[1]))
        self.assertTrue(any("tiêu đề" in e for e in check(note)))
        self.assertTrue(any("tiêu đề" in e and "bị đổi" in e for e in ledger_audit.trials_rows_errors(L.encode(), note.encode())))
        cols = lines[0].split(",")
        swapped = ",".join(cols[:6] + [cols[7], cols[6]] + cols[8:]) + "\n" + "\n".join(lines[1:]) + "\n"
        for bad, why in ((swapped, "tiêu đề"), (L.replace("trial_id", "Trial_ID", 1), "tiêu đề"), (L.replace(",regimes\n", "\n", 1), "tiêu đề"),
                         (lines[0] + ",sharpe\n" + "".join(l + ",\n" for l in lines[1:]), "tiêu đề"),
                         (FULL.replace(",sharpe,sharpe_ann,", ",sharpe_ann,sharpe,"), "tiêu đề"),
                         ("\ufeff" + L, "tiêu đề"), (L + "\n", "số ô"), (L.replace("REJECTED,{}\n", "REJECTED\n"), "số ô"),
                         (L.replace("REJECTED,{}\n", "REJECTED,{},\n"), "số ô"), (L.replace("\n", "\r\n"), "dạng chuẩn"),
                         (L.rstrip("\n"), "dạng chuẩn"), (L.replace(",ridge,", ',"ridge",', 1), "dạng chuẩn"),
                         (L.replace("T00002,", " T00002,", 1).replace(",gbm,", ', "gbm",', 1), "dạng chuẩn")):
            errs = check(bad)
            self.assertTrue(errs and any(why in e for e in errs), f"{bad[:60]!r}: {errs}")
        # kết quả lịch sử không có bốn cột mới: chèn Sharpe cho lần thử cũ (đi vào phương sai của Deflated Sharpe) → lỗi
        self.assertTrue(any("phải để trống bốn cột" in e for e in check(FULL.replace(",REJECTED,{},,,,", ",REJECTED,{},0.9,,,", 1))))
        # kiểm toán theo commit gốc: 13 → 17 cột được; 17 → 13, hay sang bất kỳ tiêu đề nào khác thì không
        f = ledger_audit.trials_rows_errors
        self.assertEqual(f(L.encode(), FULL.encode()), [])
        self.assertEqual(f(FULL.encode(), FULL.encode()), [])
        self.assertTrue(any("bị đổi" in e for e in f(FULL.encode(), L.encode())))
        self.assertTrue(any("đã bị sửa" in e for e in f(FULL.encode(), FULL.replace(",REJECTED,{},,,,", ",REJECTED,{},0.9,,,", 1).encode())))
        # vòng học ghi thêm được trên cả hai khuôn hợp lệ, và từ chối khuôn lạ thay vì ghi bừa
        (self.tmp / "cases.json").write_text(json.dumps([L, FULL, note, swapped]), encoding="utf-8")
        code, out, err = self._engine("""
            import json
            from engine import research
            from engine.config import path
            row = {"trial_id": "T00003", "cycle_date": "2026-11-20", "method": "m", "spec_id": "M-x", "features": "mom_60", "model": "ridge",
                   "ic_mean": 0.1, "ic_t": 1.0, "net_ann": 0.0, "fold_pos": 0.5, "threshold": 3.0, "status": "REJECTED", "regimes": "{}",
                   "sharpe": 0.1, "sharpe_ann": 1.0, "dsr": 0.5, "registry_hash": "h"}
            out = []
            for text in json.loads(open(path("cases.json"), encoding="utf-8").read()):
                open(path("research/trials.csv"), "w", encoding="utf-8", newline="").write(text)
                try:
                    research.append_trial_results([row]); out.append("ok")
                except RuntimeError as e:
                    out.append("refused")
            print(json.dumps(out))
        """)
        self.assertEqual(code, 0, err[-2000:])
        self.assertEqual(json.loads(out.strip().splitlines()[-1]), ["ok", "ok", "refused", "refused"])

    def test_first_210_results_are_pinned_in_config(self):
        """Vòng 7 điểm 2: 210 kết quả thử đầu tiên được ghim sha256 ngay trong config.yaml — có hiệu lực cả khi chưa có sổ đăng ký."""
        import yaml
        pin = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))["research"]["legacy_pin"]
        text = (ROOT / "research" / "trials.csv").read_text(encoding="utf-8")
        _, rows = laws_checks.read_trials(text)
        self.assertGreaterEqual(len(rows), 210)
        self.assertEqual((pin["results"], pin["last_trial_id"]), (210, rows[209]["trial_id"]))
        self.assertEqual(pin["sha256"], laws_checks.trials_digest(rows[:210]))  # kho thật khớp ghim
        self.assertEqual(laws_checks.check_trial_registry(ROOT), [])
        shutil.copy(ROOT / "config.yaml", self.tmp / "config.yaml")           # config thật, có ghim
        tp = self.tmp / "research" / "trials.csv"
        def check(t):
            tp.write_text(t, encoding="utf-8"); return laws_checks.check_trial_registry(self.tmp)
        self.assertEqual(check(text), [])
        self.assertEqual(check(text + "T99999,2026-11-20,x,M-x,mom_60,ridge,0,0,0,0,3.7,REJECTED,{}\n"), [])   # thêm dòng: việc của kiểm toán PR
        first = text.split("\n")[1]
        num = first.split(",")[6]
        self.assertTrue(any("đã ghim" in e for e in check(text.replace(num, num[:-1] + ("1" if num[-1] != "1" else "2"), 1))))   # sửa một chữ số
        lines = text.split("\n")
        self.assertTrue(any("đã ghim" in e for e in check("\n".join(lines[:1] + lines[2:]))))                # xóa dòng đầu
        self.assertTrue(any("ít hơn 210" in e for e in check("\n".join(lines[:150]) + "\n")))                # cắt bớt
        self.assertTrue(any("đã ghim" in e for e in check("\n".join(lines[:5] + [lines[5]] + lines[5:]))))    # chèn dòng

    def test_fixed_v302_boundary_from_config(self):
        """ADR-0004 (việc tồn 4 của ADR-0003): kho thật ghim mốc v3.0.2 cố định trong config.yaml. Chỉ commit nằm trong lịch
        sử của mốc mới được miễn; nhánh tách từ lịch sử cũ rồi gộp vào sau không được miễn ở BẤT KỲ lượt kiểm nào, kể cả lượt
        có commit gốc ở trước mốc. Mốc không đổi được; commit mốc vắng trong kho là lỗi."""
        import yaml
        from tools import ledger_audit
        repo = self.tmp / "repo"; (repo / "research").mkdir(parents=True)
        def git(*a):
            r = subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *a], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, f"git {a}: {r.stderr}")
            return r.stdout.strip()
        subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True, capture_output=True)
        tp = repo / "research" / "trials.csv"
        def commit(msg):
            git("add", "-A"); git("commit", "-qm", msg); return git("rev-parse", "HEAD")
        res3 = "T00003,2026-11-16,random_subset,M-c,mom_60,ridge,0.02,1.1,0.01,0.6,3.2,REJECTED,{}\n"
        res4 = res3.replace("T00003", "T00004")
        tp.write_text(self.LEGACY, encoding="utf-8")
        first = commit("kho cu")
        tp.write_text(self.LEGACY + res3, encoding="utf-8")
        old_main = commit("Vong hoc ban cu (truoc moc)")
        def cfg(boundary):
            (repo / "config.yaml").write_text(yaml.safe_dump({"research": {"v302_boundary": boundary}}), encoding="utf-8")
        cfg(old_main); merged = commit("gop v3.0.2: ghim moc")
        f = lambda b: ledger_audit.trials_history_errors(repo, b)
        self.assertEqual(f(first), [])                                           # vòng học bản cũ (trong lịch sử mốc): miễn
        # nhánh tách từ lịch sử cũ, ghi kết quả không đăng ký, gộp vào sau mốc → lỗi, kể cả khi commit gốc ở trước mốc
        git("checkout", "-q", "-b", "nhanh-cu", first)
        tp.write_text(self.LEGACY + res4, encoding="utf-8"); side = commit("ket qua tren nhanh tach tu lich su cu")
        git("checkout", "-q", "main"); git("merge", "-q", "--no-ff", "-X", "theirs", "-m", "gop nhanh cu", side)
        for base in (first, old_main, merged):
            self.assertTrue(any("T00004" in e and "commit liền trước chưa có" in e for e in f(base)), (base, f(base)))
        # đổi mốc sang một commit sau → lỗi
        git("reset", "-q", "--hard", merged)
        tp.write_text(self.LEGACY + res3 + res4, encoding="utf-8"); cfg(git("rev-parse", "HEAD")); commit("doi moc + ket qua")
        errs = f(merged)
        self.assertTrue(any("khác giá trị ở commit gốc" in e for e in errs), errs)
        self.assertTrue(any("T00004" in e and "commit liền trước chưa có" in e for e in errs), errs)   # …và không miễn được gì: vẫn dùng mốc cũ
        self.assertTrue(any("khác giá trị ở commit gốc" in e for e in ledger_audit.trials_history_errors(repo, merged, pull_request=True)))   # PR cũng bị bắt
        # PR mở từ trước khi main có mốc (base của sự kiện đã cũ): so với cha thứ nhất của commit gộp → vẫn bị bắt
        git("reset", "-q", "--hard", merged); git("checkout", "-q", "-b", "pr-doi-moc")
        cfg(first); commit("PR doi moc")
        git("checkout", "-q", "main"); git("merge", "-q", "--no-ff", "-m", "commit gop cua PR", "pr-doi-moc")
        errs = ledger_audit.trials_history_errors(repo, old_main, pull_request=True)
        self.assertTrue(any("khác giá trị ở commit gốc" in e for e in errs), errs)
        git("reset", "-q", "--hard", merged); (repo / "config.yaml").unlink(); commit("xoa moc")
        self.assertTrue(any("khác giá trị ở commit gốc" in e for e in f(merged)))   # xóa mốc cũng là đổi mốc
        tp.write_text(self.LEGACY + res3 + res4, encoding="utf-8"); commit("ket qua khong dang ky sau khi xoa moc")
        self.assertTrue(any("T00004" in e and "commit liền trước chưa có" in e for e in f(merged)), f(merged))
        # commit mốc không có trong kho → lỗi (đóng khi không chắc); mốc sai dạng → lỗi
        git("reset", "-q", "--hard", merged); cfg("0" * 40); commit("moc khong ton tai")
        errs = f(merged)
        self.assertTrue(any("khác giá trị ở commit gốc" in e for e in errs), errs)          # so với commit gốc: đổi mốc
        self.assertTrue(any("không tìm thấy commit mốc" in e for e in f(first)), f(first))   # commit gốc chưa có mốc: mốc lạ
        pr_missing = ledger_audit.trials_history_errors(repo, first, pull_request=True)
        self.assertTrue(any("không tìm thấy commit mốc" in e for e in pr_missing), pr_missing)  # PR cũng phải đóng khi thiếu mốc
        git("reset", "-q", "--hard", merged); cfg("abc"); commit("moc sai dang")
        self.assertTrue(any("40 ký tự" in e for e in f(merged)))
        # validate: kho có legacy_pin thì phải có mốc; kho thật có mốc đúng dạng
        self.assertEqual(laws_checks.check_v302_boundary(ROOT), [])
        self.assertIsNotNone(laws_checks.v302_boundary(ROOT))
        self.assertIn("check_v302_boundary(root)", (ROOT / "tools" / "laws_checks.py").read_text(encoding="utf-8").split("def run_all")[1])
        tmp = self.tmp / "cfgchk"; tmp.mkdir()
        real = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
        real["research"].pop("v302_boundary")
        (tmp / "config.yaml").write_text(yaml.safe_dump(real, allow_unicode=True), encoding="utf-8")
        self.assertTrue(any("thiếu research.v302_boundary" in e for e in laws_checks.check_v302_boundary(tmp)))

    def test_trial_results_only_from_the_cycle_on_main(self):
        """Vòng 7 điểm 2, phần cần git: PR không được thêm kết quả hay dòng đăng ký; trên main, commit ghi kết quả phải có đăng
        ký nằm sẵn ở commit liền trước; kết quả cũ không sửa được."""
        from tools import ledger_audit
        repo = self.tmp / "repo"; (repo / "research").mkdir(parents=True)
        def git(*a):
            r = subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *a], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, f"git {a}: {r.stderr}")
            return r.stdout.strip()
        subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True, capture_output=True)
        tp, rg = repo / "research" / "trials.csv", repo / "research" / "trial_registry.jsonl"
        def commit(msg):
            git("add", "-A"); git("commit", "-qm", msg); return git("rev-parse", "HEAD")
        tp.write_text(self.LEGACY, encoding="utf-8"); (repo / "x.txt").write_text("1")
        old_base = commit("kho truoc v3.0.2")
        f = lambda b, pr=False: ledger_audit.trials_history_errors(repo, b, pull_request=pr)
        # kho trước v3.0.2 (chưa có tools/registry_push.py): vòng học bản cũ ghi kết quả không đăng ký — không bị đòi trên main,
        # nhưng trong PR thì vẫn bị chặn
        tp.write_text(self.LEGACY + "T00003,2026-11-16,random_subset,M-c,mom_60,ridge,0.02,1.1,0.01,0.6,3.2,REJECTED,{}\n", encoding="utf-8")
        commit("Vong hoc ban cu")
        self.assertEqual(f(old_base), [])
        self.assertTrue(any("Pull Request thêm 1 kết quả" in e for e in f(old_base, pr=True)))
        git("reset", "-q", "--hard", old_base)
        (repo / "tools").mkdir(); (repo / "tools" / "registry_push.py").write_text("# v3.0.2\n")
        base = commit("v3.0.2")
        self.assertEqual(f(base), [])
        res3 = "T00003,2026-11-20,random_subset,M-c,mom_60,ridge,0.02,1.1,0.01,0.6,3.2,REJECTED,{}\n"
        # (a) PR thêm một kết quả, kể cả kèm dòng đăng ký ngay trong PR
        tp.write_text(self.LEGACY + res3, encoding="utf-8"); c = commit("PR: them ket qua")
        self.assertTrue(any("Pull Request thêm 1 kết quả" in e for e in f(base, pr=True)))
        rg.write_text(json.dumps({"trial_id": "T00003"}) + "\n", encoding="utf-8"); commit("PR: them dang ky")
        errs = f(base, pr=True)
        self.assertTrue(any("thêm 1 kết quả" in e for e in errs) and any("sổ đăng ký" in e for e in errs), errs)
        # (b) trên main: kết quả và đăng ký vào cùng lúc, hoặc kết quả vào trước → lỗi
        self.assertTrue(any("commit liền trước chưa có" in e for e in f(base)))
        git("reset", "-q", "--hard", base)
        rg.write_text(json.dumps({"trial_id": "T00003"}) + "\n", encoding="utf-8"); tp.write_text(self.LEGACY + res3, encoding="utf-8")
        commit("ket qua va dang ky cung mot commit")
        self.assertTrue(any("commit liền trước chưa có" in e for e in f(base)))
        # (c) đúng đường: đăng ký lên main trước, rồi commit sau mới ghi kết quả (kể cả một commit khác chen giữa)
        git("reset", "-q", "--hard", base)
        rg.write_text(json.dumps({"trial_id": "T00003"}) + "\n", encoding="utf-8"); commit("L-06: dang ky thu T00003")
        (repo / "x.txt").write_text("2"); commit("ledger: forecast")
        tp.write_text(self.LEGACY + res3, encoding="utf-8"); commit("Vong hoc")
        self.assertEqual(f(base), [])
        # xóa tệp mốc v3.0.2 ngay trong commit ghi kết quả để giả làm "kho bản cũ" → không được miễn
        git("reset", "-q", "--hard", base)
        (repo / "tools" / "registry_push.py").unlink(); tp.write_text(self.LEGACY + res3, encoding="utf-8"); commit("xoa tep moc + ghi ket qua")
        (repo / "tools" / "registry_push.py").write_text("# v3.0.2\n"); commit("tra lai tep moc")
        self.assertTrue(any("commit liền trước chưa có" in e for e in f(base)))
        # vòng 9 điểm 3: xóa tệp mốc ở MỘT COMMIT TRƯỚC, ghi kết quả không đăng ký ở commit sau, rồi trả tệp mốc lại. Phép kiểm
        # "vắng ở commit và commit cha" coi commit giữa là kho bản cũ. Nay mốc v3.0.2 xác định bằng tổ tiên.
        git("reset", "-q", "--hard", base)
        (repo / "tools" / "registry_push.py").unlink(); commit("A: xoa tep moc")
        tp.write_text(self.LEGACY + res3, encoding="utf-8"); commit("B: ghi ket qua khong dang ky")
        (repo / "tools" / "registry_push.py").write_text("# v3.0.2\n"); commit("C: tra lai tep moc")
        self.assertTrue(any("commit liền trước chưa có" in e and "T00003" in e for e in f(base)))
        # …hay ghi kết quả trên một nhánh tách ra từ lịch sử TRƯỚC v3.0.2 rồi gộp vào main sau: commit gốc của lượt kiểm đã
        # thuộc v3.0.2 thì không commit nào trong khoảng được miễn
        git("reset", "-q", "--hard", base)
        git("checkout", "-q", "-b", "nhanh-cu", old_base)
        tp.write_text(self.LEGACY + res3, encoding="utf-8"); side = commit("ket qua tren nhanh tach tu lich su cu")
        git("checkout", "-q", "main"); git("merge", "-q", "--no-ff", "-m", "gop nhanh cu", side)
        self.assertTrue(any("commit liền trước chưa có" in e for e in f(base)))
        # khoảng kiểm vắt qua lúc gộp v3.0.2 (commit gốc còn ở trước mốc): vòng học bản cũ được miễn, kết quả ghi SAU mốc mà
        # không đăng ký thì không
        git("reset", "-q", "--hard", old_base)
        tp.write_text(self.LEGACY + res3, encoding="utf-8"); commit("Vong hoc ban cu")
        (repo / "tools").mkdir(exist_ok=True); (repo / "tools" / "registry_push.py").write_text("# v3.0.2\n"); commit("gop v3.0.2")
        self.assertEqual(f(old_base), [])
        tp.write_text(self.LEGACY + res3 + res3.replace("T00003", "T00004"), encoding="utf-8"); commit("ket qua khong dang ky sau moc")
        errs = f(old_base)
        self.assertTrue(len(errs) == 1 and "T00004" in errs[0] and "T00003" not in errs[0], errs)
        git("reset", "-q", "--hard", base)
        rg.write_text(json.dumps({"trial_id": "T00003"}) + "\n", encoding="utf-8"); commit("L-06: dang ky thu T00003")
        tp.write_text(self.LEGACY + res3, encoding="utf-8"); commit("Vong hoc")
        # (d) sửa hoặc xóa kết quả cũ
        tp.write_text((self.LEGACY + res3).replace("-0.0146496299511184", "0.0946496299511184"), encoding="utf-8"); commit("sua ket qua cu")
        self.assertTrue(any("đã bị sửa" in e for e in f(base)))
        tp.write_text(self.LEGACY.split("\n", 2)[0] + "\n" + self.LEGACY.split("\n", 2)[1] + "\n", encoding="utf-8"); commit("xoa ket qua cu")
        self.assertTrue(any("mất kết quả" in e for e in f(base)))
        # PR mở từ lâu, main đã đi tiếp: vòng học ghi thêm kết quả lên main sau lúc mở PR. GitHub dựng commit gộp từ main hiện
        # tại, còn base.sha của sự kiện có thể là main cũ. Kết quả của main không được tính là của PR (lỗi gặp thật ở CI).
        git("reset", "-q", "--hard", base)
        git("checkout", "-q", "-b", "pr"); (repo / "doc.txt").write_text("PR chi sua tai lieu"); pr_head = commit("PR: sua tai lieu")
        git("checkout", "-q", "main")
        rg.write_text(json.dumps({"trial_id": "T00003"}) + "\n", encoding="utf-8"); commit("L-06: dang ky thu T00003")
        tp.write_text(self.LEGACY + res3, encoding="utf-8"); commit("Vong hoc tren main")
        git("merge", "-q", "--no-ff", "-m", "Merge PR", pr_head)                 # commit gộp như refs/pull/N/merge
        self.assertEqual(f(base, pr=True), [])                                   # base = main cũ (trước vòng học)
        tp.write_text(self.LEGACY + res3 + res3.replace("T00003", "T00004"), encoding="utf-8"); commit("PR lai them ket qua")
        git("reset", "-q", "--soft", "HEAD~1"); git("commit", "-q", "--amend", "-m", "Merge PR co them ket qua")   # nhét vào commit gộp
        self.assertTrue(any("Pull Request thêm 1 kết quả" in e for e in f(base, pr=True)))
        # thêm đúng bốn cột mới và ô rỗng vào dòng cũ (đúng như engine làm lần đầu) không bị coi là sửa
        self.assertEqual(ledger_audit.trials_rows_errors(self.LEGACY.encode(), (self.LEGACY.split("\n")[0] + ",sharpe,sharpe_ann,dsr,registry_hash\n"
                         + "\n".join(l + ",,,," for l in self.LEGACY.strip().split("\n")[1:]) + "\n").encode()), [])
        self.assertIn("research/trials.csv", ledger_audit.TRIALS)
        for name in ("paper/nav.csv", "paper/decisions.csv", "paper/trades.csv", "research/trial_registry.jsonl"):
            self.assertIn(name, ledger_audit.APPEND_ONLY)

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
        _config_without_pin(seed / "config.yaml"); (seed / "research").mkdir(); (seed / "data.txt").write_text("v1\n")
        (seed / "research" / "trials.csv").write_text(",".join(laws_checks.TRIAL_LEGACY_COLS) + "\n", encoding="utf-8")
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
        on_main = lambda: [json.loads(l)["trial_id"] for l in git(origin, "show", "main:research/trial_registry.jsonl").splitlines()][1:]
        first = lambda: json.loads(git(origin, "show", "main:research/trial_registry.jsonl").splitlines()[0])

        run1 = clone("run1"); (run1 / "data.txt").write_text("đang chạy dở\n")      # thư mục làm việc bẩn như lúc vòng học chạy
        r = cycle(run1)
        self.assertEqual(r.returncode, 7, r.stderr[-1500:])
        self.assertEqual(on_main(), ["T00001"])                                     # đăng ký đã nằm trên main dù vòng học hỏng
        self.assertEqual((first()["kind"], first()["results"]), ("legacy_anchor", 0))   # dòng neo lịch sử đi cùng lần đẩy đầu tiên
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
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        # Khác giây → "không phải tiền tố". Cùng giây → dòng JSON trùng từng byte, phải dừng cùng cách (không chạy backtest).
        self.assertTrue("không phải tiền tố" in r.stderr or "đã trùng bản đang chạy" in r.stderr, r.stderr)
        self.assertEqual(on_main(), ["T00001", "T00002", "T00003"])

    def test_identical_registry_bytes_do_not_let_a_second_cycle_run(self):
        """L-06: registered_at chỉ tới giây, nên hai vòng học đăng ký cùng nội dung ra cùng một dòng. push() từng coi
        'đã có trên main' là thành công — vòng thứ hai vẫn chạy backtest. Phải báo lỗi trước khi có kết quả."""
        from tools.registry_push import push
        origin = self.tmp / "origin.git"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True, capture_output=True)

        def git(cwd, *a):
            r = subprocess.run(["git", "-C", str(cwd), "-c", "user.name=t", "-c", "user.email=t@t", *a],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, f"git {a}: {r.stderr}")
            return r.stdout

        def clone(name):
            subprocess.run(["git", "clone", "-q", f"file://{origin}", str(self.tmp / name)], check=True, capture_output=True)
            return self.tmp / name

        seed = clone("seed-dup")
        _config_without_pin(seed / "config.yaml")
        (seed / "research").mkdir()
        (seed / "research" / "trials.csv").write_text(",".join(laws_checks.TRIAL_LEGACY_COLS) + "\n", encoding="utf-8")
        line = '{"hash":"abc","trial_id":"T00003"}\n'
        (seed / "research" / "trial_registry.jsonl").write_text(line, encoding="utf-8")
        git(seed, "add", "-A"); git(seed, "commit", "-qm", "seed"); git(seed, "push", "-q", "origin", "HEAD:main")
        other = clone("other-dup")
        self.assertEqual((other / "research" / "trial_registry.jsonl").read_text(encoding="utf-8"), line)
        with self.assertRaises(RuntimeError) as caught:
            push(other, "T00003", tries=2, wait=0)
        self.assertIn("đã trùng bản đang chạy", str(caught.exception))
        self.assertEqual(git(origin, "show", "main:research/trial_registry.jsonl"), line)

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
