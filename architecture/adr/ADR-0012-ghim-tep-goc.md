# ADR-0012: Ghim tệp gốc riêng khỏi text.md
- Ngày: 2026-11-18
- Trạng thái: PROPOSED (ACCEPTED khi Owner gộp PR chứa tệp này, sau bản chấm L-09 của ghế khác nhà cung cấp)
- Người đề xuất: Grok (xAI), ghế thi công, theo lệnh thi công cùng ngày
- Người chấm: để trống đến khi ghế khác nhà cung cấp chấm
- Owner duyệt: hiệu lực khi Owner gộp

## Quyết định
1. `sha256` và `bytes` trong `library/SOURCE_MANIFEST.json` luôn là của `library/sources/<doc_id>/text.md`. Chúng không phải hash PDF.
2. Khi một dòng khai bất kỳ trường nào trong `original_sha256`, `original_bytes`, `original_path`, `text_sha256`, `text_bytes` hoặc khai `crosscheck`, thì phải có đủ năm trường gốc. `text_sha256`/`text_bytes` phải trùng `sha256`/`bytes` và trùng byte của `text.md`. `original_sha256` phải khác hash `text.md`. `original_path` là đường dẫn tương đối trong `library/sources/<doc_id>/`, không tuyệt đối, không `..`, không được là `text.md`. Máy đọc byte tệp đó và so SHA-256 cùng số byte.
3. `may_mark_sourced` chỉ đúng khi quyết định 2 đã giữ và `crosscheck.method` là `page-by-page` với `pages_checked` = `pages_total` = đúng các trang `1..N` đã tách từ `text.md`. Khớp hash không phải bằng chứng nội dung chép đúng. `reading_queue` ghi `SOURCED` khi hàm này sai thì là lỗi L-01.
4. `luat_ke_toan_88_2015`, nếu được khai tệp gốc, chỉ khớp SHA-256 `1fd9336a3a6f4d90676db5889bdb409af9c75c96c9c256143197908a7bfcca50`, 2566253 byte, 35 trang. Chưa có tệp đó trong kho và 35 trang chưa được đối chiếu trong manifest thì hàng đợi giữ `QUEUED`. PR này không chép PDF và không chuyển `SOURCED`.
5. Dòng manifest cũ không có trường gốc vẫn hợp lệ. Không đổi `MANIFEST_KEYS` bắt buộc.

## Lý do
Máy kiểm hiện chỉ so `text.md`. Hash đó có thể bị đọc nhầm là hash PDF. Không có đường nào buộc byte tệp gốc, và không có cửa nào chặn `SOURCED` khi chưa đối chiếu từng trang.

## Điều kiện hoàn tác
- Owner nói một câu bỏ ghim kép: ADR mới ngừng bắt `original_*` khi khai. Không xóa byte tài liệu đã ghim bằng cách sửa hash cho khớp tệp khác.
- Nếu luật này làm CI đỏ với mọi dòng manifest cũ không có trường gốc, đó là lỗi thi công: nới bằng cách giữ trường tùy chọn, không bằng cách đánh dấu `SOURCED`.

## Ảnh hưởng tới ARCHITECTURE.md
Một mệnh đề ở mục nguồn: `sha256`/`bytes` là của `text.md`; tệp gốc ghim riêng; hash khớp không đủ để `SOURCED`.
