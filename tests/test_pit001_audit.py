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
        self.assertEqual(pit._status_map(result["findings"])["UNVERIFIED_EVENTS_IN_RESEARCH_CHAIN"], "INCONCLUSIVE")

    def test_schema_fail_never_certifies_ready(self):
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
        self.assertEqual(st["ENGINE_UNIVERSE_MODE"], "INCONCLUSIVE")
        self.assertEqual(st["TICKER_PRESENCE"], "PASS")
        self.assertEqual(st["PROVENANCE_HASH"], "PASS")
        self.assertEqual(result["conclusion"], "NOT_READY")
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


class FailClosedMatrixTests(unittest.TestCase):
    """Mỗi thiếu hụt trong hợp đồng đều ngăn READY, kể cả không có FAIL khác."""
    def test_each_critical_fail_blocks_ready(self):
        critical = (
            "PROVENANCE_HASH", "PUBLICATION_BEFORE_USE", "DECISION_TIME_OF_KNOWLEDGE",
            "CSV_INTERNAL", "ADR0008_SCHEMA", "UNIVERSE_COVERAGE",
            "MEMBERSHIP_BEFORE_FIRST_EVIDENCE", "CONTINUITY_BETWEEN_REVIEWS",
            "ENGINE_UNIVERSE_MODE", "CONFIG_VS_EVIDENCED_BASKET",
            "TICKER_PRESENCE", "PRICE_WINDOW_COVERAGE",
            "CORPORATE_ACTION_VERIFICATION", "UNVERIFIED_EVENTS_IN_RESEARCH_CHAIN",
            "PDF_VN30_CONTENT", "HOSE_2510691_SCOPE",
            "NEWS_EFFECTIVE_DATE_TEXT", "MARKET_MICROSTRUCTURE_ASSUMPTIONS",
        )
        baseline = [pit.finding(k, "PASS", "fixture") for k in critical]
        self.assertEqual(pit.conclude(baseline)[0], "READY")
        for key in critical:
            for status in ("FAIL", "UNKNOWN", "INCONCLUSIVE"):
                changed = [pit.finding(f["id"], status if f["id"] == key else "PASS", "fixture")
                           for f in baseline]
                got = pit.conclude(changed)[0]
                want = "NOT_READY" if status == "FAIL" else "INCONCLUSIVE"
                with self.subTest(key=key, status=status):
                    self.assertEqual(got, want)
        self.assertEqual(pit.conclude(baseline[:-1])[0], "INCONCLUSIVE")

    def test_not_ready_overrides_other_missing_evidence(self):
        rows = [pit.finding("PROVENANCE_HASH", "UNKNOWN", "x"),
                pit.finding("ADR0008_SCHEMA", "FAIL", "x")]
        self.assertEqual(pit.conclude(rows)[0], "NOT_READY")

    def test_comments_and_literals_do_not_prove_verified_gate(self):
        src = ("def build_events(a,b,c,d):\n"
               "    # source_status is checked\n"
               "    note = 'source_status'\n"
               "    return 'APPLIED'\n")
        self.assertFalse(pit.research_chain_requires_verified_status(src))
        self.assertFalse(pit.load_market_uses_verified_chain(
            "def load_market():\n    # verified_factors()\n    note = 'verified_factors'\n    return 1\n"))

    def test_engine_historical_string_in_comment_is_not_proof(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "engine").mkdir()
            (root / "engine/data.py").write_text(
                "def load_market():\n    # vn30_history is loaded\n"
                "    path = 'vn30_history'\n    return path\n", encoding="utf-8")
            result = pit.check_engine_mode(root, {"universe_basis":"HISTORICAL"})
            self.assertEqual(result["status"], "INCONCLUSIVE")

    def test_price_one_row_per_symbol_is_not_window_pass(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            p = root / "data/store/prices/2024-01.csv"
            p.parent.mkdir(parents=True)
            p.write_text("date,ticker,close\n2024-01-02,AAA,1\n"
                         "2024-01-02,BBB,1\n", encoding="utf-8")
            info = pit._price_tickers(root)
            states = [("2024-01-02", {"AAA", "BBB"})]
            self.assertEqual(pit.check_ticker_presence(info, states)["status"], "PASS")
            coverage = pit.check_price_window_coverage(info, states, {"horizon_days":20})
            self.assertEqual(coverage["status"], "FAIL")

    def test_publication_same_day_after_decision_is_fail(self):
        docs = [{"source_id":"news", "published_at":"2026-11-02T09:00:00Z",
                 "effective_date":"2026-11-02"}]   # 16:00 VN > 15:00 decision
        cfg = {"research":{"decision_time_local":"15:00"}}
        self.assertEqual(pit.check_publication_order(docs)["status"], "PASS")
        self.assertEqual(pit.check_decision_cutoff(docs, cfg)["status"], "FAIL")
        self.assertEqual(pit.check_decision_cutoff(docs, {})["status"], "INCONCLUSIVE")

    def test_date_only_outside_news_summary_is_not_proof(self):
        raw = '{"data":{"title":"13/05/2026", "summary":"Không có thông báo ngày hiệu lực"}}'
        self.assertFalse(pit._news_effective_statement(raw, "2026-05-13"))

    def test_missing_pdf_content_never_counts_as_pass(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs = [{"source_id":"p", "path":"data/missing.pdf",
                     "effective_date":"2026-11-16", "members_after":["AAA"]}]
            self.assertEqual(pit.check_pdf_contents(root, docs)["status"], "INCONCLUSIVE")

if __name__ == "__main__":
    unittest.main()
