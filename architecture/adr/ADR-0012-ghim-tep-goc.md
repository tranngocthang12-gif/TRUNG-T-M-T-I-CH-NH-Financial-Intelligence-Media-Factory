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
4. Bằng chứng QC mà reviewer kiểm được là `crosscheck.method` = `page-by-page` và `crosscheck.pages`: mỗi trang một dòng `{page, sha256, head, tail}` tính lại từ `text.md`. Số `pages_checked`, dù kèm `pages_total`, không phải biên bản đó và không được `SOURCED`. `may_mark_sourced` chỉ đúng khi biên bản khớp từng trang và, với tài liệu đã biết hash, `original_sha256`/`original_bytes` khớp bản đã công bố. `reading_queue` ghi `SOURCED` khi hàm này sai thì là lỗi L-01. Ghi chú `CITED`, `TESTED`, `PROVEN` không dùng được khi tài liệu dẫn chiếu chưa có tệp gốc đã kiểm và biên bản từng trang. `DRAFT` vẫn được. `DISPUTED` không phải trạng thái dùng cho câu trả lời.
5. `luat_ke_toan_88_2015` giữ `QUEUED`. Nếu được khai tệp gốc, chỉ khớp SHA-256 `1fd9336a3a6f4d90676db5889bdb409af9c75c96c9c256143197908a7bfcca50`, 2566253 byte, 35 trang, và biên bản đủ 35 trang. PR này không chép PDF và không chuyển `SOURCED`.

## Lý do
Máy kiểm hiện chỉ so `text.md`. Hash đó có thể bị đọc nhầm là hash PDF. Hợp đồng “chỉ bắt original_* khi có khai” cho một nguồn mới đi qua cổng chỉ bằng cách bỏ các trường đó. Một số `pages_checked` không phải biên bản để reviewer đối chiếu từng trang. Manifest trên `main` đang rỗng, nên không cần đường vòng tương thích.

## Điều kiện hoàn tác
- Owner nói một câu bỏ ghim bắt buộc: ADR mới ngừng bắt `original_*` trên mọi dòng. Không xóa byte tài liệu đã ghim bằng cách sửa hash cho khớp tệp khác.
- Không mở lại đường “bỏ trường gốc thì qua cổng” khi `files` còn rỗng.

## Ảnh hưởng tới ARCHITECTURE.md
Một mệnh đề ở mục nguồn: `sha256`/`bytes` là của `text.md`; mọi dòng phải ghim tệp gốc; `SOURCED` và ghi chú dùng được cần `crosscheck.pages`, không chỉ `pages_checked`. Luật Kế toán 88/2015 giữ `QUEUED`.
