"""Bằng chứng quyền cổ phiếu 11/2025–11/2026. Không mạng. Không ghi kho.

Ngày ký trên văn bản không phải ngày HOSE đăng. Khi chưa ghim metadata tin đã kiểm nội dung,
published_at phải null. Nguyên văn loại sự kiện giữ riêng; không gán mã kỹ thuật của engine và
không đưa văn bản vào chuỗi verified-adjusted chỉ vì có PDF hoặc ngày/hệ số trùng.
"""
import functools
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "evidence" / "corporate_actions" / "EVIDENCE_MANIFEST_2026H2.json"
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
    "published_at_note", "publication_evidence", "accessed_at", "effective_date",
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
    """published_at chỉ hợp lệ khi có metadata đã ghim, và không được là ngày ký."""
    errors = []
    for doc in docs:
        sid = doc.get("source_id")
        signed = doc.get("signed_date")
        if not isinstance(signed, str) or not DATE.fullmatch(signed):
            errors.append(f"{sid} thiếu signed_date")
            signed = None
        pub = doc.get("published_at")
        status = doc.get("published_at_status")
        evidence = doc.get("publication_evidence")
        if pub is None:
            if status != "CHUA_XAC_MINH":
                errors.append(f"{sid} published_at null nhưng không ghi CHUA_XAC_MINH")
            if evidence not in (None, ""):
                errors.append(f"{sid} có publication_evidence trong khi published_at null")
            continue
        day = str(pub)[:10]
        if signed and day == signed:
            errors.append(f"{sid} nhập ngày ký thay ngày công bố")
        ev_path = evidence if isinstance(evidence, str) else ""
        pinned = bool(ev_path) and ev_path != doc.get("path") and (pathlib.Path(root) / ev_path).is_file()
        if not pinned:
            errors.append(f"{sid} published_at không có metadata chính thức đã ghim và kiểm nội dung")
        if status == "CHUA_XAC_MINH":
            errors.append(f"{sid} vừa có published_at vừa ghi CHUA_XAC_MINH")
    return errors


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
            self.assertIsNone(doc["published_at"])
            self.assertIsNone(doc["event_type"])

    def test_published_at_is_unverified_and_not_the_signed_date(self):
        docs = _docs()
        self.assertEqual(publication_errors(docs), [])
        signed_as_published = [dict(doc) for doc in docs]
        signed_as_published[0]["published_at"] = signed_as_published[0]["signed_date"]
        signed_errors = publication_errors(signed_as_published)
        self.assertTrue(any("nhập ngày ký thay ngày công bố" in err for err in signed_errors))
        other_day = [dict(doc) for doc in docs]
        other_day[0]["published_at"] = "2020-01-01"
        other_errors = publication_errors(other_day)
        self.assertTrue(any("không có metadata chính thức đã ghim" in err for err in other_errors))
        vpb = next(doc for doc in docs if doc["source_id"] == "hose-2497757")
        self.assertEqual(vpb["signed_date"], "2026-09-16")
        self.assertIsNone(vpb["published_at"])
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
            self.assertIn("CHƯA XÁC MINH", line)
            self.assertIn(info["trade_date"], line)
            self.assertIn(f"lệch {info['offset']}", line)
            self.assertIn(ratio_cell(doc["official_ratio"], info["ratio"]), line)
            self.assertIn(info["status"], line)
            self.assertNotIn("DA_KIEM_CHUNG", line)
            self.assertIn(doc["source_id"], ids)

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
