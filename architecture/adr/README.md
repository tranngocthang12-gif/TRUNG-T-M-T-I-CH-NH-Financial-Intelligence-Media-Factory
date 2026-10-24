# ADR — Bản ghi quyết định kiến trúc

Theo L-07: chỉ `architecture/ARCHITECTURE.md` có hiệu lực; mọi thay đổi kiến trúc đi qua một ADR ở đây, không viết bản kiến trúc mới khi bản hiện hành chưa vận hành ≥ 30 ngày.

Mẫu tệp `ADR-NNNN-<slug>.md`:

```markdown
# ADR-NNNN: <tên quyết định>
- Ngày: YYYY-MM-DD
- Trạng thái: PROPOSED | ACCEPTED | SUPERSEDED by ADR-MMMM | REVERTED
- Người đề xuất: <ghế>
- Người chấm: <ghế khác nhà cung cấp>
- Owner duyệt: <ngày, nơi ghi: PR/Issue>

## Quyết định
## Lý do (bằng chứng, số đo)
## Điều kiện hoàn tác (đo được, có hạn)
## Ảnh hưởng tới ARCHITECTURE.md (mục nào đổi)
```
