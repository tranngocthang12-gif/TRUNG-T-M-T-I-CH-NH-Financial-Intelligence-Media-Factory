# ADR-0005: Tạm gác "engine cờ kinh tế" (engine kịch bản)
- Ngày: 2026-11-17
- Trạng thái: PROPOSED (ACCEPTED khi Owner gộp PR chứa tệp này)
- Người đề xuất: Claude (kiến trúc sư trưởng)
- Người chấm: ghế khác nhà cung cấp (L-09), ghi ở PR
- Owner duyệt: khi gộp PR

## Quyết định
Ý tưởng của Owner (17/11/2026): một "engine cờ kinh tế" như phần mềm cờ tướng — đóng khung trạng thái kinh tế tại ngày phân tích làm bàn cờ, hôm sau có thông tin mới thì lấy đó làm khung mới, lấy hiệu quả đầu tư làm luật. Bản thiết kế đã soạn qua hai vòng góp ý của hội đồng AI (ngoài kho). Quyết định: **tạm gác**, không đưa vào kiến trúc v3.0, không viết mã.

## Lý do
- L-KT6 (một lát chạy trọn trước khi làm dày): đường dự báo → phân định → chấm mới đi trọn vòng ngày 17/11/2026 và chưa có dự báo nào; Thư viện chưa có ghi chú nào. Engine kịch bản cần cả hai làm đầu vào và làm thước đo.
- L-KT10 (đo được): chưa có số đo nào cho thấy engine kịch bản làm tốt hơn đối chứng; thước đo duy nhất hiện có là phép thử A–B, cần ~194 cặp bất đồng.
- ADR-0002: Owner ưu tiên hoàn thiện kiến trúc.

## Điều kiện hoàn tác (mở lại)
Mở ADR mới xét đưa engine kịch bản vào kiến trúc khi đủ cả hai: (a) sổ có ≥ 60 dự báo A+B hợp lệ (điều kiện thoát G1, ARCHITECTURE §8); (b) Thư viện có ≥ 10 ghi chú CITED.

## Ảnh hưởng tới ARCHITECTURE.md
Không.
