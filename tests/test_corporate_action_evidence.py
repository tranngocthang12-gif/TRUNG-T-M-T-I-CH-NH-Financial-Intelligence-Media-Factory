"""Bằng chứng quyền VCB, TCB, FPT: chỉ đọc manifest và chạy công cụ. Không ghi kho."""
import hashlib
import json
import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "evidence" / "corporate_actions" / "EVIDENCE_MANIFEST.json"
REPORT = ROOT / "reports" / "CORPORATE_ACTION_EVIDENCE_20261119.md"
TOOL = ROOT / "tools" / "corporate_action_evidence.py"


def _docs():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))["source_documents"]


class CorporateActionEvidenceTests(unittest.TestCase):
    def test_manifest_files_and_ex_date(self):
        docs = _docs()
        self.assertGreaterEqual(len(docs), 3)
        tickers = set()
        for doc in docs:
            for key in ("source_id", "url", "issuer", "published_at", "accessed_at",
                        "effective_date", "path", "sha256", "bytes", "ticker",
                        "event_type", "official_ex_date", "official_ratio"):
                self.assertIn(key, doc)
            self.assertRegex(doc["official_ex_date"], r"^\d{4}-\d{2}-\d{2}$")
            path = ROOT / doc["path"]
            self.assertTrue(path.is_file(), doc["path"])
            blob = path.read_bytes()
            self.assertEqual(len(blob), doc["bytes"])
            self.assertEqual(hashlib.sha256(blob).hexdigest(), doc["sha256"])
            tickers.add(doc["ticker"])
        self.assertEqual(tickers, {"VCB", "TCB", "FPT"})

    def test_tool_same_hash_twice(self):
        hashes = []
        for _ in range(2):
            with tempfile.NamedTemporaryFile(prefix="ca-evidence-", suffix=".md") as handle:
                out = handle.name
            proc = subprocess.run(
                ["python", str(TOOL), "--out", out],
                cwd=ROOT, check=False, capture_output=True, text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            blob = pathlib.Path(out).read_bytes()
            pathlib.Path(out).unlink()
            hashes.append(hashlib.sha256(blob).hexdigest())
        self.assertEqual(hashes[0], hashes[1])

    def test_tool_does_not_write_store_or_engine(self):
        before = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            out = str(pathlib.Path(tmp) / "report.md")
            proc = subprocess.run(
                ["python", str(TOOL), "--out", out],
                cwd=ROOT, check=False, capture_output=True, text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
        after = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT)
        self.assertEqual(before, after)

    def test_report_has_three_events_and_sections(self):
        text = REPORT.read_text(encoding="utf-8")
        for ticker in ("VCB", "TCB", "FPT"):
            self.assertIn(ticker, text)
        for mark in ("(a)", "(b)", "(c)", "(d)"):
            self.assertIn(mark, text)
        self.assertTrue("CHƯA ĐỦ BẰNG CHỨNG" in text or "ngày giao dịch không hưởng quyền" in text)


if __name__ == "__main__":
    unittest.main()
