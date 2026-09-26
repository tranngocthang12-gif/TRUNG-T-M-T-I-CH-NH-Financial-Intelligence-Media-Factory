"""Attribution & Counterfactual: tách beta thị trường khỏi alpha; so với 'không làm gì' và chỉ số."""
import numpy as np, pandas as pd
from .config import CFG, ROOT, save_json, load_json
from .regime import market_returns

def run(close, bad=None):
    p = ROOT / "paper/nav.csv"
    if not p.exists():
        return None
    nav = pd.read_csv(p, parse_dates=["date"]).drop_duplicates("date", keep="last").set_index("date")["nav"]
    if len(nav) < 20:
        return {"status": "CHƯA ĐỦ DỮ LIỆU", "n_days": int(len(nav))}
    r = nav.pct_change().dropna()
    m = market_returns(close, bad).reindex(r.index).fillna(0)
    beta = float(np.cov(r, m)[0, 1] / m.var()) if m.var() > 0 else 0.0
    resid = r - beta * m
    t_alpha = float(resid.mean() / resid.std() * np.sqrt(len(resid))) if resid.std() > 0 else 0.0
    st = load_json("paper/state.json", {})
    nreb = st.get("n_rebalance", 0)
    if nreb < 12:
        skill = f"CHƯA ĐỦ MẪU ({nreb} lần tái cơ cấu < 12) — không kết luận về kỹ năng"
    elif t_alpha >= 2:
        skill = "CÓ DẤU HIỆU ALPHA (t ≥ 2) — cần tiếp tục theo dõi"
    else:
        skill = "CHƯA PHÂN BIỆT ĐƯỢC VỚI MAY MẮN"
    rep = {"period": {"start": str(nav.index[0].date()), "end": str(nav.index[-1].date()), "n_days": int(len(r))},
           "actual_return": float(nav.iloc[-1] / nav.iloc[0] - 1),
           "counterfactuals": {"no_trade": 0.0, "index": float((1 + m).prod() - 1)},
           "components": {"market_beta": beta, "beta_return": float((1 + beta * m).prod() - 1),
                          "residual_alpha_ann": float(resid.mean() * 252), "alpha_t": t_alpha},
           "costs_paid": float(st.get("costs_paid", 0)), "n_rebalance": nreb, "skill_assessment": skill}
    save_json("reports/attribution_latest.json", rep)
    return rep
