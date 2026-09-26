"""Paper Trading: quyết định tại close ngày d, KHỚP tại close ngày giao dịch kế tiếp, lô 100, phí + thuế + trượt giá VN."""
import numpy as np, pandas as pd
from .config import CFG, ROOT, path, load_json, save_json

ST = "paper/state.json"

def _append(rel, row):
    p = ROOT / rel
    df = pd.DataFrame([row])
    df.to_csv(path(rel), mode="a", header=not p.exists(), index=False)

def run(as_of, close, preds_today, reg, udates):
    c, lot, P = CFG["costs"], CFG["lot_size"], CFG["paper"]
    st = load_json(ST, {"cash": P["initial_cash"], "positions": {}, "pending": None,
                        "last_rebalance": None, "costs_paid": 0.0, "n_rebalance": 0})
    px = close.loc[pd.Timestamp(as_of)]
    d = str(pd.Timestamp(as_of).date())
    # 1) Khớp lệnh đã quyết định phiên trước
    if st["pending"] is not None:
        target = st["pending"]
        traded = False
        for t in [t for t in st["positions"] if t not in target]:
            sh = st["positions"].pop(t); p = px[t] * (1 - c["slippage"])
            st["cash"] += sh * p * (1 - c["sell_fee"] - c["sell_tax"])
            cost = sh * px[t] * c["slippage"] + sh * p * (c["sell_fee"] + c["sell_tax"])
            st["costs_paid"] += cost; traded = True
            _append("paper/trades.csv", {"date": d, "mode": "PAPER", "asset": t, "side": "SELL", "quantity": sh,
                                         "price": round(p, 2), "fees": round(cost, 0)})
        nav = st["cash"] + sum(s * px[t] for t, s in st["positions"].items())
        buys = [t for t in target if t not in st["positions"] and pd.notna(px.get(t))]
        per = nav / max(1, len(target)) * 0.995
        for t in buys:
            unit = px[t] * (1 + c["slippage"]) * (1 + c["buy_fee"])
            sh = int(min(per, st["cash"]) // unit // lot * lot)
            if sh <= 0:
                continue
            st["cash"] -= sh * unit; st["positions"][t] = sh; traded = True
            st["costs_paid"] += sh * px[t] * (c["slippage"] + c["buy_fee"])
            _append("paper/trades.csv", {"date": d, "mode": "PAPER", "asset": t, "side": "BUY", "quantity": sh,
                                         "price": round(px[t] * (1 + c["slippage"]), 2),
                                         "fees": round(sh * px[t] * (c["slippage"] + c["buy_fee"]), 0)})
        st["pending"], st["last_rebalance"] = None, d
        st["n_rebalance"] += int(traded)
    # 2) Định giá cuối phiên
    nav = st["cash"] + sum(s * px[t] for t, s in st["positions"].items())
    _append("paper/nav.csv", {"date": d, "nav": round(nav, 0), "cash": round(st["cash"], 0),
                              "n_positions": len(st["positions"])})
    # 3) Quyết định cho phiên sau
    pos = udates.get_loc(pd.Timestamp(as_of))
    due = st["last_rebalance"] is None or pos - udates.get_loc(pd.Timestamp(st["last_rebalance"])) >= P["rebalance_days"]
    decision = None
    if due:
        active = [k for k, v in reg.items() if v["state"] == "ACTIVE"]
        p = preds_today[preds_today.model_id.isin(active)] if len(preds_today) else preds_today
        if len(active) and len(p):
            p = p.assign(r=p.groupby("model_id")["score"].rank(pct=True),
                         w=p.model_id.map(lambda m: min(reg[m]["backtest"]["ic_t"], 6.0)))
            score = (p.r * p.w).groupby(p.ticker).sum() / p.w.groupby(p.ticker).sum()
            target = list(score.nlargest(P["top_k"]).index)
            decision = {"date": d, "action": "REBALANCE", "targets": ";".join(target), "models": ";".join(active)}
        else:
            target = []
            decision = {"date": d, "action": "NO_ACTION_CASH", "targets": "",
                        "models": "không có mô hình ACTIVE — giữ tiền mặt là quyết định mặc định"}
        if sorted(target) != sorted(st["positions"]):
            st["pending"] = target
        else:
            st["last_rebalance"] = d        # không cần giao dịch; hẹn kỳ sau
        _append("paper/decisions.csv", decision)
    save_json(ST, st)
    return nav, decision
