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


if __name__ == "__main__":
    unittest.main()
