# TRUNG TÂM TÀI CHÍNH — ARCHITECTURE v3.0 (bản hợp nhất, duy nhất có hiệu lực)

Ngày: 22/10/2026 · Kiến trúc sư trưởng: Claude · Owner: Trần Ngọc Thắng · Trạng thái: ACCEPTED (Owner gộp PR #3 ngày 24/10/2026); sửa đổi bởi ADR-0002, ADR-0003 và ADR-0004 (ACCEPTED 17/11/2026), ADR-0005, ADR-0006 và ADR-0007 (ACCEPTED 17/11/2026), ADR-0008 (ACCEPTED 18/11/2026, căn cứ Owner gộp PR #31), ADR-0009 (ACCEPTED 18/11/2026, PR #32 đã L-09; điều 7 chưa đổi engine). Ghế thi công: Grok (xAI), Owner lập 18/11/2026 (ADR-0010, hiệu lực khi Owner gộp). Do Claude soạn một mình theo lệnh Owner 22/10/2026 (giai đoạn xây kiến trúc); chưa có phản biện độc lập cho bản gốc — xem `governance/ARCHITECT_HANDOFF_20261022.md` mục 4.
Bản này **thay thế** v0.1, v0.2, v1.0, v2.0, v2.1, v2.2. Các bản cũ giữ nguyên chỗ nhưng được liệt kê là SUPERSEDED trong `architecture/ARCHIVE.md`, không xóa (luật INVALIDATED không xóa); `tools/validate.py` từ chối bất kỳ `ARCHITECTURE_v*.md` nào không có trong danh sách đó. Từ đây chỉ một tệp kiến trúc có hiệu lực; thay đổi đi qua ADR (`architecture/adr/`), mỗi ADR có điều kiện hoàn tác (L-07).

> KHÔNG XÂY AI ĐOÁN THỊ TRƯỜNG. XÂY MỘT HỆ THỐNG biết thu thập bằng chứng, biết nghi ngờ chính nó, biết đo lường độ không chắc chắn, biết quản trị rủi ro, biết học từ kết quả, và biết cải thiện cách nó học.

---

## 0. Điều gì đổi so với v2.2, và vì sao

Rà soát 21–22/10/2026 (bản hiểu tại commit `3c9f69d` + nghiên cứu bằng chứng) kết luận: kiến trúc vượt xa vận hành (6 bản trong một ngày, 0 dự báo, thư viện rỗng); engine định lượng chạy đúng và trung thực báo "không tìm thấy gì"; thứ quyết định kết quả đầu tư theo bằng chứng là kỷ luật, chi phí và kế toán, không phải dự báo vĩ mô. v3.0 làm ba việc: gộp thành một bản; mở đường ghi dự báo không cần API; đặt tầng học hiểu vào Thư viện/Học viện (khuôn học có gốc từ MINH TRÍ; ghế làm việc không phải MINH TRÍ — ADR-0003, ADR-0010) với miền hẹp đầu tiên là kế toán ngân hàng.

## 1. Ba tinh hoa giữ nguyên, hai tinh hoa thêm

Giữ (từ v1.0–v2.2): (1) mọi nhận định có ảnh hưởng phải thành dự báo chấm được; (2) mọi tri thức có địa chỉ nguồn, trích nguyên văn, máy kiểm, thang OBSERVATION→UNVERIFIED→WEAK→SUPPORTED→STRONG, INVALIDATED không xóa; (3) lợi thế = khác biệt đã được chứng minh so với nhóm đối chứng B (Claude trần không thư viện); chỉ số chính là **độ đúng của A khi bất đồng với B**.
Thêm (từ nghiên cứu 2025–2026): (4) **thời điểm**: mọi kiểm định LLM chỉ dùng câu hỏi giải sau ngày cắt dữ liệu của mô hình và được ghi trước ngày giải; cấm backtest bằng LLM (L-05); (5) **sổ thử**: mọi lần thử chiến lược hay giả thuyết được đăng ký trước, ngưỡng ý nghĩa tính theo tổng số lần thử, bổ sung Deflated Sharpe (L-06).

## 2. Kiến trúc tổng thể: ba nửa, một sổ

```text
                 OWNER (ký MISSION, gộp main, ba cổng tay người)
                                   │
        ┌──────────────────────────┼──────────────────────────┐
   NỬA CHỨNG MINH            NỬA HỌC                     NỬA QUẢN TRỊ
   Prediction Ledger         Thư viện 4 tầng               governance/
   Nhóm đối chứng B          Học viện (đề kín, sổ điểm)    LAWS.md, GATES, SAFETY_STATE
   Engine định lượng         Cỗ máy học hiểu (ghế thi công) DATA_SOURCES, FIREWALL
   (đối chứng âm)            KNOWLEDGE_NOTE → mệnh đề       ADR
        └──────────────────────────┼──────────────────────────┘
                                   ▼
                          SỔ DUY NHẤT = GitHub main
```

- Nửa CHỨNG MINH trả lời "tổ chức có giỏi hơn Claude trần không". Nửa HỌC tạo tri thức có địa chỉ để nửa CHỨNG MINH đo. Nửa QUẢN TRỊ giữ ranh giới tiền, pháp lý, dữ liệu cá nhân.
- Không có Orchestrator trong 6 tháng đầu: Owner + GitHub Actions + ghế thi công theo lệnh là đủ.

## 3. Vai và kênh

| Ghế | Vai | Không được |
|---|---|---|
| Owner | ký OWNER_MISSION, gộp `main`, đổi luật/phạm vi, giữ danh mục thật ngoài kho | commit số liệu cá nhân |
| Claude (kiến trúc sư trưởng) | thiết kế, soạn lệnh, chấm PR, ra và giữ đề thi, chấm thi | tự gộp, tự ghi kho, là phản biện độc lập cho thiết kế của mình |
| Ghế thi công — Grok (xAI), Owner lập 18/11/2026 (ADR-0010; **không phải MINH TRÍ**) | chép nguồn, viết ghi chú, mệnh đề, mã công cụ theo đặc tả, mở PR nháp | merge, sửa luật, mở API, chạm engine ngoài lệnh |
| Nhóm B | Claude trần, phiên mới không dự án không tệp, prompt cố định có hash | thấy thư viện hay câu trả lời của A |
| CI | kiểm schema, địa chỉ, trích nguyên văn, dấu thời gian Ledger, test | — |

Kênh, ba lớp đã có, không đặt lớp mới (ADR-0010 quyết định 6): lệnh vẫn là Gmail `[TTC] #N — …` (kết `Dừng.`) → `BAO CAO [TTC] #N` như `governance/ARCHITECT_HANDOFF_20261022.md` mục 2, Owner chưa thu hồi. Đưa tệp lên `main` là PR + L-09 + Owner bấm Merge (ADR-0003 quyết định 6). Tên nhánh `hoc-hieu` trong thiết kế v0.2 mục 9 là mặc định Claude chọn, chưa phải lệnh Owner. Tệp cho Claude: kho công khai đọc thẳng, hoặc ZIP nhánh.

ChatGPT (OpenAI) có thể soạn chữ một PR khi được giao. Đó là người viết, không phải ghế thi công và không có quyền trên Owner. Ghế thi công là Grok (xAI) theo ADR-0010 quyết định 1. Phản biện độc lập phải là nhà cung cấp khác người viết (L-09). Không lập ghế nào đứng trên Owner (ADR-0013).

## 4. Nửa CHỨNG MINH

### 4.1 Prediction Ledger không cần API
1. Ghế chat (A) xuất mỗi dự báo thành khối YAML theo `contracts/prediction.schema.json` mở rộng: `id, question, resolution_source, resolution_rule, resolve_at, p (0.05–0.95), base_rate, invalidation_conditions, author_seat, library_refs`.
2. Owner dán vào GitHub Issue mẫu **Forecast**; trường `seat` = `A` hoặc `B`. Chỉ Issue do Owner mở, nhận lúc mở; mỗi ghế một dự báo cho một câu hỏi; ghế B kèm `prompt_hash` của prompt chuẩn (ADR-0003).
3. GitHub Actions kiểm schema, chép vào `ledger/predictions.jsonl` kèm `issue_created_at` (giờ máy chủ GitHub), `sha256` của nội dung và hash chuỗi (mỗi dòng chứa hash dòng trước). Dự báo mới phải khai `info_lock_at` — ngày thông tin phân định có thể được công bố — trùng ngày của một lịch công bố `calendar_id` do robot ghim từ Issue `[Calendar]` mở trước Issue dự báo, và bị loại nếu ghi từ ngày đó trở đi, hoặc nếu câu hỏi đã có bằng chứng công bố, dù chưa tới `resolve_at` (ADR-0011). Dự báo thiếu nguồn giải quyết hoặc ghi sau `resolve_at` bị loại tự động; câu hỏi đã có kết quả trong sổ thì không nhận thêm dự báo. Workflow đăng hash của dòng vừa ghi thành bình luận của `github-actions[bot]` trên Issue (dấu nhận); CI đối chiếu từng dòng sổ với dấu nhận đó và chạy lại luật nhận trên mọi dòng (ADR-0003 mục 7). F-37–F-42 ghi trước hạn khóa, giữ nguyên, và không đưa vào phép kiểm định hợp lệ khi chưa chứng minh được giờ ghi đứng trước lúc công bố.
4. Phân định (ADR-0003): tới `resolve_at`, Owner hoặc ghế khác nhà cung cấp đọc nguồn và mở Issue mẫu **Resolution** (mã dự báo, YES/NO/VOID, nguồn, trích nguyên văn, người phân định); `resolution_intake.yml` kiểm (đúng hạn, một câu hỏi một sự thật, không phân định lại, người phân định khác ghế với mọi người viết, mọi đường dẫn nguồn có máy chủ thuộc tên miền đã hứa) và ghi `ledger/resolutions.jsonl`; một Issue phân định chỉ ghi kết quả cho dự báo mở trước nó; VOID (hủy câu hỏi) cũng chỉ ghi được khi tới hạn. Sổ chỉ nhận dòng từ Issue: đường để engine tự ghi và tự chấm dự báo giá (`excess_return_positive`, mã `P-…`) đóng cho tới khi có ADR kèm cơ chế bằng chứng xuất xứ (ADR-0003 quyết định 11).
5. Scorecard theo ghế: Brier, hiệu chuẩn theo nhóm, n; **tập bất đồng A–B** và độ đúng của A trên tập đó; tỷ lệ bất đồng (dưới 10% nghĩa là bộ máy TTC chưa khác Claude trần; không đo riêng Thư viện — ADR-0002, ADR-0013).

### 4.2 Nhóm đối chứng B
Cùng ngày, cùng câu hỏi; phiên Claude mới không dự án, không tệp; prompt chuẩn trong `governance/CONTROL_B_PROMPT.md` (có hash, đổi phải qua ADR; các phiên bản đã có hiệu lực ghim theo ngày trong `governance/control_b_prompts.jsonl`). Mục tiêu cỡ mẫu: ~194 bất đồng đã chấm để phát hiện A đúng 60% so với 50% (độ mạnh 80%, α 0,05 hai phía; phán quyết chốt trên đúng 194 cặp bất đồng đầu tiên theo số Issue hoàn tất cặp, chỉ ra khi cả 194 cặp đã phân định hoặc VOID, không xem lại trên mẫu lớn dần; cặp VOID tính theo hướng bất lợi cho kết luận đang xét — ADR-0003 quyết định 3, ADR-0004; câu hỏi `event_before_date` không vào phép thử vì ghế A được tìm web — ADR-0002); với tỷ lệ bất đồng ~25% cần ~800 câu, nên câu hỏi phải nhỏ, giải nhanh (tháng/quý), lấy từ BCTC và dữ liệu NHNN.

Phép thử đang chạy đo cả bộ TTC so với Claude trần, không đo riêng Thư viện: ghế A là Claude trong Project (quy trình, tìm web, và thư viện khi có); ghế B là Claude trần (ADR-0002, ADR-0013). Báo cáo sau này được phép đếm thêm một lớp theo `library_refs` của dòng ghế A (có dẫn thư viện hay không). Không có trường đó thì ghi "không khai mức dùng thư viện"; không được suy mức dùng thư viện từ tên ghế. Lớp đếm này không đổi mẫu 194 cặp trong `engine/ledger.py`.

Báo cáo tương lai tách hai lớp ghế B: câu trả lời của ghế B, và phần biểu mẫu do người khác hoàn thiện khi dán Issue. Không viết lại Ledger. F-38, F-40 và F-42 đã có câu trong `invalidation_conditions`: phần hoàn thiện biểu mẫu theo lệnh G0 của Owner, không phải lời trả lời nguyên văn của ghế B. Báo cáo dẫn câu đó.

### 4.3 Engine định lượng = đối chứng âm
Giữ nguyên mã; chạy hằng tuần thay vì hằng ngày (thứ Sáu, từ v3.0.2); đóng băng không gian giả thuyết (13 feature × 3 mô hình × VN30); thêm Deflated Sharpe và sổ đăng ký thử `research/trial_registry.jsonl` (đã làm v3.0.2: mỗi lần thử đăng ký có hash chuỗi và được đẩy lên `main` trước khi chạy, lần thử bỏ dở vẫn được đếm, kết quả chỉ-ghi-thêm có neo lịch sử, CI đối chiếu); giả thuyết mới chỉ chạy khi đã đăng ký trước. Kho dữ liệu đổi sang ghi tăng dần (append) để git không phình (C2 — đã làm, ADR-0006: kho cũ đóng băng, dòng mới nối vào tệp tháng, kiểm toán bắt mọi lần viết lại). Benchmark ghi rõ là "bình quân đều VN30 hiện tại", không gọi là VN-Index (C6).
ADR-0008: báo cáo gắn nhãn thiên lệch sống sót khi danh sách là VN30 hiện tại; giấy không khớp ở phiên khóa trần/sàn; báo cáo có sụt giảm lớn nhất (backtest và NAV giấy).
ADR-0009: bản giá dẫn xuất có phiên bản, nguồn gốc và cách hoàn tác; không sửa kho giá gốc của ADR-0006. Điều 7 chưa cho đổi `engine/adjust.py`, `data.sources`, và chưa bật SSI/DNSE.

## 5. Nửa HỌC (Thư viện + Học viện) — ghế thi công, không phải MINH TRÍ

Chi tiết ở `docs/TTC_TANG_HOC_HIEU_v0.2.md`; tóm tắt luật:
- Nguồn: chỉ tài liệu gốc công khai, ghim sha256 + ngày phát hành + ngày truy cập + trạng thái pháp lý + **trạng thái hiệu lực** (`effective_from`, `superseded_by`) (L-01, L-08). Mọi dòng manifest phải ghim riêng `original_sha256`, `original_bytes`, `original_path` của tệp gốc và `text_sha256`, `text_bytes` của `text.md`; bỏ các trường đó không còn là đường vòng. `SOURCED` và ghi chú `CITED` cần hash cả trang (gồm bảng) cộng `pdf_check` của một ghế đã đối chiếu PDF; hash tự sinh từ `text.md` không đủ (ADR-0012). Luật Kế toán 88/2015 vẫn `QUEUED` cho tới khi bản gốc và bản chép đạt kiểm tra. BCTC thêm `period_end` và `published_on` — số liệu chỉ dùng từ ngày công bố (ADR-0008, `knowledge_notes.usable_on`). Thứ cấp chỉ là CROSS_TEXT_SYNTHESIS.
- Địa chỉ: `<doc_id>:p<trang>:<đoạn>` / `<doc_id>:t<bảng>:<dòng>`; trích nguyên văn máy kiểm.
- Đơn vị: KNOWLEDGE_NOTE (`contracts/knowledge_note.schema.json`) với `not_said ≥ 2`, `testable_implications`, `self_check`; DRAFT không dùng cho mệnh đề hay quyết định.
- Mệnh đề = `knowledge_item` + `hypothesis.invalidation_conditions`; mỗi mệnh đề có `chain`, `supports ≥ 3`, hạn hiệu lực; trần 60 đang dùng; thay thế bằng `supersedes`.
- Học viện: đề kín do Claude ra và giữ ngoài kho tới khi thi; A trả lời chỉ bằng ghi chú ≥ CITED; B trả lời trần; sổ điểm theo mắt xích; phán quyết HELPED/HURT/UNUSED cho mệnh đề; `competency_map` chỉ do mã nâng.
- Miền hẹp đầu tiên: kế toán và BCTC ngân hàng VN30 (Luật Kế toán 2015, **TT 99/2025** thay TT 200 từ 01/01/2026, VAS, chế độ kế toán TCTD), Luật CK 2019 + Luật 56/2024, NĐ 155/2020 + **NĐ 245/2025**, TT 96/2020, văn bản NHNN hiện hành về phân loại nợ và an toàn vốn (kiểm hiệu lực TT 41/2016), BCTC kiểm toán 10 ngân hàng VN30. Thứ tự học: kỷ luật và chi phí → kế toán → thống kê → luật thị trường → định giá và ngành → vĩ mô truyền dẫn → địa chính trị ở mức bản đồ phơi nhiễm.

## 6. Nửa QUẢN TRỊ

- `governance/LAWS.md` (L-01…L-10) là luật vận hành; `GATES.md`, `SAFETY_STATE.yaml`, thang vốn 0–6 giữ nguyên; mọi công tắc tiền/API vẫn `false`.
- Kho công khai: không commit vốn thật, mức lỗ chịu được, nhu cầu rút tiền, vị thế thật, định danh (L-03). OWNER_MISSION chỉ ghi phạm vi, khung thời gian, nguyên tắc.
- Không khuyến nghị mua/bán mã cụ thể; chỉ dự báo xác suất về sự kiện và chỉ tiêu (L-02). Media OS: “sau sáu tháng” là mốc xem xét, không phải cam kết đạt 194 bất đồng. Chỉ cân nhắc mở sau ý kiến luật sư và khi Ledger có ≥ 194 bất đồng đã chấm. PR này không sửa `governance/SAFETY_STATE.yaml`.
- Firewall Media/Investment giữ như v1.0, và `tools/validate.py` phải kiểm thật (B6).

## 7. Runtime và chi phí

| Việc | Chạy ở đâu | Chi phí |
|---|---|---|
| Engine, Ledger, Actions kiểm Issue, validate | GitHub Actions (kho công khai: miễn phí) | 0 |
| Ghi chú, mệnh đề, mã công cụ | Ghế thi công: lệnh theo handoff mục 2 (Gmail), lên `main` bằng PR | gói thuê bao |
| Thiết kế, chấm, ra đề | Claude trong Project (gói Max) | gói thuê bao |
| Nhóm B | Phiên Claude trần | gói thuê bao |
| API trả phí | **không mở** cho tới mốc xem xét sau 6 tháng | 0 |

## 8. Lộ trình có điều kiện thoát

| GĐ | Sản phẩm | Thoát khi | Dừng/đảo khi |
|---|---|---|---|
| G0 (tuần 1–2) | v3.0 gộp; LAWS; mẫu Issue Forecast; Action kiểm + đóng dấu; handoff; 3 hợp đồng học | Action xanh trên 3 dự báo thử; 1 tệp kiến trúc | quá 3 tuần → chỉ giữ Ledger |
| G1 (tháng 1–2) | ≥ 40 tài liệu gốc có hash; ≥ 60 dự báo A+B | tỷ lệ bất đồng đo được; 100% dự báo có nguồn giải quyết | < 20 dự báo/tháng → hạ độ khó câu hỏi |
| G2 (tháng 2–4) | mệnh đề kế toán ngân hàng; đề kín ≥ 150 câu; sổ điểm | A ≥ 80% đề kín với trích dẫn kiểm được; ≥ 30 dự báo chỉ tiêu BCTC quý | trích dẫn sai > 5% → sửa retrieval theo từng tài liệu |
| G3 (tháng 4–6) | thống kê, vĩ mô truyền dẫn, luật thị trường; DSR vào engine | ≥ 150 dự báo đã chấm; báo cáo hiệu chuẩn đầu tiên | Brier A tệ hơn B có ý nghĩa → kiểm lại thư viện |
| G4 (mốc xem xét sau 6 tháng, không phải hạn phải đủ 194) | báo cáo đánh giá | chỉ cân nhắc API/Media khi đã tới mốc xem xét và Ledger có ≥ 194 bất đồng đã chấm; 194 là điều kiện cân nhắc, không phải sản lượng cam kết | chưa đủ 194 tại mốc không tự động là thất bại của mốc |

G0 đã đạt điều kiện kỹ thuật ngày 18/11/2026, chưa phải G1. Sổ có sáu dự báo F-37–F-42, ba cặp A/B (CPI, IIP, bán lẻ), mỗi cặp cùng câu hỏi và cùng ngày theo giờ Việt Nam; cả sáu có dấu nhận robot khớp hash. `state/PROJECT_STATE.yaml` ghi `V3_G0_DAT_DIEU_KIEN_KY_THUAT`. Thư viện vẫn 0/40. Việc này không hủy cột dừng/đảo (“quá 3 tuần → chỉ giữ Ledger”): cột đó đã quá hạn nếu tính từ 22/10/2026 hoặc từ ngày gộp 24/10/2026. Không có biên bản Owner bác riêng nhánh đó vào ngày 17/11/2026. Việc đang lưu vẫn là ADR-0002 (PR #29): không thu hẹp v3.0 theo điều kiện hoàn tác của ADR-0001; mốc xét lại 31/03/2027. Đó không phải bằng chứng trực tiếp về cột 3 tuần. Hai đồng hồ không phải một luật. Ghi nhận điều kiện kỹ thuật của G0 không dừng đồng hồ 3 tuần và không dời mốc 31/03/2027. Quyết định 2 của ADR-0010 giữ nguyên chữ đã chấm, kể cả câu pha cũ trong quyết định đó; pha hiện tại đọc ở `PROJECT_STATE.yaml` và ở đoạn này (ADR-0013). Dời mốc 31/03/2027 phải bằng ADR mới, không bằng sửa ngày trong ADR-0002.

Không có trong lộ trình: tiền thật; cấp vốn 4+ chỉ xét khi G3 cho alpha có ý nghĩa và Owner quyết.

## 9. Chế độ hỏng và phòng thủ (bổ sung v1.0 IX)

| Hỏng | Phòng |
|---|---|
| Kiến trúc chạy trước vận hành | L-07: không bản mới khi bản cũ chưa chạy ≥ 30 ngày; ADR có điều kiện hoàn tác |
| Ledger không có dự báo | đường Issue thủ công; mục tiêu 10–15 dự báo/tuần |
| A và B cùng mô hình nền nên sai số tương quan, tập bất đồng nhỏ | theo dõi tỷ lệ bất đồng; dưới 10% → đổi B sang nhà cung cấp khác |
| LLM nhớ dữ liệu (look-ahead) | L-05 |
| Tri thức pháp lý hết hạn | L-08: trạng thái hiệu lực, kiểm mỗi quý |
| Kho công khai lộ dữ liệu cá nhân | L-03 |
| Chạm quy định tư vấn đầu tư | L-02; Media OS hoãn; luật sư trước khi bật |
| Overfitting backtest | L-06; DSR; sổ thử |

## 10. Đối chiếu bản cũ → v3.0

| Bản cũ | Số phận trong v3.0 |
|---|---|
| v0.1 32 mục, v0.2 engine | Engine giữ làm đối chứng âm; 32 mục được bao bởi §2–§6 |
| v1.0 Prediction Ledger, Scorecard, nhóm B, ba vòng học, walking skeleton | Giữ nguyên tinh thần; Ledger có đường thủ công; nhóm B hiện thực ở §4.2; ba vòng học chạy qua Học viện |
| v2.0 Thư viện 4 tầng, Học viện, Phòng thi, KNOWLEDGE_NOTE, Hỏi chuyên gia | Thư viện/Học viện/Phòng thi giữ, hiện thực bằng ghế thi công theo khuôn học (không phải MINH TRÍ); "Hỏi chuyên gia nhập vai" hoãn tới G4 |
| v2.1 ba tốc độ, blind-spot, influence, chính trị–địa chính trị, sân chơi ảo | Địa chính trị và chính sách giữ ở mức bản đồ phơi nhiễm và luật thị trường; làn nhanh 15–30 phút, influence, blind-spot hoãn tới G4 |
| v2.2 tinh hoa, chuỗi giá trị hai đầu, quan sát thực địa | Tinh hoa và thước đo A–B giữ làm trục; chuỗi giá trị và quan sát Owner vào Thư viện tầng 3 khi có dossier |
