# FPT — báo cáo nghiên cứu thăm dò có dấu vết kiểm chứng

**Trạng thái:** RESEARCH-ONLY / ĐÃ TÍNH LẠI TRÊN GITHUB; CHƯA CÓ BẰNG CHỨNG ĐỂ KHUYẾN NGHỊ GIAO DỊCH.
**Ngày giá cuối trong kho:** 2026-11-16. **Ngày tính:** 2026-11-18. Không xem giá này là báo giá hiện thời.
**Mã:** FPT, HOSE. **Đơn vị:** VND/cổ phiếu trên chuỗi Yahoo quan sát và chuỗi phân tích đã điều chỉnh; KHÔNG chứng minh các giá trị lịch sử là giá khớp lệnh thật.

## Provenance — hai commit khác nhau, không nhầm lẫn

- **Commit dữ liệu nền (main sau PR #35):** `400de5775f6d832ff453ccc2d88c91eb35936d1a`. Kho dữ liệu legacy `data/store/prices.csv.gz` + các tệp tháng là dữ liệu đọc; nhãn nguồn của FPT là `yahoo`.
- **Commit bổ sung công cụ và workflow phân tích:** `8e7a41fd8e5f1fbeac68fb30386b353a87a9d69a` trên nhánh `analysis/fpt-readonly-20261118`, diff so với base chỉ gồm `tools/fpt_readonly_report.py` và `.github/workflows/fpt_readonly.yml`. Không phải commit đã có trên main.
- **GitHub Actions:** [FPT Readonly Analysis, run 44249663868](https://github.com/tranngocthang12-gif/TRUNG-T-M-T-I-CH-NH-Financial-Intelligence-Media-Factory/actions/runs/44249663868), `push` vào nhánh phân tích, `head_sha=8e7a41fd8e5f1fbeac68fb30386b353a87a9d69a`, kết quả `completed/success` lúc 2026-11-18 06:13:15 UTC (13:13:15 giờ Việt Nam). Job `134616946504` chạy `python -m tools.fpt_readonly_report`, sau đó `test -z "$(git status --porcelain)"` SUCCESS. Workflow `permissions: contents: read`; không tải giá mới, không sửa engine/ledger/laws hoặc ghi kết quả lên main.
- **Mốc quan sát FPT trong raw store:** `observed_at=2026-11-16 19:45:37.328665` (timestamp không gắn timezone trong file), `source=yahoo`; 2.814 hàng dữ liệu FPT.
- **Tính toán:** `engine/data.py::load_store()`, `load_market()` và `engine/adjust.py`; các cửa sổ đều kết thúc tại ngày dữ liệu cuối trong kho, không phải phát tín hiệu model.

> Chú ý: cả `raw_close` và `close` ở phiên cuối đều là 49.400. `raw_close` chỉ nghĩa là **giá Yahoo được lưu trước bước điều chỉnh của engine**, **không** có nghĩa unadjusted official exchange close. Các giá lịch sử trước split có thể đã được Yahoo điều chỉnh từ trước. MA/return/drawdown lấy từ chuỗi `load_market()['close']`.

## Bằng chứng định lượng tại 16/11/2026

| Chỉ tiêu | Giá trị | Phương pháp |
|---|---:|---|
| Yahoo close cuối cùng đã lưu | 49.400 VND | `data.load_store()`; chưa đối chiếu bảng giá HOSE |
| Biến động 20 phiên | −13,485% | `close[-1]/close[-21] - 1` |
| Biến động 60 phiên | −23,894% | Chuỗi giá điều chỉnh của engine |
| Biến động 120 phiên | −25,460% | Chuỗi giá điều chỉnh của engine |
| Biến động 252 phiên | −44,059% | Chuỗi giá điều chỉnh của engine |
| MA20 | 53.002,50 | Trung bình 20 phiên, giá phân tích điều chỉnh |
| MA60 | 60.042,95 | Trung bình 60 phiên, giá phân tích điều chỉnh |
| MA120 | 61.990,42 | Trung bình 120 phiên, giá phân tích điều chỉnh |
| So với MA20 / MA60 / MA120 | −6,80% / −17,73% / −20,31% | Giá cuối chia cho MA − 1 |
| Khối lượng TB20/TB60 | 1,450 lần | Trên `load_market()['volume']` |
| Volatility năm hóa, 20 phiên | 37,849% | Std lợi nhuận đơn 20 phiên × √252 |
| Max drawdown, 60 phiên | −27,060% | Từ đỉnh đến đáy trong cửa sổ |
| Max drawdown, 252 phiên | −48,079% | Từ đỉnh đến đáy trong cửa sổ |

**Xu hướng quan sát:** 49.400 < MA20 < MA60 < MA120; FPT đang yếu xét trên chuỗi giá và mốc dữ liệu đã lưu. Đây không phải dự báo tiếp diễn xu hướng hoặc lệnh bán.

## Sức mạnh tương đối — KHÔNG phải benchmark VN30 chính thức

Cùng ngày kết thúc, cùng N phiên và dùng 30 mã trong cấu hình `universe_basis=CURRENT`, áp ngược danh sách hiện hành cho lịch sử. Có **thiên lệch sống sót** (ADR-0008) và không dùng lịch sử thành phần VN30 theo kỳ.

| Kỳ | FPT | TB đều 30 mã | Xếp hạng | FPT kém TB (điểm %) |
|---|---:|---:|---:|---:|
| 20 phiên | −13,485% | −0,555% | 30/30 | 12,930 |
| 60 phiên | −23,894% | −4,820% | 30/30 | 19,074 |
| 120 phiên | −25,460% | −7,182% | 29/30 | 18,278 |
| 252 phiên | −44,059% | −1,119% | 30/30 | 42,940 |

Không gọi TB đều này là chỉ số VN30/VN-Index được công bố; không suy ra khả năng tạo alpha từ thứ hạng trên.

## Chất lượng dữ liệu và điểm phải kiểm chứng

- Engine đánh dấu **0 cờ giá FPT trong 20/60/120/252 phiên gần nhất**, nhưng trong toàn lịch sử có **1 cờ FPT** ở 2021-02-17; không có cờ không có nghĩa nguồn giá đã được HOSE xác nhận.
- **42 corporate actions FPT từ Yahoo**, tất cả có `source_status=TU_DONG`: **21 `APPLIED`**, **11 `DA_NAM_TRONG_GIA_NGUON`**, **10 `NGOAI_DU_LIEU`**. Những sự kiện này không được xem là đã xác minh chỉ vì engine phân nhóm.
- **Rủi ro trọng yếu trong chính cửa sổ 252 phiên:** `data/derived/yahoo_actions.csv` có `FPT,2026-09-21,stock_split,1.1,source=yahoo,source_status=TU_DONG`. `data/derived/adjustment_factors.csv` ghi `raw_return=0.0`, `status=DA_NAM_TRONG_GIA_NGUON`, `price_factor=1.0`, `split_factor=1.0`. Engine **suy đoán** việc chia cổ phiếu đã nằm sẵn trong lịch sử giá nhà cung cấp; đây **không phải kiểm chứng CBTT gốc**.
- Vì vậy lợi nhuận 252 phiên, MA dài và drawdown có thể bị tác động bởi quy ước split-adjustment của Yahoo. Cần đối chiếu công bố gốc FPT và giá giao dịch chính thức trước khi coi các mức này là kết quả đầu tư khả dụng.
- `yfinance.download(auto_adjust=False)` không chứng minh cột `Close` là giá giao dịch chưa từng điều chỉnh theo chia tách. Từ `close` có số lẻ hoặc ngày hưởng quyền chỉ có thể nhận diện nghi vấn cần đối chiếu; chưa xác nhận độc lập dữ liệu cụ thể của Sở.
- `state/PROJECT_STATE.yaml` nêu rõ Yahoo là **nguồn tạm có lỗi**, nguồn giá chính thức chưa được Owner phê duyệt; `deployment_level=0`. Dữ liệu này cũng **không fully point-in-time** (xem `docs/RESEARCH_POINT_IN_TIME_LIMITATIONS.md`).
- Các con số giá/đánh giá thị trường được trích dẫn ở bên ngoài kho chưa được độc lập kiểm tra ở đây; không dùng lời thuật báo chí thay cho bản giá sở giao dịch.

## Phân tích cơ bản và kết luận

`library/SOURCE_MANIFEST.json` hiện chưa ghim BCTC FPT gốc; không phát biểu doanh thu, lợi nhuận, EPS, P/E, định giá hay giá mục tiêu. Không tự khai nguồn, không thêm tài liệu vào thư viện khi chưa có URL/tài liệu gốc theo quy trình.

**Kết luận có giới hạn:** trên chuỗi giá Yahoo đã lưu đến 16/11/2026, xu hướng FPT giảm và sức mạnh tương đối yếu trong 30 mã đang cấu hình. Dữ liệu chưa đủ nguồn chính thức để kết luận giá cổ phiếu bị định giá thấp/cao, tạo alpha hay có điểm mua/bán. Không ghi Ledger và không giao dịch thật.

## Trạng thái nghiệm thu

Báo cáo này là **bản ghi nghiên cứu dự thảo**, không phải kết quả dự báo L-05, không phải model ACTIVE. Khi đề xuất đưa vào `main`, cần kiểm tra đúng commit tài liệu/công cụ theo L-09 và quyết định Owner theo L-10. Không mở lại những đầu việc đã đóng trong ADR-0010.
