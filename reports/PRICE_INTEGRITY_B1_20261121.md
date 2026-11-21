# PRICE-INTEGRITY B1 — Kiểm toán đường giá nghiên cứu, lỗi TCB/VCB và cổng fail-closed

- Ngày: 2026-11-21. Người viết: Claude (Anthropic), vai Validation & Research Engineer. Người chấm L-09: **chưa có**. Owner L-10: **chưa**.
- Cây đọc: `main` `20f5d924bbf52c34b68baeaff9df8d022a0af363` (merge PR #69). CI `Tests` trên SHA đó: run 44878828447 SUCCESS.
- Đo bằng: `python tools/price_integrity_b1.py` (chỉ đọc, chạy hai lần cho cùng byte). Bản máy đọc: [PRICE_INTEGRITY_B1_20261121.json](PRICE_INTEGRITY_B1_20261121.json), sinh bằng công cụ tại HEAD `1fce4c313ab792ad00e0d9242240b705339a837a` của PR #71. "Phiên" trong các số đo cửa sổ là **phiên suy từ dữ liệu** (bỏ ngày mọi mã có khối lượng 0), không phải lịch HOSE (khóa `session_definition` trong JSON).
- Tái lập trên fixture độc lập: `tests/test_price_integrity_b1.py` (18 test: 12 pass, 6 xfail strict), cũng ở PR #71.
- Báo cáo này và mã đi hai PR riêng theo LỆNH K0: mã ở PR #71, báo cáo ở PR này. Cả hai tách từ PR #70.
- Không giao dịch, không đổi `SAFETY_STATE`, `config.yaml`, `engine/adjust.py`, `engine/data.py`, kho raw, Ledger, sổ thử hay NAV giấy. Không chạy lần thử mới, không fit mô hình trên dữ liệu thật.

## 0. Kết luận

1. **Đã tái lập.** `adjust.build_events` gán `APPLIED` cho TCB 2024-06-11 và VCB 2025-03-03 dù cả hai ở trạng thái `CAN_DOI_CHIEU`. Hàm này không đọc `source_status`. Test hồi quy cho điểm này đã có từ trước (`test_root_cause_source_status_does_not_decide_applied`), nên PR #71 không viết lại nó.
2. **Ngày trong CSV không phải ngày sự kiện quyền.** Đó là ngày chuỗi giá Yahoo gãy, đúng **7 phiên** trước ngày GDKHQ in trên bản HOSE đã ghim (TCB 2024-06-20, VCB 2025-03-12). Bảng sự kiện Yahoo ghi tách cổ phiếu đúng ngày HOSE. Tại ngày HOSE, giá gốc liên tục (+2,69% và +3,01%).
3. **Nguyên nhân khả dĩ nhất (PROBABLE, chưa VERIFIED):** Yahoo chỉ chia lại 7 phiên liền trước ngày GDKHQ, các phiên trước đó để nguyên. Với VCB, dấu hiệu số học rất mạnh: 7/7 giá đóng cửa trong cửa sổ nằm ngoài lưới bước giá HOSE, nhưng nhân 1,495 thì 7/7 nằm đúng lưới. Khối lượng chia 1,495 cũng 7/7 nằm đúng lô 100, trong khi khối lượng gốc chỉ 2/7. Với TCB, dấu hiệu yếu hơn (giá 6/7 đã nằm trên lưới, chỉ phiên 2024-06-11 lệch).
   Muốn VERIFIED phải đối chiếu với giá đóng cửa chính thức của HOSE/VSD cho 2024-06-11..19 và 2025-03-03..11. Kho chưa có nguồn đó.
4. **Vì vậy sự kiện tay hiện đang vá một lỗi nguồn, không mô tả một sự kiện quyền.** Trên fixture, cặp "sự kiện tay ở ngày gãy + sự kiện Yahoo ở ngày HOSE" dựng lại đúng chuỗi lợi suất thật (sai số < 1e-12). Chỉ chặn `CAN_DOI_CHIEU` (P1a) hoặc dời ngày sang ngày HOSE (P2) đều làm lộ bước gãy −49,5% / −33,1%. Cổng chất lượng che được bước gãy đó nhưng mất 141 dòng đủ feature+nhãn mỗi mã.
5. **Rủi ro im lặng thật nằm ở tỷ lệ.** Một tỷ lệ chưa xác minh sai tới khoảng ±7% vẫn `APPLIED` và không bị cờ. Thử với VCB: tỷ lệ 1,40 thay cho 1,495 làm lợi suất qua sự kiện (2025-02-25→03-17, 14 phiên) còn +1,75% thay vì +8,65%. Cổng chất lượng không bắt được loại lỗi này.
6. **Tìm thêm một lỗ hổng trong `engine/verified_adjust.py`, đã sửa ở PR #71.** Trước bản vá, một sự kiện `DA_NAM_TRONG_GIA_NGUON` được chứng nhận `DA_KIEM_CHUNG` và không nhiễm ô, dù chuỗi còn bước gãy −50% ngay 7 phiên trước ngày GDKHQ. Đó đúng là kiểu lỗi của TCB/VCB. Bản vá cách ly ca này bằng trạng thái `CACH_LY_GIA_GAY_TRUOC_NGAY_HUONG_QUYEN`. Vòng chấm 2 thêm điều kiện 9: mã thiếu giá ở bất kỳ phiên nào trong 45 ngày trước sự kiện thì cách ly `CACH_LY_THIEU_GIA_TRUOC_NGAY_HUONG_QUYEN`, vì chỗ trống làm bước gãy lọt qua biên đã nới. Module này chưa nối vào vòng học, nên số liệu nghiên cứu hiện hành không đổi.
7. **Ngoài TCB/VCB, kho Yahoo còn có 123 ngày mọi dòng có khối lượng 0 và giá đóng cửa không đổi.** Đó là 4.954 trên 73.402 dòng. Phần lớn rơi vào các kỳ nghỉ Tết, Giỗ Tổ, 30/4–1/5, 2/9, 1/1; hai ngày năm 2026 (09-09, 10-05) không khớp lịch nghỉ phổ biến. Engine tính các ngày đó là phiên giao dịch trong cửa sổ feature và nhãn.
8. **Engine định lượng: NO_EDGE trên dữ liệu hiện có.** Có 222 lần thử, đều REJECTED. IC-t lớn nhất từ đầu là 1,06, ngưỡng hiện hành 3,69. DSR của 6 lần thử mới ≤ 2,2e-5. Không có mô hình ACTIVE. Dữ liệu đó còn thiên lệch sống sót và chưa kiểm chứng sự kiện quyền, nên kết luận NO_EDGE cũng không phải kết luận alpha.

## 1. Sơ đồ dữ liệu đang chạy thật (đọc mã, không đọc docstring)

| Bước | Hàm tạo đầu ra | Nguồn | Thời điểm thật sự được biết | Điều kiện xác minh trong mã | Thông tin chưa xác minh có ảnh hưởng không | Test đang bảo vệ |
|---|---|---|---|---|---|---|
| RAW PRICE | `data.ingest` → `_fetch_yahoo(auto_adjust=False)` → `data.save_store` (nối thêm); `data.load_store` giữ bản quan sát đầu | Yahoo, `config.yaml data.sources: [yahoo]` | `observed_at`: 72.202 dòng tới 2026-09-25 tải một lần ngày 2026-09-26; sau đó mỗi phiên một lần. Không có vintage trước 2026-09-26 | Không kiểm nội dung giá. Chỉ kiểm chỉ-ghi-thêm (ADR-0006) | Có: giá Yahoo đã điều chỉnh một phần (mục 3), 123 ngày khối lượng 0 | `test_b1_engine_bridge`, `ledger_audit` mục 1a (byte), không có test nội dung |
| CORPORATE EVENTS | `adjust.load_manual` + `adjust.load_yahoo` | `data/corporate_actions.csv` (2 dòng, cả hai `CAN_DOI_CHIEU`); `data/derived/yahoo_actions.csv` (433 dòng `TU_DONG`, **ghi đè mỗi vòng**) | Không có `published_at`; tệp Yahoo mang `fetched_at` của lần tải gần nhất | Không có | Có: mọi sự kiện đều chưa xác minh | không |
| ADJUSTED PRICE | `adjust.build_events` → `adjust.factors` → `data.load_market` (`adj = raw * F`) | hai nguồn trên | neo tại `as_of`, chỉ sự kiện `ex_date ≤ as_of` | `APPLIED` khi bước giá sau nhân tỷ lệ nằm trong ±7,3%. `DA_NAM_TRONG_GIA_NGUON` chỉ theo `source == yahoo` và `observed_at ≥ ex_date`, **không kiểm bước giá** | Có: 5 sự kiện cổ phiếu và 222 cổ tức tiền đang áp, không cái nào xác minh | `test_verified_adjust` (nguyên nhân gốc), `test_adjustment` (**khóa** TCB/VCB `APPLIED` trên dữ liệu thật) |
| QUALITY FLAGS | `adjust.quality` trên chuỗi đã điều chỉnh | — | — | biên ±7% + dung sai 0,3% (SHB ±10% tới 2023); tỷ lệ lỗi 20 phiên > 1% thì dừng | Có: sự kiện sai che bước gãy; sai tỷ lệ trong biên lọt qua | `test_quality_gate`, `test_adjustment` |
| FEATURES / LABELS | `features.dataset(close.ffill(limit=5), volume/S, h=20, bad)` | chuỗi điều chỉnh | t | ô lỗi lây 121 phiên cho feature, cửa sổ nắm giữ cho nhãn | Có: ngày khối lượng 0 bị tính là phiên | `test_no_lookahead` |
| RESEARCH | `research.walk_forward` (train ≥ 500, test 120, embargo h+1), `metrics`, `classify`; L-06 `register_trial` | dataset | — | đăng ký trước, đẩy lên main trước backtest | Có: mọi lần thử dùng chuỗi trên | `test_laws_validate`, `test_measurement_integration` |
| MODEL REGISTRY | `knowledge.promote` → `state/model_registry.json` | trials | — | ngưỡng Bonferroni + điều kiện fold/regime | — (0 ACTIVE) | `test_governance` |
| PAPER | `paper.run`, `paper.apply_corporate_actions` | `close` điều chỉnh + `events` `APPLIED` | — | khóa trần/sàn 95% biên (ADR-0008) | Có về nguyên tắc: sự kiện tay sẽ nhân đôi cổ phiếu TCB vào 2024-06-11 (sai ngày). Hiện không có vị thế, NAV 1.000.000.000 | `test_adjustment` OK 7 |
| REPORT | `report.write`, `state/ENGINE_STATE.json` | — | — | nhãn thiên lệch sống sót khi `CURRENT` | — | `test_governance` |

`engine/verified_adjust.py` và `tools/build_verified_derivation.py` dựng một chuỗi riêng ra ngoài kho. Chuỗi đó **không** nằm trên đường trên (ADR-0009 điều 7).

## 2. Tái lập trên fixture độc lập (không ghi kho)

`tests/test_price_integrity_b1.py`, phần A và B. Dữ liệu tổng hợp gồm 4 mã, 420 phiên, bước ngẫu nhiên có hạt giống. Mã AAA có tách 2:1 tại phiên 300, nguồn đã chia sẵn 7 phiên trước đó, `observed_at` 2026-09-26.

| Test | Kịch bản | Kết quả |
|---|---|---|
| A1 | Sự kiện tay `CAN_DOI_CHIEU` ở ngày gãy + Yahoo ở ngày chính thức (đúng cặp của kho thật) | Tay `APPLIED`, Yahoo `DA_NAM_TRONG_GIA_NGUON`, 0 cờ; lợi suất khớp chuỗi thật; ngày áp lệch ngày chính thức đúng 7 phiên |
| A2 | Bỏ sự kiện chưa xác minh (P1a) | Một cờ −50% ở ngày gãy; mọi feature của AAA bị loại 121 phiên; mọi nhãn có cửa sổ chứa bước gãy bị loại; không nhãn nào mang −50% |
| A3 | Dời sự kiện tay sang ngày chính thức, vẫn chưa xác minh (P2) | `KHONG_KHOP`, không áp; cờ và chuỗi **giống hệt** P1a |
| A4 | Sai tỷ lệ 5% (1,9 thay 2,0), chưa xác minh | `APPLIED`, 0 cờ, lợi suất qua sự kiện lệch khoảng −5 điểm phần trăm |
| B1 | `DA_NAM_TRONG_GIA_NGUON` + bản gốc đủ + nguồn chia một phần | Trước bản vá: `DA_KIEM_CHUNG`, vào chuỗi kiểm chứng, không nhiễm ô (**lỗi**). Sau bản vá: `CACH_LY_GIA_GAY_TRUOC_NGAY_HUONG_QUYEN`, nhiễm mọi ô AAA trước ngày chính thức |
| B2 | Nguồn điều chỉnh toàn bộ, chuỗi liền | vẫn `DA_KIEM_CHUNG` (không quá tay) |
| B3 | Lỗi −30% 4 phiên trước sự kiện, không khớp tỷ lệ | cách ly, lý do "nhân tỷ lệ vẫn ngoài biên" |
| B4 | Bước gãy cách sự kiện hơn 45 ngày lịch | sự kiện vẫn `DA_KIEM_CHUNG`; lớp chất lượng cờ bước gãy trên chuỗi kiểm chứng (phòng thủ hai lớp; phạm vi cổng được ghi rõ) |
| B5 | Cặp tay + Yahoo cùng một bản gốc | không bên nào vào chuỗi; mọi ô AAA trước ngày chính thức nhiễm |
| B6 | Như B1, xóa giá AAA 19 phiên (OFF−20…OFF−2), giữ phiên liền trước và phiên sự kiện | bước −50% đo qua chỗ trống nằm trong biên đã nới; trước điều kiện 9: `DA_KIEM_CHUNG` (**lỗi**); sau: `CACH_LY_THIEU_GIA_TRUOC_NGAY_HUONG_QUYEN`, không vào chuỗi |
| B7 | Xóa cả phiên liền trước (OFF−20…OFF−1) | `CACH_LY_THIEU_GIA_TRUOC_NGAY_HUONG_QUYEN`, không vào chuỗi |

Không có bản vá thì B1 và B3 đỏ. Có bản vá thì toàn bộ `tests/test_verified_adjust.py` (104 test sau tham số hóa) vẫn xanh. Khi một bước gãy trước sự kiện do chính một ngày engine khác của cùng bản gốc gây ra, chẩn đoán `XUNG_DOT_NGAY` được giữ ưu tiên.

## 3. Bằng chứng trên kho thật (chỉ đọc)

Số đo trong mục này lấy từ `tools/price_integrity_b1.py`. Test D1 tái lập phần TCB/VCB và kiểm hash trước/sau.

### 3.1 Giá gốc quanh hai ngày

| Mã | Ngày CSV (`CAN_DOI_CHIEU`) | Bước giá gốc ngày CSV | GDKHQ trên bản HOSE ghim | Bước giá gốc ngày HOSE | Ngày Yahoo ghi tách | Số phiên giữa |
|---|---|---|---|---|---|---|
| TCB | 2024-06-11 | −49,54% | 2024-06-20 (hose-1705374) | +2,69% | 2024-06-20, tỷ lệ 2,0 | 7 |
| VCB | 2025-03-03 | −33,11% | 2025-03-12 (hose-1753594) | +3,01% | 2025-03-12, tỷ lệ 1,495 | 7 |

### 3.2 Phép thử lưới bước giá và lô (giả định: bước giá HOSE 10 / 50 / 100 đồng theo vùng giá; văn bản quy định chưa ghim trong kho)

| Cửa sổ | Phiên | Giá gốc đúng lưới | Giá × tỷ lệ đúng lưới | Khối lượng gốc đúng lô 100 | Khối lượng ÷ tỷ lệ đúng lô | KL trung vị |
|---|---|---|---|---|---|---|
| VCB 20 phiên trước | 20 | 20 | 0 | 20 | 3 | 1.393.700 |
| **VCB cửa sổ 03-03..03-11** | 7 | **0** | **7** | **2** | **7** | 3.735.855 |
| VCB 20 phiên sau | 20 | 20 | 1 | 20 | 1 | 2.993.350 |
| TCB 20 phiên trước | 20 | 20 | 20 | 20 | 9 | 8.946.750 |
| **TCB cửa sổ 06-11..06-19** | 7 | 6 | 7 | 7 | 7 | 19.671.200 |
| TCB 20 phiên sau | 20 | 20 | 20 | 20 | 12 | 10.660.250 |

Đọc bảng:

- VCB: trong cửa sổ, giá và khối lượng của nguồn là số đã chia 1,495, trong khi phiên trước và sau cửa sổ là số chưa chia. Đây là đặc điểm số học, không suy từ riêng bước nhảy giá.
- TCB: tỷ lệ 2 làm phép thử lưới gần như không phân biệt được (nửa của một giá bội 100 vẫn là bội 50). Bằng chứng còn lại là ngày Yahoo ghi tách trùng ngày HOSE, bước giá liên tục tại ngày HOSE, và khối lượng trung vị trong cửa sổ gấp khoảng 2,2 lần 20 phiên trước. **TCB xếp PROBABLE, yếu hơn VCB.**

### 3.3 Các ứng viên khác cùng dấu hiệu

Dò mọi sự kiện cổ phiếu, 15 phiên trước ngày áp, tìm bước ngoài biên được tỷ lệ giải thích:

- TCB và VCB như trên.
- SSB 2021-07-19, 4 phiên trước tách 2021-07-23, −8,19%. Phép thử lưới không đọc được vì giá trước đó đã bị chia lại bởi các lần tách sau.
- TPB 2025-10-20, 8 phiên trước tách 2025-10-30, −9,11%. Giá 20 phiên trước và trong cửa sổ đều nhân 1,05 mới đúng lưới, tức nguồn đã chia **cả** hai đoạn. Bước −9,11% vì vậy chưa giải thích được. Ngày 2025-10-20 có 17 mã bị cờ.
- HDB, TCB, TPB 2026: bước gãy ngay ngày áp, dữ liệu tăng dần, `APPLIED` theo Yahoo `TU_DONG`. Không có dấu hiệu chia một phần.

SSB 2021 và TPB 2025 là **UNKNOWN**, không kết luận. Các ô đó đã bị cờ chất lượng loại khỏi feature và nhãn.

### 3.4 Lịch phiên: ngày mọi dòng khối lượng 0

- 123 ngày trong kho có mọi dòng khối lượng 0, và giá đóng cửa của cả 123 ngày đều bằng phiên trước. Tổng cộng 4.954/73.402 dòng có khối lượng 0.
- Phân bố theo năm (2017→2026): 3, 11, 12, 10, 18, 14, 13, 15, 12, 15.
- Các ngày rơi vào Tết, Giỗ Tổ, 30/4–1/5, 2/9, 1/1 theo nhận dạng mẫu. Hai ngày 2026-09-09 và 2026-10-05 không khớp lịch nghỉ phổ biến; có thể là nguồn mất dữ liệu: UNKNOWN.
- Danh sách đủ nằm trong JSON. Chưa đối chiếu lịch giao dịch HOSE gốc, nên đây là phát hiện dữ liệu, chưa phải lịch đã xác minh.

Ảnh hưởng: `features` và `labels_wide` đếm phiên theo dòng.

- 1.118/2.801 cửa sổ nhãn "20 phiên" chỉ có 13–19 phiên suy từ dữ liệu, tức sau khi bỏ ngày mọi mã khối lượng 0; đây không phải lịch HOSE (13: 6 cửa sổ; 14: 20; 15: 133; 16: 62; 17: 130; 18: 228; 19: 539).
- `lowvol_*` nhận các ngày lợi suất 0 giả.
- `volu_*` nhận khối lượng 0.
- Phiên mở lại sau kỳ nghỉ bị so với giá "ngày nghỉ".

Test C5 (xfail strict) ghi điều kiện để hạng mục này đạt.

## 4. Tác động đo được của từng cách xử lý (dữ liệu thật, as_of 2026-11-20, 2.822 phiên × 30 mã; không fit mô hình)

| Phương án | Sự kiện cổ phiếu trong chuỗi | Cờ chất lượng | Ô feature hợp lệ | Ô nhãn hợp lệ | Dòng đủ feature + nhãn | TCB 2024-06-04→06-26 (16 phiên) | VCB 2025-02-25→03-17 (14 phiên) | Dòng đủ mất (TCB / VCB) |
|---|---|---|---|---|---|---|---|---|
| P0 hiện hành | 5 | 142 | 796.561 | 70.515 | 56.299 | +0,84% | +8,65% | — |
| P1a bỏ sự kiện tay chưa đối chiếu | 3 | 144 | 793.415 | 70.475 | 56.017 | −49,58%* | −27,32%* | 141 / 141 |
| P1b bỏ mọi sự kiện chưa `DA_KIEM_CHUNG` (gồm Yahoo) | 0 | 152 | 784.302 | 70.318 | 55.238 | −49,58%* | −27,32%* | 158 / 141 |
| P2 dời ngày tay sang ngày HOSE | 3 (tay: `KHONG_KHOP`) | 144 | 793.415 | 70.475 | 56.017 | −49,58%* | −27,32%* | 141 / 141 |
| P3 chuỗi kiểm chứng + nhiễm ô | **0** | 152 | 220.846 | 19.776 | **15.470** | −49,58%* | −27,32%* | 1.639 / 2.091 |

\* Bước gãy này bị cờ. Feature và nhãn chạm vào nó đã bị loại, nên con số chỉ là giá trên chuỗi, không vào dataset.

Chi tiết:

- P1b: 52.216 ô nhãn đổi giá trị so với P0, lệch lớn nhất 0,0721, do bỏ điều chỉnh cổ tức tiền.
- P3:
  - Trạng thái kiểm chứng: 124 `CACH_LY_THIEU_BANG_CHUNG`, 1 `CACH_LY_LOAI_SU_KIEN_LECH`, 1 `CACH_LY_THIEU_NGAY_CONG_BO`, 25 `KHONG_ANH_HUONG`.
  - 71,83% ô bị nhiễm; 17/30 mã có ô nhiễm trong 252 phiên gần nhất.
- Độ nhạy tỷ lệ VCB (sự kiện tay, ngày 2025-03-03): mọi tỷ lệ đều `APPLIED`, không cờ.

| Tỷ lệ | 1,40 | 1,45 | 1,495 | 1,54 | 1,60 |
|---|---|---|---|---|---|
| Bước giá sau điều chỉnh tại ngày gãy | −6,35% | −3,01% | 0,00% | +3,01% | +7,02% |
| Lợi suất VCB 2025-02-25 → 2025-03-17 (14 phiên) | +1,75% | +5,38% | +8,65% | +11,92% | +16,29% |

## 5. Ba lựa chọn khắc phục (chưa chọn; Owner quyết)

| | (A) Giữ đường hiện hành, chặn chứng nhận nghiên cứu | (B) Chuỗi verified-adjusted chạy song song (shadow) | (C) Cổng fail-closed tại đầu vào nghiên cứu |
|---|---|---|---|
| Làm gì | Không đổi engine. Mọi kết quả nghiên cứu, báo cáo chu kỳ, ENGINE_STATE gắn nhãn `RETROSPECTIVE / UNVERIFIED_EVENTS`; PIT-001 giữ NOT_READY | Mỗi vòng dựng thêm bản `tools/build_verified_derivation.py` ra ngoài kho (hoặc artifact CI), báo diff P0↔P3 trong báo cáo; không cấp vào feature/nhãn | `load_market` dùng chuỗi kiểm chứng + nhiễm ô làm đầu vào nghiên cứu (P3) |
| Feature / nhãn / backtest | Không đổi | Không đổi; thêm số đo song song | Mất khoảng 73% dòng đủ feature+nhãn (56.299 → 15.470) ngay hôm nay. Thực tế nghiên cứu dừng tới khi có bằng chứng. Mọi số cũ không so được với số mới |
| Rủi ro làm sai lịch sử | Còn nguyên: sai tỷ lệ trong biên lọt qua; TCB/VCB đang dựa sự kiện vá lỗi nguồn | Như (A) trên đường chính; shadow không sai lịch sử | Thấp về lợi suất sai. Cao về thiên lệch chọn mẫu: mã có nhiều sự kiện (ngân hàng trả cổ tức cổ phiếu) bị loại nhiều hơn |
| Rollback | Không cần | Xóa bước shadow; không đụng kho | Phải giữ chuỗi cũ có phiên bản (ADR-0009 điều 6); đổi con trỏ về bản cũ |
| Test cần có | đã có (PIT-001 FAIL chặn READY); c6 đạt khi đầu ra mặc định mang nhãn RETROSPECTIVE và `derivation_id` | đối chiếu xác định (`test_verified_adjust` có `derivation_id` ổn định), diff báo cáo, không ghi kho; c1, c2 đạt khi có chế độ song song `research_input="verified"` | như (B), cộng end-to-end `load_market` → feature → nhãn → backtest ở chế độ đã kiểm; sửa `test_adjustment.py` (đang khóa TCB/VCB `APPLIED`) nếu đổi mặc định |
| Quyết định còn thiếu | Không | Owner duyệt phạm vi chạy shadow trong vòng học (đổi workflow), L-09 | ADR-0009 điều 7: PR engine riêng, end-to-end, L-09, Owner L-10. Owner chấp nhận dừng nghiên cứu cho tới khi đủ bằng chứng |

**Đề xuất (để Owner quyết, không tự làm):**

1. **(A) ngay.** Nó đã đúng với trạng thái hiện tại: PIT-001 NOT_READY, 0 ACTIVE.
2. **(B) khi Owner duyệt.** Chạy song song để có số đo xu hướng.
3. **Không làm (C) bây giờ.** Với 0/151 sự kiện cổ phiếu đủ bằng chứng, (C) chỉ biến engine thành rỗng mà không thêm sự thật.
4. **Điều kiện để mở (C):**
   - Có nguồn giá đóng cửa chính thức cho các cửa sổ nghi chia một phần.
   - `published_at` của bản HOSE được xác minh.
   - `event_type` của bản gốc được ánh xạ có kiểm (hiện 19 bản để trống: 17 bản ở `EVIDENCE_MANIFEST_2026H2.json`, cộng TCB 2024 và FPT 2026 ở `EVIDENCE_MANIFEST.json`).
   - Có quyết định cách biểu diễn "sửa giá nguồn" như một bản dẫn xuất có chứng cứ (ADR-0009 điều 1), không như một sự kiện quyền giả ngày.

Không đổi `ex_date` trong CSV sang ngày HOSE: P2 cho thấy dời ngày một mình không sửa được lỗi nguồn. Không nâng `source_status`: chưa có nguồn giá độc lập.

## 6. Bản vá mã (PR #71, tách từ PR #70)

- `engine/verified_adjust.py`: thêm điều kiện 8. Với `DA_NAM_TRONG_GIA_NGUON`, không được có bước giá gốc ngoài biên trong 45 ngày lịch trước phiên sự kiện; có thì cách ly `CACH_LY_GIA_GAY_TRUOC_NGAY_HUONG_QUYEN`. Nếu bước gãy đó chính là một ngày engine khác của cùng bản gốc, chẩn đoán `XUNG_DOT_NGAY` được ưu tiên. Không suy ngày, không suy hệ số.
- Cũng trong tệp đó, điều kiện 9 (vòng chấm 2): mọi phiên trên trục ngày của panel trong [phiên sự kiện − 45 ngày lịch, phiên sự kiện] phải có giá của mã; thiếu thì cách ly `CACH_LY_THIEU_GIA_TRUOC_NGAY_HUONG_QUYEN`, kiểm trước điều kiện 7 và 8.
- Trên kho thật: 0 sự kiện rơi vào trạng thái mới; vào chuỗi 0 trước và 0 sau; `verify_state` và `taints` giống hệt. Chẩn đoán: 4/126 sự kiện cổ phiếu `APPLIED`/`DA_NAM_TRONG_GIA_NGUON` có cửa sổ 45 ngày thiếu giá (SSI 2020-04-09, TCB 2018-07-05, TCB 2024-06-11, VIB 2020-11-19). Chúng đã bị cách ly ở bước bằng chứng trước đó. Module chưa nối vào vòng học.
- `tools/price_integrity_b1.py`: công cụ đo chỉ đọc cho báo cáo này.
- `tests/test_price_integrity_b1.py`, `.github/workflows/tests.yml` (thêm tên test vào danh sách bắt buộc). Test c1, c2 kiểm chế độ `research_input="verified"` chạy song song; không đòi đổi đường mặc định và không ngầm chọn phương án (C).
- Không sửa `engine/adjust.py`, `engine/data.py`, `config.yaml`, `data/`, `state/`, `ledger/`, `research/`, `paper/`.

## 7. Còn BLOCKED

| Việc | Chặn bởi |
|---|---|
| VERIFIED nguyên nhân TCB/VCB | Thiếu giá đóng cửa chính thức HOSE/VSD cho hai cửa sổ; thiếu `published_at` |
| Cổng `source_status` trên đường nghiên cứu | ADR-0009 điều 7, L-09, Owner L-10; và cách biểu diễn "sửa giá nguồn" chưa có quyết định |
| Lịch phiên chính thức | Chưa ghim lịch giao dịch HOSE gốc; Issue #57 (ghế thi công thu nguồn) |
| Ánh xạ `event_type` cho 19 bản gốc để trống: 17 ở `EVIDENCE_MANIFEST_2026H2.json`; TCB 2024 và FPT 2026 ở `EVIDENCE_MANIFEST.json` (VCB 2025 đã có `stock_dividend`) | Cần ghế khác đọc đối chiếu bản gốc (đang `CHUA_XAC_MINH`) |

Ghi chú phụ (không sửa): khi bản gốc có `event_type: null`, `verified_adjust._match` bỏ qua bản gốc đó. Lý do vì vậy hiện `CACH_LY_THIEU_BANG_CHUNG` ("không có bản gốc") dù đã có bản ghim. Kết quả vẫn đóng khi nghi ngờ; chỉ chữ chẩn đoán chưa chính xác.
