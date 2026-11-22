"""Paper Trading: quyết định tại close ngày d, KHỚP tại close ngày giao dịch kế tiếp, lô 100, phí + thuế + trượt giá VN.
Giá dùng là GIÁ ĐIỀU CHỈNH neo tại as_of (= giá gốc ngày as_of). Sự kiện quyền xảy ra khi đang nắm giữ được áp vào vị thế:
cổ tức cổ phiếu/chia tách → nhân số cổ phiếu; cổ tức tiền → cộng tiền (sau thuế).
Phiên khóa biên độ (ADR-0008): mã đóng cửa sát giá trần thì lệnh mua KHÔNG khớp, sát giá sàn thì lệnh bán KHÔNG khớp;
lệnh đó giữ lại và thử lại phiên sau. "Sát" = biến động phiên ≥ LOCK_SHARE × biên độ của mã hôm đó (adjust.limits).

Cổng rủi ro trước khi mua (R1a, QĐ-5 của ADR-0016; engine/risk_gate.py), gọi ở hai thời điểm:
  - lúc ra quyết định, với các vị thế sẽ còn giữ sau kỳ (mã đang giữ thuộc mục tiêu): FAIL thì mục tiêu là TOÀN BỘ vị thế đang
    giữ, nên kỳ đó không mua, không bán; mã bị cách ly thì không mua mã đó, mã đang giữ bị cách ly thì vẫn giữ;
  - lúc khớp lệnh mua đang chờ, sau các lệnh bán, với dữ liệu của phiên khớp và MỌI vị thế còn lại (kể cả lệnh bán bị khóa
    sàn): FAIL thì không mua mã nào; mã bị cách ly thì không mua mã đó. Mã bị chặn ghi UNFILLED_RISK_GATE, quyết định ghi
    RISK_GATE_BLOCK_BUY, và mã đó không quay lại hàng chờ.
Cổng không ép bán hay giảm vị thế đang giữ, không theo dõi giữa các lần chạy.

Ngắt khi sụt giảm NAV (R1b; QĐ-5, QĐ-5a của ADR-0016; O-R của Owner: paper.risk_limits.max_drawdown = 15%):
  - Đo: với mỗi phiên s trong (phiên đã đo gần nhất, as_of] trên trục risk_gate.session_axis (lịch HOSE; ngoài vùng lịch theo
    ngày của kho giá), NAV_s = tiền mặt + Σ số cổ phiếu × giá đóng cửa GỐC của phiên s đọc từ kho (data.load_store), KHÔNG dùng
    `close` (đã điều chỉnh, ffill tới 5 phiên). Số cổ phiếu và tiền mặt là trạng thái cuối lần chạy gần nhất trước s, cộng các
    sự kiện quyền có ngày giao dịch ≤ s theo đúng luật apply_corporate_actions. Phiên as_of đo trước khi khớp lệnh của phiên
    đó. Mã đang giữ thiếu giá gốc ở phiên s thì phiên s không đo được; sổ không có vị thế thì NAV = tiền mặt.
    Trạng thái đo ở paper/state.json khóa `dd` (peak, peak_date, checked_through; `runs` là trạng thái cuối các lần chạy cần để
    đo lại); mỗi phiên đã đo ghi một dòng paper/drawdown.csv, chỉ ghi thêm, chạy lại cùng phiên không ghi trùng.
  - Không đo được (thiếu giá gốc, lịch hỏng, thiếu hoặc hỏng max_drawdown): mỗi lần chạy ghi DRAWDOWN_UNVERIFIED kèm phiên và
    lý do; không mở vị thế mới (lệnh mua chờ ghi UNFILLED_RISK_UNVERIFIED); không ép bán; checked_through dừng trước phiên đó.
  - Khóa: phiên đầu tiên có sụt giảm ≥ max_drawdown → `risk_lock` {since, detected_on, drawdown, peak, nav, threshold,
    max_exit_days, exit_sessions, liquidation}; quyết định RISK_CASH_WAIT_OWNER, mục tiêu rỗng; khi khóa còn: không khớp lệnh
    mua (UNFILLED_RISK_LOCK), không chấm mô hình, mỗi kỳ tái cơ cấu chỉ ghi lại RISK_CASH_WAIT_OWNER. NAV phục hồi không gỡ
    khóa. Dữ liệu đóng băng vẫn đo, vẫn khóa.
  - Thanh lý khi khóa (O-R; Owner xác nhận 22/11/2026): từ phiên khớp kế, mỗi phiên mỗi mã bán tối đa max_participation ×
    giá trị giao dịch bình quân adv_sessions phiên (giá và khối lượng GỐC của kho, risk_gate.adv_values), theo giá đóng cửa
    gốc của chính phiên đó. Thiếu giá gốc phiên đó (UNFILLED_NO_PRICE), không đo được giá trị giao dịch bình quân hay giới
    hạn hỏng (UNFILLED_LIQUIDITY), khóa sàn (UNFILLED_LIMIT_DOWN): phiên đó không bán mã đó, thử lại phiên sau. Phần còn lại
    giữ PENDING (quyết định LIQUIDATION_PENDING kèm lý do từng mã). Sau max_exit_days phiên khớp mà còn vị thế: mỗi lần chạy
    ghi LIQUIDATION_OVERDUE (vi phạm), vẫn bán tiếp theo giới hạn. liquidation DONE chỉ khi hết vị thế.
  - Lệnh chờ đặt ở phiên s (pending_set_on) chỉ khớp ở lần chạy có phiên sau s: chạy lại cùng phiên không khớp lệnh nào.
  - Chỉ Owner gỡ (risk_gate.release_check): RISK_LOCK_RELEASED_BY_OWNER, xóa risk_lock, đỉnh = NAV phiên gỡ; thiếu điều kiện
    thì giữ khóa và ghi RISK_LOCK_RELEASE_UNVERIFIED kèm lý do. Còn vị thế (thanh lý PENDING) thì chưa gỡ dù đủ điều kiện
    (Owner xác nhận 22/11/2026): giữ khóa, ghi RISK_LOCK_RELEASE_UNVERIFIED «thanh lý chưa xong, còn N mã», bán tiếp theo
    giới hạn thanh khoản; giá trị gỡ vẫn hiệu lực, lần chạy đầu tiên sau khi thanh lý DONE xét lại và gỡ nếu đủ điều kiện.
    Mã không bán được mãi thì khóa còn mãi, kèm LIQUIDATION_OVERDUE."""
import numpy as np, pandas as pd
from .config import CFG, ROOT, path, load_json, save_json
from . import adjust, data, risk_gate

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

def _ca_events(events, after, upto):
    """Sự kiện quyền APPLIED có ngày giao dịch trong (after, upto]; after None → không sự kiện nào (sổ mới)."""
    if events is None or not len(events) or after is None:
        return []
    ev = events[(events.status == "APPLIED") & (events.trade_date > pd.Timestamp(after))
                & (events.trade_date <= pd.Timestamp(upto))]
    return list(ev.itertuples(index=False))

def _apply_ca(positions, cash, e, d):
    """Áp MỘT sự kiện quyền lên (positions, cash) → (cash mới, dòng sổ giao dịch hoặc None). Dùng chung cho sổ thật
    (apply_corporate_actions) và cho phép đo sụt giảm (_session_navs), nên hai nơi theo đúng một luật."""
    sh = positions.get(e.ticker)
    if not sh:
        return cash, None
    if e.type == "cash_dividend":
        amt = sh * float(e.cash_per_share) * (1 - CFG["costs"].get("dividend_tax", 0.0))
        return cash + amt, {"date": d, "mode": "PAPER", "asset": e.ticker, "side": "CASH_DIVIDEND",
                            "quantity": sh, "price": float(e.cash_per_share), "fees": 0}
    new = int(sh * float(e.ratio))                          # phần lẻ cổ phiếu bị bỏ (thực tế VN trả tiền, bỏ qua)
    positions[e.ticker] = new
    return cash, {"date": d, "mode": "PAPER", "asset": e.ticker, "side": "STOCK_ADJUST",
                  "quantity": new - sh, "price": 0, "fees": 0}

def apply_corporate_actions(st, events, as_of, d):
    """Áp sự kiện quyền có ngày GDKHQ trong (phiên đã xử lý gần nhất, as_of] vào vị thế đang nắm giữ."""
    for e in _ca_events(events, st.get("last_date"), as_of):
        st["cash"], row = _apply_ca(st["positions"], st["cash"], e, d)
        if row is not None:
            _append("paper/trades.csv", row)

DD_CSV = "paper/drawdown.csv"

def _refuse(buys, refused, side, d, px):
    """Từ chối mọi lệnh mua chờ trong `buys` (R1b): ghi một dòng `side` mỗi mã, thêm vào `refused` → danh sách mua rỗng."""
    for t in buys:
        refused.add(t)
        _append("paper/trades.csv", {"date": d, "mode": "PAPER", "asset": t, "side": side,
                                     "quantity": 0, "price": round(float(px[t]), 2), "fees": 0})
    return []

def _dd_state(st, P):
    """Trạng thái đo sụt giảm; sổ cũ chưa có thì khởi tạo: đỉnh = paper.initial_cash, đo từ phiên đã xử lý gần nhất."""
    if st.get("dd"):
        return st["dd"]
    last = st.get("last_date")
    return {"peak": float(P["initial_cash"]), "peak_date": None, "checked_through": last,
            "runs": [{"date": last, "positions": dict(st["positions"]), "cash": st["cash"]}] if last else []}

def _session_navs(dd, start, events, as_of):
    """→ ([(phiên, NAV hoặc None)], lý do khi một phiên không đo được). Phiên: (checked_through, as_of] trên trục phiên HOSE;
    sổ chưa từng đo thì chỉ phiên as_of. Trạng thái nền của phiên s: trạng thái cuối lần chạy gần nhất TRƯỚC s (dd.runs, hoặc
    trạng thái đầu lần chạy này), cộng sự kiện quyền có ngày giao dịch trong (ngày nền, s]. Giá: đóng cửa GỐC của kho."""
    t0 = pd.Timestamp(as_of)
    cal = risk_gate.load_calendar(ROOT)                  # lịch hỏng: ValueError, nơi gọi ghi không đo được
    s = data.load_store(root=ROOT)
    s = s[s.date <= t0]
    raw = s.pivot(index="date", columns="ticker", values="close").sort_index() if len(s) else pd.DataFrame()
    axis = risk_gate.session_axis(list(raw.index) if len(raw) else [t0], cal, until=t0)
    ct = dd.get("checked_through")
    days = [x for x in axis if x <= t0 and (ct is None or x > pd.Timestamp(ct))]
    if ct is None:
        days = [x for x in days if x == t0]
    bases = sorted(dd.get("runs") or [], key=lambda r: r["date"])
    out = []
    for x in days:
        prior = [r for r in bases if r["date"] is not None and pd.Timestamp(r["date"]) < x]
        b = prior[-1] if prior else start
        pos, cash = dict(b["positions"]), b["cash"]
        for e in _ca_events(events, b["date"], x):
            cash, _ = _apply_ca(pos, cash, e, None)
        held = {t: sh for t, sh in pos.items() if sh}
        miss = sorted(t for t in held if t not in raw.columns or x not in raw.index or pd.isna(raw.at[x, t]))
        if miss:
            out.append((x, None))
            return out, f"thiếu giá gốc phiên {x.date()} của mã đang giữ {', '.join(miss)}"
        out.append((x, float(cash + sum(sh * float(raw.at[x, t]) for t, sh in held.items()))))
    return out, None

def _measure_drawdown(dd, start, events, as_of, lim):
    """Đo sụt giảm các phiên chưa đo; cập nhật dd, ghi paper/drawdown.csv. → (dòng chạm ngưỡng hoặc None,
    (phiên, lý do) khi không đo được hoặc None)."""
    d0 = str(pd.Timestamp(as_of).date())
    why = risk_gate.drawdown_problem(lim)
    if why:
        nxt = dd.get("checked_through")
        return None, (d0 if nxt is None else f"sau {nxt}", why)
    try:
        navs, why = _session_navs(dd, start, events, as_of)
    except Exception as e:                              # noqa: BLE001 — lịch hỏng, kho đọc lỗi: không đo được
        return None, (d0, f"{type(e).__name__}: {e}")
    res = risk_gate.drawdown_path(navs, float(dd["peak"]), float(lim["max_drawdown"]), dd.get("peak_date"))
    for r in res["rows"]:
        day = str(pd.Timestamp(r["date"]).date())
        _append(DD_CSV, {"date": day, "nav": round(r["nav"], 0), "peak": round(r["peak"], 0),
                         "drawdown": round(r["drawdown"], 6), "verified": r["verified"]})
        dd["checked_through"], dd["nav"], dd["nav_date"] = day, r["nav"], day
    pdt = res["peak_date"]
    dd["peak"], dd["peak_date"] = res["peak"], (str(pd.Timestamp(pdt).date()) if pdt is not None else None)
    stop = (str(pd.Timestamp(res["stopped_at"]).date()), why) if res["stopped_at"] is not None else None
    breach = res["breach"]
    if breach is not None:
        breach = {**breach, "date": str(pd.Timestamp(breach["date"]).date())}
    return breach, stop

def _lock_text(lock, positions):
    """Trạng thái khóa cho báo cáo phiên: còn vị thế thì không ghi là đã bán. Ngưỡng lấy từ risk_lock (ghi lúc khóa), không
    đọc lại config: ngưỡng trong config hỏng sau khi khóa không làm lần chạy dừng."""
    liq = lock.get("liquidation")
    tail = (f"thanh lý PENDING, còn {len(positions)} mã ({', '.join(sorted(positions))})" if positions
            else f"thanh lý DONE phiên {lock.get('liquidated_on')}" if liq == "DONE" else f"thanh lý {liq}")
    thr = lock.get("threshold")
    thr = f"{thr:.0%}" if isinstance(thr, (int, float)) and not isinstance(thr, bool) else "không rõ"
    return (f"khóa sụt giảm NAV từ phiên {lock['since']} (sụt giảm {lock['drawdown']:.2%} ≥ ngưỡng {thr}; "
            f"đỉnh {lock['peak']:,.0f}; NAV {lock['nav']:,.0f}); {tail}; chờ Owner gỡ bằng paper.risk_lock_release")

def _liquidity(as_of, tickers, lim):
    """Đầu vào cho lệnh thanh lý khi khóa (O-R) → ({mã: giá đóng cửa gốc phiên as_of}, {mã: giá trị giao dịch bình quân},
    {mã: (mã lệnh không khớp, lý do)}). Giá và khối lượng GỐC của kho; giá trị giao dịch bình quân theo risk_gate.adv_values
    trên trục phiên HOSE (như cổng R1a). Mã có trong mục lý do thì phiên này không bán."""
    t0, why = pd.Timestamp(as_of), {}
    bad = risk_gate.limits_problem(lim)
    if bad:
        return {}, {}, {t: ("UNFILLED_LIQUIDITY", bad) for t in tickers}
    try:
        cal = risk_gate.load_calendar(ROOT)
        s = data.load_store(root=ROOT)
        s = s[s.date <= t0]
        raw = s.pivot(index="date", columns="ticker", values="close").sort_index()
        vol = s.pivot(index="date", columns="ticker", values="volume").sort_index()
        axis = risk_gate.session_axis(raw.index, cal, until=t0)
        adv, prob = risk_gate.adv_values(raw, vol, axis, list(tickers), int(lim["adv_sessions"]))
    except Exception as e:                              # noqa: BLE001 — lịch hỏng, kho đọc lỗi: không bán phiên này
        return {}, {}, {t: ("UNFILLED_LIQUIDITY", f"{type(e).__name__}: {e}") for t in tickers}
    price = {}
    for t in tickers:
        p = raw.at[t0, t] if t in raw.columns and t0 in raw.index else np.nan
        if not (pd.notna(p) and np.isfinite(float(p)) and float(p) > 0):
            why[t] = ("UNFILLED_NO_PRICE", f"thiếu giá đóng cửa gốc phiên {t0.date()}")
        elif t in prob:
            why[t] = ("UNFILLED_LIQUIDITY", f"không đo được giá trị giao dịch bình quân {int(lim['adv_sessions'])} phiên: "
                                            f"{prob[t]}")
        else:
            price[t] = float(p)
    return price, adv, why

def _exit_days(lim, lock):
    """max_exit_days đang dùng: của config nếu giới hạn hợp lệ, không thì giá trị ghi lúc khóa (có thể None)."""
    return int(lim["max_exit_days"]) if risk_gate.limits_problem(lim) is None else lock.get("max_exit_days")

def _market(as_of, tickers, px, frozen):
    """Đầu vào thị trường cho risk_gate.check tại as_of (mục tiêu và vị thế còn giữ): dữ liệu CHỈ ĐỌC dưới ROOT cộng giá."""
    snap = risk_gate.market_snapshot(as_of, list(dict.fromkeys(tickers)), CFG["paper"].get("risk_limits"), root=ROOT,
                                     frozen=frozen)
    return {**snap, "price": {t: float(px[t]) for t in px.index if pd.notna(px[t])}}

def run(as_of, close, preds_today, reg, udates, events=None, frozen=False):
    """frozen=True (dữ liệu lỗi vượt ngưỡng): chỉ định giá, không khớp lệnh chờ, không ra quyết định mới."""
    c, lot, P = CFG["costs"], CFG["lot_size"], CFG["paper"]
    lim = P.get("risk_limits")
    st = load_json(ST, {"cash": P["initial_cash"], "positions": {}, "pending": None,
                        "last_rebalance": None, "costs_paid": 0.0, "n_rebalance": 0})
    px = close.loc[pd.Timestamp(as_of)]
    d = str(pd.Timestamp(as_of).date())
    start = {"date": st.get("last_date"), "positions": dict(st["positions"]), "cash": st["cash"]}
    dd = _dd_state(st, P)
    apply_corporate_actions(st, events, as_of, d)
    st["last_date"] = d
    # R1b: đo sụt giảm mọi phiên chưa đo tới as_of, TRƯỚC khi khớp lệnh; khóa ở phiên đầu tiên chạm ngưỡng
    breach, unverified = _measure_drawdown(dd, start, events, as_of, lim)
    new_lock = breach is not None and not st.get("risk_lock")
    if new_lock:
        st["risk_lock"] = {"since": breach["date"], "detected_on": d, "drawdown": round(breach["drawdown"], 6),
                           "peak": round(breach["peak"], 0), "nav": round(breach["nav"], 0),
                           "threshold": float(lim["max_drawdown"]),
                           "max_exit_days": int(lim["max_exit_days"]) if risk_gate.limits_problem(lim) is None else None,
                           "exit_sessions": 0, "liquidation": "PENDING"}
    release = None                                     # (hành động, lý do) của việc Owner gỡ khóa ở lần chạy này
    if st.get("risk_lock") and not new_lock:
        ok, why = risk_gate.release_check(st["risk_lock"], P.get("risk_lock_release"), root=ROOT)
        if ok and dd.get("nav_date") != d:
            ok, why = False, f"chưa đo được NAV phiên gỡ {d} để đặt lại đỉnh"
        if ok and st["positions"]:      # Owner 22/11/2026: thanh lý chưa xong thì chưa gỡ, bán tiếp theo giới hạn O-R
            held = sorted(st["positions"])
            ok, why = False, (f"thanh lý chưa xong, còn {len(held)} mã ({', '.join(held)}); tiếp tục bán theo giới hạn "
                              f"thanh khoản, giá trị gỡ vẫn hiệu lực và được xét lại ở lần chạy đầu tiên sau khi thanh lý "
                              f"xong ({why})")
        if ok:
            lk = st.pop("risk_lock")
            dd["peak"], dd["peak_date"] = float(dd["nav"]), d
            st["risk_lock_released"] = {"since": lk["since"], "on": d}
            release = ("RISK_LOCK_RELEASED_BY_OWNER", f"Owner gỡ khóa sụt giảm từ phiên {lk['since']}: {why}; đỉnh đặt lại = NAV "
                                                      f"phiên {d} ({dd['peak']:,.0f})")
        elif why is not None:
            release = ("RISK_LOCK_RELEASE_UNVERIFIED", f"giữ khóa từ phiên {st['risk_lock']['since']}: {why}")
    # 1) Khớp lệnh đã quyết định phiên trước
    # R1b vòng 2: lệnh chờ đặt ở phiên s chỉ khớp ở phiên sau s (chạy lại cùng phiên không khớp, không ghi giao dịch)
    fillable = st.get("pending_set_on") is None or d > st["pending_set_on"]
    if st["pending"] is not None and not frozen and fillable:
        target = st["pending"]
        traded = False
        up, down = locked(close, as_of)
        blocked = []
        sells = [t for t in st["positions"] if t not in target]
        liq = bool(st.get("risk_lock")) and bool(sells)        # R1b: thanh lý khi khóa, theo giới hạn thanh khoản (O-R)
        if liq:
            st["risk_lock"]["exit_sessions"] = int(st["risk_lock"].get("exit_sessions") or 0) + 1
            lpx, ladv, lwhy = _liquidity(as_of, sells, lim)
            notes = []
        for t in sells:
            if t in down:                                   # khóa sàn: không bán được, giữ lại và thử phiên sau
                blocked.append(t)
                _append("paper/trades.csv", {"date": d, "mode": "PAPER", "asset": t, "side": "UNFILLED_LIMIT_DOWN",
                                             "quantity": 0, "price": round(float(px[t]), 2), "fees": 0})
                if liq:
                    notes.append(f"{t}: khóa sàn")
                continue
            if liq:
                held = st["positions"][t]
                if t in lwhy:
                    side, why = lwhy[t]
                    blocked.append(t)
                    notes.append(f"{t}: {why}")
                    _append("paper/trades.csv", {"date": d, "mode": "PAPER", "asset": t, "side": side, "quantity": 0,
                                                 "price": round(float(px[t]), 2) if pd.notna(px.get(t)) else 0, "fees": 0})
                    continue
                cap = int(float(lim["max_participation"]) * ladv[t] / lpx[t])
                sh = held if cap >= held else cap // lot * lot
                if sh <= 0:
                    blocked.append(t)
                    notes.append(f"{t}: giới hạn {float(lim['max_participation']):.0%} × giá trị giao dịch bình quân "
                                 f"{int(lim['adv_sessions'])} phiên = {cap:,} cp, chưa đủ một lô")
                    _append("paper/trades.csv", {"date": d, "mode": "PAPER", "asset": t, "side": "UNFILLED_LIQUIDITY",
                                                 "quantity": 0, "price": round(lpx[t], 2), "fees": 0})
                    continue
                p = lpx[t] * (1 - c["slippage"])
                st["cash"] += sh * p * (1 - c["sell_fee"] - c["sell_tax"])
                cost = sh * lpx[t] * c["slippage"] + sh * p * (c["sell_fee"] + c["sell_tax"])
                st["costs_paid"] += cost; traded = True
                _append("paper/trades.csv", {"date": d, "mode": "PAPER", "asset": t, "side": "SELL", "quantity": sh,
                                             "price": round(p, 2), "fees": round(cost, 0)})
                if sh < held:
                    st["positions"][t] = held - sh
                    blocked.append(t)
                    notes.append(f"{t}: bán {sh:,}/{held:,} cp (giới hạn {float(lim['max_participation']):.0%} × giá trị "
                                 f"giao dịch bình quân {int(lim['adv_sessions'])} phiên = {cap:,} cp), còn {held - sh:,}")
                else:
                    st["positions"].pop(t)
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
        refused = set()
        if buys and st.get("risk_lock"):    # R1b: khóa sụt giảm còn: không mua mã nào, không cần xét cổng R1a
            buys = _refuse(buys, refused, "UNFILLED_RISK_LOCK", d, px)
        if buys:        # R1a: lệnh mua chờ qua lại cổng ở chính phiên khớp, sau lệnh bán, với mọi vị thế còn lại
            g = risk_gate.check(target, {"nav": nav, "positions": st["positions"]},
                                _market(as_of, list(target) + list(st["positions"]), px, frozen), lim)
            refused = set(buys) if g["verdict"] == "FAIL" else set(g["excluded"]) & set(buys)
            if refused:
                for t in [t for t in buys if t in refused]:
                    _append("paper/trades.csv", {"date": d, "mode": "PAPER", "asset": t, "side": "UNFILLED_RISK_GATE",
                                                 "quantity": 0, "price": round(float(px[t]), 2), "fees": 0})
                _append("paper/decisions.csv", {"date": d, "action": "RISK_GATE_BLOCK_BUY",
                                                "targets": ";".join(t for t in buys if t in refused),
                                                "models": f"cổng rủi ro ở phiên khớp {g['verdict']}: " + "; ".join(g["reasons"])})
                buys = [t for t in buys if t not in refused]
        if buys and unverified is not None:    # R1b: sụt giảm không đo được: không mở vị thế mới (sau cổng R1a)
            buys = _refuse(buys, refused, "UNFILLED_RISK_UNVERIFIED", d, px)
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
        if liq and st["positions"]:
            _append("paper/decisions.csv", {"date": d, "action": "LIQUIDATION_PENDING", "targets": "",
                                            "models": f"phiên khớp thanh lý thứ {st['risk_lock']['exit_sessions']}: "
                                                      + "; ".join(notes)})
        # Còn lệnh chưa khớp vì khóa biên độ → thử lại phiên sau, với các mã của mục tiêu mà cổng chưa từ chối ở phiên này.
        st["pending"] = [t for t in target if t not in refused] if blocked else None
        st["last_rebalance"] = d
        st["n_rebalance"] += int(traded)
    lock = st.get("risk_lock")
    if lock and lock.get("liquidation") == "PENDING" and not st["positions"]:
        lock["liquidation"], lock["liquidated_on"] = "DONE", d
    # 2) Định giá cuối phiên
    nav = st["cash"] + sum(s * px[t] for t, s in st["positions"].items())
    _append("paper/nav.csv", {"date": d, "nav": round(nav, 0), "cash": round(st["cash"], 0),
                              "n_positions": len(st["positions"])})
    # 3) Quyết định cho phiên sau
    pos = udates.get_loc(pd.Timestamp(as_of))
    due = st["last_rebalance"] is None or pos - udates.get_loc(pd.Timestamp(st["last_rebalance"])) >= P["rebalance_days"]
    decision = None
    if unverified is not None:          # R1b: mỗi lần chạy không đo được ghi một quyết định
        decision = {"date": d, "action": "DRAWDOWN_UNVERIFIED", "targets": "",
                    "models": f"phiên {unverified[0]}: {unverified[1]} — không mở vị thế mới, không ép bán; lần chạy sau đo "
                              f"lại từ phiên này"}
        _append("paper/decisions.csv", decision)
    if release is not None:
        decision = {"date": d, "action": release[0], "targets": "", "models": release[1]}
        _append("paper/decisions.csv", decision)
    lock = st.get("risk_lock")
    if lock and st["positions"]:
        st["pending"] = []              # thanh lý từ phiên khớp kế, theo giới hạn thanh khoản; phần chưa bán thử lại mỗi lần chạy
        n_exit = _exit_days(lim, lock)
        if n_exit is not None and int(lock.get("exit_sessions") or 0) >= n_exit:
            lock.setdefault("overdue_since", d)
            _append("paper/decisions.csv", {
                "date": d, "action": "LIQUIDATION_OVERDUE", "targets": "",
                "models": f"vi phạm O-R: đã {lock['exit_sessions']} phiên khớp thanh lý (max_exit_days {n_exit}) mà còn "
                          f"{len(st['positions'])} mã ({', '.join(sorted(st['positions']))}); vẫn bán tiếp theo giới hạn"})
    if lock and (new_lock or (due and not frozen)):
        decision = {"date": d, "action": "RISK_CASH_WAIT_OWNER", "targets": "", "models": _lock_text(lock, st["positions"])}
        _append("paper/decisions.csv", decision)
        st["last_rebalance"] = d
    if frozen:
        decision = {"date": d, "action": "NO_DECISION_DATA_QUALITY", "targets": "",
                    "models": "tỷ lệ lỗi dữ liệu vượt ngưỡng — không khớp lệnh, không ra quyết định"}
        _append("paper/decisions.csv", decision)
    elif lock:
        pass                            # khóa: không chấm mô hình; mục tiêu rỗng đã đặt ở trên
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
        if target:      # R1a: cổng rủi ro trước khi ghi quyết định. Cổng không ép bán vị thế đang giữ.
            keep = {t: s for t, s in st["positions"].items() if t in target}      # vị thế sẽ còn giữ sau kỳ
            g = risk_gate.check(target, {"nav": nav, "positions": keep}, _market(as_of, target, px, frozen), lim)
            if g["verdict"] == "FAIL" or g["excluded"]:
                fail = g["verdict"] == "FAIL"
                target = list(st["positions"]) if fail else \
                    [t for t in target if t not in g["excluded"] or t in st["positions"]]
                decision = {"date": d, "action": "RISK_GATE_FAIL" if fail else decision["action"],
                            "targets": ";".join(target),
                            "models": f"{decision['models']} | cổng rủi ro {g['verdict']}: " + "; ".join(g["reasons"])}
        if sorted(target) != sorted(st["positions"]):
            st["pending"] = target
        else:
            st["last_rebalance"] = d        # không cần giao dịch; hẹn kỳ sau
        _append("paper/decisions.csv", decision)
    # R1b: trạng thái cuối lần chạy này làm nền đo các phiên sau; chỉ giữ nền còn cần (từ lần chạy cuối ≤ checked_through)
    runs = [r for r in dd.get("runs") or [] if r["date"] != d] + [{"date": d, "positions": dict(st["positions"]),
                                                                    "cash": st["cash"]}]
    ct = dd.get("checked_through")
    done = [r["date"] for r in runs if ct is not None and r["date"] <= ct]
    dd["runs"] = [r for r in runs if not done or r["date"] >= max(done)]
    st["dd"] = dd
    if st["pending"] is None:           # R1b vòng 2: phiên đặt (hoặc đặt lại) lệnh chờ; khớp từ phiên sau
        st.pop("pending_set_on", None)
    else:
        st["pending_set_on"] = d
    save_json(ST, st)
    return nav, decision
