# Ghi chú thư viện (KNOWLEDGE_NOTE)

Mỗi ghi chú là một tệp `library/notes/<KN-id>.json` theo `contracts/knowledge_note.schema.json`, viết khi đọc một tài liệu gốc trong `library/sources/<doc_id>/text.md`.

- Mọi ý có địa chỉ `<doc_id>:p<trang>:<đoạn>` hoặc `<doc_id>:t<bảng>:<dòng>` và `quote` nằm nguyên văn ở chỗ được trỏ tới (L-01). Quy ước đánh số trang/đoạn/bảng: `engine/knowledge_notes.py`.
- Ghi chú mới luôn là `DRAFT`. Trạng thái khác chỉ hợp lệ khi có biên bản `library/audits/<KN-id>.json` với `verdict: PASS`; `read_by` và `auditor` đều ghi bắt đầu bằng tên ghế ("Owner" hoặc tên mô hình/nhà cung cấp, ví dụ "ChatGPT (ghế thi công)") và không chung ghế — khác nhà cung cấp, không cùng là Owner (L-09).
- Văn bản nguồn hết hiệu lực hoặc bị thay thế → vòng học tự chuyển ghi chú sang `OUTDATED` (L-08).
- Kiểm: `python -m engine.knowledge_notes` (cũng chạy trong `tools/validate.py`).
