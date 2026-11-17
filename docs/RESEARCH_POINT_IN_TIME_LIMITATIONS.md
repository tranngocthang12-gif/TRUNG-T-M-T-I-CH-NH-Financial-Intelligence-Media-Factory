# Giới hạn point-in-time và cách diễn giải kết quả nghiên cứu

**Trạng thái:** DISCLOSURE / RESEARCH-ONLY. Không thay đổi engine, nguồn giá hay pháp luật dự án.
**Căn cứ:** `engine/data.py`, `engine/adjust.py`, ADR-0006, L-05 và L-06. Ngày rà soát: 2026-11-18.

## Bản chất của dữ liệu hiện tại

- Kho giá 9 cột (`date,ticker,open,high,low,close,volume,observed_at,source`) được ghi tăng dần theo ADR-0006. `observed_at` là ngày hệ thống *quan sát/nhận bản ghi*, không phải bằng chứng giá được công bố tại `date`.
- `load_market(as_of)` hiện lọc `date <= as_of`, nhưng không tái hiện một cách tổng quát bản dữ liệu/phiên bản nguồn và sự kiện quyền mà hệ thống *biết được* ở `as_of`. Dữ liệu lịch sử nhập về sau có thể vẫn được dùng trong backtest tại ngày trước thời điểm nhập.
- `tests/test_no_lookahead.py` kiểm tính nhân quả của feature với dữ liệu giá đã cho; nó không chứng minh toàn bộ nguồn giá, corporate actions, lịch sử thành phần VN30 và báo cáo tài chính đều point-in-time.
- Hai sự kiện quyền TCB và VCB trong `data/corporate_actions.csv` hiện vẫn là `CAN_DOI_CHIEU`; `engine/adjust.py` trên `main` không kiểm tra status này trước khi tự gán `APPLIED`. Các phép thử thực nghiệm dựa trên chuỗi điều chỉnh cần ghi giới hạn này.
- Backtest theo VN30 hiện tại có rủi ro thiên lệch sống sót. ADR-0008 đã được Owner đưa vào `main` qua PR #31 (merge commit `8c4fd4305b8154adda2ea0e1abf4e43cd7b647ab`) và bổ sung nhãn cảnh báo; danh sách VN30 theo từng kỳ vẫn chưa được cung cấp.

## Quy tắc diễn giải

1. **Backtest lịch sử hiện tại = phân tích thăm dò trên dữ liệu tái dựng**, không phải chứng minh kết quả đầu tư tái lập đúng thông tin sẵn có tại từng ngày. Không gọi là fully point-in-time.
2. Không dùng kết quả backtest này làm căn cứ duy nhất kết luận alpha, bật giao dịch, hoặc cấp vốn. Luôn ghi baseline, chi phí, số lần thử, Deflated Sharpe, provenance và các giới hạn dữ liệu.
3. Phân biệt ba thời điểm: (a) giao dịch/sự kiện có hiệu lực (`date`/`effective_at`), (b) công bố với thị trường (`published_at`), (c) hệ thống ghi nhận (`observed_at`). Không suy ra (b) bằng (a), hay (c) bằng (b).
4. Nếu chỉ yêu cầu 'thông tin công khai tại ngày X', sử dụng `published_at <= X` với bằng chứng nguồn; nếu yêu cầu 'hệ thống thực sự biết tại ngày X', phải kiểm `observed_at <= X` và chấp nhận dữ liệu lịch sử nhập sau X sẽ bị loại.
5. Không thay đổi kho gốc, không backfill thời điểm công bố bằng phỏng đoán. Dữ liệu chỉnh sửa phải là bản dẫn xuất có phiên bản, lý do, nguồn và bản kiểm toán.
6. Dự báo LLM vẫn tuân thủ L-05: dự báo prospective, ghi trước hạn giải quyết; không coi backtest giá lịch sử là phép đánh giá năng lực LLM.

## Tiêu chí gỡ cảnh báo trong tương lai

- Có bản hợp đồng dữ liệu và policy point-in-time theo từng loại sử dụng (retrospective nghiên cứu, replay lịch sử biết được, live prospective).
- Có nguồn giá và sự kiện quyền được xác minh với ngày công bố/nhận và hiệu lực; test chặn sự kiện chưa xác minh.
- Có thành phần VN30 theo kỳ và kiểm thử chống survivorship bias.
- Có test end-to-end cho dữ liệu phiên bản lại/quan sát muộn, BCTC công bố muộn, sự kiện quyền sửa sau, và đối chiếu output backtest.
- Từng kết quả nghiên cứu chỉ được nâng nhãn sau khi kiểm chứng lại bằng dữ liệu và phép thử đáp ứng các cổng trên.

**Quyền phê duyệt:** tài liệu này là disclosure, không thay ADR hoặc quyền Owner quyết định merge / nguồn mới / triển khai vốn.
