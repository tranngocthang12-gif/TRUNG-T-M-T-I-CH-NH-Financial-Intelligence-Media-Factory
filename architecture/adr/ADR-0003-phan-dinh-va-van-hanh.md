# ADR-0003: Phân định dự báo qua Issue, chấm A–B, đưa các luật còn thiếu vào máy kiểm, engine hằng tuần
- Ngày: 2026-11-17
- Trạng thái: PROPOSED (ACCEPTED khi Owner gộp PR v3.0.2)
- Người đề xuất: Claude (kiến trúc sư trưởng)
- Người chấm: ghế khác nhà cung cấp, chấm bản 1 ngày 17/11/2026: SỬA TRƯỚC (8 HIGH / 9 MEDIUM / 1 LOW), đã sửa đủ ở bản 2 (CHANGELOG v3.0.2); tên ghế do Owner ghi vào `reviewed_by` của PR #28 sau khi ghế đó chấm lại bản 2
- Owner duyệt: khi gộp PR v3.0.2
- Ghi chú số: ADR-0002 để dành cho việc xét thu hẹp v3.0 theo điều kiện hoàn tác của ADR-0001.

## Quyết định
1. **Phân định dự báo Issue** bằng Issue mẫu "Resolution" + `tools/resolution_intake.py` + `resolution_intake.yml`, ghi `ledger/resolutions.jsonl` (đúng hợp đồng `contracts/resolution.schema.json`, có chuỗi hash). Luật: một Issue phân định một câu hỏi và ghi cùng một outcome cho MỌI dự báo của câu hỏi đó (A và B không thể nhận hai sự thật); câu hỏi đã phân định thì khóa, kể cả VOID; không phân định trước `resolve_at` (trừ YES khi mọi dự báo của câu hỏi có luật `event_before_date`); người phân định không cùng nhà cung cấp với ghế viết (Anthropic) theo bảng `tools/laws_checks.PROVIDERS` (L-09); YES/NO bắt buộc nguồn và trích nguyên văn; VOID bắt buộc lý do. Thay cho ý "engine tự chấm numeric_range/comparison" ở §4.1 bước 4: chỉ tiêu BCTC/NHNN không có nguồn máy đọc ổn định, nên người đọc nguồn công khai và trích nguyên văn là cách kiểm được.
2. **Chấm A–B** trong `engine/ledger.issue_summary` → `reports/scorecard.json` (`issue_forecasts`): theo ghế n, Brier, Brier của xác suất nền, hiệu chuẩn; cặp A–B cùng câu hỏi và cùng `resolve_at` (A thứ i ghép B thứ i theo số Issue); bất đồng = hai ghế ở hai phía 0,5; độ đúng của A trên tập bất đồng mà cả hai đã được phân định cùng một sự thật; p **hai phía** so với tung đồng xu (khớp cách tính cỡ mẫu 194 ở §4.2), tiến độ tới 194; cảnh báo khi tỷ lệ bất đồng < 10% (từ 20 cặp).
3. **Luật vào máy kiểm** đúng như cột "Máy kiểm" của `governance/LAWS.md`: L-01/L-04/L-08 (`engine/knowledge_notes.py`: tài liệu gốc ghim sha256, đủ trường, nguồn không bị cấm, địa chỉ tồn tại, trích nguyên văn, hiệu lực → tự chuyển OUTDATED), L-03 (quét số định danh/số tài khoản), L-06 (sổ đăng ký thử có hash chuỗi, đăng ký trước khi chạy, CI đối chiếu; Deflated Sharpe báo cùng Sharpe), L-09 (mẫu PR `authored_by`/`reviewed_by` + `review_gate.yml`).
4. **Engine hằng tuần** (thứ Sáu 16:30 giờ VN) đúng §4.3: số lần thử tăng 6/tuần thay vì 30/tuần nên ngưỡng Bonferroni không phình vô ích; ingest tải bù mọi phiên từ ngày cuối trong kho.
5. **Đính chính §3**: ghế thi công chưa lập và không phải MINH TRÍ (quyết định Owner 22/10/2026). Mọi chỗ trong `docs/TTC_TANG_HOC_HIEU_v0.2.md` ghi MINH TRÍ là ghế thi công hoặc ghế A đọc là "ghế thi công (chưa lập)".
6. **CI**: mọi tệp `tests/test_*.py` đều chạy và chặn gộp (test dạng script chạy mỗi tệp một tiến trình); test làm thay đổi tệp của kho thì CI đỏ.

## Lý do
- Đánh giá 16/11/2026: dự báo không có đường phân định thì Ledger không bao giờ ra điểm; sáu luật ghi "máy kiểm" nhưng chưa có mã kiểm; 4 test engine hỏng bị CI bỏ qua; bộ test làm thay đổi `data/store/prices.csv.gz`; engine chạy hằng ngày trái §4.3 (210 lần thử, ngưỡng t 3,67).
- Ghi chú dựa trên văn bản hết hiệu lực phải tự chuyển OUTDATED (L-08, bài học TT 200 → TT 99/2025).

## Điều kiện hoàn tác
- Workflow nhận/phân định làm CI đỏ hoặc mất dữ liệu Ledger 2 lần trong 30 ngày → hoàn tác phần 1 bằng PR riêng; dữ liệu đã ghi giữ nguyên.
- Vòng học hằng tuần thất bại 2 tuần liên tiếp vì thay đổi của PR này → hoàn tác phần 3 (L-06/DSR) và phần 4 bằng PR riêng.
- Kiểm L-03 báo nhầm ≥ 3 lần trong 30 ngày → thu hẹp mẫu quét bằng PR riêng.

## Ảnh hưởng tới ARCHITECTURE.md
Dòng trạng thái đầu tệp; §3 (ghế thi công); §4.1 bước 2 và 4; §4.3 (ghi việc đã làm, còn C2).
