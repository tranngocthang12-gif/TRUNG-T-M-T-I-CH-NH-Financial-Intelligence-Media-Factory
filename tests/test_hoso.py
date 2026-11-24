"""Test cho bộ công cụ hồ sơ mã tools/hoso/ (ADR-0020). Chỉ dùng doanh nghiệp giả ở templates/hoso/vi_du/:
kho công khai không chứa hồ sơ thật, tệp gốc thật hay số liệu riêng của Owner."""
import pathlib
import re
import shutil
import sys
import tempfile
import unittest
from decimal import Decimal
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import laws_checks  # noqa: E402
from tools.hoso import gai_loi, kiem_luat, kiem_so_lieu, kiem_trich_dan, nhan_tep, phieu_may  # noqa: E402
from tools.hoso.chung import KhoTrang, sha256_tep, tim_so, tinh_bieu_thuc  # noqa: E402

VI_DU = ROOT / "templates" / "hoso" / "vi_du"
MUC_8 = "**Chưa viết.** Theo ADR-0019 QĐ-P13, mục này chỉ viết sau khi Owner sửa L-02."
MUC_9 = "## Mục 9. Thị trường chung và chu kỳ"


class HoSoBase(unittest.TestCase):
    def setUp(self):
        self.tm = pathlib.Path(tempfile.mkdtemp())
        shutil.copytree(VI_DU, self.tm, dirs_exist_ok=True)
        nhan_tep.nhan(self.tm, self.tm / "ma_nguon.csv")
        self.ho_so = self.tm / "HO_SO_MAU.md"
        self.addCleanup(shutil.rmtree, self.tm, True)

    def sua(self, ten, cu, moi, lan=1):
        p = self.tm / ten
        chu = p.read_text(encoding="utf-8")
        self.assertEqual(chu.count(cu), lan, f"{cu!r} phải có đúng {lan} lần trong {ten}")
        p.write_text(chu.replace(cu, moi), encoding="utf-8")

    def them_sau(self, moc, doan):
        self.sua("HO_SO_MAU.md", moc, moc + "\n\n" + doan)

    def trich_dan(self):
        return kiem_trich_dan.kiem(self.tm, self.ho_so.read_text(encoding="utf-8"))

    def luat(self):
        return kiem_luat.kiem(self.ho_so.read_text(encoding="utf-8"), self.tm)

    def phieu(self):
        return phieu_may.lap_phieu(self.tm, self.ho_so)

    def ngoai_le(self, *dong, cot="so,ngu_canh,ly_do,nguon,trang"):
        (self.tm / "ngoai_le.csv").write_text(cot + "\n" + "".join(d + "\n" for d in dong), encoding="utf-8")

    def them_dong(self, ten, *dong):
        with open(self.tm / ten, "a", encoding="utf-8") as f:
            f.write("".join(d + "\n" for d in dong))

    def doc_sai(self, tep, *thay):
        """Giả lập máy đọc sai: đổi tệp gốc giả (mỗi mẫu đúng một chỗ) rồi nhận lại, ghim lại sha256 trong bảng nguồn."""
        goc = self.tm / "goc" / tep
        cu, chu = sha256_tep(goc)[:12], goc.read_text(encoding="utf-8")
        for a, b in thay:
            self.assertEqual(len(re.findall(a, chu)), 1, a)
            chu = re.sub(a, b, chu)
        goc.write_text(chu, encoding="utf-8")
        nhan_tep.nhan(self.tm, self.tm / "ma_nguon.csv")
        self.sua("HO_SO_MAU.md", f"| {cu} |", f"| {sha256_tep(goc)[:12]} |")


class DocSoTests(unittest.TestCase):
    def test_so_kieu_viet(self):
        so = {s.raw: s for s in tim_so("Doanh thu 1.234.567,89; lỗ (1.193); tăng 10–15% và −4,5%; mã VN30, D1.")}
        self.assertEqual(so["1.234.567,89"].gia_tri, Decimal("1234567.89"))
        self.assertEqual(so["1.193"].gia_tri, Decimal(-1193))
        self.assertEqual(so["10"].gia_tri, Decimal(10))            # gạch nối trong khoảng 10–15 không phải dấu âm
        self.assertTrue(so["15"].pt and so["15"].gia_tri == 15)
        self.assertEqual(so["4,5"].gia_tri, Decimal("-4.5"))
        self.assertNotIn("30", so)                                 # số dính liền chữ không phải số liệu

    def test_so_kieu_anh_va_tep_lan_hai_kieu(self):
        self.assertEqual([s.gia_tri for s in tim_so("1,885,727,648 và 46.85", "en")], [Decimal(1885727648), Decimal("46.85")])
        ca_hai = {s.gia_tri for s in tim_so("171.401.226 cổ phiếu; room 447,487,205", "ca_hai")}
        self.assertTrue({Decimal(171401226), Decimal(447487205)} <= ca_hai)

    def test_bieu_thuc_chi_cho_phep_so_hoc(self):
        self.assertEqual(tinh_bieu_thuc("(a - b) / b * 100", {"a": Decimal(120), "b": Decimal(100)}), Decimal(20))
        for xau in ("__import__('os').system('true')", "a.real", "[a]", "a if a else b", "a ** 9", "abs(a)"):
            with self.assertRaises((ValueError, KeyError, SyntaxError)):
                tinh_bieu_thuc(xau, {"a": Decimal(1), "b": Decimal(1)})


class SoCanKiemTests(unittest.TestCase):
    def test_bo_ngay_thang_va_ma_nhung_giu_so_lieu(self):
        raw = [s.raw for s in kiem_trich_dan.so_can_kiem(
            "Ngày 30/09/2026 (quý 3, mục 5, QĐ-P13, D5 tr.8–9): 9 tháng 2026 đạt 8.770 tỷ so với cùng kỳ 7.495 tỷ, "
            "tăng 17,0%; 33.000 người; 3 mảng; năm 2025 là 1.200.")]
        self.assertEqual(raw, ["8.770", "7.495", "17,0", "33.000", "1.200"])

    def test_dia_chi_trong_nhan(self):
        self.assertEqual(kiem_trich_dan.doc_dia_chi("[ĐÃ KIỂM D1 tr.8–11; D5 tr.3, tr.7; G2]"),
                         {"D1": {8, 9, 10, 11}, "D5": {3, 7}, "G2": None})
        self.assertEqual(kiem_trich_dan.loai_nhan("[SUY LUẬN, tính từ số ĐÃ KIỂM ở D1 tr.12]"), "SUY LUẬN")


class PhieuMayTests(HoSoBase):
    def test_vi_du_dat_va_phieu_chay_lai_duoc(self):
        phieu, dat = phieu_may.lap_phieu(self.tm, self.ho_so)
        self.assertTrue(dat, phieu)
        self.assertIn("KẾT LUẬN: ĐẠT", phieu)
        self.assertEqual(phieu, phieu_may.lap_phieu(self.tm, self.ho_so)[0])   # không có giờ chạy: chạy lại ra đúng phiếu cũ
        self.sua("HO_SO_MAU.md", "Bản đầu", "Bản đầu.")
        self.assertNotEqual(phieu, phieu_may.lap_phieu(self.tm, self.ho_so)[0])  # sửa hồ sơ một chữ là phiếu cũ hết giá trị

    def test_tep_goc_bi_doi_thi_dung_ngay(self):
        with open(self.tm / "goc" / "gia_mau.csv", "a", encoding="utf-8") as f:
            f.write("24/11/2026,27.00,1\n")
        self.assertTrue(any("sha256" in x for x in nhan_tep.kiem_ke(self.tm)))
        phieu, dat = phieu_may.lap_phieu(self.tm, self.ho_so)
        self.assertFalse(dat)
        self.assertNotIn("2. Sổ số liệu", phieu)

    def test_thieu_dang_thuc_cua_mot_bao_cao(self):
        chu = (self.tm / "quan_he.csv").read_text(encoding="utf-8")
        (self.tm / "quan_he.csv").write_text("\n".join(d for d in chu.splitlines() if not d.startswith("cdkt")), encoding="utf-8")
        phieu, dat = phieu_may.lap_phieu(self.tm, self.ho_so)
        self.assertFalse(dat)
        self.assertIn("'cdkt'", phieu)


class TrichDanTests(HoSoBase):
    def test_so_khong_co_tren_trang(self):
        self.sua("HO_SO_MAU.md", "| 12,50% |", "| 15,20% |")
        loi = self.trich_dan()["loi"]
        self.assertEqual(len(loi), 1)
        self.assertIn("15,20", loi[0])
        self.assertIn("không có trên trang", loi[0])

    def test_ghi_sai_trang_cung_bi_bat(self):
        (self.tm / "trang" / "D1" / "p002.txt").write_text("Trang hai không có số nào.\n", encoding="utf-8")
        self.sua("HO_SO_MAU.md", "là 250 tỷ đồng, nợ phải trả là 400 tỷ đồng, vốn chủ sở hữu là 500 tỷ đồng. [ĐÃ KIỂM D1 tr.1]",
                 "là 250 tỷ đồng, nợ phải trả là 400 tỷ đồng, vốn chủ sở hữu là 500 tỷ đồng. [ĐÃ KIỂM D1 tr.2]")
        self.assertEqual(len(self.trich_dan()["loi"]), 3)

    def test_khong_cho_tinh_vong(self):
        # ba số tự khớp nhau (777 − 333 = 444) nhưng không số nào có trên trang: không được coi là lần ra
        self.them_sau("## Mục 5. Sức khỏe tài chính",
                      "Tiền gửi là 777 tỷ đồng, nợ vay là 333 tỷ đồng, tiền ròng là 444 tỷ đồng. [ĐÃ KIỂM D1 tr.1]")
        kq = self.trich_dan()
        self.assertEqual(kq["dem"]["KHÔNG LẦN RA"], 3)

    def test_tinh_tu_so_da_lan_ra(self):
        truoc = self.trich_dan()["dem"]["TÍNH"]
        self.them_sau("## Mục 6. Chất lượng lợi nhuận",
                      "Giá vốn 840 tỷ đồng trên doanh thu 1.200 tỷ đồng, tức 70,0%. [ĐÃ KIỂM D1 tr.1]")
        kq = self.trich_dan()
        self.assertEqual(kq["loi"], [])
        self.assertEqual(kq["dem"]["TÍNH"], truoc + 1)

    def test_doan_co_so_ma_khong_nhan(self):
        self.them_sau("## Mục 9. Thị trường chung và chu kỳ", "Doanh thu năm tới ước 1.444 tỷ đồng.")
        kq = self.trich_dan()
        self.assertEqual(kq["dem"]["CHƯA GẮN NHÃN"], 1)
        self.assertIn("không có nhãn", kq["loi"][0])

    def test_suy_luan_khong_bi_chan_nhung_duoc_dem(self):
        self.them_sau("## Mục 9. Thị trường chung và chu kỳ", "Doanh thu năm tới ước 1.444 tỷ đồng. [GIẢ ĐỊNH]")
        kq = self.trich_dan()
        self.assertEqual(kq["loi"], [])
        self.assertEqual(kq["dem"]["MÁY KHÔNG KIỂM"], 1)

    def test_ma_nguon_la(self):
        self.them_sau("## Mục 9. Thị trường chung và chu kỳ", "Ngành tăng 12,3% năm 2025. [ĐÃ KIỂM Z9 tr.1]")
        kq = self.trich_dan()
        self.assertEqual(kq["dem"]["ĐỊA CHỈ SAI"], 1)

    def test_ngoai_le_khong_con_la_duong_lan_ra(self):
        # vòng sửa 2 (Owner quyết 24/11/2026: bỏ hẳn ngoại lệ): dòng ngoại lệ đủ cột trước đây cho số này qua, nay không
        self.sua("HO_SO_MAU.md", "| 12,50% |", "| 15,20% |")
        self.ngoai_le('"15,20",Nguyễn Văn A,ví dụ: số lấy từ ảnh chữ ký máy không đọc được,D1,1')
        kq = self.trich_dan()
        self.assertEqual(kq["dem"]["KHÔNG LẦN RA"], 1)
        self.assertTrue(any("ngoai_le.csv: tệp không còn được dùng" in x for x in kq["loi"]))
        self.assertFalse(self.phieu()[1])


class SoLieuTests(HoSoBase):
    def _may_doc_sai(self):
        """Giả lập máy nhận dạng đọc 135.000 thành 125.000, và sổ chép đúng theo máy. Trang do máy tách ra nên không sửa tay
        được (trang_sha256.csv): giả lập bằng cách đổi tệp gốc giả rồi nhận lại, và ghim lại sha256 trong bảng nguồn."""
        cu = sha256_tep(self.tm / "goc" / "bctc_mau_q3_2026.txt")[:12]
        self.sua("goc/bctc_mau_q3_2026.txt", "135.000", "125.000")
        nhan_tep.nhan(self.tm, self.tm / "ma_nguon.csv")
        self.sua("HO_SO_MAU.md", f"| {cu} |", f"| {sha256_tep(self.tm / 'goc' / 'bctc_mau_q3_2026.txt')[:12]} |")
        self.sua("so_lieu.csv", "q3_lntt_9t25,D2,1,135.000,,trieu,,", "q3_lntt_9t25,D2,1,125.000,,trieu,,")

    def test_phep_tru_hang_bat_chu_so_doc_sai(self):
        self._may_doc_sai()
        kho = KhoTrang(self.tm)
        sl = kiem_so_lieu.doc_so_lieu(kho)
        self.assertEqual(sl["loi"], [])                            # số có trên trang: đối chiếu trích dẫn không bắt được
        qh = kiem_so_lieu.kiem_quan_he(kho, sl["bien"])
        self.assertEqual(len(qh["loi"]), 1)                        # phép trừ của chính hàng đó thì bắt được
        self.assertIn("lợi nhuận trước thuế 9 tháng", qh["loi"][0])
        nghi = kiem_so_lieu.soat_bang(kho)["nghi"]
        self.assertEqual(len(nghi), 1)
        self.assertIn("125.000 → 135.000", nghi[0]["mo_ta"])

    def test_sua_phai_co_ghi_chu_va_hien_tren_phieu(self):
        self._may_doc_sai()
        self.assertFalse(phieu_may.lap_phieu(self.tm, self.ho_so)[1])
        self.sua("so_lieu.csv", "q3_lntt_9t25,D2,1,125.000,,trieu,,", "q3_lntt_9t25,D2,1,125.000,135.000,trieu,,")
        self.assertTrue(any("không có ghi_chu" in x for x in kiem_so_lieu.doc_so_lieu(KhoTrang(self.tm))["loi"]))
        self.sua("so_lieu.csv", "q3_lntt_9t25,D2,1,125.000,135.000,trieu,,",
                 "q3_lntt_9t25,D2,1,125.000,135.000,trieu,máy đọc 3 thành 2: 168.000 − 33.000 = 135.000,")
        phieu, dat = phieu_may.lap_phieu(self.tm, self.ho_so)
        self.assertTrue(dat, phieu)
        self.assertIn("ĐÃ SỬA SO VỚI MÁY ĐỌC: q3_lntt_9t25", phieu)
        self.assertIn("chứng minh bằng đẳng thức «quý 3 2026: lợi nhuận trước thuế 9 tháng»", phieu)

    def test_chuoi_goc_phai_co_tren_trang(self):
        self.sua("so_lieu.csv", "kq25_thue,D1,1,36.000.000.000", "kq25_thue,D1,1,63.000.000.000")
        loi = kiem_so_lieu.doc_so_lieu(KhoTrang(self.tm))["loi"]
        self.assertTrue(any("không thấy '63.000.000.000'" in x for x in loi))

    def test_dong_tinh_sai_bi_bat(self):
        self.sua("so_lieu.csv", 'bien_gop_25,,,,"30,0"', 'bien_gop_25,,,,"33,0"')
        self.assertTrue(any("bien_gop_25" in x for x in kiem_so_lieu.doc_so_lieu(KhoTrang(self.tm))["loi"]))

    def test_soat_dong(self):
        self.assertEqual(kiem_so_lieu.soat_dong("LNTT  8.770.161  7.495.490  1.274.670  17,0%")[0][0], "khop")
        nghi = kiem_so_lieu.soat_dong("LNTT  8.770.161  7.485.490  1.274.670  17,0%")
        self.assertEqual(nghi[0][0], "nghi")
        self.assertIn("7.485.490 → 7.495.490", nghi[0][4])
        self.assertEqual(kiem_so_lieu.soat_dong("Năm 2024 2025 2026 và 1.500 6.250 7.750")[0][0], "khop")  # hàng cộng; bỏ qua năm
        self.assertEqual(kiem_so_lieu.soat_dong("Tài sản 5.123.456 9.876.543 1.111.111"), [])           # ba số không liên quan


class LuatTests(HoSoBase):
    def loi(self):
        return kiem_luat.kiem(self.ho_so.read_text(encoding="utf-8"), self.tm)

    def test_vi_du_sach(self):
        self.assertEqual(self.loi(), [])

    def test_dung_chung_bo_mau_l02_cua_kho(self):
        for mau in laws_checks.RECOMMEND_PATTERNS:
            self.assertIn(mau, kiem_luat._CAM.pattern)

    def test_cum_tu_l02(self):
        self.them_sau("## Mục 2. Loại doanh nghiệp", "Hồ sơ không nêu nên mua hay bán. [SUY LUẬN]")
        self.assertTrue(any("L-02" in x and "nên mua" in x for x in self.loi()))   # kiểm cứng: câu phủ định cũng bị bắt

    def test_muc_8_phai_trong(self):
        self.them_sau("**Chưa viết.** Theo ADR-0019 QĐ-P13, mục này chỉ viết sau khi Owner sửa L-02.",
                      "Khoảng giá trị 20,5 tới 30,5 nghìn đồng một cổ phiếu. [GIẢ ĐỊNH]")
        self.assertTrue(any(x.startswith("Mục 8") for x in self.loi()))

    def test_khung(self):
        self.sua("HO_SO_MAU.md", "## Mục 12. Ca tương tự, thành và bại", "## Ca tương tự")
        self.assertTrue(any(x.startswith("khung") for x in self.loi()))

    def test_gia_thuyet_va_diem_soi(self):
        self.sua("HO_SO_MAU.md", "| **H0 — Không có gì đặc biệt** |", "| **Giả thuyết ba** |")
        self.sua("HO_SO_MAU.md", "| 15 | Dấu hiệu", "| — | Dấu hiệu")
        loi = self.loi()
        self.assertTrue(any(x.startswith("Mục 11") and "H0" in x for x in loi))
        self.assertTrue(any("15 điểm soi" in x and "[15]" in x for x in loi))

    def test_bang_nguon_khop_sha256(self):
        self.sua("HO_SO_MAU.md", "| cb37fce58f1b |", "| cb37fce58f17 |")
        self.assertTrue(any("sha256 của D1" in x for x in self.loi()))


class KhoangGiaTests(HoSoBase):
    """Lỗi chặn 1 của bản chấm L-09 vòng 1, PR #117: mục 8 và khoảng giá lọt qua L-02 (QĐ-P13)."""

    def test_muc_8_chi_duoc_dung_cau_co_dinh(self):
        for them in ("Giá trị một cổ phiếu là 9 đồng.", "Giá trị một cổ phiếu là `45` nghìn đồng.", "Chưa có số.",
                     "| Kịch bản | |\n|---|---|\n| Cơ sở | |"):
            with self.subTest(them=them):
                chu = self.ho_so.read_text(encoding="utf-8")
                self.sua("HO_SO_MAU.md", MUC_8, MUC_8 + "\n" + them)
                self.assertTrue(any(x.startswith("Mục 8") for x in self.luat()))
                self.assertFalse(self.phieu()[1])
                self.ho_so.write_text(chu, encoding="utf-8")
        self.sua("HO_SO_MAU.md", MUC_8, "Chưa   viết.  Theo ADR-0019 **QĐ-P13**,\nmục này chỉ viết sau khi Owner sửa L-02.")
        self.assertEqual(self.luat(), [])                       # chỉ đổi chữ đậm và khoảng trắng: vẫn đạt

    def test_khoang_gia_gia_dinh_o_muc_khac(self):
        self.them_sau(MUC_9, "Khoảng giá trị 20,5–30,5 nghìn đồng. [GIẢ ĐỊNH]")
        self.assertEqual(self.trich_dan()["loi"], [])           # đối chiếu trích dẫn không kiểm đoạn GIẢ ĐỊNH
        self.assertTrue(any("khoảng giá «20,5–30,5 nghìn đồng»" in x for x in self.luat()))
        self.assertFalse(self.phieu()[1])

    def test_khoang_gia_suy_luan(self):
        self.them_sau(MUC_9, "Cổ phiếu có thể giao dịch từ 20,5 tới 30,5 nghìn đồng. [SUY LUẬN]")
        self.assertTrue(any("khoảng giá «20,5 tới 30,5 nghìn đồng»" in x for x in self.luat()))

    def test_khoang_gia_dang_bang(self):
        self.them_sau(MUC_9, "| Kịch bản | Giá trị (nghìn đồng) |\n|---|---:|\n| Cơ sở | 20,5–30,5 |\n\n[GIẢ ĐỊNH]")
        self.assertTrue(any("khoảng giá «20,5–30,5 nghìn đồng»" in x for x in self.luat()))   # đơn vị ở tiêu đề cột
        self.assertFalse(self.phieu()[1])

    def test_gia_tri_mot_co_phieu_theo_kich_ban_dang_bang(self):
        self.them_sau(MUC_9, "| Kịch bản | Giá trị một cổ phiếu (nghìn đồng) |\n|---|---:|\n| Xấu | 20,5 |\n| Tốt | 30,5 |"
                             "\n\n[GIẢ ĐỊNH]")
        self.assertEqual(sum("«Giá trị một cổ phiếu» đi với số" in x for x in self.luat()), 2)

    def test_khoang_nam_trong_nhan_cung_bi_bat(self):
        self.them_sau(MUC_9, "Các tệp hiện có không nói về ngành. [GIẢ ĐỊNH 20–30 nghìn đồng]")
        self.assertTrue(any("khoảng giá «20–30 nghìn đồng»" in x for x in self.luat()))

    def test_gia_qua_khu_da_kiem_tren_trang_thi_qua(self):
        self.them_sau(MUC_9, "Giá đóng cửa hai phiên nằm trong khoảng 25,40–26,10 nghìn đồng. [ĐÃ KIỂM G1]\n\n"
                             "Mức giá đóng cửa phiên 23/11/2026 là 26,10 nghìn đồng. [ĐÃ KIỂM G1]")
        self.assertEqual(self.luat(), [])
        self.assertTrue(self.phieu()[1])

    def test_mot_dau_khong_co_tren_trang_thi_bi_bat(self):
        self.them_sau(MUC_9, "Giá đóng cửa hai phiên nằm trong khoảng 25,40–29,10 nghìn đồng. [ĐÃ KIỂM G1]")
        self.assertTrue(any("khoảng giá «25,40–29,10 nghìn đồng»" in x for x in self.luat()))
        self.assertTrue(any("khoảng giá" in x for x in kiem_luat.kiem(self.ho_so.read_text(encoding="utf-8"))))  # không có trang


class DauVaDiaChiTests(HoSoBase):
    """Lỗi chặn 2: số sai dấu, dòng tính của sổ và trang không có thật không được coi là đã kiểm."""

    def test_so_am_khong_khop_so_duong_tren_trang(self):
        for viet in ("-1.200", "(1.200)", "−1.200"):
            with self.subTest(viet=viet):
                chu = self.ho_so.read_text(encoding="utf-8")
                self.sua("HO_SO_MAU.md", "Doanh thu thuần năm 2025 là 1.200 tỷ đồng, năm trước",
                         f"Doanh thu thuần năm 2025 là {viet} tỷ đồng, năm trước")
                loi = self.trich_dan()["loi"]
                self.assertEqual(len(loi), 1, loi)
                self.assertIn("1.200 — không có trên trang", loi[0])
                self.ho_so.write_text(chu, encoding="utf-8")

    def test_so_am_khong_tinh_ra_bang_phep_cong(self):
        # 1.000 + 200 = 1.200 đều có trên trang, nhưng tổng của hai số dương không ra số âm
        self.them_sau(MUC_9, "Doanh thu 2025 là -1.200 tỷ đồng, năm trước 1.000 tỷ đồng, tiền đầu năm 200 tỷ đồng. "
                             "[ĐÃ KIỂM D1 tr.1]")
        loi = self.trich_dan()["loi"]
        self.assertEqual(len(loi), 1, loi)
        self.assertIn("1.200 — không có trên trang", loi[0])

    def test_so_am_viet_dung_dau_van_qua(self):
        # tệp mẫu in lưu chuyển tiền đầu tư và tài chính trong ngoặc đơn (số âm)
        self.them_sau(MUC_9, "Lưu chuyển tiền từ đầu tư là (60) tỷ đồng, từ tài chính là -10 tỷ đồng, kinh doanh 120 tỷ đồng. "
                             "[ĐÃ KIỂM D1 tr.1]")
        kq = self.trich_dan()
        self.assertEqual(kq["loi"], [])
        self.assertTrue(self.phieu()[1])

    def test_dong_tinh_khong_hop_thuc_hoa_dia_chi_trang(self):
        self.them_sau(MUC_9, "Phải thu khách hàng tăng 36,4%. [ĐÃ KIỂM D2 tr.1]")
        loi = self.trich_dan()["loi"]
        self.assertEqual(len(loi), 1, loi)
        self.assertIn("36,4% — không có trên trang", loi[0])
        self.assertFalse(self.phieu()[1])

    def test_dong_goc_cua_so_chi_khop_dung_trang(self):
        # 135 (tỷ) là dòng gốc q3_lntt_9t25 của D2 tr.1 trong sổ; nhãn ghi D1 tr.1 thì không được dùng dòng đó
        self.them_sau(MUC_9, "Lợi nhuận trước thuế chín tháng năm trước là 135 tỷ đồng. [ĐÃ KIỂM D1 tr.1]")
        self.assertEqual(len(self.trich_dan()["loi"]), 1)

    def test_trang_khong_co_trong_kho(self):
        self.them_sau(MUC_9, "Phải thu khách hàng tăng 36,4%. [ĐÃ KIỂM D1 tr.99]")
        kq = self.trich_dan()
        self.assertEqual(kq["dem"]["ĐỊA CHỈ SAI"], 1)
        self.assertIn("D1 tr.99", kq["loi"][0])
        self.assertFalse(self.phieu()[1])

    def test_so_khong_nhan_khong_thanh_nhac_lai_hay_so(self):
        # 1.200 đã lần ra ở chỗ khác và 36,4 có trong sổ, nhưng đoạn không có nhãn thì vẫn là CHƯA GẮN NHÃN
        self.them_sau(MUC_9, "Doanh thu năm 2025 là 1.200 tỷ đồng, phải thu tăng 36,4%.")
        kq = self.trich_dan()
        self.assertEqual(kq["dem"]["CHƯA GẮN NHÃN"], 2)
        self.assertEqual(len(kq["loi"]), 2)


class BoNgoaiLeTests(HoSoBase):
    """Lỗi chặn 2a của bản chấm L-09 vòng 2: con số tự khai qua ngoại lệ. Owner quyết bỏ hẳn ngoại lệ (24/11/2026): con số
    máy không lần ra thì không mang nhãn ĐÃ KIỂM."""
    CAU = "Dự kiến doanh thu 2027 là 987,65 tỷ. [ĐÃ KIỂM D1 tr.1]"

    def test_vi_du_ban_cham_vong_2_nay_chua_dat(self):
        self.them_sau(MUC_9, self.CAU)
        self.ngoai_le('"987,65",Dự kiến doanh thu 2027,máy nhận dạng sai,D1,1')
        kq = self.trich_dan()
        self.assertTrue(any(": 987,65 — không có trên trang" in x for x in kq["loi"]), kq["loi"])
        self.assertTrue(any("ngoai_le.csv: tệp không còn được dùng" in x for x in kq["loi"]))
        phieu, dat = self.phieu()
        self.assertFalse(dat)
        self.assertNotIn("NGOẠI LỆ", phieu)

    def test_so_nho_nam_va_backtick_trong_doan_da_kiem_cung_phai_lan_ra(self):
        # so_can_kiem bỏ qua số nguyên dưới 10, năm và số trong backtick; trong đoạn ĐÃ KIỂM chúng vẫn phải có trên trang
        for cau, so in (("Dự kiến doanh thu 2027 là 9 nghìn tỷ đồng. [ĐÃ KIỂM D1 tr.1]", {"2027", "9"}),
                        ("Doanh thu năm tới là `987,65` tỷ đồng. [ĐÃ KIỂM D1 tr.1]", {"987,65"})):
            with self.subTest(cau=cau):
                chu = self.ho_so.read_text(encoding="utf-8")
                self.them_sau(MUC_9, cau)
                loi = self.trich_dan()["loi"]
                self.assertEqual({x.split(" — ")[0].split(": ")[1] for x in loi}, so, loi)
                self.assertFalse(self.phieu()[1])
                self.ho_so.write_text(chu, encoding="utf-8")
        self.them_sau(MUC_9, "Hai phiên quan sát đều thuộc 2026. [ĐÃ KIỂM G1]")    # 2026 có trên trang G1
        self.assertEqual(self.trich_dan()["loi"], [])
        self.assertTrue(self.phieu()[1])

    def test_tep_ngoai_le_con_trong_thu_muc_la_loi(self):
        self.ngoai_le()                                            # chỉ dòng tiêu đề, không dòng nào
        self.assertEqual(len(self.trich_dan()["loi"]), 1)
        self.assertFalse(self.phieu()[1])
        (self.tm / "ngoai_le.csv").unlink()
        self.assertTrue(self.phieu()[1])


class CongGiaTests(HoSoBase):
    """Lỗi chặn 1 của bản chấm L-09 vòng 2: giá mục tiêu lọt cổng L-02. Quy tắc cho phép (kiem_luat.kiem_cong_gia): giá cổ
    phiếu, hệ số định giá và vốn hóa chỉ được nêu dưới dạng số quá khứ có nguồn trong đoạn ĐÃ KIỂM, không kèm từ chỉ tương
    lai. Mọi ca DO đều cho phiếu ĐẠT tại 8a06134 (ca số tuyệt đối tính ra thì phiếu đã CHƯA ĐẠT vì mục 4, nhưng cổng luật
    không báo gì)."""
    DO = ("Dự kiến giá cổ phiếu MAU kỳ tới là 25,40 nghìn đồng. [GIẢ ĐỊNH]",
          "Giá cổ phiếu dự báo dao động từ 25,40 tới 26,10 nghìn đồng. [ĐÃ KIỂM G1]",
          "Dự kiến giá cổ phiếu MAU kỳ tới là 25,40. [GIẢ ĐỊNH]",
          "Kỳ vọng thị giá năm tới đạt 31.500 đ một cổ phiếu. [SUY LUẬN, tính từ D1 tr.1]",
          "Với P/E 15 lần và EPS 2.000 đồng, cổ phiếu đáng 30.000 đồng. [GIẢ ĐỊNH]",
          "Cổ phiếu sẽ về lại 25,40 nghìn đồng trong quý tới. [ĐÃ KIỂM G1]",
          "Tiềm năng tăng giá 35% trong mười hai tháng tới. [GIẢ ĐỊNH]",
          "P/E mục tiêu 15 lần. [GIẢ ĐỊNH]",
          "Vốn hóa có thể đạt 100.000 tỷ đồng. [GIẢ ĐỊNH]",
          "Mục tiêu mười hai tháng: 30 nghìn. [GIẢ ĐỊNH]",
          "Giá 26,10 nghìn đồng, tăng 10% tức 2,61, thành 28,71 nghìn đồng. [ĐÃ KIỂM G1]",
          "| Kịch bản | Giá (nghìn đồng) |\n|---|---:|\n| Cơ sở | 27,50 |\n\n[SUY LUẬN]")
    XANH = ("Giá vốn hàng bán năm 2025 là 840 tỷ đồng. [ĐÃ KIỂM D1 tr.1]",
            "Giá vốn bằng 70,0% doanh thu. [SUY LUẬN, sổ số liệu: bien_gop_25]",
            "Giá đóng cửa tăng từ 25,40 lên 26,10 nghìn đồng, tức 2,8%. [ĐÃ KIỂM G1]")

    def test_gia_tuong_lai_hay_khong_nguon_bi_bat(self):
        chu = self.ho_so.read_text(encoding="utf-8")
        for cau in self.DO:
            with self.subTest(cau=cau):
                self.ho_so.write_text(chu.replace(MUC_9, MUC_9 + "\n\n" + cau), encoding="utf-8")
                self.assertTrue(any("ngữ cảnh giá cổ phiếu" in x for x in self.luat()), self.luat())
                self.assertFalse(self.phieu()[1])

    def test_khong_bat_nham(self):
        # hồ sơ mẫu có: tiêu đề "Mục 8. Định giá theo khoảng", "Mục 10. … xu hướng giá", hàng G1 của Bảng nguồn, hàng
        # "Chi phí vốn hóa, trả trước" của bảng 15 điểm soi, câu giá đóng cửa ĐÃ KIỂM G1 ở mục 10
        self.assertEqual(kiem_luat.kiem_cong_gia(self.ho_so.read_text(encoding="utf-8"), KhoTrang(self.tm)), [])
        chu = self.ho_so.read_text(encoding="utf-8")
        for cau in self.XANH:
            with self.subTest(cau=cau):
                self.ho_so.write_text(chu.replace(MUC_9, MUC_9 + "\n\n" + cau), encoding="utf-8")
                self.assertEqual(self.luat(), [])
                self.assertTrue(self.phieu()[1])

    def test_tieu_de_va_bang_nguon_khong_lot(self):
        # tiêu đề, hàng tiêu đề bảng và bảng nguồn không mang nhãn: có dấu hiệu giá kèm số (không tính năm) là lỗi
        chu = self.ho_so.read_text(encoding="utf-8")
        for cu, moi in ((MUC_9, MUC_9 + "\n\n### Dự kiến giá cổ phiếu năm tới: 30.000 đồng\n\nCác tệp không nói. [CHƯA BIẾT]"),
                        (MUC_9, MUC_9 + "\n\n| Dự kiến giá 30.000 đồng |\n|---|\n\n[GIẢ ĐỊNH]"),
                        ("| G1 | Giá đóng cửa hai phiên", "| — | Dự kiến giá 30.000 đồng | — | — |\n| G1 | Giá đóng cửa hai phiên")):
            with self.subTest(moi=moi):
                self.ho_so.write_text(chu.replace(cu, moi), encoding="utf-8")
                self.assertTrue(any("tiêu đề hay bảng nguồn ở ngữ cảnh giá" in x for x in self.luat()), self.luat())
                self.assertFalse(self.phieu()[1])
        self.ho_so.write_text(chu.replace(MUC_9, MUC_9 + "\n\n### Giá đóng cửa 2024–2026\n\nCác tệp không nói. [CHƯA BIẾT]"),
                              encoding="utf-8")
        self.assertEqual(self.luat(), [])                                         # chỉ có năm: không bắt

    def test_danh_sach_loai_tru_la_hang_so(self):
        dh = kiem_luat.dau_hieu_gia
        for cum in kiem_luat.GIA_KHONG_TINH:
            self.assertEqual(dh(f"{cum[0].upper()}{cum[1:]} năm 2025 là 840 tỷ đồng"), [], cum)
        for cum in kiem_luat.VON_HOA_KHONG_TINH:
            self.assertEqual(dh(f"{cum} 12 tỷ đồng"), [], cum)
        self.assertEqual(dh("Chi phí vốn hoá, trả trước 12"), [])                 # biến thể "hoá"
        self.assertEqual(dh("Giá trị sổ sách 12 tỷ đồng"), [])
        for cum in kiem_luat.GIA_TRI_TINH:
            self.assertIn("(b) chữ «giá»", dh(f"Giá trị {cum} là 12"), cum)
        self.assertIn("(b) chữ «giá»", dh("Thị giá 25"))
        self.assertIn("(a) đơn vị giá", dh("Mục tiêu: 30 nghìn."))
        self.assertIn("(a) đơn vị giá", dh("EPS 2.880/cp"))
        self.assertEqual(dh("Khối lượng 30 nghìn cổ phiếu; doanh thu 1.200 tỷ đồng; quỹ 5 nghìn tỷ đồng"), [])
        self.assertIn("(c) hệ số định giá hoặc vốn hóa", dh("P / E 15 lần"))
        self.assertIn("(c) hệ số định giá hoặc vốn hóa", dh("vốn hoá 100 tỷ đồng"))


class ChungMinhSuaTests(HoSoBase):
    """Lỗi chặn 2b của bản chấm L-09 vòng 2: dòng sửa trong sổ (gia_tri khác máy đọc) chỉ kèm ghi chú chữ vẫn đi đường SỔ.
    Nay dòng sửa phải cách chuỗi máy đọc không quá hai ký tự và có đẳng thức cộng trừ trong quan_he.csv chứng minh."""
    SUA = "x_sua,D1,1,36.000.000.000,37.000.000.000,dong,máy đọc 7 thành 6 (giả),"

    def cho(self, khoa):
        return [x for x in kiem_so_lieu.doc_so_lieu(KhoTrang(self.tm))["loi"] if "CHỜ CHỨNG MINH" in x and f"'{khoa}'" in x]

    def test_x_bia_cua_kien_truc_su(self):
        self.them_dong("so_lieu.csv", "x_bia,D1,1,36.000.000.000,987.650.000.000,dong,máy đọc sai,")
        self.them_sau(MUC_9, "Dự kiến doanh thu 2027 là 987,65 tỷ. [ĐÃ KIỂM D1 tr.1]")
        self.assertTrue(self.cho("x_bia"))
        self.assertTrue(any(": 987,65 — không có trên trang" in x for x in self.trich_dan()["loi"]))
        phieu, dat = self.phieu()
        self.assertFalse(dat)
        self.assertIn("x_bia", phieu)

    def test_dang_thuc_khong_chung_minh_duoc(self):
        so_lieu = (self.tm / "so_lieu.csv").read_text(encoding="utf-8")
        quan_he = (self.tm / "quan_he.csv").read_text(encoding="utf-8")
        ca = {
            "hệ số gộp của khóa bằng 0": ([self.SUA], ["thu,x_sua - x_sua + kq25_dt,kq25_dt,0"], ["x_sua"]),
            "có hằng số": ([self.SUA], ["thu,x_sua,kq25_dt - 1163000000000,1"], ["x_sua"]),
            "sai_so lớn": ([self.SUA], ["thu,x_sua,kq25_thue,1.000.000.000"], ["x_sua"]),
            "khóa còn lại là dòng sửa chưa chứng minh": (
                [self.SUA, "y_sua,D1,1,10.000.000.000,11.000.000.000,dong,máy đọc 1 thành 0 (giả),"],
                ["thu,x_sua - y_sua,kq25_thue - lc25_tc,1"], ["x_sua", "y_sua"]),
            "dùng dòng tính": ([self.SUA, "z_tinh,,,,,dong,,kq25_thue + lc25_tc / 10"], ["thu,x_sua,z_tinh,1"], ["x_sua"]),
            "cách chuỗi máy đọc ba ký tự": (["x_xa,D1,1,36.000.000.000,144.000.000.000,dong,máy đọc sai (giả),"],
                                            ["thu,x_xa,kq25_lnst,1"], ["x_xa"]),
        }
        for ten, (dong_so, dong_qh, cho) in ca.items():
            with self.subTest(ca=ten):
                (self.tm / "so_lieu.csv").write_text(so_lieu, encoding="utf-8")
                (self.tm / "quan_he.csv").write_text(quan_he, encoding="utf-8")
                self.them_dong("so_lieu.csv", *dong_so)
                self.them_dong("quan_he.csv", *dong_qh)
                self.assertEqual(kiem_so_lieu.kiem_quan_he(KhoTrang(self.tm),
                                                           kiem_so_lieu.doc_so_lieu(KhoTrang(self.tm))["bien"])["loi"], [])
                for k in cho:
                    self.assertTrue(self.cho(k), (ten, k))
                self.assertFalse(self.phieu()[1])

    def test_hai_dong_sua_chung_minh_noi_tiep(self):
        # máy đọc sai giá vốn (840 → 870) và lợi nhuận gộp (360 → 350). Đẳng thức doanh thu − giá vốn = lợi nhuận gộp chứa
        # cả hai nên chưa chứng minh được dòng nào; lợi nhuận gộp được chứng minh trước bằng đẳng thức kế tiếp, rồi mới tới
        # giá vốn.
        self.doc_sai("bctc_mau_2025.txt", (r"840\.000\.000\.000", "870.000.000.000"), (r"360\.000\.000\.000", "350.000.000.000"))
        self.sua("so_lieu.csv", "kq25_gia_von,D1,1,840.000.000.000,,dong,,",
                 "kq25_gia_von,D1,1,870.000.000.000,840.000.000.000,dong,máy đọc 4 thành 7 (giả),")
        self.sua("so_lieu.csv", "kq25_ln_gop,D1,1,360.000.000.000,,dong,,",
                 "kq25_ln_gop,D1,1,350.000.000.000,360.000.000.000,dong,máy đọc 6 thành 5 (giả),")
        phieu, dat = self.phieu()
        self.assertTrue(dat, phieu)
        self.assertIn("kq25_ln_gop: máy đọc 350.000.000.000, ghế phân tích ghi 360.000.000.000 (D1 tr.1) — máy đọc 6 thành 5 "
                      "(giả); chứng minh bằng đẳng thức «kqkd 2025: lợi nhuận gộp − chi phí bán hàng và quản lý = lợi nhuận "
                      "trước thuế»", phieu)
        self.assertIn("chứng minh bằng đẳng thức «kqkd 2025: doanh thu thuần − giá vốn = lợi nhuận gộp»", phieu)

    def test_dong_chi_thieu_dau_cham(self):
        self.doc_sai("bctc_mau_q3_2026.txt", (r"1\.050\.000", "1.050000"))
        self.sua("so_lieu.csv", "q3_dt_9t26,D2,1,1.050.000,,trieu,,",
                 "q3_dt_9t26,D2,1,1.050000,1.050.000,trieu,máy đọc thiếu dấu chấm (giả),")
        phieu, dat = self.phieu()
        self.assertTrue(dat, phieu)
        self.assertIn("chứng minh bằng đẳng thức «quý 3 2026: doanh thu 9 tháng»", phieu)

    def test_khoang_cach_va_he_so(self):
        self.assertEqual(kiem_so_lieu.khoang_cach(kiem_so_lieu.day_so("(36.000.000.000)"), kiem_so_lieu.day_so("36000000000")), 0)
        self.assertEqual(kiem_so_lieu.khoang_cach("36000000000", "144000000000"), 3)
        self.assertEqual(kiem_so_lieu.he_so_cong_tru("a - (b - c) + -d"), {"a": 1, "b": -1, "c": 1, "d": -1})
        for xau in ("a - 1", "a * b", "a / b", "abs(a)", "a ** 2"):
            self.assertIsNone(kiem_so_lieu.he_so_cong_tru(xau), xau)


class VanTayTrangTests(HoSoBase):
    """Lỗi chặn 4: văn bản trang đã tách không sửa tay được mà kiểm nguồn vẫn đạt."""

    def test_nhan_ghi_dau_van_tay_tung_trang(self):
        van_tay = nhan_tep.doc_van_tay(self.tm)
        self.assertEqual(sorted(van_tay), [("D1", "p001.txt"), ("D2", "p001.txt"), ("G1", "p001.txt")])
        self.assertEqual(van_tay[("D1", "p001.txt")]["sha256"], sha256_tep(self.tm / "trang" / "D1" / "p001.txt"))
        self.assertEqual(nhan_tep.kiem_ke(self.tm), [])

    def test_sua_trang_sau_khi_nhan(self):
        with open(self.tm / "trang" / "D1" / "p001.txt", "a", encoding="utf-8") as f:
            f.write("Dữ liệu bổ sung: 987,65 tỷ đồng\n")
        self.them_sau(MUC_9, "Dữ liệu bổ sung 987,65 tỷ. [ĐÃ KIỂM D1 tr.1]")
        self.assertEqual(self.trich_dan()["loi"], [])             # chính đối chiếu số thì bị lừa
        self.assertTrue(any("trang/D1/p001.txt đã bị sửa" in x for x in nhan_tep.kiem_ke(self.tm)))
        phieu, dat = self.phieu()
        self.assertFalse(dat)
        self.assertNotIn("4. Trích dẫn", phieu)                   # nguồn không đáng tin thì không kiểm tiếp

    def test_sua_ca_trang_lan_danh_muc_voi_tep_van_ban(self):
        p = self.tm / "trang" / "D1" / "p001.txt"
        p.write_text(p.read_text(encoding="utf-8") + "Dữ liệu bổ sung: 987,65 tỷ đồng\n", encoding="utf-8")
        dm = self.tm / "trang_sha256.csv"                        # sửa luôn cột sha256 của trang trong danh mục
        cu = nhan_tep.doc_van_tay(self.tm)[("D1", "p001.txt")]["sha256"]
        dm.write_text("".join(d.replace(cu, sha256_tep(p), 1) if d.startswith("D1,p001.txt,") else d
                              for d in dm.read_text(encoding="utf-8").splitlines(True)), encoding="utf-8")
        self.assertNotIn("đã bị sửa", " ".join(nhan_tep.kiem_ke(self.tm)))
        self.assertEqual(nhan_tep.kiem_ke(self.tm), ["D1: trang/D1/p001.txt khác văn bản tách lại từ tệp gốc"])

    def test_tep_trang_la_hoac_bi_xoa(self):
        (self.tm / "trang" / "D1" / "p001.tay.txt").write_text("987,65\n", encoding="utf-8")
        self.assertTrue(any("p001.tay.txt không có trong trang_sha256.csv" in x for x in nhan_tep.kiem_ke(self.tm)))
        self.assertFalse(self.phieu()[1])
        with self.assertRaises(SystemExit):                       # nhận lại cũng không hợp thức hóa tệp lạ
            nhan_tep.nhan(self.tm, self.tm / "ma_nguon.csv")
        (self.tm / "trang" / "D1" / "p001.tay.txt").unlink()
        nhan_tep.nhan(self.tm, self.tm / "ma_nguon.csv")
        (self.tm / "trang" / "D2" / "p001.txt").unlink()
        loi = nhan_tep.kiem_ke(self.tm)
        self.assertTrue(any("trang/D2/p001.txt có trong trang_sha256.csv mà đã mất" in x for x in loi))
        (self.tm / "trang_sha256.csv").unlink()
        self.assertTrue(nhan_tep.kiem_ke(self.tm)[0].startswith("thiếu trang_sha256.csv"))

    def test_doc_lai_hop_le_van_qua(self):
        with mock.patch.object(nhan_tep, "_chay", return_value="Doanh thu thuần 1.200.000.000.000\n"):
            ra = nhan_tep.doc_lai(self.tm, "D1", 1)
        self.assertEqual(ra.name, "p001.dpi400psm4.txt")
        self.assertEqual(nhan_tep.kiem_ke(self.tm), [])
        self.assertTrue(self.phieu()[1])
        nhan_tep.nhan(self.tm, self.tm / "ma_nguon.csv")          # nhận lại: bản đọc lại còn nguyên thì được giữ
        self.assertEqual(nhan_tep.kiem_ke(self.tm), [])
        with open(ra, "a", encoding="utf-8") as f:
            f.write("987,65\n")
        self.assertTrue(any("p001.dpi400psm4.txt đã bị sửa" in x for x in nhan_tep.kiem_ke(self.tm)))


class GaiLoiTests(HoSoBase):
    def test_tao_va_kiem(self):
        pb, np_ = gai_loi.tao(self.tm, self.ho_so, "12,50%", "15,20%")
        self.assertTrue(pb.read_text(encoding="utf-8").split("\n", 1)[0].endswith(gai_loi.HAU_TO))
        self.assertIn("15,20%", pb.read_text(encoding="utf-8"))
        self.assertNotIn("15,20%", self.ho_so.read_text(encoding="utf-8"))      # bản Owner không bị đụng tới
        ma = [d for d in np_.read_text(encoding="utf-8").splitlines() if d.startswith("- ma_nhan_tep: ")][0].split(": ")[1]
        self.assertEqual(len(ma), 8)
        self.assertIn(f"Mã nhận tệp: {ma}", pb.read_text(encoding="utf-8"))      # ghế khác hãng phải chép lại mã này
        self.assertNotIn("Mã nhận tệp", self.ho_so.read_text(encoding="utf-8"))
        self.assertEqual(kiem_luat.kiem(pb.read_text(encoding="utf-8"), self.tm), [])   # bản phản biện vẫn đúng khung
        self.assertEqual(gai_loi.kiem(self.ho_so, np_), [])
        self.assertTrue(gai_loi.kiem(pb, np_))                                    # đưa nhầm bản phản biện cho Owner: bị bắt

    def test_ho_so_con_loi_cu_van_gai_duoc(self):
        self.them_sau("## Mục 9. Thị trường chung và chu kỳ", "Doanh thu năm tới ước 1.444 tỷ đồng.")   # lỗi có sẵn: thiếu nhãn
        pb, np_ = gai_loi.tao(self.tm, self.ho_so, "7,25%", "9,25%")
        dong_pb = int([d for d in np_.read_text(encoding="utf-8").splitlines()
                       if d.startswith("- dong_trong_ban_phan_bien: ")][0].split(": ")[1])
        self.assertIn("9,25%", pb.read_text(encoding="utf-8").split("\n")[dong_pb - 1])

    def test_tu_choi_loi_gai_ngoai_tam_doi_chieu(self):
        with self.assertRaises(SystemExit):                                        # số SUY LUẬN: đối chiếu số không bắt được
            gai_loi.tao(self.tm, self.ho_so, "36,4%", "46,4%")
        with self.assertRaises(SystemExit):                                        # xuất hiện nhiều dòng: không rõ gài ở đâu
            gai_loi.tao(self.tm, self.ho_so, "1.200", "1.300")
        self.assertFalse((self.tm / "HO_SO_MAU_BAN_PHAN_BIEN.md").exists())


if __name__ == "__main__":
    unittest.main()
