"""LỆNH R1a (QĐ-5, ADR-0016): cổng rủi ro trước khi mua của sổ giấy. Không mạng. Không ghi kho (ROOT trỏ vào thư mục tạm)."""
import copy
import json
import pathlib
import subprocess

import numpy as np
import pandas as pd
import pytest

from engine import config, paper, risk_gate as rg
from engine import verified_adjust as va

REPO = pathlib.Path(__file__).resolve().parents[1]
LIM = {"max_weight": 0.20, "max_participation": 0.10, "max_exit_days": 3, "adv_sessions": 20,
       "quarantine_sessions_before": 21, "quarantine_sessions_after": 120}
NAV = 1_000_000_000.0
T5 = ["A", "B", "C", "D", "E"]


def _market(**over):
    m = {"frozen": False, "price": {t: 10_000.0 for t in T5 + ["F"]}, "adv_value": {t: 5e10 for t in T5 + ["F"]},
         "quarantined": {}}
    m.update(over)
    return m


def _book(nav=NAV, positions=None):
    return {"nav": nav, "positions": positions or {}}


def _check(targets=T5, book=None, market=None, limits=LIM):
    return rg.check(list(targets), book or _book(), market or _market(), limits)


# ---------- 1. Tỷ trọng một mã ----------

def test_weight_pass_with_five_new_targets():
    g = _check()
    assert g["verdict"] == "PASS" and g["targets"] == T5 and g["reasons"] == []


def test_weight_fail_with_four_new_targets():
    g = _check(T5[:4])
    assert g["verdict"] == "FAIL" and any("tỷ trọng 24.88%" in r for r in g["reasons"])


def test_weight_fail_when_a_held_position_is_too_large():
    g = _check(book=_book(positions={"A": 25_000}))         # 25.000 × 10.000 = 250 triệu = 25% NAV
    assert g["verdict"] == "FAIL" and any(r.startswith("A: tỷ trọng 25.00%") for r in g["reasons"])
    assert _check(book=_book(positions={"A": 19_000}))["verdict"] == "PASS"


# ---------- 2. Số phiên thoát vị thế ----------

def test_liquidity_pass_and_fail_at_the_limit():
    value = NAV / 5 * rg.BUY_BUDGET
    just_ok = value / (0.10 * 3)                           # đúng 3 phiên
    assert _check(market=_market(adv_value={t: just_ok for t in T5}))["verdict"] == "PASS"
    g = _check(market=_market(adv_value={t: just_ok * 0.99 for t in T5}))
    assert g["verdict"] == "FAIL" and any("phiên để thoát vị thế" in r for r in g["reasons"])


@pytest.mark.parametrize("adv", [None, 0.0, float("nan"), -1.0])
def test_liquidity_fail_when_traded_value_is_missing(adv):
    m = _market()
    m["adv_value"] = dict(m["adv_value"], C=adv)
    g = _check(market=m)
    assert g["verdict"] == "FAIL" and any(r.startswith("C: thiếu giá trị giao dịch") for r in g["reasons"])


# ---------- 3. Mã có sự kiện bị cách ly (QĐ-3) ----------

def test_quarantined_ticker_is_excluded_then_remaining_targets_are_checked():
    m = _market(quarantined={"C": "sự kiện stock_split bị cách ly"})
    g = _check(T5 + ["F"], market=m)
    assert g["targets"] == ["A", "B", "D", "E", "F"] and "C" in g["excluded"] and g["verdict"] == "PASS"
    g = _check(market=m)                                   # còn 4 mã → mỗi mã 24,9% > 20%
    assert g["excluded"] == {"C": "sự kiện stock_split bị cách ly"} and g["verdict"] == "FAIL"


def test_quarantine_not_checked_fails():
    g = _check(market=_market(quarantined=None))
    assert g["verdict"] == "FAIL" and "cách ly" in g["reasons"][0]


def test_snapshot_window_for_quarantined_events(tmp_path, monkeypatch):
    """market_snapshot loại mã theo cửa sổ QĐ-3 quanh sự kiện cổ phiếu chưa vào chuỗi kiểm chứng, kể cả sự kiện sau t đã
    có trong bảng sự kiện; sự kiện đã vào chuỗi không loại. Cửa sổ thu nhỏ (−2/+5 phiên) cho dễ đọc."""
    idx, _ = _store(tmp_path, volume=1e6)                 # 40 phiên, phiên cuối idx[39] = 2026-02-27
    as_of = pd.Timestamp("2026-03-02")
    lim = dict(LIM, quarantine_sessions_before=2, quarantine_sessions_after=5)
    k = [idx[36], idx[30], idx[37], pd.Timestamp("2026-03-03"), pd.Timestamp("2026-03-05")]
    rows = pd.DataFrame({"ticker": list("ABCDE"), "type": ["stock_split"] * 5, "ex_date": k,
                         "trade_date": k[:3] + [pd.NaT, pd.NaT],
                         "verify_state": [va.Q + "THIEU_BANG_CHUNG", va.Q + "THIEU_BANG_CHUNG", va.OK,
                                          va.NA_NODATA, va.NA_NODATA],
                         "in_verified_chain": [False, False, True, False, False]})
    monkeypatch.setattr(va, "verify_events", lambda *a, **kw: rows)
    snap = rg.market_snapshot(as_of, list("ABCDE"), lim, root=tmp_path, frozen=False)
    # A: 3 phiên sau k (≤ 5) → loại. B: 9 phiên sau → không. C: đã vào chuỗi → không.
    # D: k = 2026-03-03, 2 phiên sau phiên cuối → t ở 2 phiên trước k (≤ 2) → loại. E: 4 phiên trước k → không.
    assert sorted(snap["quarantined"]) == ["A", "D"], snap
    assert "3 phiên sau" in snap["quarantined"]["A"] and "2 phiên trước" in snap["quarantined"]["D"]
    assert set(snap["adv_value"]) == set("ABCDE")


AXIS = pd.bdate_range("2025-01-01", periods=400)


@pytest.mark.parametrize("offset,hit", [(120, True), (121, False), (0, True), (-21, True), (-22, False)])
def test_qd3_window_boundaries(offset, hit):
    k = AXIS[100]
    t = AXIS[100 + offset]
    got = rg.quarantine_window_hits(t, AXIS, [("X", k, "sự kiện")], 21, 120)
    assert ("X" in got) is hit, (offset, got)


def test_qd3_counts_sessions_without_calendar_holidays():
    """Đếm phiên bỏ ngày lịch HOSE ghi is_session=0 (ví dụ ngày «ma» trong kho giá)."""
    k, t = AXIS[100], AXIS[221]                           # 121 ngày của bảng giá sau k: ngoài cửa sổ
    assert rg.quarantine_window_hits(t, rg.session_axis(AXIS), [("X", k, "s")], 21, 120) == {}
    holiday = AXIS[150].date().isoformat()
    axis = rg.session_axis(AXIS, {holiday: 0})            # bỏ một ngày nghỉ giữa k và t → còn 120 phiên
    assert len(axis) == len(AXIS) - 1
    assert "X" in rg.quarantine_window_hits(t, axis, [("X", k, "s")], 21, 120)
    # Ngày lịch không phủ hoặc ghi 1 thì giữ nguyên.
    assert len(rg.session_axis(AXIS, {holiday: 1})) == len(AXIS)


def test_qd3_future_event_counts_calendar_sessions_after_the_last_price_date():
    axis = AXIS[:200]
    t = axis[-1]
    future = pd.bdate_range(t + pd.Timedelta(days=1), periods=30)
    assert "X" in rg.quarantine_window_hits(t, axis, [("X", future[20], "s")], 21, 120)      # 21 phiên trước k
    assert rg.quarantine_window_hits(t, axis, [("X", future[21], "s")], 21, 120) == {}        # 22 phiên trước k
    cal = {future[3].date().isoformat(): 0}               # một ngày nghỉ HOSE giữa t và k: k gần thêm một phiên
    assert "X" in rg.quarantine_window_hits(t, axis, [("X", future[21], "s")], 21, 120, cal)


def test_snapshot_failure_leaves_inputs_empty_so_check_fails(tmp_path, monkeypatch):
    _store(tmp_path, volume=1e6)

    def boom(*a, **k):
        raise ValueError("manifest hỏng")
    monkeypatch.setattr(va, "verify_events", boom)
    snap = rg.market_snapshot(pd.Timestamp("2026-03-02"), T5, LIM, root=tmp_path, frozen=False)
    assert snap["quarantined"] is None and snap["errors"] and snap["adv_value"] == {}
    g = rg.check(T5, _book(), {**snap, "price": _market()["price"]}, LIM)
    assert g["verdict"] == "FAIL" and "manifest hỏng" in g["reasons"][0]


# ---------- 4. Dữ liệu đóng băng ----------

def test_frozen_data_fails_and_missing_flag_counts_as_frozen():
    assert _check(market=_market(frozen=True))["verdict"] == "FAIL"
    m = _market()
    del m["frozen"]
    assert _check(market=m)["verdict"] == "FAIL"


# ---------- 5. Giới hạn thiếu hoặc còn TODO ----------

@pytest.mark.parametrize("key", rg.LIMIT_KEYS)
@pytest.mark.parametrize("bad", ["drop", "TODO", "todo: Owner điền", None, 0, -1, float("nan"), True, "0.2"])
def test_missing_or_todo_limits_fail(key, bad):
    lim = dict(LIM)
    if bad == "drop":
        lim.pop(key)
    else:
        lim[key] = bad
    g = _check(limits=lim)
    assert g["verdict"] == "FAIL" and key in g["reasons"][0]


@pytest.mark.parametrize("key", rg.FRACTION_KEYS)
def test_fraction_limits_must_be_below_one(key):
    assert _check(limits=dict(LIM, **{key: 1.0}))["verdict"] == "FAIL"


def test_limits_not_a_dict_fail_and_config_defaults_are_valid():
    assert _check(limits=None)["verdict"] == "FAIL"
    assert rg.limits_problem(dict(LIM, adv_sessions=20.5))
    assert rg.limits_problem(dict(LIM, quarantine_sessions_before=21.5))
    assert rg.limits_problem(dict(LIM, quarantine_sessions_after=120.5))
    assert config.CFG["paper"]["risk_limits"] == LIM and rg.limits_problem(config.CFG["paper"]["risk_limits"]) is None


def test_check_is_pure():
    b, m = _book(positions={"A": 100}), _market(quarantined={"C": "x"})
    b0, m0 = copy.deepcopy(b), copy.deepcopy(m)
    _check(T5, b, m)
    assert b == b0 and m == m0


# ---------- 6. Sổ giấy: cổng lúc ra quyết định ----------

def _store(root, volume, n=40, tickers=("A", "B", "C", "D", "E", "F", "G", "H")):
    idx = pd.bdate_range("2026-01-05", periods=n)
    rows = []
    for j, t in enumerate(tickers):
        for i, d in enumerate(idx):
            px = 10_000.0 + 100 * j + 10 * i
            rows.append({"date": d.date().isoformat(), "ticker": t, "open": px, "high": px, "low": px, "close": px,
                         "volume": volume, "observed_at": "2026-03-10", "source": "test"})
    p = root / config.CFG["data"]["store_dir"] / "2026-01.csv"
    p.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(p, index=False)
    return idx, list(tickers)


def _run_paper(root, monkeypatch, volume, limits="default", frozen=False, state=None):
    monkeypatch.setattr(config, "ROOT", root)
    monkeypatch.setattr(paper, "ROOT", root)
    if limits != "default":
        monkeypatch.setitem(config.CFG["paper"], "risk_limits", limits)
    idx, tickers = _store(root, volume)
    if state is not None:
        (root / "paper").mkdir(parents=True, exist_ok=True)
        (root / "paper" / "state.json").write_text(json.dumps(state), encoding="utf-8")
    close = pd.DataFrame({t: [10_000.0 + 100 * j + 10 * i for i in range(len(idx))] for j, t in enumerate(tickers)}, index=idx)
    reg = {"M": {"state": "ACTIVE", "backtest": {"ic_t": 3.0}}}
    as_of = idx[-1]
    preds = pd.DataFrame([(as_of, "M", t, float(k)) for k, t in enumerate(tickers)],
                         columns=["date", "model_id", "ticker", "score"])
    nav, decision = paper.run(str(as_of.date()), close, preds, reg, idx, frozen=frozen)
    state = json.loads((root / "paper" / "state.json").read_text(encoding="utf-8"))
    dec = root / "paper" / "decisions.csv"
    return decision, state, dec.read_text(encoding="utf-8") if dec.exists() else ""


def test_paper_output_unchanged_when_every_condition_passes(tmp_path, monkeypatch):
    """Mọi điều kiện đạt: quyết định, sổ và tệp đầu ra trùng từng ký tự với lúc cổng được thay bằng 'luôn PASS'."""
    d1, s1, f1 = _run_paper(tmp_path / "co_cong", monkeypatch, volume=1e6)
    assert d1["action"] == "REBALANCE" and d1["targets"] == "H;G;F;E;D" and "cổng rủi ro" not in d1["models"]
    monkeypatch.setattr(rg, "check", lambda targets, *a, **k: {"verdict": "PASS", "reasons": [], "targets": list(targets),
                                                                "excluded": {}})
    d2, s2, f2 = _run_paper(tmp_path / "khong_cong", monkeypatch, volume=1e6)
    assert (d1, s1, f1) == (d2, s2, f2)


def test_paper_fail_opens_no_new_position(tmp_path, monkeypatch):
    d, s, _ = _run_paper(tmp_path, monkeypatch, volume=1.0)
    assert d["action"] == "RISK_GATE_FAIL" and d["targets"] == "" and "phiên để thoát vị thế" in d["models"]
    assert s["pending"] is None and s["positions"] == {}


def test_paper_fails_closed_without_limits(tmp_path, monkeypatch):
    d, s, _ = _run_paper(tmp_path, monkeypatch, volume=1e6, limits=None)
    assert d["action"] == "RISK_GATE_FAIL" and "risk_limits" in d["models"] and s["pending"] is None


def _read(root, name):
    return pd.read_csv(root / "paper" / name, dtype={"date": str})


# ---------- 7. Thanh khoản: đúng adv_sessions phiên cuối, thiếu thì FAIL, không lùi cửa sổ ----------

ADV_IDX = pd.bdate_range("2026-01-05", periods=30)


def _adv_frames(gaps=()):
    raw = pd.DataFrame({"A": 10_000.0, "B": 20_000.0}, index=ADV_IDX)
    vol = pd.DataFrame({"A": [1_000.0 * (i + 1) for i in range(30)], "B": 500.0}, index=ADV_IDX)
    for t, i, col in gaps:
        (raw if col == "close" else vol).iloc[i, list(raw.columns).index(t)] = np.nan
    return raw, vol


def test_adv_uses_exactly_the_last_n_sessions():
    adv, why = rg.adv_values(*_adv_frames(), ADV_IDX, ["A", "B"], 20)
    assert why == {} and adv["A"] == pytest.approx(10_000.0 * np.mean([1_000.0 * (i + 1) for i in range(10, 30)]))
    assert adv["B"] == pytest.approx(20_000.0 * 500.0)


@pytest.mark.parametrize("col", ["volume", "close"])
def test_adv_gap_inside_the_window_fails_without_backfilling(col):
    adv, why = rg.adv_values(*_adv_frames([("A", 25, col)]), ADV_IDX, ["A", "B"], 20)
    assert "A" not in adv and "1/20 phiên" in why["A"] and str(ADV_IDX[25].date()) in why["A"] and "B" in adv
    g = _check(["A", "B"], market=_market(adv_value=adv, adv_problem=why), limits=dict(LIM, max_weight=0.6))
    assert g["verdict"] == "FAIL" and any(r.startswith("A: thiếu giá trị giao dịch") and "1/20" in r for r in g["reasons"])


def test_adv_gap_just_outside_the_window_is_ignored():
    full, _ = rg.adv_values(*_adv_frames(), ADV_IDX, ["A"], 20)
    adv, why = rg.adv_values(*_adv_frames([("A", 9, "volume")]), ADV_IDX, ["A"], 20)
    assert why == {} and adv == full


def test_adv_fails_with_too_few_sessions_or_unknown_ticker():
    adv, why = rg.adv_values(*_adv_frames(), ADV_IDX[:15], ["A", "Z"], 20)
    assert adv == {} and "chỉ có 15 phiên" in why["A"]
    adv, why = rg.adv_values(*_adv_frames(), ADV_IDX, ["Z"], 20)
    assert adv == {} and "không có trong kho giá" in why["Z"]


def test_adv_window_counts_a_calendar_session_missing_from_the_store(tmp_path, monkeypatch):
    """Lịch HOSE ghi một ngày là phiên mà kho giá không có dòng nào: cửa sổ vẫn tính ngày đó, nên mọi mã FAIL."""
    idx, _ = _store(tmp_path, volume=1e6)
    gone = idx[30]
    store = tmp_path / config.CFG["data"]["store_dir"] / "2026-01.csv"
    df = pd.read_csv(store)
    df[df.date != gone.date().isoformat()].to_csv(store, index=False)
    _calendar(tmp_path, "2026-01-01", "2026-12-31")
    monkeypatch.setattr(va, "verify_events", lambda *a, **kw: _NO_EVENTS)
    snap = rg.market_snapshot(idx[-1], T5, LIM, root=tmp_path, frozen=False)
    assert snap["adv_value"] == {} and all(str(gone.date()) in snap["adv_problem"][t] for t in T5)
    (tmp_path / "data" / "trading_calendar.csv").unlink()        # không có lịch: dự phòng theo ngày của kho giá
    snap = rg.market_snapshot(idx[-1], T5, LIM, root=tmp_path, frozen=False)
    assert set(snap["adv_value"]) == set(T5)


def test_session_axis_adds_calendar_sessions_missing_from_prices():
    days = pd.bdate_range("2026-03-02", periods=5)
    cal = {d.date().isoformat(): 1 for d in pd.bdate_range("2026-03-02", periods=7)}
    axis = rg.session_axis(days.delete(2), cal, until=days[-1])
    assert list(axis) == list(days)
    assert list(rg.session_axis(days.delete(2), cal)) == list(days)
    assert len(rg.session_axis(days, cal, until=pd.Timestamp("2026-03-10"))) == 7


# ---------- 8. Lịch HOSE: có mà hỏng thì FAIL; không có thì dự phòng ----------

_NO_EVENTS = pd.DataFrame(columns=["ticker", "type", "ex_date", "trade_date", "verify_state", "in_verified_chain"])


def _calendar(root, start, end, holidays=(), mutate=None):
    days = pd.date_range(start, end, freq="D")
    df = pd.DataFrame({"date": [d.date().isoformat() for d in days],
                       "is_session": [0 if d.weekday() >= 5 or d.date().isoformat() in holidays else 1 for d in days],
                       "source_id": "test"})
    if mutate is not None:
        df = mutate(df)
    p = root / "data" / "trading_calendar.csv"
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(p, index=False)
    return p


def test_real_calendar_loads_and_missing_calendar_is_none(tmp_path):
    cal = rg.load_calendar(REPO)
    assert len(cal) == 730 and set(cal.values()) == {0, 1}
    assert rg.load_calendar(tmp_path) is None


def _set(i, col, value):
    def f(df):
        df = df.astype({col: object})
        df.loc[i, col] = value
        return df
    return f


CORRUPT = {                                                       # tên: (cách làm hỏng, đoạn lý do phải có)
    "is_session=2": (_set(3, "is_session", 2), "is_session khác 0 và 1"),
    "is_session rỗng": (_set(3, "is_session", ""), "is_session khác 0 và 1"),
    "is_session chữ": (_set(3, "is_session", "yes"), "is_session khác 0 và 1"),
    "ngày sai dạng": (_set(3, "date", "2026-1-04"), "không đúng dạng"),
    "ngày không tồn tại": (_set(3, "date", "2026-02-30"), "không đúng dạng"),
    "ngày trùng": (_set(3, "date", "2026-01-03"), "ngày trùng"),
    "thiếu một ngày": (lambda df: df.drop(index=10), "không liền ngày"),
    "thiếu cột is_session": (lambda df: df.drop(columns="is_session"), "thiếu cột"),
    "rỗng": (lambda df: df.iloc[0:0], "rỗng"),
}


@pytest.mark.parametrize("name", sorted(CORRUPT))
def test_corrupt_calendar_raises(tmp_path, name):
    mutate, why = CORRUPT[name]
    _calendar(tmp_path, "2026-01-01", "2026-03-31", mutate=mutate)
    with pytest.raises(ValueError, match="lịch phiên HOSE") as e:
        rg.load_calendar(tmp_path)
    assert why in str(e.value)


def test_unreadable_calendar_raises(tmp_path):
    p = tmp_path / "data" / "trading_calendar.csv"
    p.parent.mkdir(parents=True)
    p.write_bytes(b"\xff\xfe\x00date")
    with pytest.raises(ValueError, match="lịch phiên HOSE"):
        rg.load_calendar(tmp_path)


def _boundary_store(root):
    idx = pd.bdate_range("2026-01-05", periods=160)
    rows = [{"date": d.date().isoformat(), "ticker": t, "open": 10_000.0, "high": 10_000.0, "low": 10_000.0,
             "close": 10_000.0, "volume": 1e6, "observed_at": "2026-01-01", "source": "test"}
            for d in idx for t in ("X", "Y")]
    p = root / config.CFG["data"]["store_dir"] / "2026-01.csv"
    p.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(p, index=False)
    return idx


@pytest.mark.parametrize("cal,t_pos,hit", [("holiday", 131, True), ("holiday", 132, False), ("none", 131, False),
                                           ("none", 130, True)])
def test_qd3_boundary_120_121_through_the_snapshot(tmp_path, monkeypatch, cal, t_pos, hit):
    """k = phiên 10 của kho. Lịch HOSE ghi ngày idx[60] (có dòng trong kho) là ngày nghỉ: t = idx[131] là 120 phiên sau k
    (trong cửa sổ), idx[132] là 121 (ngoài). Không có lịch thì đếm theo ngày của kho: idx[131] là 121 phiên (ngoài)."""
    idx = _boundary_store(tmp_path)
    if cal == "holiday":
        _calendar(tmp_path, "2026-01-01", "2026-12-31", holidays={idx[60].date().isoformat()})
    k = idx[10]
    rows = pd.DataFrame({"ticker": ["X"], "type": ["stock_split"], "ex_date": [k], "trade_date": [k],
                         "verify_state": [va.Q + "THIEU_BANG_CHUNG"], "in_verified_chain": [False]})
    monkeypatch.setattr(va, "verify_events", lambda *a, **kw: rows)
    snap = rg.market_snapshot(idx[t_pos], ["X", "Y"], LIM, root=tmp_path, frozen=False)
    assert ("X" in snap["quarantined"]) is hit and "Y" not in snap["quarantined"], snap["quarantined"]


@pytest.mark.parametrize("name", sorted(CORRUPT))
def test_corrupt_calendar_makes_the_snapshot_fail_instead_of_falling_back(tmp_path, monkeypatch, name):
    idx = _boundary_store(tmp_path)
    _calendar(tmp_path, "2026-01-01", "2026-12-31", holidays={idx[60].date().isoformat()}, mutate=CORRUPT[name][0])
    monkeypatch.setattr(va, "verify_events", lambda *a, **kw: _NO_EVENTS)
    snap = rg.market_snapshot(idx[131], ["X", "Y"], LIM, root=tmp_path, frozen=False)
    assert snap["quarantined"] is None and snap["adv_value"] == {} and "lịch phiên HOSE" in snap["errors"][0]
    g = rg.check(["X", "Y"], _book(), {**snap, "price": {"X": 1e4, "Y": 1e4}}, dict(LIM, max_weight=0.6))
    assert g["verdict"] == "FAIL" and "lịch phiên HOSE" in g["reasons"][0]


# ---------- 9. Sổ giấy: cổng lúc khớp lệnh mua chờ ----------

def _two_sessions(root, monkeypatch, between=None):
    """Phiên T = idx[38]: cổng PASS, REBALANCE, đặt lệnh mua chờ. `between(root)` đổi dữ liệu. Phiên T+1 = idx[39]: khớp."""
    monkeypatch.setattr(config, "ROOT", root)
    monkeypatch.setattr(paper, "ROOT", root)
    idx, tickers = _store(root, volume=1e6)
    close = pd.DataFrame({t: [10_000.0 + 100 * j + 10 * i for i in range(len(idx))] for j, t in enumerate(tickers)}, index=idx)
    reg = {"M": {"state": "ACTIVE", "backtest": {"ic_t": 3.0}}}
    for i in (38, 39):
        preds = pd.DataFrame([(idx[i], "M", t, float(k)) for k, t in enumerate(tickers)],
                             columns=["date", "model_id", "ticker", "score"])
        _, decision = paper.run(str(idx[i].date()), close, preds, reg, idx)
        if i == 38:
            assert decision["action"] == "REBALANCE" and decision["targets"] == "H;G;F;E;D"
            if between is not None:
                between(root)
    st = json.loads((root / "paper" / "state.json").read_text(encoding="utf-8"))
    return st, _read(root, "decisions.csv"), _read(root, "trades.csv"), str(idx[39].date())


def test_pending_buys_fill_when_the_gate_still_passes(tmp_path, monkeypatch):
    st, dec, trd, t1 = _two_sessions(tmp_path, monkeypatch)
    assert sorted(trd[(trd.date == t1) & (trd.side == "BUY")].asset) == list("DEFGH") and len(dec) == 1


def _no_buy(st, dec, trd, t1, why):
    assert trd[trd.side == "BUY"].empty and st["positions"] == {} and st["pending"] is None
    assert sorted(trd[(trd.date == t1) & (trd.side == "UNFILLED_RISK_GATE")].asset) == list("DEFGH")
    row = dec[dec.date == t1]
    assert row.action.tolist() == ["RISK_GATE_BLOCK_BUY"] and why in row.models.item(), row.models.item()


@pytest.mark.parametrize("bad", [None, {**LIM, "max_weight": "TODO"}, {**LIM, "adv_sessions": 0}])
def test_pending_buys_blocked_when_limits_break_before_the_fill(tmp_path, monkeypatch, bad):
    def between(r):
        monkeypatch.setitem(config.CFG["paper"], "risk_limits", bad)
    st, dec, trd, t1 = _two_sessions(tmp_path, monkeypatch, between)
    _no_buy(st, dec, trd, t1, "risk_limits" if bad is None else ("TODO" if bad.get("max_weight") == "TODO" else "adv_sessions"))


def test_pending_buys_blocked_when_liquidity_data_breaks_before_the_fill(tmp_path, monkeypatch):
    def between(r):
        store = r / config.CFG["data"]["store_dir"] / "2026-01.csv"
        df = pd.read_csv(store)
        df.loc[(df.ticker == "F") & (df.date == df.date.max()), "volume"] = np.nan
        df.to_csv(store, index=False)
    st, dec, trd, t1 = _two_sessions(tmp_path, monkeypatch, between)
    _no_buy(st, dec, trd, t1, "F: thiếu giá trị giao dịch bình quân")


def _quarantine_g(monkeypatch, max_weight=None):
    def between(r):
        k = pd.Timestamp("2026-02-27")
        rows = pd.DataFrame({"ticker": ["G"], "type": ["stock_split"], "ex_date": [k], "trade_date": [k],
                             "verify_state": [va.Q + "THIEU_BANG_CHUNG"], "in_verified_chain": [False]})
        monkeypatch.setattr(va, "verify_events", lambda *a, **kw: rows)
        if max_weight is not None:
            monkeypatch.setitem(config.CFG["paper"], "risk_limits", dict(LIM, max_weight=max_weight))
    return between


def test_newly_quarantined_ticker_at_the_fill_reweighs_the_rest_like_the_decision_gate(tmp_path, monkeypatch):
    """G vào cửa sổ cách ly ở phiên khớp. Còn 4 mã thì mỗi mã 24,9% > 20%: cổng FAIL như lúc quyết định, không mua mã nào."""
    st, dec, trd, t1 = _two_sessions(tmp_path, monkeypatch, _quarantine_g(monkeypatch))
    _no_buy(st, dec, trd, t1, "loại G")
    assert "tỷ trọng 24.88%" in dec[dec.date == t1].models.item()


def test_newly_quarantined_ticker_at_the_fill_is_dropped_and_the_rest_fill(tmp_path, monkeypatch):
    st, dec, trd, t1 = _two_sessions(tmp_path, monkeypatch, _quarantine_g(monkeypatch, max_weight=0.3))
    assert sorted(trd[(trd.date == t1) & (trd.side == "BUY")].asset) == list("DEFH")
    assert trd[trd.side == "UNFILLED_RISK_GATE"].asset.tolist() == ["G"] and "G" not in st["positions"]
    row = dec[dec.date == t1]
    assert row.action.tolist() == ["RISK_GATE_BLOCK_BUY"] and row.targets.item() == "G" and "PASS" in row.models.item()


# ---------- 10. Hàng chờ sau phiên khớp: mã cổng từ chối không quay lại ----------

def _paper_days(root, monkeypatch, close_edit=None, state=None):
    """Sổ giấy trên kho 41 phiên (idx[0..40]); trả (idx, chạy phiên i, đọc state.json)."""
    monkeypatch.setattr(config, "ROOT", root)
    monkeypatch.setattr(paper, "ROOT", root)
    idx, tickers = _store(root, volume=1e6, n=41)
    close = pd.DataFrame({t: [10_000.0 + 100 * j + 10 * i for i in range(len(idx))] for j, t in enumerate(tickers)}, index=idx)
    if close_edit is not None:
        close_edit(close, idx)
    if state is not None:
        (root / "paper").mkdir(parents=True, exist_ok=True)
        (root / "paper" / "state.json").write_text(json.dumps(state), encoding="utf-8")
    reg = {"M": {"state": "ACTIVE", "backtest": {"ic_t": 3.0}}}

    def day(i):
        preds = pd.DataFrame([(idx[i], "M", t, float(k)) for k, t in enumerate(tickers)],
                             columns=["date", "model_id", "ticker", "score"])
        return paper.run(str(idx[i].date()), close, preds, reg, idx)[1]

    return idx, day, lambda: json.loads((root / "paper" / "state.json").read_text(encoding="utf-8"))


def _quarantine_from(monkeypatch, ticker, k, max_weight=0.3):
    """Từ lúc gọi: `ticker` có sự kiện cổ phiếu bị cách ly ở phiên k; max_weight 0,3 đủ cho mục tiêu còn 4 mã (24,9%)."""
    rows = pd.DataFrame({"ticker": [ticker], "type": ["stock_split"], "ex_date": [k], "trade_date": [k],
                         "verify_state": [va.Q + "THIEU_BANG_CHUNG"], "in_verified_chain": [False]})
    monkeypatch.setattr(va, "verify_events", lambda *a, **kw: rows)
    monkeypatch.setitem(config.CFG["paper"], "risk_limits", dict(LIM, max_weight=max_weight))


def test_refused_ticker_leaves_the_queue_while_a_limit_up_buy_retries(tmp_path, monkeypatch):
    """Phiên khớp idx[39]: G bị cách ly (cổng từ chối), H khóa trần. Hàng chờ còn H, không còn G; phiên sau mua H, không thử G."""
    def edit(close, idx):
        close.loc[idx[39]:, "H"] *= 1.07
    idx, day, state = _paper_days(tmp_path, monkeypatch, edit)
    assert day(38)["targets"] == "H;G;F;E;D"
    _quarantine_from(monkeypatch, "G", idx[39])
    day(39)
    t39 = _read(tmp_path, "trades.csv")
    assert sorted(t39[t39.side == "BUY"].asset) == list("DEF")
    assert t39[t39.side == "UNFILLED_RISK_GATE"].asset.tolist() == ["G"]
    assert t39[t39.side == "UNFILLED_LIMIT_UP"].asset.tolist() == ["H"]
    assert state()["pending"] == ["H", "F", "E", "D"]
    day(40)
    trd = _read(tmp_path, "trades.csv")
    assert trd[(trd.date == str(idx[40].date())) & (trd.side == "BUY")].asset.tolist() == ["H"]
    assert trd[trd.side == "UNFILLED_RISK_GATE"].asset.tolist() == ["G"] and "G" not in set(trd[trd.side == "BUY"].asset)
    assert state()["pending"] is None and sorted(state()["positions"]) == list("DEFH")


def test_refused_ticker_leaves_the_queue_while_a_limit_down_sell_retries(tmp_path, monkeypatch):
    """Đang giữ A (không thuộc mục tiêu). Phiên khớp idx[39]: A khóa sàn, G bị cách ly. Hàng chờ không còn G; phiên sau bán A."""
    def edit(close, idx):
        close.loc[idx[39]:, "A"] *= 0.93
    px_a = 10_000.0 + 10 * 38
    st0 = {"cash": 1e9 - 10_000 * px_a, "positions": {"A": 10_000}, "pending": None, "last_rebalance": None,
           "costs_paid": 0.0, "n_rebalance": 0}
    idx, day, state = _paper_days(tmp_path, monkeypatch, edit, st0)
    assert day(38)["targets"] == "H;G;F;E;D"
    _quarantine_from(monkeypatch, "G", idx[39])
    day(39)
    t39 = _read(tmp_path, "trades.csv")
    assert t39[t39.side == "UNFILLED_LIMIT_DOWN"].asset.tolist() == ["A"]
    assert t39[t39.side == "UNFILLED_RISK_GATE"].asset.tolist() == ["G"] and sorted(t39[t39.side == "BUY"].asset) == list("DEFH")
    assert state()["pending"] == ["H", "F", "E", "D"]
    day(40)
    trd = _read(tmp_path, "trades.csv")
    assert trd[(trd.date == str(idx[40].date())) & (trd.side == "SELL")].asset.tolist() == ["A"]
    assert trd[trd.side == "UNFILLED_RISK_GATE"].asset.tolist() == ["G"] and "G" not in set(trd[trd.side == "BUY"].asset)
    assert state()["pending"] is None and sorted(state()["positions"]) == list("DEFH")


def test_quarantined_ticker_is_dropped_at_the_decision_and_never_queued(tmp_path, monkeypatch):
    """G bị cách ly ngay lúc ra quyết định (chưa giữ): mục tiêu bỏ G, nên phiên khớp không phải từ chối G lần nữa."""
    idx, day, state = _paper_days(tmp_path, monkeypatch)
    _quarantine_from(monkeypatch, "G", idx[37])
    d = day(38)
    assert d["action"] == "REBALANCE" and d["targets"] == "H;F;E;D" and "loại G" in d["models"]
    assert state()["pending"] == ["H", "F", "E", "D"]
    day(39)
    trd = _read(tmp_path, "trades.csv")
    assert sorted(trd[trd.side == "BUY"].asset) == list("DEFH") and "UNFILLED_RISK_GATE" not in set(trd.side)


# ---------- 11. Cổng không ép bán vị thế đang giữ ----------

def _held_h(px_h=10_000.0 + 700 + 10 * 38):
    return {"cash": 1e9 - 10_000 * px_h, "positions": {"H": 10_000}, "pending": None, "last_rebalance": None,
            "costs_paid": 0.0, "n_rebalance": 0}


def test_fail_at_decision_keeps_held_targets_and_sells_nothing_because_of_the_gate(tmp_path, monkeypatch):
    """Đang giữ H (thuộc mục tiêu mô hình) và H bị cách ly. Còn 4 mã mới mỗi mã 24,9% > 20%: FAIL. Mục tiêu còn H; H không bị bán."""
    idx, day, state = _paper_days(tmp_path, monkeypatch, state=_held_h())
    k = idx[37]
    rows = pd.DataFrame({"ticker": ["H"], "type": ["stock_split"], "ex_date": [k], "trade_date": [k],
                         "verify_state": [va.Q + "THIEU_BANG_CHUNG"], "in_verified_chain": [False]})
    monkeypatch.setattr(va, "verify_events", lambda *a, **kw: rows)
    d = day(38)
    assert d["action"] == "RISK_GATE_FAIL" and d["targets"] == "H" and "loại H" in d["models"]
    assert state()["positions"] == {"H": 10_000} and state()["pending"] is None


def test_quarantined_held_ticker_stays_held_while_the_rest_are_bought(tmp_path, monkeypatch):
    idx, day, state = _paper_days(tmp_path, monkeypatch, state=_held_h())
    _quarantine_from(monkeypatch, "H", idx[37])
    d = day(38)
    assert d["action"] == "REBALANCE" and d["targets"] == "H;G;F;E;D" and "loại H" in d["models"]
    day(39)
    trd = _read(tmp_path, "trades.csv")
    assert sorted(trd[trd.side == "BUY"].asset) == list("DEFG") and trd[trd.side == "SELL"].empty
    assert state()["positions"]["H"] == 10_000


# ---------- 12. Danh mục tồn dư ngoài mục tiêu (vòng chấm L-09, BLOCKER 2) ----------

RESID = "(vị thế còn giữ ngoài mục tiêu)"


def test_residual_holding_over_the_weight_limit_fails():
    g = _check(book=_book(positions={"Z": 25_000}), market=_market(price={**_market()["price"], "Z": 10_000.0},
                                                                     adv_value={**_market()["adv_value"], "Z": 5e10}))
    assert g["verdict"] == "FAIL" and any(r.startswith(f"Z {RESID}: tỷ trọng 25.00%") for r in g["reasons"])
    g = _check(book=_book(positions={"Z": 15_000}), market=_market(price={**_market()["price"], "Z": 10_000.0},
                                                                     adv_value={**_market()["adv_value"], "Z": 5e10}))
    assert g["verdict"] == "PASS"


@pytest.mark.parametrize("adv,why", [(1e8, "cần 15.0 phiên để thoát vị thế"), (None, "thiếu giá trị giao dịch bình quân")])
def test_residual_holding_must_be_liquid_and_measurable(adv, why):
    m = _market(price={**_market()["price"], "Z": 10_000.0})
    m["adv_value"] = {**m["adv_value"], "Z": adv}
    g = _check(book=_book(positions={"Z": 15_000}), market=m)          # 150 triệu, 7,5% NAV
    assert g["verdict"] == "FAIL" and any(r.startswith(f"Z {RESID}: {why}") for r in g["reasons"])


def test_residual_holding_without_a_price_fails():
    g = _check(book=_book(positions={"Z": 15_000}))
    assert g["verdict"] == "FAIL" and f"Z {RESID}: không có giá để định giá vị thế đang giữ" in g["reasons"]


def test_held_quarantined_ticker_counts_as_residual():
    m = _market(quarantined={"C": "sự kiện bị cách ly"})
    g = _check(T5 + ["F"], book=_book(positions={"C": 25_000}), market=m)
    assert g["excluded"] == {"C": "sự kiện bị cách ly"} and g["verdict"] == "FAIL"
    assert any(r.startswith(f"C {RESID}: tỷ trọng 25.00%") for r in g["reasons"])


PX_A38 = 10_000.0 + 10 * 38                                      # giá A ở idx[38] trong _paper_days


def _holding_a(shares):
    return {"cash": 1e9 - shares * PX_A38, "positions": {"A": shares}, "pending": None, "last_rebalance": None,
            "costs_paid": 0.0, "n_rebalance": 0}


def _a_limit_down(close, idx):
    close.loc[idx[39]:, "A"] *= 0.93


def test_limit_down_sell_of_an_overweight_holding_blocks_every_buy(tmp_path, monkeypatch):
    """Đang giữ A khoảng 30% NAV, không thuộc mục tiêu. Phiên khớp idx[39]: A khóa sàn nên không bán được; A còn khoảng 28,6%
    NAV > 20%: cổng FAIL, không mua mã nào. Phiên sau bán A; không mua lại các mã đã bị từ chối."""
    idx, day, state = _paper_days(tmp_path, monkeypatch, _a_limit_down, _holding_a(29_000))
    assert day(38)["targets"] == "H;G;F;E;D"
    day(39)
    trd, dec = _read(tmp_path, "trades.csv"), _read(tmp_path, "decisions.csv")
    t39 = trd[trd.date == str(idx[39].date())]
    assert t39[t39.side == "UNFILLED_LIMIT_DOWN"].asset.tolist() == ["A"] and "BUY" not in set(t39.side)
    assert sorted(t39[t39.side == "UNFILLED_RISK_GATE"].asset) == list("DEFGH")
    row = dec[dec.date == str(idx[39].date())]
    assert row.action.tolist() == ["RISK_GATE_BLOCK_BUY"] and f"A {RESID}: tỷ trọng 28." in row.models.item()
    assert state()["pending"] == []
    day(40)
    trd = _read(tmp_path, "trades.csv")
    assert trd[trd.date == str(idx[40].date())].side.tolist() == ["SELL"] and "BUY" not in set(trd.side)
    assert state()["positions"] == {} and state()["pending"] is None


def test_limit_down_sell_of_a_small_holding_does_not_block_buys(tmp_path, monkeypatch):
    idx, day, state = _paper_days(tmp_path, monkeypatch, _a_limit_down, _holding_a(9_000))      # khoảng 9% NAV
    day(38)
    day(39)
    trd = _read(tmp_path, "trades.csv")
    assert trd[trd.side == "UNFILLED_LIMIT_DOWN"].asset.tolist() == ["A"] and "UNFILLED_RISK_GATE" not in set(trd.side)
    assert len(trd[trd.side == "BUY"]) >= 4


# ---------- 13. FAIL lúc ra quyết định giữ nguyên MỌI vị thế (vòng chấm L-09, BLOCKER 1) ----------

def test_fail_at_decision_keeps_holdings_outside_the_new_target_and_trades_nothing(tmp_path, monkeypatch):
    """Đang giữ A, không thuộc mục tiêu mới H;G;F;E;D. G bị cách ly nên còn 4 mã mới, mỗi mã 24,9% > 20%: FAIL. Mục tiêu là
    toàn bộ vị thế đang giữ; phiên sau không có giao dịch nào, A vẫn còn."""
    idx, day, state = _paper_days(tmp_path, monkeypatch, state=_holding_a(9_000))
    rows = pd.DataFrame({"ticker": ["G"], "type": ["stock_split"], "ex_date": [idx[37]], "trade_date": [idx[37]],
                         "verify_state": [va.Q + "THIEU_BANG_CHUNG"], "in_verified_chain": [False]})
    monkeypatch.setattr(va, "verify_events", lambda *a, **kw: rows)
    d = day(38)
    assert d["action"] == "RISK_GATE_FAIL" and d["targets"] == "A" and "tỷ trọng 24.88%" in d["models"]
    assert state()["pending"] is None
    day(39)
    assert not (tmp_path / "paper" / "trades.csv").exists() and state()["positions"] == {"A": 9_000}


def test_rebalance_still_sells_an_overweight_holding_the_model_dropped(tmp_path, monkeypatch):
    """Đang giữ A khoảng 30% NAV, không thuộc mục tiêu mới. Cổng lúc ra quyết định chỉ xét vị thế sẽ còn giữ sau kỳ, nên PASS:
    kỳ tái cơ cấu bán A (giảm rủi ro), không bị FAIL giữ A lại."""
    idx, day, state = _paper_days(tmp_path, monkeypatch, state=_holding_a(29_000))
    d = day(38)
    assert d["action"] == "REBALANCE" and d["targets"] == "H;G;F;E;D" and "cổng rủi ro" not in d["models"]
    day(39)
    trd = _read(tmp_path, "trades.csv")
    assert trd[trd.side == "SELL"].asset.tolist() == ["A"] and "A" not in state()["positions"]


def test_tests_do_not_touch_the_repo():
    assert subprocess.check_output(["git", "status", "--porcelain", "--", "paper", "state"], cwd=REPO) == b""
