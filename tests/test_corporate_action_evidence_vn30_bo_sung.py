"""Sự kiện quyền BSR, LPB, MCH, TCX, VPL từ 2026-06-01 (LỆNH D2b). Không mạng. Không ghi kho.

Dùng lại các hàm kiểm của tests/test_corporate_action_evidence_2026h2.py (sha256 và số byte, luật published_at, luật
event_type) cho manifest mới. Mã không tìm thấy thông báo phải ghi UNKNOWN kèm truy vấn đã tra, không ghi "không có sự kiện".
"""
import hashlib
import importlib.util
import json
import pathlib
import shutil
import subprocess
import tempfile
import unittest
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "evidence" / "corporate_actions" / "EVIDENCE_MANIFEST_VN30_BO_SUNG.json"
REPORT = ROOT / "reports" / "CORPORATE_ACTION_EVIDENCE_VN30_BO_SUNG_20261121.md"
TICKERS = ("BSR", "LPB", "MCH", "TCX", "VPL")
WINDOW = ("2026-06-01", "2026-11-21")
HOSE = "Sở Giao dịch Chứng khoán Thành phố Hồ Chí Minh (HOSE)"

_spec = importlib.util.spec_from_file_location("_h2_checks", ROOT / "tests" / "test_corporate_action_evidence_2026h2.py")
h2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(h2)


def _man(path=MANIFEST):
    return json.loads(path.read_text(encoding="utf-8"))


def _docs(path=MANIFEST):
    return _man(path)["source_documents"]


def metadata_errors(root, docs):
    """JSON tin và JSON tệp đính kèm của HOSE đã ghim cạnh bản gốc: đúng id, đúng mã, tệp đính kèm trùng url, sha256 khớp note."""
    errors = []
    for doc in docs:
        sid = doc["source_id"]
        nid = sid.split("-", 1)[1]
        folder = pathlib.Path(root) / pathlib.Path(doc["path"]).parent
        news_p, media_p = folder / f"hose_news_{nid}.json", folder / f"hose_mediafiles_{nid}.json"
        if not news_p.is_file() or not media_p.is_file():
            errors.append(f"{sid} thiếu JSON tin hoặc JSON tệp đính kèm")
            continue
        for p in (news_p, media_p):
            if hashlib.sha256(p.read_bytes()).hexdigest() not in doc["published_at_note"]:
                errors.append(f"{sid} sha256 của {p.name} không khớp note")
        news = json.loads(news_p.read_bytes())["data"]
        if str(news.get("id")) != nid or news.get("code") != doc["ticker"]:
            errors.append(f"{sid} tin HOSE sai id hoặc sai mã")
        want = urllib.parse.unquote(doc["url"].split("staticfile.hsx.vn", 1)[1])
        files = json.loads(media_p.read_bytes())["data"]["list"]
        if [m.get("filePath", "").replace("~", "", 1) for m in files].count(want) != 1:
            errors.append(f"{sid} danh sách tệp đính kèm của tin không có đúng url bản gốc")
    return errors


class CorporateActionEvidenceVN30BoSungTests(unittest.TestCase):
    def test_files_and_shared_rules(self):
        docs = _docs()
        self.assertTrue(docs)
        self.assertEqual(h2.check_bytes(ROOT, docs), [])
        self.assertEqual(h2.publication_errors(docs), [])
        self.assertEqual(h2.classification_errors(docs), [])
        self.assertEqual(metadata_errors(ROOT, docs), [])
        for doc in docs:
            self.assertEqual(set(doc), set(h2.REQUIRED), doc["source_id"])
            self.assertEqual(doc["issuer"], HOSE)
            self.assertIn(doc["ticker"], TICKERS)
            self.assertLess(doc["signed_date"], doc["official_ex_date"], doc["source_id"])
            self.assertLess(doc["official_ex_date"], doc["official_record_date"], doc["source_id"])
            self.assertTrue(WINDOW[0] <= doc["official_ex_date"] <= WINDOW[1], doc["source_id"])
            self.assertIn("TB-SGDHCM", doc["note"])

    def test_ratio_is_a_price_factor_only_for_stock_events(self):
        for doc in _docs():
            if "bằng tiền" in doc["event_type_verbatim"]:
                self.assertIsNone(doc["official_ratio"], doc["source_id"])
                self.assertIn("đồng", doc["official_ratio_text"])
            else:
                self.assertIsInstance(doc["official_ratio"], (int, float))
                self.assertGreater(doc["official_ratio"], 1.0)

    def test_search_log_covers_every_ticker_and_unknown_is_not_absence(self):
        man = _man()
        log = {row["ticker"]: row for row in man["tra_cuu"]}
        self.assertEqual(sorted(log), sorted(TICKERS))
        ids = {doc["source_id"]: doc["ticker"] for doc in man["source_documents"]}
        for ticker, row in log.items():
            self.assertIn(row["result"], ("FOUND", "UNKNOWN"))
            self.assertTrue(row["queries"], ticker)
            self.assertTrue(row["accessed_at"].endswith("Z"), ticker)
            if row["result"] == "FOUND":
                self.assertTrue(row["source_ids"], ticker)
                self.assertTrue(all(ids.get(s) == ticker for s in row["source_ids"]), ticker)
            else:
                self.assertEqual(row["source_ids"], [], ticker)
                self.assertNotIn(ticker, ids.values())
            self.assertNotIn("không có sự kiện", row["other"].lower())
        self.assertEqual(sorted(ids), sorted(s for row in log.values() for s in row["source_ids"]))
        self.assertEqual({t for t, r in log.items() if r["result"] == "UNKNOWN"}, {"LPB", "VPL"})

    def test_report_matches_manifest(self):
        text = REPORT.read_text(encoding="utf-8")
        for doc in _docs():
            line = next(row for row in text.splitlines() if doc["source_id"] in row and row.startswith("|"))
            self.assertIn(doc["ticker"], line)
            self.assertIn(doc["official_ex_date"], line)
            self.assertIn(doc["published_at"] or "CHƯA XÁC MINH", line)
            if doc["published_at"] is None:
                posted = doc["published_at_note"].split("HOSE đăng tin lúc ", 1)[1].split(" ", 1)[0]
                self.assertIn(f"HOSE đăng {posted}", line)
        for row in _man()["tra_cuu"]:
            if row["result"] == "UNKNOWN":
                self.assertTrue(any(row["ticker"] in r and "UNKNOWN" in r for r in text.splitlines()), row["ticker"])

    def test_violations_are_caught(self):
        docs = _docs()
        bad = [dict(d) for d in docs]
        bad[0]["published_at"] = bad[0]["signed_date"]
        self.assertTrue(h2.publication_errors(bad))
        bad = [dict(d) for d in docs]
        bad[0]["event_type"] = "stock_dividend"
        self.assertTrue(h2.classification_errors(bad))
        bad = [dict(d) for d in docs]
        bad[0]["url"] = bad[0]["url"].replace(".pdf", "x.pdf")
        self.assertTrue(metadata_errors(ROOT, bad))

    def test_flipping_one_byte_in_a_temp_copy_fails_and_repo_untouched(self):
        before = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT)
        docs = _docs()
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            for doc in docs:
                src = (ROOT / doc["path"]).parent
                shutil.copytree(src, root / src.relative_to(ROOT))
            self.assertEqual(h2.check_bytes(root, docs), [])
            self.assertEqual(metadata_errors(root, docs), [])
            pdf = root / docs[0]["path"]
            blob = bytearray(pdf.read_bytes())
            blob[150] ^= 0x01
            pdf.write_bytes(blob)
            news = root / pathlib.Path(docs[-1]["path"]).parent / f"hose_news_{docs[-1]['source_id'].split('-')[1]}.json"
            news.write_bytes(news.read_bytes() + b" ")
            self.assertTrue(any("sha256" in e for e in h2.check_bytes(root, docs)))
            self.assertTrue(any("không khớp note" in e for e in metadata_errors(root, docs)))
        self.assertEqual(before, subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT))


if __name__ == "__main__":
    unittest.main()
