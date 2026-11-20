# DIFF rổ VN30 — 19/11/2026

Chỉ những câu dưới đây được lấy từ bản gốc HOSE đã tải và ghim sha256 trong `data/evidence/vn30_reviews/EVIDENCE_MANIFEST.json`. Không lấy số liệu từ báo chí.

## 1. VN30 chính thức có hiệu lực tại 2026-11-16

Nguồn: tin HOSE id 2510691 (đăng 02/11/2026 15:31:45 UTC) và PDF đính kèm `II.2. 20261102 QUY MO VNAllshare ky 10.2026.pdf`. Tin ghi các chỉ số quy mô VNAllshare có hiệu lực vào ngày 16/11/2026. Mục PDF «CẬP NHẬT THÔNG TIN CỔ PHIẾU THÀNH PHẦN CỦA CHỈ SỐ VN30», kỳ tháng 10/2026, in đủ 30 mã:

ACB, BID, BSR, CTG, FPT, GAS, GVR, HDB, HPG, LPB, MBB, MCH, MSN, MWG, SAB, SHB, SSB, SSI, STB, TCB, TCX, VCB, VHM, VIB, VIC, VJC, VNM, VPB, VPL, VRE.

Tập này trùng danh sách 30 mã trong PDF kỳ 7/2026 (hiệu lực 03/08/2026). PDF kỳ 10/2026 không thêm và không bớt mã so với kỳ đó.

## 2. Mã có trong `config.yaml` `universe` nhưng không có trong danh sách mục 1

BCM, BVH, PLX, POW, TPB.

## 3. Mã có trong danh sách mục 1 nhưng không có trong `config.yaml` `universe`

BSR, LPB, MCH, TCX, VPL.

`data/store/prices.csv.gz` có đúng 30 mã, trùng `universe` trong `config.yaml`. Năm mã trên không có dòng giá trong kho. BCM, BVH, PLX, POW, TPB có dòng giá trong kho.

## 4. Kỳ CHƯA ĐỦ BẰNG CHỨNG

Đã ghim được năm mốc, đều từ hsx.vn / api.hsx.vn / staticfile.hsx.vn:

| Kỳ | Hiệu lực | Bản gốc | Việc CSV ghi |
| --- | --- | --- | --- |
| 07/2025 | 04/08/2025 | PDF đủ 30 mã + tin 2388633 | 30 dòng ADD. Đây là kỳ sớm nhất có bản gốc và đủ 30 mã trong lần thu này. Không suy về trước ngày này. |
| 01/2026 | 02/02/2026 | PDF đủ 30 mã + tin 2432828 | REMOVE BCM, ADD VPL. |
| 05/2026 | 13/05/2026 | Tin 2460387, không có file đính kèm | REMOVE DGC, ADD BSR. Tin chỉ nêu hai mã này và ngày hiệu lực, không in lại 28 mã còn lại. 28 mã đó giữ từ PDF kỳ 01/2026 đã ghim. |
| 07/2026 | 03/08/2026 | PDF đủ 30 mã + tin 2479382 | So với tập sau tin 05/2026: REMOVE PLX, REMOVE TPB, ADD MCH, ADD TCX. |
| 10/2026 | 16/11/2026 | PDF đủ 30 mã + tin 2510691 | Không có dòng ADD/REMOVE. Tập trùng kỳ 07/2026. |

Các kỳ rà soát thành phần tháng 1 và tháng 7 từ 01/2016 đến 01/2025, và các kỳ cập nhật quý 04/2025, 10/2025, 04/2026: CHƯA ĐỦ BẰNG CHỨNG. Lý do: chưa tải được bản gốc tương ứng từ HOSE trong lần thu này. API tin tức của HOSE trả chậm và bị ngắt kết nối khi quét dài; không điền các kỳ đó từ báo chí hay từ trí nhớ. Vì vậy CSV không có dòng nào trước 04/08/2025.

Khoảng giữa 04/08/2025 và 02/02/2026, và giữa 13/05/2026 và 03/08/2026, không có thêm công bố thay đổi thành phần VN30 nào đã được tải. Không kết luận rằng không tồn tại công bố khác — chỉ kết luận rằng lần thu này chưa ghim được công bố đó.
