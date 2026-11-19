"""VN30 theo kỳ: chỉ đọc CSV, manifest và bản gốc đã ghim. Không mạng, không ghi kho."""
import csv, hashlib, json, pathlib, unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "vn30_history.csv"
MANIFEST_PATH = ROOT / "data" / "evidence" / "vn30_reviews" / "EVIDENCE_MANIFEST.json"
COLUMNS = ["effective_date", "ticker", "action", "source_id"]


def _load():
    with CSV_PATH.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    docs = manifest["source_documents"]
    return rows, docs


def _reconstruct(rows):
    """Trả (thứ tự ngày, tập thành viên sau mỗi ngày)."""
    by_date = {}
    for row in rows:
        by_date.setdefault(row["effective_date"], []).append(row)
    members = set()
    states = []
    for date in sorted(by_date):
        day = by_date[date]
        for row in day:
            if row["action"] == "REMOVE":
                if row["ticker"] not in members:
                    raise AssertionError(f"REMOVE mã không có mặt: {row['ticker']} {date}")
                members.remove(row["ticker"])
        for row in day:
            if row["action"] == "ADD":
                if row["ticker"] in members:
                    raise AssertionError(f"ADD mã đang có mặt: {row['ticker']} {date}")
                members.add(row["ticker"])
        if len(members) != 30:
            raise AssertionError(f"{date}: {len(members)} mã, không phải 30")
        states.append((date, set(members)))
    return states


def _at(states, day):
    current = None
    for date, members in states:
        if date <= day:
            current = members
        else:
            break
    return current


class Vn30HistoryTests(unittest.TestCase):
    def test_csv_schema(self):
        with CSV_PATH.open(encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            header = next(reader)
            body = list(reader)
        self.assertEqual(header, COLUMNS)
        self.assertGreater(len(body), 0)
        for row in body:
            self.assertEqual(len(row), 4)
            date, ticker, action, source_id = row
            self.assertRegex(date, r"^\d{4}-\d{2}-\d{2}$")
            self.assertRegex(ticker, r"^[A-Z0-9]{3}$")
            self.assertIn(action, ("ADD", "REMOVE"))
            self.assertTrue(source_id)

    def test_manifest_files_match_hash(self):
        rows, docs = _load()
        by_id = {d["source_id"]: d for d in docs}
        self.assertEqual(len(by_id), len(docs))
        for row in rows:
            self.assertIn(row["source_id"], by_id)
        for doc in docs:
            for key in ("source_id", "url", "issuer", "published_at", "accessed_at",
                        "effective_date", "path", "sha256", "bytes", "members_after"):
                self.assertIn(key, doc)
            self.assertRegex(doc["effective_date"], r"^\d{4}-\d{2}-\d{2}$")
            self.assertEqual(len(doc["members_after"]), 30)
            self.assertEqual(doc["members_after"], sorted(doc["members_after"]))
            path = ROOT / doc["path"]
            self.assertTrue(path.is_file(), doc["path"])
            blob = path.read_bytes()
            self.assertEqual(len(blob), doc["bytes"])
            self.assertEqual(hashlib.sha256(blob).hexdigest(), doc["sha256"])

    def test_membership_stays_thirty(self):
        rows, _ = _load()
        states = _reconstruct(rows)
        self.assertGreater(len(states), 0)
        for date, members in states:
            self.assertEqual(len(members), 30, date)

    def test_each_period_matches_members_after(self):
        rows, docs = _load()
        states = _reconstruct(rows)
        for doc in docs:
            got = _at(states, doc["effective_date"])
            self.assertIsNotNone(got, doc["source_id"])
            self.assertEqual(got, set(doc["members_after"]), doc["source_id"])

    def test_set_on_2026_11_16_is_period_10_2026(self):
        rows, docs = _load()
        states = _reconstruct(rows)
        period = [d for d in docs if d.get("review_period") == "2026-10"]
        self.assertGreaterEqual(len(period), 1)
        official = set(period[0]["members_after"])
        for doc in period:
            self.assertEqual(set(doc["members_after"]), official)
            self.assertEqual(doc["effective_date"], "2026-11-16")
        self.assertEqual(_at(states, "2026-11-16"), official)

    def test_reads_only(self):
        # Chỉ đọc. Không mở tệp để ghi, không tạo thư mục.
        rows, docs = _load()
        self.assertTrue(rows)
        self.assertTrue(docs)
        self.assertTrue(CSV_PATH.is_file())
        self.assertTrue(MANIFEST_PATH.is_file())


if __name__ == "__main__":
    unittest.main()
