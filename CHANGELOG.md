# Changelog

## v1.1 — 2026-09-26 (phiên sửa lỗi sau kiểm tra)
- **Giá điều chỉnh (engine/adjust.py).** Kho `data/store` vẫn giữ GIÁ GỐC append-only làm bằng chứng. Hệ số điều chỉnh
  (chia tách / cổ tức cổ phiếu / cổ tức tiền) là dữ liệu DẪN XUẤT, tính lại toàn bộ mỗi lần, point-in-time, ghi
  `data/derived/adjustment_factors.csv` kèm `computed_at`. Sự kiện quyền: `data/corporate_actions.csv` (nhập tay, có nguồn)
  + `data/derived/yahoo_actions.csv` (tải lại mỗi lần). Feature, nhãn, regime, paper trading, Ledger resolution dùng giá điều chỉnh;
  paper áp sự kiện quyền vào vị thế đang nắm giữ.
- **Kiểm tra chất lượng.** Biến động vượt biên độ sàn (HOSE ±7%, SHB ±10% khi còn ở HNX) mà không có sự kiện quyền → cờ lỗi
  (`data/derived/quality_flags.csv`); ô lỗi bị loại khỏi feature (121 phiên nhìn lại), nhãn và chấm Ledger (VOID). Tỷ lệ lỗi
  20 phiên gần nhất > 1% → hôm đó không nghiên cứu, không dự báo, không khớp lệnh giấy. Hiện tại: 147/72.172 ô bị cờ (0,20%),
  0% trong 20 phiên gần nhất.
- **Xóa kết quả nghiên cứu đã học trên giá SAI**: `research/trials.csv` (16 thử nghiệm), `state/bandit.json`,
  `state/model_registry.json`. Lý do: giá Yahoo chưa điều chỉnh cổ tức cổ phiếu (TCB −49,5% ngày 11/06/2024, VCB −33,1% ngày
  03/03/2025 là cú rơi giả) và còn ~145 ô biến động vượt biên độ không có sự kiện → feature/nhãn của vòng 25/09 bị nhiễm.
  `knowledge/candidates/` chưa từng được tạo (không phát hiện nào sống sót) nên không có gì để xóa. `data/store` KHÔNG bị xóa.
  `state/ENGINE_STATE.json` và báo cáo 25/09 giữ làm lịch sử, sẽ được vòng kế tiếp ghi đè.
- **Nguồn dữ liệu.** PyPI đang cách ly (quarantined) gói `vnstock` và phụ thuộc `vnai` → không cài; bỏ bước
  `pip install vnstock` khỏi workflow. Yahoo là nguồn giá chính (`config.yaml: data.sources: [yahoo]`, `--source live`).
  Lỗi nguồn dữ liệu (từng mã, từng nguồn, kể cả sự kiện quyền Yahoo và RSS) ghi đầy đủ vào báo cáo chu kỳ và
  `state/ENGINE_STATE.json` (`data_ingest`, `news_errors`), kể cả ngày bỏ qua vòng học. Cập nhật `governance/DATA_SOURCES.yaml`.
  Test: `tests/test_ingest_errors.py`.
- **tools/validate.py** kiểm cấu trúc v2.x: file/thư mục bắt buộc (library/, academy/, DATA_SOURCES.yaml, OWNER_PROFILE.md,
  3 bản kiến trúc hiện hành), MỌI file YAML trong repo, cấp độ hợp lệ trong competency_map, đường dẫn `library:` của
  competency_map (cảnh báo nếu chưa có), contract đếm theo kiến trúc v2.0 (21/24 — thiếu knowledge_note, exam_item, dossier:
  cảnh báo, chưa chặn). Thiếu file bắt buộc / YAML hỏng / cấp độ sai → LỖI.
- `ARCHITECTURE_v2.0.md` chuyển vào `architecture/` cho khớp BOOT.md. `llm_review.py` đi qua Budget Governor
  (`tests/test_llm_review_budget.py`).
- `academy/competency_map.yaml`: hạ `tin_tuc_su_kien` và `dinh_luong` từ PRACTICED về SYNTHESIZED cho tới khi có bằng chứng
  dữ liệu thật.
- Test mới: `tests/test_adjustment.py` (TCB/VCB trên dữ liệu thật, point-in-time, loại ô lỗi, VOID, paper),
  `tests/test_quality_gate.py` (cổng chất lượng); `tests/test_no_lookahead.py` kiểm thêm trường hợp có cờ lỗi.
  Dữ liệu giả lập nay tôn trọng biên độ ±7%.

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
