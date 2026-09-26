"""Paper Trading: quyết định tại close ngày d, KHỚP tại close ngày giao dịch kế tiếp, lô 100, phí + thuế + trượt giá VN.
Giá dùng là GIÁ ĐIỀU CHỈNH neo tại as_of (= giá gốc ngày as_of). Sự kiện quyền xảy ra khi đang nắm giữ được áp vào vị thế:
cổ tức cổ phiếu/chia tách → nhân số cổ phiếu; cổ tức tiền → cộng tiền (sau thuế)."""
import numpy as np, pandas as pd
from .config import CFG, ROOT, path, load_json, save_json

ST = "paper/state.json"

def _append(rel, row):
    p = ROOT / rel
    df = pd.DataFrame([row])
    df.to_csv(path(rel), mode="a", header=not p.exists(), index=False)

def apply_corporate_actions(st, events, as_of, d):
    """Áp sự kiện quyền có ngày GDKHQ trong (phiên đã xử lý gần nhất, as_of] vào vị thế đang nắm giữ."""
    last = st.get("last_date")
    if events is None or not len(events) or last is None:
        return
    ev = events[(events.status == "APPLIED") & (events.trade_date > pd.Timestamp(last))
                & (events.trade_date <= pd.Timestamp(as_of))]
    for e in ev.itertuples(index=False):
        sh = st["positions"].get(e.ticker)
        if not sh:
            continue
        if e.type == "cash_dividend":
            amt = sh * float(e.cash_per_share) * (1 - CFG["costs"].get("dividend_tax", 0.0))
            st["cash"] += amt
            _append("paper/trades.csv", {"date": d, "mode": "PAPER", "asset": e.ticker, "side": "CASH_DIVIDEND",
                                         "quantity": sh, "price": float(e.cash_per_share), "fees": 0})
        else:
            new = int(sh * float(e.ratio))                  # phần lẻ cổ phiếu bị bỏ (thực tế VN trả tiền, bỏ qua)
            st["positions"][e.ticker] = new
            _append("paper/trades.csv", {"date": d, "mode": "PAPER", "asset": e.ticker, "side": "STOCK_ADJUST",
                                         "quantity": new - sh, "price": 0, "fees": 0})

def run(as_of, close, preds_today, reg, udates, events=None, frozen=False):
    """frozen=True (dữ liệu lỗi vượt ngưỡng): chỉ định giá, không khớp lệnh chờ, không ra quyết định mới."""
    c, lot, P = CFG["costs"], CFG["lot_size"], CFG["paper"]
    st = load_json(ST, {"cash": P["initial_cash"], "positions": {}, "pending": None,
                        "last_rebalance": None, "costs_paid": 0.0, "n_rebalance": 0})
    px = close.loc[pd.Timestamp(as_of)]
    d = str(pd.Timestamp(as_of).date())
    apply_corporate_actions(st, events, as_of, d)
    st["last_date"] = d
    # 1) Khớp lệnh đã quyết định phiên trước
    if st["pending"] is not None and not frozen:
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
    if frozen:
        decision = {"date": d, "action": "NO_DECISION_DATA_QUALITY", "targets": "",
                    "models": "tỷ lệ lỗi dữ liệu vượt ngưỡng — không khớp lệnh, không ra quyết định"}
        _append("paper/decisions.csv", decision)
    elif due:
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
