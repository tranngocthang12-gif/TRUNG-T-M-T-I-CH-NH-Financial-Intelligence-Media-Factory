# Ma trận khả năng nghiên cứu point-in-time (VN30) và khả năng đánh giá alpha — 21/11/2026

- Cây đọc: `main` `20f5d924bbf52c34b68baeaff9df8d022a0af363`. Người viết: Claude (Anthropic). Chưa L-09, chưa Owner.
- Mã và test nhắc trong báo cáo (`tools/price_integrity_b1.py`, `tests/test_price_integrity_b1.py`, điều kiện 8 của `engine/verified_adjust.py`) nằm ở PR #71.
- Nguồn số liệu:
  - `data/vn30_history.csv` và `data/evidence/vn30_reviews/EVIDENCE_MANIFEST.json`;
  - kho giá (`data.load_store`, as_of 2026-11-20);
  - `data/derived/adjustment_factors.csv` (computed_at 2026-11-20T17:56);
  - `tools/price_integrity_b1.py`;
  - `reports/PIT-001_20261121.json` (chạy lại hai lần cho cùng byte, NOT_READY, 18 hạng mục).
- Phạm vi: kiểm định kỹ thuật. Không thu nguồn VN30 mới: việc đó là của ghế thi công trong Issue #57, không làm trùng. Không suy thành phần trước 2025-08-04 từ danh sách 2026. Không chuyển sang `HISTORICAL`.

## 1. Ma trận

`price_coverage` đếm số mã của rổ đã ghim có ít nhất một dòng giá trong khoảng. Có dòng giá không có nghĩa là đủ phiên (PIT-001 `PRICE_WINDOW_COVERAGE`). "KL0" là số ngày trong khoảng mà mọi dòng có khối lượng 0.

| date_from | date_to | universe_evidence | price_coverage | corporate_action_status | knowledge_cutoff | eligibility | blocker |
|---|---|---|---|---|---|---|---|
| 2016-01-01 | 2025-08-03 | **UNKNOWN**. Không có bản HOSE ghim; engine dùng 30 mã config | Rổ: UNKNOWN. Config: 15/30 mã có giá bắt đầu sau 2016 (ACB 2020-12-09, BCM 2021-03-15, GVR 2020-03-17, HDB 2018-01-05, PLX 2017-04-21, POW 2019-01-14, SAB 2016-12-06, SSB 2021-03-24, TCB 2018-06-04, TPB 2018-04-19, VHM 2018-05-17, VIB 2020-11-10, VJC 2017-02-28, VPB 2017-08-17, VRE 2017-11-06). KL0: 106 ngày | 0 xác minh. 102 sự kiện cổ phiếu Yahoo `TU_DONG` → `DA_NAM_TRONG_GIA_NGUON`; 2 sự kiện tay `CAN_DOI_CHIEU` → `APPLIED` (TCB, VCB, sai ngày, mục 3 báo cáo B1); 187 cổ tức tiền Yahoo `APPLIED` | Giá: tải một lần 2026-09-26, hồi cứu, không vintage. Sự kiện: không có `published_at` | **NOT_ELIGIBLE** (chỉ RETROSPECTIVE) | Thành phần UNKNOWN; thiên lệch sống sót; nguồn Yahoo điều chỉnh một phần; sự kiện chưa xác minh |
| 2025-08-04 | 2026-02-01 | Rổ tại đúng ngày 2025-08-04: hose-2388633 (PDF + tin), công bố 2025-07-16T16:28Z. Các ngày sau trong khoảng: **UNKNOWN** (không có bằng chứng rổ đứng yên) | 28/30; thiếu DGC, LPB. KL0: 4 | 8 Yahoo `DA_NAM_TRONG_GIA_NGUON`; 12 cổ tức tiền; 0 xác minh | Thành phần: công bố trước hiệu lực. Giờ quyết định chưa đăng ký (PIT-001 `DECISION_TIME_OF_KNOWLEDGE` INCONCLUSIVE). Giá: hồi cứu | **NOT_ELIGIBLE** | Thiếu giá 2 mã; continuity UNKNOWN; sự kiện chưa xác minh |
| 2026-02-02 | 2026-05-12 | Rổ tại 2026-02-02: hose-2432828 (PDF + tin), công bố 2026-01-21T19:06Z. Sau đó: UNKNOWN | 27/30; thiếu DGC, LPB, VPL. KL0: 8 | không có sự kiện cổ phiếu; 3 cổ tức tiền | như trên | **NOT_ELIGIBLE** | Thiếu giá 3 mã; continuity UNKNOWN |
| 2026-05-13 | 2026-08-02 | hose-2460387: **chỉ có tin**, không có PDF. Tin xác nhận loại DGC, thêm BSR; 28 mã còn lại chép từ PDF kỳ 01/2026. Không phải xác minh độc lập cả rổ | 27/30; thiếu BSR, LPB, VPL. KL0: 0 | 4 Yahoo `DA_NAM_TRONG_GIA_NGUON`; 13 cổ tức tiền | như trên | **NOT_ELIGIBLE** | Rổ chưa xác minh độc lập; thiếu giá 3 mã |
| 2026-08-03 | 2026-11-15 | Rổ tại 2026-08-03: hose-2479382 (PDF + tin), công bố 2026-07-15T15:05Z. Sau đó: UNKNOWN | 25/30; thiếu BSR, LPB, MCH, TCX, VPL. KL0: 5 (2026-08-31, 09-01, 09-02, 09-09, 10-05) | 3 Yahoo `TU_DONG` `APPLIED` (TPB 10-02, HDB 10-09, TCB 10-29) và 7 `DA_NAM_TRONG_GIA_NGUON`. Có 18 bản HOSE 2026H2 đã ghim nhưng `published_at` và `event_type` đều null, nên 0 xác minh | Giá từ 2026-09-28: quan sát theo phiên (vintage thật, khoảng 40 phiên tới as_of). Trước đó: hồi cứu | **NOT_ELIGIBLE** | Thiếu giá 5/30; sự kiện chưa xác minh; cửa sổ vintage quá ngắn cho walk-forward (train ≥ 500 phiên) |
| 2026-11-16 | 2026-11-20 | hose-2510691: PDF VNAllshare có mục VN30, 30 mã trùng rổ 2026-08-03; ngày hiệu lực lấy từ tin, công bố 2026-11-02T15:31Z | 25/30; thiếu như trên. KL0: 0 | không có sự kiện cổ phiếu mới | Giá quan sát theo phiên | **NOT_ELIGIBLE**. Đây là **ứng viên duy nhất cho đánh giá tiến về tương lai**, nếu bổ sung giá 5 mã | Thiếu giá 5/30; giờ quyết định chưa đăng ký |

**Kết luận ma trận: không có khoảng nào ĐỦ ĐIỀU KIỆN cho backtest point-in-time.**

- Hướng khả thi duy nhất là đánh giá tiến về tương lai từ một mốc có rổ đã ghim, cụ thể 2026-11-16. Điều kiện:
  - ghi giá theo phiên;
  - đăng ký trước giờ quyết định;
  - bổ sung giá cho BSR, LPB, MCH, TCX, VPL.
- Hướng này không cho số liệu lịch sử và không được gọi là backtest.

## 2. Kiểm định kỹ thuật VN30 (mục V lệnh)

| Câu hỏi | Trả lời có căn cứ | Trạng thái |
|---|---|---|
| Tài liệu HOSE gốc có đủ ngày hiệu lực và đúng chỉ số? | Bốn PDF có mục VN30 trùng `members_after` (PIT-001 `PDF_VN30_CONTENT` PASS). Ngày hiệu lực **không** in trong chữ PDF mà nằm ở tin JSON đã ghim (`NEWS_EFFECTIVE_DATE_TEXT` PASS). Kỳ 2026-05-13 chỉ có tin | PASS có giới hạn |
| Lịch sử bao phủ từ đầu nghiên cứu? | Không. `data.start` 2016-01-01; bản gốc đầu 2025-08-04 | FAIL |
| Khoảng giữa các kỳ có bằng chứng rổ không đổi? | Không có tệp nào (thay thế bất thường, hủy niêm yết, sáp nhập đều chưa loại trừ được) | UNKNOWN |
| Schema CSV lệch ADR-0008 ở đâu? | CSV: `effective_date,ticker,action,source_id` với `ADD/REMOVE`. ADR-0008: `effective_date,ticker,change,source_url,source_status` với `IN/OUT` và `DA_DOI_CHIEU/CAN_DOI_CHIEU`. Thiếu `source_status`; `source_url` chỉ suy được qua manifest. Cần adapter hoặc quyết định Owner; **không ghi đè CSV** | FAIL (ADR0008_SCHEMA) |
| `universe_basis: CURRENT` gây sai lệch gì? | (1) Thiên lệch sống sót và nhìn trước: mã được chọn vì đã lớn ở thời điểm lập danh sách, nên IC, lãi ròng, Sharpe 2016–2025 bị đẩy lên. Độ lớn **không đo được** khi chưa có thành phần lịch sử; không bịa con số. (2) Danh sách config **không còn là rổ hiện tại**: có BCM, BVH, PLX, POW, TPB đã ngoài rổ 2026-08-03/11-16; thiếu BSR, LPB, MCH, TCX, VPL. (3) Mã niêm yết muộn chỉ vào panel khi có trên 250 dòng giá, và mã thiếu lịch sử bị loại **im lặng** (test C3 xfail). (4) Benchmark là bình quân đều các mã đó, không phải VN30 hay VN-Index | FAIL (ENGINE_UNIVERSE_MODE, CONFIG_VS_EVIDENCED_BASKET) |
| Mã thiếu giá hoặc thiếu sự kiện? | Thiếu giá: BSR, DGC, LPB, MCH, TCX, VPL. Có giá nhưng ngoài mọi rổ ghim: BVH, POW. Sự kiện: 0/151 sự kiện cổ phiếu và 0/283 cổ tức tiền được xác minh | FAIL |
| Lịch giao dịch | 123 ngày trong kho có mọi dòng khối lượng 0 và giá không đổi (4.954/73.402 dòng). Phần lớn trùng kỳ nghỉ lễ; 2 ngày năm 2026 không giải thích được. Engine tính chúng là phiên. Chưa ghim lịch HOSE gốc | FAIL (mới) |
| Ngày niêm yết và hủy niêm yết | ACB, VIB, SSB, BCM, GVR có giá Yahoo `.VN` chỉ từ ngày lên HOSE; lịch sử ở sàn trước không có. Không có dữ liệu hủy niêm yết (rổ config chỉ gồm mã còn sống) | UNKNOWN |
| Trần/sàn và khả năng khớp | Biên 7% (SHB 10% tới 2023 theo override, ngày chuyển sàn chưa đối chiếu). Giấy không khớp ở 95% biên (ADR-0008). **Backtest (`research.metrics`) không có** điều kiện không khớp, giới hạn tham gia khối lượng hay làm tròn lô: giả định khớp của backtest lạc quan hơn giấy | INCONCLUSIVE (MARKET_MICROSTRUCTURE_ASSUMPTIONS) |

## 3. Điều kiện để sáu hạng mục PIT-001 đạt PASS bằng bằng chứng

Không hạ ngưỡng, không đổi UNKNOWN thành PASS. Cột "test" chỉ test hành vi đã viết thành mã. Test `xfail(strict=True)` sẽ đỏ CI khi engine bắt đầu đạt, buộc người sửa gỡ xfail và nộp chứng cứ.

| Hạng mục | Hiện tại | Điều kiện PASS (đủ cả) | Test hành vi | Cổng còn thiếu |
|---|---|---|---|---|
| `DECISION_TIME_OF_KNOWLEDGE` | INCONCLUSIVE | (a) Giờ quyết định của mỗi phiên được đăng ký trước, có hash, theo giờ VN. (b) Với mọi dữ liệu dùng tại phiên đó (thành phần, sự kiện quyền, giá) có `published_at` và `observed_at` ≤ giờ quyết định. (c) Truy vấn tại giờ trước công bố trả "không biết" | `test_c2_verified_research_input_ignores_event_published_after_decision_date` (xfail; kiểm chế độ `research_input="verified"` chạy song song). Phía cổng kiểm chứng đã có `cong_bo_sau_ngay_cat`, phía thành phần đã có `test_publication_same_day_after_decision_is_fail` | Owner chọn giờ quyết định; engine đọc `published_at` (PR engine, ADR-0009 điều 7) |
| `CONTINUITY_BETWEEN_REVIEWS` | UNKNOWN | Với mỗi khoảng giữa hai kỳ: bản gốc HOSE chứng minh không có thay đổi bất thường, hoặc mọi thay đổi bất thường đã ghim. Không suy từ việc thiếu tin | (chưa viết: thiếu nguồn) | Ghế thi công thu thông báo thay đổi bất thường (Issue #57) |
| `ENGINE_UNIVERSE_MODE` | FAIL | Với `universe_basis: HISTORICAL`, panel nghiên cứu không có ô (ngày, mã) ngoài thời gian là thành viên; ngày UNKNOWN bị loại khỏi kết luận | `test_c4_historical_universe_excludes_ticker_after_exit` (xfail) | PR engine riêng theo ADR-0008 khi `vn30_history` phủ đủ; L-09; Owner |
| `PRICE_WINDOW_COVERAGE` | FAIL | Mọi mã trong rổ có giá ở mọi phiên chính thức của khoảng (đối chiếu lịch HOSE gốc); phiên không giao dịch không được tính; mã bị loại vì thiếu lịch sử phải được báo | `test_c3_ticker_dropped_for_short_history_is_reported`, `test_c5_non_trading_rows_are_not_counted_as_sessions` (xfail); `test_price_one_row_per_symbol_is_not_window_pass` (đã có) | Giá cho 6 mã thiếu; lịch HOSE ghim; PR engine |
| `UNVERIFIED_EVENTS_IN_RESEARCH_CHAIN` | FAIL | Có chế độ đầu vào nghiên cứu đã kiểm (`research_input="verified"`) chỉ chứa sự kiện `in_verified_chain`, ô nhiễm bị loại; đầu ra mang `derivation_id` và nhãn PIT. Đường mặc định có đổi hay không là phương án (A)/(B)/(C) do Owner chọn, không phải điều kiện PASS | `test_c1_verified_research_input_rejects_unverified_corporate_event`, `test_c6_research_input_carries_derivation_id_and_pit_label` (xfail); `test_b1`–`b5` (cổng kiểm chứng, pass) | ADR-0009 điều 7; quyết định phương án (A)/(B)/(C) tại báo cáo B1 mục 5 |
| `MARKET_MICROSTRUCTURE_ASSUMPTIONS` | INCONCLUSIVE | (a) Biểu phí, thuế, bước giá, lô có văn bản gốc ghim. (b) Backtest áp không khớp ở khóa trần/sàn như giấy và giới hạn tham gia khối lượng. (c) Có `paper/trades.csv` thật để đối chiếu tỷ lệ không khớp | (chưa viết: cần quyết định mô hình khớp) | Thư viện nguồn (biểu phí HOSE/VSD, quy chế giao dịch); ADR cho mô hình khớp của backtest |

## 4. Khả năng đánh giá alpha và L-06 (mục VIII lệnh)

Đối chiếu Issue #59 và PR #67, không làm trùng: PR #67 chặn chạy thủ công từ nhánh phụ, vẫn DRAFT.

| Kiểm tra | Bằng chứng trên `main` | Đánh giá |
|---|---|---|
| Sổ đăng ký thử | `research/trial_registry.jsonl` 7 dòng: neo `LEGACY-ANCHOR` (216 kết quả cũ) + T00217–T00222. Chuỗi `prev_hash` liền | Đạt về cấu trúc |
| Đăng ký trước, ghi remote | `git log`: c87a004 (14:43:06Z) … deebcda (14:43:18Z), sáu commit đăng ký, **trước** commit kết quả 7aa4634 (14:43:29Z) ngày 2026-11-20 | Đạt cho 6 lần thử này. Lần chạy dùng 6 lần thử trong khi Owner duyệt 1 (Issue #59); PR #65 đã gộp guard |
| Chạy từ nhánh phụ | PR #67 DRAFT | Chưa có trên main; không làm trùng |
| Scorecard | `tools/validate.py --require-fresh-scorecard` OK tại HEAD | FRESH. 6 dự báo, 0 resolved, 0 `timing_valid` |
| Thứ tự đăng ký → huấn luyện → đánh giá → ghi | `run_cycle.cycle`: `register_trial` (kèm `persist_registration`, ném lỗi nếu push hỏng) trước `walk_forward`; `append_trial_results` sau | Đạt theo mã |
| Walk-forward, nhãn chồng lấn, embargo | Embargo h+1 phiên: nhãn train cuối dùng giá tới phiên trước ngày test đầu, purge đúng. t-stat IC nhân √(n/h) (hiệu chỉnh chồng lấn thô) | Đạt có giới hạn |
| Holdout | **Không có holdout khóa.** Mọi 222 lần thử đánh giá trên cùng chuỗi ngoài mẫu walk-forward, nên mẫu ngoài mẫu bị dùng lại; chỉ được bù bằng ngưỡng Bonferroni theo số lần thử và DSR | Thiếu |
| Multiple testing / DSR | Ngưỡng t hiện 3,69 (222 lần thử). DSR chỉ có cho 6 lần mới; phương sai Sharpe dùng công thức lý thuyết vì < 10 Sharpe đã ghi. Max IC-t lịch sử 1,06. 222/222 REJECTED | Đạt về cơ chế; kết quả **NO_EDGE** |
| Benchmark, phí, trượt giá, không khớp | Nhãn là lợi suất vượt bình quân đều các mã có dữ liệu trong danh sách config (không phải VN30 hay VN-Index); trừ 0,6% mỗi vòng quay (phí 0,15% × 2 + thuế 0,1% + trượt 0,1% × 2); không có khóa trần/sàn, giới hạn thanh khoản hay lô trong backtest | INCONCLUSIVE |

**Kiến nghị:**

1. Chưa mở baseline.
2. Không chạy lần thử mới, không huấn luyện lại, không promote.
3. Mở baseline (BASELINE-001 trong ADR-0015 nếu Owner duyệt) chỉ khi cùng lúc có đủ:
   - một khoảng có thành phần đã ghim và đủ giá;
   - đầu vào nghiên cứu chỉ gồm sự kiện đã kiểm chứng (hoặc Owner chấp nhận nhãn RETROSPECTIVE có ghi rõ);
   - lịch phiên đã ghim;
   - holdout khóa được đăng ký trước;
   - mô hình khớp cho backtest;
   - benchmark đặt đúng tên.

Kết quả hiện có của engine chỉ được ghi là **NO_EDGE trên dữ liệu chưa đạt PIT**. Đó không phải bằng chứng thị trường không có lợi thế, cũng không phải bằng chứng có.
