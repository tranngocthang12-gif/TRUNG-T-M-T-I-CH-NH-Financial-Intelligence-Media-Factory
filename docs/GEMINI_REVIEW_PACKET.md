# Quy ước TTC: luôn đóng gói tệp tải được khi nhờ Gemini phản biện

**Yêu cầu Owner (20/11/2026).** Áp dụng cho ghế điều phối/kiến trúc sư trưởng ở dự án này và các phiên tiếp nối sau khi văn bản được Owner merge. Đây là quy ước giao chứng cứ, **không** thay đổi L-09, L-10, hợp đồng dữ liệu, hay quyền phê duyệt.

## Quy tắc bắt buộc

1. **Trước khi gửi lệnh cho Gemini**, tự tạo **ít nhất một tệp hoàn chỉnh** `.md` hoặc `.pdf` chứa đúng hồ sơ phản biện. Không chỉ gửi link `github.com/.../blob/...` hoặc giả định Gemini có thể đọc trang React. Nếu Gemini chỉ đọc Markdown thì ưu tiên **một tệp .md tự chứa**.
2. Tệp phải có: repo + PR/Issue, **full SHA HEAD đã ghim**, mục tiêu kiểm, thay đổi/patch hoặc nội dung bằng chứng đủ để kiểm, tiêu chí chấm, trích nguồn, hash/byte khi có, CI, mọi giới hạn chưa kiểm, và mẫu phán quyết. Nếu quá dài, chia ít tệp có chỉ mục rõ ràng; không nói “đã đầy đủ” khi thiếu dữ liệu gốc.
3. **Phải tạo tệp trong phiên làm việc** và **xác minh đúng đường dẫn** trước khi trả liên kết tải trực tiếp. Ví dụ, trong ChatGPT dùng `sandbox:/mnt/data/<ten_tep>.md` hoặc `.pdf` sau khi đã xác minh tệp tồn tại; trong môi trường khác dùng liên kết tải tệp thực tế được môi trường đó hỗ trợ. Có thể lưu thêm bản kiểm toán trên GitHub nhưng không coi GitHub là đường tải duy nhất. Không tái sử dụng liên kết tải chưa xác minh ở phiên khác.
4. Gemini được chấm **đúng loại chứng cứ đã đọc**: nếu chỉ xem Markdown thì chỉ được `MD_REVIEW`; **không** ký `pdf_check MATCH`, xác nhận hash PDF tự tính, hay nâng `SOURCED`. Nếu phải kiểm PDF/ảnh, gửi kèm PDF gốc hoặc bản render cho người có quyền đọc ảnh và yêu cầu ghi rõ trang đã thực sự xem.
5. Sau mỗi commit mới của PR, **đóng gói lại theo HEAD mới** trước khi yêu cầu L-09; bản chấm cũ không đủ thay cho việc kiểm HEAD cuối. Ghi rõ ai viết, ai chấm, ai chuyển tiếp; không giả mạo lời chấm của Gemini.
6. Trước khi đưa lên GitHub hay gửi Gemini: loại trừ secrets, PII, quyền truy cập và nội dung vi phạm chính sách bản quyền; tách `DECLARED` (hash/số do nguồn khai) khỏi `VERIFIED` (hash/số thực sự được tự kiểm).
7. Đưa **link tải tệp lên đầu câu trả lời**, tiếp theo là lệnh ngắn để Owner chuyển cho Gemini. Bản chấm Gemini phải được Owner chuyển lại; ghế điều phối đối chiếu SHA, lỗi và ranh giới trước khi ghi bình luận PR. **Chỉ Owner merge theo L-10.**

## Mẫu tên tệp

- `TTC_GEMINI_PR<so>_<HEAD7>_REVIEW.md` — kỹ thuật/Markdown.
- `TTC_GEMINI_PR<so>_<HEAD7>_PDF_EVIDENCE.pdf` — có PDF/ảnh nguồn để kiểm bằng mắt, khi môi trường có tệp gốc.
- `TTC_GEMINI_ISSUE<so>_<HEAD7>_REVIEW.md` — phản biện issue.

## Đầu ra bắt buộc

- Tệp có thật, kiểm được độ dài và trang/phần.
- Liên kết tải trực tiếp trong chat.
- Lệnh Gemini giới hạn đúng phạm vi kiểm chứng.
- Hồ sơ GitHub/PR lưu kết luận, người chấm, SHA, điều kiện còn mở.
- **Không báo PASS** nếu chưa mở/kiểm được tài liệu cần thiết.

### Áp dụng vào PR #60 (ví dụ)

Bản chép Luật Các tổ chức tín dụng 32/2024 có 152 trang Markdown; gói một tệp chỉ cho phép Gemini kiểm `MD_REVIEW`, không cho phép `PDF_VISUAL_MATCH`. Các nghi vấn `[p9]`, `[p81]`, `[p83]`, `[p134]` cần ghế có PDF gốc đối chiếu trước khi sửa bản chép. G1 vẫn **1/40 `SOURCED`** (trong khi manifest đã ghim **2/40** hồ sơ); chỉ tăng số `SOURCED` khi hoàn tất `pdf_check` độc lập.

**Quy tắc cho phiên mới:** đọc `BOOT.md` và tài liệu này trước khi giao phản biện Gemini. Nếu sử dụng một dự án GitHub khác, phải chép quy ước này sang kho mới; file trong kho hiện tại không tự xuất hiện ở mọi dự án.
