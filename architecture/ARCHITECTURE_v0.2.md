# ARCHITECTURE v0.2 — HAI BỘ NÃO

v0.1 là bộ luật và quy trình. v0.2 thêm một **bộ não học máy chạy thật**, tự vận hành hằng ngày trên GitHub Actions.

```text
                        HUMAN OWNER
                             │
                    FINANCIAL GOVERNOR  (governance/ — chỉ Owner sửa)
                             │
          ┌──────────────────┴──────────────────┐
          ▼                                     ▼
   BỘ NÃO LẬP LUẬN (LLM)                 BỘ NÃO HỌC MÁY (engine/)
   đọc BOOT.md, phản biện,               chạy tự động mỗi ngày,
   giải thích, soạn quyết định           đo lường, kiểm định, ghi nhận
          │                                     │
          └──────────────► REPO ◄───────────────┘
                (trạng thái, tri thức, nhật ký = bộ nhớ chung)
```

Nguyên tắc phân quyền: **số liệu quyết định cái gì đúng; LLM chỉ phản biện và giải thích.** LLM không được nâng hạng một phát hiện mà engine chưa kiểm định.

## Vòng học hằng ngày (`engine/run_cycle.py`)

```text
1  DATA        vnstock → kho append-only, giữ bản quan sát đầu tiên
2  FEATURES    13 đặc trưng / 5 họ, chuẩn hóa xếp hạng chéo, test chống look-ahead
3  REGIME      xu hướng × biến động của chỉ số đại diện
4  RESEARCH    meta-learning chọn phương pháp → đề xuất giả thuyết → walk-forward có embargo
               → chi phí VN → ngưỡng t tăng theo tổng số thử → cổng 12 tháng gần nhất
5  PROMOTION   WEAK / SUPPORTED / STRONG / REGIME_SPECIFIC → knowledge/candidates + model registry
6  LIVE        mô hình còn sống dự báo cho hôm nay (ghi lại TRƯỚC khi biết kết quả)
7  DECAY       so dự báo cũ với kết quả thật → ACTIVE / DEGRADING / PAUSED / INVALIDATED
8  PAPER       quyết định phiên d, khớp phiên d+1, lô 100, phí + thuế + trượt giá
9  ATTRIBUTION tách beta khỏi alpha; so với "không làm gì" và chỉ số
10 REPORT      reports/cycle_<ngày>.md + state/ENGINE_STATE.json
11 LLM REVIEW  (tùy chọn) Devil's Advocate cho phát hiện mới → research/reviews/
```

## Ba tầng học

| Tầng | Học cái gì | Bằng chứng |
|---|---|---|
| Học từ dữ liệu | Quy luật nào dự báo được lợi nhuận vượt trội | Walk-forward ngoài mẫu |
| Học từ thực tế | Quy luật nào còn sống | Dự báo đã ghi trước, đối chiếu sau |
| Học cách học | Phương pháp nghiên cứu nào sinh phát hiện đứng vững | Thompson sampling trên tỷ lệ sống sót |

## Các chốt chống tự lừa mình

- Nhãn bắt đầu ở close t+1; train kết thúc trước test `horizon+1` phiên.
- Ngưỡng Bonferroni: càng thử nhiều, càng phải mạnh.
- Phải dương ở ≥ 60% fold và trong 12 tháng gần nhất.
- Giao dịch giấy khớp lệnh trễ một phiên.
- Không đủ 12 lần tái cơ cấu thì không kết luận kỹ năng.
- Không có mô hình ACTIVE → mặc định giữ tiền mặt.
- `knowledge/canonical/` vẫn chỉ Owner chuyển vào.

## Kết quả diễn tập (dữ liệu giả lập, `tests/demo_synthetic.py`)

Cài sẵn quy luật động lượng 60 phiên, đảo chiều ngày 16/10/2024:
- 16 thử đầu → 4 mô hình SUPPORTED, đều thuộc họ xu hướng/động lượng.
- Sau khi quy luật đảo: hạ 8 mô hình trong khoảng 25/12/2024 – 04/02/2025 (trễ 2–3 tháng do nhãn 20 phiên).
- Cuối kỳ: 0 ACTIVE, 9 DEGRADING, 6 PAUSED → giữ tiền mặt.
- Paper +29,9% vs chỉ số +22,5%, beta 1,0, alpha t = 0,41 → **"chưa phân biệt được với may mắn"**.

## Giới hạn đã biết

- Kết nối vnstock chưa kiểm chứng với dữ liệu thật (API bên thứ ba có thể đổi).
- Giá lịch sử tải bổ sung là giá đã điều chỉnh của nhà cung cấp → point-in-time chỉ đảm bảo từ ngày bắt đầu thu thập.
- Chưa có dữ liệu cơ bản (BCTC), vĩ mô, tin tức — mới là tầng giá/khối lượng.
- Mô hình cũ vẫn có thể được thăng hạng khi backtest dài bị chi phối bởi giai đoạn trước; tầng DECAY là lưới chặn cuối.
- Universe VN30 hiện tại → có survivorship bias (danh sách hôm nay, không phải danh sách lịch sử).
