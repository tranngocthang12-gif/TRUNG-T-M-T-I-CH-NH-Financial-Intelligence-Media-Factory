"""L-01: ghim tệp gốc riêng khỏi text.md. Hash khớp không đủ để ghi SOURCED (ADR-0012)."""
import hashlib, json, pathlib, shutil, sys, tempfile, textwrap, unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from engine import knowledge_notes as kn  # noqa: E402

TEXT = textwrap.dedent("""\
    [p1]
    Điều 1. Phạm vi điều chỉnh

    Luật này quy định về nội dung công tác kế toán.

    [p2]
    Điều 4. Nhiệm vụ kế toán

    Thu thập, xử lý thông tin, số liệu kế toán.
    """)
PDF = b"%PDF-1.4 fake-original-not-the-transcript\n"
KNOWN = kn.KNOWN_ORIGINALS["luat_ke_toan_88_2015"]


class OriginalBindingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        (self.tmp / "governance").mkdir()
        shutil.copy(ROOT / "governance" / "DATA_SOURCES.yaml", self.tmp / "governance")
        self.doc = "van_ban_mau"
        self.dir = self.tmp / "library" / "sources" / self.doc
        self.dir.mkdir(parents=True)
        (self.dir / "text.md").write_text(TEXT, encoding="utf-8")
        (self.dir / "goc.pdf").write_bytes(PDF)
        self.text_b = (self.dir / "text.md").read_bytes()
        self.entry = self._pin(self.doc, self.text_b, PDF, "goc.pdf", pages=2)
        self._manifest({self.doc: self.entry})

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _pin(self, doc, text_b, pdf, name, pages=None, cross=True):
        e = {"sha256": hashlib.sha256(text_b).hexdigest(), "bytes": len(text_b), "issuer": "Quốc hội",
             "issued_on": "2015-11-20", "accessed_on": "2026-11-18", "source_url": "https://vbpl.vn/x",
             "data_source": "Công báo / Cổng TTĐT Chính phủ", "legal_status": "văn bản quy phạm, không bảo hộ",
             "license": "public-domain-vn-law", "kind": "LAW", "effective_from": "2017-01-01",
             "effective_to": None, "superseded_by": None,
             "text_sha256": hashlib.sha256(text_b).hexdigest(), "text_bytes": len(text_b),
             "original_sha256": hashlib.sha256(pdf).hexdigest(), "original_bytes": len(pdf),
             "original_path": f"library/sources/{doc}/{name}"}
        if cross:
            e["crosscheck"] = kn.page_crosscheck(text_b.decode("utf-8"))
        return e

    def _manifest(self, files):
        (self.tmp / "library" / "SOURCE_MANIFEST.json").write_text(
            json.dumps({"files": files}, ensure_ascii=False), encoding="utf-8")

    def _queue(self, status, doc=None):
        (self.tmp / "library" / "reading_queue.yaml").write_text(json.dumps({"items": [
            {"doc_id": doc or self.doc, "status": status}]}), encoding="utf-8")

    def _errs(self):
        return kn.check_library(self.tmp)[0]

    def _witness(self, entry, text, checker="Owner"):
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        cc = json.loads(json.dumps(entry["crosscheck"]))
        cc["pdf_check"] = {"checker": checker, "result": "MATCH",
                           "pages_checked": [p["page"] for p in cc["pages"]],
                           "evidence": "Đối chiếu từng trang text.md với PDF gốc, gồm các ô bảng.",
                           "text_sha256": digest, "original_sha256": entry["original_sha256"]}
        return dict(entry, sha256=digest, bytes=len(text.encode("utf-8")), text_sha256=digest,
                    text_bytes=len(text.encode("utf-8")), crosscheck=cc)

    def test_separate_pins_allow_sourced_only_after_every_page(self):
        pages, _ = kn.parse_text(TEXT)
        self.assertNotIn("pdf_check", self.entry["crosscheck"])
        self.assertFalse(kn.may_mark_sourced(self.entry, pages, self.doc, TEXT))   # hash tự sinh không phải đối chiếu PDF
        witnessed = self._witness(self.entry, TEXT)
        self.assertTrue(kn.may_mark_sourced(witnessed, pages, self.doc, TEXT))
        self.assertFalse(kn.may_mark_sourced(dict(self.entry, crosscheck={"method": "hash-only", "pages_checked": 2, "pages_total": 2}), pages, self.doc, TEXT))
        bare = {k: v for k, v in self.entry.items() if k not in kn.ORIGINAL_KEYS and k != "crosscheck"}
        self.assertFalse(kn.may_mark_sourced(bare, pages, self.doc, TEXT))          # hash text.md một mình không đủ
        self._queue("SOURCED")
        self.assertTrue(any("SOURCED" in e and "hash khớp không" in e for e in self._errs()), self._errs())
        self._manifest({self.doc: witnessed})
        self.assertEqual(self._errs(), [])

    def test_rejects_swapped_pdf_swapped_text_missing_original_and_bad_metadata(self):
        (self.dir / "goc.pdf").write_bytes(PDF + b"X")
        self.assertTrue(any("tệp gốc lệch" in e for e in self._errs()), self._errs())
        (self.dir / "goc.pdf").write_bytes(PDF)
        (self.dir / "text.md").write_text(TEXT.replace("kế toán", "tài chính"), encoding="utf-8")
        self.assertTrue(any("sha256" in e for e in self._errs()), self._errs())
        (self.dir / "text.md").write_bytes(self.text_b)
        (self.dir / "goc.pdf").unlink()
        self.assertTrue(any("thiếu tệp gốc" in e for e in self._errs()), self._errs())
        (self.dir / "goc.pdf").write_bytes(PDF)
        bad = dict(self.entry, original_sha256=self.entry["text_sha256"])
        self._manifest({self.doc: bad})
        self.assertTrue(any("không được dùng làm hash tệp gốc" in e for e in self._errs()), self._errs())
        bad = dict(self.entry, original_bytes=self.entry["original_bytes"] + 1)
        self._manifest({self.doc: bad})
        self.assertTrue(any("tệp gốc lệch" in e for e in self._errs()), self._errs())
        for path in (f"library/sources/{self.doc}/text.md", f"library/sources/{self.doc}/../../etc/passwd", "/tmp/x.pdf"):
            self._manifest({self.doc: dict(self.entry, original_path=path)})
            self.assertTrue(self._errs(), path)
        partial = dict(self.entry, crosscheck={"method": "page-by-page", "pages_checked": 1, "pages_total": 2})
        self._manifest({self.doc: partial})
        self.assertTrue(any("chưa đối chiếu đủ" in e for e in self._errs()), self._errs())
        self._manifest({self.doc: dict(self.entry, crosscheck={"method": "hash-only", "pages_checked": 2, "pages_total": 2})})
        self.assertTrue(any("page-by-page" in e for e in self._errs()), self._errs())

    def test_sourced_without_crosscheck_is_rejected_even_if_hashes_match(self):
        pinned = self._pin(self.doc, self.text_b, PDF, "goc.pdf", pages=2, cross=False)
        self._manifest({self.doc: pinned})
        self.assertEqual(kn.origin_binding_errors(self.tmp, self.doc, pinned, self.text_b), [])
        pages, _ = kn.parse_text(TEXT)
        self.assertFalse(kn.may_mark_sourced(pinned, pages, self.doc))
        self._queue("SOURCED")
        errs = self._errs()
        self.assertTrue(any("SOURCED" in e and "hash khớp không" in e for e in errs), errs)

    def test_legacy_manifest_without_original_fields_is_rejected(self):
        legacy = {k: v for k, v in self.entry.items() if k not in kn.ORIGINAL_KEYS and k != "crosscheck"}
        self._manifest({self.doc: legacy})
        self._queue("QUEUED")
        errs, _warns = kn.check_library(self.tmp)
        self.assertTrue(any("thiếu ghim tệp gốc" in e for e in errs), errs)

    def test_cited_note_needs_verified_original_not_a_page_count(self):
        bare = self._pin(self.doc, self.text_b, PDF, "goc.pdf", pages=2, cross=False)
        self._manifest({self.doc: bare})
        note = {"id": "KN-T2-mau", "tier": 2, "topic": "Phạm vi", "doc_ids": [self.doc],
                "applies_to": "mọi doanh nghiệp", "effective_date": "2017-01-01",
                "points": [
                    {"id": "P1", "vi": "Luật điều chỉnh công tác kế toán",
                     "addresses": [f"{self.doc}:p1:2"], "quote": "quy định về nội dung công tác kế toán",
                     "kind": "TEXT_ATTESTED"},
                    {"id": "P2", "vi": "Nhiệm vụ thu thập số liệu",
                     "addresses": [f"{self.doc}:p2:2"], "quote": "Thu thập, xử lý thông tin, số liệu kế toán.",
                     "kind": "TEXT_ATTESTED"},
                    {"id": "P3", "vi": "Tên điều phạm vi",
                     "addresses": [f"{self.doc}:p1:1"], "quote": "Điều 1. Phạm vi điều chỉnh",
                     "kind": "TEXT_ATTESTED"}],
                "not_said": ["Không nói về ngân hàng", "Không nói mức phạt"],
                "testable_implications": [], "status": "CITED", "review_by": "2099-01-01",
                "read_by": "ChatGPT (OpenAI)",
                "self_check": {"parallelism": True, "one_word_one_meaning": True, "contrast_pairs": False,
                               "question_answer": False, "counts_from_source": True, "doubts": []}}
        (self.tmp / "contracts").mkdir()
        shutil.copy(ROOT / "contracts" / "knowledge_note.schema.json", self.tmp / "contracts")
        (self.tmp / "library" / "notes").mkdir()
        (self.tmp / "library" / "INDEX.md").write_text("KN-T2-mau", encoding="utf-8")
        (self.tmp / "library" / "notes" / "KN-T2-mau.json").write_text(json.dumps(note), encoding="utf-8")
        (self.tmp / "library" / "audits").mkdir()
        digest = kn.note_digest(note)
        (self.tmp / "library" / "audits" / "KN-T2-mau.json").write_text(json.dumps({
            "note_id": "KN-T2-mau", "auditor": "Owner", "verdict": "PASS", "date": "2026-11-18",
            "note_sha256": digest}), encoding="utf-8")
        errs = self._errs()
        self.assertTrue(any("CITED" in e and "tệp gốc" in e for e in errs), errs)
        counted = dict(bare, crosscheck={"method": "page-by-page", "pages_checked": 2, "pages_total": 2})
        self._manifest({self.doc: counted})
        self.assertTrue(any("pages_checked" in e for e in self._errs()), self._errs())
        full = self._pin(self.doc, self.text_b, PDF, "goc.pdf", pages=2, cross=True)
        self._manifest({self.doc: full})
        self.assertTrue(any("PDF" in e for e in self._errs()), self._errs())
        witnessed = self._witness(full, TEXT, checker="Owner")
        self._manifest({self.doc: witnessed})
        self.assertFalse(any("KN-T2-mau" in e and ("L-01" in e or "L-09" in e) for e in self._errs()), self._errs())
        same = self._witness(full, TEXT, checker="ChatGPT (OpenAI)")
        self._manifest({self.doc: same})
        self.assertTrue(any("trùng ghế" in e for e in self._errs()), self._errs())

    def test_known_accounting_law_rejects_wrong_pdf_and_cannot_be_sourced_early(self):
        self.assertEqual(KNOWN["original_sha256"], "1fd9336a3a6f4d90676db5889bdb409af9c75c96c9c256143197908a7bfcca50")
        self.assertEqual(KNOWN["original_bytes"], 2566253)
        self.assertEqual(KNOWN["pages"], 35)
        doc = "luat_ke_toan_88_2015"
        d = self.tmp / "library" / "sources" / doc
        d.mkdir(parents=True)
        (d / "text.md").write_bytes(self.text_b)
        (d / "goc.pdf").write_bytes(PDF)
        wrong = self._pin(doc, self.text_b, PDF, "goc.pdf", pages=2)
        self._manifest({doc: wrong})
        self.assertTrue(any("không khớp bản gốc đã công bố" in e for e in self._errs()), self._errs())
        claimed = dict(wrong, original_sha256=KNOWN["original_sha256"], original_bytes=KNOWN["original_bytes"],
                       crosscheck={"method": "page-by-page", "pages_checked": 35, "pages_total": 35})
        self._manifest({doc: claimed})
        errs = self._errs()
        self.assertTrue(any("tệp gốc lệch" in e for e in errs), errs)
        self.assertTrue(any("không có đủ trang 1..35" in e for e in errs), errs)
        pages, _ = kn.parse_text(TEXT)
        self.assertFalse(kn.may_mark_sourced(claimed, pages, doc))
        self._queue("SOURCED", doc)
        self.assertTrue(any("SOURCED" in e for e in self._errs()))

    def test_repo_pins_the_checked_accounting_law_pdf(self):
        man = json.loads((ROOT / "library" / "SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
        entry = man["files"]["luat_ke_toan_88_2015"]
        self.assertEqual(entry["original_sha256"], KNOWN["original_sha256"])
        self.assertEqual(entry["original_bytes"], KNOWN["original_bytes"])
        self.assertEqual(entry["text_sha256"], entry["sha256"])
        pdf = (ROOT / entry["original_path"]).read_bytes()
        text = (ROOT / "library/sources/luat_ke_toan_88_2015/text.md").read_text(encoding="utf-8")
        self.assertEqual(hashlib.sha256(pdf).hexdigest(), KNOWN["original_sha256"])
        self.assertEqual(len(pdf), KNOWN["original_bytes"])
        self.assertEqual(hashlib.sha256(text.encode("utf-8")).hexdigest(), entry["text_sha256"])
        pages, _ = kn.parse_text(text)
        self.assertEqual(set(pages), set(range(1, 36)))
        self.assertTrue(kn.may_mark_sourced(entry, pages, "luat_ke_toan_88_2015", text))
        self.assertEqual(entry["crosscheck"]["pdf_check"]["checker"], "Claude (Anthropic)")
        self.assertEqual(entry["crosscheck"]["pdf_check"]["result"], "MATCH")
        self.assertEqual(entry["crosscheck"]["pdf_check"]["text_sha256"], entry["text_sha256"])
        # 8 lỗi chép đã sửa sau khi đọc ảnh trang (p11, p12, p23, p32): bản chép phải giữ dạng in, không quay về bản cũ
        self.assertNotEqual(entry["text_sha256"], "bd31f9b83d891e559c0b356c0f7efcb1c86f4d379cac55cea1c726a23ba0d2b3")
        for printed in ("quản lý và sử dụng hoá đơn", "được cụ thể hoá các sổ", "thì Toà án tuyên bố phá sản",
                        "Có quan hệ kinh tế, tài chính với đơn vị kế toán đó;"):
            self.assertIn(printed, text)
        import yaml
        items = (yaml.safe_load((ROOT / "library" / "reading_queue.yaml").read_text(encoding="utf-8")) or {}).get("items") or []
        law = next(i for i in items if i.get("doc_id") == "luat_ke_toan_88_2015")
        self.assertEqual(law.get("status"), "SOURCED")
        note = json.loads((ROOT / "library/notes/KN-T2-luat-ke-toan-88-2015-goc.json").read_text(encoding="utf-8"))
        self.assertEqual(note["status"], "DRAFT")
        errs, _ = kn.check_library(ROOT)
        self.assertFalse(any("luat_ke_toan_88_2015" in e for e in errs), errs)


TABLE = textwrap.dedent("""\
    [p1]
    Điều 1. Phạm vi điều chỉnh

    Không được đổi dấu của số liệu.

    [t1]
    | Chỉ tiêu | Số |
    |---|---|
    | Nợ nhóm 3 | 1.200 |
    | Nợ nhóm 5 | -4.100 |

    [p2]
    Điều 4. Nhiệm vụ kế toán

    Thu thập, xử lý thông tin, số liệu kế toán.
    """)


class TableAndPdfWitnessTests(unittest.TestCase):
    """Số trong bảng phải đổi hash trang. Hash tự sinh từ text.md không phải biên bản đối chiếu PDF."""

    def setUp(self):
        self.host = OriginalBindingTests()
        self.host.setUp()
        self.doc = self.host.doc
        self.dir = self.host.dir
        (self.dir / "text.md").write_text(TABLE, encoding="utf-8")
        self.text_b = (self.dir / "text.md").read_bytes()
        self.entry = self.host._pin(self.doc, self.text_b, PDF, "goc.pdf", pages=2)
        self.host._manifest({self.doc: self.entry})

    def tearDown(self):
        self.host.tearDown()

    def _errs(self):
        return self.host._errs()

    def _manifest(self, files):
        self.host._manifest(files)

    def _queue(self, status, doc=None):
        self.host._queue(status, doc or self.doc)

    def _pin(self, *args, **kwargs):
        return self.host._pin(*args, **kwargs)

    def _witness(self, entry, text, checker="Owner"):
        return self.host._witness(entry, text, checker)

    def _fp(self, text, page=1):
        return kn.page_fingerprint(kn.page_surface(text)[page])[1]

    def _para(self, text, page=1):
        pages, _tables = kn.parse_text(text)
        return hashlib.sha256("\n".join(pages[page]).encode("utf-8")).hexdigest()

    def test_table_edits_change_the_page_fingerprint(self):
        body = kn.page_fingerprint(kn.page_surface(TABLE)[1])[0]
        self.assertIn("1.200", body)
        self.assertIn("-4.100", body)
        self.assertIn("Không", body)
        self.assertNotIn("pdf_check", kn.page_crosscheck(TABLE))
        edited = TABLE.replace("1.200", "1.900")
        self.assertEqual(self._para(TABLE), self._para(edited))          # lỗ cũ: đoạn văn không đổi
        self.assertNotEqual(self._fp(TABLE), self._fp(edited))            # ô bảng phải đổi hash cả trang
        self.assertNotEqual(self._fp(TABLE), self._fp(TABLE.replace("-4.100", "4.100")))
        self.assertNotEqual(self._fp(TABLE), self._fp(TABLE.replace("Không được", "Được")))
        self.assertNotEqual(self._fp(TABLE), self._fp(TABLE.replace("| Nợ nhóm 5 | -4.100 |\n", "")))
        added = TABLE.replace("| Nợ nhóm 5 | -4.100 |", "| Nợ nhóm 5 | -4.100 |\n| Nợ nhóm 2 | 50 |")
        self.assertNotEqual(self._fp(TABLE), self._fp(added))
        moved = textwrap.dedent("""\
            [p1]
            Điều 1. Phạm vi điều chỉnh

            Không được đổi dấu của số liệu.

            [p2]
            Điều 4. Nhiệm vụ kế toán

            Thu thập, xử lý thông tin, số liệu kế toán.

            [t1]
            | Chỉ tiêu | Số |
            |---|---|
            | Nợ nhóm 3 | 1.200 |
            | Nợ nhóm 5 | -4.100 |
            """)
        self.assertNotEqual(self._fp(TABLE, 1), self._fp(moved, 1))
        self.assertNotEqual(self._fp(TABLE, 2), self._fp(moved, 2))

    def test_stale_qc_regenerated_hash_and_bad_pages_are_blocked(self):
        changed = TABLE.replace("1.200", "1.900")
        (self.dir / "text.md").write_text(changed, encoding="utf-8")
        b = (self.dir / "text.md").read_bytes()
        stale = dict(self.entry, sha256=hashlib.sha256(b).hexdigest(), bytes=len(b),
                     text_sha256=hashlib.sha256(b).hexdigest(), text_bytes=len(b))
        self._manifest({self.doc: stale})
        self.assertTrue(any("không khớp" in e for e in self._errs()), self._errs())
        fresh = self._pin(self.doc, b, PDF, "goc.pdf")
        self.assertNotIn("pdf_check", fresh["crosscheck"])
        pages, _ = kn.parse_text(changed)
        self.assertFalse(kn.may_mark_sourced(fresh, pages, self.doc, changed))
        self._manifest({self.doc: fresh})
        self._queue("SOURCED")
        self.assertTrue(any("SOURCED" in e and "hash khớp không" in e for e in self._errs()), self._errs())
        gap = TABLE.replace("[p2]", "[p3]")
        gap_b = gap.encode("utf-8")
        (self.dir / "text.md").write_bytes(gap_b)
        gapped = self._pin(self.doc, gap_b, PDF, "goc.pdf")
        self._manifest({self.doc: gapped})
        self.assertTrue(any("thiếu trang" in e or "đánh số" in e for e in self._errs()), self._errs())
        short = "\n".join(TABLE.split("[p2]")[0])
        self._manifest({self.doc: self.entry})
        (self.dir / "text.md").write_text(TABLE, encoding="utf-8")
        (self.dir / "text.md").write_text(short, encoding="utf-8")
        short_b = (self.dir / "text.md").read_bytes()
        kept = dict(self.entry, sha256=hashlib.sha256(short_b).hexdigest(), bytes=len(short_b),
                    text_sha256=hashlib.sha256(short_b).hexdigest(), text_bytes=len(short_b))
        self._manifest({self.doc: kept})
        self.assertTrue(self._errs(), self._errs())
        (self.dir / "text.md").write_text(TABLE, encoding="utf-8")
        (self.dir / "goc.pdf").write_bytes(PDF + b"TAMPER")
        self._manifest({self.doc: self.entry})
        self.assertTrue(any("tệp gốc lệch" in e for e in self._errs()), self._errs())

    def test_valid_pdf_witness_passes_sourced(self):
        (self.dir / "goc.pdf").write_bytes(PDF)
        (self.dir / "text.md").write_text(TABLE, encoding="utf-8")
        witnessed = self._witness(self.entry, TABLE)
        pages, _ = kn.parse_text(TABLE)
        self.assertTrue(kn.may_mark_sourced(witnessed, pages, self.doc, TABLE))
        self._manifest({self.doc: witnessed})
        self._queue("SOURCED")
        self.assertEqual(self._errs(), [])


def _tiny_pdf(n, extra=b""):
    body = b"%PDF-1.4\n" + extra
    for _ in range(n):
        body += b"<< /Type /Page >>\n"
    body += f"<< /Type /Pages /Count {n} >>\n".encode()
    return body


MULTI_TEXT = textwrap.dedent("""\
    [p1]
    Điều 1. Phần đầu trang một

    Nội dung được giữ nguyên trên trang một.

    [p2]
    Điều 2. Phần đầu trang hai

    Nội dung được giữ nguyên trên trang hai.

    [p3]
    Điều 3. Phần sau trang một

    Nội dung được giữ nguyên trên trang sau.
    """)


class MultiPartOriginalTests(unittest.TestCase):
    """ADR-0014: N≥2 PDF gốc. Không nối tệp. Không SOURCED khi chưa có pdf_check đủ phần."""

    def setUp(self):
        self.host = OriginalBindingTests()
        self.host.setUp()
        self.doc = self.host.doc
        self.dir = self.host.dir
        (self.dir / "text.md").write_text(MULTI_TEXT, encoding="utf-8")
        self.text_b = (self.dir / "text.md").read_bytes()
        self.pdf_a = _tiny_pdf(2, b"part-a\n")
        self.pdf_b = _tiny_pdf(2, b"part-b\n")
        (self.dir / "a.pdf").write_bytes(self.pdf_a)
        (self.dir / "b.pdf").write_bytes(self.pdf_b)
        self.entry = self._entry()
        self.host._manifest({self.doc: self.entry})

    def tearDown(self):
        self.host.tearDown()

    def _part(self, pid, name, raw, pages):
        return {"part_id": pid, "original_path": f"library/sources/{self.doc}/{name}",
                "source_url": f"https://congbao.chinhphu.vn/{pid}",
                "original_sha256": hashlib.sha256(raw).hexdigest(), "original_bytes": len(raw),
                "page_count": pages}

    def _entry(self, text_b=None, pdf_a=None, pdf_b=None):
        text_b = self.text_b if text_b is None else text_b
        pdf_a = self.pdf_a if pdf_a is None else pdf_a
        pdf_b = self.pdf_b if pdf_b is None else pdf_b
        text = text_b.decode("utf-8")
        e = {"sha256": hashlib.sha256(text_b).hexdigest(), "bytes": len(text_b), "issuer": "Quốc hội",
             "issued_on": "2024-01-18", "accessed_on": "2026-11-20",
             "source_url": "https://congbao.chinhphu.vn/van-ban/luat-so-32-2024-qh15-41339.htm",
             "data_source": "Công báo / Cổng TTĐT Chính phủ", "legal_status": "văn bản quy phạm, không bảo hộ",
             "license": "public-domain-vn-law", "kind": "LAW", "effective_from": "2024-07-01",
             "effective_to": None, "superseded_by": None,
             "text_sha256": hashlib.sha256(text_b).hexdigest(), "text_bytes": len(text_b),
             "original_parts": [self._part("phan-a", "a.pdf", pdf_a, 2), self._part("phan-b", "b.pdf", pdf_b, 2)],
             "page_map": [
                 {"text_page": 1, "part_id": "phan-a", "pdf_page": 1},
                 {"text_page": 2, "part_id": "phan-a", "pdf_page": 2},
                 {"text_page": 3, "part_id": "phan-b", "pdf_page": 1},
             ],
             "excluded_pages": [{"part_id": "phan-b", "pdf_page": 2,
                                 "reason": "Trang trống cuối phần, không chứa điều khoản của văn bản."}],
             "crosscheck": kn.page_crosscheck(text)}
        return e

    def _errs(self):
        return self.host._errs()

    def _witness(self, entry, text, checker="Owner", originals=None, page_map=None, single_hash=False):
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        cc = json.loads(json.dumps(entry["crosscheck"]))
        check = {"checker": checker, "result": "MATCH",
                 "pages_checked": [p["page"] for p in cc["pages"]],
                 "evidence": "Đối chiếu từng trang text.md với từng PDF gốc theo page_map.",
                 "text_sha256": digest,
                 "originals": originals if originals is not None else [
                     {"part_id": p["part_id"], "original_sha256": p["original_sha256"]}
                     for p in entry["original_parts"]],
                 "page_map": entry["page_map"] if page_map is None else page_map}
        if single_hash:
            check["original_sha256"] = entry["original_parts"][0]["original_sha256"]
        cc["pdf_check"] = check
        return dict(entry, sha256=digest, bytes=len(text.encode("utf-8")), text_sha256=digest,
                    text_bytes=len(text.encode("utf-8")), crosscheck=cc)

    def test_two_parts_pass_gate_but_not_sourced_without_witness(self):
        self.assertEqual(kn.origin_binding_errors(self.host.tmp, self.doc, self.entry, self.text_b), [])
        self.assertNotIn("pdf_check", self.entry["crosscheck"])
        pages, _ = kn.parse_text(MULTI_TEXT)
        self.assertFalse(kn.may_mark_sourced(self.entry, pages, self.doc, MULTI_TEXT))
        self.host._queue("SOURCED")
        self.assertTrue(any("SOURCED" in e for e in self._errs()), self._errs())
        witnessed = self._witness(self.entry, MULTI_TEXT)
        self.assertTrue(kn.may_mark_sourced(witnessed, pages, self.doc, MULTI_TEXT))
        self.host._manifest({self.doc: witnessed})
        self.assertEqual(self._errs(), [])

    def test_flip_delete_swap_duplicate_path_and_reused_text_hash(self):
        (self.dir / "a.pdf").write_bytes(self.pdf_a + b"X")
        self.assertTrue(any("tệp gốc lệch" in e for e in self._errs()), self._errs())
        (self.dir / "a.pdf").write_bytes(self.pdf_a)
        (self.dir / "b.pdf").unlink()
        self.assertTrue(any("thiếu tệp gốc" in e for e in self._errs()), self._errs())
        (self.dir / "b.pdf").write_bytes(self.pdf_b)
        swapped = json.loads(json.dumps(self.entry))
        swapped["original_parts"] = list(reversed(swapped["original_parts"]))
        self.host._manifest({self.doc: swapped})
        self.assertTrue(any("tráo" in e for e in self._errs()), self._errs())
        dup = json.loads(json.dumps(self.entry))
        dup["original_parts"][1]["part_id"] = "phan-a"
        self.host._manifest({self.doc: dup})
        self.assertTrue(any("lặp part_id" in e for e in self._errs()), self._errs())
        for path in (f"library/sources/{self.doc}/../../etc/passwd", "/tmp/x.pdf"):
            bad = json.loads(json.dumps(self.entry))
            bad["original_parts"][0]["original_path"] = path
            self.host._manifest({self.doc: bad})
            self.assertTrue(self._errs(), path)
        reused = json.loads(json.dumps(self.entry))
        reused["original_parts"][0]["original_sha256"] = reused["text_sha256"]
        self.host._manifest({self.doc: reused})
        self.assertTrue(any("không được dùng làm hash tệp gốc" in e for e in self._errs()), self._errs())

    def test_missing_middle_page_wrong_map_and_bad_page_count(self):
        short = textwrap.dedent("""\
            [p1]
            Điều 1. Trang đầu của phần một.

            [p2]
            Điều 2. Trang đầu của phần hai.
            """)
        (self.dir / "text.md").write_text(short, encoding="utf-8")
        raw = (self.dir / "text.md").read_bytes()
        gap = self._entry(text_b=raw)
        gap["page_map"] = [
            {"text_page": 1, "part_id": "phan-a", "pdf_page": 1},
            {"text_page": 2, "part_id": "phan-b", "pdf_page": 1},
        ]
        gap["crosscheck"] = kn.page_crosscheck(short)
        self.host._manifest({self.doc: gap})
        self.assertTrue(any("chưa ánh xạ" in e for e in self._errs()), self._errs())
        wrong = json.loads(json.dumps(self.entry))
        wrong["page_map"][0]["pdf_page"] = 9
        self.host._manifest({self.doc: wrong})
        (self.dir / "text.md").write_bytes(self.text_b)
        self.assertTrue(any("nằm ngoài" in e or "không khớp" in e for e in self._errs()), self._errs())
        counted = json.loads(json.dumps(self.entry))
        counted["original_parts"][1]["page_count"] = 3
        counted["excluded_pages"] = [
            {"part_id": "phan-b", "pdf_page": 2, "reason": "Trang trống cuối phần, không chứa điều khoản."},
            {"part_id": "phan-b", "pdf_page": 3, "reason": "Khai thêm trang mà PDF không có để thử page_count."},
        ]
        self.host._manifest({self.doc: counted})
        self.assertTrue(any("page_count lệch" in e for e in self._errs()), self._errs())
        blank = b"%PDF-1.4\nno page markers\n"
        (self.dir / "a.pdf").write_bytes(blank)
        blind = json.loads(json.dumps(self.entry))
        blind["original_parts"][0]["original_sha256"] = hashlib.sha256(blank).hexdigest()
        blind["original_parts"][0]["original_bytes"] = len(blank)
        self.host._manifest({self.doc: blind})
        self.assertTrue(any("fail closed" in e for e in self._errs()), self._errs())

    def test_fake_witness_and_sourced_before_reviewer(self):
        pages, _ = kn.parse_text(MULTI_TEXT)
        fake = self._witness(self.entry, MULTI_TEXT, single_hash=True)
        self.assertFalse(kn.may_mark_sourced(fake, pages, self.doc, MULTI_TEXT))
        self.assertTrue(any("một original_sha256" in e for e in kn.pdf_witness_errors(fake, MULTI_TEXT)))
        swapped = self._witness(self.entry, MULTI_TEXT, originals=list(reversed([
            {"part_id": p["part_id"], "original_sha256": p["original_sha256"]} for p in self.entry["original_parts"]])))
        self.assertTrue(any("lệch" in e for e in kn.pdf_witness_errors(swapped, MULTI_TEXT)))
        moved = self._witness(self.entry, MULTI_TEXT, page_map=list(reversed(self.entry["page_map"])))
        self.assertTrue(any("page_map" in e for e in kn.pdf_witness_errors(moved, MULTI_TEXT)))
        self.host._manifest({self.doc: fake})
        self.host._queue("SOURCED")
        self.assertTrue(any("SOURCED" in e for e in self._errs()), self._errs())

    def test_both_schemas_and_single_part_are_rejected(self):
        both = dict(self.entry, original_sha256="ab" * 32, original_bytes=4,
                    original_path=f"library/sources/{self.doc}/a.pdf")
        self.host._manifest({self.doc: both})
        self.assertTrue(any("đồng thời" in e for e in self._errs()), self._errs())
        one = json.loads(json.dumps(self.entry))
        one["original_parts"] = one["original_parts"][:1]
        self.host._manifest({self.doc: one})
        self.assertTrue(any("từ 2 phần" in e for e in self._errs()), self._errs())
        self.assertIsNone(kn.pdf_page_count(b"not a pdf"))
        self.assertIsNone(kn.pdf_page_count(b"%PDF-1.4\n<< /Type /Pages /Count 1 >>\n"))
        self.assertEqual(kn.pdf_page_count(_tiny_pdf(2)), 2)
        self.assertIsNone(kn.pdf_page_count(_tiny_pdf(2) + b"<< /Count 9 >>\n"))

    def test_known_single_file_law_cannot_be_declared_multipart(self):
        doc = "luat_ke_toan_88_2015"
        d = self.host.tmp / "library" / "sources" / doc
        d.mkdir(parents=True)
        (d / "text.md").write_bytes(self.text_b)
        (d / "a.pdf").write_bytes(self.pdf_a)
        (d / "b.pdf").write_bytes(self.pdf_b)
        self.doc = doc
        entry = self._entry()
        self.doc = self.host.doc
        self.host._manifest({doc: entry})
        errs = kn.origin_binding_errors(self.host.tmp, doc, entry, self.text_b)
        self.assertTrue(any("một tệp" in e for e in errs), errs)
        pages, _ = kn.parse_text(MULTI_TEXT)
        self.assertFalse(kn.may_mark_sourced(self._witness(entry, MULTI_TEXT), pages, doc, MULTI_TEXT))

    def test_repo_keeps_accounting_law_and_queues_credit_institutions_law(self):
        man = json.loads((ROOT / "library" / "SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
        law88 = man["files"]["luat_ke_toan_88_2015"]
        self.assertNotIn("original_parts", law88)
        self.assertEqual(law88["original_sha256"], KNOWN["original_sha256"])
        text88 = (ROOT / "library/sources/luat_ke_toan_88_2015/text.md").read_text(encoding="utf-8")
        pages88, _ = kn.parse_text(text88)
        self.assertTrue(kn.may_mark_sourced(law88, pages88, "luat_ke_toan_88_2015", text88))
        entry = man["files"]["luat_tctd_32_2024"]
        for key in ("original_sha256", "original_bytes", "original_path"):
            self.assertNotIn(key, entry)
        self.assertNotIn("pdf_check", entry.get("crosscheck") or {})
        parts = entry["original_parts"]
        self.assertEqual([p["part_id"] for p in parts], ["cb-369-370", "cb-371-372"])
        self.assertEqual(parts[0]["original_sha256"], "b613a8f94e1955a776035be2b7cd14dc34a76c568973f8db7367324ebf50581a")
        self.assertEqual(parts[0]["original_bytes"], 1188965)
        self.assertEqual(parts[0]["page_count"], 94)
        self.assertEqual(parts[1]["original_sha256"], "67852f403c7f368989ef47f98a47933d732d3d6b9d2db40cda2a9af84b969c49")
        self.assertEqual(parts[1]["original_bytes"], 741096)
        self.assertEqual(parts[1]["page_count"], 59)
        self.assertEqual(entry["page_map"][0], {"text_page": 1, "part_id": "cb-369-370", "pdf_page": 1})
        self.assertEqual(entry["page_map"][92], {"text_page": 93, "part_id": "cb-369-370", "pdf_page": 93})
        self.assertEqual(entry["page_map"][93], {"text_page": 94, "part_id": "cb-371-372", "pdf_page": 1})
        self.assertEqual(entry["page_map"][-1], {"text_page": 152, "part_id": "cb-371-372", "pdf_page": 59})
        self.assertEqual(entry["excluded_pages"][0]["part_id"], "cb-369-370")
        self.assertEqual(entry["excluded_pages"][0]["pdf_page"], 94)
        text = (ROOT / "library/sources/luat_tctd_32_2024/text.md").read_text(encoding="utf-8")
        surface = kn.page_surface(text)
        self.assertEqual(set(surface), set(range(1, 153)))
        self.assertIn("Điều 115. Hoạt động ngân hàng của công ty tài chính tổng hợp", surface[85])
        self.assertTrue(any("Tại mỗi tỉnh, thành phố trực thuộc Trung ương" in line for line in surface[94]))
        self.assertTrue(any("Điều 131." in line for line in surface[93]))
        self.assertTrue(any(line.startswith("Điều 132.") for line in surface[94]))
        self.assertIn("có hiệu lực thi hành từ ngày 01 tháng 7 năm 2024", text)
        self.assertIn("thông qua ngày 18 tháng 01 năm 2024", text)
        pages, _ = kn.parse_text(text)
        self.assertFalse(kn.may_mark_sourced(entry, pages, "luat_tctd_32_2024", text))
        self.assertEqual(kn.origin_binding_errors(ROOT, "luat_tctd_32_2024", entry, text.encode("utf-8")), [])
        import yaml
        items = (yaml.safe_load((ROOT / "library/reading_queue.yaml").read_text(encoding="utf-8")) or {}).get("items") or []
        row = next(i for i in items if i.get("doc_id") == "luat_tctd_32_2024")
        self.assertEqual(row.get("status"), "QUEUED")
        errs, _warns = kn.check_library(ROOT)
        self.assertFalse(any(e.startswith("LỖI") or "luat_tctd_32_2024" in e or "luat_ke_toan_88_2015" in e for e in errs), errs)


if __name__ == "__main__":
    unittest.main()
