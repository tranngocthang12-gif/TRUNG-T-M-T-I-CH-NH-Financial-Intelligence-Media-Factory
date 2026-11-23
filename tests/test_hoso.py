"""Test cho bộ công cụ hồ sơ mã tools/hoso/ (ADR-0020). Chỉ dùng doanh nghiệp giả ở templates/hoso/vi_du/:
kho công khai không chứa hồ sơ thật, tệp gốc thật hay số liệu riêng của Owner."""
import pathlib
import shutil
import sys
import tempfile
import unittest
from decimal import Decimal

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import laws_checks  # noqa: E402
from tools.hoso import gai_loi, kiem_luat, kiem_so_lieu, kiem_trich_dan, nhan_tep, phieu_may  # noqa: E402
from tools.hoso.chung import KhoTrang, tim_so, tinh_bieu_thuc  # noqa: E402

VI_DU = ROOT / "templates" / "hoso" / "vi_du"


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
        self.them_sau("## Mục 6. Chất lượng lợi nhuận",
                      "Giá vốn 840 tỷ đồng trên doanh thu 1.200 tỷ đồng, tức 70,0%. [ĐÃ KIỂM D1 tr.1]")
        kq = self.trich_dan()
        self.assertEqual(kq["loi"], [])
        self.assertEqual(kq["dem"]["TÍNH"], 1)

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

    def test_ngoai_le_phai_co_ly_do_va_khong_de_thua(self):
        self.sua("HO_SO_MAU.md", "| 12,50% |", "| 15,20% |")
        (self.tm / "ngoai_le.csv").write_text(
            "so,ngu_canh,ly_do\n\"15,20\",Nguyễn Văn A,ví dụ: số lấy từ ảnh chữ ký máy không đọc được\n", encoding="utf-8")
        kq = self.trich_dan()
        self.assertEqual((kq["loi"], kq["dem"]["NGOẠI LỆ"], len(kq["ngoai_le"])), ([], 1, 1))
        self.assertIn("NGOẠI LỆ: 15,20", phieu_may.lap_phieu(self.tm, self.ho_so)[0])
        self.sua("HO_SO_MAU.md", "| 15,20% |", "| 12,50% |")       # hết cần mà còn để: báo lỗi
        self.assertTrue(any("ngoai_le.csv" in x for x in self.trich_dan()["loi"]))


class SoLieuTests(HoSoBase):
    def _may_doc_sai(self):
        """Giả lập máy nhận dạng đọc 135.000 thành 125.000 trên trang, và sổ chép đúng theo máy."""
        self.sua("trang/D2/p001.txt", "135.000", "125.000")
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
