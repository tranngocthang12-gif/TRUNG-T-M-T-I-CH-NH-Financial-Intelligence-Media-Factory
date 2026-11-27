"""Test cho ADR-0021: số SUY LUẬN gắn đúng khóa sổ (QĐ-K1), bảng định nghĩa (QĐ-K2), mục Trạng thái kiểm (QĐ-K3) và ba số
Owner tự mở do máy chọn (QĐ-K4). Chỉ dùng doanh nghiệp giả ở templates/hoso/vi_du/."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_hoso import MUC_9, HoSoBase  # noqa: E402
from tools.hoso import bang_dinh_nghia, kiem_luat, kiem_trich_dan  # noqa: E402

K = "[SUY LUẬN, sổ số liệu: phai_thu_tang_25]"                  # khóa phai_thu_tang_25 của hồ sơ mẫu: 36,3636
KD = "[SUY LUẬN, sổ số liệu: dt_tang_25]"                       # khóa dt_tang_25: 20,0
BANG = "| Chỉ tiêu | Tỷ lệ |\n|---|---:|\n"
DINH_TINH = "Phải thu tăng nhanh hơn doanh thu. "
TT_DU = ("- Phiếu máy: chưa làm.\n- Đối chiếu số khác hãng: chưa làm.\n- Phản biện khác hãng: chưa làm.\n"
         "- Owner tự mở ba số: chưa làm.")


class KhoaBase(HoSoBase):
    def chen(self, cau):
        self.sua("HO_SO_MAU.md", MUC_9, MUC_9 + "\n\n" + cau)

    def loi(self):
        return "\n".join(self.trich_dan()["loi"])


class SoSuyLuanGanKhoaTests(KhoaBase):
    def test_ho_so_mau_dat(self):
        kq = self.trich_dan()
        self.assertEqual(kq["loi"], [])
        self.assertEqual(kq["dem"]["KHÓA"], 4)
        self.assertTrue(self.phieu()[1])

    def test_so_cua_khoa_khac_bi_bat(self):
        # trước ADR-0021: 20,0 trùng dòng dt_tang_25 nên được đếm là SỔ và phiếu ĐẠT, dù nhãn gọi phai_thu_tang_25 (36,4)
        self.sua("HO_SO_MAU.md", "Phải thu khách hàng tăng 36,4%", "Phải thu khách hàng tăng 20,0%")
        loi = self.loi()
        self.assertIn("20,0% — đoạn SUY LUẬN: số không khớp khóa nào nhãn gọi tên (phai_thu_tang_25)", loi)
        self.assertIn("nhãn gọi khóa phai_thu_tang_25 (sổ: 36.3636)", loi)
        self.assertFalse(self.phieu()[1])

    def test_so_khong_co_trong_so_bi_bat(self):
        # trước ADR-0021: MÁY KHÔNG KIỂM, phiếu vẫn ĐẠT
        self.sua("HO_SO_MAU.md", "Phải thu khách hàng tăng 36,4%", "Phải thu khách hàng tăng 63,4%")
        self.assertIn("63,4% — đoạn SUY LUẬN", self.loi())
        self.assertFalse(self.phieu()[1])

    def test_mot_so_cho_hai_khoa(self):
        # một con số đứng cho hai khóa mà khóa thứ hai làm tròn ra số khác: chỉ chiều ngược bắt được
        self.them_dong("so_lieu.csv", "no_tren_ts_25,,,,,lan,,cd25_no / cd25_tong_ts")
        self.chen("Nợ phải trả bằng 0,8 lần vốn chủ sở hữu, tính theo cả hai cách. "
                  "[SUY LUẬN, sổ số liệu: no_tren_von_25, no_tren_ts_25]")
        loi = self.loi()
        self.assertIn("nhãn gọi khóa no_tren_ts_25 (sổ: 0.4444)", loi)
        self.assertNotIn("nhãn gọi khóa no_tren_von_25", loi)

    def test_khoa_khong_co_va_ten_sai(self):
        self.chen("Doanh thu tăng 20,0%. [SUY LUẬN, sổ số liệu: dt_tang_25, khong_co_khoa]")
        self.assertIn("khóa khong_co_khoa không có trong sổ số liệu", self.loi())
        self.sua("HO_SO_MAU.md", "dt_tang_25, khong_co_khoa]", "dt tăng hai năm]")
        self.assertIn("«dt tăng hai năm» không phải tên khóa sổ", self.loi())

    def test_ghi_chu_sau_dau_cham_phay(self):
        self.chen("Doanh thu tăng 20,0%, phải thu tăng nhanh hơn. "
                  "[SUY LUẬN, sổ số liệu: dt_tang_25; căn cứ thêm phai_thu_tang_25, không in số]")
        self.assertEqual(self.trich_dan()["loi"], [])
        self.assertTrue(self.phieu()[1])

    def test_khoa_can_cu_khong_in_so(self):
        self.chen("Doanh thu năm 2025 là 1.200 tỷ; phải thu tăng nhanh hơn. [SUY LUẬN, sổ số liệu: phai_thu_tang_25, dt_tang_25]")
        loi = self.loi()
        self.assertIn("nhãn gọi khóa phai_thu_tang_25", loi)
        self.assertIn("đặt sau dấu «;»", loi)
        self.sua("HO_SO_MAU.md", "[SUY LUẬN, sổ số liệu: phai_thu_tang_25, dt_tang_25]",
                 "[SUY LUẬN; căn cứ sổ: phai_thu_tang_25, dt_tang_25]")
        self.assertEqual(self.trich_dan()["loi"], [])

    def test_cau_dan_khong_chu_so_khong_xet_chieu_nguoc(self):
        self.chen("Phải thu tăng nhanh hơn doanh thu. [SUY LUẬN, sổ số liệu: phai_thu_tang_25, dt_tang_25]")
        self.assertEqual(self.trich_dan()["loi"], [])

    def test_so_dem_thoi_gian_sai_bi_bat(self):
        self.them_dong("so_lieu.csv", "ngay_thu_25,,,,,ngay,,cd25_phai_thu / kq25_dt * 365")
        self.chen("Số ngày thu tiền năm 2025 là 95 ngày. [SUY LUẬN, sổ số liệu: ngay_thu_25]")
        self.assertIn("nhãn gọi khóa ngay_thu_25", self.loi())

    def test_day_khoa(self):
        self.them_dong("so_lieu.csv", "x01,,,,,ty,,kq25_dt / 1000000000", "x02,,,,,ty,,kq24_dt / 1000000000",
                       "x03,,,,,ty,,kq25_lnst / 1000000000")
        self.chen("Ba con số: 1.200, 1.000 và 144 tỷ. [SUY LUẬN, sổ số liệu: x01 tới x03]")
        self.assertEqual(self.trich_dan()["loi"], [])
        self.sua("HO_SO_MAU.md", "x01 tới x03]", "x01 tới x04]")
        self.assertIn("khóa x04 không có trong sổ số liệu", self.loi())
        self.sua("HO_SO_MAU.md", "x01 tới x04]", "x01 tới y03]")
        self.assertIn("dãy «x01 tới y03» không hợp lệ", self.loi())
        self.sua("HO_SO_MAU.md", "x01 tới y03]", "x03 tới x01]")
        self.assertIn("dãy «x03 tới x01» không hợp lệ", self.loi())

    def test_hang_so_cong_thuc(self):
        self.them_dong("so_lieu.csv", "phan_49,,,,,dong,,cd25_no * 49 / 100")
        self.chen("Lấy 49% nợ phải trả được 196 tỷ. [SUY LUẬN, sổ số liệu: phan_49]")
        kq = self.trich_dan()
        self.assertEqual(kq["loi"], [])
        self.assertEqual(kq["dem"]["HẰNG SỐ"], 1)

    def test_nhac_lai_so_da_kiem(self):
        self.chen("Doanh thu 1.200 tỷ, tăng 20,0%. [SUY LUẬN, sổ số liệu: dt_tang_25]")
        kq = self.trich_dan()
        self.assertEqual(kq["loi"], [])
        self.assertEqual(kq["dem"]["NHẮC LẠI"], 1)

    def test_suy_luan_khong_khoa_la_tinh_nham(self):
        self.chen("Hai năm cộng lại, doanh thu là 2.200 tỷ. [SUY LUẬN]")
        self.assertIn("2.200 — đoạn SUY LUẬN: số không khớp khóa nào nhãn gọi tên (nhãn không gọi khóa nào)", self.loi())
        self.assertFalse(self.phieu()[1])

    def test_gia_dinh_va_chua_biet_chi_dem(self):
        self.chen("Giả sử biên lợi nhuận gộp giữ 31,5%. [GIẢ ĐỊNH] Tỷ lệ của năm sau là 77,7%. [CHƯA BIẾT]")
        kq = self.trich_dan()
        self.assertEqual(kq["loi"], [])
        self.assertEqual(kq["dem"]["MÁY KHÔNG KIỂM"], 2)

    def test_nhan_phu_ca_bang(self):
        self.chen("| Chỉ tiêu | Giá trị |\n|---|---:|\n| Doanh thu tăng | 20,0% |\n| Nợ trên vốn | 0,80 |\n\n"
                  "[SUY LUẬN, sổ số liệu: dt_tang_25, no_tren_von_25]")
        self.assertEqual(self.trich_dan()["loi"], [])

    def test_so_dem_thoi_gian_o_chieu_nguoc(self):
        self.them_dong("so_lieu.csv", "ngay_thu_25,,,,,ngay,,cd25_phai_thu / kq25_dt * 365")
        self.chen("Số ngày thu tiền năm 2025 là 91 ngày. [SUY LUẬN, sổ số liệu: ngay_thu_25]")
        self.assertEqual(self.trich_dan()["loi"], [])


class VongSua1Tests(KhoaBase):
    """Năm đầu vào của bản chấm L-09 vòng 1 (ChatGPT, CHƯA GỘP ĐƯỢC 3cb2d6f) và các ca cùng loại."""

    def test_loi_chan_1_so_trong_backtick(self):
        self.chen("Phải thu khách hàng tăng `63,4%`. [SUY LUẬN, sổ số liệu: phai_thu_tang_25]")
        loi = self.loi()
        self.assertIn("63,4% — đoạn SUY LUẬN: số không khớp khóa", loi)
        self.assertIn("nhãn gọi khóa phai_thu_tang_25", loi)
        self.assertFalse(self.phieu()[1])
        self.sua("HO_SO_MAU.md", "`63,4%`", "`36,4%`")
        self.assertEqual(self.trich_dan()["loi"], [])

    def test_loi_chan_2_hai_nhan_giong_nhau_trong_mot_doan(self):
        self.chen("Phải thu khách hàng tăng 100%. [SUY LUẬN, sổ số liệu: phai_thu_tang_25] Mức tăng phải thu theo sổ là 36,4%. "
                  "[SUY LUẬN, sổ số liệu: phai_thu_tang_25]")
        self.assertIn("nhãn gọi khóa phai_thu_tang_25", self.loi())
        self.assertFalse(self.phieu()[1])

    def test_loi_chan_3_so_so_lieu_sau_dau_cham_phay(self):
        self.chen("Phải thu khách hàng tăng 20,0%. [SUY LUẬN; căn cứ sổ số liệu: dt_tang_25]")
        loi = self.loi()
        self.assertIn("20,0% — đoạn SUY LUẬN: số không khớp khóa nào nhãn gọi tên (nhãn không gọi khóa nào)", loi)
        self.assertIn("«sổ số liệu:» đứng sau dấu «;» nên là ghi chú", loi)
        self.assertFalse(self.phieu()[1])

    def test_loi_chan_4_so_thu_tu_khong_phai_so_lieu(self):
        self.chen("1. Phải thu tăng nhanh hơn doanh thu. [SUY LUẬN, sổ số liệu: phai_thu_tang_25]")
        self.assertEqual(self.trich_dan()["loi"], [])
        self.assertTrue(self.phieu()[1])

    def test_nam_va_so_nho_khong_phai_so_lieu(self):
        self.chen("Năm 2025, sau 4 kỳ, phải thu tăng nhanh hơn doanh thu. [SUY LUẬN, sổ số liệu: phai_thu_tang_25]")
        self.assertEqual(self.trich_dan()["loi"], [])

    def test_bang_co_so_thu_tu_nhan_trong_o(self):
        self.chen("| # | Điểm | Kết quả | Nhãn |\n|---|---|---|---|\n"
                  "| 1 | Phải thu | Tăng nhanh hơn doanh thu | [SUY LUẬN, sổ số liệu: phai_thu_tang_25] |\n"
                  "| 2 | Doanh thu | Tăng 20,0% | [SUY LUẬN, sổ số liệu: dt_tang_25] |")
        self.assertEqual(self.trich_dan()["loi"], [])
        self.sua("HO_SO_MAU.md", "| Tăng 20,0% |", "| Tăng 36,4% |")
        self.assertIn("nhãn gọi khóa dt_tang_25", self.loi())

    def test_bang_nhan_o_doan_dan_gop_mot_pham_vi(self):
        # đoạn dẫn có số liệu, nhãn cuối đoạn phủ luôn bảng ngay dưới: khóa hiện ở bảng vẫn tính
        self.chen("Hai chỉ tiêu năm 2025, đơn vị phần trăm, theo sổ 30 dòng: [SUY LUẬN, sổ số liệu: dt_tang_25, phai_thu_tang_25]\n"
                  "| Chỉ tiêu | Giá trị |\n|---|---:|\n| Doanh thu tăng | 20,0% |\n| Phải thu tăng | 36,4% |")
        kq = self.trich_dan()
        self.assertNotIn("nhãn gọi khóa", "\n".join(kq["loi"]))

    def test_loi_chan_5_trang_thai_mot_dong(self):
        chu = self.ho_so.read_text(encoding="utf-8")
        dau = chu.index("## Trạng thái kiểm\n") + len("## Trạng thái kiểm\n")
        cuoi = chu.index("## Cách đọc")
        self.ho_so.write_text(chu[:dau] + "\n- Phiếu máy: chưa làm; Đối chiếu số khác hãng: chưa làm; Phản biện khác hãng: chưa "
                              "làm; Owner tự mở ba số: chưa làm.\n\n" + chu[cuoi:], encoding="utf-8")
        self.assertIn("thiếu hoặc trùng: «- Đối chiếu số khác hãng:», «- Phản biện khác hãng:», «- Owner tự mở ba số:»",
                      "\n".join(self.luat()))
        self.assertFalse(self.phieu()[1])

    def test_trang_thai_trung_dong(self):
        self.sua("HO_SO_MAU.md", "- **Phản biện khác hãng:** chưa làm (bước B7).",
                 "- **Phản biện khác hãng:** chưa làm (bước B7).\n- **Phản biện khác hãng:** chưa làm.")
        self.assertIn("thiếu hoặc trùng: «- Phản biện khác hãng:»", "\n".join(self.luat()))


class VongSua2Tests(KhoaBase):
    """Bốn đầu vào của bản chấm L-09 vòng 2 (ChatGPT, CHƯA GỘP ĐƯỢC c5becc5) và các ca cùng loại. Mỗi ca chèn vào dưới tiêu
    đề mục 9 của hồ sơ mẫu, trừ ca ghi khác."""

    def thu(self, cau, *so):
        """Chèn cau vào hồ sơ mẫu (thêm dòng so vào sổ số liệu); trả (mọi lỗi nối lại, phiếu có ĐẠT không) rồi khôi phục."""
        goc, so_goc = self.ho_so.read_text(encoding="utf-8"), (self.tm / "so_lieu.csv").read_text(encoding="utf-8")
        self.addCleanup(self.ho_so.write_text, goc, encoding="utf-8")
        self.addCleanup((self.tm / "so_lieu.csv").write_text, so_goc, encoding="utf-8")
        if so:
            self.them_dong("so_lieu.csv", *so)
        self.ho_so.write_text(goc.replace(MUC_9, MUC_9 + "\n\n" + cau, 1), encoding="utf-8")
        kq = "\n".join(self.trich_dan()["loi"] + self.luat()), self.phieu()[1]
        self.ho_so.write_text(goc, encoding="utf-8")
        (self.tm / "so_lieu.csv").write_text(so_goc, encoding="utf-8")
        return kq

    def chua_dat(self, ca):
        for ten, (cau, loi_can) in ca.items():
            with self.subTest(ten):
                loi, dat = self.thu(cau)
                self.assertIn(loi_can, loi, ten)
                self.assertFalse(dat, ten)

    def dat(self, ca):
        for ten, cau in ca.items():
            with self.subTest(ten):
                loi, dat = self.thu(cau)
                self.assertEqual(loi, "", ten)
                self.assertTrue(dat, ten)

    def thay_trang_thai(self, than):
        chu = self.ho_so.read_text(encoding="utf-8")
        dau = chu.index("## Trạng thái kiểm\n") + len("## Trạng thái kiểm\n")
        self.ho_so.write_text(chu[:dau] + "\n" + than + "\n\n" + chu[chu.index("## Cách đọc"):], encoding="utf-8")

    # ---------- lỗi chặn 1: định dạng làm biến đổi giá trị số
    def test_loi_chan_1_dinh_dang_khong_doi_con_so(self):
        khong_khop, dd = "đoạn SUY LUẬN: số không khớp khóa", "định dạng ngoài bộ cho phép — dấu ** hay ` chen vào con số"
        self.chua_dat({
            "bản chấm: dấu trừ ngoài backtick": ("Mức biến động phải thu là -`36,4%`. " + K, "36,4% — " + khong_khop),
            "bản chấm: chữ đậm cắt đôi số": ("Phải thu khách hàng tăng **6**3 phần trăm. " + K, "63 — " + khong_khop),
            "dấu trừ ngoài chữ đậm": ("Mức biến động phải thu là -**36,4%**. " + K, "36,4% — " + khong_khop),
            "dấu trừ in đậm riêng": ("Mức biến động phải thu là **-**36,4%. " + K, "36,4% — " + khong_khop),
            "ngoặc âm ngoài backtick": ("Mức biến động phải thu là (`36,4`) phần trăm. " + K, "36,4 — " + khong_khop),
            "backtick cắt phần lẻ": ("Phải thu khách hàng tăng `63`,4%. " + K, "63,4% — " + khong_khop),
            "chữ đậm cắt hàng nghìn": ("Phải thu khách hàng tăng **1**.193 phần trăm. " + K, "1.193 — " + khong_khop),
            "chữ đậm giấu số nhỏ có %": ("Phải thu khách hàng tăng **5**%. " + K, "5% — " + khong_khop),
            "chữ đậm trong ô bảng": (BANG + "| Phải thu tăng | **6**3 |\n\n" + K, "63 — " + khong_khop),
            "cổng định dạng: dấu trừ ngoài backtick": ("Mức biến động phải thu là -`36,4%`. " + K, dd),
            "cổng định dạng: chữ đậm cắt đôi số": ("Phải thu khách hàng tăng **6**3 phần trăm. " + K, dd),
            "cổng định dạng: số đậm dán vào chữ": ("Phải thu khách hàng tăng**63,4%**. " + K, dd),
            "mã có dấu cách sát mép": ("Mức biến động phải thu là -` 36,4% `. " + K, "mã «`…`» có dấu cách sát mép trong"),
            "gạch nối không ngắt làm dấu âm": ("Mức biến động phải thu là ‑36,4%. " + K, "U+2011"),
            "gạch dài dính số": ("Mức biến động phải thu là —36,4%. " + K, "U+2014"),
            "ký tự trống dán số vào chữ": ("Phải thu khách hàng tăngㅤ63,4%. " + K, "U+3164"),
            "ĐÃ KIỂM: dấu trừ ngoài backtick": ("Doanh thu thuần là -`1.200` tỷ đồng. [ĐÃ KIỂM D1 tr.1]",
                                                "1.200 — số nhỏ, năm hay số trong backtick ở đoạn ĐÃ KIỂM không có trên trang"),
            "số dương viết thành âm": ("Mức biến động phải thu là -36,4%. " + K, "36,4% — " + khong_khop),
        })
        self.dat({
            "đậm trọn số": "Phải thu khách hàng tăng **36,4%**. " + K,
            "mã trọn số": "Phải thu khách hàng tăng `36,4%`. " + K,
            "đậm số, % ngoài": "Phải thu khách hàng tăng **36,4**%. " + K,
            "ngoặc quanh số đậm có %": "Phải thu khách hàng tăng nhanh (**36,4%**). " + K,
            "đậm nhãn chữ, tên tệp trong mã": "**Lưu ý:** phải thu khách hàng tăng 36,4% (xem `so_lieu.csv`). " + K,
            "gạch dài có dấu cách": "Phải thu khách hàng tăng **36,4%** — nhanh hơn doanh thu. " + K,
            "khóa viết trong backtick": "Phải thu khách hàng tăng 36,4%. [SUY LUẬN, sổ số liệu: `phai_thu_tang_25`]",
            "nhãn in đậm": "Phải thu khách hàng tăng 36,4%. **" + K + "**",
        })
        loi, dat = self.thu("Mức chênh là **-26,7%**, tức −26,7%. [SUY LUẬN, sổ số liệu: am_25]",
                            "am_25,,,,,pt,,(cd24_phai_thu / cd25_phai_thu - 1) * 100")
        self.assertEqual((loi, dat), ("", True))                   # số âm thật khớp khóa âm, cả hai cách viết dấu

    def test_doc_so_tren_chu_hien_thi(self):
        ktd = kiem_trich_dan
        self.assertEqual(ktd.chu_hien("-`36,4%` và **6**3"), "-36,4% và 63")
        self.assertEqual([(s.raw, s.gia_tri < 0) for s in ktd.so_lieu_hien("-`36,4%`, **6**3, (**1.200**)")],
                         [("36,4", True), ("63", False), ("1.200", True)])
        self.assertEqual([s.raw for s in ktd.so_can_kiem("tăng **6**3 và **5**%")], ["63", "5"])
        self.assertEqual([s.raw for s in ktd.so_hien("**Tháng** 12 năm `2025`: 4 kỳ, 91 ngày")], ["4", "91"])
        k = kiem_luat.kiem_dinh_dang
        for xau in ("-`36,4%`", "**6**3", "-**36,4**", "(`36,4`)", "`63`,4", "**1**.193", "x**5**", "` 5`", "`5 `",
                    "a ** b", "** a**", "**a **", "`a**b**`", "—36", "‑5", "aㅤb", "a⠀b"):
            with self.subTest(xau):
                self.assertTrue(k(xau), repr(xau))
        for xau in ("**36,4%**", "`36,4%`", "**36,4** %", "(**36,4%**)", "**-5** tới **5**", "2024—2025", "a — 5",
                    "**1.** Doanh thu", "**Tháng 12**/2025", "| **A** | `b_c.txt` | 5 |\n|---|---|---:|\n| a | b | 6 |"):
            with self.subTest(xau):
                self.assertEqual(k(xau), [], repr(xau))

    # ---------- lỗi chặn 2: phạm vi theo lần xuất hiện của nhãn
    def test_loi_chan_2_pham_vi_theo_lan_xuat_hien_cua_nhan(self):
        nguoc = "nhãn gọi khóa phai_thu_tang_25 (sổ: 36.3636)"
        self.chua_dat({
            "bản chấm: nhãn cùng chữ sau bảng, cách một tiêu đề": (
                "Phải thu khách hàng tăng 100%. " + K + " Bảng sau ghi kết quả riêng.\n\n" + BANG
                + "| Phải thu tăng | 36,4% |\n\n### Ghi chú\n\n" + K, "dòng 89: " + nguoc),
            "như trên, nhãn ngay sau bảng": (
                "Phải thu khách hàng tăng 100%. " + K + " Bảng sau ghi kết quả riêng.\n\n" + BANG
                + "| Phải thu tăng | 36,4% |\n\n" + K, "dòng 89: " + nguoc),
            "đoạn dẫn kết bằng nhãn khác, nhãn cùng chữ sau bảng": (
                "Phải thu khách hàng tăng 100%. " + K + " Doanh thu tăng 20,0%. " + KD + "\n\n" + BANG
                + "| Phải thu tăng | 36,4% |\n\n" + K, "dòng 89: " + nguoc),
            "hai nhãn cùng chữ trong đoạn dẫn, bảng ngay dưới": (
                "Phải thu khách hàng tăng 100%. " + K + " Bảng dưới ghi số sổ. " + K + "\n" + BANG
                + "| Phải thu tăng | 36,4% |", "dòng 89: " + nguoc),
            "nhãn sau bảng cách một tiêu đề thì bảng không có nhãn": (
                BANG + "| Phải thu tăng | 36,4% |\n\n### Ghi chú\n\n" + K, "36,4% — đoạn có số mà không có nhãn"),
            "hai nhãn trong một hàng bảng": (
                "| Chỉ tiêu | A | B |\n|---|---|---|\n| Tăng | 20,0% " + KD + " | 20,0% " + K + " |", "hàng bảng có 2 nhãn"),
            "nhãn gọi khóa đứng sau một nhãn khác, không phủ chữ nào": (
                "Phải thu khách hàng tăng 63,4%. [GIẢ ĐỊNH] " + K, "nhãn gọi khóa (phai_thu_tang_25) nhưng không phủ chữ nào"),
            "nhãn giữa hai bảng, bảng dưới sai khóa": (
                BANG + "| Phải thu tăng | 36,4% |\n\n" + K + "\n\n" + BANG + "| Doanh thu tăng | 20,0% |", "20,0% — đoạn SUY LUẬN"),
        })
        self.dat({
            "đoạn dẫn kết bằng nhãn, bảng ngay dưới: một phạm vi":
                "Hai chỉ tiêu, đơn vị phần trăm: [SUY LUẬN, sổ số liệu: dt_tang_25, phai_thu_tang_25]\n" + BANG
                + "| Doanh thu tăng | 20,0% |\n| Phải thu tăng | 36,4% |",
            "đoạn dẫn kết bằng nhãn, cách dòng trống, rồi bảng": "Mức tăng phải thu, đơn vị phần trăm: " + K + "\n\n" + BANG
                + "| Phải thu tăng | 36,4% |",
            "một nhãn giữa hai bảng: một lần xuất hiện, một phạm vi":
                BANG + "| Doanh thu tăng | 20,0% |\n\n[SUY LUẬN, sổ số liệu: dt_tang_25, phai_thu_tang_25]\n\n" + BANG
                + "| Phải thu tăng | 36,4% |",
            "bảng có hàng mang nhãn riêng và nhãn sau bảng":
                "| Chỉ tiêu | Tỷ lệ | Nhãn |\n|---|---:|---|\n| Doanh thu tăng | 20,0% | " + KD
                + " |\n| Phải thu tăng | 36,4% | |\n\n" + K,
        })

    def test_pham_vi_nhan_theo_dinh_danh(self):
        chu = ("## Mục 9. Thị trường chung và chu kỳ\n\nA 100%. " + K + " B.\n\n" + BANG + "| x | 36,4% |\n\n### Ghi chú\n\n" + K
               + "\n\nC 36,4%. " + K + "\n" + BANG + "| y | 36,4% |\n")
        nhom = kiem_trich_dan.pham_vi_nhan(kiem_trich_dan.cac_phan_chu(chu))
        self.assertEqual([[p["chu"].strip() for p in ds] for ds in nhom.values()],
                         [["A 100%."], [""], ["C 36,4%.", "y | 36,4%"]])   # bảng đầu không có nhãn; bảng sau gộp với đoạn dẫn

    # ---------- lỗi chặn 3: ngày tháng không phải số đếm thời gian
    def test_loi_chan_3_ngay_thang_khong_phai_so_dem_thoi_gian(self):
        self.dat({
            "bản chấm: Tháng 12 năm 2025": "Tháng 12 năm 2025, phải thu tăng nhanh hơn doanh thu. " + K,
            "ngày 31 tháng 12 năm 2025": "Tới ngày 31 tháng 12 năm 2025, phải thu tăng nhanh hơn doanh thu. " + K,
            "quý 4 năm 2025": "Quý 4 năm 2025, phải thu tăng nhanh hơn doanh thu. " + K,
            "31/12/2025": "Tới 31/12/2025, phải thu tăng nhanh hơn doanh thu. " + K,
            "tháng 12/2025": "Tháng 12/2025, phải thu tăng nhanh hơn doanh thu. " + K,
            "chữ đậm quanh ngày tháng": "**Tháng 12 năm 2025**, phải thu tăng nhanh hơn doanh thu. " + K,
            "chữ đậm cắt ngang ngày tháng": "**Tháng** 12 năm `2025`, phải thu tăng nhanh hơn doanh thu. " + K,
            "hai năm": "So năm 2025 với năm 2024, phải thu tăng nhanh hơn doanh thu. " + K,
            "khóa căn cứ đặt sau dấu ;": "Trong 12 tháng qua, phải thu tăng nhanh hơn doanh thu. [SUY LUẬN; căn cứ sổ: phai_thu_tang_25]",
        })
        for cau, co in (("Tháng 12 năm 2025, phải thu tăng nhanh", False), ("ngày 31 tháng 12 năm 2025", False),
                        ("quý 4 năm 2025", False), ("trong 12 tháng qua", True), ("số ngày thu tiền là 95 ngày", True),
                        ("sau 4 kỳ", False), ("tăng 36,4%", True), ("tăng 63.4%", True)):
            with self.subTest(cau):
                self.assertEqual(kiem_trich_dan.co_so_lieu(cau), co)
        self.chua_dat({                                          # số đếm thời gian thật vẫn làm phạm vi «có số liệu»
            "12 tháng": ("Trong 12 tháng qua, phải thu tăng nhanh hơn doanh thu. " + K, "nhãn gọi khóa phai_thu_tang_25"),
        })

    # ---------- lỗi chặn 4: tiêu đề cấp hai lặp
    def test_loi_chan_4_tieu_de_cap_hai_lap(self):
        lap = "khung: tiêu đề cấp hai xuất hiện hơn một lần: '## Trạng thái kiểm'"
        goc = self.ho_so.read_text(encoding="utf-8")
        for ten, than, them in (
                ("bản chấm: mục đầu thiếu ba dòng, mục lặp đủ", "- Phiếu máy: chưa làm.\n\n## Trạng thái kiểm\n\n" + TT_DU,
                 "thiếu hoặc trùng: «- Đối chiếu số khác hãng:», «- Phản biện khác hãng:», «- Owner tự mở ba số:»"),
                ("cả hai mục đều đủ", TT_DU + "\n\n## Trạng thái kiểm\n\n" + TT_DU, lap)):
            with self.subTest(ten):
                self.thay_trang_thai(than)
                loi = "\n".join(self.luat())
                self.assertIn(lap, loi)
                self.assertIn(them, loi)
                self.assertFalse(self.phieu()[1])
                self.ho_so.write_text(goc, encoding="utf-8")
        self.ho_so.write_text(goc.rstrip("\n") + "\n\n## Trạng thái kiểm\n\n" + TT_DU + "\n", encoding="utf-8")
        self.assertIn(lap, "\n".join(self.luat()))                # mục lặp ở cuối hồ sơ
        self.ho_so.write_text(goc.replace("## Kết quả 15 điểm soi\n", "## Kết quả 15 điểm soi\n\n| # | Điểm soi |\n|---|---|\n"
                                          "| 1 | Chỉ một dòng |\n\n## Kết quả 15 điểm soi\n", 1), encoding="utf-8")
        loi = "\n".join(self.luat())
        self.assertIn("xuất hiện hơn một lần: '## Kết quả 15 điểm soi'", loi)
        self.assertIn("Kết quả 15 điểm soi: thiếu dòng [2, 3,", loi)   # xét thân của lần xuất hiện đầu tiên
        self.ho_so.write_text(goc, encoding="utf-8")
        self.thay_trang_thai(TT_DU)
        self.assertEqual(self.luat(), [])
        self.assertTrue(self.phieu()[1])

    # ---------- cùng loại: con số ở chỗ máy trước đó không đọc
    def test_so_thu_tu_chi_o_dau_muc_cua_danh_sach_danh_dung(self):
        ds = "\n".join(f"{i}. Ý định tính. [SUY LUẬN]" for i in range(1, 13))
        self.chua_dat({
            "63. nối tiếp một đoạn": ("Phải thu khách hàng tăng nhanh, mức tăng tính theo phần trăm là\n63. " + K, "63 — đoạn SUY LUẬN"),
            "63. sau dòng trống": ("Mức tăng phải thu tính theo phần trăm là:\n\n63. " + K, "63 — đoạn SUY LUẬN"),
            "63. đứng giữa đoạn, sau một nhãn": (DINH_TINH + "[SUY LUẬN] 63. " + K, "63 — đoạn SUY LUẬN"),
            "63. trong ô bảng": ("| Chỉ tiêu | Tỷ lệ |\n|---|---|\n| Phải thu tăng | 63. " + K + " |", "63 — đoạn SUY LUẬN"),
            "số đậm 63. đầu đoạn": ("**63.** Phải thu khách hàng tăng, tính theo phần trăm. " + K, "63 — đoạn SUY LUẬN"),
            # dãy 1..9, 13, 11, 12 không phải 1, 2, …, n: số đầu mục từ 10 trở lên là con số (13 và 12 tình cờ trùng số
            # ĐÃ KIỂM 12,50 sau làm tròn nên là NHẮC LẠI — giới hạn đã công bố; 11 không trùng số nào)
            "danh sách 1..12 mà mục 10 ghi 13": (ds.replace("\n10. ", "\n13. "), "11 — đoạn SUY LUẬN"),
        })
        self.dat({
            "bản chấm vòng 1: 1. câu định tính": "1. " + DINH_TINH + K,
            "danh sách 1..12": ds,
            "mục con gạch đầu dòng giữa danh sách số": "1. " + DINH_TINH + K + "\n  - Ý phụ. [SUY LUẬN]\n2. Ý thứ hai. [SUY LUẬN]",
            "danh sách ĐÃ KIỂM bị bảng ngắt, đánh tiếp 2.":
                "1. Doanh thu thuần năm 2025 là 1.200 tỷ đồng. [ĐÃ KIỂM D1 tr.1]\n\n| Chỉ tiêu | Giá trị |\n|---|---:|\n"
                "| Lợi nhuận gộp | 360 |\n\n[ĐÃ KIỂM D1 tr.1]\n\n2. Lợi nhuận sau thuế là 144 tỷ đồng. [ĐÃ KIỂM D1 tr.1]",
        })

    def test_so_o_cho_khong_mang_nhan(self):
        self.chua_dat({
            "bảng một hàng: hàng tiêu đề có số": ("| Phải thu khách hàng tăng 63,4% |\n\n" + K, "63,4% — số liệu ở hàng tiêu đề bảng"),
            "tiêu đề phụ có số": ("### Phải thu tăng 63,4%\n\n" + DINH_TINH + K, "63,4% — số liệu ở tiêu đề phụ"),
            "tiêu đề phụ đánh số 3.1.": ("### 3.1. Phải thu\n\n" + DINH_TINH + K, "3.1 — số liệu ở tiêu đề phụ"),
            "số không nhãn trong backtick": ("Phải thu khách hàng tăng `63,4%`.", "63,4% — đoạn có số mà không có nhãn"),
        })
        self.dat({
            "tiêu đề phụ có năm": "### Năm 2025\n\n" + DINH_TINH + K,
            "tiêu đề phụ đánh số một tầng": "### 3. Phải thu\n\n" + DINH_TINH + K,
            "hàng tiêu đề có năm và quý": "| Chỉ tiêu | 2025 | Quý 3 năm 2026 |\n|---|---:|---:|\n"
                                          "| Doanh thu thuần | 1.200 | 1.050 |\n\n[ĐÃ KIỂM D1 tr.1; D2 tr.1]",
            "GIẢ ĐỊNH có số trong backtick: chỉ đếm": "Giả sử biên lợi nhuận gộp giữ `31,5%`. [GIẢ ĐỊNH]",
        })

    def test_so_khong_doc_duoc_theo_kieu_viet_nam(self):
        la = "cụm chữ số không đọc được theo kiểu số Việt Nam"
        self.chua_dat({
            "dấu chấm thập phân, số sai": ("Phải thu khách hàng tăng 63.4%. " + K, "«63.4» — " + la),
            "dấu chấm thập phân, đúng giá trị": ("Phải thu khách hàng tăng 36.4%. " + K, "«36.4» — " + la),
            "dấu phẩy tách nghìn": ("Phải thu khách hàng là 1,234,567. " + K, "«1,234,567» — " + la),
            "trong backtick": ("Phải thu khách hàng tăng `63.4%`. " + K, "«63.4» — " + la),
            "trong ô bảng": (BANG + "| Phải thu tăng | 63.4% |\n\n" + K, "«63.4» — " + la),
            "không nhãn": ("Phải thu khách hàng tăng 63.4%.", "đoạn có số mà không có nhãn"),
            "ở tiêu đề phụ": ("### Phải thu tăng 63.4%\n\n" + DINH_TINH + K, "63.4 — số liệu ở tiêu đề phụ"),
        })
        self.assertEqual(kiem_trich_dan.so_khong_doc_duoc("63.4% và 1,234,567; 1.200,5; ngày 31/12/2025; kq25_dt; D1 tr.3"),
                         ["63.4", "1,234,567"])
        self.dat({"GIẢ ĐỊNH: chỉ đếm": "Giả sử doanh thu gấp 1.5 lần. [GIẢ ĐỊNH]"})
        self.assertEqual(self.thu("Giả sử doanh thu gấp 1.5 lần. [GIẢ ĐỊNH]"), ("", True))


class VongSua2TanCongTests(VongSua2Tests):
    """Các đầu vào do lượt tấn công độc lập tìm ra trên bản sửa đầu của vòng sửa 2 (commit 42e42da), cùng loại với bốn lỗi
    chặn. Thừa hưởng các phép thử của VongSua2Tests để chạy lại chúng trên cùng mã."""

    def test_bang_phai_la_bang_that(self):
        dd = "định dạng ngoài bộ cho phép — "
        self.chua_dat({
            "ô thừa giấu nhãn GIẢ ĐỊNH": (BANG + "| Phải thu tăng | 63,4% | [GIẢ ĐỊNH] |\n\n" + K, dd + "hàng bảng có 3 ô"),
            "ô thừa giấu số đúng": (BANG + "| Phải thu tăng | 100% | 36,4% |\n\n" + K, dd + "hàng bảng có 3 ô"),
            "bảng giả không dòng kẻ": ("Mức tăng như sau. [GIẢ ĐỊNH]\n| Chỉ tiêu\n| Phải thu khách hàng tăng 63,4%,\n"
                                       "nhanh hơn doanh thu. " + K, dd + "bảng thiếu dòng kẻ"),
            "dòng kẻ lệch số ô": ("| Chỉ tiêu | Tỷ lệ |\n|---|\n| Phải thu tăng | 63,4% |\n\n[GIẢ ĐỊNH]", dd + "bảng thiếu dòng kẻ"),
        })
        self.dat({
            "hàng tiêu đề trống": "| | |\n|---|---:|\n| Phải thu tăng | 36,4% |\n\n" + K,
            "nhãn in đậm sau bảng": BANG + "| Phải thu tăng | 36,4% |\n\n**" + K + "**",
            "nhãn in đậm cuối đoạn dẫn": "Mức tăng phải thu, đơn vị phần trăm: **" + K + "**\n" + BANG + "| Phải thu tăng | 36,4% |",
        })

    def test_bo_loc_chi_nhan_ngay_gio_nam_hop_le(self):
        sai = "đoạn SUY LUẬN: số không khớp khóa"
        self.chua_dat({
            "mỗi quý 63%": ("Phải thu khách hàng tăng bình quân mỗi quý 63%. " + K, "63% — " + sai),
            "mỗi tháng 99 tỷ, không nhãn": ("Doanh thu bình quân mỗi tháng 99 tỷ đồng.", "99 — đoạn có số mà không có nhãn"),
            "cả năm 1300 tỷ dưới ĐÃ KIỂM": ("Doanh thu thuần cả năm 1300 tỷ đồng. [ĐÃ KIỂM D1 tr.1]", "1300 — không có trên trang"),
            "63:37 không nhãn": ("Cơ cấu nợ trên vốn là 63:37.", "63 — đoạn có số mà không có nhãn"),
            "45/55": ("Cơ cấu nợ trên vốn là 45/55. [SUY LUẬN]", "45 — " + sai),
            "chữ thường-số không phải mã tài liệu": ("Biến động: phải thu-63,4%. " + K, "63,4% — " + sai),
            "tr. trước số có phần lẻ": ("Phải thu khách hàng tăng, xem tr. 63,4%. " + K, "63,4% — " + sai),
            "5 và % cách hai dấu cách": ("Phải thu khách hàng tăng 5  %. " + K, "5% — " + sai),
            "chữ hoa-số không phải mã tài liệu": ("Lợi nhuận sau thuế: LNST-999 tỷ đồng. [ĐÃ KIỂM D1 tr.1]", "999 — không có trên trang"),
            "khoảng trang có dấu cách": ("Doanh thu thuần theo D1 tr.1 – 999 tỷ đồng. [ĐÃ KIỂM D1 tr.1]", "999 — không có trên trang"),
        })
        self.assertEqual([s.raw for s in kiem_trich_dan.so_can_kiem(
            "Ngày 31/12/2025, 9:30, tháng 12, quý 4, năm 2025, D1 tr.8–11, QĐ-P13: quý 63%, tháng 99, năm 1300, 63:37, 45/55")],
            ["63", "99", "1300", "63", "37", "45", "55"])

    def test_cum_so_dung_sau_dau_cham_dau_phay(self):
        la = "cụm chữ số không đọc được theo kiểu số Việt Nam"
        self.chua_dat({
            "hai số dính nhau qua dấu phẩy": ("Hai mức tăng: 20,0%,63,4%. " + KD, "«63,4» — " + la),
            "dấu cách trước dấu phẩy": ("Phải thu khách hàng tăng 36 ,9%. " + K, "«9» — " + la),
            "dấu cách trước dấu chấm, không nhãn": ("Doanh thu thuần là 1 .300 tỷ đồng.", "«300» — " + la),
            "0.005 kiểu Anh": ("Phải thu khách hàng tăng 0.005 lần. [SUY LUẬN]", "«0.005» — " + la),
        })
        self.assertEqual(kiem_trich_dan.so_khong_doc_duoc("20,0%,63,4% và 36 ,9; 1 .300; 0.005; .634; v1.2; 1.200,5."),
                         ["63,4", "9", "300", "0.005", "634"])

    def test_danh_sach_danh_so(self):
        self.chua_dat({
            "số đầu mục trình dựng không hiện": ("1. Ý định tính. [SUY LUẬN]\n36. Phải thu khách hàng tăng 100%. " + K,
                                                 "mục liệt kê mở đầu bằng «36.» nhưng danh sách không được đánh đúng"),
        })
        con = "\n".join(f"  {i}. Ý con. [SUY LUẬN]" for i in range(1, 11))
        self.dat({
            "danh sách con mười ý dưới hai mục gạch đầu dòng": "- Nhóm một. [SUY LUẬN]\n" + con + "\n- Nhóm hai. [SUY LUẬN]\n"
                                                              "  1. Ý con. [SUY LUẬN]",
            "danh sách 1..10 có danh sách con": "\n".join(f"{i}. Ý. [SUY LUẬN]" + ("\n    1. Ý con. [SUY LUẬN]" if i == 3 else "")
                                                          for i in range(1, 11)),
            "xuống dòng giữa «tháng» và «11.»": "Số liệu dưới đây tính tới hết tháng\n11. Phải thu khách hàng tăng 36,4%. " + K,
        })

    def test_khung_va_trang_thai_kiem(self):
        goc = self.ho_so.read_text(encoding="utf-8")
        self.ho_so.write_text(goc.replace(MUC_9, MUC_9 + "\n\n## Phiếu máy\n\nPhải thu khách hàng tăng 63,4%.", 1), encoding="utf-8")
        self.assertIn("khung: tiêu đề cấp hai không theo thứ tự của khung", "\n".join(self.luat()))
        self.assertFalse(self.phieu()[1])
        cd, mt = goc.index("## Cách đọc"), goc.index("## Một trang")
        muc1 = goc.index("## Mục 1.")
        self.ho_so.write_text(goc[:cd] + "## Một trang\n\n" + goc[cd:mt] + goc[mt + len("## Một trang\n"):muc1].replace("1.200", "9.999")
                              + goc[muc1:], encoding="utf-8")        # dời «Cách đọc» xuống dưới «Một trang» để che số sai
        self.assertIn("khung: tiêu đề cấp hai không theo thứ tự của khung", "\n".join(self.luat()))
        self.assertFalse(self.phieu()[1])
        self.ho_so.write_text(goc, encoding="utf-8")
        self.thay_trang_thai("**- Phiếu máy:** chưa làm.\n**- Đối chiếu số khác hãng:** chưa làm.\n"
                             "**- Phản biện khác hãng:** chưa làm.\n**- Owner tự mở ba số:** chưa làm.")
        self.assertIn("Trạng thái kiểm: cần đúng một mục liệt kê riêng", "\n".join(self.luat()))   # đoạn chữ đậm, không phải mục liệt kê
        self.assertFalse(self.phieu()[1])

    def test_nam_truoc_chu_dong_khong_phai_so_dem_thoi_gian(self):
        self.dat({"cuối 2025 dòng tiền": "Cuối 2025 dòng tiền kinh doanh thấp hơn lợi nhuận sau thuế. "
                                         "[SUY LUẬN, sổ số liệu: tien_tren_lnst_25]"})

    def test_day_khoa_qua_dai_khong_lam_van(self):
        self.chua_dat({"dãy một tỷ khóa": ("Phải thu khách hàng tăng 36,4%. [SUY LUẬN, sổ số liệu: a000000000 tới a999999999]",
                                           "quá dài: một dãy không quá 1000 khóa")})
        # số đầu mục dài hơn giới hạn đổi chuỗi sang số của Python: phần tách khối của kiem_trich_dan không văng
        kiem_trich_dan.cac_phan_chu(MUC_9 + "\n\n" + "1" * 4301 + ". Ý định tính. [SUY LUẬN]")


class BangDinhNghiaTests(KhoaBase):
    def test_bang(self):
        bang = bang_dinh_nghia.lap_bang(self.tm, self.ho_so)
        for khoa in ("dt_tang_25", "tien_tren_lnst_25", "phai_thu_tang_25", "no_tren_von_25"):
            self.assertIn(f"| {khoa} |", bang)
        self.assertIn("(kq25_dt / kq24_dt - 1) * 100", bang)
        self.assertIn("kq25_dt: D1 tr.1 «1.200.000.000.000»", bang)
        self.assertIn("dòng 30 (Một trang)", bang)
        self.assertEqual(bang, bang_dinh_nghia.lap_bang(self.tm, self.ho_so))    # không có giờ chạy


class TrangThaiKiemTests(KhoaBase):
    def test_thieu_muc_hay_thieu_dong(self):
        self.sua("HO_SO_MAU.md", "- **Phản biện khác hãng:** chưa làm (bước B7).\n", "")
        self.assertIn("thiếu hoặc trùng: «- Phản biện khác hãng:»", "\n".join(self.luat()))
        self.sua("HO_SO_MAU.md", "## Trạng thái kiểm\n", "")
        self.assertIn("tiêu đề cấp hai đầu tiên phải là '## Trạng thái kiểm'", "\n".join(self.luat()))
        self.assertFalse(self.phieu()[1])

    def test_so_trong_muc_khong_bi_doi_chieu(self):
        self.sua("HO_SO_MAU.md", "- **Đối chiếu số khác hãng:** chưa làm (bước B7).",
                 "- **Đối chiếu số khác hãng:** 35 dòng KHỚP, 1 dòng LỆCH (đúng dòng gài).")
        self.assertEqual(kiem_trich_dan.kiem(self.tm, self.ho_so.read_text(encoding="utf-8"))["loi"], [])
        self.assertEqual(self.luat(), [])


class BaSoTests(KhoaBase):
    def test_xac_dinh_va_du_ba_dong(self):
        a, b = self.phieu()[0], self.phieu()[0]
        self.assertEqual(a, b)
        phan = a.split("OWNER TỰ MỞ BA SỐ", 1)[1]
        for so in ("\n1. ", "\n2. ", "\n3. "):
            self.assertIn(so, phan)
        self.assertIn("Số ĐÃ KIỂM", phan)
        self.assertIn("(Một trang)", phan)
        self.assertIn("Dòng gốc khóa", phan)

    def test_dong_sua_duoc_chon(self):
        self.doc_sai("bctc_mau_2025.txt", (r"1\.200\.000\.000\.000", "1.290.000.000.000"))
        self.sua("so_lieu.csv", "kq25_dt,D1,1,1.200.000.000.000,,dong,,",
                 "kq25_dt,D1,1,1.290.000.000.000,1.200.000.000.000,dong,máy đọc 2 thành 9; đẳng thức kqkd 2025,")
        phieu, dat = self.phieu()
        self.assertTrue(dat, phieu)
        self.assertIn("ĐÃ SỬA SO VỚI MÁY ĐỌC: kq25_dt", phieu)
        self.assertIn("2. Dòng máy đọc sai đã sửa: khóa kq25_dt — máy đọc «1.290.000.000.000», sổ ghi «1.200.000.000.000»",
                      phieu)
