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

## Danh mục
| ADR | Tên | Trạng thái |
|---|---|---|
| ADR-0001 | Hợp nhất sáu bản kiến trúc thành ARCHITECTURE.md v3.0 | ACCEPTED 24/10/2026 (PR #3) |
| ADR-0002 | (để dành: xét thu hẹp v3.0 theo điều kiện hoàn tác của ADR-0001) | — |
| ADR-0003 | Phân định dự báo qua Issue, chấm A–B, luật vào máy kiểm, engine hằng tuần | PROPOSED |
