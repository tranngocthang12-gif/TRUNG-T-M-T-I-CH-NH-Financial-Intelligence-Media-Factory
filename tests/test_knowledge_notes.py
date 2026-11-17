"""Kiểm máy Thư viện (engine/knowledge_notes.py) và L-03 (tools/laws_checks.check_personal_data) trên thư viện dựng tay."""
import copy, hashlib, json, os, pathlib, shutil, subprocess, sys, tempfile, textwrap, unittest
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from engine import knowledge_notes as kn  # noqa: E402
from tools import laws_checks  # noqa: E402

TEXT = textwrap.dedent("""\
    [p1]
    Điều 1. Phạm vi điều chỉnh

    Luật này quy định về nội dung công tác kế toán, tổ chức bộ máy kế toán, người làm kế toán.

    [p2]
    Điều 4. Nhiệm vụ kế toán

    Thu thập, xử lý thông tin, số liệu kế toán theo đối tượng và nội dung công việc kế toán.

    [t1]
    | Chỉ tiêu | 30/9/2026 | 31/12/2026 |
    |---|---|---|
    | Nợ nhóm 3 | 1.200 | 1.350 |
    | Nợ nhóm 5 | 4.000 | 4.100 |
    """)

NOTE = {
    "id": "KN-T2-luat-ke-toan-pham-vi", "tier": 2, "topic": "Phạm vi Luật Kế toán",
    "doc_ids": ["luat_ke_toan_88_2015"], "applies_to": "mọi doanh nghiệp", "effective_date": "2017-01-01",
    "points": [
        {"id": "P1", "vi": "Luật điều chỉnh nội dung công tác kế toán", "addresses": ["luat_ke_toan_88_2015:p1:2"],
         "quote": "quy định về nội dung công tác kế toán", "kind": "TEXT_ATTESTED"},
        {"id": "P2", "vi": "Nhiệm vụ: thu thập, xử lý số liệu", "addresses": ["luat_ke_toan_88_2015:p2:2"],
         "quote": "Thu thập, xử lý thông tin,  số liệu kế toán", "kind": "TEXT_ATTESTED"},
        {"id": "P3", "vi": "Nợ nhóm 3 tại 31/12 là 1.350", "addresses": ["luat_ke_toan_88_2015:t1:1"],
         "quote": "| Nợ nhóm 3 | 1.200 | 1.350 |", "kind": "TEXT_ATTESTED"}],
    "not_said": ["Không nói về kế toán ngân hàng", "Không nói mức phạt"],
    "testable_implications": [], "status": "DRAFT", "review_by": "2099-01-01", "read_by": "ChatGPT (ghế thi công)",
    "self_check": {"parallelism": True, "one_word_one_meaning": True, "contrast_pairs": False,
                   "question_answer": False, "counts_from_source": True, "doubts": []}}


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        (self.tmp / "contracts").mkdir(); (self.tmp / "governance").mkdir()
        shutil.copy(ROOT / "contracts" / "knowledge_note.schema.json", self.tmp / "contracts")
        shutil.copy(ROOT / "governance" / "DATA_SOURCES.yaml", self.tmp / "governance")
        d = self.tmp / "library" / "sources" / "luat_ke_toan_88_2015"; d.mkdir(parents=True)
        (d / "text.md").write_text(TEXT, encoding="utf-8")
        b = (d / "text.md").read_bytes()
        self.entry = {"sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b), "issuer": "Quốc hội",
                      "issued_on": "2015-11-20", "accessed_on": "2026-11-17", "source_url": "https://vbpl.vn/x",
                      "data_source": "Công báo / Cổng TTĐT Chính phủ", "legal_status": "văn bản quy phạm, không bảo hộ",
                      "license": "public-domain-vn-law", "kind": "LAW", "effective_from": "2017-01-01",
                      "effective_to": None, "superseded_by": None}
        self._manifest({"luat_ke_toan_88_2015": self.entry})
        (self.tmp / "library" / "notes").mkdir()
        (self.tmp / "library" / "INDEX.md").write_text("| KN-T2-luat-ke-toan-pham-vi |", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _manifest(self, files):
        (self.tmp / "library" / "SOURCE_MANIFEST.json").write_text(json.dumps({"files": files}, ensure_ascii=False), encoding="utf-8")

    def _note(self, note):
        (self.tmp / "library" / "notes" / f"{note['id']}.json").write_text(json.dumps(note, ensure_ascii=False), encoding="utf-8")

    def _check(self, today=date(2026, 11, 17)):
        return kn.check_library(self.tmp, today)

    def test_parse_pages_paragraphs_tables(self):
        pages, tables = kn.parse_text(TEXT)
        self.assertEqual(pages[1][1], "Luật này quy định về nội dung công tác kế toán, tổ chức bộ máy kế toán, người làm kế toán.")
        self.assertEqual(tables[1], ["| Nợ nhóm 3 | 1.200 | 1.350 |", "| Nợ nhóm 5 | 4.000 | 4.100 |"])

    def test_valid_note_passes(self):
        self._note(NOTE)
        self.assertEqual(self._check(), ([], []))

    def test_quote_matches_across_unicode_forms(self):
        """text.md rút từ PDF ở dạng tổ hợp (NFD), quote gõ dạng dựng sẵn (NFC) → vẫn là nguyên văn."""
        import unicodedata
        d = self.tmp / "library" / "sources" / "luat_ke_toan_88_2015" / "text.md"
        d.write_text(unicodedata.normalize("NFD", TEXT), encoding="utf-8")
        b = d.read_bytes()
        self._manifest({"luat_ke_toan_88_2015": dict(self.entry, sha256=hashlib.sha256(b).hexdigest(), bytes=len(b))})
        self._note(NOTE)
        self.assertEqual(self._check()[0], [])

    def test_quote_and_address_errors(self):
        bad = copy.deepcopy(NOTE)
        bad["points"][0]["quote"] = "quy định về mọi hoạt động tài chính"
        bad["points"][1]["addresses"] = ["luat_ke_toan_88_2015:p2:9"]
        self._note(bad)
        errs, _ = self._check()
        self.assertTrue(any("P1" in e and "nguyên văn" in e for e in errs), errs)
        self.assertTrue(any("P2" in e and "không tồn tại" in e for e in errs), errs)

    def test_manifest_pinning_and_sources(self):
        (self.tmp / "library" / "sources" / "chua_ghim").mkdir()
        e = dict(self.entry, data_source="Mạng xã hội (Facebook/Zalo/Telegram/TikTok)", license="")
        self._manifest({"luat_ke_toan_88_2015": e})
        errs, _ = self._check()
        self.assertTrue(any("chua_ghim" in x for x in errs))
        self.assertTrue(any("nguồn bị cấm" in x for x in errs))
        self.assertTrue(any("license" in x for x in errs))
        (self.tmp / "library" / "sources" / "chua_ghim").rmdir()
        self._manifest({"luat_ke_toan_88_2015": self.entry})
        p = self.tmp / "library" / "sources" / "luat_ke_toan_88_2015" / "text.md"
        p.write_text(TEXT.replace("1.350", "1.360"), encoding="utf-8")
        self.assertTrue(any("sha256" in x for x in self._check()[0]))

    def _audit(self, note, auditor, verdict="PASS", digest=None):
        a = self.tmp / "library" / "audits"; a.mkdir(exist_ok=True)
        (a / f"{note['id']}.json").write_text(json.dumps({"note_id": note["id"], "auditor": auditor, "verdict": verdict,
            "date": "2026-11-17", "note_sha256": digest or kn.note_digest(note)}), encoding="utf-8")

    def _l09(self):
        return [e for e in self._check()[0] if "L-09" in e]

    def test_status_needs_independent_audit_bound_to_content(self):
        cited = dict(NOTE, status="CITED")
        self._note(cited)
        self.assertTrue(self._l09())                                          # chưa có biên bản
        for auditor in ("ChatGPT (ghế thi công)", "GPT-5.5", "ai đó", "ghe-cham"):   # tự chấm, cùng nhà, hoặc không nhận ra ghế
            self._audit(cited, auditor)
            self.assertTrue(self._l09(), auditor)
        self._note(dict(cited, read_by="ghe-thi-cong")); self._audit(dict(cited, read_by="ghe-thi-cong"), "Owner")
        self.assertTrue(self._l09())                                          # người đọc không nhận ra ghế
        self._note(dict(cited, read_by="Claude")); self._audit(dict(cited, read_by="Claude"), "Opus 5.5")
        self.assertTrue(self._l09())                                          # khác tên nhưng cùng nhà cung cấp
        self._note(dict(cited, read_by="Owner")); self._audit(dict(cited, read_by="Owner"), "Owner (xem lại)")
        self.assertTrue(self._l09())                                          # Owner đọc thì Owner không tự chấm
        self._note(cited); self._audit(cited, "Owner", verdict="FAIL")
        self.assertTrue(self._l09())                                          # CITED cần PASS
        self._audit(cited, "Owner")
        self.assertEqual(self._check()[0], [])                                # hợp lệ: Owner chấm ghi chú do ChatGPT đọc
        edited = copy.deepcopy(cited); edited["points"][0]["vi"] = "Ý đã bị sửa sau khi chấm"
        self._note(edited)
        self.assertTrue(any("note_sha256" in e for e in self._l09()))         # sửa ghi chú sau khi chấm → biên bản hết hiệu lực
        self._note(cited)
        self.assertEqual(self._check()[0], [])
        self._note(dict(cited, status="OUTDATED"))                            # đổi status không làm hỏng biên bản (digest bỏ status)
        self.assertEqual(self._check()[0], [])

    def test_disputed_needs_fail_audit_and_tested_proven_fail_closed(self):
        disputed = dict(NOTE, status="DISPUTED")
        self._note(disputed); self._audit(disputed, "Owner", verdict="PASS")
        self.assertTrue(self._l09())
        self._audit(disputed, "Owner", verdict="FAIL")
        self.assertEqual(self._check()[0], [])
        for st in ("TESTED", "PROVEN"):
            n = dict(NOTE, status=st)
            self._note(n); self._audit(n, "Owner")
            self.assertTrue(any("chưa có cơ chế" in e for e in self._l09()), st)

    def test_quote_must_be_long_enough_and_synthesis_needs_two_addresses(self):
        bad = copy.deepcopy(NOTE)
        bad["points"][0]["quote"] = "kế toán"                                  # có trong đoạn nhưng quá ngắn để kiểm
        bad["points"][1]["kind"] = "CROSS_TEXT_SYNTHESIS"                      # tổng hợp mà chỉ một địa chỉ
        bad["counts"] = [{"what": "số nhóm nợ", "n": 2, "addresses": ["luat_ke_toan_88_2015:t1:1"]}]
        bad["self_check"]["counts_from_source"] = False
        self._note(bad)
        errs, _ = self._check()
        self.assertTrue(any("P1" in e and "ký tự" in e for e in errs), errs)
        self.assertTrue(any("P2" in e and "hai địa chỉ" in e for e in errs), errs)
        self.assertTrue(any("counts_from_source" in e for e in errs), errs)
        ok = copy.deepcopy(NOTE)
        ok["points"][0].update(quote="Điều 1. Phạm vi điều chỉnh", addresses=["luat_ke_toan_88_2015:p1:1"])   # nguyên cả đoạn ngắn
        ok["points"][1].update(kind="CROSS_TEXT_SYNTHESIS", addresses=["luat_ke_toan_88_2015:p2:2", "luat_ke_toan_88_2015:p1:2"])
        self._note(ok)
        self.assertEqual(self._check()[0], [])

    def test_reading_queue_consistency_warnings(self):
        self._note(NOTE)
        (self.tmp / "library" / "reading_queue.yaml").write_text(json.dumps({"items": [
            {"doc_id": "luat_ke_toan_88_2015", "status": "QUEUED"},
            {"doc_id": "tt_99_2025", "status": "NOTE_WRITTEN"}]}), encoding="utf-8")
        errs, warns = self._check()
        self.assertEqual(errs, [])
        self.assertTrue(any("luat_ke_toan_88_2015" in w and "QUEUED" in w for w in warns), warns)
        self.assertTrue(any("tt_99_2025" in w for w in warns), warns)

    def test_outdated_source_warns_then_marked(self):
        self._note(NOTE)
        self._manifest({"luat_ke_toan_88_2015": dict(self.entry, superseded_by="luat_ke_toan_moi")})
        errs, warns = self._check()
        self.assertEqual(errs, [])
        self.assertTrue(any("OUTDATED" in w for w in warns))
        self.assertEqual(kn.mark_outdated(self.tmp, date(2026, 11, 17)), [NOTE["id"]])
        self.assertEqual(json.loads((self.tmp / "library" / "notes" / f"{NOTE['id']}.json").read_text(encoding="utf-8"))["status"], "OUTDATED")
        self.assertEqual(self._check(), ([], []))

    def test_counts_and_flags_addresses_must_exist(self):
        bad = copy.deepcopy(NOTE)
        bad["counts"] = [{"what": "số nhóm nợ", "n": 2, "addresses": ["luat_ke_toan_88_2015:t1:9"]}]
        bad["reading_flags"] = [{"addresses": ["luat_ke_toan_88_2015:p7:1"], "note": "bản dịch lệch", "material": False}]
        self._note(bad)
        errs, _ = self._check()
        self.assertTrue(any("counts" in e and "không tồn tại" in e for e in errs), errs)
        self.assertTrue(any("reading_flags" in e and "không tồn tại" in e for e in errs), errs)

    def test_bad_dates_are_errors_not_crashes(self):
        self._note(dict(NOTE, review_by="31/12/2026"))
        self._manifest({"luat_ke_toan_88_2015": dict(self.entry, effective_to="sau nay")})
        errs, _ = self._check()
        self.assertTrue(any("review_by" in e for e in errs), errs)
        self.assertTrue(any("effective_to" in e for e in errs), errs)

    def test_financial_statements_are_usable_only_from_publication_date(self):
        """ADR-0008: BCTC ghi period_end và published_on; ghi chú trích BCTC có effective_date ≥ ngày công bố."""
        d = self.tmp / "library" / "sources" / "bctc_vcb_2025_q4"; d.mkdir(parents=True)
        (d / "text.md").write_text(TEXT, encoding="utf-8")
        b = (d / "text.md").read_bytes()
        fin = dict(self.entry, sha256=hashlib.sha256(b).hexdigest(), bytes=len(b), issuer="Vietcombank",
                   issued_on="2026-01-20", kind="FINANCIAL_STATEMENT", effective_from=None,
                   period_end="2025-12-31", published_on="2026-01-30", source_url="https://example.vn/cbtt")
        self._manifest({"luat_ke_toan_88_2015": self.entry, "bctc_vcb_2025_q4": fin})
        man = kn.load_manifest(self.tmp)
        self.assertFalse(kn.usable_on(man, "bctc_vcb_2025_q4", date(2026, 1, 29)))    # chưa công bố
        self.assertTrue(kn.usable_on(man, "bctc_vcb_2025_q4", date(2026, 1, 30)))
        self.assertTrue(kn.usable_on(man, "luat_ke_toan_88_2015", "2016-01-01"))      # tài liệu khác: từ issued_on
        self.assertFalse(kn.usable_on(man, "khong_co", date(2030, 1, 1)))              # không biết → không dùng
        for invalid_day in (None, "", "not-a-date", "2026-02-30"):
            with self.subTest(day=invalid_day):
                self.assertFalse(kn.usable_on(man, "bctc_vcb_2025_q4", invalid_day))
        note = copy.deepcopy(NOTE); note["id"] = "KN-T3-vcb-no-nhom3"; note["tier"] = 3
        note["doc_ids"] = ["bctc_vcb_2025_q4"]
        for p in note["points"]:
            p["addresses"] = [a.replace("luat_ke_toan_88_2015", "bctc_vcb_2025_q4") for a in p["addresses"]]
        (self.tmp / "library" / "INDEX.md").write_text("| KN-T2-luat-ke-toan-pham-vi | KN-T3-vcb-no-nhom3 |", encoding="utf-8")
        for eff, bad in (("2025-12-31", True), (None, True), ("2026-01-30", False)):
            note["effective_date"] = eff; self._note(note)
            errs = [e for e in self._check()[0] if "KN-T3-vcb-no-nhom3" in e and "ADR-0008" in e]
            self.assertEqual(bool(errs), bad, (eff, errs))
        for k, v, msg in (("published_on", None, "phải có period_end và published_on"),
                          ("published_on", "2025-12-30", "trước period_end"),
                          ("published_on", "2026-12-01", "sau ngày truy cập")):
            self._manifest({"luat_ke_toan_88_2015": self.entry, "bctc_vcb_2025_q4": dict(fin, **{k: v})})
            self.assertTrue(any(msg in e for e in self._check()[0]), msg)

    def test_personal_data_l03(self):
        (self.tmp / "governance" / "ghi_chu.md").write_text("Phân tích NIM của ngân hàng.\n", encoding="utf-8")
        self.assertEqual(laws_checks.check_personal_data(self.tmp), [])
        (self.tmp / "governance" / "ghi_chu.md").write_text("Số tài khoản: 0123 4567 8910\n", encoding="utf-8")
        self.assertTrue(laws_checks.check_personal_data(self.tmp))
        (self.tmp / "governance" / "ghi_chu.md").write_text("CCCD 001234567890\n", encoding="utf-8")
        self.assertTrue(laws_checks.check_personal_data(self.tmp))
        (self.tmp / "governance" / "ghi_chu.md").write_text("ok\n", encoding="utf-8")
        (self.tmp / "research").mkdir()
        (self.tmp / "research" / "note.jsonl").write_text('{"x": "Số tài khoản 0123 4567 8910"}\n', encoding="utf-8")
        self.assertTrue(laws_checks.check_personal_data(self.tmp))              # research/ không được bỏ qua
        (self.tmp / "research" / "note.jsonl").unlink()
        src = self.tmp / "library" / "sources" / "luat_ke_toan_88_2015" / "phu_luc.md"
        src.write_text("Số tài khoản của doanh nghiệp: 0123 4567 8910 (trích nguyên văn BCTC)\n", encoding="utf-8")
        self.assertEqual(laws_checks.check_personal_data(self.tmp), [])         # tài liệu gốc công khai chép nguyên văn: không quét


if __name__ == "__main__":
    unittest.main()
