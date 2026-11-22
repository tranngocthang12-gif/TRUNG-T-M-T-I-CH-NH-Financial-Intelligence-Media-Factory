# Đọc lại — bản sau PR #62

Ngày: 2026-11-20. Ghế thi công: Grok (xAI). Không ghi `pdf_check`.

## text-vs-text — VERIFIED

Năm tệp `lo-01-text.md` … `lo-05-text.md` chứa đúng lát `[p1]` … `[p152]` của `text.md` SHA-256 `bd639d7951f68b6d41d502cb84a7fca53fe0490706c2aa8b84dd7b2b21961d44` (406070 byte). Không thiếu, không trùng, không tráo lô. Kết quả: **text-vs-text PASS**.

## Bốn chỗ đã sửa so với hash cũ

Hash cũ `8c69c6a2b0c516e8093a22dc2bdba68a0f62944cd25d5fa83789f0863f95aa5a` là STALE. Các dòng sau đây là bản mới, đã nhìn trên ảnh PDF trong PR #62, không phải đoán:

- `[p9]`: ngoặc kép cong “ ” thay U+0093/U+0094.
- `[p81]`: `a) Thực hiện dịch vụ thanh toán trong nước bao gồm séc, lệnh chi, ủy nhiệm`.
- `[p83]`: dòng kết thúc `kiều hối, vàng, bao thanh`.
- `[p134]`: `Điều 185. Quyền, nghĩa vụ của bên nhận chuyển giao bắt buộc`.

Báo cáo máy "0 dòng lệch" trên hash cũ **không còn hiệu lực**. Bộ tách 6pt vẫn tách bốn chỗ đó; bản chép cố ý không theo bốn chỗ tách ấy.

## PDF

Byte hai PDF gốc không đổi. Lát `lo-*.pdf` không dựng lại. Ảnh trang loại trừ giữ nguyên. Ghế khác Grok chưa xem đủ 152 trang ảnh trong phiên đóng gói này. Phần PDF: **BLOCKED**.
