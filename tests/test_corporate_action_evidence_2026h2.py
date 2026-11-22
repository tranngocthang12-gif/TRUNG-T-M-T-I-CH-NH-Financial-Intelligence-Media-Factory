"""Bằng chứng quyền cổ phiếu 11/2025–11/2026. Không mạng. Không ghi kho.

Ngày ký trên văn bản không phải ngày HOSE đăng. Khi chưa ghim metadata tin đã kiểm nội dung,
published_at phải null. Nguyên văn loại sự kiện giữ riêng; không gán mã kỹ thuật của engine và
không đưa văn bản vào chuỗi verified-adjusted chỉ vì có PDF hoặc ngày/hệ số trùng.
"""
import copy
import datetime as dt
import functools
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import tempfile
import unittest
import urllib.parse

from tools.publication_proof import proof_errors

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "evidence" / "corporate_actions" / "EVIDENCE_MANIFEST_2026H2.json"
FIRST_MANIFEST = ROOT / "data" / "evidence" / "corporate_actions" / "EVIDENCE_MANIFEST.json"
REPORT = ROOT / "reports" / "CORPORATE_ACTION_EVIDENCE_2026H2_20261119.md"

# 17 sự kiện cần ghim, nhận diện bằng mã và ngày không hưởng quyền trên văn bản.
# Không phải hệ số engine và không phải ngày công bố.
EVENTS = (
    ("TPB", "2026-10-02"),
    ("HDB", "2026-10-09"),
    ("TCB", "2026-10-29"),
    ("VIC", "2025-12-05"),
    ("POW", "2025-12-10"),
    ("CTG", "2025-12-17"),
    ("HDB", "2025-12-18"),
    ("HPG", "2026-05-25"),
    ("SSB", "2026-05-28"),
    ("ACB", "2026-06-15"),
    ("VJC", "2026-06-16"),
    ("VHM", "2026-08-06"),
    ("MBB", "2026-08-11"),
    ("SSI", "2026-08-17"),
    ("BID", "2026-08-17"),
    ("VIB", "2026-09-10"),
    ("VPB", "2026-09-24"),
)
TECHNICAL = {"stock_split", "stock_dividend"}
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REQUIRED = (
    "source_id", "url", "issuer", "signed_date", "published_at", "published_at_status",
    "published_at_note", "publication_evidence", "publication_evidence_sha256", "publication_media_evidence",
    "publication_media_sha256", "accessed_at", "effective_date",
    "path", "sha256", "bytes", "ticker", "event_type", "event_type_status",
    "event_type_verbatim", "event_type_note", "official_ex_date", "official_record_date",
    "official_ratio", "official_ratio_text", "note",
)


def _docs(path=MANIFEST):
    return json.loads(path.read_text(encoding="utf-8"))["source_documents"]


def fmt(value):
    """Số thập phân ngắn, dấu phẩy, đúng giá trị float đã đọc — không làm tròn thêm về 6 chữ số."""
    text = format(float(value), ".12f").rstrip("0").rstrip(".")
    return text.replace(".", ",")


def ratio_cell(official, engine):
    left, right = fmt(official), fmt(engine)
    if abs(float(official) - float(engine)) <= 1e-12:
        return f"{left} = {right}"
    return f"{left} khác {right}"


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


def publication_errors(docs, root=ROOT):
    """published_at chỉ hợp lệ khi tools/publication_proof.proof_errors đạt (QĐ-9, ADR-0016): metadata HOSE đã ghim chứng
    minh đúng ngày đó, kể cả khi trùng ngày ký. Ngày gõ tay, hay suy từ ngày ký, tên tệp, ngày hưởng quyền đều bị từ chối."""
    errors = []
    for doc in docs:
        sid = doc.get("source_id")
        signed = doc.get("signed_date")
        if not isinstance(signed, str) or not DATE.fullmatch(signed):
            errors.append(f"{sid} thiếu signed_date")
        pub = doc.get("published_at")
        status = doc.get("published_at_status")
        if pub is None:
            if status != "CHUA_XAC_MINH":
                errors.append(f"{sid} published_at null nhưng không ghi CHUA_XAC_MINH")
            if doc.get("publication_evidence") not in (None, ""):
                errors.append(f"{sid} có publication_evidence trong khi published_at null")
            continue
        if status != "DA_XAC_MINH":
            errors.append(f"{sid} có published_at nhưng không ghi DA_XAC_MINH")
        errors += proof_errors(doc, root)
    return errors


def posted_iso(seconds):
    """Giây Unix → ISO 8601 theo phép đổi chuẩn của Unix (UTC), không gắn múi giờ (luật D1)."""
    return dt.datetime.fromtimestamp(seconds, dt.timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds")


def hose_metadata_errors(doc, root=ROOT):
    """Ràng buộc ngày công bố của MỘT bản gốc với metadata HOSE đã ghim cạnh nó, cho cả hai lược đồ manifest.

    Đòi: JSON tin và JSON danh sách tệp đính kèm có mặt cạnh bản gốc, sha256 và số byte khớp note; published_at bằng đúng
    data.postedDate đổi theo UTC (QĐ-9: kể cả khi trùng ngày ký); trường chứng cứ trỏ đúng hai tệp đó; và
    tools/publication_proof.proof_errors đạt."""
    errors = []
    sid = str(doc.get("source_id"))
    nid = sid.split("-", 1)[1] if sid.startswith("hose-") else ""
    folder = pathlib.Path(doc["path"]).parent
    news_rel, media_rel = str(folder / f"hose_news_{nid}.json"), str(folder / f"hose_mediafiles_{nid}.json")
    note = doc.get("published_at_note") or ""
    blobs = {}
    for rel in (news_rel, media_rel):
        p = pathlib.Path(root) / rel
        if not p.is_file():
            errors.append(f"{sid} thiếu {rel}")
            continue
        blobs[rel] = p.read_bytes()
        if f"{len(blobs[rel])} byte, sha256 {hashlib.sha256(blobs[rel]).hexdigest()}" not in note:
            errors.append(f"{sid} sha256 hoặc số byte của {pathlib.Path(rel).name} không khớp note")
    if len(blobs) < 2:
        return errors
    try:
        news = json.loads(blobs[news_rel])["data"]
        files = json.loads(blobs[media_rel])["data"]["list"]
    except (ValueError, KeyError, TypeError):
        return errors + [f"{sid} JSON metadata hỏng"]
    if str(news.get("id")) != nid or news.get("code") != doc.get("ticker"):
        errors.append(f"{sid} JSON tin có id {news.get('id')} mã {news.get('code')}, không khớp bản gốc")
    want = urllib.parse.unquote(str(doc.get("url", "")).split("staticfile.hsx.vn", 1)[-1])
    if [str(m.get("filePath", "")).replace("~", "", 1) for m in files].count(want) != 1:
        errors.append(f"{sid} danh sách tệp đính kèm không có đúng một tệp trùng url bản gốc")
    posted = news.get("postedDate")
    if isinstance(posted, bool) or not isinstance(posted, int):
        return errors + [f"{sid} JSON tin không có data.postedDate dạng số"]
    iso = posted_iso(posted)
    expected = iso
    if doc.get("published_at") != expected:
        errors.append(f"{sid} published_at {doc.get('published_at')!r} khác giá trị suy từ data.postedDate {expected!r}")
    if doc.get("published_at_status") != ("DA_XAC_MINH" if expected else "CHUA_XAC_MINH"):
        errors.append(f"{sid} published_at_status không khớp published_at")
    if iso not in note:
        errors.append(f"{sid} note không ghi giờ đăng {iso}")
    if "publication_evidence" in doc:                                   # lược đồ 2026H2
        if (doc["publication_evidence"], doc.get("publication_media_evidence")) != (news_rel, media_rel):
            errors.append(f"{sid} publication_evidence hoặc publication_media_evidence không trỏ đúng JSON đã ghim")
    else:                                                                # lược đồ manifest đầu
        ev = doc.get("published_at_evidence")
        good = (isinstance(ev, dict) and ev.get("path") == news_rel and ev.get("media_path") == media_rel
                and ev.get("field") == "data.postedDate" and ev.get("accessed_at"))
        if not good:
            errors.append(f"{sid} published_at_evidence không khớp JSON đã ghim")
    return errors + proof_errors(doc, root)


def all_twenty_docs():
    return _docs(FIRST_MANIFEST) + _docs(MANIFEST)


def classification_errors(docs):
    """Nguyên văn HOSE không được ghi vào trường loại kỹ thuật mà cổng verified-adjusted đọc."""
    errors = []
    for doc in docs:
        sid = doc.get("source_id")
        kind = doc.get("event_type")
        if kind is not None:
            errors.append(f"{sid} event_type phải để trống; nguyên văn nằm ở event_type_verbatim")
        if kind in TECHNICAL:
            errors.append(f"{sid} gán loại kỹ thuật chưa xác minh")
        if doc.get("event_type_status") != "CHUA_XAC_MINH":
            errors.append(f"{sid} event_type_status phải là CHUA_XAC_MINH")
        text = doc.get("event_type_verbatim")
        if not isinstance(text, str) or not text.strip() or text.strip() in TECHNICAL:
            errors.append(f"{sid} mất nguyên văn loại sự kiện HOSE")
    return errors


@functools.lru_cache(maxsize=1)
def _market():
    """Đọc kho và dựng sự kiện engine trong bộ nhớ. Không ghi đĩa."""
    import pandas as pd

    from engine import adjust, data

    store = data.load_store()
    raw = store.pivot(index="date", columns="ticker", values="close").sort_index()
    observed = store.pivot(index="date", columns="ticker", values="observed_at").sort_index()
    events = adjust.build_events(raw, observed, adjust.load_manual(), adjust.load_yahoo())
    return raw, events


def engine_rows():
    """Một dòng cổ phiếu của engine cho đúng ngày không hưởng quyền của từng văn bản."""
    import pandas as pd

    from engine import adjust

    raw, events = _market()
    stock = events[events["type"].isin(adjust.STOCK)]
    found = {}
    for doc in _docs():
        key = (doc["ticker"], doc["official_ex_date"])
        hit = stock[(stock.ticker == key[0]) & (stock.ex_date == pd.Timestamp(key[1]))]
        if len(hit) != 1:
            found[key] = None
            continue
        row = hit.iloc[0]
        sessions = raw[key[0]].dropna().index
        pos = int(sessions.searchsorted(pd.Timestamp(key[1])))
        trade = row.trade_date
        offset = int(sessions.get_loc(trade)) - pos
        found[key] = {
            "type": str(row.type),
            "ratio": float(row.ratio),
            "status": str(row.status),
            "source": str(row.source),
            "trade_date": str(trade.date()),
            "offset": offset,
        }
    return found


class CorporateActionEvidence2026H2Tests(unittest.TestCase):
    def test_manifest_files_hash_and_keys(self):
        docs = _docs()
        self.assertEqual(len(docs), 17)
        self.assertEqual(check_bytes(ROOT, docs), [])
        for doc in docs:
            self.assertTrue(doc["url"])
            self.assertTrue(doc["issuer"])
            self.assertRegex(doc["signed_date"], r"^\d{4}-\d{2}-\d{2}$")
            self.assertLess(doc["signed_date"], doc["official_ex_date"], doc["source_id"])
            self.assertRegex(doc["official_ex_date"], r"^\d{4}-\d{2}-\d{2}$")
            self.assertIsInstance(doc["official_ratio"], (int, float))
            self.assertEqual(publication_errors([doc]), [], doc["source_id"])
            self.assertIsNone(doc["event_type"])

    def test_published_at_is_unverified_and_not_the_signed_date(self):
        docs = _docs()
        self.assertEqual(publication_errors(docs), [])
        signed_as_published = [dict(doc) for doc in docs]
        signed_as_published[0]["published_at"] = signed_as_published[0]["signed_date"]
        signed_errors = publication_errors(signed_as_published)
        self.assertTrue(any("khác data.postedDate" in err for err in signed_errors))
        other_day = [dict(doc) for doc in docs]
        other_day[0]["published_at"] = "2020-01-01"
        other_day[0]["publication_evidence"] = None  # một ngày không kèm metadata đã ghim
        other_errors = publication_errors(other_day)
        self.assertTrue(any("thiếu đường dẫn JSON tin HOSE" in err for err in other_errors))
        # QĐ-9: ngày HOSE đăng trùng ngày ký được nhận khi máy kiểm được từ metadata đã ghim.
        same_day = [doc for doc in docs if doc["published_at"][:10] == doc["signed_date"]]
        self.assertEqual(sorted(d["source_id"] for d in same_day),
                         ["hose-2423183", "hose-2423661", "hose-2468381", "hose-2501920", "hose-2507504"])
        self.assertEqual(publication_errors(same_day), [])
        vpb = next(doc for doc in docs if doc["source_id"] == "hose-2497757")
        self.assertEqual(vpb["signed_date"], "2026-09-16")
        self.assertEqual(publication_errors([vpb]), [])
        self.assertIn("2026-09-16", vpb["published_at_note"])
        self.assertIn("2026-09-17", vpb["published_at_note"])
        self.assertIn("Không chọn", vpb["published_at_note"])

    def test_verbatim_type_is_not_a_verified_technical_type(self):
        docs = _docs()
        self.assertEqual(classification_errors(docs), [])
        forged = [dict(doc) for doc in docs]
        forged[0]["event_type"] = "stock_dividend"
        errors = classification_errors(forged)
        self.assertTrue(any("loại kỹ thuật" in err for err in errors))
        for doc in docs:
            self.assertNotIn(doc["event_type_verbatim"], TECHNICAL)

    def test_each_document_is_exactly_one_of_seventeen_events(self):
        docs = _docs()
        got = [(doc["ticker"], doc["official_ex_date"]) for doc in docs]
        self.assertEqual(sorted(got), sorted(EVENTS))
        self.assertEqual(len(got), len(set(got)))

    def test_report_quotes_the_engine_read_not_the_order_list(self):
        text = REPORT.read_text(encoding="utf-8")
        self.assertNotIn("1,446366", text)
        rows = engine_rows()
        ids = {doc["source_id"] for doc in _docs()}
        self.assertEqual(len(rows), 17)
        for doc in _docs():
            key = (doc["ticker"], doc["official_ex_date"])
            info = rows[key]
            self.assertIsNotNone(info, key)
            line = next(row for row in text.splitlines() if f"{key[0]} {key[1]}" in row)
            self.assertIn(doc["source_id"], line)
            if doc["published_at"] is None:
                self.assertIn("CHƯA XÁC MINH", line)
                self.assertNotIn("DA_KIEM_CHUNG", line)
            else:
                self.assertIn(doc["published_at"], line)
            self.assertIn(info["trade_date"], line)
            self.assertIn(f"lệch {info['offset']}", line)
            self.assertIn(ratio_cell(doc["official_ratio"], info["ratio"]), line)
            self.assertIn(info["status"], line)
            self.assertIn(doc["source_id"], ids)

    def test_report_on_disk_equals_tool_output(self):
        """Báo cáo do tools/corporate_action_evidence_2026h2.py sinh tất định; tệp trên đĩa phải bằng đúng đầu ra công cụ."""
        import importlib.util

        spec = importlib.util.spec_from_file_location("_ca_2026h2_tool", ROOT / "tools" / "corporate_action_evidence_2026h2.py")
        tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tool)
        text = tool.render()
        self.assertEqual(REPORT.read_text(encoding="utf-8"), text)
        self.assertTrue(text.startswith("> Tệp do `tools/corporate_action_evidence_2026h2.py` sinh tất định"))
        self.assertEqual(text, tool.render())
        for old in ("Cả 17 văn bản chưa có metadata", "Ghi nhận trước nói tin HOSE"):
            self.assertNotIn(old, text)
        docs = _docs()
        n_pub = sum(1 for d in docs if d["published_at"])
        self.assertIn(f"Trong {len(docs)} văn bản, {n_pub} văn bản có ngày công bố", text)
        for doc in docs:
            line = next(row for row in text.splitlines() if row.startswith(f"| {doc['ticker']} {doc['official_ex_date']} |"))
            self.assertTrue(line.rstrip().endswith(f"| {doc['note']} |"), doc["source_id"])

    def test_pdf_and_matching_numbers_do_not_enter_verified_chain(self):
        import pandas as pd

        from engine import verified_adjust as va

        raw, events = _market()
        docs = _docs()
        checked = va.verify_events(events, raw, docs, evidence_root=ROOT, as_of=raw.index.max())
        # Có PDF, ngày và hệ số trùng chưa đủ: bản gốc chưa có published_at thì dòng ghép với nó luôn bị cách ly.
        unpublished = {doc["source_id"] for doc in docs if doc["published_at"] is None}
        for row in checked[checked["evidence_id"].isin(unpublished)].itertuples(index=False):
            self.assertFalse(bool(row.in_verified_chain), (row.ticker, row.evidence_id))
            self.assertTrue(row.verify_state.startswith("CACH_LY_"), (row.ticker, row.verify_state))
        by_event = {(doc["ticker"], doc["official_ex_date"]): doc for doc in docs}
        for ticker, day in EVENTS:
            hit = checked[(checked.ticker == ticker) & (checked.ex_date == pd.Timestamp(day))
                          & checked.type.isin(va.STOCK)]
            self.assertEqual(len(hit), 1, (ticker, day))
            if by_event[(ticker, day)]["published_at"] is None:
                self.assertFalse(bool(hit.iloc[0].in_verified_chain), (ticker, day))

    def test_all_twenty_publication_dates_are_bound_to_pinned_hose_metadata(self):
        docs = all_twenty_docs()
        self.assertEqual(len(docs), 20)
        for doc in docs:
            self.assertEqual(hose_metadata_errors(doc), [], doc["source_id"])
        self.assertEqual(sum(1 for d in docs if d["published_at"]), 20)

    def test_publication_binding_catches_independent_mutations(self):
        """Mỗi kiểu sửa sai dưới đây phải bị bắt bởi hose_metadata_errors, không chỉ bởi việc tệp có tồn tại."""
        import importlib.util

        docs = all_twenty_docs()
        published = [d for d in docs if d["published_at"]]
        same_day = [d for d in docs if d["published_at"][:10] == d["signed_date"]]
        self.assertEqual(len(same_day), 5)
        # 1. Sửa riêng published_at, giữ đường dẫn chứng cứ và DA_XAC_MINH.
        for doc in published:
            bad = copy.deepcopy(doc)
            bad["published_at"] = bad["published_at"][:-2] + ("00" if bad["published_at"][-2:] != "00" else "01")
            self.assertTrue(hose_metadata_errors(bad), doc["source_id"])
        # 2. Sửa ngày trong manifest RỒI tái sinh báo cáo: báo cáo khớp công cụ nhưng ràng buộc vẫn bắt.
        spec = importlib.util.spec_from_file_location("_ca_2026h2_tool_b", ROOT / "tools" / "corporate_action_evidence_2026h2.py")
        tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tool)
        h2 = [copy.deepcopy(d) for d in _docs()]
        target = next(d for d in h2 if d["published_at"])
        target["published_at"] = "2020-01-02T03:04:05"
        rows = {(d["ticker"], d["official_ex_date"]): None for d in h2}
        self.assertIn("2020-01-02T03:04:05", tool.render(h2, rows))
        self.assertTrue(hose_metadata_errors(target))
        # 3. QĐ-9: bản HOSE đăng cùng ngày ký được nhận theo đúng giờ đăng; ngày ký gõ tay vẫn bị từ chối.
        for doc in same_day:
            self.assertEqual(hose_metadata_errors(doc), [], doc["source_id"])
            bad = copy.deepcopy(doc)
            bad["published_at"] = doc["signed_date"] + "T00:00:00"
            self.assertTrue(hose_metadata_errors(bad), doc["source_id"])
        # 4a. Trạng thái hoặc đường dẫn chứng cứ 2026H2 lệch với published_at, dù ngày đúng.
        h2_pub = next(d for d in _docs() if d["published_at"])
        for key, val in (("published_at_status", "CHUA_XAC_MINH"), ("publication_evidence", h2_pub["path"]),
                         ("publication_evidence", None), ("publication_evidence_sha256", "0" * 64),
                         ("publication_media_evidence", None), ("publication_media_sha256", "0" * 64)):
            bad = copy.deepcopy(h2_pub)
            bad[key] = val
            self.assertTrue(hose_metadata_errors(bad), (key, val))
        # 4. Chứng cứ manifest đầu trỏ sai hoặc sai sha256.
        first = next(d for d in _docs(FIRST_MANIFEST) if d["published_at"])
        for key, val in (("sha256", "0" * 64), ("path", first["path"]), ("field", "data.createdDate"),
                         ("media_sha256", "0" * 64), ("media_path", first["path"])):
            bad = copy.deepcopy(first)
            bad["published_at_evidence"][key] = val
            self.assertTrue(hose_metadata_errors(bad), key)
        # 5. Một byte của metadata bị sửa, hoặc JSON bị thay bằng tin khác (trên bản sao tạm, kho không đổi).
        before = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT)
        a, b = published[0], published[1]
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            for d in (a, b):
                shutil.copytree(ROOT / pathlib.Path(d["path"]).parent, root / pathlib.Path(d["path"]).parent)
            self.assertEqual(hose_metadata_errors(a, root), [])
            for name in (f"hose_news_{a['source_id'][5:]}.json", f"hose_mediafiles_{a['source_id'][5:]}.json"):
                f = root / pathlib.Path(a["path"]).parent / name
                orig = f.read_bytes()
                blob = bytearray(orig)
                blob[len(blob) // 2] ^= 0x01
                f.write_bytes(bytes(blob))
                self.assertTrue(hose_metadata_errors(a, root), name)
                f.write_bytes(orig)
            # JSON vẫn hợp lệ, cùng id và ngày, chỉ khác byte: chỉ kiểm sha256/số byte bắt được.
            news_a = root / pathlib.Path(a["path"]).parent / f"hose_news_{a['source_id'][5:]}.json"
            orig = news_a.read_bytes()
            news_a.write_bytes(orig + b"\n")
            self.assertTrue(any("không khớp note" in e for e in hose_metadata_errors(a, root)))
            news_a.write_bytes(orig)
            # Danh sách đính kèm trỏ PDF khác; note được sửa theo sha256 mới để chỉ còn lỗi trỏ PDF.
            media_a = root / pathlib.Path(a["path"]).parent / f"hose_mediafiles_{a['source_id'][5:]}.json"
            m_orig = media_a.read_bytes()
            mj = json.loads(m_orig)
            mj["data"]["list"][0]["filePath"] = "~/Uploads/UploadDocuments/1/khac.pdf"
            m_new = json.dumps(mj, ensure_ascii=False).encode()
            media_a.write_bytes(m_new)
            moved = copy.deepcopy(a)
            moved["published_at_note"] = a["published_at_note"].replace(
                f"{len(m_orig)} byte, sha256 {hashlib.sha256(m_orig).hexdigest()}",
                f"{len(m_new)} byte, sha256 {hashlib.sha256(m_new).hexdigest()}")
            if "publication_media_sha256" in moved:
                moved["publication_media_sha256"] = hashlib.sha256(m_new).hexdigest()
            else:
                moved["published_at_evidence"]["media_sha256"] = hashlib.sha256(m_new).hexdigest()
            errs = hose_metadata_errors(moved, root)
            self.assertTrue(errs and all("đính kèm" in e for e in errs), errs)
            media_a.write_bytes(m_orig)
            other = (root / pathlib.Path(b["path"]).parent / f"hose_news_{b['source_id'][5:]}.json").read_bytes()
            (root / pathlib.Path(a["path"]).parent / f"hose_news_{a['source_id'][5:]}.json").write_bytes(other)
            errs = hose_metadata_errors(a, root)
            self.assertTrue(any("không khớp bản gốc" in e for e in errs), errs)
        self.assertEqual(before, subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT))

    def test_qd9_proof_rejects_each_case(self):
        """QĐ-9 (gói giao số 2, C5 mục 6): mỗi trường hợp sau phải ra lỗi từ tools/publication_proof.proof_errors."""
        docs = all_twenty_docs()
        a = next(d for d in _docs() if d["published_at"][:10] == d["signed_date"])   # một bản đăng trùng ngày ký
        b = next(d for d in _docs() if d["source_id"] != a["source_id"])
        self.assertEqual(proof_errors(a, ROOT), [])
        # 1. Ngày gõ tay khác JSON.
        self.assertTrue(proof_errors({**a, "published_at": a["published_at"][:-1] + "9"}, ROOT))
        # 4. Danh sách đính kèm trỏ tới PDF khác (url bản gốc đổi).
        self.assertTrue(any("đính kèm" in e for e in proof_errors({**a, "url": b["url"]}, ROOT)))
        # 5. Ngày đăng sớm hơn ngày ký.
        later = (dt.date.fromisoformat(a["signed_date"]) + dt.timedelta(days=1)).isoformat()
        self.assertTrue(any("sớm hơn ngày ký" in e for e in proof_errors({**a, "signed_date": later}, ROOT)))
        # 6. Ngày đăng cộng 7 giờ không sớm hơn ngày không hưởng quyền.
        shifted = (dt.datetime.fromisoformat(a["published_at"]) + dt.timedelta(hours=7)).date().isoformat()
        self.assertTrue(any("cộng 7 giờ" in e for e in proof_errors({**a, "official_ex_date": shifted}, ROOT)))
        day_after = (dt.date.fromisoformat(shifted) + dt.timedelta(days=1)).isoformat()
        self.assertEqual(proof_errors({**a, "official_ex_date": day_after}, ROOT), [])
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            for d in (a, b):
                shutil.copytree(ROOT / pathlib.Path(d["path"]).parent, root / pathlib.Path(d["path"]).parent)
            self.assertEqual(proof_errors(a, root), [])
            news = root / a["publication_evidence"]
            orig = news.read_bytes()
            # 2. JSON bị đổi một byte.
            flipped = bytearray(orig)
            flipped[len(flipped) // 2] ^= 0x01
            news.write_bytes(bytes(flipped))
            self.assertTrue(any("sha256" in e for e in proof_errors(a, root)))
            # 3. JSON của tin khác (sha256 khai theo tệp mới, nên chỉ còn lỗi id/mã).
            other = (root / b["publication_evidence"]).read_bytes()
            news.write_bytes(other)
            errs = proof_errors({**a, "publication_evidence_sha256": hashlib.sha256(other).hexdigest()}, root)
            self.assertTrue(errs and all("id" in e or "mã" in e or "data.postedDate" in e for e in errs), errs)
            self.assertTrue(any("khác số trong source_id" in e for e in errs))
            # JSON cùng id nhưng sai mã chứng khoán (sha256 khai theo tệp mới).
            nj = json.loads(orig)
            nj["data"]["code"] = "XXX"
            wrong = json.dumps(nj, ensure_ascii=False).encode()
            news.write_bytes(wrong)
            errs = proof_errors({**a, "publication_evidence_sha256": hashlib.sha256(wrong).hexdigest()}, root)
            self.assertEqual(len(errs), 1)
            self.assertIn("khác ticker", errs[0])
            news.write_bytes(orig)
        # Chứng cứ trỏ vào chính PDF bản gốc (kể cả khi sha256 khai khớp PDF) bị từ chối với lý do riêng.
        pdf_sha = hashlib.sha256((ROOT / a["path"]).read_bytes()).hexdigest()
        errs = proof_errors({**a, "publication_evidence": a["path"], "publication_evidence_sha256": pdf_sha}, ROOT)
        self.assertTrue(any("chính bản gốc PDF" in e for e in errs), errs)
        self.assertEqual(len(docs), 20)

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
