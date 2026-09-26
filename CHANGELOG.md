# Changelog

## v1.0-GĐ1 — 2026-09-26 (AUTO HỌC)
- Prediction Ledger: dự báo ghi trước khi biết kết quả (ledger/predictions.jsonl), kết quả ghi riêng (ledger/resolutions.jsonl).
- Auditor (code): loại dự báo có nguồn không tồn tại, mã ngoài universe, horizon/xác suất sai luật → ledger/rejected.jsonl.
- Resolution + Scorecard (code): Brier, calibration, so với baseline MẠNH NHẤT (xác suất nền lịch sử, luôn 50%).
- Fact Layer tin tức (RSS) với id = hash(link).
- Chuyên gia Claude: news@v1 và devils_advocate@v1 (lần gọi riêng, xác suất riêng, cũng bị chấm).
- Budget Governor: chuyên gia chỉ chạy khi Owner bật chi tiêu, đặt trần ngày/tháng và đơn giá; nhật ký memory/economic/api_spend.csv.
- 3 contract mới: PREDICTION, RESOLUTION, PROCEDURE.
- Kiểm thử tests/test_ledger_pipeline.py (chuyên gia giả lập, không tốn API).

## v0.2 — 2026-09-26
- Thêm bộ não học máy `engine/`: data append-only, 13 feature, regime, walk-forward có embargo, ngưỡng t tăng theo số thử, cổng 12 tháng gần nhất, meta-learning Thompson sampling, model registry, decay từ dự báo thực tế, paper trading khớp T+1, attribution, LLM phản biện tùy chọn.
- GitHub Actions chạy vòng học 16:30 mỗi ngày giao dịch và tự commit kết quả.
- Test chống look-ahead và diễn tập trên dữ liệu giả lập có quy luật đảo chiều.

## v0.1 — 2026-09-26
- Khởi tạo bộ não Trung Tâm Tài Chính theo Architecture v0.1.
- 18 core contracts, governance, safety state, orchestrator, auto mode, state, memory.
