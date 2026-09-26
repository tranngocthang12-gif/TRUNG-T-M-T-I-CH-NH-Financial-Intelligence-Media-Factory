# Data & Evidence Engine

```text
SOURCE → INGESTION → NORMALIZATION → TIMESTAMP → POINT-IN-TIME CONTROL → QUALITY CHECK → VERSION → EVIDENCE GRAPH
```

**Nguồn:** giá, khối lượng, BCTC, hồ sơ cơ quan quản lý, báo cáo công ty, earnings call, dữ liệu vĩ mô, lãi suất, lạm phát, sự kiện doanh nghiệp, dự phóng analyst, tin tức, dữ liệu thay thế.

**Mỗi bản ghi phải có:** `source, published_at, effective_at, observed_at, revision, version, universe, quality, known_limitations` → `contracts/market_data_contract.schema.json`.

**Chống:** look-ahead bias, survivorship bias, revised-data leakage, target leakage, universe leakage.

## Evidence Graph
```text
CLAIM → SOURCES → OBSERVATIONS → SUPPORTING EVIDENCE → CONTRARY EVIDENCE → ASSUMPTIONS → CONFIDENCE → EXPIRY / REVIEW DATE
```
Hệ thống phải trả lời được: *"Tại sao tôi tin điều này?"* và *"Điều gì có thể làm kết luận này sai?"* → `contracts/evidence_item.schema.json` (trường `stance`: supporting / contrary).
