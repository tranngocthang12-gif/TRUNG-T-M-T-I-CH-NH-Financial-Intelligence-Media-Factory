# ARCHITECTURE v2.1 — BỔ SUNG VÀO v2.0
**Ngày:** 26/09/2026 · **Nguồn:** các yêu cầu Owner nêu trong phiên làm việc + rà soát điểm thiếu của kiến trúc sư trưởng.
**Quan hệ:** v2.1 bổ sung, không thay thế v2.0. Khi mâu thuẫn, theo v2.1.

---

## 1. Những điều Owner đã nêu — nay thành luật của bộ não

| # | Owner nêu | Ghi vào đâu |
|---|---|---|
| 1 | Bộ não phải **học chuyên sâu** như dự án Phật học học Kinh Trung Bộ, rồi **nhập vai chuyên gia**, nói ngôn ngữ đời sống nhưng giữ đúng bản chất | v2.0 (Thư viện, Học viện, Phòng thi, Nhập vai) |
| 2 | Đầu tư cần **8 nhóm thông tin** | `library/INFORMATION_MAP.md` |
| 3 | **Chính trị, chính sách, pháp luật, cạnh tranh địa chính trị** có ảnh hưởng mạnh | `library/vietnam/policy/`, chuyên gia Macro/Policy |
| 4 | Hệ thống phải **tự biết mình thiếu gì** khi Owner không nhắc | Mục 4: Blind-Spot Detector |
| 5 | **Thời đại AI, thông tin chậm là thua** | Mục 3: Ba tốc độ |
| 6 | **Ảnh hưởng của người nổi tiếng** | Mục 5: Influence & Narrative |
| 7 | Chơi ảo thực chiến | Mục 7: nguồn dữ liệu & sân chơi |

---

## 2. Rà soát — những gì còn thiếu (ngoài các điều Owner nêu)

| Mảng thiếu | Vì sao quan trọng ở VN | Xử lý |
|---|---|---|
| **Lịch sự kiện** (ĐHCĐ, GDKHQ, công bố KQKD, đáo hạn phái sinh, cơ cấu VN30/ETF, xét nâng hạng FTSE/MSCI) | Giá biến động quanh các mốc biết trước | `fact/calendar.jsonl` + chuyên gia Event |
| **Dòng tiền chỉ số & ETF** | Quỹ ngoại đảo danh mục kéo giá hàng loạt | Theo dõi kỳ cơ cấu, danh sách vào/ra |
| **Nguồn cung cổ phiếu mới** (IPO lớn, niêm yết mới, phát hành thêm) | Hút thanh khoản khỏi phần còn lại | Mục Event + Casebook pha loãng |
| **Margin toàn thị trường & tâm lý nhà đầu tư cá nhân** (số tài khoản mở mới, thanh khoản) | Margin cao + tâm lý hưng phấn → rủi ro bán tháo dây chuyền | Chỉ số Sentiment trong Regime |
| **Giá hàng hóa** (thép, dầu, phân bón, cao su, cà phê, gạo) | Quyết định lợi nhuận nhiều ngành | Fact Layer hàng hóa |
| **Lãi suất tiền gửi, giá vàng, bất động sản** — kênh cạnh tranh với chứng khoán | Tiền chảy giữa các kênh | Chuyên gia Macro |
| **Hệ sinh thái tập đoàn & sở hữu chéo** | Rủi ro lan truyền trong nhóm công ty liên quan | Dossier: bản đồ bên liên quan |
| **Thoái vốn Nhà nước (SCIC, bộ ngành)** | Sự kiện định giá lại lớn | Lịch Event |
| **Lịch chính trị** (đại hội, kỳ họp Quốc hội, nhân sự cấp cao) | Chính sách lớn gắn với các mốc này | Lịch Event + Policy |
| **Mùa vụ & ngày lễ** (Tết, cuối quý, chốt sổ) | Hành vi dòng tiền theo mùa | Feature định lượng |
| **Thị trường quốc tế qua đêm** (Mỹ, châu Á, hợp đồng tương lai) | Ảnh hưởng phiên mở cửa | Fact Layer quốc tế |
| **Khí hậu & thời tiết** (El Niño, hạn mặn) | Thủy điện, nông nghiệp, thủy sản | Chuyên gia Macro (mức thấp) |
| **Rủi ro vận hành thị trường** (lỗi hệ thống sàn, nghẽn lệnh) | Không bán được khi cần | Risk Gate |
| **Hồ sơ Owner** (nhóm thông tin số 1) | Mọi quyết định phụ thuộc mục tiêu & khẩu vị rủi ro | `governance/OWNER_PROFILE.md` |

---

## 3. BA TỐC ĐỘ — "thông tin chậm là thua"

**Sự thật cần nói rõ:** hệ thống này **không thể thắng về tốc độ** so với quỹ giao dịch tần suất cao, người có thông tin nội bộ, hay tự doanh có đường truyền riêng. Ở cuộc đua mili-giây, nhà đầu tư cá nhân luôn thua.
Nhưng "chậm là thua" vẫn đúng theo nghĩa khác: **biết tin xấu muộn hơn đám đông vài giờ, vài ngày** là mất tiền. Vì vậy thiết kế ba làn tốc độ, mỗi làn một mục tiêu:

| Làn | Tần suất | Việc | Mục tiêu | Chạy ở |
|---|---|---|---|---|
| **NHANH — Cảnh báo** | 15–30 phút trong giờ giao dịch | Quét tin, công bố thông tin, biến động giá/khối lượng bất thường của mã đang theo dõi; khớp với Casebook | **Không bị bất ngờ** với rủi ro (không nhằm lướt sóng) | GitHub Actions (tất định, miễn phí) → tạo **GitHub Issue** → GitHub tự gửi email/thông báo điện thoại cho Owner |
| **NGÀY — Phân tích** | 16:30 mỗi ngày giao dịch | Vòng học đầy đủ, chuyên gia dự báo, Ledger | Quyết định có kỷ luật | Actions (hiện có) |
| **SÂU — Học** | Khi Owner ra lệnh | AUTO HỌC, viết Thư viện, soạn đề | Hiểu sâu hơn đám đông | Claude Code / chat (gói Max) |

Giới hạn kỹ thuật: lịch chạy của GitHub Actions có thể trễ vài phút đến hàng chục phút khi hệ thống GitHub bận; làn NHANH vì vậy là "nhanh hơn đọc báo buổi tối", không phải thời gian thực.

**Lợi thế thật của hệ thống không phải tốc độ mà là:** đọc được nhiều nguồn cùng lúc, không bỏ sót, không hoảng loạn, và có bảng điểm cho biết loại tin nào thật sự làm giá thay đổi.

---

## 4. BLIND-SPOT DETECTOR — tự biết mình thiếu gì

Trả lời câu hỏi Owner: *"Nếu mình không nhắc, hệ thống có tự biết không?"* — có cơ chế này thì **tự phát hiện và đề xuất**, Owner duyệt.

```text
NGUỒN 1 — HỌC TỪ SAI:     dự báo sai nặng → gom theo loại sự kiện trong cửa sổ dự báo
                           → cụm sai không có năng lực tương ứng = ĐIỂM MÙ
NGUỒN 2 — QUÉT CHỦ ĐỀ:     chủ đề xuất hiện nhiều trong tin 30 ngày qua
                           − chủ đề đã có trong Thư viện = ĐIỂM MÙ
NGUỒN 3 — CHUẨN NGHỀ:      so bản đồ năng lực với khung kiến thức nghề phân tích đầu tư
                           (định kỳ quý, chạy trong phiên AUTO HỌC)
NGUỒN 4 — OWNER:           mọi điều Owner nêu mà chưa có trong kiến trúc → ghi ngay vào mục 1

→ reports/BLIND_SPOTS.md: điểm mù, bằng chứng, mức ảnh hưởng ước tính, đề xuất (nguồn dữ liệu / Thư viện / chuyên gia)
→ Owner duyệt → vào academy/competency_map.yaml → AUTO HỌC lấp
```

Giới hạn: rủi ro **chưa từng xảy ra** không học được từ quá khứ — vẫn cần con người.

---

## 5. INFLUENCE & NARRATIVE — ảnh hưởng của người nổi tiếng

### 5.1 Ba nhóm người ảnh hưởng

| Nhóm | Ví dụ loại người | Kênh tác động | Cách xử lý |
|---|---|---|---|
| **Nhà hoạch định chính sách** | Lãnh đạo Chính phủ, NHNN, Bộ Tài chính, UBCKNN; Chủ tịch Fed, lãnh đạo các cường quốc | Phát biểu → kỳ vọng chính sách → cả thị trường | Chỉ ghi **phát biểu chính thức có nguồn**; phân tích như chính sách (kênh truyền dẫn, kịch bản) |
| **Lãnh đạo doanh nghiệp** | Chủ tịch, CEO các tập đoàn niêm yết | Cam kết kế hoạch, tin M&A, mua/bán cổ phiếu | Ghi lời hứa → **chấm độ giữ lời** (kế hoạch vs kết quả thực) → điểm uy tín vào Dossier |
| **Người có ảnh hưởng trên mạng (KOL/"chuyên gia" MXH)** | Người điều hành nhóm Zalo/Telegram/Facebook, kênh YouTube/TikTok chứng khoán | Tâm lý đám đông, "phím hàng", đẩy giá mã nhỏ | Là **tín hiệu rủi ro**, không phải nguồn sự thật; Casebook "phím hàng – thổi giá" |

### 5.2 Luật xử lý

1. **Lời nói không phải sự thật.** Phát biểu của bất kỳ ai vào Fact Layer ở trạng thái "tuyên bố của X", không phải "sự kiện đã xảy ra".
2. **Đo uy tín bằng thành tích:** với lãnh đạo doanh nghiệp và người phát biểu công khai thường xuyên, Ledger ghi lời dự báo/cam kết, chấm khi đến hạn → **điểm độ tin theo từng người**, cập nhật theo thời gian.
3. **Đám đông hưng phấn là rủi ro:** một mã được nhắc đột biến trên kênh đại chúng + khối lượng tăng mạnh không có tin chính thức → cảnh báo làn NHANH, đối chiếu Casebook.
4. **Chỉ dùng nội dung công khai, hợp pháp.** Không thu thập dữ liệu cá nhân, không theo dõi người không phải nhân vật công chúng, tuân thủ điều khoản của từng nền tảng. Giai đoạn đầu: lấy qua **báo chí đưa tin** về phát biểu (có nguồn), chưa quét trực tiếp mạng xã hội.
5. **Trung lập:** phân tích tác động kinh tế của phát biểu, không đánh giá chính trị hay cá nhân.

---

## 6. CHÍNH TRỊ – CHÍNH SÁCH – PHÁP LUẬT – ĐỊA CHÍNH TRỊ

Chi tiết tại `library/vietnam/policy/README.md`. Nguyên tắc:
- Nguồn chính thức trước (Công báo, Cổng TTĐT Chính phủ, NHNN, Bộ Tài chính, UBCKNN); bình luận chỉ là tham khảo.
- Theo dõi **vòng đời văn bản**: dự thảo → lấy ý kiến → thông qua → hiệu lực — thị trường phản ứng ở từng mốc.
- Phân tích theo **kênh truyền dẫn**: chính sách → ngành → doanh nghiệp → chỉ tiêu tài chính.
- **Kịch bản có xác suất** cho sự kiện địa chính trị, ghi vào Ledger để chấm.
- Chuyên gia mới: **policy@v1** (tách khỏi Macro khi đủ dữ liệu).

---

## 7. NGUỒN DỮ LIỆU & SÂN CHƠI ẢO

Danh mục đầy đủ, có trạng thái pháp lý: `governance/DATA_SOURCES.yaml`. Tóm tắt:
- **Được dùng tự động:** API dữ liệu SSI FastConnect / DNSE (cần tài khoản), RSS báo chí, website công bố thông tin chính thức.
- **Chỉ tham khảo bằng mắt:** Investing.com (điều khoản cấm sao chép, dữ liệu không đảm bảo cho giao dịch).
- **Sân chơi ảo có bên thứ ba xác nhận:** Đấu trường Vietstock, Vnstockgame — Owner nhập lệnh tay theo `paper/decisions.csv`.
- **Paper trading nội bộ:** tự động, hiện có.
- **API đặt lệnh thật:** cấm cho tới khi đạt cấp vốn 4 và Owner duyệt.

---

## 8. Lộ trình cập nhật (chèn vào lộ trình v2.0)

| Việc | Giai đoạn | Làn |
|---|---|---|
| OWNER_PROFILE, DATA_SOURCES, INFORMATION_MAP | Ngay (tài liệu) | HỌC |
| Làn NHANH: cảnh báo qua GitHub Issue | GĐ2 | CHỨNG MINH |
| Lịch sự kiện `fact/calendar.jsonl` | GĐ2 | CHỨNG MINH |
| Blind-Spot Detector nguồn 2 (quét chủ đề) | GĐ2 | CHỨNG MINH |
| Thư viện Policy + Influence + Casebook "phím hàng" | GĐ3 | HỌC |
| Điểm uy tín lãnh đạo doanh nghiệp (lời hứa vs kết quả) | GĐ3 | CHỨNG MINH |
| Blind-Spot nguồn 1 (học từ sai) | Khi Ledger có ≥ 200 dự báo đã chấm | CHỨNG MINH |
| policy@v1 | GĐ4 | CHỨNG MINH |
