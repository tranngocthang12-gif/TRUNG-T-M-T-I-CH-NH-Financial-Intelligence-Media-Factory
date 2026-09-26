# Các cổng (Gates)

## Cổng dừng của Orchestrator
Orchestrator chỉ dừng khi gặp một trong:
- **OWNER GATE** — cần Owner duyệt
- **CAPITAL GATE** — liên quan tiền thật
- **LEGAL / COMPLIANCE UNCERTAINTY**
- **CREDENTIAL REQUIREMENT** — cần khóa/tài khoản
- **IRREVERSIBLE ACTION** — hành động không thể hoàn tác
- **REAL BLOCKER** — không thể tiến tiếp

## Chuỗi cổng cho quyết định đầu tư
```text
INVESTMENT DECISION → RISK GATE → CAPITAL GATE → HUMAN GATE
```
Risk Gate fail ⇒ không deploy, dù lợi nhuận kỳ vọng cao.

## Capital Deployment Ladder
| Level | Tên | Điều kiện qua cổng |
|---|---|---|
| 0 | RESEARCH ONLY | Hypothesis hợp lệ theo contract |
| 1 | SIMULATION | Mô phỏng có baseline |
| 2 | BACKTEST | Có phí giao dịch, slippage, holdout, walk-forward, regime test |
| 3 | PAPER TRADING | Backtest qua robustness; Owner duyệt |
| 4 | SMALL CONTROLLED CAPITAL | Paper đạt tiêu chí; Risk Gate pass; Owner duyệt; `live_trading_enabled` = true |
| 5 | NORMAL CAPITAL | Vốn nhỏ đạt tiêu chí qua attribution |
| 6 | SCALE | Production proven; Owner duyệt |

**Không được tự nhảy tầng.** Cấm tuyệt đối: `BACKTEST → LIVE MONEY`.

## Deployment Gate cho mô hình
```text
NEW DATA → DRIFT TEST → PERFORMANCE TEST → RETRAIN PROPOSAL → EVALUATION → DEPLOYMENT GATE
```
