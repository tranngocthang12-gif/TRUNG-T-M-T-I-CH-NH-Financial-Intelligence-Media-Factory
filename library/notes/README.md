# Ghi chú thư viện (KNOWLEDGE_NOTE)

Mỗi ghi chú là một tệp `library/notes/<KN-id>.json` theo `contracts/knowledge_note.schema.json`, viết khi đọc một tài liệu gốc trong `library/sources/<doc_id>/text.md`.

- Mọi ý có địa chỉ `<doc_id>:p<trang>:<đoạn>` hoặc `<doc_id>:t<bảng>:<dòng>`, và `quote` nằm nguyên văn ở chỗ được trỏ tới — từ 15 ký tự trở lên, hoặc nguyên cả đoạn nếu đoạn ngắn hơn (L-01). Ý loại `CROSS_TEXT_SYNTHESIS` dẫn ít nhất hai địa chỉ. Có `counts` thì `self_check.counts_from_source` phải là `true`.
- `read_by` ghi bắt đầu bằng tên ghế đã đọc, ví dụ "ChatGPT (ghế thi công)".
- Ghi chú mới luôn là `DRAFT`. `CITED` chỉ hợp lệ khi có biên bản `library/audits/<KN-id>.json`: `{note_id, auditor, verdict: "PASS", date, note_sha256}`. `note_sha256` do `engine.knowledge_notes.note_digest()` tính (mọi trường trừ `status`) — sửa ghi chú sau khi chấm thì biên bản hết hiệu lực. `auditor` bắt đầu bằng tên ghế và không chung ghế với `read_by`: khác nhà cung cấp; Owner đọc thì Owner không tự chấm (L-09). `DISPUTED` cần biên bản `verdict: "FAIL"`. `TESTED`, `PROVEN` chưa dùng được cho tới khi Học viện có mã gán.
- Văn bản nguồn hết hiệu lực hoặc bị thay thế → vòng học tự chuyển ghi chú sang `OUTDATED` (L-08).
- Kiểm: `python -m engine.knowledge_notes` (cũng chạy trong `tools/validate.py`).
