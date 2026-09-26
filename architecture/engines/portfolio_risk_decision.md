# Portfolio · Risk · Decision

## Portfolio Engine
`APPROVED IDEAS → EXPECTED RETURN → UNCERTAINTY → CORRELATION → LIQUIDITY → DRAWDOWN → CONCENTRATION → RISK BUDGET → POSITION SIZE`
Tối ưu tổng danh mục, không tối ưu từng cổ phiếu. Analyst không tự quyết vốn.

## Risk Engine (có quyền chặn)
Kiểm tra: position risk, portfolio risk, sector/factor exposure, correlation, liquidity, volatility, drawdown, tail risk, leverage, counterparty risk, data/model risk → `contracts/risk_assessment.schema.json`.

## Decision Engine
Output theo `contracts/investment_decision.schema.json`: asset, action, size, horizon, thesis, evidence, bull/base/bear, expected return, downside, confidence, regime, risks, invalidation, owner_gate_status.
