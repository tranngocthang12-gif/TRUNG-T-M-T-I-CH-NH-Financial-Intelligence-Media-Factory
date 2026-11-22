"""Sự kiện quyền BSR, LPB, MCH, TCX, VPL từ 2026-06-01 (LỆNH D2b). Không mạng. Không ghi kho.

Dùng lại các hàm kiểm của tests/test_corporate_action_evidence_2026h2.py (sha256 và số byte, luật published_at, luật
event_type) cho manifest mới. Mã không tìm thấy thông báo phải ghi UNKNOWN kèm truy vấn đã tra, không ghi "không có sự kiện".
"""
import datetime as dt
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


def published_from_posted(seconds, signed_date):
    """Luật D1: giây Unix → ISO 8601 theo phép đổi chuẩn của Unix (UTC), không gắn múi giờ; phần ngày trùng signed_date → None."""
    iso = dt.datetime.fromtimestamp(seconds, dt.timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds")
    return None if iso[:10] == signed_date else iso


def publication_binding_errors(root, docs):
    """published_at, published_at_status và publication_evidence phải suy ra đúng từ data.postedDate của JSON tin đã ghim."""
    errors = []
    for doc in docs:
        sid, nid = doc["source_id"], doc["source_id"].split("-", 1)[1]
        rel = str(pathlib.Path(doc["path"]).parent / f"hose_news_{nid}.json")
        p = pathlib.Path(root) / rel
        if not p.is_file():
            errors.append(f"{sid} thiếu JSON tin")
            continue
        posted = json.loads(p.read_bytes())["data"].get("postedDate")
        if not isinstance(posted, int):
            errors.append(f"{sid} JSON tin không có data.postedDate")
            continue
        want = published_from_posted(posted, doc["signed_date"])
        if doc["published_at"] != want:
            errors.append(f"{sid} published_at {doc['published_at']!r} khác giá trị suy từ data.postedDate {want!r}")
        status, ev = ("DA_XAC_MINH", rel) if want else ("CHUA_XAC_MINH", None)
        if doc["published_at_status"] != status or doc["publication_evidence"] != ev:
            errors.append(f"{sid} trạng thái hoặc publication_evidence không khớp published_at")
    return errors


def snapshot_errors(root, man):
    """Trang kết quả tra cứu đã ghim: đúng sha256/số byte; tin theo mã tải đủ mọi trang; mã FOUND có mặt trong trang đã ghim."""
    errors = []
    for row in man["tra_cuu"]:
        t1 = []
        for snap in row.get("snapshots") or []:
            p = pathlib.Path(root) / snap["path"]
            if not p.is_file():
                errors.append(f"{row['ticker']} thiếu {snap['path']}")
                continue
            blob = p.read_bytes()
            if len(blob) != snap["bytes"] or hashlib.sha256(blob).hexdigest() != snap["sha256"]:
                errors.append(f"{snap['path']} sha256 hoặc số byte lệch")
                continue
            data = json.loads(blob)["data"]
            if data["paging"]["totalCount"] != snap["totalCount"] or len(data["list"]) != snap["items"]:
                errors.append(f"{snap['path']} số mục khác manifest")
            if "/1?" in snap["url"]:
                t1.append(data)
        if not t1:
            errors.append(f"{row['ticker']} không có trang tin theo mã nào được ghim")
            continue
        total, pages = t1[0]["paging"]["totalCount"], t1[0]["paging"]["totalPages"]
        if len(t1) != pages or sum(len(d["list"]) for d in t1) != total:
            errors.append(f"{row['ticker']} chưa tải đủ trang tin theo mã ({len(t1)}/{pages} trang)")
        ids = {f"hose-{x['id']}" for d in t1 for x in d["list"]}
        missing = set(row["source_ids"]) - ids
        if missing:
            errors.append(f"{row['ticker']} bản gốc {sorted(missing)} không có trong trang tin đã ghim")
    return errors


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
        self.assertEqual(publication_binding_errors(ROOT, docs), [])
        self.assertEqual(snapshot_errors(ROOT, _man()), [])
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


# ---------- Bản chấm L-09 vòng 1 (PR #78): luật múi giờ, ràng buộc published_at với JSON gốc, trang tra cứu ----------

class PublicationRuleTests(unittest.TestCase):
    def test_rule_uses_the_unix_utc_date_at_day_boundaries(self):
        day = dt.datetime(2026, 7, 31, tzinfo=dt.timezone.utc)
        s = lambda d: int((day + d).timestamp())  # noqa: E731
        self.assertIsNone(published_from_posted(s(dt.timedelta(0)), "2026-07-31"))
        self.assertIsNone(published_from_posted(s(dt.timedelta(hours=23, minutes=59, seconds=59)), "2026-07-31"))
        self.assertEqual(published_from_posted(s(dt.timedelta(days=1)), "2026-07-31"), "2026-08-01T00:00:00")
        # 17:00 UTC là 00:00 giờ Việt Nam ngày hôm sau: theo luật D1 vẫn là cùng ngày ký, nên để trống (thận trọng).
        self.assertIsNone(published_from_posted(s(dt.timedelta(hours=17)), "2026-07-31"))
        self.assertEqual(published_from_posted(s(dt.timedelta(hours=-1)), "2026-07-31"), "2026-07-30T23:00:00")

    def test_mch_is_same_day_under_the_d1_rule(self):
        mch = next(d for d in _docs() if d["ticker"] == "MCH")
        posted = json.loads((ROOT / pathlib.Path(mch["path"]).parent / "hose_news_2485688.json").read_bytes())["data"]["postedDate"]
        self.assertEqual(posted, 1785522230)
        self.assertIsNone(published_from_posted(posted, mch["signed_date"]))
        self.assertIsNone(mch["published_at"])
        self.assertIn("2026-07-31T18:23:50", mch["published_at_note"])

    def test_editing_only_the_manifest_date_is_caught(self):
        docs = _docs()
        for i, doc in enumerate(docs):
            bad = [dict(d) for d in docs]
            bad[i]["published_at"] = "2026-06-30T18:10:56" if doc["published_at"] else "2026-08-01T01:23:50"
            if doc["published_at"] is None:
                bad[i].update(published_at_status="DA_XAC_MINH",
                              publication_evidence=str(pathlib.Path(doc["path"]).parent / f"hose_news_{doc['source_id'][5:]}.json"))
            self.assertTrue(publication_binding_errors(ROOT, bad), doc["source_id"])
        bad = [dict(d) for d in docs]
        first = next(i for i, d in enumerate(bad) if d["published_at"])
        bad[first]["publication_evidence"] = bad[first]["path"]
        self.assertTrue(publication_binding_errors(ROOT, bad))

    def test_snapshot_checks_catch_missing_pages_and_tampering(self):
        man = _man()
        broken = json.loads(json.dumps(man))
        lpb = next(r for r in broken["tra_cuu"] if r["ticker"] == "LPB")
        lpb["snapshots"] = [x for x in lpb["snapshots"] if "pageIndex=2" not in x["url"]]
        self.assertTrue(any("chưa tải đủ trang" in e for e in snapshot_errors(ROOT, broken)))
        broken = json.loads(json.dumps(man))
        broken["tra_cuu"][0]["snapshots"][0]["sha256"] = "0" * 64
        self.assertTrue(any("sha256" in e for e in snapshot_errors(ROOT, broken)))
        broken = json.loads(json.dumps(man))
        broken["tra_cuu"][0]["source_ids"] = ["hose-1"]
        self.assertTrue(any("không có trong trang tin" in e for e in snapshot_errors(ROOT, broken)))

    def test_unknown_tickers_have_no_rights_event_in_the_window_on_the_pinned_calendar(self):
        for row in _man()["tra_cuu"]:
            cal = [x for x in row["snapshots"] if "/3?" in x["url"]]
            self.assertEqual(len(cal), 1, row["ticker"])
            items = json.loads((ROOT / cal[0]["path"]).read_bytes())["data"]["list"]
            days = [dt.datetime.fromtimestamp(x["postedDate"], dt.timezone.utc).date().isoformat() for x in items]
            in_window = [d for d in days if d >= WINDOW[0]]
            if row["result"] == "UNKNOWN":
                self.assertEqual(in_window, [], row["ticker"])
            else:
                self.assertTrue(in_window, row["ticker"])
