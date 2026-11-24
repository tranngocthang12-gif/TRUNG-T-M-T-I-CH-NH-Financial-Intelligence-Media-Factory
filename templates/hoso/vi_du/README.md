# Ví dụ thư mục mã (số liệu bịa)

Thư mục này là một "thư mục mã" thu nhỏ của một doanh nghiệp không có thật, mã `MAU`. Nó có hai việc:

1. Cho ghế phân tích xem một hồ sơ đạt phiếu máy trông thế nào (`HO_SO_MAU.md`, `so_lieu.csv`, `quan_he.csv`).
2. Làm dữ liệu cho `tests/test_hoso.py`.

Chạy thử từ gốc kho (chép ra chỗ khác trước, vì lệnh `nhan` sinh thêm `nguon.csv`, `trang/` và `trang_sha256.csv`):

```
cp -r templates/hoso/vi_du /tmp/MAU
python tools/hoso/nhan_tep.py nhan --thu-muc /tmp/MAU --ma-nguon /tmp/MAU/ma_nguon.csv
python tools/hoso/kiem_so_lieu.py --thu-muc /tmp/MAU
python tools/hoso/phieu_may.py --thu-muc /tmp/MAU --ho-so /tmp/MAU/HO_SO_MAU.md
```

Mã nguồn trong `ma_nguon.csv`: `D1`, `D2` là báo cáo tài chính; `G1` là tệp giá. Quy ước của dự án: tệp giá thị trường mang mã bắt đầu bằng chữ G, để cổng giá của phiếu máy nhận ra nhãn ĐÃ KIỂM dẫn nguồn giá (`docs/QUY_TRINH_HO_SO_MA.md` B2, B3).

Hồ sơ thật, tệp gốc thật và sổ số liệu thật không nằm trong kho này. Xem `docs/QUY_TRINH_HO_SO_MA.md` mục 1.
