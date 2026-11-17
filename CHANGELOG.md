# Changelog

## v3.0.2 — 2026-11-17 (làm nốt G0/G1: phân định, chấm A–B, mười luật vào máy kiểm) — Claude soạn, Owner đưa lên kho; ADR-0003
Sau bảy vòng chấm độc lập của ghế khác nhà cung cấp (năm vòng đầu 25 điểm; vòng 6 thêm 4 điểm HIGH; vòng 7 thêm 2 HIGH và 2 MEDIUM — đều đã sửa) và một lượt Claude tự rà toàn bộ theo lệnh Owner. Bảng luật ↔ máy kiểm và các giới hạn: `architecture/adr/ADR-0003-phan-dinh-va-van-hanh.md`. Hướng dẫn thao tác cho Owner: `docs/HUONG_DAN_VAN_HANH.md` mục 6–10.
- **Nhận dự báo** (`tools/ledger_intake.py`): ngày tính theo giờ Việt Nam; `model_cutoff` dạng YYYY-MM và `resolve_at` phải sau ngày cắt dữ liệu (L-05); `author_seat` bắt đầu bằng tên ghế (L-09); ghế B bắt buộc `prompt_hash` đúng prompt chuẩn hiện hành; mỗi ghế một dự báo cho một câu hỏi, A và B cùng luật và cùng nguồn; thân Issue không được trùng tiêu đề; nhận dấu phẩy thập phân; ghi `issue_author`. Vòng 6: `p`/`base_rate` chỉ nhận số thập phân viết bằng chữ số 0–9 (`NaN`, `Infinity`, `1e309`… bị từ chối; sổ ghi với `allow_nan=False` và kiểm chuỗi từ chối JSON không chuẩn); `resolve_at` đúng dạng `YYYY-MM-DD`; `resolution_source` phải nêu tên miền; câu hỏi đã phân định không nhận thêm dự báo.
- **Phân định** (Issue mẫu "Resolution", `tools/resolution_intake.py`, `resolution_intake.yml`) → `ledger/resolutions.jsonl` có chuỗi hash, khớp `contracts/resolution.schema.json`: một câu hỏi một sự thật cho mọi dự báo; đã phân định thì khóa (kể cả VOID); không trước hạn, trừ YES khi cả câu hỏi là `event_before_date`; người phân định khác ghế với mọi người viết; nguồn phải thuộc tên miền đã hứa. Vòng 6: tên máy chủ tách bằng `urllib` từ từng đường dẫn `https://` (không dò chuỗi) và mọi đường dẫn phải thuộc tên miền đã hứa — `https://nso.gov.vn@evil.com`, `https://evil.com/path/nso.gov.vn`, `https://evil.com/?referer=nso.gov.vn` bị từ chối.
- **Chấm A–B** (`engine/ledger.py` → `reports/scorecard.json` mục `issue_forecasts`, báo cáo vòng học): Brier theo ghế (so với xác suất nền và 0,5), hiệu chuẩn, VOID đếm riêng; cặp = cùng câu hỏi, cùng ngày; chỉ chấm khi cả hai đã phân định cùng sự thật; kiểm định nhị thức hai phía chốt trên 194 bất đồng đầu tiên; dòng hỏng không làm vỡ vòng học.
- **Sổ thử L-06 + Deflated Sharpe** (`engine/research.py`): đăng ký có hash chuỗi trước khi chạy; không gian giả thuyết đóng băng trong `config.yaml`; CI đối chiếu sổ với `trials.csv`; báo cáo in Sharpe và DSR. Vòng 6: trong vòng học trên GitHub, dòng đăng ký được đẩy lên `main` trước khi backtest chạy (`tools/registry_push.py`, `TTC_REGISTRY_PUSH=1`); đẩy không được thì không chạy; vòng học hỏng giữa chừng không làm mất lần thử, mã thử không bị dùng lại, báo cáo liệt kê mã bỏ dở.
- **Thư viện có máy kiểm** (`engine/knowledge_notes.py`): L-01 ghim sha256, địa chỉ, trích nguyên văn; L-04 giấy phép và nguồn được phép; L-08 hiệu lực, tự chuyển OUTDATED; L-09 biên bản chấm gắn nội dung (`note_sha256`), khác ghế; TESTED/PROVEN đóng cho tới khi có Học viện.
- **Cổng chấm PR** (`tools/review_gate.py`, `review_gate.yml`, mẫu PR): hai trường khác ghế + bản chấm dán thành bình luận PR có dòng đầu đúng `GỘP ĐƯỢC — commit <SHA>` (không chữ nào khác trên dòng đó); chạy bằng mã của `main`.
- **Kiểm toán sổ** (`tools/ledger_audit.py` trong CI): sổ chỉ-ghi-thêm so với commit gốc; mỗi dòng đối chiếu với Issue thật trên GitHub; cảnh báo khi `main` chưa có luật bảo vệ. Vòng 6: **dấu nhận** — workflow nhận đăng hash của dòng vừa ghi thành bình luận của `github-actions[bot]`, kiểm toán đòi mỗi dòng có dấu nhận trên đúng Issue, chưa sửa, trong 6 giờ sau khi Issue mở và trước ngày `resolve_at`, không có hash thứ hai cho cùng mã (dòng viết sau khi biết kết quả không mượn được giờ của Issue cũ); và `tools/validate.py` **chạy lại luật nhận và luật phân định** trên mọi dòng Issue đã có trong sổ.
- **Vòng 7** (chấm commit `2ba54fc`): (1) dòng phân định thiếu `resolution_issue` chỉ được trỏ tới dự báo của engine, engine không dùng nó để chấm dự báo Issue; dòng dự báo không từ Issue phải đúng là dòng engine (`P-…`). (2) Kết quả thử: 210 kết quả đầu ghim sha256 trong `config.yaml`; dòng neo lịch sử có sha256 ở đầu sổ đăng ký; engine chỉ ghi thêm vào `research/trials.csv` (`research.append_trial_results`), không viết lại dòng cũ; PR không được thêm kết quả hay dòng đăng ký; trên `main` commit ghi kết quả phải có đăng ký ở commit liền trước; thêm `paper/*.csv` vào danh sách chỉ-ghi-thêm. (3) Tổng số lần thử ở báo cáo và trạng thái gồm cả lần bỏ dở (`research.total_trials`). (4) Dấu nhận không còn 15 phút miễn kiểm; workflow mới `ledger_audit.yml` chạy kiểm toán sau mỗi lần robot ghi sổ, sau vòng học và mỗi ngày. Thiếu `jsonschema` là lỗi, không còn bỏ qua lặng lẽ.
- **Luật khác**: L-03 quét số định danh/số tài khoản; L-07 kiểm theo từng dòng của ARCHIVE; L-10 đề thi trong kho phải đã phát hành; công tắc an toàn lệch là lỗi.
- **Vận hành**: engine hằng tuần (thứ Sáu), kiểm luật trước và sau khi chạy; CI chặn gộp chạy mọi tệp test, test sửa tệp của kho thì đỏ; workflow không chèn biểu thức `${{ }}` nào vào lệnh (có test soát; vòng 6 sửa nốt ô `trials` của vòng học). Sửa `tests/test_adjustment.py`: kiểm point-in-time theo bảng sự kiện (chặt hơn bản gốc).
- **Văn bản**: ARCHITECTURE §3, §4.1, §4.2, §4.3; ADR-0001 ACCEPTED; ADR-0003; `state/PROJECT_STATE.yaml` cập nhật theo BOOT; README của `library/sources/` và `library/notes/` khớp với mã kiểm.
- **Không sửa**: `governance/LAWS.md` (chỉ Owner sửa; hai chỗ cần sửa chữ ghi ở ADR-0003).
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
