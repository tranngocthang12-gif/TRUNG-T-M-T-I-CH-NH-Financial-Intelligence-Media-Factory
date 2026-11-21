# Sự kiện quyền BSR, LPB, MCH, TCX, VPL từ 01/06/2026 — 21/11/2026

**Phạm vi:** năm mã bổ sung cho rổ VN30 theo QĐ-4 (ADR-0016). Gồm mọi thông báo ngày đăng ký cuối cùng của HOSE có ngày giao dịch không hưởng quyền từ 01/06/2026 tới 21/11/2026. Loại sự kiện gồm: cổ tức tiền, cổ tức cổ phiếu, cổ phiếu thưởng, phát hành, chia tách.

**Nguồn:** chỉ dùng tin và tệp đính kèm trên `api.hsx.vn` và `staticfile.hsx.vn`, tải nguyên byte ngày 21/11/2026. Không dùng báo chí hay trang thứ cấp.

**Manifest:** `data/evidence/corporate_actions/EVIDENCE_MANIFEST_VN30_BO_SUNG.json`. Dùng cùng khuôn trường với `EVIDENCE_MANIFEST_2026H2.json`:
- `event_type` để trống;
- nguyên văn loại sự kiện chép vào `event_type_verbatim`;
- `published_at` theo luật D1: lấy `data.postedDate` của tin HOSE, không gắn múi giờ. Ngày đăng trùng ngày ký thì để trống.

**Cách đọc PDF:** PDF là ảnh quét, không có lớp chữ. Ngày, tỷ lệ và lý do do Claude (Anthropic) đọc từ ảnh; chưa có người khác đối chiếu.

## Sự kiện tìm được

| Mã | Bản gốc | Thông báo | Ngày ký | Ngày công bố | Ngày không hưởng quyền | Ngày đăng ký cuối cùng | Nguyên văn loại | Tỷ lệ |
|---|---|---|---|---|---|---|---|---|
| BSR | hose-2475353 | 1434/TB-SGDHCM | 2026-06-29 | 2026-06-30T18:10:55 | 2026-08-11 | 2026-08-12 | chi trả cổ tức bằng tiền | 3%/mệnh giá, 300 đồng/cổ phiếu |
| MCH | hose-2485688 | 1643/TB-SGDHCM | 2026-07-31 | CHƯA XÁC MINH (HOSE đăng 2026-07-31T18:23:50, trùng ngày ký) | 2026-08-10 | 2026-08-11 | tạm ứng cổ tức bằng tiền | 20%/mệnh giá, 2.000 đồng/cổ phiếu |
| TCX | hose-2496161 | 1860/TB-SGDHCM | 2026-09-10 | 2026-09-11T08:41:56 | 2026-09-17 | 2026-09-18 | trả cổ tức bằng cổ phiếu | 5:1, hệ số 1,2 |

- Hai dòng cổ tức tiền có `official_ratio` để trống, vì cổ tức tiền không phải hệ số giá.
- Mỗi bản gốc được ghim kèm JSON tin HOSE và JSON danh sách tệp đính kèm. Tên PDF trong danh sách tệp đính kèm trùng đúng `url` của bản gốc.

## Mã chưa tìm thấy thông báo

| Mã | Kết quả | Ghi chú |
|---|---|---|
| LPB | UNKNOWN | Không thấy thông báo HOSE nào có ngày không hưởng quyền từ 01/06/2026. Thông báo gần nhất là 1062/TB-SGDHCM (tin 2460398): trả cổ tức năm 2025 bằng tiền, 30%/mệnh giá, ngày không hưởng quyền 14/05/2026, ngoài khung, không ghim. |
| VPL | UNKNOWN | Từ 01/05/2026 có 15 tin theo mã, không tin nào là thông báo ngày đăng ký cuối cùng. Lịch sự kiện quyền của HOSE cho mã này trống. |

UNKNOWN nghĩa là đã tra theo các truy vấn dưới đây mà không tìm thấy. UNKNOWN không có nghĩa là mã không có sự kiện.

## Thông báo đã thấy nhưng không ghim

- **BSR, tin 2481627** (TB 1575/TB-SGDHCM): ngày đăng ký cuối cùng để lấy ý kiến cổ đông bằng văn bản. Đây không phải cổ tức, thưởng, phát hành hay chia tách.
- **TCX, tin 2463430** (TB 1170/TB-SGDHCM): trả cổ tức bằng cổ phiếu năm 2024, tỷ lệ 5:1, ngày không hưởng quyền 25/05/2026, ngoài khung.
- **TCX, tin 2492159**: trả lãi trái phiếu TCX126011, không phải cổ phiếu.
- **Thông báo của chính công ty**, không phải văn bản HOSE:
  - LPB 2459317;
  - MCH 2484666;
  - TCX 2462172 và 2496179. Tin 2496179 đính chính thông báo phát hành cổ phiếu trả cổ tức của TCX; thông báo HOSE 1860 vẫn ghi tỷ lệ 5:1.
- **MCH, các tin ESOP** (2469853, 2473379, 2475320): phát hành cho người lao động, không có ngày đăng ký cuối cùng.

## Truy vấn đã tra

Áp dụng cho từng mã. Mã chứng khoán và id lần lượt: BSR 4682, LPB 2955, MCH 7519, TCX 7391, VPL 4483.

1. `https://api.hsx.vn/q/api/v1/search?indexName=securities&field=code^2,isin,figi,introduction&query=<mã>&page=1&pageSize=100`: lấy id chứng khoán.
2. `https://api.hsx.vn/n/api/v1/1/news/securities/<id>/1?pageIndex=<1..>&pageSize=50&startDate=2026-05-01&endDate=2026-11-21`: lấy mọi tin theo mã.
3. `https://api.hsx.vn/n/api/v1/1/news/securities/<id>/2?...` và `.../3?...`: lấy lịch sự kiện quyền của HOSE.
   - BSR: 11/08/2026.
   - LPB: 14/05/2026.
   - MCH: 10/08/2026.
   - TCX: 25/05/2026 và 17/09/2026.
   - VPL: không có.

Chưa đưa các sự kiện này vào engine hay chuỗi giá. Kho giá chưa có năm mã này.
