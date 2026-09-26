# NHÀ MÁY TRÍ TUỆ TÀI CHÍNH
## FINANCIAL INTELLIGENCE & MEDIA FACTORY — ARCHITECTURE v2.0

**Kiến trúc sư trưởng:** Claude · **Owner:** Trần Ngọc Thắng · **Ngày:** 26/09/2026
**Thay thế:** v1.0 (giữ toàn bộ phần "Chứng minh"), bổ sung toàn bộ phần "Học".
**Khi mâu thuẫn giữa các phiên bản: theo v2.0.**

> KHÔNG XÂY AI ĐOÁN THỊ TRƯỜNG.
> XÂY MỘT HỆ THỐNG biết thu thập bằng chứng, biết nghi ngờ chính nó, biết đo lường độ không chắc chắn,
> biết quản trị rủi ro, biết học từ kết quả, và biết cải thiện cách nó học.

---

# PHẦN 0 — Ý TƯỞNG CỦA OWNER, VIẾT LẠI THÀNH KIẾN TRÚC

Owner đã làm dự án Phật học: bộ não trên GitHub chứa Kinh Trung Bộ, AI học hiểu toàn bộ kinh, rồi **nhập vai** trả lời bằng ngôn ngữ đời sống nhưng giữ đúng ý kinh.

Dự án tài chính đi cùng con đường đó, cộng thêm một bước mà Phật học không cần:

```text
   NGƯỜI GIỎI TOÁN                         BỘ NÃO TÀI CHÍNH
   ───────────────                         ────────────────
   1. Học giáo trình                  →    1. HỌC: Thư viện chuyên môn (nền tảng + Việt Nam
                                              + hồ sơ doanh nghiệp + thủ đoạn thị trường)
   2. Làm bài tập, đi thi             →    2. THI: bộ đề có đáp án do máy chấm, ca mù lịch sử
   3. Giải bài toán thật ngoài đời    →    3. HÀNH: phân tích, dự báo, cảnh báo trên thị trường thật
   4. Được đánh giá bằng kết quả      →    4. CHỨNG MINH: Prediction Ledger chấm bằng kết quả thật
   5. Rút kinh nghiệm, học tiếp       →    5. HỌC LẠI: bài học kiểm chứng quay về Thư viện
```

| | Dự án Phật học | Dự án Tài chính |
|---|---|---|
| Nguồn chân lý | Bản kinh | **Kết quả thị trường** |
| Kho kiến thức | Cố định | Nền cố định + dữ liệu đổi hằng ngày |
| "Hiểu đúng" nghĩa là | Diễn giải trung thành với kinh | Diễn giải trung thành với bằng chứng **và** dự báo đúng |
| Nhập vai | Như Đức Phật | Như **chuyên gia tài chính hàng đầu Việt Nam** |

v1.0 đã xây nửa **Chứng minh** (bước 3–4). v2.0 xây nửa **Học** (bước 1, 2, 5) và **Nhập vai** — hai nửa hợp thành một bộ não hoàn chỉnh.

---

# PHẦN I — RÀ SOÁT: v1.0 CÒN THIẾU GÌ

| # | Thiếu | Hệ quả | v2.0 bổ sung |
|---|---|---|---|
| 1 | Không có **kho kiến thức chuyên môn** — chuyên gia chỉ dựa vào trí nhớ chung của Claude | Không khác gì AI thông thường; không có lợi thế Việt Nam | **Thư viện Chuyên môn 4 tầng** (Phần III) |
| 2 | Không có **chương trình học** — "AUTO HỌC" chưa biết học cái gì, theo thứ tự nào | Học dàn trải, không đo được tiến bộ | **Học viện: bản đồ năng lực + giáo trình** (Phần IV) |
| 3 | Không có **kỳ thi** trước khi ra trận | Chuyên gia chưa chứng minh năng lực đã được dự báo thật; phải chờ hàng tháng mới biết giỏi hay dở | **Phòng thi: đề máy chấm + ca mù lịch sử** (Phần V) |
| 4 | Không có **chế độ nhập vai hỏi đáp** | Owner không "hỏi chuyện" được bộ não như dự án Phật học | **Chế độ Chuyên gia Nhập vai** (Phần VI) |
| 5 | Không có **hồ sơ doanh nghiệp** tích lũy | Mỗi lần phân tích lại từ đầu | **Hồ sơ sống cho từng mã** (Tầng 3) |
| 6 | Không có kiến thức về **thủ đoạn thị trường** | Dễ bị dẫn dắt bởi tin đồn, làm giá, BCTC đẹp giả | **Hồ sơ Thủ đoạn** có dấu hiệu nhận biết (Tầng 2) |
| 7 | Học tốn tiền API | Hạn chế khối lượng học | **Học bằng gói Max, thi hành bằng Actions** (Phần VIII) |

Mọi thành phần v1.0 **giữ nguyên**: Governor, Orchestrator, Fact Layer, Firewall, Prediction Ledger, Scorecard, nhóm đối chứng, ba vòng học, engine định lượng, Budget Governor.

---

# PHẦN II — KIẾN TRÚC TỔNG THỂ v2.0

```text
                                 HUMAN OWNER
                                      │
                             FINANCIAL GOVERNOR
                  (vốn · rủi ro · ngân sách · pháp lý · an toàn)
                                      │
                          INTELLIGENCE ORCHESTRATOR
                                      │
   ┌──────────────────┬───────────────┼────────────────┬────────────────────┐
   ▼                  ▼               ▼                ▼                    ▼
 HỌC VIỆN          PHÒNG THI      CHUYÊN GIA        INVESTMENT OS        MEDIA OS
 (học gì, thứ tự)  (đề + chấm)    NHẬP VAI          (dự báo, quyết định)  (tòa soạn)
   │                  │           (hỏi đáp)             │                    │
   └────────┬─────────┘               │                 │                    │
            ▼                         ▼                 ▼                    ▼
 ┌─────────────────────────── THƯ VIỆN CHUYÊN MÔN ───────────────────────────────┐
 │ T1 Nền tảng (playbook) · T2 Việt Nam (luật, VAS, ngành, thủ đoạn)             │
 │ T3 Hồ sơ doanh nghiệp  · T4 Bài học đã chứng minh                             │
 └──────────────────────────────────┬─────────────────────────────────────────────┘
                                    │ tra cứu theo câu hỏi (RETRIEVAL)
 ┌──────────────────────────────────▼─────────────────────────────────────────────┐
 │ FACT LAYER (dữ liệu đã kiểm chứng) ── FIREWALL ── MEDIA chỉ đọc sự thật         │
 └──────────────────────────────────┬─────────────────────────────────────────────┘
 ┌──────────────────────────────────▼─────────────────────────────────────────────┐
 │ UNIVERSAL LEARNING CORE: Source · Evidence · Claim · Prediction · Resolution ·  │
 │ Lesson · Procedure  ─▶  PREDICTION LEDGER ─▶ SCORECARD ─▶ trọng số chuyên gia    │
 └──────────────────────────────────┬─────────────────────────────────────────────┘
 ┌──────────────────────────────────▼─────────────────────────────────────────────┐
 │ DETERMINISTIC ENGINE: dữ liệu · chỉ số BCTC · regime · backtest · decay ·        │
 │ portfolio · risk gate · paper trading · attribution                             │
 └──────────────────────────────────┬─────────────────────────────────────────────┘
                                    ▼
                          DURABLE MEMORY (git)
```

**Vòng lớn của bộ não:**

```text
THƯ VIỆN ──▶ THI ──▶ HÀNH (dự báo/phân tích) ──▶ LEDGER CHẤM ──▶ BÀI HỌC ──▶ THƯ VIỆN
   ▲                                                                           │
   └────────────────────────── AUTO HỌC lấp khoảng trống ◀─────────────────────┘
```

---

# PHẦN III — THƯ VIỆN CHUYÊN MÔN (4 TẦNG)

Nguyên tắc: **không dạy lại những gì Claude đã biết. Chỉ biên soạn thứ tạo ra khác biệt.**

## Tầng 1 — Nền tảng: chưng cất thành PLAYBOOK

Claude và mọi AI khác đều biết định giá, kế toán, vĩ mô. Khác biệt không nằm ở "biết" mà ở **làm đủ, làm đúng, làm giống nhau mọi lần**. Tầng 1 vì vậy không phải giáo trình mà là **quy trình bắt buộc**:

| Playbook | Nội dung |
|---|---|
| `doc_bctc` | 25 bước đọc BCTC: dòng tiền vs lợi nhuận, phải thu, tồn kho, chi phí vốn hóa, giao dịch bên liên quan, ý kiến kiểm toán |
| `chat_luong_loi_nhuan` | Dấu hiệu lợi nhuận "ảo": lãi từ thanh lý, đánh giá lại, hoàn nhập dự phòng, doanh thu nội bộ |
| `dinh_gia` | Khi nào dùng P/E, P/B, EV/EBITDA, DCF; reverse DCF để hỏi "giá đang kỳ vọng gì" |
| `rui_ro_danh_muc` | Tập trung, tương quan, thanh khoản, kịch bản xấu |
| `vi_mo_truyen_dan` | Lãi suất → tín dụng → ngành nào hưởng lợi/bị hại |
| `phan_bien` | 12 câu hỏi Devil's Advocate bắt buộc |

## Tầng 2 — Việt Nam: nơi tạo lợi thế

AI thông thường biết Việt Nam **chung chung và cũ**. Tầng 2 là kiến thức Việt Nam **cụ thể, có nguồn, có ngày hiệu lực**:

| Mảng | Nội dung | Nguồn ưu tiên |
|---|---|---|
| **Luật & quy định** | Luật Chứng khoán, công bố thông tin, giao dịch nội bộ, margin, room ngoại | Văn bản pháp luật chính thức, UBCKNN |
| **Kế toán VAS** | Khác biệt VAS–IFRS ảnh hưởng số liệu; những chỗ VAS cho phép "làm đẹp" | Chuẩn mực VAS, thông tư Bộ Tài chính |
| **Cơ chế thị trường** | Biên độ, T+2, lô, phiên ATO/ATC, cơ cấu nhà đầu tư, dòng tiền ngoại/tự doanh | HOSE, HNX, VSDC |
| **Chuyên ngành** | Ngân hàng (NIM, NPL, CASA, trích lập, nợ tái cơ cấu), BĐS (tồn kho, người mua trả trước, pháp lý dự án), thép, bán lẻ, chứng khoán, dầu khí, điện… | BCTC ngành, báo cáo ngành |
| **Hồ sơ Thủ đoạn** | Xem dưới | Quyết định xử phạt UBCKNN, bản án, báo chí điều tra |

### Hồ sơ Thủ đoạn thị trường (Casebook)

Mỗi thủ đoạn là một hồ sơ:

```text
TÊN:            Làm giá bằng giao dịch khớp chéo
CƠ CHẾ:         (cách hoạt động)
DẤU HIỆU:       khối lượng tăng đột biến không có tin · giá tăng trần nhiều phiên ·
                cổ đông lớn bán ra sau đợt tăng · thanh khoản sụp sau đỉnh
DẤU HIỆU MÁY ĐO ĐƯỢC:  (chuyển thành chỉ số do code tính → cảnh báo tự động)
VỤ VIỆC THẬT:   (tên vụ, năm, quyết định xử phạt/bản án — kèm nguồn)
PHÒNG TRÁNH:    (nhà đầu tư nên làm gì)
TRẠNG THÁI:     CITED / TESTED / PROVEN
```

Danh mục ban đầu: làm giá, bơm thổi tin đồn, giao dịch nội bộ, thao túng BCTC, pha loãng ngầm (phát hành riêng lẻ giá thấp), "chạy" room margin, rút vốn qua bên liên quan, trái phiếu doanh nghiệp rủi ro.

**Mục đích duy nhất: nhận diện và phòng tránh.** Thư viện không chứa và AI không hướng dẫn cách thực hiện thao túng — đó là hành vi vi phạm pháp luật.

## Tầng 3 — Hồ sơ doanh nghiệp (DOSSIER)

Mỗi mã trong universe có một hồ sơ **sống**, cập nhật mỗi quý và mỗi lệnh AUTO:

```text
library/dossiers/VCB/
  profile.md        mô hình kinh doanh, lợi thế, ban lãnh đạo, cổ đông lớn   (Claude viết, có trích nguồn)
  financials.json   số liệu BCTC nhiều năm + chỉ số                           (CODE tính, không LLM)
  red_flags.json    cảnh báo tự động theo Playbook + Casebook                 (CODE)
  thesis.md         luận điểm hiện tại, điều kiện vô hiệu, dự báo đang mở    (Claude, trỏ tới Ledger)
  history.md        các lần luận điểm thay đổi và vì sao                     (append-only)
```

## Tầng 4 — Bài học đã chứng minh

Chảy tự động từ Prediction Ledger (v1.0). Mỗi bài học ghi rõ: đã đúng bao nhiêu lần, trong regime nào, sai khi nào. Đây là tầng **không AI nào khác có**, vì nó sinh ra từ chính lịch sử dự báo của hệ thống.

## Đơn vị kiến thức: KNOWLEDGE_NOTE

Mọi mục trong Thư viện có cùng khuôn:

```text
id · tầng · chủ đề · nội dung (ngôn ngữ rõ ràng)
sources[]            nguồn có đường dẫn, ngày truy cập — Auditor kiểm tồn tại
effective_date       quy định có hiệu lực từ/đến
applies_to           ngành / loại doanh nghiệp / regime
testable_implications[]   hệ quả kiểm chứng được → mẫu dự báo hoặc câu thi
status               DRAFT → CITED → TESTED → PROVEN   (hoặc DISPUTED / OUTDATED)
review_by            ngày phải xem lại
```

| Trạng thái | Nghĩa | Ai gán |
|---|---|---|
| DRAFT | Mới viết | Claude |
| CITED | Mọi khẳng định có nguồn tồn tại | Auditor (code) |
| TESTED | Đã qua câu thi hoặc có dự báo liên quan đã chấm | Code |
| PROVEN | Hệ quả kiểm chứng đúng có ý nghĩa thống kê | Code + Owner duyệt |
| DISPUTED / OUTDATED | Bị bằng chứng mới bác / hết hiệu lực | Code |

**Chuyên gia khi lập luận phải ghi rõ đang dựa vào kiến thức ở trạng thái nào.** Kiến thức DRAFT không được dùng cho quyết định.

## Tra cứu (RETRIEVAL)

AI không "đọc hết" thư viện mỗi lần — không đủ chỗ và không cần. Mỗi câu hỏi:

```text
Câu hỏi ─▶ CODE chọn: mã liên quan → dossier · ngành → playbook ngành ·
                     dấu hiệu bất thường → casebook · bài học T4 cùng regime
        ─▶ gói tối đa N ghi chú liên quan nhất vào ngữ cảnh ─▶ chuyên gia lập luận
```

Giai đoạn đầu: tra theo **mã, ngành, thẻ (tag)** trong `library/INDEX.md` — đơn giản, tất định. Khi thư viện > vài nghìn ghi chú mới thêm tìm kiếm ngữ nghĩa.

---

# PHẦN IV — HỌC VIỆN: HỌC CÁI GÌ, THỨ TỰ NÀO

## Bản đồ năng lực

Mỗi năng lực có cấp độ (giữ thang v0.1) và **điều kiện lên cấp đo được**:

```text
NOT_STARTED → STUDYING → SYNTHESIZED → PRACTICED → VALIDATED → READY → PRODUCTION_PROVEN
                         (có ghi chú   (qua đề thi   (qua ca mù   (dự báo thật
                          CITED)        ≥ ngưỡng)     lịch sử)     hơn baseline)
```

| Năng lực | Thư viện cần | Thi | Ra trận khi |
|---|---|---|---|
| Đọc BCTC | T1 `doc_bctc`, T2 VAS | Tính chỉ số, phát hiện bất thường | ≥ 90% câu tính toán, ≥ 70% phát hiện |
| Ngân hàng | T2 ngân hàng, dossier 10 ngân hàng VN30 | Câu hỏi ngành + ca mù | Đạt đề + ca mù hơn baseline |
| Bất động sản | T2 BĐS, dossier | như trên | như trên |
| Nhận diện thủ đoạn | T2 Casebook | Ca mù: có phát hiện trước khi sự việc lộ không | Tỷ lệ phát hiện > ngẫu nhiên, báo động giả thấp |
| Tin tức/sự kiện | T1 phản biện, T4 | — | Đã chạy (news@v1) — chấm bằng Ledger |
| Vĩ mô | T1 truyền dẫn, dữ liệu vĩ mô | Dự báo có đáp án lịch sử | như trên |
| Định giá | T1 định giá, dossier | Reverse DCF có đáp án | như trên |

**Một chuyên gia chỉ được dự báo thật (ghi vào Ledger, có trọng số) khi năng lực tương ứng ≥ VALIDATED.** Trước đó nó chỉ được chạy ở chế độ SHADOW (dự báo nhưng không ảnh hưởng quyết định).

## AUTO HỌC — vòng học kiến thức

Khi Owner ra lệnh `AUTO HỌC HIỂU HÀNH ĐỘNG`:

```text
1. ĐỌC bản đồ năng lực → chọn KHOẢNG TRỐNG có đòn bẩy cao nhất
     (năng lực đang chặn nhiều việc nhất, hoặc chuyên gia có Brier kém nhất)
2. NGHIÊN CỨU từ nguồn có thể trích dẫn (văn bản pháp luật, BCTC, báo cáo chính thức)
3. CHƯNG CẤT thành KNOWLEDGE_NOTE (DRAFT), kèm testable_implications
4. AUDITOR (code) kiểm nguồn → CITED hoặc trả lại
5. SINH CÂU THI từ ghi chú mới (câu có đáp án từ dữ liệu, không từ ý kiến)
6. THI → cập nhật cấp năng lực
7. GHI trạng thái, CHANGELOG, chọn khoảng trống tiếp theo ↺
DỪNG khi: cổng Owner · cần chi tiền · cần credential · hết ngân sách phiên
```

## CẬP NHẬT — vòng cập nhật dữ liệu

`CẬP NHẬT` (hoặc tự động theo lịch): BCTC quý mới → code tính lại `financials.json`, `red_flags.json` → Claude cập nhật `thesis.md` nếu có thay đổi đáng kể → dự báo mới vào Ledger.

---

# PHẦN V — PHÒNG THI

Giải quyết vấn đề lớn nhất của tài chính: **kết quả thật về chậm** (20–60 phiên). Phòng thi cho phản hồi **ngay lập tức** để học nhanh hơn.

## Loại đề 1 — Đề có đáp án tất định

Đáp án do **code** tính từ dữ liệu, không từ ý kiến:
- "Từ BCTC này, dòng tiền kinh doanh / lợi nhuận sau thuế = ?"
- "Khoản mục nào tăng bất thường nhất so với doanh thu?"
- "Theo quy định hiện hành, cổ đông nội bộ phải công bố giao dịch trước bao nhiêu ngày?" (đáp án trỏ tới văn bản)

## Loại đề 2 — Ca mù lịch sử (Blind Case)

Cho chuyên gia **dữ liệu tại một thời điểm trong quá khứ**, hỏi dự báo, rồi so với điều đã thật sự xảy ra.

**Rủi ro lớn nhất: Claude đã "biết trước" kết cục** của các vụ nổi tiếng (vì có trong dữ liệu huấn luyện). Nếu đưa nguyên tên, bài thi vô nghĩa. Phòng thủ bắt buộc:

```text
• ẨN DANH: thay tên công ty, mã, tên người bằng ký hiệu
• DỜI MỐC: chuẩn hóa số liệu (tỷ lệ, chỉ số), bỏ ngày tháng tuyệt đối
• TRỘN: mỗi đề trộn ca "có sự cố" với ca "bình thường" cùng ngành, tỷ lệ không tiết lộ
• KIỂM TRA RÒ RỈ: hỏi riêng "đây là công ty nào?" — đoán đúng → loại ca đó khỏi đề
```

Chấm bằng Brier như Ledger. Ca mù là cách **duy nhất** đo nhanh năng lực nhận diện thủ đoạn và rủi ro trước khi có sự kiện thật.

## Loại đề 3 — Đối kháng

Một chuyên gia viết luận điểm, Devil's Advocate phản biện, **kết quả lịch sử** phân xử ai đúng. Cả hai được chấm.

Mọi đề thi lưu trong `academy/exams/`, kết quả trong `academy/results/` — thi lại được sau mỗi lần sửa Thư viện hoặc quy trình để đo **học có tiến bộ không**.

---

# PHẦN VI — CHUYÊN GIA NHẬP VAI (HỎI ĐÁP)

Tương đương dự án Phật học "trả lời như Phật", nhưng ở đây là **"trả lời như chuyên gia tài chính hàng đầu Việt Nam — người đã đọc hết Thư viện và có thành tích được đo"**.

## Khi Owner hỏi `HỎI CHUYÊN GIA: <câu hỏi>`

```text
1. CODE tra Thư viện + Fact Layer + Ledger theo câu hỏi
2. Chuyên gia phù hợp lập luận (có thể nhiều chuyên gia độc lập nếu câu hỏi rộng)
3. Devil's Advocate phản biện
4. Tầng NGÔN NGỮ ĐỜI SỐNG chuyển thể — tự do về cách nói, trung thành về nội dung
5. Trả lời theo khuôn:
```

```text
KẾT LUẬN NGẮN      một hai câu, ngôn ngữ đời thường
VÌ SAO             lập luận chính, mỗi ý trỏ tới nguồn / ghi chú / số liệu
ĐIỀU GÌ LÀM SAI    giả định yếu nhất, kịch bản ngược
ĐỘ TIN             mức độ + thành tích thật của chuyên gia trong lĩnh vực này (từ Scorecard)
                   ví dụ: "Chuyên gia ngân hàng: 64 dự báo đã chấm, hơn baseline 8%"
CẦN THEO DÕI       mốc/chỉ số sẽ xác nhận hoặc bác bỏ
```

## Luật chuyển thể ngôn ngữ

| Được | Không được |
|---|---|
| Dùng ví von đời thường, ngôn ngữ giản dị | Thêm khẳng định không có trong bằng chứng |
| Tóm lược, sắp xếp lại | Bỏ phần "điều gì làm sai" hoặc độ tin |
| Thay thuật ngữ bằng lời giải thích | Làm độ chắc chắn nghe cao hơn thực tế |

Tầng ngôn ngữ đời sống **dùng chung với Media OS** — cùng một năng lực, hai đầu ra (trả lời Owner / kịch bản video).

## Phạm vi an toàn

- Trả lời Owner: được phân tích sâu, nêu xác suất, không có giới hạn chủ đề tài chính hợp pháp.
- Nội dung công khai (Media OS): phân tích và giáo dục, **không khuyến nghị mua/bán cá nhân**, có miễn trừ trách nhiệm (Owner Gate pháp lý giữ nguyên).
- Thủ đoạn thị trường: chỉ giải thích để **nhận diện và phòng tránh**.

---

# PHẦN VII — INVESTMENT OS & MEDIA OS (GIỮ v1.0, NÂNG CẤP)

Toàn bộ Phần VII của v1.0 giữ nguyên. Nâng cấp:

| Thành phần | v1.0 | v2.0 |
|---|---|---|
| Đầu vào chuyên gia | Tin tức + số liệu thô | + Thư viện đúng chủ đề (playbook, dossier, casebook, bài học) |
| Quyền dự báo thật | Mọi chuyên gia | Chỉ chuyên gia có năng lực ≥ VALIDATED; còn lại SHADOW |
| Cảnh báo rủi ro | Risk Gate theo giới hạn danh mục | + `red_flags.json` từ Casebook: mã có dấu hiệu thủ đoạn bị hạ tỷ trọng / loại |
| Media OS | Bản tin từ Fact Layer | + tầng ngôn ngữ đời sống chung; chuyên mục "nhận diện thủ đoạn" từ Casebook (giáo dục nhà đầu tư) |

---

# PHẦN VIII — RUNTIME: HỌC BẰNG GÓI MAX, THI HÀNH BẰNG ACTIONS

Phát hiện quan trọng: phần **học** (biên soạn Thư viện) và phần **thi hành** (dự báo hằng ngày) có nhu cầu khác nhau, nên chạy ở hai nơi khác nhau để tiết kiệm.

| Việc | Chạy ở | Chi phí | Lý do |
|---|---|---|---|
| **AUTO HỌC** — nghiên cứu, viết Thư viện, soạn đề thi | **Claude Code / Claude chat (gói Max)** kết nối repo | Trong hạn mức gói, **không tốn API** | Cần suy nghĩ sâu, không cần chạy theo giờ cố định |
| Dữ liệu, chỉ số BCTC, red flags, chấm thi tất định, Ledger, engine | GitHub Actions — job tất định | Miễn phí | Tất định, chạy mỗi ngày |
| Chuyên gia dự báo hằng ngày, ca mù định kỳ | GitHub Actions — gọi API | **Tiền API**, có trần | Phải tự chạy khi Owner không mở máy |
| HỎI CHUYÊN GIA | Claude chat trong Project (có Thư viện đồng bộ từ GitHub) | Trong hạn mức gói | Owner hỏi lúc nào trả lời lúc đó |

Hệ quả: **khối lượng học lớn nhất lại gần như miễn phí**; tiền API chỉ dùng cho phần phải tự động chạy hằng ngày.

---

# PHẦN IX — CẤU TRÚC REPO v2.0

```text
BOOT.md                     ← thêm: thứ tự đọc Thư viện, lệnh mới
architecture/ARCHITECTURE_v2.0.md
governance/                 (giữ)
library/                    ← MỚI
  INDEX.md                  mục lục + thẻ, code sinh tự động
  foundations/playbooks/    Tầng 1
  vietnam/law/  vietnam/accounting/  vietnam/market/  vietnam/sectors/
  casebook/manipulation/    Tầng 2 — hồ sơ thủ đoạn
  dossiers/<MÃ>/            Tầng 3
  lessons/                  Tầng 4 (sinh từ Ledger)
academy/                    ← MỚI
  competency_map.yaml       bản đồ năng lực + điều kiện lên cấp
  curriculum.md             thứ tự học
  exams/  results/          đề thi + kết quả
engine/                     (giữ) + financials.py, red_flags.py, retrieval.py, exams.py
ledger/  fact/  data/  paper/  reports/  memory/  state/   (giữ)
contracts/                  + KNOWLEDGE_NOTE, EXAM_ITEM, DOSSIER  (tổng 24)
```

---

# PHẦN X — LỆNH CỦA OWNER

| Lệnh | Việc | Chạy ở |
|---|---|---|
| `AUTO HỌC HIỂU HÀNH ĐỘNG` | Lấp khoảng trống năng lực lớn nhất: học → viết Thư viện → soạn đề → thi | Claude Code / chat |
| `CẬP NHẬT` | Cập nhật dữ liệu, BCTC, dossier, tin tức | Actions (tự động) hoặc chat |
| `HỎI CHUYÊN GIA: …` | Nhập vai chuyên gia trả lời theo khuôn Phần VI | Chat trong Project |
| `THI <năng lực>` | Chạy lại đề thi, báo điểm | Chat / Actions |
| `TRẠNG THÁI` | Bản đồ năng lực + Scorecard + ngân sách | Chat |
| `PHẢN BIỆN <id>` · `DUYỆT/TỪ CHỐI <id>` | Giữ v1.0 | — |
| `NGÂN SÁCH <số>` · `ĐỐI CHỨNG` | Giữ v1.0 | — |

---

# PHẦN XI — THƯỚC ĐO: BỘ NÃO CÓ GIỎI LÊN KHÔNG

| Câu hỏi | Chỉ số | Nguồn |
|---|---|---|
| Học được bao nhiêu? | Số ghi chú theo trạng thái (CITED/TESTED/PROVEN); độ phủ bản đồ năng lực | Thư viện |
| Học có vào không? | Điểm thi theo thời gian (thi lại cùng đề sau mỗi lần sửa Thư viện) | Phòng thi |
| Có nhận diện được rủi ro không? | Brier ca mù; tỷ lệ phát hiện vs báo động giả | Phòng thi |
| Có đúng ngoài đời không? | Brier skill vs baseline mạnh nhất, theo chuyên gia | Ledger |
| **Có hơn Claude đứng một mình không?** | Nhóm A (có Thư viện) vs nhóm B (Claude trần) — trên **cả đề thi lẫn dự báo thật** | Nhóm đối chứng |
| Thư viện có đáng tiền không? | Chênh lệch điểm A–B / chi phí API | Kinh tế |

Nhóm đối chứng v1.0 giờ đo đúng giá trị của Thư viện: **cùng Claude, có Thư viện vs không có Thư viện**. Nếu không có chênh lệch, Thư viện đang được biên soạn sai hướng.

---

# PHẦN XII — LỘ TRÌNH v2.0

Chạy **hai làn song song**: làn HỌC (chủ yếu miễn phí qua gói Max) và làn CHỨNG MINH (Actions).

| GĐ | Làn HỌC | Làn CHỨNG MINH | Điều kiện thoát |
|---|---|---|---|
| **0** | — | Engine định lượng, Actions | ✅ Xong |
| **1** | Khung Thư viện + Học viện + 3 contract mới; Playbook `doc_bctc`, `phan_bien` | Prediction Ledger, news@v1, Devil's Advocate | ✅ Code Ledger xong; chờ Owner mở cổng ngân sách |
| **2** | Dữ liệu BCTC + `financials.json`, `red_flags.json` cho VN30 (code); dossier 30 mã | Chuyên gia chạy SHADOW với Thư viện | Dossier đủ 30 mã, 100% số liệu do code tính |
| **3** | Tầng 2: VAS, ngân hàng, BĐS, chứng khoán; Casebook 8 thủ đoạn | Đề thi loại 1; bộ ca mù đầu tiên (ẩn danh, kiểm rò rỉ) | Chuyên gia ngân hàng đạt VALIDATED |
| **4** | Chế độ HỎI CHUYÊN GIA đầy đủ | Nhóm đối chứng A/B trên đề + dự báo | Báo cáo A vs B đầu tiên có ý nghĩa thống kê |
| **5** | Mở rộng ngành còn lại | Portfolio kết hợp; Decision Package | 12 lần tái cơ cấu giấy, attribution đầy đủ |
| **6** | — | Media OS dùng tầng ngôn ngữ đời sống chung | 8 bản tin, 0 lỗi sự thật |
| **7** | Meta-learning trên cách học (loại ghi chú nào nâng điểm nhiều nhất) | Shadow procedure | ≥ 1 quy trình học mới được chứng minh tốt hơn |
| **8** | Tách Universal Core → dùng cho dự án Phật học / YouTube | — | Dự án thứ hai chạy trên lõi chung |

Giao dịch tiền thật: **không nằm trong lộ trình** — giữ nguyên điều kiện v1.0.

---

# PHẦN XIII — CHẾ ĐỘ HỎNG MỚI & CÁCH PHÒNG

Giữ toàn bộ bảng của v1.0, thêm:

| Chế độ hỏng | Phòng thủ |
|---|---|
| **Thư viện đầy chữ, không nâng năng lực** ("học vẹt") | Mỗi ghi chú phải có testable_implications; nhóm đối chứng A/B đo giá trị thật |
| **Ghi chú bịa nguồn** | Auditor kiểm nguồn tồn tại trước khi lên CITED |
| **Kiến thức lỗi thời** (luật đổi, chính sách đổi) | `effective_date`, `review_by`; quá hạn tự chuyển OUTDATED |
| **Ca mù bị rò rỉ** (Claude nhận ra công ty) | Ẩn danh, chuẩn hóa, trộn ca, kiểm tra nhận diện — lộ thì loại |
| **Thi giỏi, ra trận kém** (học tủ theo đề) | Đề mới sinh liên tục; năng lực chỉ lên PRODUCTION_PROVEN bằng Ledger thật |
| **Nhập vai nói quá chắc** | Khuôn trả lời bắt buộc có "điều gì làm sai" + độ tin từ Scorecard |
| **Kiến thức thủ đoạn bị dùng sai mục đích** | Casebook chỉ gồm dấu hiệu nhận biết và phòng tránh; không hướng dẫn thực hiện |

---

# KẾT

```text
v0.1  vẽ TỔ CHỨC nên trông như thế nào
v1.0  xây cách tổ chức CHỨNG MINH mình đúng
v2.0  xây cách tổ chức HỌC để ngày càng đúng hơn

HỌC có nguồn      → Thư viện
HỌC có kiểm tra   → Phòng thi
HỌC có ứng dụng   → Dự báo thật, chấm bằng thị trường
HỌC có tiến bộ    → Thi lại, đối chứng, meta-learning
TRẢ LỜI như chuyên gia hàng đầu → nhưng luôn nói rõ: dựa vào đâu, sai khi nào, tin được bao nhiêu
```

Cùng một bộ não Claude — nhưng được **đào tạo nghề riêng cho thị trường Việt Nam, có giáo trình, có kỳ thi, có thành tích được đo**. Đó là cách hợp lệ và kiểm chứng được để vượt các AI phân tích thông thường.
