# ADR-0012: Ghim tệp gốc riêng khỏi text.md
- Ngày: 2026-11-18
- Trạng thái: PROPOSED (ACCEPTED khi Owner gộp PR chứa tệp này, sau bản chấm L-09 của ghế khác nhà cung cấp)
- Người đề xuất: Grok (xAI), ghế thi công, theo lệnh thi công cùng ngày
- Người chấm: để trống đến khi ghế khác nhà cung cấp chấm
- Owner duyệt: hiệu lực khi Owner gộp

## Quyết định
1. `sha256` và `bytes` trong `library/SOURCE_MANIFEST.json` luôn là của `library/sources/<doc_id>/text.md`. Chúng không phải hash PDF.
2. Mọi dòng manifest phải có đủ `original_sha256`, `original_bytes`, `original_path`, `text_sha256`, `text_bytes`. Bỏ các trường này là lỗi cổng nguồn. Không còn đường vòng “không khai thì qua”. `files` trên `main` đang rỗng, nên không có dòng cũ để miễn. `MANIFEST_KEYS` của metadata `text.md` không thêm trường; ghim gốc do `origin_binding_errors` bắt trên mọi dòng.
3. `text_sha256`/`text_bytes` phải trùng `sha256`/`bytes` và trùng byte của `text.md`. `original_sha256` phải khác hash `text.md`. `original_path` là đường dẫn tương đối trong `library/sources/<doc_id>/`, không tuyệt đối, không `..`, không được là `text.md`. Máy đọc byte tệp đó và so SHA-256 cùng số byte.
4. **Tầng máy.** `crosscheck.method` = `page-by-page` và `crosscheck.pages` là `{page, sha256, head, tail}` tính trên mọi dòng nội dung của trang: đoạn, tiêu đề, bảng và từng ô. Không tính trên danh sách đoạn sau khi parser tách bảng. Số `pages_checked` không phải biên bản đó. Máy tính lại hash; lệch thì lỗi. `page_crosscheck()` chỉ sinh tầng này và không điền `pdf_check`.
5. **Tầng đối chiếu PDF.** Máy không đọc ảnh trang nên không tự chứng minh `text.md` khớp PDF. `SOURCED` và ghi chú `CITED`/`TESTED`/`PROVEN` chỉ được khi có thêm `crosscheck.pdf_check`: `checker` là ghế nhận ra, `result` = `MATCH`, `pages_checked` là danh sách `1..N`, `evidence` đủ để reviewer đọc, `text_sha256` và `original_sha256` đúng bản đang ghim. Đổi `text.md` hoặc PDF thì biên bản cũ hết hiệu lực. Ghi chú dùng được còn đòi `checker` khác ghế với `read_by`. Không có `pdf_check` thì hash tự sinh không nâng nguồn lên trạng thái dùng được. `DRAFT` vẫn được. `DISPUTED` không phải trạng thái dùng cho câu trả lời.
6. `luat_ke_toan_88_2015` giữ `QUEUED`. Nếu được khai tệp gốc, chỉ khớp SHA-256 `1fd9336a3a6f4d90676db5889bdb409af9c75c96c9c256143197908a7bfcca50`, 2566253 byte, 35 trang, và đủ hai tầng trên cho 35 trang. PR này không chép PDF và không chuyển `SOURCED`.

## Lý do
Máy kiểm hiện chỉ so `text.md`. Hash đó có thể bị đọc nhầm là hash PDF. Hash trang tính trên đoạn văn sau khi tách bảng thì sửa số trong bảng không đổi fingerprint. Hash tự sinh từ chính `text.md` cũng không chứng minh bản chép khớp PDF. Manifest trên `main` đang rỗng, nên không cần đường vòng tương thích.

## Điều kiện hoàn tác
- Owner nói một câu bỏ ghim bắt buộc: ADR mới ngừng bắt `original_*` trên mọi dòng. Không xóa byte tài liệu đã ghim bằng cách sửa hash cho khớp tệp khác.
- Không mở lại đường “bỏ trường gốc thì qua cổng” khi `files` còn rỗng.

## Ảnh hưởng tới ARCHITECTURE.md
Một mệnh đề ở mục nguồn: `sha256`/`bytes` là của `text.md`; mọi dòng phải ghim tệp gốc; hash trang gồm bảng; `SOURCED` và ghi chú dùng được cần `pdf_check`, không chỉ hash tự sinh. Luật Kế toán 88/2015 giữ `QUEUED`.
