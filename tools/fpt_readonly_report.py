"""Read-only, reproducible FPT technical research from the existing GitHub price store.

Research-only / not investment advice. Do not fetch new prices, mutate raw/derived data,
write to Ledger or alter live trading settings. This script prints JSON to CI logs.
"""
from __future__ import annotations

import json
import numpy as np
import pandas as pd

from engine import data
from engine.config import CFG

LOOKBACKS = (20, 60, 120, 252)
TARGET = "FPT"

def finite(x, digits=6):
    try:
        f = float(x)
        return round(f, digits) if np.isfinite(f) else None
    except (TypeError, ValueError):
        return None

def main():
    store = data.load_store()
    mk = data.load_market()
    close = mk["close"].sort_index()
    raw = mk["raw_close"].sort_index()
    volume = mk["volume"].sort_index()
    dates = close.index
    assert len(dates) > 260, "historical price data insufficient"
    assert TARGET in close.columns, "FPT missing from universe"
    last = dates[-1]
    result = {
        "provenance": {
            "repository": "tranngocthang12-gif/TRUNG-T-M-T-I-CH-NH-Financial-Intelligence-Media-Factory",
            "base_main": "400de5775f6d832ff453ccc2d88c91eb35936d1a",
            "as_of": str(last.date()),
            "price_source_type": "first-observation Yahoo/raw, with engine-adjusted research series",
            "universe_basis": CFG.get("universe_basis"),
            "comparison_universe": list(CFG["universe"]),
            "read_only": True,
        },
        "fpt": {},
        "relative_strength": {},
        "quality": {},
        "limitations": [
            "Raw prices originate from Yahoo and are not exchange-authenticated.",
            "Engine adjusted history is not a fully point-in-time source vintage.",
            "Universe is the current VN30 list, not membership by historical period.",
            "No financial statements are in the original-source library; no valuation or fundamental claims.",
            "Does not recommend buying or selling; does not imply future returns.",
        ],
    }
    f = close[TARGET]
    fr = raw[TARGET]
    fv = volume[TARGET]
    fstore = store[store["ticker"] == TARGET].sort_values("date")
    most_recent = fstore.tail(1)
    result["fpt"]["last_observation"] = {
        "date": str(most_recent.iloc[0]["date"].date()) if len(most_recent) else None,
        "raw_close": finite(most_recent.iloc[0]["close"]) if len(most_recent) else None,
        "observed_at": str(most_recent.iloc[0]["observed_at"]) if len(most_recent) else None,
        "source": str(most_recent.iloc[0]["source"]) if len(most_recent) else None,
        "adjusted_close_at_market_end": finite(f.iloc[-1]),
        "rows": int(fstore.shape[0]),
    }
    result["fpt"]["moving_averages"] = {
        f"ma{n}": finite(f.rolling(n, min_periods=n).mean().iloc[-1]) for n in (20,60,120)
    }
    result["fpt"]["last_vs_averages_pct"] = {
        f"ma{n}": finite(100*(f.iloc[-1]/f.rolling(n, min_periods=n).mean().iloc[-1]-1))
        for n in (20,60,120)
    }
    result["fpt"]["ret_pct"] = {}
    result["relative_strength"]["comparison"] = "same last date, same N sessions, mean and median of tickers with valid adjusted prices (survivorship-biased current VN30)"
    for n in LOOKBACKS:
        if len(dates) < n+1:
            result["fpt"]["ret_pct"][str(n)] = None
            continue
        start = close.iloc[-(n+1)]
        end = close.iloc[-1]
        ret = (end / start - 1).replace([np.inf,-np.inf],np.nan).dropna()*100
        fpt_ret = finite(ret.get(TARGET))
        result["fpt"]["ret_pct"][str(n)] = fpt_ret
        if TARGET in ret.index:
            rank = int(ret.rank(method="min", ascending=False)[TARGET])
            eq = finite(ret.mean()); med = finite(ret.median())
            result["relative_strength"][str(n)] = {
                "fpt_rank":rank,"total":int(len(ret)),
                "equal_weight_mean_return_pct":eq,
                "median_ticker_return_pct":med,
                "fpt_minus_equal_weight_pp":finite(fpt_ret-eq),
                "fpt_minus_median_pp":finite(fpt_ret-med),
                "best_5": [{ "ticker":t,"ret_pct":finite(v)} for t,v in ret.nlargest(5).items()],
            }
    daily=(f/f.shift(1)-1).replace([np.inf,-np.inf],np.nan)
    result["fpt"]["volatility_annual_pct"] = {
        str(n): finite(daily.tail(n).std(ddof=1)*np.sqrt(252)*100) for n in (20,60,120)
    }
    d252=f.tail(253).dropna()
    result["fpt"]["max_drawdown_252_sessions_pct"] = finite(((d252 / d252.cummax())-1).min()*100) if len(d252)>2 else None
    result["fpt"]["max_drawdown_60_sessions_pct"] = finite(((f.tail(61).dropna()/f.tail(61).dropna().cummax())-1).min()*100)
    result["fpt"]["volume_ratio_20_to_60"] = finite(fv.tail(20).mean()/fv.tail(60).mean()) if fv.tail(60).mean()>0 else None
    result["fpt"]["raw_last_close"] = finite(fr.iloc[-1])
    result["quality"]["overall_engine"] = {k:mk["quality"].get(k) for k in ("as_of","checked","flagged_total","error_rate_window","skip")}
    bad=mk["bad"].get(TARGET)
    if bad is not None:
        result["quality"]["fpt_bad_flag_count"] = {str(n):int(bad.tail(n).sum()) for n in LOOKBACKS}
        result["quality"]["fpt_recent_bad_dates"] = [str(x.date()) for x in bad[bad].tail(15).index]
    ev=mk["events"]
    ev=ev[ev["ticker"]==TARGET] if "ticker" in ev.columns else ev.iloc[0:0]
    result["quality"]["fpt_events"] = {
        "total":int(len(ev)),
        "status_counts":{str(k):int(v) for k,v in ev["status"].value_counts().items()},
        "source_status_counts":{str(k):int(v) for k,v in ev["source_status"].value_counts().items()},
    }
    print("FPT_RESEARCH_JSON_START")
    print(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2))
    print("FPT_RESEARCH_JSON_END")

if __name__ == "__main__":
    main()
