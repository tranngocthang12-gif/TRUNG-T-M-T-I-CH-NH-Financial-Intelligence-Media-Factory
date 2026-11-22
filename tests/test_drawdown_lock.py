"""R1b (QĐ-5, QĐ-5a của ADR-0016; O-R của Owner): ngắt khi sụt giảm NAV 15% cho sổ giấy chính.

- engine.risk_gate: drawdown_path (hàm thuần), drawdown_problem, release_check (gỡ khóa chỉ khi Owner gộp PR đổi
  paper.risk_lock_release đúng bằng risk_lock.since), git_last_release_commit.
- engine.paper: đo NAV từng phiên (giá gốc của kho, sự kiện quyền theo phiên) giữa hai lần chạy, khóa, thanh lý, không đo được.
Fixture: kho giá và sổ giấy trong thư mục tạm (config.ROOT, paper.ROOT được vá). Không lịch phiên: trục phiên = ngày kho giá.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from engine import adjust, config, data, paper, risk_gate as rg  # noqa: E402

IDX = pd.bdate_range("2026-03-02", periods=30)
D = [str(x.date()) for x in IDX]
NONE_PREDS = pd.DataFrame(columns=["date", "model_id", "ticker", "score"])
CASH0, SH0 = 100_000_000.0, 90_000            # NAV ban đầu = 100 triệu + 90.000 × 10.000 = 1 tỷ = paper.initial_cash


def _prices(drop_at=None, drop_to=8_000.0, recover=9_800.0, tickers=("A", "B")):
    px = pd.DataFrame({t: 10_000.0 + 0 * np.arange(len(IDX)) for t in tickers}, index=IDX)
    if drop_at is not None:
        px.loc[IDX[drop_at], "A"] = drop_to
        px.loc[IDX[drop_at + 1]:, "A"] = recover
    return px


def _home(tmp, raw, skip=(), vol=None):
    vol = vol or {}
    rows = [{"date": d.strftime("%Y-%m-%d"), "ticker": t, "open": raw.at[d, t], "high": raw.at[d, t], "low": raw.at[d, t],
             "close": raw.at[d, t], "volume": vol.get(t, 10_000_000.0), "observed_at": "2026-03-01", "source": "fixture"}
            for d in raw.index for t in raw.columns if (str(d.date()), t) not in skip and pd.notna(raw.at[d, t])]
    data.save_store(pd.DataFrame(rows, columns=data.COLS), root=tmp)
    return tmp


def _state(home, last, positions=None, cash=CASH0, pending=None, **extra):
    positions = {"A": SH0} if positions is None else positions
    st = {"cash": cash, "positions": positions, "pending": pending, "last_rebalance": last, "costs_paid": 0.0,
          "n_rebalance": 0, "last_date": last,
          "dd": {"peak": 1_000_000_000.0, "peak_date": last, "checked_through": last,
                 "runs": [{"date": last, "positions": dict(positions), "cash": cash}]}, **extra}
    (home / "paper").mkdir(parents=True, exist_ok=True)
    (home / "paper" / "state.json").write_text(json.dumps(st), encoding="utf-8")


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "ROOT", tmp_path)
    monkeypatch.setattr(paper, "ROOT", tmp_path)
    monkeypatch.setitem(config.CFG["paper"], "risk_lock_release", None)
    return tmp_path


def _run(home, i, close, events=None, frozen=False, reg=None, preds=None):
    nav, decision = paper.run(D[i], close, NONE_PREDS if preds is None else preds, reg or {}, IDX, events=events,
                              frozen=frozen)
    return decision, _st(home)


def _st(home):
    return json.loads((home / "paper" / "state.json").read_text(encoding="utf-8"))


def _csv(home, name):
    p = home / "paper" / name
    return pd.read_csv(p, dtype=str) if p.exists() else pd.DataFrame()


# ---------- 1. hàm thuần ----------

def test_drawdown_path_measures_each_session_and_stops_at_a_gap():
    r = rg.drawdown_path([("s1", 1000.0), ("s2", 1100.0), ("s3", 930.0), ("s4", None), ("s5", 500.0)], 1000.0, 0.15)
    assert [x["date"] for x in r["rows"]] == ["s1", "s2", "s3"] and r["stopped_at"] == "s4"
    assert r["peak"] == 1100.0 and r["peak_date"] == "s2"
    assert r["breach"]["date"] == "s3" and abs(r["breach"]["drawdown"] - (1 - 930 / 1100)) < 1e-12
    assert rg.drawdown_path([("s1", 860.0)], 1000.0, 0.15)["breach"] is None            # 14% < 15%
    assert rg.drawdown_path([("s1", 850.0)], 1000.0, 0.15)["breach"]["date"] == "s1"    # đúng 15%: chạm ngưỡng
    with pytest.raises(ValueError):
        rg.drawdown_path([("s1", 1.0)], 0.0, 0.15)


@pytest.mark.parametrize("bad", [None, {}, {"max_drawdown": "TODO"}, {"max_drawdown": 0}, {"max_drawdown": 1.0},
                                 {"max_drawdown": True}, {"max_drawdown": float("nan")}])
def test_drawdown_problem_rejects_missing_or_broken_thresholds(bad):
    assert rg.drawdown_problem(bad)
    assert rg.drawdown_problem({"max_drawdown": 0.15}) is None
    assert config.CFG["paper"]["risk_limits"]["max_drawdown"] == 0.15
    assert "max_drawdown" not in rg.LIMIT_KEYS                                          # R1a giữ nguyên


# ---------- 2. khóa ở phiên chạm ngưỡng giữa hai lần chạy ----------

def test_breach_between_two_runs_locks_at_that_session(env):
    raw = _prices(drop_at=23)                                   # A: 10.000 → 8.000 ở IDX[23] (NAV 820 triệu, −18%), hồi 9.800
    home = _home(env, raw)
    _state(home, D[20])
    dec, st = _run(home, 25, raw)                               # lần chạy kế: IDX[25], đo IDX[21..25]
    lock = st["risk_lock"]
    assert lock["since"] == D[23] and lock["detected_on"] == D[25] and lock["liquidation"] == "PENDING"
    assert abs(lock["drawdown"] - 0.18) < 1e-6 and lock["nav"] == 820_000_000 and lock["peak"] == 1_000_000_000
    assert dec["action"] == "RISK_CASH_WAIT_OWNER" and dec["targets"] == "" and "thanh lý PENDING" in dec["models"]
    assert st["pending"] == [] and st["dd"]["checked_through"] == D[25]
    dd = _csv(home, "drawdown.csv")
    assert dd.date.tolist() == D[21:26] and dd.verified.unique().tolist() == ["True"]
    # NAV đã hồi (IDX[25]: 982 triệu, −1,8%) nhưng khóa vẫn còn
    dec, st = _run(home, 26, raw)
    assert "risk_lock" in st and st["positions"] == {} and st["risk_lock"]["liquidation"] == "DONE"
    assert st["risk_lock"]["liquidated_on"] == D[26]
    trd = _csv(home, "trades.csv")
    assert trd[(trd.date == D[26]) & (trd.side == "SELL")].asset.tolist() == ["A"]


def test_lock_blocks_buys_and_skips_models_while_it_holds(env):
    raw = _prices(drop_at=23)
    home = _home(env, raw)
    _state(home, D[20], pending=["A", "B"])                     # lệnh chờ: giữ A, mua B
    dec, st = _run(home, 25, raw)
    trd = _csv(home, "trades.csv")
    assert trd[trd.side == "UNFILLED_RISK_LOCK"].asset.tolist() == ["B"] and "B" not in st["positions"]
    reg = {"M": {"state": "ACTIVE", "backtest": {"ic_t": 3.0}}}
    preds = pd.DataFrame([(IDX[29], "M", t, float(k)) for k, t in enumerate("AB")], columns=["date", "model_id", "ticker",
                                                                                            "score"])
    for i in (26, 27, 28, 29):
        dec, st = _run(home, i, raw, reg=reg, preds=preds)
    decs = _csv(home, "decisions.csv")
    assert set(decs.action) == {"RISK_CASH_WAIT_OWNER"} and "REBALANCE" not in decs.action.tolist()
    assert "risk_lock" in st and st["positions"] == {}


# ---------- 3. sự kiện quyền giữa hai lần chạy ----------

def _events(rows):
    ev = pd.DataFrame(rows)
    for c in ("ex_date", "trade_date"):
        ev[c] = pd.to_datetime(ev[c])
    return ev


def test_split_between_runs_is_not_a_drawdown_and_cash_dividend_counts_from_its_session(env):
    raw = _prices()
    raw.loc[IDX[23]:, "A"] = 5_000.0                            # chia tách 2:1 ở IDX[23]: giá gốc giảm một nửa
    raw.loc[IDX[22], "B"] = 10_000.0
    home = _home(env, raw)
    _state(home, D[20], positions={"A": SH0, "B": 1_000})
    ev = _events([{"ticker": "A", "ex_date": D[23], "trade_date": D[23], "type": "stock_split", "ratio": 2.0,
                   "cash_per_share": np.nan, "status": "APPLIED"},
                  {"ticker": "B", "ex_date": D[22], "trade_date": D[22], "type": "cash_dividend", "ratio": np.nan,
                   "cash_per_share": 1_000.0, "status": "APPLIED"}])
    adj = raw.copy()
    adj.loc[:IDX[22], "A"] /= 2                                  # giá điều chỉnh neo tại as_of (như load_market)
    dec, st = _run(home, 25, adj, events=ev)
    assert "risk_lock" not in st and dec is None
    dd = _csv(home, "drawdown.csv").set_index("date")
    tax = config.CFG["costs"].get("dividend_tax", 0.0)
    assert float(dd.at[D[21], "nav"]) == round(CASH0 + SH0 * 10_000 + 1_000 * 10_000)
    assert float(dd.at[D[22], "nav"]) == round(CASH0 + 1_000 * 1_000 * (1 - tax) + SH0 * 10_000 + 1_000 * 10_000)
    assert float(dd.at[D[23], "nav"]) == float(dd.at[D[22], "nav"])                  # 2 × 90.000 × 5.000 = 90.000 × 10.000
    assert st["positions"]["A"] == 2 * SH0


# ---------- 4. không đo được ----------

def test_missing_raw_price_is_unverified_blocks_buys_then_resumes_and_locks(env, monkeypatch):
    """Thiếu giá gốc của A ở IDX[2], ngoài cửa sổ ADV 20 phiên của cổng R1a ở các phiên khớp, nên cổng R1a đạt và chỉ R1b chặn."""
    monkeypatch.setitem(config.CFG["paper"]["risk_limits"], "max_weight", 0.9)
    raw = _prices(drop_at=24)                                   # sụt 18% ở IDX[24]
    home = _home(env, raw, skip={(D[2], "A")})
    _state(home, D[1], pending=["A", "B"])
    close = raw.copy()                                           # bảng close có giá cho mọi phiên (như sau ffill)
    dec, st = _run(home, 25, close)
    assert dec["action"] == "DRAWDOWN_UNVERIFIED" and D[2] in dec["models"] and "thiếu giá gốc" in dec["models"]
    assert st["dd"]["checked_through"] == D[1] and "risk_lock" not in st
    trd = _csv(home, "trades.csv")
    assert trd[trd.side == "UNFILLED_RISK_UNVERIFIED"].asset.tolist() == ["B"] and "B" not in st["positions"]
    assert "UNFILLED_RISK_GATE" not in trd.side.tolist() and st["positions"] == {"A": SH0}       # không ép bán
    dec, st = _run(home, 26, close)                              # vẫn thiếu IDX[2]: lần chạy này cũng ghi
    decs = _csv(home, "decisions.csv")
    assert decs.action.tolist().count("DRAWDOWN_UNVERIFIED") == 2 and st["dd"]["checked_through"] == D[1]
    assert not (home / "paper" / "drawdown.csv").exists()
    # bổ sung giá gốc IDX[2] (kho chỉ ghi thêm): lần chạy sau đo tiếp từ IDX[2] và khóa ở IDX[24]
    data.save_store(pd.DataFrame([{"date": D[2], "ticker": "A", "open": 10_000.0, "high": 10_000.0, "low": 10_000.0,
                                   "close": 10_000.0, "volume": 1e7, "observed_at": "2026-04-20", "source": "fixture"}],
                                 columns=data.COLS), root=home)
    dec, st = _run(home, 27, close)
    assert st["risk_lock"]["since"] == D[24] and st["dd"]["checked_through"] == D[27]
    assert _csv(home, "drawdown.csv").date.tolist() == D[2:28]


def test_sessions_before_a_trade_made_while_unverified_are_valued_with_the_old_holdings(env):
    """Đo kẹt ở IDX[2]; lần chạy IDX[25] vẫn khớp lệnh bán A đang chờ (không ép bán, nhưng lệnh cũ vẫn khớp). Khi có giá
    IDX[2], các phiên IDX[2..25] phải định giá theo vị thế trước lần bán (còn A), phiên IDX[26] theo trạng thái sau lần bán."""
    raw = _prices()
    home = _home(env, raw, skip={(D[2], "A")})
    _state(home, D[1], pending=[])                               # lệnh chờ: bán hết A
    dec, st = _run(home, 25, raw)
    assert dec["action"] == "DRAWDOWN_UNVERIFIED" and st["positions"] == {} and st["dd"]["checked_through"] == D[1]
    cash_after = st["cash"]
    assert [r["date"] for r in st["dd"]["runs"]] == [D[1], D[25]]
    data.save_store(pd.DataFrame([{"date": D[2], "ticker": "A", "open": 10_000.0, "high": 10_000.0, "low": 10_000.0,
                                   "close": 10_000.0, "volume": 1e7, "observed_at": "2026-04-20", "source": "fixture"}],
                                 columns=data.COLS), root=home)
    dec, st = _run(home, 26, raw)
    dd = _csv(home, "drawdown.csv").set_index("date")
    assert dd.index.tolist() == D[2:27]
    assert {float(dd.at[x, "nav"]) for x in D[2:26]} == {CASH0 + SH0 * 10_000}
    assert float(dd.at[D[26], "nav"]) == round(cash_after)
    assert [r["date"] for r in st["dd"]["runs"]] == [D[26]]


@pytest.mark.parametrize("bad", [None, "TODO", 2.0])
def test_missing_or_broken_threshold_is_unverified(env, monkeypatch, bad):
    lim = dict(config.CFG["paper"]["risk_limits"])
    lim.pop("max_drawdown")
    if bad is not None:
        lim["max_drawdown"] = bad
    monkeypatch.setitem(config.CFG["paper"], "risk_limits", lim)
    raw = _prices()
    home = _home(env, raw)
    _state(home, D[20])
    dec, st = _run(home, 21, raw)
    assert dec["action"] == "DRAWDOWN_UNVERIFIED" and "max_drawdown" in dec["models"]
    assert st["dd"]["checked_through"] == D[20] and not (home / "paper" / "drawdown.csv").exists()


def test_broken_calendar_is_unverified(env):
    raw = _prices()
    home = _home(env, raw)
    _state(home, D[20])
    (home / "data").mkdir(exist_ok=True)
    (home / "data" / "trading_calendar.csv").write_text("date,is_session\n2026-03-02,2\n", encoding="utf-8")
    dec, st = _run(home, 21, raw)
    assert dec["action"] == "DRAWDOWN_UNVERIFIED" and "lịch" in dec["models"]


# ---------- 5. thanh lý khi khóa sàn ----------

def test_floor_locked_sell_stays_pending_and_is_not_reported_as_sold(env):
    raw = _prices(drop_at=23)
    raw.loc[IDX[26], "A"] = 9_800.0 * 0.93                       # IDX[26]: A giảm sàn −7% → không bán được
    raw.loc[IDX[27]:, "A"] = 9_000.0
    home = _home(env, raw)
    _state(home, D[20])
    _run(home, 25, raw)
    dec, st = _run(home, 26, raw)
    assert st["positions"] == {"A": SH0} and st["pending"] == [] and st["risk_lock"]["liquidation"] == "PENDING"
    assert "UNFILLED_LIMIT_DOWN" in _csv(home, "trades.csv").side.tolist()
    dec, st = _run(home, 27, raw)
    assert st["positions"] == {} and st["risk_lock"]["liquidation"] == "DONE" and st["risk_lock"]["liquidated_on"] == D[27]
    for i in range(28, 30):
        dec, st = _run(home, i, raw)
    lines = _csv(home, "decisions.csv")
    first = lines[lines.date == D[25]].models.item()
    assert "thanh lý PENDING, còn 1 mã (A)" in first and "DONE" not in first


# ---------- 5b. thanh lý theo giới hạn thanh khoản, giá gốc, chạy lại (bản chấm L-09 PR #91 vòng 1) ----------

def _cap(raw, vol, i, ticker="A"):
    """Số cổ phiếu được bán ở phiên IDX[i]: max_participation × giá trị giao dịch bình quân adv_sessions phiên / giá gốc,
    làm tròn xuống lô (tính độc lập với mã: từ bảng giá fixture)."""
    lim, lot = config.CFG["paper"]["risk_limits"], config.CFG["lot_size"]
    n = int(lim["adv_sessions"])
    p = raw[ticker].iloc[i - n + 1:i + 1].to_numpy(dtype=float)
    adv = float((p * vol).mean())
    return int(float(lim["max_participation"]) * adv / float(raw[ticker].iloc[i])) // lot * lot


def test_rerun_of_the_lock_session_does_not_sell_early(env):
    raw = _prices(drop_at=23)
    home = _home(env, raw)
    _state(home, D[20])
    _, st1 = _run(home, 25, raw)                                 # phát hiện, đặt lệnh thanh lý cho phiên sau
    assert st1["pending"] == [] and st1["pending_set_on"] == D[25]
    trd1 = _csv(home, "trades.csv")
    _, st2 = _run(home, 25, raw)                                 # chạy lại cùng phiên: không khớp, không ghi giao dịch
    assert _csv(home, "trades.csv").equals(trd1) and "SELL" not in trd1.get("side", pd.Series(dtype=str)).tolist()
    for k in ("positions", "cash", "pending", "pending_set_on", "risk_lock"):
        assert st2[k] == st1[k], k
    _, st3 = _run(home, 26, raw)                                 # phiên sau mới bán
    trd = _csv(home, "trades.csv")
    assert trd[trd.side == "SELL"].date.tolist() == [D[26]] and st3["positions"] == {}
    assert st3["risk_lock"]["liquidated_on"] == D[26] and "pending_set_on" not in st3


def test_liquidation_sells_within_the_participation_limit_and_flags_overdue(env):
    raw, v = _prices(drop_at=23), 200_000.0                      # A: 200.000 cp/phiên → ~20.100 cp/phiên được bán
    home = _home(env, raw, vol={"A": v})
    _state(home, D[20])
    _run(home, 25, raw)
    held = SH0
    for i in (26, 27, 28, 29):
        dec, st = _run(home, i, raw)
        if i == 26:                                              # chạy lại phiên vừa bán một phần: không bán thêm
            trd_before, st_before = _csv(home, "trades.csv"), st
            _, st_again = _run(home, 26, raw)
            assert _csv(home, "trades.csv").equals(trd_before) and st_again["positions"] == st_before["positions"]
            assert st_again["risk_lock"]["exit_sessions"] == 1
        cap = _cap(raw, v, i)
        trd = _csv(home, "trades.csv")
        sold = trd[(trd.date == D[i]) & (trd.side == "SELL")]
        assert sold.quantity.astype(int).tolist() == [min(cap, held)], i
        held -= min(cap, held)
        assert st["positions"] == ({"A": held} if held else {}) and st["risk_lock"]["exit_sessions"] == i - 25
        assert st["risk_lock"]["liquidation"] == "PENDING" and held > 0
    decs = _csv(home, "decisions.csv")
    assert decs[decs.action == "LIQUIDATION_PENDING"].date.tolist() == D[26:30]
    assert decs[decs.action == "LIQUIDATION_OVERDUE"].date.tolist() == D[28:30]          # sau 3 phiên khớp vẫn còn
    assert "max_exit_days 3" in decs[decs.action == "LIQUIDATION_OVERDUE"].models.iloc[0]
    assert st["risk_lock"]["overdue_since"] == D[28]


def test_liquidation_without_the_raw_price_of_the_session_waits_and_is_not_done(env):
    raw = _prices(drop_at=23)
    home = _home(env, raw, skip={(D[26], "A")})                  # kho thiếu giá gốc A phiên IDX[26]
    _state(home, D[20])
    _run(home, 25, raw)
    dec, st = _run(home, 26, raw)                                # bảng close (đã ffill) vẫn có giá A ở IDX[26]
    trd = _csv(home, "trades.csv")
    assert "SELL" not in trd.side.tolist() and trd[trd.side == "UNFILLED_NO_PRICE"].asset.tolist() == ["A"]
    assert st["positions"] == {"A": SH0} and st["risk_lock"]["liquidation"] == "PENDING"
    decs = _csv(home, "decisions.csv")
    assert "thiếu giá đóng cửa gốc phiên " + D[26] in decs[decs.action == "LIQUIDATION_PENDING"].models.item()
    data.save_store(pd.DataFrame([{"date": D[26], "ticker": "A", "open": 9_800.0, "high": 9_800.0, "low": 9_800.0,
                                   "close": 9_800.0, "volume": 1e7, "observed_at": "2026-04-20", "source": "fixture"}],
                                 columns=data.COLS), root=home)
    dec, st = _run(home, 27, raw)                                # có giá: thử lại và bán
    assert st["positions"] == {} and st["risk_lock"]["liquidation"] == "DONE" and st["risk_lock"]["liquidated_on"] == D[27]


@pytest.mark.parametrize("broken", ["TODO", None])
def test_broken_threshold_while_locked_keeps_the_lock_and_saves_the_state(env, monkeypatch, broken):
    """Ngưỡng hỏng SAU khi đã khóa (broken=None: mất cả khối risk_limits): tới kỳ ghi lại RISK_CASH_WAIT_OWNER, lần chạy không
    dừng; ngưỡng trong thông báo lấy từ risk_lock; vẫn ghi DRAWDOWN_UNVERIFIED, giữ khóa và lưu trạng thái."""
    monkeypatch.setitem(config.CFG["paper"], "rebalance_days", 1)          # tới kỳ mỗi phiên
    raw = _prices(drop_at=23)
    home = _home(env, raw)
    _state(home, D[20])
    _, st = _run(home, 25, raw)
    assert st["risk_lock"]["threshold"] == 0.15 and st["risk_lock"]["max_exit_days"] == 3
    _, st = _run(home, 26, raw)                                  # bán hết
    assert st["risk_lock"]["liquidation"] == "DONE"
    if broken is None:
        monkeypatch.setitem(config.CFG["paper"], "risk_limits", None)
    else:
        monkeypatch.setitem(config.CFG["paper"]["risk_limits"], "max_drawdown", broken)
    dec, st = _run(home, 27, raw)
    today = _csv(home, "decisions.csv").query("date == @D[27]")
    assert {"DRAWDOWN_UNVERIFIED", "RISK_CASH_WAIT_OWNER"} <= set(today.action)
    assert "ngưỡng 15%" in today[today.action == "RISK_CASH_WAIT_OWNER"].models.item()
    assert dec["action"] == "RISK_CASH_WAIT_OWNER" and st["last_date"] == D[27] and "risk_lock" in st


def test_liquidation_with_broken_limits_sells_nothing_and_retries(env, monkeypatch):
    raw = _prices(drop_at=23)
    home = _home(env, raw)
    _state(home, D[20])
    _run(home, 25, raw)
    monkeypatch.setitem(config.CFG["paper"], "risk_limits", None)
    dec, st = _run(home, 26, raw)
    trd = _csv(home, "trades.csv")
    assert trd[trd.date == D[26]].side.tolist() == ["UNFILLED_LIQUIDITY"] and st["positions"] == {"A": SH0}
    assert st["risk_lock"]["liquidation"] == "PENDING" and st["risk_lock"]["exit_sessions"] == 1 and st["pending"] == []
    decs = _csv(home, "decisions.csv").query("date == @D[26]")
    assert "thiếu paper.risk_limits" in decs[decs.action == "LIQUIDATION_PENDING"].models.item()
    assert "DRAWDOWN_UNVERIFIED" in decs.action.tolist()


# ---------- 6. chạy lại cùng phiên, dữ liệu đóng băng ----------

def test_running_the_same_session_twice_adds_no_row_and_keeps_the_state(env):
    raw = _prices()
    home = _home(env, raw)
    _state(home, D[20])
    _, st1 = _run(home, 22, raw)
    rows1 = _csv(home, "drawdown.csv")
    _, st2 = _run(home, 22, raw)
    assert _csv(home, "drawdown.csv").equals(rows1) and st1["dd"] == st2["dd"]
    assert rows1.date.tolist() == D[21:23]


def test_frozen_data_still_measures_and_locks(env):
    raw = _prices(drop_at=23)
    home = _home(env, raw)
    _state(home, D[20])
    dec, st = _run(home, 25, raw, frozen=True)
    assert st["risk_lock"]["since"] == D[23] and st["pending"] == [] and st["positions"] == {"A": SH0}
    assert set(_csv(home, "decisions.csv").action) == {"RISK_CASH_WAIT_OWNER", "NO_DECISION_DATA_QUALITY"}
    dec, st = _run(home, 26, raw)                                # hết đóng băng: lệnh bán chờ mới khớp
    assert st["positions"] == {} and st["risk_lock"]["liquidation"] == "DONE"


# ---------- 7. chỉ Owner gỡ khóa ----------

class Api:
    def __init__(self, merged_by="owner", base="main", merged=True, fail=False, pulls=None):
        self.merged_by, self.base, self.merged, self.fail, self.pulls, self.calls = merged_by, base, merged, fail, pulls, []

    def __call__(self, path):
        self.calls.append(path)
        if self.fail:
            raise OSError("mạng lỗi")
        if path.startswith("commits/"):
            return self.pulls if self.pulls is not None else [
                {"number": 91, "merged_at": "2026-04-10T00:00:00Z" if self.merged else None, "base": {"ref": self.base}}]
        return {"number": 91, "merged": self.merged, "merged_at": "2026-04-10T00:00:00Z", "merged_by": {"login": self.merged_by}}


def _git(value):
    """git_last_release_commit giả: commit đổi giá trị mới nhất là 'aaaa…' và đặt `value`."""
    return lambda root: ("a" * 40, value, None)


GIT = _git("2026-03-25")


@pytest.mark.parametrize("value, api, git, ok, why", [
    ("2026-03-25", Api(), GIT, True, "chủ kho"),
    (None, Api(), GIT, False, None),
    ("2026-03-24", Api(), GIT, False, "khác risk_lock.since"),
    ("2026-03-25", Api(merged_by="ai-khac"), GIT, False, "không phải chủ kho"),
    ("2026-03-25", Api(base="feature"), GIT, False, "không thuộc PR nào đã gộp vào main"),
    ("2026-03-25", Api(merged=False), GIT, False, "không thuộc PR nào đã gộp vào main"),
    ("2026-03-25", Api(pulls=[]), GIT, False, "không thuộc PR nào"),
    ("2026-03-25", Api(fail=True), GIT, False, "API GitHub"),
    ("2026-03-25", Api(), lambda root: (None, None, "kho nông (shallow clone)"), False, "kho nông"),
    ("2026-03-25", Api(), _git("2026-03-24"), False, "lần đổi giá trị paper.risk_lock_release mới nhất"),
    ("2026-03-25", Api(), _git(None), False, "khác risk_lock.since"),
])
def test_release_check_needs_the_exact_value_and_an_owner_merged_pr(value, api, git, ok, why):
    got, reason = rg.release_check({"since": "2026-03-25"}, value, root=".", git=git, api=api, owner="owner")
    assert got is ok and (reason is None if why is None else why in reason)
    import datetime as dt
    assert rg.release_check({"since": "2026-03-25"}, dt.date(2026, 3, 25), root=".", git=GIT, api=Api(), owner="owner")[0]
    assert not rg.release_check({"since": "2026-03-25"}, "2026-03-25", root=".", git=GIT, api=Api(), owner="")[0]


def _locked_home(env):
    raw = _prices(drop_at=23)
    home = _home(env, raw)
    _state(home, D[20])
    _run(home, 25, raw)
    _run(home, 26, raw)                                          # bán hết
    assert _st(home)["risk_lock"]["since"] == D[23]
    return home, raw


def test_recovered_nav_or_wrong_release_does_not_unlock(env, monkeypatch):
    home, raw = _locked_home(env)
    monkeypatch.setattr(rg, "git_last_release_commit", _git(D[23]))
    monkeypatch.setattr(rg, "github_api", Api())
    monkeypatch.setenv("GITHUB_REPOSITORY_OWNER", "owner")
    _run(home, 27, raw)                                          # chưa đặt giá trị gỡ: NAV hồi cũng không gỡ
    assert "risk_lock" in _st(home)
    monkeypatch.setitem(config.CFG["paper"], "risk_lock_release", D[22])
    dec, st = _run(home, 28, raw)
    assert "risk_lock" in st and dec["action"] == "RISK_LOCK_RELEASE_UNVERIFIED" and "khác risk_lock.since" in dec["models"]


@pytest.mark.parametrize("api, git, why", [
    (Api(merged_by="ai-khac"), _git(D[23]), "không phải chủ kho"),
    (Api(fail=True), _git(D[23]), "API GitHub"),
    (Api(), _git(D[22]), "lần đổi giá trị paper.risk_lock_release mới nhất"),
    (Api(), lambda root: (None, None, "kho nông (shallow clone): thiếu lịch sử git"), "kho nông"),
])
def test_release_without_owner_merge_keeps_the_lock(env, monkeypatch, api, git, why):
    home, raw = _locked_home(env)
    monkeypatch.setattr(rg, "git_last_release_commit", git)
    monkeypatch.setattr(rg, "github_api", api)
    monkeypatch.setenv("GITHUB_REPOSITORY_OWNER", "owner")
    monkeypatch.setitem(config.CFG["paper"], "risk_lock_release", D[23])
    dec, st = _run(home, 27, raw)
    assert "risk_lock" in st and dec["action"] == "RISK_LOCK_RELEASE_UNVERIFIED" and why in dec["models"]


def test_owner_release_unlocks_and_resets_the_peak(env, monkeypatch):
    home, raw = _locked_home(env)
    monkeypatch.setattr(rg, "git_last_release_commit", _git(D[23]))
    monkeypatch.setattr(rg, "github_api", Api())
    monkeypatch.setenv("GITHUB_REPOSITORY_OWNER", "owner")
    monkeypatch.setitem(config.CFG["paper"], "risk_lock_release", D[23])
    dec, st = _run(home, 27, raw)
    assert "risk_lock" not in st and dec["action"] == "RISK_LOCK_RELEASED_BY_OWNER"
    assert st["risk_lock_released"] == {"since": D[23], "on": D[27]}
    assert st["dd"]["peak"] == st["dd"]["nav"] and st["dd"]["peak_date"] == D[27]
    dec, st = _run(home, 28, raw)                                # giá trị cũ còn trong config: không còn khóa nào để gỡ
    assert dec is None or dec["action"] not in ("RISK_LOCK_RELEASED_BY_OWNER", "RISK_LOCK_RELEASE_UNVERIFIED")


def _repo(path):
    """Kho git tạm: → (git, commit); commit(nội dung, thông điệp[, tệp]) ghi tệp, commit và trả sha."""
    path.mkdir(parents=True, exist_ok=True)

    def git(*a):
        return subprocess.run(["git", *a], cwd=path, check=True, capture_output=True, text=True).stdout.strip()

    def commit(text, msg, name="config.yaml"):
        (path / name).write_text(text, encoding="utf-8")
        git("add", name)
        git("commit", "-q", "-m", msg)
        return git("rev-parse", "HEAD")
    git("init", "-q")
    git("config", "user.email", "t@example.invalid")
    git("config", "user.name", "t")
    return git, commit


def test_git_release_commit_follows_the_yaml_value_and_refuses_shallow_clones(tmp_path):
    """Bản chấm L-09 PR #91 vòng 2, BLOCKER 2: chỉ commit đổi GIÁ TRỊ paper.risk_lock_release mới tính; commit chỉ sửa chú
    thích có tên field, đổi ngoặc kép, đổi định dạng hay khóa khác thì không; dòng đổi giá trị không chứa tên field vẫn tính."""
    src = tmp_path / "src"
    _, commit = _repo(src)
    commit("paper:\n  risk_lock_release: null\n", "a")                                      # commit gốc: null, chưa đổi
    b = commit("paper:\n  risk_lock_release: 2026-03-25\n", "b")                            # đổi giá trị
    commit("x", "c", name="note.txt")                                                       # không đụng config.yaml
    commit("paper:\n  # risk_lock_release: chỉ chủ kho đổi\n  risk_lock_release: '2026-03-25'\n", "d")  # chú thích, ngoặc
    commit("paper:\n  risk_lock_release:\n    2026-03-25\n  other: 1\n", "e")               # định dạng, khóa khác
    assert rg.git_last_release_commit(src) == (b, "2026-03-25", None)
    f = commit("paper:\n  risk_lock_release:\n    2026-03-27\n  other: 1\n", "f")           # dòng đổi không có tên field
    assert rg.git_last_release_commit(src) == (f, "2026-03-27", None)
    shallow = tmp_path / "shallow"
    subprocess.run(["git", "clone", "-q", "--depth", "1", f"file://{src}", str(shallow)], check=True, capture_output=True)
    sha, value, why = rg.git_last_release_commit(shallow)
    assert sha is None and value is None and "kho nông" in why
    commit("paper: [\n", "g")                                                                # YAML hỏng: không đoán
    sha, value, why = rg.git_last_release_commit(src)
    assert sha is None and value is None and "không phải YAML hợp lệ" in why
    root = tmp_path / "root"
    _, commit = _repo(root)
    r0 = commit("paper:\n  risk_lock_release: 2026-03-25\n", "gốc")                         # commit gốc đặt giá trị
    assert rg.git_last_release_commit(root) == (r0, "2026-03-25", None)
    added = tmp_path / "added"
    _, commit = _repo(added)
    commit("x", "gốc", name="note.txt")
    a1 = commit("paper:\n  risk_lock_release: 2026-03-25\n", "thêm config.yaml")             # commit cha chưa có tệp
    assert rg.git_last_release_commit(added) == (a1, "2026-03-25", None)
    never = tmp_path / "never"
    _, commit = _repo(never)
    commit("paper:\n  risk_lock_release: null  # risk_lock_release\n", "n0")
    commit("paper:\n  risk_lock_release: null  # risk_lock_release: sửa chú thích\n", "n1")
    sha, value, why = rg.git_last_release_commit(never)
    assert sha is None and "không tìm thấy commit nào đổi giá trị" in why


class ShaApi:
    """API GitHub giả theo commit: commits/{sha}/pulls → PR prs[sha] đã gộp vào main; pulls/{số} → người gộp merged_by[số]."""
    def __init__(self, prs, merged_by):
        self.prs, self.merged_by, self.calls = prs, merged_by, []

    def __call__(self, path):
        self.calls.append(path)
        kind, key = path.split("/")[:2]
        if kind == "commits":
            return ([{"number": self.prs[key], "merged_at": "2026-04-10T00:00:00Z", "base": {"ref": "main"}}]
                    if key in self.prs else [])
        n = int(key)
        return {"number": n, "merged": True, "merged_at": "2026-04-10T00:00:00Z", "merged_by": {"login": self.merged_by[n]}}


def test_owner_comment_commit_after_an_unapproved_value_change_keeps_the_lock(env, monkeypatch):
    """Bản chấm L-09 PR #91 vòng 2, BLOCKER 2 (đối kháng, git thật): giá trị gỡ do một PR không phải chủ kho gộp đặt; sau đó chủ
    kho gộp PR chỉ sửa chú thích có tên field. Commit được xác minh là commit đổi GIÁ TRỊ → giữ khóa. Đối chứng: chủ kho gộp
    PR đổi giá trị thì gỡ."""
    home, raw = _locked_home(env)                                # khóa từ D[23], đã bán hết
    _, commit = _repo(home)
    commit("paper:\n  risk_lock_release: null\n", "nền")
    bad = commit(f"paper:\n  risk_lock_release: {D[23]}\n", "đổi giá trị, không do chủ kho gộp")
    note = commit(f"paper:\n  # risk_lock_release: chỉ chủ kho gộp PR đổi giá trị này\n  risk_lock_release: {D[23]}\n",
                  "chỉ sửa chú thích")
    api = ShaApi({bad: 7, note: 8}, {7: "ai-khac", 8: "owner"})
    monkeypatch.setattr(rg, "github_api", api)
    monkeypatch.setenv("GITHUB_REPOSITORY_OWNER", "owner")
    monkeypatch.setitem(config.CFG["paper"], "risk_lock_release", D[23])
    dec, st = _run(home, 27, raw)
    assert "risk_lock" in st and dec["action"] == "RISK_LOCK_RELEASE_UNVERIFIED"
    assert "không phải chủ kho" in dec["models"] and "#7: ai-khac" in dec["models"]
    assert f"commits/{bad}/pulls" in api.calls and f"commits/{note}/pulls" not in api.calls
    commit("paper:\n  risk_lock_release: null\n", "về null")                                 # đối chứng
    good = commit(f"paper:\n  risk_lock_release: {D[23]}\n", "chủ kho gộp PR đặt lại giá trị")
    api.prs[good], api.merged_by[9] = 9, "owner"
    _, st = _run(home, 28, raw)
    rel = _csv(home, "decisions.csv").query("date == @D[28] and action == 'RISK_LOCK_RELEASED_BY_OWNER'")
    assert "risk_lock" not in st and "PR #9" in rel.models.item() and good[:7] in rel.models.item()


def test_owner_release_during_liquidation_waits_until_everything_is_sold(env, monkeypatch):
    """Bản chấm L-09 PR #91 vòng 2, BLOCKER 1; Owner chọn 22/11/2026 «Hoãn gỡ tới khi thanh lý xong»: Owner gỡ khi đã bán một
    phần → giữ khóa, RISK_LOCK_RELEASE_UNVERIFIED «thanh lý chưa xong», không phiên nào bán quá giới hạn thanh khoản; lần
    chạy đầu tiên sau khi thanh lý DONE thì gỡ, đỉnh đặt lại."""
    raw, v = _prices(drop_at=23), 400_000.0                      # A: ~40.200 cp/phiên được bán → hết sau 3 phiên khớp
    home = _home(env, raw, vol={"A": v})
    _state(home, D[20])
    _run(home, 25, raw)
    _, st = _run(home, 26, raw)                                  # phiên khớp thứ nhất: bán một phần
    assert st["positions"] == {"A": SH0 - _cap(raw, v, 26)} and st["risk_lock"]["liquidation"] == "PENDING"
    monkeypatch.setattr(rg, "git_last_release_commit", _git(D[23]))
    monkeypatch.setattr(rg, "github_api", Api())
    monkeypatch.setenv("GITHUB_REPOSITORY_OWNER", "owner")
    monkeypatch.setitem(config.CFG["paper"], "risk_lock_release", D[23])  # Owner gỡ khi còn vị thế
    for i in (27, 28):
        before = st["positions"]["A"]
        _, st = _run(home, i, raw)
        trd = _csv(home, "trades.csv")
        sold = trd[(trd.date == D[i]) & (trd.side == "SELL")].quantity.astype(int).tolist()
        assert sold == [min(_cap(raw, v, i), before)], i         # bán theo giới hạn, không bán hết một lần
        assert "risk_lock" in st and "risk_lock_released" not in st
        day = D[i]
        rel = _csv(home, "decisions.csv").query("date == @day and action == 'RISK_LOCK_RELEASE_UNVERIFIED'")
        assert "thanh lý chưa xong, còn 1 mã (A)" in rel.models.item() and "chủ kho" in rel.models.item()
    assert st["positions"] == {} and st["risk_lock"]["liquidation"] == "DONE" and st["risk_lock"]["liquidated_on"] == D[28]
    decs = _csv(home, "decisions.csv")
    assert not {"RISK_LOCK_RELEASED_BY_OWNER", "LIQUIDATION_OVERDUE"} & set(decs.action)
    _, st = _run(home, 29, raw)                                  # lần chạy đầu tiên sau khi thanh lý xong: gỡ
    assert "risk_lock" not in st and st["risk_lock_released"] == {"since": D[23], "on": D[29]}
    assert _csv(home, "decisions.csv").query("date == @D[29]").action.tolist().count("RISK_LOCK_RELEASED_BY_OWNER") == 1
    assert st["dd"]["peak"] == st["dd"]["nav"] and st["dd"]["peak_date"] == D[29]


def test_owner_release_with_a_position_that_cannot_be_sold_keeps_the_lock_and_flags_overdue(env, monkeypatch):
    """Owner 22/11/2026: mã không bán được mãi (ở đây: giao dịch quá ít, giới hạn chưa đủ một lô) thì khóa còn mãi, kèm
    LIQUIDATION_OVERDUE; mỗi lần chạy ghi RISK_LOCK_RELEASE_UNVERIFIED «thanh lý chưa xong»."""
    raw = _prices(drop_at=23)
    home = _home(env, raw, vol={"A": 100.0})
    _state(home, D[20])
    _run(home, 25, raw)
    monkeypatch.setattr(rg, "git_last_release_commit", _git(D[23]))
    monkeypatch.setattr(rg, "github_api", Api())
    monkeypatch.setenv("GITHUB_REPOSITORY_OWNER", "owner")
    monkeypatch.setitem(config.CFG["paper"], "risk_lock_release", D[23])
    for i in (26, 27, 28, 29):
        _, st = _run(home, i, raw)
    assert "risk_lock" in st and st["positions"] == {"A": SH0} and st["risk_lock"]["liquidation"] == "PENDING"
    decs = _csv(home, "decisions.csv")
    rel = decs[decs.action == "RISK_LOCK_RELEASE_UNVERIFIED"]
    assert rel.date.tolist() == D[26:30] and rel.models.str.contains("thanh lý chưa xong, còn 1 mã").all()
    assert decs[decs.action == "LIQUIDATION_OVERDUE"].date.tolist() == D[28:30]
    assert "RISK_LOCK_RELEASED_BY_OWNER" not in decs.action.tolist() and "SELL" not in _csv(home, "trades.csv").side.tolist()


# ---------- 8. sổ không có vị thế: đầu ra cũ không đổi ----------

def _book_without_positions(home, monkeypatch, measure):
    monkeypatch.setattr(config, "ROOT", home)
    monkeypatch.setattr(paper, "ROOT", home)
    if not measure:                                             # như trước R1b: không đo, không khóa
        monkeypatch.setattr(paper, "_measure_drawdown", lambda *a, **k: (None, None))
    raw = _prices()
    _home(home, raw)
    for i in (20, 21, 22, 25, 29):
        paper.run(D[i], raw, NONE_PREDS, {}, IDX)
    monkeypatch.undo()
    out = {n: (home / "paper" / n).read_bytes() for n in ("nav.csv", "decisions.csv") if (home / "paper" / n).exists()}
    st = json.loads((home / "paper" / "state.json").read_text(encoding="utf-8"))
    return out, st


def test_book_without_positions_keeps_its_outputs_byte_for_byte(tmp_path, monkeypatch):
    new, st_new = _book_without_positions(tmp_path / "r1b", monkeypatch, measure=True)
    old, st_old = _book_without_positions(tmp_path / "old", monkeypatch, measure=False)
    assert new == old and not (tmp_path / "r1b" / "paper" / "trades.csv").exists()
    dd = st_new.pop("dd")
    st_old.pop("dd")
    assert st_new == st_old and dd["checked_through"] == D[29] and dd["peak"] == 1_000_000_000.0
    rows = pd.read_csv(tmp_path / "r1b" / "paper" / "drawdown.csv", dtype=str)
    assert rows.date.tolist() == D[20:30] and set(rows.drawdown) == {"0.0"}
