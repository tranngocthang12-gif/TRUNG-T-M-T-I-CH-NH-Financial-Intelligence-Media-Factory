"""Dự báo từ Issue 'Forecast' (tools/ledger_intake.py) và engine (engine/ledger.py) cùng ghi/đọc ledger/predictions.jsonl.

Lỗi được chặn ở đây: dòng từ Issue không có khóa 'id' và resolution_rule là chuỗi, nên engine.ledger.resolve()
và scorecard() ném KeyError → vòng học hằng ngày dừng ngay sau dự báo Issue đầu tiên.
Mọi thứ chạy trong thư mục tạm (TTC_HOME, bản sao tools/) và tiến trình con: không chạm tệp nào của kho.
"""
import json, os, pathlib, shutil, subprocess, sys, tempfile, textwrap, unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.ledger_intake import control_b_hash  # noqa: E402
B_HASH = control_b_hash(ROOT / "governance" / "CONTROL_B_PROMPT.md")


def _form(seat, question, resolve_at="2099-02-15", p="0.25"):
    fields = {"seat": seat, "question": question,
              "resolution_source": "https://example.org/bctc-q4", "resolution_rule": "comparison",
              "resolve_at": resolve_at, "p": p, "base_rate": "0.30",
              "invalidation_conditions": "Ngân hàng đổi cách phân loại nợ",
              "author_seat": "Claude Project TTC" if seat == "A" else "Claude trần",
              "model_cutoff": "2026-06", "library_refs": "_No response_" if seat == "B" else "KN-T2-vas-01",
              "prompt_hash": B_HASH if seat == "B" else "_No response_"}
    return "\n\n".join(f"### {k}\n\n{v}" for k, v in fields.items())


class LedgerCompatTests(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        (self.tmp / "contracts").mkdir()
        shutil.copy(ROOT / "contracts" / "forecast_issue.schema.json", self.tmp / "contracts")
        shutil.copytree(ROOT / "tools", self.tmp / "tools", ignore=shutil.ignore_patterns("__pycache__"))
        (self.tmp / "governance").mkdir()
        shutil.copy(ROOT / "governance" / "CONTROL_B_PROMPT.md", self.tmp / "governance")
        (self.tmp / "ledger").mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _intake(self, number, body, created="2026-11-17T02:00:00Z"):
        env = {**os.environ, "ISSUE_NUMBER": str(number), "ISSUE_CREATED_AT": created, "ISSUE_BODY": body}
        r = subprocess.run([sys.executable, str(self.tmp / "tools" / "ledger_intake.py")],
                           env=env, capture_output=True, text=True)
        return r.returncode, r.stdout

    def _engine(self, code):
        """Chạy mã engine với TTC_HOME = thư mục tạm; trả về JSON in ra ở dòng cuối."""
        env = {**os.environ, "TTC_HOME": str(self.tmp), "PYTHONPATH": str(ROOT)}
        r = subprocess.run([sys.executable, "-c", textwrap.dedent(code)], cwd=str(ROOT), env=env,
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr[-3000:])
        return json.loads(r.stdout.strip().splitlines()[-1])

    def _chain_errors(self):
        sys.path.insert(0, str(ROOT))
        from tools import laws_checks
        return laws_checks.check_ledger_chain(self.tmp)

    def test_issue_rows_do_not_break_engine_and_chain_holds(self):
        self.assertEqual(self._intake(101, _form("A", "Nợ nhóm 3-5 VCB tại 31/12 cao hơn 30/9?"))[0], 0)
        self.assertEqual(self._intake(102, _form("B", "Nợ nhóm 3-5 VCB tại 31/12 cao hơn 30/9?", p="0.40"))[0], 0)
        rows = [json.loads(l) for l in (self.tmp / "ledger" / "predictions.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual([r["id"] for r in rows], ["F-101", "F-102"])

        out = self._engine("""
            import json
            import numpy as np, pandas as pd
            from engine import ledger
            idx = pd.bdate_range("2026-01-02", periods=60)
            close = pd.DataFrame({"AAA": np.linspace(10, 13, 60), "BBB": np.linspace(10, 9, 60)}, index=idx)
            # engine ghi một dự báo giá xen giữa các dòng Issue (đường experts)
            pred = {"procedure": "test", "claim": "x", "ticker": "AAA", "horizon": 5, "probability": 0.6,
                    "requires_evidence": False}
            ok, rej = ledger.record([pred], "2026-01-05", ["AAA", "BBB"], set(), close)
            res = ledger.resolve(close, "2026-03-20")
            sc = ledger.scorecard("2026-03-20")
            print(json.dumps({"ok": len(ok), "rej": len(rej), "resolved": [r["prediction_id"] for r in res], "sc": sc},
                             ensure_ascii=False))
        """)
        self.assertEqual((out["ok"], out["rej"]), (1, 0))
        self.assertEqual(len(out["resolved"]), 1)                       # chỉ dòng engine được chấm bằng giá
        self.assertTrue(out["resolved"][0].startswith("P-"))
        sc = out["sc"]
        self.assertEqual(sc["total_predictions"], 3)
        self.assertEqual(sc["resolved"], 1)
        self.assertEqual(sc["issue_forecasts"]["total"], 2)
        self.assertEqual(sc["issue_forecasts"]["by_seat"]["A"], {"n": 1, "resolved": 0, "void": 0, "pending": 1})
        self.assertEqual(sc["issue_forecasts"]["by_seat"]["B"], {"n": 1, "resolved": 0, "void": 0, "pending": 1})
        self.assertEqual(sc["issue_forecasts"]["ab"]["pairs"], 1)
        self.assertIn("test", sc["procedures"])

        # Issue tiếp theo nối chuỗi sau dòng engine; toàn tệp vẫn đúng hash chuỗi
        self.assertEqual(self._intake(103, _form("A", "NIM quý IV của BID trong khoảng 2,4–2,8%?"))[0], 0)
        self.assertEqual(self._chain_errors(), [])
        resolved_again = self._engine("""
            import json
            import numpy as np, pandas as pd
            from engine import ledger
            idx = pd.bdate_range("2026-01-02", periods=60)
            close = pd.DataFrame({"AAA": np.linspace(10, 13, 60), "BBB": np.linspace(10, 9, 60)}, index=idx)
            print(json.dumps({"n": len(ledger.resolve(close, "2026-03-21")), "sc": ledger.scorecard("2026-03-21")}))
        """)
        self.assertEqual(resolved_again["n"], 0)                        # không chấm lại, không chấm dòng Issue
        self.assertEqual(resolved_again["sc"]["issue_forecasts"]["total"], 3)

    def test_engine_void_row_matches_resolution_schema(self):
        """Dòng VOID của engine (excess_return null, outcome null, void) phải khớp contracts/resolution.schema.json."""
        import jsonschema
        schema = json.loads((ROOT / "contracts" / "resolution.schema.json").read_text(encoding="utf-8"))
        void_row = {"prediction_id": "P-x", "resolved_at": "2026-11-17", "entry_date": "2026-11-01", "exit_date": "2026-11-10",
                    "excess_return": None, "outcome": None, "void": "lỗi dữ liệu giá trong cửa sổ chấm"}
        jsonschema.validate(void_row, schema)
        jsonschema.validate({"prediction_id": "P-y", "resolved_at": "2026-11-17", "excess_return": 0.012, "outcome": 1}, schema)
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate({"prediction_id": "P-z", "resolved_at": "2026-11-17", "outcome": None}, schema)   # VOID thiếu lý do

    def test_intake_rejects_recommendation_words_before_writing(self):
        code, out = self._intake(201, _form("A", "VCB: nên mua trước khi công bố BCTC?"))
        self.assertEqual(code, 2, out)
        self.assertIn("L-02", out)
        self.assertFalse((self.tmp / "ledger" / "predictions.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
