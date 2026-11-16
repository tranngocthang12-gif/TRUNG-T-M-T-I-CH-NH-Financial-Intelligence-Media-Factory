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
    "testable_implications": [], "status": "DRAFT", "review_by": "2099-01-01", "read_by": "ghe-thi-cong",
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

    def test_status_needs_independent_audit(self):
        cited = dict(NOTE, status="CITED")
        self._note(cited)
        self.assertTrue(any("L-09" in e for e in self._check()[0]))
        a = self.tmp / "library" / "audits"; a.mkdir()
        (a / f"{NOTE['id']}.json").write_text(json.dumps({"note_id": NOTE["id"], "auditor": "ghe-thi-cong", "verdict": "PASS"}), encoding="utf-8")
        self.assertTrue(any("L-09" in e for e in self._check()[0]))          # tự chấm mình: không tính
        (a / f"{NOTE['id']}.json").write_text(json.dumps({"note_id": NOTE["id"], "auditor": "Owner", "verdict": "PASS"}), encoding="utf-8")
        self.assertEqual(self._check()[0], [])

    def test_outdated_source_warns_then_marked(self):
        self._note(NOTE)
        self._manifest({"luat_ke_toan_88_2015": dict(self.entry, superseded_by="luat_ke_toan_moi")})
        errs, warns = self._check()
        self.assertEqual(errs, [])
        self.assertTrue(any("OUTDATED" in w for w in warns))
        self.assertEqual(kn.mark_outdated(self.tmp, date(2026, 11, 17)), [NOTE["id"]])
        self.assertEqual(json.loads((self.tmp / "library" / "notes" / f"{NOTE['id']}.json").read_text(encoding="utf-8"))["status"], "OUTDATED")
        self.assertEqual(self._check(), ([], []))

    def test_bad_dates_are_errors_not_crashes(self):
        self._note(dict(NOTE, review_by="31/12/2026"))
        self._manifest({"luat_ke_toan_88_2015": dict(self.entry, effective_to="sau nay")})
        errs, _ = self._check()
        self.assertTrue(any("review_by" in e for e in errs), errs)
        self.assertTrue(any("effective_to" in e for e in errs), errs)

    def test_personal_data_l03(self):
        (self.tmp / "governance" / "ghi_chu.md").write_text("Phân tích NIM của ngân hàng.\n", encoding="utf-8")
        self.assertEqual(laws_checks.check_personal_data(self.tmp), [])
        (self.tmp / "governance" / "ghi_chu.md").write_text("Số tài khoản: 0123 4567 8910\n", encoding="utf-8")
        self.assertTrue(laws_checks.check_personal_data(self.tmp))
        (self.tmp / "governance" / "ghi_chu.md").write_text("CCCD 001234567890\n", encoding="utf-8")
        self.assertTrue(laws_checks.check_personal_data(self.tmp))


if __name__ == "__main__":
    unittest.main()
