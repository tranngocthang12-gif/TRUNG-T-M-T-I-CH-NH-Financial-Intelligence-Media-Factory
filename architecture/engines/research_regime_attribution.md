# Regime · Research & Backtest · Counterfactual · Attribution · Model Decay

## Market Regime Engine
`MARKET DATA → REGIME FEATURES → REGIME CLASSIFIER → CONFIDENCE → STRATEGY COMPATIBILITY`
Regime: RISK_ON/RISK_OFF, HIGH_VOL/LOW_VOL, INFLATIONARY/DISINFLATIONARY, TIGHTENING/EASING, TRENDING/RANGING, LIQUID/ILLIQUID, CRISIS/NORMAL.
Mọi tri thức mang metadata `valid_regimes` và `unverified_regimes`. Không có quy luật vĩnh viễn.

## Research & Backtest Engine
`HYPOTHESIS → DATA CONTRACT → BASELINE → BACKTEST → TRANSACTION COST → SLIPPAGE → ROBUSTNESS → OUT-OF-SAMPLE → WALK-FORWARD → REGIME TEST → PAPER TRADING`
Cấm `BACKTEST → LIVE MONEY`.

## Counterfactual Engine
Sau mỗi quyết định hỏi: nếu không làm gì? vào lệnh trễ 1 ngày? size một nửa? tín hiệu khác? beta thị trường giải thích hết lợi nhuận?
Ví dụ: thực tế +12%, index +9%, ngành +11% ⇒ alpha ≈ +1%.

## Attribution Engine
`RETURN → MARKET BETA → SECTOR → FACTOR → SECURITY SELECTION → TIMING → POSITION SIZE → LEVERAGE → EXECUTION → LUCK → SKILL`
**Learning Engine chỉ được học sau attribution.**

## Model Decay Engine
Theo dõi: signal strength, hit rate, calibration, IC, turnover, transaction cost, drawdown, feature drift, regime dependency.
Trạng thái: `ACTIVE, WATCH, DEGRADING, REGIME_LIMITED, PAUSED, RETIRED, INVALIDATED` → `state/MODEL_REGISTRY.yaml`.
Không retrain chỉ vì có data mới.
