"""Bằng chứng quyền cổ phiếu 11/2025–11/2026. Không mạng. Không ghi kho."""
import hashlib
import json
import pathlib
import shutil
import subprocess
import tempfile
import unittest
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "evidence" / "corporate_actions" / "EVIDENCE_MANIFEST_2026H2.json"
REPORT = ROOT / "reports" / "CORPORATE_ACTION_EVIDENCE_2026H2_20261119.md"

# Ngày và hệ số engine trong lệnh. Không phải bằng chứng.
EVENTS = (
    ("TPB", "2026-10-02", 1.15),
    ("HDB", "2026-10-09", 1.30),
    ("TCB", "2026-10-29", 1.50),
    ("VIC", "2025-12-05", 2.0),
    ("POW", "2025-12-10", 1.19),
    ("CTG", "2025-12-17", 1.446366),
    ("HDB", "2025-12-18", 1.2969),
    ("HPG", "2026-05-25", 1.10),
    ("SSB", "2026-05-28", 1.205202),
    ("ACB", "2026-06-15", 1.13),
    ("VJC", "2026-06-16", 1.30),
    ("VHM", "2026-08-06", 2.0),
    ("MBB", "2026-08-11", 1.15),
    ("SSI", "2026-08-17", 1.20),
    ("BID", "2026-08-17", 1.068433),
    ("VIB", "2026-09-10", 1.095),
    ("VPB", "2026-09-24", 1.260410),
)
REQUIRED = (
    "source_id", "url", "issuer", "published_at", "accessed_at", "effective_date",
    "path", "sha256", "bytes", "ticker", "event_type", "official_ex_date",
    "official_record_date", "official_ratio", "official_ratio_text", "note",
)
NEAR_DAYS = 21


def _docs(path=MANIFEST):
    return json.loads(path.read_text(encoding="utf-8"))["source_documents"]


def _day(value):
    return str(value)[:10]


def _match(doc):
    official = date.fromisoformat(_day(doc["official_ex_date"]))
    hits = []
    for ticker, day, _ratio in EVENTS:
        if doc["ticker"] != ticker:
            continue
        if abs((official - date.fromisoformat(day)).days) <= NEAR_DAYS:
            hits.append((ticker, day))
    return hits


def check_bytes(root, docs):
    errors = []
    for doc in docs:
        for key in REQUIRED:
            if key not in doc:
                errors.append(f"{doc.get('source_id')} thiếu {key}")
        path = pathlib.Path(root) / doc["path"]
        if not path.is_file():
            errors.append(f"không có tệp {doc['path']}")
            continue
        blob = path.read_bytes()
        if len(blob) != doc["bytes"]:
            errors.append(f"{doc['source_id']} bytes {len(blob)} != {doc['bytes']}")
        digest = hashlib.sha256(blob).hexdigest()
        if digest != doc["sha256"]:
            errors.append(f"{doc['source_id']} sha256 lệch")
    return errors


class CorporateActionEvidence2026H2Tests(unittest.TestCase):
    def test_manifest_files_hash_and_keys(self):
        docs = _docs()
        self.assertGreaterEqual(len(docs), 1)
        self.assertEqual(check_bytes(ROOT, docs), [])
        for doc in docs:
            self.assertTrue(doc["url"])
            self.assertTrue(doc["issuer"])
            self.assertRegex(_day(doc["published_at"]), r"^\d{4}-\d{2}-\d{2}$")
            self.assertRegex(doc["official_ex_date"], r"^\d{4}-\d{2}-\d{2}$")
            self.assertIsInstance(doc["official_ratio"], (int, float))

    def test_published_on_or_before_ex_date(self):
        for doc in _docs():
            self.assertLessEqual(_day(doc["published_at"]), doc["official_ex_date"], doc["source_id"])

    def test_each_document_matches_exactly_one_ordered_event(self):
        seen = []
        for doc in _docs():
            hits = _match(doc)
            self.assertEqual(len(hits), 1, (doc["source_id"], hits))
            seen.append(hits[0])
        self.assertEqual(len(seen), len(set(seen)))

    def test_report_has_seventeen_rows(self):
        text = REPORT.read_text(encoding="utf-8")
        ids = {doc["source_id"] for doc in _docs()}
        for ticker, day, _ratio in EVENTS:
            key = f"{ticker} {day}"
            self.assertIn(key, text, key)
            line = next(row for row in text.splitlines() if key in row)
            pinned = any(source_id in line for source_id in ids)
            missing = "CHƯA ĐỦ BẰNG CHỨNG" in line and len(line.split("CHƯA ĐỦ BẰNG CHỨNG", 1)[1].strip(" |")) > 8
            self.assertTrue(pinned or missing, line)

    def test_flipping_one_byte_in_a_temp_copy_fails_and_repo_untouched(self):
        before = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT)
        docs = _docs()
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            for doc in docs:
                src = ROOT / doc["path"]
                dest = root / doc["path"]
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dest)
            manifest = root / "data" / "evidence" / "corporate_actions" / "EVIDENCE_MANIFEST_2026H2.json"
            manifest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(MANIFEST, manifest)
            self.assertEqual(check_bytes(root, _docs(manifest)), [])
            target = root / docs[0]["path"]
            blob = bytearray(target.read_bytes())
            blob[min(100, len(blob) - 1)] ^= 0x01
            target.write_bytes(blob)
            errors = check_bytes(root, _docs(manifest))
            self.assertTrue(errors)
            self.assertTrue(any("sha256" in err for err in errors))
        after = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT)
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
