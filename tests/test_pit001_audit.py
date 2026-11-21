"""PIT-001: fixture độc lập. Không đụng kho giá, config hay engine của repo khi dựng cây tạm."""
import hashlib, json, unittest
from pathlib import Path

from tools import pit001_audit as pit

ROOT = Path(__file__).resolve().parents[1]
HEADING = pit.VN30_HEADING


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _members(n=30, prefix="A"):
    # 30 mã giả, đúng 3 chữ, không trùng mã thật để fixture không bị đọc nhầm là khuyến nghị.
    out = []
    i = 0
    while len(out) < n:
        out.append(f"{prefix}{i:02d}"[-3:])
        i += 1
    return out


class ParserTests(unittest.TestCase):
    def test_vn30_section_stops_before_reserve_list(self):
        names = [f"T{i:02d}" for i in range(30)]
        lines = [f"    {i+1:2d}         {name}      Công ty" for i, name in enumerate(names)]
        text = HEADING + "\n" + "\n".join(lines) + "\nDanh mục cổ phiếu dự phòng chỉ số VN30\n    1         ZZZ      ngoài rổ"
        self.assertEqual(pit.tickers_in_vn30_section(text), names)

    def test_missing_heading_is_none(self):
        self.assertIsNone(pit.tickers_in_vn30_section("không có mục chỉ số\n    1         AAA      x"))


class AuditFixtureTests(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _snapshot(self):
        h = hashlib.sha256()
        for path in sorted(p for p in self.root.rglob("*") if p.is_file()):
            h.update(str(path.relative_to(self.root)).encode())
            h.update(path.read_bytes())
        return h.hexdigest()

    def _write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def _manifest(self, docs):
        self._write("data/evidence/vn30_reviews/EVIDENCE_MANIFEST.json",
                    json.dumps({"source_documents": docs}, ensure_ascii=False))

    def _doc(self, source_id, body, effective, published, members):
        rel = f"data/evidence/vn30_reviews/{source_id}/note.txt"
        self._write(rel, body)
        return {
            "source_id": source_id, "path": rel, "sha256": _sha(body), "bytes": len(body.encode("utf-8")),
            "published_at": published, "effective_date": effective, "members_after": members,
        }

    def test_bad_hash_is_fail_and_audit_does_not_write(self):
        body = "nguon"
        doc = self._doc("s1", body, "2024-01-02", "2024-01-01T00:00:00Z", ["AAA"])
        doc["sha256"] = "0" * 64
        self._manifest([doc])
        self._write("data/vn30_history.csv", "effective_date,ticker,action,source_id\n")
        before = self._snapshot()
        result = pit.audit(self.root)
        self.assertEqual(before, self._snapshot())
        self.assertEqual(pit._status_map(result["findings"])["PROVENANCE_HASH"], "FAIL")
        self.assertTrue(result["read_only"])

    def test_missing_source_file_is_fail(self):
        self._manifest([{
            "source_id": "s1", "path": "data/evidence/vn30_reviews/missing.txt",
            "sha256": "abc", "bytes": 1, "published_at": "2024-01-01", "effective_date": "2024-01-02",
            "members_after": [],
        }])
        result = pit.audit(self.root)
        self.assertEqual(pit._status_map(result["findings"])["PROVENANCE_HASH"], "FAIL")

    def test_published_after_effective_is_fail(self):
        members = _members()
        doc = self._doc("s1", "ban goc", "2024-01-02", "2024-01-03T00:00:00Z", members)
        self._manifest([doc])
        rows = ["effective_date,ticker,action,source_id"]
        for ticker in members:
            rows.append(f"2024-01-02,{ticker},ADD,s1")
        self._write("data/vn30_history.csv", "\n".join(rows) + "\n")
        result = pit.audit(self.root)
        self.assertEqual(pit._status_map(result["findings"])["PUBLICATION_BEFORE_USE"], "FAIL")

    def test_missing_published_at_is_unknown(self):
        doc = self._doc("s1", "ban goc", "2024-01-02", "2024-01-01T00:00:00Z", ["AAA"])
        doc["published_at"] = None
        self._manifest([doc])
        result = pit.audit(self.root)
        self.assertEqual(pit._status_map(result["findings"])["PUBLICATION_BEFORE_USE"], "UNKNOWN")

    def test_universe_short_of_research_start_is_fail_and_before_is_unknown(self):
        members = _members()
        doc = self._doc("s1", "ban goc", "2025-08-04", "2025-07-16T00:00:00Z", members)
        self._manifest([doc])
        rows = ["effective_date,ticker,action,source_id"]
        for ticker in members:
            rows.append(f"2025-08-04,{ticker},ADD,s1")
        self._write("data/vn30_history.csv", "\n".join(rows) + "\n")
        self._write("config.yaml", "universe_basis: CURRENT\ndata:\n  start: \"2016-01-01\"\nuniverse: [" + ", ".join(members) + "]\n")
        result = pit.audit(self.root)
        st = pit._status_map(result["findings"])
        self.assertEqual(st["UNIVERSE_COVERAGE"], "FAIL")
        self.assertEqual(st["MEMBERSHIP_BEFORE_FIRST_EVIDENCE"], "UNKNOWN")
        self.assertEqual(st["CSV_INTERNAL"], "PASS")
        self.assertNotEqual(result["conclusion"], "READY")

    def test_incomplete_membership_is_fail(self):
        members = _members(29)
        doc = self._doc("s1", "ban goc", "2024-01-02", "2024-01-01T00:00:00Z", members)
        self._manifest([doc])
        rows = ["effective_date,ticker,action,source_id"]
        for ticker in members:
            rows.append(f"2024-01-02,{ticker},ADD,s1")
        self._write("data/vn30_history.csv", "\n".join(rows) + "\n")
        result = pit.audit(self.root)
        self.assertEqual(pit._status_map(result["findings"])["CSV_INTERNAL"], "FAIL")

    def test_unverified_event_enters_chain_when_adjust_ignores_status(self):
        self._write("data/corporate_actions.csv",
                    "ticker,ex_date,type,ratio,cash_per_share,source,source_status,note\n"
                    "ZZZ,2024-06-11,stock_dividend,2.0,,nguon,CAN_DOI_CHIEU,chua doi chieu\n")
        self._write("engine/adjust.py", "def build_events(close, observed, manual, yahoo):\n    status = 'APPLIED'\n    return status\n")
        self._write("engine/data.py", "def load_market(as_of=None):\n    events = adjust.build_events(None, None, None, None)\n    return events\n")
        result = pit.audit(self.root)
        st = pit._status_map(result["findings"])
        self.assertEqual(st["CORPORATE_ACTION_VERIFICATION"], "FAIL")
        self.assertEqual(st["UNVERIFIED_EVENTS_IN_RESEARCH_CHAIN"], "FAIL")

    def test_verified_gate_is_pass_for_chain_check(self):
        self._write("data/corporate_actions.csv",
                    "ticker,ex_date,type,ratio,cash_per_share,source,source_status,note\n"
                    "ZZZ,2024-06-11,stock_dividend,2.0,,nguon,DA_DOI_CHIEU,da doi chieu\n")
        self._write("engine/adjust.py",
                    "def build_events(close, observed, manual, yahoo):\n"
                    "    source_status = manual\n"
                    "    if source_status != 'DA_DOI_CHIEU':\n"
                    "        return 'KHONG'\n"
                    "    return 'APPLIED'\n")
        self._write("engine/data.py", "def load_market(as_of=None):\n    return adjust.build_events(None, None, None, None)\n")
        result = pit.audit(self.root)
        self.assertEqual(pit._status_map(result["findings"])["UNVERIFIED_EVENTS_IN_RESEARCH_CHAIN"], "PASS")

    def test_blocking_checks_can_pass_while_adr_schema_stays_fail(self):
        members = _members()
        doc = self._doc("s1", "ban goc", "2024-01-02", "2024-01-01T10:00:00Z", members)
        self._manifest([doc])
        rows = ["effective_date,ticker,action,source_id"]
        for ticker in members:
            rows.append(f"2024-01-02,{ticker},ADD,s1")
        self._write("data/vn30_history.csv", "\n".join(rows) + "\n")
        self._write("config.yaml",
                    "universe_basis: HISTORICAL\n"
                    "data:\n  start: \"2024-01-02\"\n"
                    "universe: [" + ", ".join(members) + "]\n")
        self._write("engine/data.py",
                    "def ingest(end=None):\n"
                    "    history = open('data/vn30_history.csv').read()\n"
                    "    return history\n"
                    "def load_market(as_of=None):\n"
                    "    return verified_factors()\n")
        self._write("engine/adjust.py",
                    "def build_events(close, observed, manual, yahoo):\n"
                    "    source_status = 'DA_DOI_CHIEU'\n"
                    "    return source_status\n")
        self._write("data/corporate_actions.csv",
                    "ticker,ex_date,type,ratio,cash_per_share,source,source_status,note\n")
        prices = ["date,ticker,close"]
        for ticker in members:
            prices.append(f"2024-01-02,{ticker},1")
        self._write("data/store/prices/2024-01.csv", "\n".join(prices) + "\n")
        before = self._snapshot()
        result = pit.audit(self.root)
        self.assertEqual(before, self._snapshot())
        st = pit._status_map(result["findings"])
        self.assertEqual(st["ADR0008_SCHEMA"], "FAIL")
        self.assertEqual(st["UNIVERSE_COVERAGE"], "PASS")
        self.assertEqual(st["ENGINE_UNIVERSE_MODE"], "PASS")
        self.assertEqual(st["PRICE_COVERAGE"], "PASS")
        self.assertEqual(st["PROVENANCE_HASH"], "PASS")
        self.assertEqual(result["conclusion"], "READY")
        self.assertFalse(result["alpha_claim"])

    def test_news_without_effective_token_is_fail(self):
        rel = "data/evidence/vn30_reviews/n1/news.json"
        self._write(rel, '{"data":{"summary":"khong ghi ngay hieu luc"}}')
        blob = (self.root / rel).read_bytes()
        self._manifest([{
            "source_id": "n1", "path": rel, "sha256": hashlib.sha256(blob).hexdigest(), "bytes": len(blob),
            "published_at": "2024-01-01T00:00:00Z", "effective_date": "2024-01-02", "members_after": [],
        }])
        result = pit.audit(self.root)
        self.assertEqual(pit._status_map(result["findings"])["NEWS_EFFECTIVE_DATE_TEXT"], "FAIL")

    def test_schema_mismatch_does_not_invent_rows(self):
        self._write("data/vn30_history.csv", "effective_date,ticker,action,source_id\n2024-01-02,ABC,ADD,s1\n")
        result = pit.audit(self.root)
        finding = next(item for item in result["findings"] if item["id"] == "ADR0008_SCHEMA")
        self.assertEqual(finding["status"], "FAIL")
        self.assertEqual(finding["evidence"]["actual_columns"], ["effective_date", "ticker", "action", "source_id"])


if __name__ == "__main__":
    unittest.main()
