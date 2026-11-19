# P1 — Sự kiện quyền TCB/VCB (Issue #33): nguyên nhân đã xác minh và cổng bằng chứng — 19/11/2026

Phạm vi: nguyên nhân, đo trên dữ liệu thật của `main` `0f42220`, và cổng kiểm chứng độc lập. KHÔNG sửa `engine/adjust.py`, KHÔNG sửa kho raw, KHÔNG đổi `data/corporate_actions.csv`, KHÔNG chuyển nguồn sang DA_KIEM_CHUNG. **Issue #33 chưa xong.**

## 1. Vì sao CAN_DOI_CHIEU vẫn thành APPLIED (đã tái hiện bằng test)

`engine/adjust.py` `build_events` chép cột `source_status` sang kết quả nhưng không dùng nó. Một sự kiện cổ phiếu thành APPLIED khi: tỷ lệ > 0; không phải sự kiện Yahoo có `observed_at` lớn nhất của các dòng trước ngày đó ≥ `ex_date`; và lợi suất đã nhân tỷ lệ nằm trong biên độ giá. `tests/test_verified_adjust.py::test_root_cause_source_status_does_not_decide_applied` cho bốn giá trị `source_status` (CAN_DOI_CHIEU, DA_KIEM_CHUNG, TU_DONG, CHUA_XAC_MINH) cùng ra APPLIED. Nghĩa là biến động giá khớp tỷ lệ được dùng làm bằng chứng, trái với ADR-0009 điều 2 và 3.

Tại `ex_date` trong `data/corporate_actions.csv`, hai dòng nhập tay (TCB `2024-06-11`, VCB `2025-03-03`) ghi ngày chuỗi giá gốc gãy trong kho, không ghi ngày chính thức. Ngày chính thức theo bản gốc HOSE ghim trong PR #54 (chưa gộp): TCB `2024-06-20`, VCB `2025-03-12`, mỗi mã lệch 7 phiên. Mỗi mã có hai dòng cho cùng một bản gốc: dòng nhập tay (APPLIED, ngày gãy) và dòng Yahoo (ngày chính thức, DA_NAM_TRONG_GIA_NGUON). Quy tắc DA_NAM_TRONG_GIA_NGUON chỉ nhìn `observed_at` lớn nhất, không kiểm từng dòng giá.

## 2. Vì sao không sửa `adjust.py` bằng một bản vá cổng đơn lẻ

Đo trên bản sao trong bộ nhớ (không ghi đĩa): đổi ngày hai dòng nhập tay sang ngày chính thức làm VCB và TCB chuyển APPLIED → KHONG_KHOP. Hệ số 1,495 và 2,0 không còn được áp vào giá trước sự kiện:

| Mã | Số phiên có giá điều chỉnh khác chuỗi hiện hành | Khoảng ngày | Chênh lớn nhất |
|---|---|---|---|
| VCB | 2.360 | 04/01/2016 – 28/02/2025 | 31.752,57 |
| TCB | 1.562 | 04/06/2018 – 10/06/2024 | 18.103,60 |

Lợi suất 20, 60, 120, 252 phiên tại 16/11/2026 của hai mã không đổi vì cửa sổ không chạm hai sự kiện. Mọi cửa sổ dài hơn, hoặc tính tại ngày trước đó, bị đổi. Bản vá cổng làm mất hệ số này sẽ diễn giải sai lịch sử.

## 3. Cổng kiểm chứng độc lập (thêm mới, chưa nối vào vòng học)

`engine/verified_adjust.py` dựng chuỗi `verified-adjusted` riêng. Một sự kiện cổ phiếu chỉ vào chuỗi khi đủ: bản gốc ghim (`source_id`, url, issuer, path, sha256 đều là chuỗi không rỗng; tệp tồn tại, sha256 và số byte khớp); loại sự kiện trên văn bản trùng đúng loại engine ghi (`stock_split` khác `stock_dividend`); ngày công bố có, không muộn hơn ngày cắt `as_of`, sớm hơn ngày không hưởng quyền; tỷ lệ in trên văn bản là số hữu hạn dương và trùng tỷ lệ sự kiện; ngày giao dịch engine áp trùng ngày giao dịch của ngày không hưởng quyền chính thức; không có ngày áp thứ hai cho cùng bản gốc (nhận dạng theo cả `source_id` lẫn sha256 của tệp); trạng thái engine nằm trong danh sách cho phép `APPLIED` / `DA_NAM_TRONG_GIA_NGUON` (mọi trạng thái khác, kể cả trạng thái chưa biết, bị cách ly). Không đạt: cách ly (không vào hệ số) và đánh dấu TAINTED các ô giá của mã đó trước ngày giao dịch. Cổng không đổi ngày hộ và không suy ngày từ bước nhảy giá. Cổ tức tiền mặt chưa có bằng chứng ghim nên chưa được xét; chuỗi này không điều chỉnh cổ tức tiền mặt.

`tools/build_verified_derivation.py` ghi bản dẫn xuất ra `--out`. `--out` phải nằm NGOÀI kho (cả thư mục mã lẫn `TTC_HOME`, kể cả `reports/`, kể cả đi vòng qua liên kết tượng trưng) và phải CHƯA tồn tại; thư mục được tạo nguyên tử và từng tệp mở ở chế độ tạo-mới, nên không có đường ghi đè bản đã xuất (ADR-0009 điều 6). Từ chối thì thoát mã 2, không tạo gì. Tệp ghi ra: `manifest.json` (derivation_id, hash kho raw, mã commit, hash cấu hình, hash sự kiện quyền, bản gốc, phạm vi hiệu lực RETROSPECTIVE), `events_verification.csv`, `taint_by_ticker.csv`, `before_after.md`. Cùng đầu vào cho cùng từng byte.

## 4. Kết quả đo trên dữ liệu thật (as_of 16/11/2026)

| Đầu vào | Sự kiện cổ phiếu | Vào chuỗi kiểm chứng | Ô giá bị cách ly trong 252 phiên gần nhất |
|---|---|---|---|
| `main` (chưa có bản gốc ghim) | 151 | 0 | 34,5% |
| `main` + bản gốc của PR #54 (VCB, TCB, FPT) | 151 | 0 | 34,5%, 17/30 mã |

Với bản gốc của PR #54: TCB `2024-06-11` và VCB `2025-03-03` bị CACH_LY_LECH_NGAY (lệch −7 phiên). Ba dòng Yahoo ở đúng ngày chính thức (TCB `2024-06-20`, VCB `2025-03-12`, FPT `2026-09-21`) bị CACH_LY_LOAI_SU_KIEN_LECH: Yahoo ghi `stock_split`, cả ba văn bản HOSE ghi `stock_dividend`. 121 sự kiện cổ phiếu chưa có bản gốc nào.

Bản đầu của PR này (`ec47dc8`) báo 1 sự kiện vào chuỗi (FPT) và 31,7%. Con số đó sai: FPT được xác minh nhờ cổng bỏ qua loại sự kiện (phát hiện MEDIUM-1 của phản biện L-09). Cổng không đổi loại hộ. Muốn FPT vào chuỗi kiểm chứng thì cần một dòng sự kiện ghi đúng loại theo văn bản, qua PR có Owner (ADR-0009 điều 7); PR này không sửa `data/corporate_actions.csv`.

Khoảng trống mới: engine đang áp tự động ba chia tách Yahoo gần nhất, không có bản gốc nào ghim: TPB `2026-10-02` (tỷ lệ 1,15), HDB `2026-10-09` (1,30), TCB `2026-10-29` (1,50). Tại 16/11/2026 cả ba nằm trong cửa sổ 60, 120 và 252 phiên, riêng TCB còn nằm trong cửa sổ 20 phiên. Lợi suất của ba mã này ở các cửa sổ đó phụ thuộc vào ba tỷ lệ chưa kiểm; chênh giữa chuỗi hiện hành và chuỗi kiểm chứng lên tới 0,32 (20 phiên) và 0,34 (60 phiên).

## 5. Khắc phục phản biện L-09 (ChatGPT, trên `ec47dc8`)

| Phát hiện | Sửa | Test đối kháng (`tests/test_verified_adjust.py`, nhóm `test_m*`) |
|---|---|---|
| MEDIUM-1: loại sự kiện không khớp vẫn được xác minh | `_match` nhận loại sự kiện, ưu tiên văn bản cùng loại; `_judge` cách ly `CACH_LY_LOAI_SU_KIEN_LECH` khi loại khác | `stock_split` ↔ `stock_dividend` cả hai chiều; ca Yahoo đã điều chỉnh sẵn (giống FPT thật); ưu tiên đúng loại |
| MEDIUM-2: thiếu danh sách cho phép trạng thái engine | `VERIFIABLE = (APPLIED, DA_NAM_TRONG_GIA_NGUON)`; ngoài danh sách → `CACH_LY_TRANG_THAI_ENGINE_KHONG_HOP_LE`; `in_verified_chain` đòi cả trạng thái kiểm OK lẫn trạng thái engine trong danh sách; tỷ lệ phải là số hữu hạn dương; trạng thái chưa biết cũng nhiễm ô | tỷ lệ 0 + `official_ratio=0` (ca phản biện nêu); LOI_TY_LE, LOAI_KHONG_HO_TRO, LOAI_BAT_THUONG, trạng thái lạ; tỷ lệ 0, âm, NaN, vô cực, chuỗi, bool, list; lớp tỷ lệ tách riêng khỏi danh sách cho phép |
| MEDIUM-3: lách kiểm tra trùng ngày khi thiếu `source_id` | `source_id` bắt buộc (chuỗi không rỗng); kiểm tra trùng ngày nhận dạng bản gốc theo cả `source_id` và sha256 | `source_id` rỗng, toàn khoảng trắng, thiếu hẳn; cùng tệp khai dưới hai `source_id` |
| MEDIUM-4: đường xuất có thể ghi đè bản đã xuất | Từ chối mọi `--out` trong kho và mọi `--out` đã tồn tại; `mkdir` không `exist_ok`; tệp mở chế độ `x` | `--out` trong `reports/` của kho và trong `TTC_HOME`; chạy lại vào thư mục đã có (bytes giữ nguyên); thư mục rỗng, tệp, liên kết treo, liên kết cha trỏ vào kho; thư mục xuất hiện giữa lúc kiểm và lúc ghi; tệp đã có |

Trên mã `ec47dc8`, 31 test mới thất bại. Đột biến: gỡ từng lớp sửa (11 đột biến: bỏ kiểm loại, đảo ưu tiên loại, bỏ danh sách cho phép, bỏ kiểm tỷ lệ dương, thu hẹp nhiễm, bỏ `source_id` bắt buộc, bỏ khóa sha256, cho ghi trong kho, bỏ kiểm tồn tại, `exist_ok=True`, mở `w`) — cả 11 bị test bắt.

## 6. Chưa đạt

- Ngày chính thức của VCB và TCB lệch ngày gãy của chuỗi giá gốc; nguyên nhân sự lệch ở nguồn dữ liệu chưa xác định và không được suy từ giá.
- Yahoo ghi mọi sự kiện cổ phiếu là `stock_split`; văn bản HOSE của VCB, TCB, FPT là `stock_dividend`. Cổng không suy loại. Chưa có quyết định về cách ghi loại đúng cho dòng Yahoo (cần Owner, ADR-0009 điều 7).
- Cần bản gốc HOSE/VSD cho TPB, HDB, TCB 2026 và mọi sự kiện cổ phiếu còn lại, rồi một PR riêng, có Owner theo ADR-0009 điều 7, để quyết định cách biểu diễn "ngày chính thức" khác "ngày chuỗi gãy" trong dữ liệu dẫn xuất.
- Chưa có bản dẫn xuất nào được công bố; chưa đổi `data.sources`; `deployment_level` giữ 0.
