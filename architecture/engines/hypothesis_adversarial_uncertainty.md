# Hypothesis · Adversarial Review · Uncertainty

## Hypothesis Engine
Không dùng "cổ phiếu này có vẻ tốt". Mọi ý tưởng là một `HYPOTHESIS` (`contracts/hypothesis.schema.json`):
`IF <điều kiện> AND <điều kiện> THEN <kỳ vọng> UNLESS <điều kiện vô hiệu>`.

## Adversarial Review
```text
ORIGINAL THESIS → BULL CASE → BEAR CASE → DEVIL'S ADVOCATE → ALTERNATIVE EXPLANATION → DISCONFIRMING EVIDENCE SEARCH → FINAL REVISED THESIS
```
Devil's Advocate bắt buộc hỏi:
- Bằng chứng nào mâu thuẫn?
- Giả định nào yếu nhất?
- Tín hiệu có thể do nguyên nhân khác?
- Đã được định giá vào giá chưa?
- Backtest có overfit không?
- Thesis có sống sót ở regime khác không?

## Uncertainty Engine
Không chỉ BUY/HOLD/SELL. Trả về: expected range, confidence, evidence quality, assumption risk, model risk, regime risk, tail risk, xác suất kịch bản bull/base/bear (tổng = 1), điểm bất định lớn nhất, điều kiện vô hiệu chính. Mục tiêu: **calibrated confidence**.
