# Changelog

## v3.0.2 — 2026-11-17 (làm nốt G0/G1: phân định, chấm A–B, luật vào máy kiểm) — Claude soạn, Owner đưa lên kho; ADR-0003
- **Phân định dự báo.** Issue mẫu "Resolution" + `resolution_intake.yml` + `tools/resolution_intake.py` → `ledger/resolutions.jsonl`. Không phân định trước hạn (trừ YES của `event_before_date`), không phân định lại, một Issue một câu hỏi, người phân định không phải Claude (L-09), YES/NO phải có nguồn và trích nguyên văn, VOID phải có lý do. Chỉ Issue do Owner mở.
- **Chấm A–B** (`reports/scorecard.json` → `issue_forecasts`; báo cáo vòng học): Brier theo ghế, hiệu chuẩn, cặp A–B, tỷ lệ bất đồng, độ đúng của A trên tập bất đồng, p so với tung đồng xu, tiến độ tới 194.
- **Thư viện có máy kiểm** (`engine/knowledge_notes.py`, gọi từ `validate.py`): L-01 tài liệu gốc ghim sha256/bytes, địa chỉ trang/đoạn/bảng tồn tại, trích nguyên văn; L-04 giấy phép, nguồn không bị cấm trong `DATA_SOURCES.yaml`; L-08 hiệu lực văn bản, vòng học tự chuyển OUTDATED; L-09 trạng thái ngoài DRAFT cần biên bản chấm của người khác. Quy ước: `library/notes/README.md`.
- **L-03** quét số định danh/số tài khoản trong tệp chữ. **L-09** mẫu PR `authored_by`/`reviewed_by` + workflow `review_gate.yml`.
- **L-06 + Deflated Sharpe.** Mỗi lần thử đăng ký vào `research/trial_registry.jsonl` (hash chuỗi) trước khi chạy; `trials.csv` thêm `sharpe`, `sharpe_ann`, `dsr`, `registry_hash`; CI đối chiếu sổ với kết quả.
- **Engine hằng tuần** (thứ Sáu 16:30 giờ VN) theo §4.3.
- **CI chặn gộp chạy đủ mọi test**: test dạng script mỗi tệp một tiến trình (hết lỗi thu thập của pytest), thêm bước "test không được sửa tệp nào của kho". Sửa `tests/test_adjustment.py`: Yahoo bổ sung nhiều sự kiện quyền cho TCB/VCB nên test kiểm đúng sự kiện (mã, ngày GDKHQ) và hệ số chia tách qua ngày 11/06/2024 thay vì đòi "không điều chỉnh gì".
- **`validate.py` theo v3.0**: bỏ danh sách "v2.x yêu cầu" (đã SUPERSEDED); thêm tệp bắt buộc của v3.0; contract 25/25 thành lỗi nếu thiếu; dòng THÔNG TIN tiến độ G1.
- **Văn bản**: ARCHITECTURE §3 ghế thi công không phải MINH TRÍ; §4.1 bước 2 và 4; §4.3; ADR-0001 ACCEPTED; ADR-0003; danh mục ADR.
- **Bản 2 sau chấm độc lập (17/11/2026, ghế khác nhà cung cấp — SỬA TRƯỚC, 8 HIGH / 9 MEDIUM / 1 LOW; sửa đủ 18):**
  (1) `test_adjustment.py` kiểm point-in-time chặt hơn bản gốc: hệ số neo = 1 đúng bằng 1, chỉ cổ tức tiền ∈ [1; 1,05), không sự kiện tương lai APPLIED, và close/raw tại mỗi ngày = tích `price_factor` các sự kiện APPLIED sau ngày đó;
  (2) phân định: một Issue ghi cho MỌI dự báo của câu hỏi (một sự thật), câu hỏi đã phân định thì khóa kể cả VOID, YES sớm chỉ khi mọi dự báo của câu hỏi là `event_before_date`, chặn resolver theo bảng nhà cung cấp (Opus/Sonnet/Haiku…), ghi theo `resolution.schema.json` (VOID = `outcome null` + `void`), chuỗi hash cho `resolutions.jsonl` và CI kiểm;
  (3) chấm A–B: ghép cặp theo thứ tự trong từng câu hỏi, chỉ tính khi cả A và B đã phân định cùng một sự thật, p hai phía (khớp cỡ mẫu 194), đếm cặp lẻ và cặp mâu thuẫn;
  (4) DSR: phương sai Sharpe dự phòng 1/(T−1) khi sổ cũ chưa có Sharpe (SR0 không còn = 0), N = mọi lần thử;
  (5) L-09 dùng chung `same_provider()` cho PR, biên bản chấm ghi chú và resolver; (6) `knowledge_notes` kiểm địa chỉ `counts` và `reading_flags` tồn tại; (7) L-03 quét cả `research/`, `paper/`; (8) `validate` đếm tiến độ G1 chỉ dự báo A+B; (9) workflow intake đỏ khi mã 1.
  **Bản 3 (vòng chấm 2, 17/11/2026 — còn 4 điểm, đã sửa đủ):** `reviewed_by` nhận "Owner" theo từ, không theo chuỗi con (`not-an-owner`, `downer` → đỏ); `resolution.schema.json` cho `excess_return` null ở dòng VOID của engine (test khớp schema cho cả hai loại dòng); `validate.py` báo lỗi thay vì đổ khi `predictions.jsonl` có dòng hỏng; báo cáo vòng học in cả số cặp lẻ và số cặp mâu thuẫn.
  **Bản 4 (vòng chấm 3, 17/11/2026 — còn 1 điểm LOW, đã sửa):** `reviewed_by` phải BẮT ĐẦU bằng tên ghế chấm ("Owner" hoặc tên mô hình/nhà cung cấp), ranh giới theo `\w` Unicode; `not_an_owner`, `éowner`, `an owner`, `not_a_grok` đều đỏ. Dò cùng nhà cung cấp vẫn lỏng ở mọi vị trí.
  **Bản 5 (vòng chấm 4, 17/11/2026 — còn 1 điểm MEDIUM, đã sửa; kèm tự rà cùng loại kẽ ở ba nơi dùng L-09):** Owner là một ghế: `authored_by: Owner` với `reviewed_by: Owner (…)` bị chặn; mỗi trường chỉ được một dòng; `authored_by` cũng phải bắt đầu bằng tên ghế. Một hàm `recognised_seat()` dùng chung: người phân định dự báo phải bắt đầu bằng tên ghế và không chung nhà cung cấp với bất kỳ `author_seat` nào của câu hỏi (không chỉ Anthropic); biên bản chấm ghi chú đòi cả `read_by` và `auditor` nhận ra được ghế.
  **Bản 6 (vòng chấm 5, 17/11/2026 — còn 1 điểm MEDIUM, đã sửa):** tập người viết của một câu hỏi gom bằng `_seats` (nhà cung cấp hoặc Owner), nên dự báo có `author_seat: Owner` thì resolver Owner bị chặn; `ledger_intake` từ chối `author_seat` không bắt đầu bằng tên ghế; phân định đóng lại khi gặp dòng cũ không nhận ra ghế viết. Không còn chỗ nào so người viết/người chấm bằng `_providers` trần.
  Lỗi phát hiện thêm nhờ bước CI "test không được sửa tệp của kho": `test_adjustment` giả lập `_append` nhưng `resolve` nay ghi qua `_append_chained` → stub cả hai.
- **Còn lại (ADR riêng):** kho dữ liệu ghi tăng dần (C2).

## v3.0.1 — 2026-11-16 (sửa lỗi Ledger P0 của G0) — Claude soạn, Owner đưa lên kho
- **Vòng học không vỡ khi có dự báo Issue.** Dòng từ Issue "Forecast" không có `id` và `resolution_rule` là chuỗi, nên `engine/ledger.py` (`resolve`, `scorecard`) ném lỗi → `daily_cycle` dừng ngay sau dự báo đầu tiên. Nay engine chỉ chấm bằng giá dòng của chính nó; dòng Issue được đếm theo ghế A/B trong `reports/scorecard.json` (`issue_forecasts`) và báo cáo vòng học.
- **Một hash chuỗi cho mọi bên ghi.** Đường experts của engine ghi `prev_hash`/`hash` như `tools/ledger_intake.py` (trước đó sẽ làm đỏ `validate`). Dòng Issue có `id` = `F-<số Issue>`.
- **L-02 kiểm ngay khi nhận.** Dự báo chứa từ khóa khuyến nghị bị từ chối trước khi ghi (Ledger chỉ ghi thêm; một dòng sai sẽ làm `validate` đỏ và dừng vòng học vĩnh viễn).
- **`ledger_intake.yml`.** Chỉ nhận Issue lúc mở (`opened`) do chính Owner mở (kho công khai: người lạ không ghi được vào sổ); bỏ sự kiện `labeled` (Issue cũ gắn nhãn muộn có thể đã bị sửa sau khi biết kết quả, trái L-05); bỏ nhóm concurrency chung (GitHub hủy run đang chờ → mất dự báo khi mở nhiều Issue liền); mỗi run tự lấy `main` mới nhất, tính lại chuỗi và thử lại khi bị trùng.
- **`daily_cycle.yml`.** Rebase rồi mới đẩy, thử lại tối đa 5 lần (Ledger intake có thể đã đẩy trong lúc vòng học chạy).
- **Test.** `tests/test_ledger_compat.py` (chặn merge): Issue A/B + dự báo engine + Issue tiếp theo trong một tệp; engine chấm đúng một dòng, đếm đúng theo ghế, chuỗi hash nguyên vẹn; L-02 từ chối khi nhận. Thêm `tools/__init__.py`.

## v3.0 — 2026-10-22 (G0: hợp nhất kiến trúc, luật, đường ghi dự báo) — Claude soạn, Owner đưa lên kho
- **Một kiến trúc.** `architecture/ARCHITECTURE.md` thay v0.1–v2.2; bản cũ liệt kê SUPERSEDED trong `architecture/ARCHIVE.md`; ADR-0001 có điều kiện hoàn tác 30 ngày.
- **Luật vận hành.** `governance/LAWS.md` L-01…L-10; `tools/laws_checks.py` kiểm máy L-02 (không khuyến nghị), L-07 (một kiến trúc), hash chuỗi Ledger; gọi từ `tools/validate.py`.
- **Ledger không cần API.** Mẫu Issue "Forecast" + `ledger_intake.yml` + `tools/ledger_intake.py`: kiểm schema `contracts/forecast_issue.schema.json`, từ chối ngày đã qua (L-05), ghi `ledger/predictions.jsonl` với `issue_created_at`, `sha256`, `prev_hash`.
- **Hợp đồng.** Thêm `knowledge_note`, `exam_item`, `dossier` (v2.0 IX) và `forecast_issue`; tổng 25.
- **Học viện / Thư viện.** `academy/curriculum.md` v0.1 theo thứ tự có bằng chứng; `library/INDEX.md`, `library/SOURCE_MANIFEST.json`, `library/reading_queue.yaml` (miền hẹp đầu tiên, đã cập nhật TT 99/2025, NĐ 245/2025, Luật 56/2024).
- **CI.** `tests.yml`: việc `gate` (test luật, chống nhìn trước, validate) chặn merge; việc `full-suite` chạy đủ 7 test ở chế độ thông tin (`continue-on-error`) vì 4 test engine hiện lỗi khi thu thập trong môi trường mới (C5 bản hiểu, sửa ở ADR riêng); `daily_cycle.yml` không đổi.
- **Chưa làm (ADR riêng):** hạ engine về hằng tuần, sổ thử + Deflated Sharpe, kho dữ liệu append.

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
- **Chưa làm được / còn mở:** sự kiện quyền TCB, VCB nhập từ hiểu biết + khớp tỷ lệ với bước nhảy giá, CHƯA gắn đường dẫn CBTT
  (không truy cập được HOSE/VSD từ môi trường phiên này); 147 ô Yahoo vượt biên độ chưa giải thích (đang bị loại);
  phần tải sự kiện quyền Yahoo chưa chạy với mạng thật (Yahoo bị chặn trong môi trường phiên, sẽ chạy lần đầu trên Actions);
  3 contract v2.0 và khung Thư viện/Học viện GĐ1 chưa có.

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
