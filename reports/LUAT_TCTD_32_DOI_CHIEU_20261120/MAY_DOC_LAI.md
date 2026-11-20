# Đọc lại bằng máy — không phải đối chiếu độc lập

Ngày lập: 2026-11-20. Máy: ghế thi công Grok (xAI). Không ghi `pdf_check`.

## Phạm vi

Đối chiếu `page_surface` của `library/sources/luat_tctd_32_2024/text.md` với lớp chữ đọc lại từ hai PDF gốc (ToUnicode, cụm dòng lệch tối đa 6pt). 152 trang trong `page_map`. Không gồm PDF A trang 94 vì trang đó không có toán tử chữ.

## Kết quả máy

- Lệch dòng: **0** trên 152 trang đã ánh xạ.
- PDF A: parser strict 94 trang. PDF B: 59 trang.
- `page_map`: text 1–93 → `cb-369-370` PDF 1–93; text 94–152 → `cb-371-372` PDF 1–59. Không lỗ, không trùng.
- Tiêu đề `Điều N.` trong text.md: 210 tiêu đề, số 1..210, không thiếu, không lặp.
- Cụm đã thấy trong text.md: "thông qua ngày 18 tháng 01 năm 2024"; "có hiệu lực thi hành từ ngày 01 tháng 7 năm 2024".
- Không có ký tự thay thế U+FFFD. Không có dòng nội dung dài hơn 180 ký tự.
- Không có mốc bảng `[tN]`.

Chỗ nối hai Công báo, máy đọc được (chưa phải người xem):

- text 93 / PDF A trang 93 kết bằng "(Xem tiếp Công báo số 371 + 372)" sau Điều 131.
- text 94 / PDF B trang 1 mở đầu "(Tiếp theo Công báo số 369 + 370)" rồi Điều 132, có cụm "Tại mỗi tỉnh, thành phố trực thuộc Trung ương".

## Giới hạn — vì sao chưa MATCH

Công cụ này không đọc chữ vẽ bằng path. PDF A trang 94 là trường hợp đó (trang in, xem ảnh `trang-loai-tru-cb-369-370-p94.png`). Nếu một trang luật có chữ chỉ vẽ bằng path, máy sẽ không báo lệch.

Grok mở ảnh bốn trang để chắc hồ sơ không cắt nhầm: text 1, text 93, text 94, và PDF A/94. Bốn ảnh này khớp các dòng đầu/cuối tương ứng trong text.md hoặc lý do loại trừ. **149 trang còn lại chưa được mắt người kiểm.** Sai khác nội dung do ghế độc lập: chưa có, vì chưa có người chấm.
