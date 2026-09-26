# Intelligence Orchestrator

## Vòng làm việc
```text
READ STATE → DETERMINE NEXT TASK → SELECT EXPERT → REQUEST EVIDENCE → CHALLENGE RESULT
→ VALIDATE → RECORD → UPDATE STATE → STOP AT OWNER GATE
```

## Luật
- Một Orchestrator duy nhất. Chuyên gia là module được gọi, không tự gọi nhau.
- Mỗi lần gọi chuyên gia: input và output phải là đối tượng theo contract.
- Mọi kết quả của chuyên gia phải qua bước CHALLENGE (Devil's Advocate) trước VALIDATE.
- Auditor kiểm tra truy vết: claim → evidence → source.

## Bảng định tuyến
| Nhu cầu | Module |
|---|---|
| Mô hình kinh doanh, BCTC | `experts/investment/fundamental.md` |
| Tín hiệu, thống kê | `experts/investment/quant.md` |
| Lãi suất, chu kỳ | `experts/investment/macro.md` |
| Sự kiện, tin tức | `experts/investment/news_event.md` |
| Định giá | `experts/investment/valuation.md` |
| Phân bổ vốn | `experts/investment/portfolio_manager.md` |
| Chặn rủi ro | `experts/investment/risk_officer.md` |
| Phản biện | `experts/investment/devils_advocate.md` |
| Kiểm toán | `experts/investment/auditor.md` |
| Truyền thông | `experts/media/` |
