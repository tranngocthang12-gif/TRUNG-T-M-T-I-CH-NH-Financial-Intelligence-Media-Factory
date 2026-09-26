# NHÀ MÁY TRÍ TUỆ TÀI CHÍNH
## FINANCIAL INTELLIGENCE & MEDIA FACTORY — ARCHITECTURE v1.0

**Kiến trúc sư trưởng:** Claude · **Owner:** Trần Ngọc Thắng · **Ngày:** 26/09/2026
**Kế thừa:** Architecture v0.1 (32 mục của Owner) + bài học từ v0.2 (engine định lượng đã chạy trên GitHub)

> KHÔNG XÂY AI ĐOÁN THỊ TRƯỜNG.
> XÂY MỘT HỆ THỐNG biết thu thập bằng chứng, biết nghi ngờ chính nó, biết đo lường độ không chắc chắn,
> biết quản trị rủi ro, biết học từ kết quả, và biết cải thiện cách nó học.

Câu này giữ nguyên. v1.0 không đổi tầm nhìn — v1.0 trả lời câu hỏi mà v0.1 còn bỏ ngỏ:
**cụ thể thì "học" xảy ra ở đâu, bằng cơ chế gì, đo bằng gì, chạy trên máy nào, tốn bao nhiêu.**

---

# PHẦN I — CHẨN ĐOÁN v0.1

v0.1 có tầm nhìn đúng và danh mục thành phần đầy đủ. Năm điểm cần sửa trước khi xây:

| # | Vấn đề của v0.1 | Hệ quả nếu giữ nguyên | Cách v1.0 xử lý |
|---|---|---|---|
| 1 | "Learning" được nêu nhưng **không có cơ chế chấm điểm cho chuyên gia định tính** (Fundamental, Macro, News). Chỉ Quant có backtest. | Các chuyên gia LLM viết phân tích mãi mà không bao giờ biết mình đúng hay sai. Tổ chức không học được. | **Prediction Ledger** trở thành trái tim hệ thống (Phần III). |
| 2 | Không phân biệt **việc của code** và **việc của LLM**. | LLM tự tính số, tự bịa nguồn, tự khẳng định đã "kiểm chứng". | **Ranh giới Tất định / Diễn giải** (Phần II.2). |
| 3 | 32 thành phần cùng cấp độ ưu tiên. | Xây dàn trải, không thành phần nào chạy trọn vẹn. Chính v0.2 đã rơi vào bẫy ngược lại: chỉ xây Quant. | **Walking skeleton**: một lát mỏng xuyên suốt mọi tầng trước, làm dày sau (Phần VIII). |
| 4 | Không nói hệ thống **chạy ở đâu, khi nào, tốn bao nhiêu**. | Không vận hành được thật; chi phí API không kiểm soát. | **Runtime topology + Budget Governor** (Phần VI). |
| 5 | Universal Learning Core là **danh sách khái niệm**, chưa phải thiết kế. | Không tái sử dụng được cho YouTube/kinh doanh. | Core = **7 primitive** có schema, tài chính và truyền thông là plugin (Phần II.3). |

---

# PHẦN II — NGUYÊN LÝ THIẾT KẾ

## II.1 Tổ chức học, mô hình không học

Trọng số của Claude không thay đổi. Cái thay đổi là **tổ chức bao quanh Claude**:

```text
                ┌─────────────────────────────────────────────┐
                │   MÔ HÌNH (Claude) — cố định, rất mạnh,     │
                │   không trí nhớ, có thể sai một cách tự tin │
                └──────────────────────┬──────────────────────┘
                                       │ được đặt trong
                ┌──────────────────────▼──────────────────────┐
                │   TỔ CHỨC — học được, đo được, nhớ được     │
                │   • Tri thức đã kiểm chứng (đọc mỗi lần)    │
                │   • Bảng điểm từng chuyên gia (trọng số)    │
                │   • Quy trình/prompt đã thắng (phiên bản)   │
                │   • Cổng rủi ro, phản biện bắt buộc         │
                └─────────────────────────────────────────────┘
```

**Câu hỏi thiết kế trung tâm của v1.0:**
*Claude trong tổ chức này, sau 12 tháng, có dự báo tốt hơn, hiệu chuẩn tốt hơn, và ít sai lầm tốn kém hơn Claude đứng một mình không?*
Mọi thành phần phải góp phần trả lời "có" — và phải **đo được** câu trả lời đó.

## II.2 Ranh giới Tất định / Diễn giải

```text
┌───────────────────────────────┐        ┌────────────────────────────────┐
│  TẤT ĐỊNH (code Python)       │        │  DIỄN GIẢI (Claude)            │
│  — không bao giờ để LLM làm   │        │  — không bao giờ để code làm   │
├───────────────────────────────┤        ├────────────────────────────────┤
│ Lấy dữ liệu, gắn timestamp    │        │ Đọc tin, báo cáo, BCTC         │
│ Mọi phép tính số              │  ───▶  │ Đặt giả thuyết, lập luận       │
│ Backtest, IC, Brier, alpha    │ số liệu│ Phản biện, tìm giải thích khác │
│ Chấm dự báo khi đến hạn       │  ◀───  │ Viết kịch bản truyền thông     │
│ Kiểm nguồn có tồn tại không   │  claim │ Đề xuất feature/quy trình mới  │
│ Cổng rủi ro, thang vốn        │        │ Tóm tắt cho Owner              │
└───────────────────────────────┘        └────────────────────────────────┘
```

Luật: **Claude không được tự tính con số mà quyết định dựa vào.** Claude gọi công cụ, code trả số. Claude không được tự đánh dấu một claim là "đã kiểm chứng" — chỉ Auditor (code) làm được.

## II.3 Universal Learning Core = 7 primitive

Đây là toàn bộ "bộ não học" dùng chung cho mọi lĩnh vực. Tài chính và truyền thông chỉ là **plugin** định nghĩa nguồn dữ liệu, chuyên gia và cách chấm.

```text
 CLAIM ──── dựa trên ────▶ EVIDENCE ──── trích từ ────▶ SOURCE
   │                                                       (có hash, retrieved_at)
   │ phải sinh ra
   ▼
 PREDICTION ─── đến hạn ───▶ RESOLUTION ─── rút ra ───▶ LESSON
   │ (xác suất, hạn, cách chấm)   (code chấm)              │
   │                                                       ▼
   └────── tạo bởi ──────▶ PROCEDURE (chuyên gia + prompt + phiên bản)
                                  │
                                  ▼
                             SCORECARD (Brier, calibration, vs baseline)
```

| Primitive | Là gì | Ví dụ tài chính | Ví dụ YouTube (tái sử dụng) |
|---|---|---|---|
| **Source** | Nguồn gốc có dấu thời gian | BCTC Q2 của FPT, tin CafeF | Số liệu YouTube Analytics |
| **Evidence** | Một quan sát trích từ nguồn | Biên gộp tăng 2,1 điểm % | CTR video A = 7,2% |
| **Claim** | Một nhận định | "FPT cải thiện biên lợi nhuận" | "Tiêu đề dạng câu hỏi tăng CTR" |
| **Prediction** | Dự báo kiểm chứng được | "FPT vượt VN30 trong 20 phiên, p=0,6" | "Video B có CTR > 6%, p=0,55" |
| **Resolution** | Kết quả do code chấm | Đúng/sai + lợi nhuận thực | CTR thực = 5,1% → sai |
| **Lesson** | Bài học rút ra sau attribution | "Tín hiệu biên lợi nhuận chỉ đúng khi thanh khoản cao" | "Câu hỏi chỉ hiệu quả với chủ đề vĩ mô" |
| **Procedure** | Cách tạo ra claim/dự báo, có phiên bản | Prompt Fundamental v3 | Prompt viết tiêu đề v2 |

---

# PHẦN III — TRÁI TIM: PREDICTION LEDGER & CALIBRATION

Đây là thành phần **quan trọng nhất** mà v0.1 thiếu. Không có nó, mục 8 (Uncertainty), 12 (Attribution), 22 (Meta-learning) của v0.1 chỉ tồn tại trên giấy đối với các chuyên gia LLM.

## III.1 Luật dự báo

Mọi chuyên gia khi đưa ra nhận định có ảnh hưởng tới quyết định **bắt buộc** phát ra ít nhất một dự báo:

```text
PREDICTION
  id, created_at (bất biến, commit vào git TRƯỚC khi có kết quả)
  procedure_id + version     (ai, bằng quy trình nào)
  claim_refs                 (dự báo này kiểm tra claim nào)
  question                   ("FPT có vượt VN30 trong 20 phiên từ 2026-09-29?")
  resolution_rule            (máy chấm thế nào — viết bằng tham số, không bằng lời)
  resolve_at                 (ngày đến hạn)
  probability                (0.05–0.95; cấm 0 và 1)
  base_rate                  (xác suất nền, do code cung cấp)
```

Dự báo **không có resolution_rule máy chấm được** → Auditor từ chối, claim không được dùng cho quyết định.

## III.2 Chấm điểm

Code chấm mỗi ngày những dự báo đến hạn, rồi tính cho từng chuyên gia/quy trình:

| Chỉ số | Ý nghĩa | Ngưỡng tin cậy |
|---|---|---|
| **Brier score** | Sai số xác suất (thấp = tốt) | So với baseline, không so tuyệt đối |
| **Brier skill score** vs base rate | Có hơn việc luôn đoán xác suất nền không? | > 0 mới có giá trị |
| **Calibration** theo nhóm (50–60%, 60–70%…) | Nói 70% thì có đúng ~70% không? | Sai lệch < 10 điểm % |
| **Resolution** | Có phân biệt được trường hợp đúng/sai không? | > 0 |
| **Số dự báo đã chấm (n)** | Độ tin của chính bảng điểm | n < 30: chưa kết luận |

**Baseline bắt buộc** — mỗi chuyên gia phải thắng ít nhất một trong:
1. Xác suất nền (luôn đoán tỷ lệ lịch sử),
2. Mô hình ngây thơ (ví dụ: động lượng 60 phiên của engine),
3. Claude đứng một mình không có tri thức tổ chức (**nhóm đối chứng** — xem III.4).

## III.3 Trọng số chuyên gia

Khi nhiều chuyên gia dự báo cùng một câu hỏi, Portfolio Manager **không tự cân nhắc bằng cảm tính** — code gộp:

```text
log-odds tổng hợp = Σ w_i × log-odds_i        (chỉ chuyên gia có n ≥ 30)
w_i ∝ Brier skill score_i, co về 0 khi n nhỏ    (chưa có thành tích → không có tiếng nói)
```

Kết quả: chuyên gia **tự kiếm quyền ảnh hưởng bằng thành tích**, không bằng độ hùng hồn.

## III.4 Nhóm đối chứng — đo chính câu hỏi trung tâm

Mỗi tuần, cùng một bộ câu hỏi được trả lời bởi:
- **Nhóm A:** chuyên gia trong tổ chức (có tri thức canonical, bảng điểm, phản biện),
- **Nhóm B:** Claude "trần" — cùng mô hình, cùng dữ liệu thô, **không** có tri thức tổ chức.

So Brier của A và B theo thời gian. Đây là **bằng chứng duy nhất** cho việc tổ chức có thật sự thông minh hơn hay không. Nếu sau 6 tháng A không hơn B → kiến trúc có vấn đề, phải xem lại, không được tự huyễn.

---

# PHẦN IV — KIẾN TRÚC TỔNG THỂ v1.0

```text
                              HUMAN OWNER
                    (mục tiêu, giới hạn, duyệt cổng)
                                   │
                          FINANCIAL GOVERNOR
          (vốn · rủi ro · ngân sách API · pháp lý · an toàn — chỉ Owner sửa)
                                   │
                        INTELLIGENCE ORCHESTRATOR
          (đọc state → chọn việc → gọi chuyên gia → phản biện → ghi → dừng ở cổng)
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        ▼                          ▼                          ▼
 INVESTMENT OS               FACT LAYER                 MEDIA OS
 (chuyên gia, quyết định)    (sự thật dùng chung,       (tòa soạn)
        │                     trạng thái kiểm chứng)          │
        │            ▲ chỉ đọc            ▲ chỉ đọc           │
        │            └─────── FIREWALL ───┘                   │
        │                                                     │
        └──────────────────────────┬──────────────────────────┘
                                   ▼
        ┌──────────────────── UNIVERSAL LEARNING CORE ─────────────────────┐
        │  Source · Evidence · Claim · Prediction · Resolution · Lesson ·  │
        │  Procedure  ─▶  Prediction Ledger  ─▶  Scorecard  ─▶  Weights    │
        └──────────────────────────────┬───────────────────────────────────┘
                                       ▼
        ┌──────────────────── DETERMINISTIC ENGINE ────────────────────────┐
        │  Data (point-in-time) · Features · Regime · Backtest · Decay ·   │
        │  Portfolio · Risk Gate · Paper Trading · Attribution             │
        │  (đã có trong v0.2, giữ nguyên và mở rộng)                        │
        └──────────────────────────────┬───────────────────────────────────┘
                                       ▼
                               DURABLE MEMORY (git)
                                       ▼
                         THREE LEARNING LOOPS (Phần V)
```

## IV.1 Fact Layer — thay đổi so với v0.1

v0.1 đặt Fact Layer chỉ ở mục Firewall. v1.0 nâng nó thành **dịch vụ trung tâm**:
- Mỗi fact có trạng thái: `RAW → EXTRACTED → CROSS_CHECKED → VERIFIED` (hoặc `DISPUTED`).
- `VERIFIED` chỉ do code gán: có ≥ 1 nguồn gốc tồn tại (hash khớp) và, với số liệu, khớp giữa ≥ 2 nguồn hoặc khớp với dữ liệu gốc.
- Investment OS và Media OS **chỉ được trích fact có trạng thái ≥ CROSS_CHECKED** khi đưa ra kết luận hoặc xuất bản.

## IV.2 Firewall — cưỡng chế bằng cấu trúc, không bằng lời hứa

```text
positions/, decisions/, paper/     ── Media OS KHÔNG có quyền đọc
media/                             ── Investment OS KHÔNG có quyền ghi
fact/                              ── cả hai chỉ đọc; chỉ Fact pipeline ghi
```

`tools/validate.py` kiểm tra trong mỗi lần chạy: nếu code Media import hoặc đọc đường dẫn `positions/`/`decisions/`/`paper/` → **chặn cả vòng chạy**. Mỗi MEDIA_STORY bắt buộc có CONFLICT_DISCLOSURE do code tạo (so danh sách mã được nhắc với danh sách đang nắm).

## IV.3 Chuyên gia — "vai là logic, lần gọi là vật lý"

v0.1 có 10 vai đầu tư + 10 vai tòa soạn. Gọi Claude riêng cho từng vai rất tốn và dễ "đồng thuận giả". v1.0 quy định:

| Quy tắc | Lý do |
|---|---|
| **Vòng 1 độc lập:** Fundamental, Macro, News, Valuation mỗi người phân tích riêng, **không thấy** kết quả nhau | Tránh bầy đàn; đo được đóng góp riêng |
| **Devil's Advocate luôn là lần gọi riêng**, được đưa bằng chứng phản bác do code tìm | Phản biện thật, không tự phản biện chính mình |
| **Auditor là code**, không phải LLM | Kiểm nguồn tồn tại, số khớp dữ liệu, dự báo có luật chấm |
| **Risk Officer là code + LLM giải thích** | Cổng chặn phải tất định |
| Vai không cần độc lập (CIO tổng hợp, Script Editor + Director…) được **gộp chung một lần gọi** | Tiết kiệm ngân sách |
| Mỗi chuyên gia là một **Procedure có phiên bản**: prompt + công cụ được dùng + contract đầu ra | Đo, so sánh, thay thế được |

## IV.4 Chuyên gia nào làm gì trong tuần đầu

| Chuyên gia | Đầu vào (do code cấp) | Đầu ra bắt buộc | Chấm bằng |
|---|---|---|---|
| **News/Event** | Tin RSS 24h, sự kiện doanh nghiệp | Evidence + dự báo phản ứng giá 5/20 phiên | Lợi nhuận vượt trội thực tế |
| **Fundamental** | BCTC, chỉ số do code tính | Claim chất lượng + dự báo 60 phiên | Lợi nhuận vượt trội, KQKD kỳ sau |
| **Macro** | Lãi suất, tỷ giá, CPI | Nhận định regime + dự báo chỉ số | Regime thực tế, VN-Index |
| **Valuation** | Dự phóng, giá, số liệu ngành | Khoảng giá trị + xác suất giá vào khoảng | Giá thực tế sau kỳ hạn |
| **Quant** | *Đã có — engine v0.2* | Tín hiệu, IC | Walk-forward + live decay |
| **Devil's Advocate** | Luận điểm + bằng chứng phản bác | Giả định yếu nhất + dự báo **ngược** | Được chấm như mọi chuyên gia |

Devil's Advocate cũng phải dự báo và bị chấm — để phản biện có trách nhiệm, không phản biện cho có.

---

# PHẦN V — BA VÒNG HỌC

v0.1 gộp mọi thứ vào "Learning" và "Meta-learning". v1.0 tách thành ba vòng, mỗi vòng có tốc độ, bằng chứng và quyền hạn khác nhau:

```text
VÒNG 1 — HỌC TRI THỨC            VÒNG 2 — HỌC TIN AI              VÒNG 3 — HỌC CÁCH HỌC
(nhanh: hằng ngày)               (trung bình: hằng tuần)          (chậm: hằng tháng)

Resolution + Attribution         Scorecard cập nhật               So các Procedure với nhau
       ↓                                ↓                                 ↓
LESSON (UNVERIFIED)              Trọng số chuyên gia              Đề xuất prompt/quy trình mới
       ↓                                ↓                                 ↓
đủ bằng chứng → SUPPORTED        Chuyên gia kém → giảm tiếng nói  SANDBOX: chạy song song
       ↓                         Chuyên gia tốt → tăng             trên câu hỏi mới (shadow)
Owner duyệt → CANONICAL                                                   ↓
       ↓                                                          Thắng có ý nghĩa thống kê
Mọi chuyên gia đọc                                                → Owner duyệt → phiên bản mới
```

**Quy tắc chung của ba vòng:**
1. Không vòng nào được học từ kết quả chưa qua **Attribution** (tách beta, ngành, may mắn).
2. Vòng 3 thử nghiệm quy trình mới ở chế độ **shadow** — quy trình mới dự báo song song nhưng không được dùng cho quyết định cho tới khi thắng quy trình cũ trên dữ liệu chưa từng thấy.
3. Mỗi lần thay đổi đều được version trong git — luôn quay lại được.

Vòng 3 chính là mục 22 (Meta-learning) và 23 (Self-repair) của v0.1, nay có cơ chế đo thật.

---

# PHẦN VI — RUNTIME: CHẠY Ở ĐÂU, KHI NÀO, TỐN BAO NHIÊU

## VI.1 Ba nơi chạy

| Nơi | Chạy gì | Khi nào | Chi phí |
|---|---|---|---|
| **GitHub Actions — job tất định** | Data, Fact pipeline, engine định lượng, chấm dự báo, Auditor, Risk Gate, paper trading, báo cáo | 16:30 mỗi ngày giao dịch | Miễn phí (trong hạn mức GitHub) |
| **GitHub Actions — job chuyên gia** | Các lần gọi Claude API theo lịch của Orchestrator | Sau job tất định | **Tiền API** — có trần do Governor giữ |
| **Claude chat / Claude Code (gói Max)** | Owner review tuần, thay đổi kiến trúc, viết code mới, phân tích sâu theo yêu cầu | Khi Owner mở phiên | Trong hạn mức gói, không tính API |

## VI.2 Budget Governor (mới)

Thêm vào `GOVERNOR_POLICY.yaml`:

```yaml
api_budget:
  monthly_cap_usd: TODO          # Owner đặt
  daily_cap_usd: TODO
  on_cap_reached: skip_experts   # engine tất định vẫn chạy
  priority_order:                # hết tiền thì cắt từ dưới lên
    - resolution_and_audit       # luôn chạy (không tốn API)
    - devils_advocate
    - news_event
    - fundamental
    - control_group_weekly
    - media_brief
```

Mỗi lần gọi API ghi vào `memory/economic/api_spend.csv` (ngày, chuyên gia, token, chi phí). Vòng 3 dùng số liệu này để tính **chi phí cho mỗi bài học được kiểm chứng** — một thước đo hiệu quả của cả tổ chức.

## VI.3 Lưu trữ — theo giai đoạn, không làm sẵn

v0.1 liệt kê Database, Object Storage, Vector Index, Model Registry ngay từ đầu. v1.0: **git là đủ cho tới khi có lý do đo được để chuyển.**

| Giai đoạn | Lưu trữ | Điều kiện chuyển lên |
|---|---|---|
| Hiện tại | Git: CSV nén, JSON, JSONL, Markdown | Repo > 500 MB hoặc truy vấn chậm > 1 phút |
| Sau đó | + SQLite/DuckDB trong repo hoặc artifact | Cần truy vấn phức tạp trên nhiều năm dữ liệu |
| Khi có video | + Object storage cho media | Có file video/ảnh thật |
| Khi tri thức > vài nghìn mục | + Search index | Chuyên gia không đọc hết được tri thức liên quan |

Secrets luôn ở GitHub Secrets. Không bao giờ trong repo.

---

# PHẦN VII — INVESTMENT OS & MEDIA OS TRONG v1.0

## VII.1 Luồng đầu tư một ngày

```text
16:30  DATA ─▶ FACT LAYER ─▶ ENGINE (tín hiệu, regime, decay)
         │
         ▼
       ORCHESTRATOR chọn 1–3 chủ đề (theo: tin mới, tín hiệu mạnh, dự báo sắp đến hạn,
                                     khoảng trống năng lực lớn nhất)
         │
         ▼
       VÒNG 1: chuyên gia độc lập ─▶ Claim + Evidence + Prediction
         │
         ▼
       AUDITOR (code): nguồn có thật? số khớp? dự báo chấm được?   ── fail ─▶ loại
         │
         ▼
       DEVIL'S ADVOCATE ─▶ phản biện + dự báo ngược
         │
         ▼
       GỘP XÁC SUẤT (code, theo trọng số Scorecard)
         │
         ▼
       PORTFOLIO (code) ─▶ RISK GATE (code) ─▶ DECISION PACKAGE
         │                                          │
         ▼                                          ▼
       PAPER TRADING (tự động)             decisions/pending/ ─▶ OWNER (chỉ khi lên cấp vốn)
         │
         ▼
       RESOLUTION + ATTRIBUTION (các ngày sau) ─▶ BA VÒNG HỌC
```

## VII.2 Media OS — tòa soạn có bảng điểm

Media dùng **cùng Universal Learning Core**, nhưng chấm hai thứ tách biệt (giữ nguyên mục 24 v0.1, thêm cơ chế):

| Trục | Dự báo trước khi đăng | Chấm sau khi đăng | Luật |
|---|---|---|---|
| **Sự thật** | Mọi con số trong kịch bản trỏ tới fact VERIFIED | Fact Checker (code) đối chiếu; đính chính nếu sai | Sai sự thật = không được bù bằng lượt xem |
| **Khán giả** | "Tiêu đề A có CTR > x%, p=…" | YouTube Analytics | Chỉ học tối ưu hình thức **khi điểm sự thật không giảm** |

Luật chống clickbait được viết thành điều kiện máy kiểm: một thay đổi quy trình truyền thông chỉ được duyệt nếu **retention ≥ cũ** (khán giả xem hết, không chỉ bấm vào) **và** không có đính chính.

**Pháp lý (Owner Gate):** nội dung tài chính công khai tại Việt Nam có thể chạm quy định về tư vấn đầu tư chứng khoán. Media OS mặc định: phân tích và giáo dục, **không khuyến nghị mua/bán mã cụ thể**, có tuyên bố miễn trừ. Mở rộng phạm vi phải có Owner duyệt sau khi tham khảo chuyên gia pháp lý.

---

# PHẦN VIII — LỘ TRÌNH: WALKING SKELETON

Nguyên tắc: **mỗi giai đoạn có một lát chạy trọn vẹn từ dữ liệu tới bài học**, và chỉ qua giai đoạn sau khi đạt **điều kiện thoát** — không theo ngày.

| GĐ | Tên | Xây gì | Điều kiện thoát (đo được) |
|---|---|---|---|
| **0** | Nền móng | Governance, contracts, engine định lượng, GitHub Actions | ✅ **Đã xong** (v0.2 chạy thành công) |
| **1** | Bộ xương sống | Prediction Ledger + Resolution + Scorecard; **1 chuyên gia (News)** + Devil's Advocate + Auditor code; Budget Governor | 30 ngày chạy liên tục; ≥ 100 dự báo đã chấm; 0 claim thiếu nguồn lọt qua Auditor |
| **2** | Hội đồng | + Fundamental, Macro, Valuation; Evidence Graph; gộp xác suất theo trọng số; nhóm đối chứng hằng tuần | Mỗi chuyên gia ≥ 30 dự báo đã chấm; báo cáo Brier A vs B đầu tiên |
| **3** | Quyết định | Portfolio kết hợp engine + chuyên gia; Risk Gate đọc Governor; Decision Package; paper trading theo quyết định tổng hợp | 12 lần tái cơ cấu; attribution tách beta/alpha có báo cáo |
| **4** | Tòa soạn | Fact Layer đầy đủ; bản tin tuần (kịch bản + biểu đồ) dạng nháp; firewall cưỡng chế bằng validate | 8 bản tin liên tiếp, 0 lỗi sự thật, conflict check 100% |
| **5** | Học cách học | Vòng 3: shadow procedure, so sánh phiên bản, đề xuất tự sửa qua sandbox | ≥ 1 quy trình mới thắng quy trình cũ có ý nghĩa thống kê và được Owner duyệt |
| **6** | Tách lõi | Universal Learning Core thành package riêng; plugin YouTube cho dự án nội dung của Owner | Plugin thứ hai chạy được mà không sửa lõi |

**Không có trong lộ trình:** giao dịch tiền thật. Cấp vốn 4+ (thang vốn v0.1) chỉ được xem xét khi GĐ 3 cho **alpha có t ≥ 2 sau ≥ 12 tháng paper trading** và Owner quyết định.

---

# PHẦN IX — CÁC CHẾ ĐỘ HỎNG VÀ CÁCH PHÒNG

| Chế độ hỏng | Dấu hiệu | Phòng thủ trong v1.0 |
|---|---|---|
| **LLM bịa nguồn / bịa số** | Claim trích báo cáo không tồn tại | Auditor code kiểm nguồn và số; Fact Layer VERIFIED do code gán |
| **Đóng kịch tuân thủ** | Schema điền đẹp, không kiểm chứng được | Mọi claim quan trọng phải có dự báo chấm được; không có → vô hiệu |
| **Đồng thuận giả (bầy đàn)** | Mọi chuyên gia cùng kết luận | Vòng 1 độc lập; Devil's Advocate riêng có dự báo ngược |
| **Overfitting / đào bới dữ liệu** | Nhiều phát hiện, không cái nào sống ngoài mẫu | Ngưỡng t tăng theo số thử (đã có); shadow trước khi dùng |
| **Tự huyễn về kỹ năng** | Lãi do thị trường chung tăng | Attribution + counterfactual bắt buộc; nhóm đối chứng |
| **Goodhart truyền thông** | CTR tăng, retention giảm, đính chính tăng | Luật duyệt 2 trục (VII.2) |
| **Chi phí API mất kiểm soát** | Hóa đơn tăng đột biến | Budget Governor, trần ngày/tháng, thứ tự cắt |
| **Mất dữ liệu nguồn** | vnstock/Yahoo đổi API | Nhiều nguồn dự phòng; báo lỗi rõ; engine không chạy trên dữ liệu thiếu |
| **Trôi mục tiêu** | Hệ thống tối ưu thứ Owner không muốn | Governor chỉ Owner sửa; review tuần của Owner |
| **Rò xung đột lợi ích** | Media nói về mã đang nắm | Firewall cấu trúc + conflict disclosure tự động |

---

# PHẦN X — BẢNG ĐIỀU KHIỂN CỦA OWNER

Owner không cần đọc code. Owner đọc **một trang mỗi tuần**: `reports/WEEKLY_OWNER.md`

```text
1. SỨC KHỎE HỆ THỐNG      vòng chạy đạt/lỗi · chi phí API tuần/tháng so với trần
2. TỔ CHỨC CÓ THÔNG MINH HƠN KHÔNG?
                          Brier nhóm A vs nhóm B (đối chứng) · xu hướng 4/12 tuần
3. BẢNG ĐIỂM CHUYÊN GIA   từng người: n, Brier skill, calibration, trọng số hiện tại
4. ĐẦU TƯ                 NAV giấy · alpha, t · quyết định chờ duyệt
5. TRI THỨC               bài học mới SUPPORTED chờ Owner đưa lên CANONICAL · bài học bị bác bỏ
6. TÒA SOẠN               bản nháp chờ duyệt · lỗi sự thật · số liệu khán giả
7. CỔNG CHỜ OWNER         mọi việc đang dừng chờ quyết định
```

Lệnh Owner giữ nguyên từ v0.1 (`AUTO HỌC HIỂU HÀNH ĐỘNG`, `TRẠNG THÁI`, `PHẢN BIỆN <id>`, `DUYỆT/TỪ CHỐI <id>`), thêm:
- `NGÂN SÁCH <số>` — đặt trần API tháng
- `ĐỐI CHỨNG` — xem riêng báo cáo nhóm A vs B

---

# PHẦN XI — ĐỐI CHIẾU v0.1 → v1.0

| Mục v0.1 | Giữ / Sửa / Mới trong v1.0 |
|---|---|
| 1 Ba tầng | **Sửa:** Universal Core cụ thể thành 7 primitive |
| 2 Control plane | **Giữ** + Budget Governor |
| 3 Data & Evidence | **Giữ** (engine v0.2) + Fact Layer có trạng thái kiểm chứng |
| 4 Evidence Graph | **Giữ**, hiện thực bằng Source–Evidence–Claim có hash |
| 5 Expert layer | **Sửa:** vai logic/lần gọi vật lý; vòng 1 độc lập; Auditor là code |
| 6 Hypothesis | **Giữ**, bắt buộc kèm Prediction |
| 7 Adversarial | **Giữ**, Devil's Advocate phải dự báo và bị chấm |
| 8 Uncertainty | **Sửa:** calibration đo bằng Prediction Ledger |
| 9–13 Regime/Backtest/Counterfactual/Attribution/Decay | **Giữ** — đã có code v0.2 |
| 14–17 Portfolio/Risk/Decision/Ladder | **Giữ**, Risk Gate là code |
| 18–19, 24, 28 Media | **Giữ** + chấm 2 trục + firewall cưỡng chế bằng cấu trúc + Owner Gate pháp lý |
| 20–21 Memory/Knowledge | **Giữ**, thêm economic memory cho chi phí API |
| 22–23 Meta-learning/Self-repair | **Sửa:** Vòng 3 với shadow procedure |
| 25 Storage | **Sửa:** theo giai đoạn, git trước |
| 26 Contracts | **Giữ 18** + thêm 3: `PREDICTION`, `RESOLUTION`, `PROCEDURE` |
| 27 Workflow | **Giữ**, chi tiết hóa theo ngày (VII.1) |
| 29 Capability maturity | **Giữ**; chỉ được lên VALIDATED khi có dữ liệu thật, không phải giả lập |
| 30 Auto mode | **Giữ**, chạy trên GitHub Actions trong trần ngân sách |
| 31 Safety state | **Giữ** + `api_budget` |
| 32 Kiến trúc cuối | **Giữ** + Prediction Ledger và nhóm đối chứng ở trung tâm |
| — | **Mới:** Prediction Ledger, Scorecard, trọng số chuyên gia, nhóm đối chứng, ba vòng học, ranh giới tất định/diễn giải, runtime topology, bảng hỏng hóc, trang Owner tuần, lộ trình có điều kiện thoát |

---

# KẾT

v0.1 mô tả **một tổ chức nên trông như thế nào**.
v1.0 mô tả **một tổ chức chứng minh mình giỏi lên bằng cách nào**.

```text
MỖI NHẬN ĐỊNH  → PHẢI THÀNH DỰ BÁO
MỖI DỰ BÁO     → PHẢI ĐƯỢC CHẤM
MỖI ĐIỂM SỐ    → QUYẾT ĐỊNH AI ĐƯỢC TIN
MỖI BÀI HỌC    → PHẢI SỐNG SÓT QUA ATTRIBUTION
MỖI QUY TRÌNH  → PHẢI THẮNG QUY TRÌNH CŨ MỚI ĐƯỢC THAY
VÀ CẢ TỔ CHỨC  → PHẢI THẮNG CLAUDE ĐỨNG MỘT MÌNH
               → NẾU KHÔNG, KIẾN TRÚC PHẢI SỬA, KHÔNG PHẢI CON SỐ.
```
