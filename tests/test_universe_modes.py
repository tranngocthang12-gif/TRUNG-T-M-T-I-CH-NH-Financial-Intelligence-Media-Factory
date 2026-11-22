"""E2b (QĐ-1, QĐ-4 của ADR-0016): rổ theo ngày, mã bị loại vì thiếu lịch sử, tải giá thêm 5 mã.

- `data.ingest_tickers()`: `universe` rồi `data.ingest_extra`, không trùng; `ingest` và `fetch_yahoo_actions` lặp trên đó.
- `load_market(..., universe=None|"config"|"historical")`:
  - mặc định ("config" khi universe_basis CURRENT) không đổi một byte so với mã trước E2b, kể cả khi kho có thêm mã ngoài
    `universe` (mã `ingest_extra` hay mã bất kỳ);
  - "historical" theo data/vn30_history.csv: mỗi ngày chỉ giữ thành viên của ngày đó; trước ngày đầu không mã nào eligible;
    tệp thiếu hoặc hỏng thì lỗi, không tự chuyển sang "config";
  - mã bị loại vì không có hơn 250 dòng giá được liệt kê kèm số dòng; sự kiện quyền của mã không có trong bảng bị lọc
    trước adjust.build_events.
Fixture ghi vào thư mục tạm (config.ROOT và adjust.ROOT được vá); test trên kho thật chỉ đọc.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import pickle
import sys
import types
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from engine import adjust, config, data  # noqa: E402

IDX = pd.bdate_range("2023-01-02", periods=420)
U = list(config.CFG["universe"][:4])                     # mã thật của universe (giữ nguyên biên độ HOSE mặc định)
EXTRA = list(config.CFG["data"]["ingest_extra"])
OLD_KEYS = ("close", "volume", "raw_close", "bad", "events", "quality", "flags")
OBS = "2026-09-26"
NONE = pd.DataFrame(columns=adjust.EV_COLS)


def _walk(cols, seed=7):
    rng = np.random.default_rng(seed)
    r = rng.normal(0.0, 0.012, size=(len(IDX), len(cols))).clip(-0.05, 0.05)
    return pd.DataFrame(20000.0 * np.cumprod(1 + r, axis=0), index=IDX, columns=list(cols))


def _rows(close):
    out = []
    for d in close.index:
        for t in close.columns:
            p = close.at[d, t]
            if pd.notna(p):
                out.append({"date": d.strftime("%Y-%m-%d"), "ticker": t, "open": p, "high": p, "low": p, "close": p,
                            "volume": 1e6, "observed_at": OBS, "source": "fixture"})
    return pd.DataFrame(out, columns=data.COLS)


def _cash(ticker, at, amount=500.0):
    return pd.DataFrame([{"ticker": ticker, "ex_date": at, "type": adjust.CASH, "ratio": np.nan, "cash_per_share": amount,
                          "source": "yahoo", "source_status": "TU_DONG", "note": ""}], columns=adjust.EV_COLS)


def _home(tmp, close, manual=None, yahoo=None, history=None):
    tmp = pathlib.Path(tmp)
    assert data.save_store(_rows(close), root=tmp) > 0
    for key, df in (("manual", NONE if manual is None else manual), ("yahoo_cache", NONE if yahoo is None else yahoo)):
        p = tmp / config.CFG["corporate_actions"][key]
        p.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(p, index=False)
    if history is not None:
        (tmp / "data").mkdir(parents=True, exist_ok=True)
        (tmp / data.VN30_HISTORY).write_text(history, encoding="utf-8")
    return tmp


def _history(rows):
    return "effective_date,ticker,action,source_id\n" + "".join(f"{d},{t},{a},fx\n" for d, t, a in rows)


def _market(home, as_of=None, cfg=None, **kw):
    with patch.object(config, "ROOT", home), patch.object(adjust, "ROOT", home), patch.dict(config.CFG, cfg or {}):
        return data.load_market(as_of, **kw)


def _h(x):
    if isinstance(x, pd.DataFrame):
        return hashlib.sha256(pickle.dumps((x.to_csv(), [str(t) for t in x.dtypes], str(x.index.dtype)))).hexdigest()
    return hashlib.sha256(json.dumps(x, sort_keys=True, default=str, ensure_ascii=False).encode()).hexdigest()


def _main_reference(as_of=None):
    """Thân load_market chế độ mặc định trên main trước E2b (e6778d1), chép nguyên văn phần dựng bảng: mốc 'không đổi một
    byte'. Mã trước E2b không lọc theo universe và không lọc sự kiện theo mã."""
    s = data.load_store()
    if as_of is not None:
        s = s[s.date <= pd.Timestamp(as_of)]
    raw = s.pivot(index="date", columns="ticker", values="close").sort_index()
    vol = s.pivot(index="date", columns="ticker", values="volume").sort_index()
    obs = s.pivot(index="date", columns="ticker", values="observed_at").sort_index()
    keep = raw.columns[raw.notna().sum() > 250]
    raw, vol, obs = raw[keep], vol[keep], obs[keep]
    events = adjust.build_events(raw, obs, adjust.load_manual(), adjust.load_yahoo())
    F, S = adjust.factors(raw.index, raw.columns, events)
    adj = raw * F
    bad, rep, flags = adjust.quality(adj)
    rep["events"] = events.status.value_counts().to_dict() if len(events) else {}
    rep["events_not_applied"] = [f"{e.ticker} {e.ex_date.date()} {e.type} ({e.source}): {e.status}"
                                 for e in events.itertuples() if e.status not in ("APPLIED", "CHUA_DEN_HAN",
                                                                                  "DA_NAM_TRONG_GIA_NGUON")]
    rep["events_applied"] = [f"{e.ticker} {e.trade_date.date()} {e.type} ({e.source}, {e.source_status}): "
                             f"gốc {e.raw_return:+.2%} → điều chỉnh {e.adj_return:+.2%}"
                             for e in events.itertuples() if e.status == "APPLIED"]
    return {"close": adj.ffill(limit=5), "volume": (vol / S).fillna(0), "raw_close": raw, "bad": bad,
            "events": events, "quality": rep, "flags": flags}


def _ref(home, as_of=None):
    with patch.object(config, "ROOT", home), patch.object(adjust, "ROOT", home):
        return _main_reference(as_of)


def _same(a, b):
    return {k: _h(a[k]) for k in OLD_KEYS} == {k: _h(b[k]) for k in OLD_KEYS}


# ---------- 1. tải giá: universe + ingest_extra ----------

def test_ingest_tickers_are_universe_then_extras_without_duplicates():
    assert config.CFG["data"]["ingest_extra"] == ["BSR", "LPB", "MCH", "TCX", "VPL"]
    assert data.ingest_tickers() == list(config.CFG["universe"]) + ["BSR", "LPB", "MCH", "TCX", "VPL"]
    with patch.dict(config.CFG["data"], {"ingest_extra": ["BSR", U[0], "BSR", "LPB"]}):
        assert data.ingest_tickers() == list(config.CFG["universe"]) + ["BSR", "LPB"]
    with patch.dict(config.CFG["data"], {"ingest_extra": None}):
        assert data.ingest_tickers() == list(config.CFG["universe"])


def test_ingest_and_yahoo_actions_loop_over_universe_and_extras(tmp_path):
    asked, acted = [], []

    def fake_fetch(t, start, end):
        asked.append(t)
        return pd.DataFrame({"Date": pd.to_datetime(["2026-11-19", "2026-11-20"]), "Open": 1.0, "High": 1.0, "Low": 1.0,
                             "Close": 1.0, "Volume": 10.0}).set_index("Date")

    class FakeTicker:
        def __init__(self, sym):
            acted.append(sym)
            self.actions = pd.DataFrame()

    yf = types.SimpleNamespace(Ticker=FakeTicker)
    with patch.object(config, "ROOT", tmp_path), patch.dict(data.FETCHERS, {"yahoo": fake_fetch}), \
            patch.dict(config.CFG["data"], {"sources": ["yahoo"]}), patch.dict(sys.modules, {"yfinance": yf}):
        log = data.ingest(end=pd.Timestamp("2026-11-20").date())
    want = data.ingest_tickers()
    assert asked == want and acted == [f"{t}.VN" for t in want]
    assert set(log["last_date_by_ticker"]) == set(want) and log["errors"] == []


# ---------- 2. chế độ mặc định ("config") không đổi một byte ----------

def test_default_mode_ignores_extra_tickers_in_the_store_byte_for_byte(tmp_path):
    base = _walk(U)
    clean = _home(tmp_path / "clean", base, yahoo=_cash(U[0], IDX[200]))
    more = base.join(_walk(["BSR", "ZZZ"], seed=11))                       # mã ingest_extra và một mã bất kỳ ngoài universe
    dirty = _home(tmp_path / "dirty", more, yahoo=pd.concat([_cash(U[0], IDX[200]), _cash("BSR", IDX[210]),
                                                             _cash("ZZZ", IDX[220])], ignore_index=True))
    a, b = _market(clean), _market(dirty)
    assert _same(a, b) and _same(a, _ref(clean))                           # = mã trước E2b trên kho không có mã thêm
    assert list(b["close"].columns) == U and "BSR" not in b["events"]["ticker"].tolist()
    assert (a["research_input"], a["pit_label"], a["pit_gaps"]) == (b["research_input"], b["pit_label"], b["pit_gaps"])
    assert set(b) == set(OLD_KEYS) | {"research_input", "derivation_id", "pit_label", "pit_gaps"}
    assert "dropped_short_history" not in b["quality"] and "universe_mode" not in b["quality"]
    for as_of in (str(IDX[300].date()), str(IDX[-1].date())):
        assert _same(_market(dirty, as_of), _ref(clean, as_of))
    # chế độ "config" chọn tường minh = mặc định khi universe_basis là CURRENT
    assert _same(_market(dirty, universe="config"), b)


def test_store_without_any_universe_ticker_keeps_its_tickers_but_not_ingest_extra(tmp_path):
    home = _home(tmp_path, _walk(["AAA", "BBB", "BSR"]))
    mk = _market(home)
    assert list(mk["close"].columns) == ["AAA", "BBB"]
    assert any("kho không có mã nào của universe" in g for g in mk["pit_gaps"])
    assert not any("kho không có mã nào" in g for g in _market(_home(tmp_path / "u", _walk(U)))["pit_gaps"])


def test_real_store_default_is_byte_identical_to_main_reference():
    assert _same(data.load_market(), _main_reference())


# ---------- 3. mã bị loại vì thiếu lịch sử, sự kiện của mã vắng ----------

def test_short_history_ticker_is_reported_with_row_count(tmp_path):
    c = _walk(U)
    c.iloc[:-200, 3] = np.nan                                              # U[3] mới niêm yết: 200 dòng
    mk = _market(_home(tmp_path, c))
    assert mk["quality"]["dropped_short_history"] == {U[3]: 200} and U[3] not in mk["close"].columns
    c.iloc[-250:, 3] = 1.0 * c.iloc[-250:, 0]                              # đúng 250 dòng: chưa HƠN 250, vẫn bị loại
    mk = _market(_home(tmp_path / "b", c))
    assert mk["quality"]["dropped_short_history"] == {U[3]: 250} and U[3] not in mk["close"].columns
    c.iloc[-251:, 3] = 1.0 * c.iloc[-251:, 0]                              # 251 dòng: hơn 250 thì giữ
    mk = _market(_home(tmp_path / "c", c))
    assert U[3] in mk["close"].columns and "dropped_short_history" not in mk["quality"]


def test_events_of_tickers_absent_from_the_table_are_dropped_before_build_events(tmp_path):
    c = _walk(U)
    c.iloc[:-100, 3] = np.nan                                              # U[3] bị loại vì thiếu lịch sử
    ev = pd.concat([_cash(U[0], IDX[200]), _cash(U[3], IDX[-50]), _cash("BSR", IDX[210])], ignore_index=True)
    home = _home(tmp_path, c.join(_walk(["BSR"], seed=3)), manual=_cash("MCH", IDX[150]), yahoo=ev)
    seen = []
    real = adjust.build_events

    def spy(close, observed, manual, yahoo):
        seen.append((set(close.columns), set(manual["ticker"]) | set(yahoo["ticker"])))
        return real(close, observed, manual, yahoo)

    with patch.object(adjust, "build_events", spy):
        mk = _market(home)
    cols, tick = seen[0]
    assert tick == {U[0]} and tick <= cols
    assert set(mk["events"]["ticker"]) == {U[0]}
    assert not any("KHONG_CO_MA" in x for x in mk["quality"]["events_not_applied"])


# ---------- 4. chế độ "historical" ----------

HIST = [(IDX[100].date(), U[0], "ADD"), (IDX[100].date(), U[1], "ADD"), (IDX[100].date(), U[2], "ADD"),
        (IDX[100].date(), "MCH", "ADD"), (IDX[250].date(), "BSR", "ADD"), (IDX[300].date(), U[2], "REMOVE")]


def _hist_home(tmp_path, rows=HIST):
    close = _walk(U).join(_walk(["BSR", "ZZZ"], seed=5))                  # MCH là thành viên nhưng không có giá
    return _home(tmp_path, close, history=_history(rows))


def test_historical_keeps_only_the_members_of_each_day(tmp_path):
    mk = _market(_hist_home(tmp_path), universe="historical")
    c, v, el, m = mk["close"], mk["volume"], mk["eligible"], mk["members"]
    assert list(c.columns) == sorted([U[0], U[1], U[2], "BSR"])          # U[3], ZZZ không có trong tệp lịch sử
    assert c.loc[IDX[299], U[2]] > 0 and c.loc[IDX[300]:, U[2]].isna().all()    # REMOVE có hiệu lực từ ngày ghi
    assert c.loc[:IDX[249], "BSR"].isna().all() and c.loc[IDX[250]:, "BSR"].notna().all()  # ADD tính cả ngày ghi
    assert v.loc[IDX[300]:, U[2]].isna().all() and v.loc[:IDX[249], "BSR"].isna().all()
    assert mk["raw_close"].loc[IDX[300]:, U[2]].isna().all()
    assert not el.loc[IDX[300]:, U[2]].any() and el.loc[IDX[100]:IDX[299], U[2]].all()
    assert el.loc[IDX[250]:, "BSR"].all() and not el.loc[:IDX[249], "BSR"].any()
    assert (el == (m & mk["raw_close"].notna())).all().all()
    q = mk["quality"]
    assert q["universe_mode"] == "historical"
    assert q["members_without_prices"] == {"MCH": "không có dòng giá trong kho"}
    assert q["members_last_session"] == {"date": str(IDX[-1].date()), "members": 4, "with_prices": 3, "eligible": 3}
    assert any(data.VN30_HISTORY in g and str(IDX[100].date()) in g for g in mk["pit_gaps"])
    assert not any("rổ theo cấu hình" in g for g in mk["pit_gaps"])


def test_historical_before_the_first_effective_date_nothing_is_eligible(tmp_path):
    mk = _market(_hist_home(tmp_path), universe="historical")
    assert mk["quality"]["universe_unknown_before"] == str(IDX[100].date())
    assert not mk["eligible"].loc[:IDX[99]].any().any() and mk["close"].loc[:IDX[99]].isna().all().all()
    assert mk["eligible"].loc[IDX[100], [U[0], U[1], U[2]]].all()
    early = _market(_hist_home(tmp_path / "e"), as_of=str(IDX[80].date()), universe="historical")
    assert not early["eligible"].any().any() and early["quality"]["members_without_prices"] == {}


def test_historical_short_history_member_is_listed(tmp_path):
    close = _walk(U).join(_walk(["BSR"], seed=5))
    close.iloc[:-120, close.columns.get_loc("BSR")] = np.nan
    mk = _market(_home(tmp_path, close, history=_history(HIST)), universe="historical")
    assert mk["quality"]["dropped_short_history"] == {"BSR": 120}
    assert mk["quality"]["members_without_prices"] == {"BSR": "bị loại vì thiếu lịch sử (120 dòng)",
                                                        "MCH": "không có dòng giá trong kho"}


def test_universe_basis_historical_is_the_default_historical_mode(tmp_path):
    home = _hist_home(tmp_path)
    a = _market(home, cfg={"universe_basis": "HISTORICAL"})
    b = _market(home, universe="historical")
    assert a["quality"]["universe_mode"] == "historical" and _same(a, b)
    assert "universe_mode" not in _market(home, cfg={"universe_basis": "HISTORICAL"}, universe="config")["quality"]


@pytest.mark.parametrize("text", [
    "",                                                                    # rỗng
    "effective_date,ticker\n2023-05-24,ACB\n",                             # thiếu cột action
    "effective_date,ticker,action,source_id\n24/05/2023,ACB,ADD,fx\n",     # ngày không ISO
    "effective_date,ticker,action,source_id\n2023-05-24,ACB,KEEP,fx\n",    # action lạ
    "effective_date,ticker,action,source_id\n2023-05-24,ACB,REMOVE,fx\n",  # REMOVE mã không có mặt
    "effective_date,ticker,action,source_id\n2023-05-24,ACB,ADD,fx\n2023-06-01,ACB,ADD,fx\n",  # ADD mã đang có mặt
    "effective_date,ticker,action,source_id\n2023-05-24,ACB,ADD,fx\n2023-05-24,ACB,ADD,fx\n",  # trùng dòng cùng ngày
    "effective_date,ticker,action,source_id\n2023-05-24,,ADD,fx\n",        # ô trống
])
def test_historical_broken_file_raises_and_does_not_fall_back(tmp_path, text):
    home = _home(tmp_path, _walk(U), history=text)
    with pytest.raises(ValueError):
        _market(home, universe="historical")
    _market(home)                                                          # chế độ mặc định không đọc tệp này


def test_historical_missing_file_raises(tmp_path):
    home = _home(tmp_path, _walk(U))
    with pytest.raises(FileNotFoundError):
        _market(home, universe="historical")
    with pytest.raises(FileNotFoundError):
        _market(home, cfg={"universe_basis": "HISTORICAL"})


def test_bad_universe_arguments_raise(tmp_path):
    home = _home(tmp_path, _walk(U))
    with pytest.raises(ValueError):
        _market(home, universe="vn30")
    with pytest.raises(ValueError):
        _market(home, cfg={"universe_basis": "SOMETIMES"})


def test_derivation_id_binds_the_history_file_only_in_historical_mode(tmp_path):
    home = _hist_home(tmp_path)
    h1, c1 = _market(home, universe="historical")["derivation_id"], _market(home)["derivation_id"]
    (home / data.VN30_HISTORY).write_text(_history(HIST + [(IDX[350].date(), U[1], "REMOVE")]), encoding="utf-8")
    h2, c2 = _market(home, universe="historical")["derivation_id"], _market(home)["derivation_id"]
    assert h1 != h2 and c1 == c2 and h1 != c1


def test_historical_with_verified_input_keeps_both_masks(tmp_path):
    mk = _market(_hist_home(tmp_path), universe="historical", research_input="verified")
    assert (mk["eligible"] == (mk["members"] & mk["raw_close"].notna() & ~mk["exclude"])).all().all()


# ---------- 5. kho thật, chỉ đọc ----------

def test_real_store_historical_mode_runs_and_reports_members():
    mk = data.load_market(universe="historical")
    q, d = mk["quality"], mk["close"].index[-1]
    last = data.membership(mk["close"].index[-1:], data.load_vn30_history()).iloc[0]
    members = set(last[last].index)
    priced = {t for t in members if t in mk["raw_close"].columns and pd.notna(mk["raw_close"].at[d, t])}
    assert len(members) == 30
    assert q["members_last_session"] == {"date": str(d.date()), "members": 30, "with_prices": len(priced),
                                         "eligible": int(mk["eligible"].loc[d].sum())}
    assert set(q["members_without_prices"]) >= members - set(mk["raw_close"].columns)
    assert q["universe_unknown_before"] == "2025-08-04" and not mk["eligible"].loc[:"2025-08-01"].any().any()
