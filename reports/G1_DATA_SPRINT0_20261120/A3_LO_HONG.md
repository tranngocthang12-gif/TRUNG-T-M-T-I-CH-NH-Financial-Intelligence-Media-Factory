# A3 — lỗ hổng VN30 và sự kiện quyền

Ngày: 2026-11-20. Không sửa `data/corporate_actions.csv`, `data/vn30_history.csv`, `engine/adjust.py`, `config.yaml`.

## VN30

`data/vn30_history.csv` có 38 dòng ADD/REMOVE, không phải giá. Bốn mốc hiệu lực: 2025-08-04, 2026-02-02, 2026-05-13, 2026-08-03. Không có rổ trước 04/08/2025. Không được gọi là point-in-time toàn bộ lịch sử.

Tệp `hose-2510691` hiệu lực 2026-11-16 là **VNAllshare kỳ 10/2026**, SHA-256 `ca0c5ee6fc20234ea7c0dff93f0b0a5eac4bb16df93f9b36268c0ffadaa567d4`, 416988 byte. Không phải kỳ VN30 và không có trong csv. Lỗ hổng: chưa có bản gốc rổ VN30 cho kỳ sau 03/08/2026.

## Hai sự kiện vẫn CAN_DOI_CHIEU trong csv

| Mã | Dòng csv | Trạng thái csv | Bản HOSE đã ghim | Ngày chính thức | Hash PDF |
|---|---|---|---|---|---|
| TCB | 2024-06-11 stock_dividend 2.0 | CAN_DOI_CHIEU | hose-1705374 | 2024-06-20, tỷ lệ 1:1 | `fac79d718815dc8b47578a6778b55f5ad71700ed18102aae84dd4eb23cd9d1de` (262114) |
| VCB | 2025-03-03 stock_dividend 1.495 | CAN_DOI_CHIEU | hose-1753594 | 2025-03-12, tỷ lệ 1.000:495 | `10c6d4426a691dd4abfef2b4b3da7df4e53e2eb86daf012c13f3ff6ff9cd07e1` (430569) |

`published_at` của cả hai bản HOSE trong manifest vẫn `CHUA_XAC_MINH`. Ngày csv là ngày giá gốc gãy, lệch ngày văn bản. Không sửa csv trong phiên này. Engine không được đụng; báo cáo cũ đã chỉ ra `source_status` không chặn APPLIED. Việc đó là quyết định engine riêng.

## Giá

Yahoo Finance vẫn là nguồn giá tạm trong `governance/DATA_SOURCES.yaml`. SSI và DNSE cần tài khoản: **Owner Gate**, không xin khóa trên Issue.

## Cột

corporate-action verified: chưa. Hai dòng trên vẫn CAN_DOI_CHIEU. Không có vốn thật.
