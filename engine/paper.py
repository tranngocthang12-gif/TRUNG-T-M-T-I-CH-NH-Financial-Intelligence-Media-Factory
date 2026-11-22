"""Paper Trading: quyết định tại close ngày d, KHỚP tại close ngày giao dịch kế tiếp, lô 100, phí + thuế + trượt giá VN.
Giá dùng là GIÁ ĐIỀU CHỈNH neo tại as_of (= giá gốc ngày as_of). Sự kiện quyền xảy ra khi đang nắm giữ được áp vào vị thế:
cổ tức cổ phiếu/chia tách → nhân số cổ phiếu; cổ tức tiền → cộng tiền (sau thuế).
Phiên khóa biên độ (ADR-0008): mã đóng cửa sát giá trần thì lệnh mua KHÔNG khớp, sát giá sàn thì lệnh bán KHÔNG khớp;
lệnh đó giữ lại và thử lại phiên sau. "Sát" = biến động phiên ≥ LOCK_SHARE × biên độ của mã hôm đó (adjust.limits).

Khóa rủi ro (R1, QĐ-5 của ADR-0016). Sau khi định giá, MỌI phiên (kể cả ngoài kỳ tái cơ cấu và khi dữ liệu đóng băng) đo sụt
giảm NAV từ đỉnh bằng engine.risk_gate.breach. Chạm max_drawdown thì ghi `risk_lock` = {since, reason} vào paper/state.json,
ghi quyết định RISK_CASH_WAIT_OWNER, đặt lệnh bán hết cho phiên sau. Khi khóa còn đó: không khớp lệnh mua nào, lệnh bán hết
được giữ và thử lại tới khi xong (kể cả khi khóa sàn), mỗi kỳ tái cơ cấu chỉ ghi lại RISK_CASH_WAIT_OWNER, không chấm mô hình,
không mở vị thế mới; NAV phục hồi cũng không gỡ khóa. Chỉ Owner gỡ: ghi đúng ngày `risk_lock.since` vào
config.yaml paper.risk_lock_release (đi PR, Owner gộp). Gỡ xong thì ghi RISK_LOCK_RELEASED_BY_OWNER và tính lại đỉnh NAV từ
phiên gỡ (`risk_lock_released.on`).

Sổ có thể không chạy mỗi phiên (vòng học chạy hằng tuần). Trước khi khớp lệnh, sổ định giá vị thế đang giữ ở TỪNG phiên của
bảng giá nằm giữa lần chạy trước và as_of (nav_between_runs) và đo sụt giảm ở từng phiên đó; chạm ngưỡng thì khóa ngay, trước
khi khớp. Các NAV giữa hai lần chạy chỉ dùng để đo, không ghi vào paper/nav.csv.

Lệnh mua đang chờ phải qua lại cổng rủi ro (risk_gate.check) ở chính phiên khớp, với NAV, lịch sử NAV, giới hạn và dữ liệu thị
trường của phiên đó. Cổng FAIL (kể cả vì mất lịch sử NAV hay giới hạn hỏng) thì không mua mã nào; mã bị cách ly thì không mua
mã đó. Lệnh mua bị chặn ghi UNFILLED_RISK_GATE và quyết định RISK_GATE_BLOCK_BUY, không thử lại; lệnh bán vẫn khớp."""
import numpy as np, pandas as pd
from .config import CFG, ROOT, path, load_json, save_json
from . import adjust, risk_gate

LOCK_SHARE = 0.95          # 95% biên độ: HOSE ±7% → ≥ +6,65% coi như khóa trần (giá trần làm tròn bước giá nên thấp hơn 7%)

def locked(close, as_of):
    """→ (mã khóa trần, mã khóa sàn) tại phiên as_of, theo biến động giá điều chỉnh so với phiên trước trong bảng giá.
    Phép xấp xỉ thận trọng: đóng cửa ở giá trần không luôn nghĩa là trắng bên bán, nhưng giấy không được giả định khớp
    ở nơi thị trường thật có thể không khớp."""
    t = pd.Timestamp(as_of)
    hist = close.loc[:t]
    if len(hist) < 2 or hist.index[-1] != t:
        return set(), set()
    r = hist.iloc[-1] / hist.iloc[-2] - 1
    L = adjust.limits(pd.Index([t]), close.columns).iloc[0]
    up = {c for c in close.columns if pd.notna(r.get(c)) and r[c] >= LOCK_SHARE * L[c]}
    down = {c for c in close.columns if pd.notna(r.get(c)) and r[c] <= -LOCK_SHARE * L[c]}
    return up, down

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

def nav_between_runs(close, st, prev_last, as_of):
    """[(ngày ISO, NAV)] của vị thế đang giữ tại mỗi phiên của bảng giá nằm GIỮA lần chạy trước và as_of (không gồm hai đầu).
    NAV không đo được (thiếu giá) thì bỏ phiên đó."""
    if prev_last is None:
        return []
    lo, hi = pd.Timestamp(prev_last), pd.Timestamp(as_of)
    out = []
    for s in close.index[(close.index > lo) & (close.index < hi)]:
        row = close.loc[s]
        v = st["cash"] + sum(sh * row.get(t, np.nan) for t, sh in st["positions"].items())
        if np.isfinite(v):
            out.append((str(s.date()), float(v)))
    return out

def owner_release(st, d):
    """Gỡ khóa rủi ro khi Owner ghi đúng ngày bắt đầu khóa vào config.yaml paper.risk_lock_release. → True nếu đã gỡ."""
    lock, rel = st.get("risk_lock"), CFG["paper"].get("risk_lock_release")
    if not lock or rel is None or str(rel) != lock.get("since"):
        return False
    st.pop("risk_lock")
    st["risk_lock_released"] = {"since": lock["since"], "on": d}
    _append("paper/decisions.csv", {"date": d, "action": "RISK_LOCK_RELEASED_BY_OWNER", "targets": "",
                                    "models": f"Owner gỡ khóa rủi ro từ phiên {lock['since']} bằng paper.risk_lock_release; "
                                              f"đỉnh NAV tính lại từ phiên {d}"})
    return True

def run(as_of, close, preds_today, reg, udates, events=None, frozen=False):
    """frozen=True (dữ liệu lỗi vượt ngưỡng): chỉ định giá, không khớp lệnh chờ, không ra quyết định mới."""
    c, lot, P = CFG["costs"], CFG["lot_size"], CFG["paper"]
    st = load_json(ST, {"cash": P["initial_cash"], "positions": {}, "pending": None,
                        "last_rebalance": None, "costs_paid": 0.0, "n_rebalance": 0})
    px = close.loc[pd.Timestamp(as_of)]
    d = str(pd.Timestamp(as_of).date())
    prev_last = st.get("last_date")                         # phiên gần nhất đã xử lý TRƯỚC lần chạy này
    apply_corporate_actions(st, events, as_of, d)
    st["last_date"] = d
    owner_release(st, d)
    lim = P.get("risk_limits")
    rel_on = (st.get("risk_lock_released") or {}).get("on")
    # 0) Sụt giảm ở các phiên giữa lần chạy trước và as_of: đo trước khi khớp lệnh.
    mids = [(s_, v) for s_, v in nav_between_runs(close, st, prev_last, as_of) if rel_on is None or s_ >= rel_on]
    locked_now = False
    base, _ = risk_gate.read_nav_history(ROOT, as_of, 0.0, last_date=prev_last, initial_cash=P["initial_cash"], since=rel_on,
                                         lower_bound=True)
    if base is not None and not st.get("risk_lock"):
        seq = base[:-1]
        for s_, v in mids:
            why = risk_gate.breach(seq + [v], v, lim)
            if why:
                st["risk_lock"] = {"since": d, "reason": f"{why} ở phiên {s_}, giữa hai lần chạy sổ giấy"}
                locked_now = True
                break
            seq.append(v)
    if locked_now and st["positions"] and st["pending"] is None:
        st["pending"] = []                                  # bán hết ngay ở phiên khớp này, như khi chạy mỗi phiên

    def history(nav_now, lower_bound=False):
        """Lịch sử NAV để đo tại as_of: các dòng trước as_of, các phiên giữa hai lần chạy, rồi NAV hiện tại. lower_bound=True
        chỉ dùng để dò chạm ngưỡng (xem risk_gate.read_nav_history)."""
        h, why = risk_gate.read_nav_history(ROOT, as_of, nav_now, last_date=prev_last, initial_cash=P["initial_cash"],
                                            since=rel_on, lower_bound=lower_bound)
        return (None, why) if h is None else (h[:-1] + [v for _, v in mids] + h[-1:], None)

    # 1) Khớp lệnh đã quyết định phiên trước. Đang khóa rủi ro thì mục tiêu luôn rỗng: chỉ bán, không mua.
    if st["pending"] is not None and not frozen:
        target = [] if st.get("risk_lock") else st["pending"]
        traded = False
        up, down = locked(close, as_of)
        blocked = []
        for t in [t for t in st["positions"] if t not in target]:
            if t in down:                                   # khóa sàn: không bán được, giữ lại và thử phiên sau
                blocked.append(t)
                _append("paper/trades.csv", {"date": d, "mode": "PAPER", "asset": t, "side": "UNFILLED_LIMIT_DOWN",
                                             "quantity": 0, "price": round(float(px[t]), 2), "fees": 0})
                continue
            sh = st["positions"].pop(t); p = px[t] * (1 - c["slippage"])
            st["cash"] += sh * p * (1 - c["sell_fee"] - c["sell_tax"])
            cost = sh * px[t] * c["slippage"] + sh * p * (c["sell_fee"] + c["sell_tax"])
            st["costs_paid"] += cost; traded = True
            _append("paper/trades.csv", {"date": d, "mode": "PAPER", "asset": t, "side": "SELL", "quantity": sh,
                                         "price": round(p, 2), "fees": round(cost, 0)})
        nav = st["cash"] + sum(s * px[t] for t, s in st["positions"].items())
        buys = [t for t in target if t not in st["positions"] and pd.notna(px.get(t))]
        per = nav / max(1, len(target)) * 0.995
        if buys:        # R1: lệnh mua chờ qua lại cổng rủi ro ở chính phiên khớp, với dữ liệu của phiên này
            h, hw = history(nav)
            g = risk_gate.check(target, {"nav": nav, "positions": st["positions"]},
                                {**risk_gate.market_snapshot(as_of, target, lim, root=ROOT, frozen=frozen, nav_history=h,
                                                             nav_history_problem=hw),
                                 "price": {t: float(px[t]) for t in px.index if pd.notna(px[t])}}, lim)
            stop = set(buys) if g["verdict"] == "FAIL" else set(g["excluded"]) & set(buys)
            if stop:
                for t in [t for t in buys if t in stop]:
                    _append("paper/trades.csv", {"date": d, "mode": "PAPER", "asset": t, "side": "UNFILLED_RISK_GATE",
                                                 "quantity": 0, "price": round(float(px[t]), 2), "fees": 0})
                _append("paper/decisions.csv", {"date": d, "action": "RISK_GATE_BLOCK_BUY",
                                                "targets": ";".join(t for t in buys if t in stop),
                                                "models": f"cổng rủi ro ở phiên khớp {g['verdict']}: " + "; ".join(g["reasons"])})
                buys = [t for t in buys if t not in stop]
        for t in [t for t in buys if t in up]:              # khóa trần: không mua được, giữ lại và thử phiên sau
            blocked.append(t)
            _append("paper/trades.csv", {"date": d, "mode": "PAPER", "asset": t, "side": "UNFILLED_LIMIT_UP",
                                         "quantity": 0, "price": round(float(px[t]), 2), "fees": 0})
        for t in [t for t in buys if t not in up]:
            unit = px[t] * (1 + c["slippage"]) * (1 + c["buy_fee"])
            sh = int(min(per, st["cash"]) // unit // lot * lot)
            if sh <= 0:
                continue
            st["cash"] -= sh * unit; st["positions"][t] = sh; traded = True
            st["costs_paid"] += sh * px[t] * (c["slippage"] + c["buy_fee"])
            _append("paper/trades.csv", {"date": d, "mode": "PAPER", "asset": t, "side": "BUY", "quantity": sh,
                                         "price": round(px[t] * (1 + c["slippage"]), 2),
                                         "fees": round(sh * px[t] * (c["slippage"] + c["buy_fee"]), 0)})
        st["pending"] = target if blocked else None         # còn lệnh chưa khớp vì khóa biên độ → thử lại phiên sau
        st["last_rebalance"] = d
        st["n_rebalance"] += int(traded)
    # 2) Định giá cuối phiên
    nav = st["cash"] + sum(s * px[t] for t, s in st["positions"].items())
    _append("paper/nav.csv", {"date": d, "nav": round(nav, 0), "cash": round(st["cash"], 0),
                              "n_positions": len(st["positions"])})
    # 2b) Sụt giảm NAV từ đỉnh: đo MỖI phiên định giá, không chờ kỳ tái cơ cấu (R1).
    hist, hist_why = history(nav)
    if not st.get("risk_lock"):
        why = risk_gate.breach(history(nav, lower_bound=True)[0], nav, lim)
        if why:
            st["risk_lock"] = {"since": d, "reason": why}
            locked_now = True
    # 3) Quyết định cho phiên sau
    pos = udates.get_loc(pd.Timestamp(as_of))
    due = st["last_rebalance"] is None or pos - udates.get_loc(pd.Timestamp(st["last_rebalance"])) >= P["rebalance_days"]
    decision = None
    if st.get("risk_lock"):
        st["pending"] = [] if st["positions"] else None     # bán hết; lệnh bán chưa khớp được giữ và thử lại phiên sau
        if locked_now or due:
            lk = st["risk_lock"]
            decision = {"date": d, "action": "RISK_CASH_WAIT_OWNER", "targets": "",
                        "models": f"khóa rủi ro từ phiên {lk['since']}: {lk['reason']} — bán hết, không mở vị thế mới; "
                                  f"chờ Owner gỡ bằng paper.risk_lock_release"}
            st["last_rebalance"] = d
            _append("paper/decisions.csv", decision)
    elif frozen:
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
        if target:      # R1 (QĐ-5, ADR-0016): cổng rủi ro trước khi ghi quyết định. FAIL thì không mở vị thế mới.
            g = risk_gate.check(target, {"nav": nav, "positions": st["positions"]},
                                {**risk_gate.market_snapshot(as_of, target, lim, root=ROOT, frozen=frozen, nav_history=hist,
                                                             nav_history_problem=hist_why),
                                 "price": {t: float(px[t]) for t in px.index if pd.notna(px[t])}}, lim)
            if g["cash_wait_owner"]:                        # cùng lịch sử với bước 2b nên hiếm khi tới đây; vẫn khóa
                st["risk_lock"] = {"since": d, "reason": "; ".join(g["reasons"])}
            if g["verdict"] == "FAIL" or g["excluded"]:
                fail = g["verdict"] == "FAIL"
                target = ([] if g["cash_wait_owner"] else [t for t in g["targets"] if t in st["positions"]]) if fail \
                    else g["targets"]
                decision = {"date": d, "action": ("RISK_CASH_WAIT_OWNER" if g["cash_wait_owner"] else "RISK_GATE_FAIL")
                            if fail else decision["action"], "targets": ";".join(target),
                            "models": f"{decision['models']} | cổng rủi ro {g['verdict']}: " + "; ".join(g["reasons"])}
        if sorted(target) != sorted(st["positions"]):
            st["pending"] = target
        else:
            st["last_rebalance"] = d        # không cần giao dịch; hẹn kỳ sau
        _append("paper/decisions.csv", decision)
    save_json(ST, st)
    return nav, decision
