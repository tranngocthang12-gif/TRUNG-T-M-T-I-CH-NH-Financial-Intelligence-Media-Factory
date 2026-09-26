# ARCHITECTURE v2.2 — TINH HOA & CHUỖI GIÁ TRỊ
**Ngày:** 26/09/2026 · Bổ sung v2.0 + v2.1. Khi mâu thuẫn, theo bản mới nhất.

---

## 1. TINH HOA — lấy gì để hơn khi ai cũng có AI giỏi

Khi mọi người dùng AI, **phân tích thành hàng hóa**: ai cũng hỏi được, câu trả lời giống nhau, và vì thế **đã nằm trong giá**. Lợi thế không thể là "AI của ta thông minh hơn".

### Năm lớp tinh hoa
| # | Tinh hoa | Bộ phận của bộ não tạo ra nó |
|---|---|---|
| 1 | **Biết mình giỏi ở đâu — bằng con số** | Prediction Ledger, Scorecard, bản đồ năng lực |
| 2 | **Không thua đậm** — lãi kép thưởng người sống sót lâu nhất | Risk Gate, thang vốn, Casebook thủ đoạn, mặc định tiền mặt |
| 3 | **Kiên nhẫn** — đánh ở khung thời gian ít người chịu đứng; vốn nhỏ vào được chỗ quỹ lớn không vào | Horizon dài, không chạy theo chỉ số |
| 4 | **Tri thức riêng không AI nào có** — lịch sử dự báo, bài học kiểm chứng, Thư viện VN, điểm uy tín lãnh đạo, quan sát thực địa của Owner | Thư viện T2–T4, Ledger, mục 3 dưới đây |
| 5 | **Kỷ luật cảm xúc** — luật cứng làm thay phần ý chí con người thiếu | Governor, SAFETY_STATE, cổng Owner |

### Tinh hoa trong tinh hoa
> **Thấy sự việc đúng như nó là — kể cả sự thật về chính mình — và hành động kiên định theo đó trong thời gian đủ dài.**
> Người thắng lâu dài không phải người biết nhiều nhất, mà là người **ít tự lừa mình nhất**.

### Nguyên lý vận hành rút ra: LỢI THẾ = KHÁC BIỆT ĐÃ ĐƯỢC CHỨNG MINH
Nhóm đối chứng B (Claude trần, không Thư viện, không bảng điểm) = **đồng thuận của các AI thông thường = điều đã nằm trong giá**.

| Bộ não so với nhóm B | Bảng điểm trong loại tình huống này | Ý nghĩa | Hành động |
|---|---|---|---|
| Đồng ý | — | Không có lợi thế | Không tăng tỷ trọng vì lý do này |
| Khác | Chưa đủ mẫu | Khác nhưng chưa chứng minh = liều | Chỉ SHADOW / ghi Ledger |
| Khác | **Bộ não đúng hơn B có ý nghĩa** | **Lợi thế thật** | Được phép dùng cho quyết định (qua Risk Gate) |
| Khác | Bộ não sai hơn B | Tự tin sai | Hạ trọng số chuyên gia liên quan |

Triển khai: mỗi dự báo chính ghi kèm dự báo của nhóm B cho **cùng câu hỏi**; Scorecard tính riêng **"độ đúng khi bất đồng với B"** — chỉ số quan trọng nhất của cả hệ thống.

---

## 2. CHUỖI GIÁ TRỊ HAI ĐẦU (Owner bổ sung 26/09/2026)

> Thị trường đầu cuối người tiêu dùng, cạnh tranh đầu cuối, và nguồn nguyên liệu **phản ánh ngược lên doanh nghiệp** — trước khi BCTC kịp ghi nhận.

```text
NGUYÊN LIỆU (đầu vào)  →  DOANH NGHIỆP  →  NGƯỜI TIÊU DÙNG (đầu ra)
        └──────── phản ánh ngược: biên lợi nhuận, doanh thu, thị phần ────────┘
                  → xuất hiện trong BCTC 1–2 quý sau
```

BCTC là gương chiếu hậu; hai đầu chuỗi là kính chắn gió.

### Luật phân tích
1. **Mọi tín hiệu phải nối về doanh nghiệp cụ thể bằng tỷ trọng**: % doanh thu từ thị trường đầu ra đó, % giá vốn từ nguyên liệu đó. Không có tỷ trọng → không kết luận mức tác động.
2. **Ghi rõ chiều tác động**: cùng một giá nguyên liệu, bên bán lợi — bên mua thiệt.
3. **Ghi độ trễ**: tồn kho giá cũ, hợp đồng dài hạn, phòng ngừa rủi ro giá.
4. **Hỏi "đã vào giá chưa"**: tín hiệu công khai (giá hàng hóa) thì quỹ cũng thấy; lợi thế lớn nằm ở tín hiệu khó thấy (hành vi người tiêu dùng, cường độ cạnh tranh tại điểm bán).
5. **Biến thành dự báo chấm được**, ví dụ: "giá nguyên liệu X tăng ≥ 15% trong quý → biên gộp doanh nghiệp Y quý sau giảm".

Chi tiết: `library/value_chain/README.md`.

---

## 3. QUAN SÁT THỰC ĐỊA CỦA OWNER — "con mắt ngoài đời"

Owner là người tiêu dùng thật, sống giữa thị trường thật — nguồn dữ liệu mà quỹ lớn phải trả tiền mới có, và **không AI nào có**.

- Owner ghi quan sát vào `library/owner_observations/` theo mẫu (ngày, nơi, điều thấy, doanh nghiệp liên quan, Owner nghĩ nó dẫn tới gì).
- Mỗi quan sát có liên quan tới mã niêm yết → chuyển thành **dự báo** trong Ledger với procedure `owner_field@v1`.
- Chấm như mọi chuyên gia → sau một thời gian Owner biết **con mắt ngoài đời của mình đáng tin đến đâu, ở ngành nào**.
- Chống thiên lệch: một cửa hàng vắng ≠ cả hệ thống vắng; ghi số điểm quan sát, không suy rộng quá mức.

---

## 4. Cập nhật bản đồ năng lực & lộ trình

| Việc | Giai đoạn |
|---|---|
| Bản đồ chuỗi giá trị cho 30 mã (đầu vào + đầu ra + tỷ trọng + độ trễ) trong Dossier | GĐ2 (cùng Dossier) |
| Fact Layer giá hàng hóa chính | GĐ2 |
| Nhật ký quan sát Owner + procedure `owner_field@v1` | GĐ2 |
| Dự báo nhóm B song song + chỉ số "độ đúng khi bất đồng với B" | GĐ4 (cùng nhóm đối chứng) |
| Chỉ báo đầu cuối (bán lẻ, khuyến mãi, thị phần online) — chỉ nguồn hợp pháp | GĐ3 |
