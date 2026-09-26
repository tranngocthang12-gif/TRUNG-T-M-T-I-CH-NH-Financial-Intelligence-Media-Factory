"""Research & Backtest Engine: walk-forward có embargo, chi phí thật, ngưỡng thống kê tăng theo số lần thử."""
import hashlib, json
from statistics import NormalDist
import numpy as np, pandas as pd
from sklearn.linear_model import Ridge
from sklearn.ensemble import HistGradientBoostingRegressor
from .config import CFG, ROUNDTRIP

MODELS = ["ridge", "gbm", "signed_sum"]

def spec_id(spec):
    s = json.dumps({"f": sorted(spec["features"]), "m": spec["model"]})
    return "M-" + hashlib.sha1(s.encode()).hexdigest()[:10]

def fit(model, X, y):
    if model == "ridge":
        return ("sk", Ridge(alpha=1.0).fit(X, y))
    if model == "gbm":
        return ("sk", HistGradientBoostingRegressor(max_iter=80, max_depth=3, learning_rate=0.05,
                                                    min_samples_leaf=200, random_state=0).fit(X, y))
    signs = np.array([np.nan_to_num(np.corrcoef(X[:, j], y)[0, 1]) for j in range(X.shape[1])])
    return ("sum", np.sign(signs))

def predict(f, X):
    kind, m = f
    return m.predict(X) if kind == "sk" else X @ m

def threshold(n_trials):
    """Ngưỡng t kiểu Bonferroni: càng thử nhiều, càng phải mạnh mới được tin."""
    a = CFG["research"]["family_wise_alpha"] / max(1, n_trials)
    return max(CFG["research"]["min_t"], NormalDist().inv_cdf(1 - a / 2))

def walk_forward(ds, spec):
    r, h = CFG["research"], CFG["horizon_days"]
    f = spec["features"]
    d = ds[f + ["y", "yr"]]
    dates = d.index.get_level_values(0)
    valid = d[f].notna().all(axis=1).values
    labeled = d["y"].notna().values
    udates = pd.Index(sorted(dates[valid].unique()))
    emb = h + 1
    preds, fold_ics = [], []
    i = r["min_train_days"]
    while i < len(udates):
        test_dates = udates[i:i + r["test_days"]]
        cutoff = udates[i - emb]                      # nhãn tập train kết thúc trước ngày test đầu tiên
        trm = valid & labeled & (dates < cutoff)
        tem = valid & dates.isin(test_dates)
        if trm.sum() >= 1000 and tem.sum() > 0:
            m = fit(spec["model"], d.loc[trm, f].values, d.loc[trm, "yr"].values)
            out = pd.DataFrame({"pred": predict(m, d.loc[tem, f].values), "y": d.loc[tem, "y"].values},
                               index=d.index[tem])
            preds.append(out)
            ic = daily_ic(out)
            if len(ic):
                fold_ics.append(ic.mean())
        i += r["test_days"]
    oos = pd.concat(preds) if preds else pd.DataFrame(columns=["pred", "y"])
    return oos, fold_ics

def daily_ic(o):
    """Rank IC theo ngày (Spearman), tính vector hóa."""
    o = o.dropna(subset=["pred", "y"])
    if o.empty:
        return pd.Series(dtype=float)
    lv = o.index.get_level_values(0)
    rp = o["pred"].groupby(lv).rank(); ry = o["y"].groupby(lv).rank()
    dp = rp - rp.groupby(lv).transform("mean"); dy = ry - ry.groupby(lv).transform("mean")
    cov = (dp * dy).groupby(lv).sum()
    den = np.sqrt((dp ** 2).groupby(lv).sum() * (dy ** 2).groupby(lv).sum())
    return (cov / den).replace([np.inf, -np.inf], np.nan).dropna()

def tstat(ic, h):
    n = len(ic)
    if n < 2 or ic.std() == 0:
        return 0.0
    return float(ic.mean() / ic.std() * np.sqrt(n / h))    # hiệu chỉnh nhãn chồng lấn

def metrics(oos, fold_ics, regime):
    h, k = CFG["horizon_days"], CFG["research"]["top_k"]
    ic = daily_ic(oos)
    out = {"n_days": int(len(ic)), "ic_mean": float(ic.mean()) if len(ic) else 0.0, "ic_t": tstat(ic, h),
           "fold_pos": float(np.mean([x > 0 for x in fold_ics])) if fold_ics else 0.0, "n_folds": len(fold_ics)}
    o = oos.dropna(subset=["y"])
    prev, net = set(), []
    for d in ic.index[::h]:
        g = o.loc[d]
        top = set(g["pred"].nlargest(k).index)
        turnover = 1 - len(top & prev) / k if prev else 1.0
        net.append(g.loc[list(top), "y"].mean() - turnover * ROUNDTRIP)
        prev = top
    out["net_ann"] = float(np.mean(net) * 252 / h) if net else 0.0
    reg = {}
    lab = regime.reindex(ic.index)
    for rname, s in ic.groupby(lab):
        reg[rname] = {"n": int(len(s)), "ic_mean": float(s.mean()), "t": tstat(s, h)}
    out["regimes"] = reg
    recent = ic[ic.index >= ic.index.max() - pd.Timedelta(days=365)] if len(ic) else ic
    out["recent_ic"] = float(recent.mean()) if len(recent) else 0.0     # cổng gần đây: quy luật còn sống không?
    return out

def classify(m, thr):
    r = CFG["research"]
    if (m["ic_t"] >= thr and m["net_ann"] > 0 and m["fold_pos"] >= r["min_fold_positive"]
            and m.get("recent_ic", 0) > 0):
        good = [k for k, v in m["regimes"].items() if k != "UNKNOWN" and v["n"] >= 60 and v["ic_mean"] > 0]
        if len(good) <= 1:
            return "REGIME_SPECIFIC"
        return "STRONG" if m["ic_t"] >= thr + 1 else "SUPPORTED"
    if m["ic_t"] >= 2:
        return "WEAK"
    return "REJECTED"
