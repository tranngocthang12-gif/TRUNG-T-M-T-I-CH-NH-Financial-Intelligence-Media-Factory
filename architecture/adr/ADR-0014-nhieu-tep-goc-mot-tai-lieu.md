# ADR-0014: Nhiều tệp gốc cho một tài liệu
- Ngày: 2026-11-20
- Trạng thái: PROPOSED (chưa hiệu lực trên main; PR nháp, chưa có người chấm, Owner chưa gộp)
- Người đề xuất: Grok (xAI)
- Người chấm: (trống — ghế khác nhà cung cấp, L-09; người đề xuất không tự chấm)
- Owner duyệt: chưa

## Khác ADR-0012
ADR-0012 vẫn đúng với một PDF: ba trường `original_sha256`, `original_bytes`, `original_path`, cộng `text_sha256`/`text_bytes`. ADR này không sửa ADR-0012 và không viết ARCHITECTURE v4. Nó chỉ thêm lối thứ hai khi một văn bản logic không có một tệp hoàn chỉnh mà có từ hai PDF gốc chính thức.

## Quyết định
1. Một `doc_id` vẫn là một đơn vị. N PDF không phải N tài liệu và không được đếm N lần khi xét G1.
2. Manifest là union, không phải bản ghi vừa đơn vừa nhiều phần:
   - Một bản gốc: đúng ba trường `original_*` như ADR-0012. Không có `original_parts`.
   - N≥2: có `original_parts`, không có ba trường `original_*` ở cấp tài liệu. Mỗi phần có `part_id`, `original_path` trong `library/sources/<doc_id>/`, `source_url` https thuộc miền đã gắn với `data_source` (Công báo: `chinhphu.vn` và miền con, kể cả `g7.cdnchinhphu.vn` trên miền `cdnchinhphu.vn`), `original_sha256`, `original_bytes`, `page_count`. URL bên thứ ba không qua cổng chỉ vì nhãn `data_source` đúng.
   - Thiếu cả hai schema, hoặc có cả hai, hoặc để trống trường, hoặc N<2: lỗi cổng. Không ghép các PDF thành một tệp rồi gọi là original.
3. `sha256`/`bytes` và `text_sha256`/`text_bytes` vẫn là `text.md`. Hash từng phần phải khác hash `text.md` và khác nhau.
4. `page_map` gắn mỗi `[pN]` của `text.md` với `part_id` và trang PDF vật lý, đúng thứ tự 1..N, không trùng, không nhảy, không tráo phần. Trong một phần, `pdf_page` tăng nghiêm ngặt. Trang PDF không vào `text.md` chỉ được khi có `excluded_pages` và lý do reviewer kiểm được. Mọi trang vật lý 1..`page_count` phải nằm ở một trong hai chỗ đó.
5. `page_count` được đối chiếu bằng parser PDF (`pypdf==7.1.1`, chế độ strict): trailer, catalog, cây `/Pages`, và `/Count` phải khớp số trang parser đọc được. Không đếm regex trên byte. PDF giả hoặc cây trang lệch thì lỗi, không đoán. Gói này không dùng để OCR.
6. Hash từng trang `text.md` (kể cả bảng) giữ nguyên. Máy không tự nhận đã nhìn PDF. `pdf_check` của nhiều phần, do ghế khác Grok, phải có `originals` đúng `part_id` và hash theo thứ tự `original_parts`, `text_sha256`, `page_map` trùng bản đang ghim, `excluded_pages` trùng đúng thứ tự (kể cả danh sách rỗng), và `pages_checked` = 1..N. Một `original_sha256` đơn không thay tập hash. Đổi byte, thứ tự, lý do loại trang hoặc tập trang loại trừ thì biên bản cũ hết hiệu lực. Chưa có biên bản đó thì hàng đợi ở `QUEUED`, không `SOURCED`.
7. `luat_ke_toan_88_2015` giữ một tệp, hash và `pdf_check` đã có. Khai tài liệu đó thành `original_parts` là lỗi.

## Lý do
Luật Các tổ chức tín dụng số 32/2024/QH15 trên Công báo chỉ có hai PDF (`369+370` và `371+372`). Hợp đồng một `original_path` không ghim được cả hai mà không nối tệp. Nối tệp rồi gọi là original làm mất URL, hash và số trang của từng bản Công báo.

## Quyền truy xuất
Mỗi phần giữ nguyên byte đã tải, URL Công báo của chính phần đó, SHA-256 và số trang. `text.md` dẫn `[pN]` về đúng phần và đúng trang PDF. Trang loại ra ghi lý do. Người chấm đối chiếu từng phần, không đối chiếu một hash do ghế thi công tự gán cho cả bộ.

## Tính tương thích
Đường một tệp, `KNOWN_ORIGINALS` của Luật Kế toán 88/2015, và các test hiện có không đổi hành vi. `may_mark_sourced` vẫn từ chối khi thiếu `pdf_check`.

## Giới hạn
- Chưa chứng nhận nội dung Luật 32 đã khớp PDF. Pilot chỉ ghim byte và bản chép máy; trạng thái `QUEUED`. Trang PDF 94 của phần `cb-369-370` không trống: ảnh trang là ấn phẩm Văn phòng Chính phủ xuất bản (chữ vẽ bằng path). Trang đó bị loại, có lý do; không có `pdf_check`.
- `tt_99_2025` không nằm trong PR này. Luật 54/2019 là bản scan, không OCR bỏ dấu ở đây. BCTC VCB 2025 chưa ghim.
- ADR này chưa được chấm và chưa được Owner gộp. Không tự nhận ACCEPTED bằng comment Issue.

## Điều kiện hoàn tác
Nếu lối nhiều phần không giữ được kiểm chứng: quay về đúng đường một tệp của ADR-0012, giữ nguyên byte và hash đã chứng nhận, không tự nâng tài liệu nhiều phần lên `SOURCED`. Xóa `original_parts` khỏi cổng chỉ bằng ADR sau khi Owner quyết, không bằng cách sửa hash cho khớp tệp khác.

## Ảnh hưởng tới ARCHITECTURE.md
Không sửa `architecture/ARCHITECTURE.md` trong PR này. Khi Owner gộp, một câu ở mục nguồn là đủ: N≥2 PDF gốc dùng `original_parts` thay ba trường `original_*` (ADR-0014); vẫn một `doc_id`; `SOURCED` cần `pdf_check` gắn đủ hash từng phần.
