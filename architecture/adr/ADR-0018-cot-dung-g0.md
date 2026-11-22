# ADR-0018: Cột dừng/đảo 3 tuần của G0

- Ngày: 2026-11-22
- Trạng thái: QĐ-G0 ACCEPTED 22/11/2026, hiệu lực khi Owner gộp PR này.
- Người đề xuất: Claude Project TTC (Anthropic), ghế kiến trúc sư trưởng. Chép vào kho: phiên Claude Code (Anthropic).
- Người chấm: theo L-09, ghi trong thân PR.

## Bối cảnh

- `architecture/ARCHITECTURE.md` §8, hàng G0, cột "Dừng/đảo khi": "quá 3 tuần → chỉ giữ Ledger". Tính từ 22/10/2026 hoặc từ ngày gộp 24/10/2026, cột này đã quá hạn. §8 ghi chưa có biên bản Owner về cột này.
- ADR-0002 (mốc xét lại 31/03/2027) và ADR-0016 (mục "Điều kiện dừng và đảo") không thay cột này.

## Quyết định

| Mã | Quyết định |
|---|---|
| QĐ-G0 | Owner không áp cột "quá 3 tuần → chỉ giữ Ledger" của G0. Phạm vi v3.0 tiếp tục. Cột đó hết hiệu lực từ ngày Owner gộp ADR này. Các điều kiện dừng đo được sau đây tiếp tục áp dụng, không nới: (1) mốc xét lại 31/03/2027 của ADR-0002; (2) theo ADR-0016: D0 của FWD-001 chưa có tới 05/03/2027 thì báo Owner; sau 12 kỳ, không sổ bóng nào PASS thì FWD-001 ghi NO_EDGE (mục «Giao thức FWD-001 (QĐ-11)»); NO_EDGE cho cả không gian 13 × 3 trên VN30 chỉ ghi khi đồng thời không sổ bóng nào đạt và đợt 2 không có đặc tả qua bậc 2 (mục «Điều kiện dừng và đảo»); (3) cột "Dừng/đảo khi" của hàng G1 ở §8: dưới 20 dự báo mỗi tháng thì hạ độ khó câu hỏi. |

## Trạng thái từng quyết định

| QĐ | Trạng thái | Owner | Ngày |
|---|---|---|---|
| QĐ-G0 | ACCEPTED | Owner | 22/11/2026 |

## Không đổi

ADR này không sửa `architecture/ARCHITECTURE.md`, ADR-0002 hay ADR-0016. Dòng trỏ tới ADR này trong `ARCHITECTURE.md` do một PR riêng thêm (L-07).

## Điều kiện hoàn tác

Owner muốn áp lại cột cũ hoặc đặt cột dừng mới thì ghi bằng một ADR mới.
