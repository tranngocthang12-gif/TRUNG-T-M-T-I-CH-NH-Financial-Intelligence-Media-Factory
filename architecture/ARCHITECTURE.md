# TRUNG TÂM TÀI CHÍNH — ARCHITECTURE v3.0 (bản hợp nhất, duy nhất có hiệu lực)

Ngày: 22/10/2026 · Kiến trúc sư trưởng: Claude · Owner: Trần Ngọc Thắng · Trạng thái: DRAFT chờ Owner gộp. Do Claude soạn một mình theo lệnh Owner 22/10/2026 (giai đoạn xây kiến trúc); chưa có phản biện độc lập — xem `governance/ARCHITECT_HANDOFF_20261022.md` mục 4.
Bản này **thay thế** v0.1, v0.2, v1.0, v2.0, v2.1, v2.2. Các bản cũ giữ nguyên chỗ nhưng được liệt kê là SUPERSEDED trong `architecture/ARCHIVE.md`, không xóa (luật INVALIDATED không xóa); `tools/validate.py` từ chối bất kỳ `ARCHITECTURE_v*.md` nào không có trong danh sách đó. Từ đây chỉ một tệp kiến trúc có hiệu lực; thay đổi đi qua ADR (`architecture/adr/`), mỗi ADR có điều kiện hoàn tác (L-07).

> KHÔNG XÂY AI ĐOÁN THỊ TRƯỜNG. XÂY MỘT HỆ THỐNG biết thu thập bằng chứng, biết nghi ngờ chính nó, biết đo lường độ không chắc chắn, biết quản trị rủi ro, biết học từ kết quả, và biết cải thiện cách nó học.

---

## 0. Điều gì đổi so với v2.2, và vì sao

Rà soát 21–22/10/2026 (bản hiểu tại commit `3c9f69d` + nghiên cứu bằng chứng) kết luận: kiến trúc vượt xa vận hành (6 bản trong một ngày, 0 dự báo, thư viện rỗng); engine định lượng chạy đúng và trung thực báo "không tìm thấy gì"; thứ quyết định kết quả đầu tư theo bằng chứng là kỷ luật, chi phí và kế toán, không phải dự báo vĩ mô. v3.0 làm ba việc: gộp thành một bản; mở đường ghi dự báo không cần API; đặt tầng học hiểu (cỗ máy MINH TRÍ) vào Thư viện/Học viện với miền hẹp đầu tiên là kế toán ngân hàng.

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
   Engine định lượng         Cỗ máy học hiểu (từ MINH TRÍ)  DATA_SOURCES, FIREWALL
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
| Ghế thi công (ChatGPT, "MINH TRÍ") | chép nguồn, viết ghi chú, mệnh đề, mã công cụ theo đặc tả, mở PR nháp | merge, sửa luật, mở API, chạm engine ngoài lệnh |
| Nhóm B | Claude trần, phiên mới không dự án không tệp, prompt cố định có hash | thấy thư viện hay câu trả lời của A |
| CI | kiểm schema, địa chỉ, trích nguyên văn, dấu thời gian Ledger, test | — |

Kênh lệnh: Gmail `[TTC] #N — …` (kết `Dừng.`) → `BAO CAO #N`. Tệp cho Claude: kho công khai đọc thẳng, hoặc ZIP nhánh.

## 4. Nửa CHỨNG MINH

### 4.1 Prediction Ledger không cần API
1. Ghế chat (A) xuất mỗi dự báo thành khối YAML theo `contracts/prediction.schema.json` mở rộng: `id, question, resolution_source, resolution_rule, resolve_at, p (0.05–0.95), base_rate, invalidation_conditions, author_seat, library_refs`.
2. Owner dán vào GitHub Issue mẫu **Forecast**; nhãn `A` hoặc `B`.
3. GitHub Actions kiểm schema, chép vào `ledger/predictions.jsonl` kèm `issue_created_at` (giờ máy chủ GitHub), `sha256` của nội dung và hash chuỗi (mỗi dòng chứa hash dòng trước). Dự báo thiếu nguồn giải quyết hoặc ghi sau `resolve_at` bị loại tự động.
4. Chấm: `engine/ledger.py` mở rộng luật chấm ngoài `excess_return_positive`: `numeric_range` (chỉ tiêu BCTC/NHNN trong khoảng), `event_before_date`, `comparison` (quý này so quý trước). Người chấm khác nhà với người viết; kết quả `ledger/resolutions.jsonl`.
5. Scorecard theo ghế: Brier, hiệu chuẩn theo nhóm, n; **tập bất đồng A–B** và độ đúng của A trên tập đó; tỷ lệ bất đồng (dưới 10% nghĩa là thư viện chưa đổi gì).

### 4.2 Nhóm đối chứng B
Cùng ngày, cùng câu hỏi; phiên Claude mới không dự án, không tệp; prompt chuẩn trong `governance/CONTROL_B_PROMPT.md` (có hash, đổi phải qua ADR). Mục tiêu cỡ mẫu: ~194 bất đồng đã chấm để phát hiện A đúng 60% so với 50% (độ mạnh 80%, α 0,05); với tỷ lệ bất đồng ~25% cần ~800 câu, nên câu hỏi phải nhỏ, giải nhanh (tháng/quý), lấy từ BCTC và dữ liệu NHNN.

### 4.3 Engine định lượng = đối chứng âm
Giữ nguyên mã; chạy hằng tuần thay vì hằng ngày; đóng băng không gian giả thuyết (13 feature × 3 mô hình × VN30); thêm Deflated Sharpe và sổ đăng ký thử `research/trial_registry.jsonl`; giả thuyết mới chỉ chạy khi đã đăng ký trước. Kho dữ liệu đổi sang ghi tăng dần (append) để git không phình (C2). Benchmark ghi rõ là "bình quân đều VN30 hiện tại", không gọi là VN-Index (C6).

## 5. Nửa HỌC (Thư viện + Học viện) — cỗ máy học hiểu từ MINH TRÍ

Chi tiết ở `docs/TTC_TANG_HOC_HIEU_v0.2_20261022.md`; tóm tắt luật:
- Nguồn: chỉ tài liệu gốc công khai, ghim sha256 + ngày phát hành + ngày truy cập + trạng thái pháp lý + **trạng thái hiệu lực** (`effective_from`, `superseded_by`) (L-01, L-08). Thứ cấp chỉ là CROSS_TEXT_SYNTHESIS.
- Địa chỉ: `<doc_id>:p<trang>:<đoạn>` / `<doc_id>:t<bảng>:<dòng>`; trích nguyên văn máy kiểm.
- Đơn vị: KNOWLEDGE_NOTE (`contracts/knowledge_note.schema.json`) với `not_said ≥ 2`, `testable_implications`, `self_check`; DRAFT không dùng cho mệnh đề hay quyết định.
- Mệnh đề = `knowledge_item` + `hypothesis.invalidation_conditions`; mỗi mệnh đề có `chain`, `supports ≥ 3`, hạn hiệu lực; trần 60 đang dùng; thay thế bằng `supersedes`.
- Học viện: đề kín do Claude ra và giữ ngoài kho tới khi thi; A trả lời chỉ bằng ghi chú ≥ CITED; B trả lời trần; sổ điểm theo mắt xích; phán quyết HELPED/HURT/UNUSED cho mệnh đề; `competency_map` chỉ do mã nâng.
- Miền hẹp đầu tiên: kế toán và BCTC ngân hàng VN30 (Luật Kế toán 2015, **TT 99/2025** thay TT 200 từ 01/01/2026, VAS, chế độ kế toán TCTD), Luật CK 2019 + Luật 56/2024, NĐ 155/2020 + **NĐ 245/2025**, TT 96/2020, văn bản NHNN hiện hành về phân loại nợ và an toàn vốn (kiểm hiệu lực TT 41/2016), BCTC kiểm toán 10 ngân hàng VN30. Thứ tự học: kỷ luật và chi phí → kế toán → thống kê → luật thị trường → định giá và ngành → vĩ mô truyền dẫn → địa chính trị ở mức bản đồ phơi nhiễm.

## 6. Nửa QUẢN TRỊ

- `governance/LAWS.md` (L-01…L-10) là luật vận hành; `GATES.md`, `SAFETY_STATE.yaml`, thang vốn 0–6 giữ nguyên; mọi công tắc tiền/API vẫn `false`.
- Kho công khai: không commit vốn thật, mức lỗ chịu được, nhu cầu rút tiền, vị thế thật, định danh (L-03). OWNER_MISSION chỉ ghi phạm vi, khung thời gian, nguyên tắc.
- Không khuyến nghị mua/bán mã cụ thể; chỉ dự báo xác suất về sự kiện và chỉ tiêu (L-02). Media OS hoãn ≥ 6 tháng, chỉ mở sau ý kiến luật sư và khi Ledger có ≥ 194 bất đồng đã chấm.
- Firewall Media/Investment giữ như v1.0, và `tools/validate.py` phải kiểm thật (B6).

## 7. Runtime và chi phí

| Việc | Chạy ở đâu | Chi phí |
|---|---|---|
| Engine, Ledger, Actions kiểm Issue, validate | GitHub Actions (kho công khai: miễn phí) | 0 |
| Ghi chú, mệnh đề, mã công cụ | Ghế thi công theo lịch Gmail + PR | gói thuê bao |
| Thiết kế, chấm, ra đề | Claude trong Project (gói Max) | gói thuê bao |
| Nhóm B | Phiên Claude trần | gói thuê bao |
| API trả phí | **không mở** trong 6 tháng | 0 |

## 8. Lộ trình có điều kiện thoát

| GĐ | Sản phẩm | Thoát khi | Dừng/đảo khi |
|---|---|---|---|
| G0 (tuần 1–2) | v3.0 gộp; LAWS; mẫu Issue Forecast; Action kiểm + đóng dấu; handoff; 3 hợp đồng học | Action xanh trên 3 dự báo thử; 1 tệp kiến trúc | quá 3 tuần → chỉ giữ Ledger |
| G1 (tháng 1–2) | ≥ 40 tài liệu gốc có hash; ≥ 60 dự báo A+B | tỷ lệ bất đồng đo được; 100% dự báo có nguồn giải quyết | < 20 dự báo/tháng → hạ độ khó câu hỏi |
| G2 (tháng 2–4) | mệnh đề kế toán ngân hàng; đề kín ≥ 150 câu; sổ điểm | A ≥ 80% đề kín với trích dẫn kiểm được; ≥ 30 dự báo chỉ tiêu BCTC quý | trích dẫn sai > 5% → sửa retrieval theo từng tài liệu |
| G3 (tháng 4–6) | thống kê, vĩ mô truyền dẫn, luật thị trường; DSR vào engine | ≥ 150 dự báo đã chấm; báo cáo hiệu chuẩn đầu tiên | Brier A tệ hơn B có ý nghĩa → kiểm lại thư viện |
| G4 (sau 6 tháng) | báo cáo đánh giá | chỉ cân nhắc API/Media khi ≥ 194 bất đồng đã chấm | — |

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
| v2.0 Thư viện 4 tầng, Học viện, Phòng thi, KNOWLEDGE_NOTE, Hỏi chuyên gia | Thư viện/Học viện/Phòng thi giữ, hiện thực bằng cỗ máy MINH TRÍ; "Hỏi chuyên gia nhập vai" hoãn tới G4 |
| v2.1 ba tốc độ, blind-spot, influence, chính trị–địa chính trị, sân chơi ảo | Địa chính trị và chính sách giữ ở mức bản đồ phơi nhiễm và luật thị trường; làn nhanh 15–30 phút, influence, blind-spot hoãn tới G4 |
| v2.2 tinh hoa, chuỗi giá trị hai đầu, quan sát thực địa | Tinh hoa và thước đo A–B giữ làm trục; chuỗi giá trị và quan sát Owner vào Thư viện tầng 3 khi có dossier |
