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

    def _pin(self, doc, text_b, pdf, name, pages, cross=True):
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

    def test_separate_pins_allow_sourced_only_after_every_page(self):
        pages, _ = kn.parse_text(TEXT)
        self.assertTrue(kn.may_mark_sourced(self.entry, pages, self.doc))
        self.assertFalse(kn.may_mark_sourced(dict(self.entry, crosscheck={"method": "hash-only", "pages_checked": 2, "pages_total": 2}), pages, self.doc))
        bare = {k: v for k, v in self.entry.items() if k not in kn.ORIGINAL_KEYS and k != "crosscheck"}
        self.assertFalse(kn.may_mark_sourced(bare, pages, self.doc))          # hash text.md một mình không đủ
        self._queue("SOURCED")
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
        self.assertFalse(any("KN-T2-mau" in e and "L-01" in e for e in self._errs()), self._errs())

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

    def test_repo_does_not_mark_the_law_sourced_or_pin_an_unchecked_pdf(self):
        man = json.loads((ROOT / "library" / "SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(man.get("files"), {})
        import yaml
        items = (yaml.safe_load((ROOT / "library" / "reading_queue.yaml").read_text(encoding="utf-8")) or {}).get("items") or []
        law = next(i for i in items if i.get("doc_id") == "luat_ke_toan_88_2015")
        self.assertEqual(law.get("status"), "QUEUED")
        self.assertTrue(all(i.get("status") != "SOURCED" for i in items))
        errs, _ = kn.check_library(ROOT)
        self.assertFalse(any("SOURCED" in e for e in errs), errs)


if __name__ == "__main__":
    unittest.main()
