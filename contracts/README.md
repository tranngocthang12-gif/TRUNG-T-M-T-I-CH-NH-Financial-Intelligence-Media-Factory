# Core Contracts (25)

Mọi output quan trọng phải khớp một schema dưới đây. Chỉ thêm schema mới khi có ranh giới thực sự mới.

| Contract | Mô tả | Từ |
|---|---|---|
| `market_data_contract` | Bản ghi dữ liệu thị trường có kiểm soát point-in-time | v0.1 |
| `evidence_item` | Một mảnh bằng chứng trong Evidence Graph | v0.1 |
| `hypothesis` | Ý tưởng đầu tư dạng giả thuyết kiểm chứng được, có `invalidation_conditions` | v0.1 |
| `research_report` | Báo cáo nghiên cứu của một chuyên gia | v0.1 |
| `valuation_case` | Trường hợp định giá | v0.1 |
| `backtest_run` | Một lần chạy backtest | v0.1 |
| `model_card` | Thẻ mô hình | v0.1 |
| `market_regime` | Phân loại regime thị trường | v0.1 |
| `investment_decision` | Gói quyết định đầu tư gửi Owner | v0.1 |
| `risk_assessment` | Đánh giá của Risk Officer — có quyền chặn | v0.1 |
| `portfolio_snapshot` | Ảnh chụp danh mục | v0.1 |
| `trade_record` | Bản ghi giao dịch | v0.1 |
| `attribution_report` | Phân rã kết quả — Learning chỉ học sau báo cáo này | v0.1 |
| `learning_lesson` | Bài học rút ra | v0.1 |
| `knowledge_item` | Mục tri thức (candidate hoặc canonical) | v0.1 |
| `media_story` | Câu chuyện truyền thông | v0.1 |
| `editorial_review` | Duyệt biên tập | v0.1 |
| `conflict_disclosure` | Kiểm tra xung đột lợi ích Đầu tư ↔ Truyền thông | v0.1 |
| `prediction` | Dự báo kiểm chứng được, ghi trước khi biết kết quả | v1.0 |
| `resolution` | Kết quả chấm một dự báo | v1.0 |
| `procedure` | Quy trình/prompt có phiên bản | v1.0 |
| `knowledge_note` | Ghi chú tri thức có địa chỉ nguồn, trích nguyên văn, self_check | v3.0 (v2.0 IX) |
| `exam_item` | Câu thi Học viện, đề giữ kín | v3.0 (v2.0 IX) |
| `dossier` | Hồ sơ doanh nghiệp tầng 3 | v3.0 (v2.0 IX) |
| `forecast_issue` | Dự báo ghi qua GitHub Issue "Forecast" | v3.0 |
