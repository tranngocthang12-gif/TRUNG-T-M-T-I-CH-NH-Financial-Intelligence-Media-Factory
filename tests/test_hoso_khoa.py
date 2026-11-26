"""Test cho ADR-0021: số SUY LUẬN gắn đúng khóa sổ (QĐ-K1), bảng định nghĩa (QĐ-K2), mục Trạng thái kiểm (QĐ-K3) và ba số
Owner tự mở do máy chọn (QĐ-K4). Chỉ dùng doanh nghiệp giả ở templates/hoso/vi_du/."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_hoso import MUC_9, HoSoBase  # noqa: E402
from tools.hoso import bang_dinh_nghia, kiem_trich_dan  # noqa: E402


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
