"""LỆNH R1 (QĐ-5, ADR-0016): cổng rủi ro bằng mã của sổ giấy. Không mạng. Không ghi kho (ROOT trỏ vào thư mục tạm)."""
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
LIM = {"max_weight": 0.20, "max_participation": 0.10, "max_exit_days": 3, "max_drawdown": 0.15, "adv_sessions": 20,
       "quarantine_sessions_before": 21, "quarantine_sessions_after": 120}
NAV = 1_000_000_000.0
T5 = ["A", "B", "C", "D", "E"]


def _market(**over):
    m = {"frozen": False, "price": {t: 10_000.0 for t in T5 + ["F"]}, "adv_value": {t: 5e10 for t in T5 + ["F"]},
         "nav_history": [NAV], "quarantined": {}}
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


# ---------- 3. Sụt giảm NAV từ đỉnh ----------

def test_drawdown_below_threshold_passes_and_at_threshold_goes_to_cash():
    assert _check(market=_market(nav_history=[NAV / 0.8501]))["verdict"] == "PASS"     # sụt 14,99%
    g = _check(market=_market(nav_history=[NAV / 0.85, NAV]))                          # sụt đúng 15%
    assert g["verdict"] == "FAIL" and g["cash_wait_owner"] and g["targets"] == []
    assert "chờ Owner" in g["reasons"][0]


def test_missing_nav_history_fails():
    g = _check(market=_market(nav_history=None))
    assert g["verdict"] == "FAIL" and "lịch sử NAV" in g["reasons"][0]


# ---------- 4. Mã có sự kiện bị cách ly ----------

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
    snap = rg.market_snapshot(as_of, list("ABCDE"), lim, root=tmp_path, frozen=False, nav_history=[NAV])
    # A: 3 phiên sau k (≤ 5) → loại. B: 9 phiên sau → không. C: đã vào chuỗi → không.
    # D: k = 2026-03-03, 2 phiên sau phiên cuối → t ở 2 phiên trước k (≤ 2) → loại. E: 4 phiên trước k → không.
    assert sorted(snap["quarantined"]) == ["A", "D"], snap
    assert "3 phiên sau" in snap["quarantined"]["A"] and "2 phiên trước" in snap["quarantined"]["D"]
    assert set(snap["adv_value"]) == set("ABCDE") and snap["nav_history"] == [NAV]


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
    snap = rg.market_snapshot(pd.Timestamp("2026-03-02"), T5, LIM, root=tmp_path, frozen=False, nav_history=[NAV])
    assert snap["quarantined"] is None and snap["errors"] and snap["adv_value"] == {}
    g = rg.check(T5, _book(), {**snap, "price": _market()["price"]}, LIM)
    assert g["verdict"] == "FAIL" and "manifest hỏng" in g["reasons"][0]


# ---------- 5. Dữ liệu đóng băng ----------

def test_frozen_data_fails_and_missing_flag_counts_as_frozen():
    assert _check(market=_market(frozen=True))["verdict"] == "FAIL"
    m = _market()
    del m["frozen"]
    assert _check(market=m)["verdict"] == "FAIL"


# ---------- 6. Giới hạn thiếu hoặc còn TODO ----------

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


# ---------- 7. Sổ giấy: gọi cổng trước khi ghi quyết định ----------

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


def _run_paper(root, monkeypatch, volume, nav_hist=None, limits="default", frozen=False, state=None):
    monkeypatch.setattr(config, "ROOT", root)
    monkeypatch.setattr(paper, "ROOT", root)
    if limits != "default":
        monkeypatch.setitem(config.CFG["paper"], "risk_limits", limits)
    idx, tickers = _store(root, volume)
    if nav_hist is not None:
        (root / "paper").mkdir(parents=True, exist_ok=True)
        pd.DataFrame({"date": "2026-01-05", "nav": nav_hist, "cash": nav_hist, "n_positions": 0}).to_csv(
            root / "paper" / "nav.csv", index=False)
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
                                                                "excluded": {}, "cash_wait_owner": False})
    monkeypatch.setattr(rg, "breach", lambda *a, **k: None)             # tắt cả khóa sụt giảm mỗi phiên
    d2, s2, f2 = _run_paper(tmp_path / "khong_cong", monkeypatch, volume=1e6)
    assert (d1, s1, f1) == (d2, s2, f2)
    assert "risk_lock" not in s1 and "risk_lock_released" not in s1


def test_paper_fail_opens_no_new_position(tmp_path, monkeypatch):
    d, s, _ = _run_paper(tmp_path, monkeypatch, volume=1.0)
    assert d["action"] == "RISK_GATE_FAIL" and d["targets"] == "" and "phiên để thoát vị thế" in d["models"]
    assert s["pending"] is None and s["positions"] == {}


def test_paper_drawdown_goes_to_cash_and_waits_for_owner(tmp_path, monkeypatch):
    d, s, _ = _run_paper(tmp_path, monkeypatch, volume=1e6, nav_hist=[1.2e9])
    assert d["action"] == "RISK_CASH_WAIT_OWNER" and d["targets"] == "" and "chờ Owner" in d["models"]
    assert s["pending"] is None and s["risk_lock"]["since"] == "2026-02-27" and "16.67%" in s["risk_lock"]["reason"]


def test_paper_fails_closed_without_limits(tmp_path, monkeypatch):
    d, s, _ = _run_paper(tmp_path, monkeypatch, volume=1e6, limits=None)
    assert d["action"] == "RISK_GATE_FAIL" and "risk_limits" in d["models"] and s["pending"] is None


# ---------- 8. Vòng chấm 1 (L-09), lỗi 1–2: khóa sụt giảm đo MỖI phiên và giữ tới khi Owner gỡ ----------

DD_DATES = pd.bdate_range("2026-01-05", periods=60)
DD_TICKERS = list("ABCDEFGH")


def _dd_close():
    """Giá điều chỉnh: phẳng tới phiên 27; phiên 28–30 cả rổ −6%/phiên; phiên 31 D −7% (khóa sàn), mã khác +6%; phiên 32
    D +6,5%; sau đó phẳng."""
    r = np.zeros((len(DD_DATES), len(DD_TICKERS)))
    r[28:31, :] = -0.06
    r[31, :] = 0.06
    r[31, DD_TICKERS.index("D")] = -0.07
    r[32, DD_TICKERS.index("D")] = 0.065
    base = np.array([10_000.0 + 1_000 * j for j in range(len(DD_TICKERS))])
    return pd.DataFrame(base * np.cumprod(1 + r, axis=0), index=DD_DATES, columns=DD_TICKERS)


def _dd_session(root, close, i):
    as_of = DD_DATES[i]
    preds = pd.DataFrame([(as_of, "M", t, float(k)) for k, t in enumerate(DD_TICKERS)],
                         columns=["date", "model_id", "ticker", "score"])
    return paper.run(str(as_of.date()), close, preds, {"M": {"state": "ACTIVE", "backtest": {"ic_t": 3.0}}}, DD_DATES)


def _read(root, name):
    return pd.read_csv(root / "paper" / name, dtype={"date": str})


def test_drawdown_lock_trips_between_rebalances_and_holds_until_owner_releases(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "ROOT", tmp_path)
    monkeypatch.setattr(paper, "ROOT", tmp_path)
    monkeypatch.setitem(config.CFG["paper"], "rebalance_days", 5)
    monkeypatch.setitem(config.CFG["paper"], "risk_lock_release", None)
    close = _dd_close()
    rows = [{"date": d.date().isoformat(), "ticker": t, "open": close.at[d, t], "high": close.at[d, t], "low": close.at[d, t],
             "close": close.at[d, t], "volume": 1e9, "observed_at": "2026-01-01", "source": "test"}
            for d in DD_DATES for t in DD_TICKERS]
    store = tmp_path / config.CFG["data"]["store_dir"] / "2026-01.csv"
    store.parent.mkdir(parents=True)
    pd.DataFrame(rows).to_csv(store, index=False)
    day = [str(d.date()) for d in DD_DATES]
    for i in range(25, 45):
        _dd_session(tmp_path, close, i)
    dec, trd, nav = _read(tmp_path, "decisions.csv"), _read(tmp_path, "trades.csv"), _read(tmp_path, "nav.csv")
    dd = 1 - nav.nav / nav.nav.cummax().clip(lower=1e9)
    # Dữ liệu dựng đúng kịch bản: chạm 15% ở phiên 30, giữa hai kỳ (mua phiên 26, kỳ kế ở phiên 31).
    assert dd[nav.date == day[29]].item() < 0.15 <= dd[nav.date == day[30]].item()
    assert dec.date.tolist()[:2] == [day[25], day[30]] and dec.action.tolist()[:2] == ["REBALANCE", "RISK_CASH_WAIT_OWNER"]
    st = json.loads((tmp_path / "paper" / "state.json").read_text(encoding="utf-8"))
    assert st["risk_lock"]["since"] == day[30] and "≥ ngưỡng 15.00%" in st["risk_lock"]["reason"]
    # Phiên 31: bán hết trừ D khóa sàn. NAV hồi lên dưới ngưỡng sụt giảm trong khi chưa thoát xong. Phiên 32: bán D.
    t31 = trd[trd.date == day[31]]
    assert sorted(t31[t31.side == "SELL"].asset) == ["E", "F", "G", "H"]
    assert t31[t31.side == "UNFILLED_LIMIT_DOWN"].asset.tolist() == ["D"]
    assert dd[nav.date == day[31]].item() < 0.15
    assert trd[(trd.date == day[32])].side.tolist() == ["SELL"] and trd[(trd.date == day[32])].asset.tolist() == ["D"]
    # Qua nhiều kỳ: không mua lại, mỗi kỳ chỉ ghi RISK_CASH_WAIT_OWNER.
    after = dec[dec.date > day[30]]
    assert len(after) >= 2 and set(after.action) == {"RISK_CASH_WAIT_OWNER"} and (after.targets.isna()).all()
    assert trd[(trd.date > day[30]) & (trd.side == "BUY")].empty
    assert st["positions"] == {} and st["pending"] is None
    # Giá trị gỡ sai (không phải ngày bắt đầu khóa) không gỡ được khóa.
    monkeypatch.setitem(config.CFG["paper"], "risk_lock_release", day[29])
    for i in range(45, 50):
        _dd_session(tmp_path, close, i)
    st = json.loads((tmp_path / "paper" / "state.json").read_text(encoding="utf-8"))
    assert st["risk_lock"]["since"] == day[30] and "RISK_LOCK_RELEASED_BY_OWNER" not in set(_read(tmp_path, "decisions.csv").action)
    # Owner ghi đúng ngày (YAML không nháy cho ra datetime.date): gỡ ở phiên 50, đỉnh tính lại, kỳ sau được mở vị thế.
    monkeypatch.setitem(config.CFG["paper"], "risk_lock_release", DD_DATES[30].date())
    for i in range(50, 60):
        _dd_session(tmp_path, close, i)
    dec, trd = _read(tmp_path, "decisions.csv"), _read(tmp_path, "trades.csv")
    st = json.loads((tmp_path / "paper" / "state.json").read_text(encoding="utf-8"))
    assert "risk_lock" not in st and st["risk_lock_released"] == {"since": day[30], "on": day[50]}
    rel = dec[dec.action == "RISK_LOCK_RELEASED_BY_OWNER"]
    assert rel.date.tolist() == [day[50]]
    later = dec[dec.date > day[50]]
    assert later.action.tolist()[0] == "REBALANCE" and not trd[(trd.date > day[50]) & (trd.side == "BUY")].empty


def test_owner_release_resets_the_peak_so_the_lock_does_not_trip_again_at_once(tmp_path, monkeypatch):
    """NAV sau khi thoát vẫn thấp hơn đỉnh cũ quá 15%: gỡ khóa mà không tính lại đỉnh thì khóa lại ngay ở phiên gỡ."""
    monkeypatch.setitem(config.CFG["paper"], "risk_lock_release", "2026-02-10")
    st = {"cash": 1e9, "positions": {}, "pending": None, "last_rebalance": "2026-02-26", "costs_paid": 0.0,
          "n_rebalance": 0, "last_date": "2026-02-26", "risk_lock": {"since": "2026-02-10", "reason": "thử"}}
    (tmp_path / "paper").mkdir(parents=True)
    pd.DataFrame({"date": ["2026-02-09", "2026-02-26"], "nav": [1.2e9, 1e9], "cash": [0, 1e9], "n_positions": [5, 0]}).to_csv(
        tmp_path / "paper" / "nav.csv", index=False)
    d, s, text = _run_paper(tmp_path, monkeypatch, volume=1e6, state=st)
    assert "risk_lock" not in s and s["risk_lock_released"] == {"since": "2026-02-10", "on": "2026-02-27"}
    assert d is None and text.splitlines()[1].split(",")[:2] == ["2026-02-27", "RISK_LOCK_RELEASED_BY_OWNER"]
    assert len(text.splitlines()) == 2


def test_drawdown_lock_also_trips_on_a_frozen_session(tmp_path, monkeypatch):
    d, s, _ = _run_paper(tmp_path, monkeypatch, volume=1e6, nav_hist=[1.2e9], frozen=True)
    assert d["action"] == "RISK_CASH_WAIT_OWNER" and s["risk_lock"]["since"] == "2026-02-27"


def test_no_lock_and_no_state_change_below_the_threshold(tmp_path, monkeypatch):
    d, s, _ = _run_paper(tmp_path, monkeypatch, volume=1e6, nav_hist=[1e9 / 0.8501])     # sụt 14,99%
    assert d["action"] == "REBALANCE" and "risk_lock" not in s



def test_locked_book_never_fills_a_buy_left_in_pending(tmp_path, monkeypatch):
    """Khóa còn đó mà pending còn mã mua (ví dụ trạng thái ghi từ trước): bước khớp lệnh vẫn coi mục tiêu là rỗng. Năm mã
    mỗi mã 19,9% nên cổng ở phiên khớp sẽ PASS: chỉ khóa chặn lệnh mua."""
    st = {"cash": 1e9, "positions": {}, "pending": list("HGFED"), "last_rebalance": "2026-02-26", "costs_paid": 0.0,
          "n_rebalance": 0, "last_date": "2026-02-26", "risk_lock": {"since": "2026-02-20", "reason": "thử"}}
    (tmp_path / "paper").mkdir(parents=True)
    pd.DataFrame({"date": ["2026-02-26"], "nav": [1e9], "cash": [1e9], "n_positions": [0]}).to_csv(
        tmp_path / "paper" / "nav.csv", index=False)
    d, s, _ = _run_paper(tmp_path, monkeypatch, volume=1e6, state=st)
    assert s["positions"] == {} and s["pending"] is None and s["risk_lock"]["since"] == "2026-02-20"
    assert d is None                                            # không tới kỳ, không mới khóa: không ghi quyết định
    assert not (tmp_path / "paper" / "trades.csv").exists() or "BUY" not in (tmp_path / "paper" / "trades.csv").read_text()

# ---------- 9. Lỗi 3: lịch sử NAV — khởi tạo hợp lệ, mất lịch sử, dòng tương lai, tệp hỏng ----------

def _nav_csv(root, rows):
    (root / "paper").mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=["date", "nav", "cash", "n_positions"]).to_csv(root / "paper" / "nav.csv", index=False)


def test_nav_history_initial_book_starts_from_initial_cash(tmp_path):
    assert rg.read_nav_history(tmp_path, "2026-03-02", 9e8, last_date=None, initial_cash=1e9) == ([1e9, 9e8], None)
    _nav_csv(tmp_path, [("2026-03-02", 9e8, 9e8, 0)])          # chỉ có dòng của chính as_of: vẫn là phiên đầu
    assert rg.read_nav_history(tmp_path, "2026-03-02", 9e8, last_date=None, initial_cash=1e9) == ([1e9, 9e8], None)
    assert rg.breach([1e9, 8.5e8], 8.5e8, LIM) and rg.breach([1e9, 8.51e8], 8.51e8, LIM) is None
    # Chạm ngưỡng tính cả sai số dấu phẩy động (EPS = 1e-12), không hơn.
    assert rg.breach([1e9], 1e9 * (0.85 + 1e-13), LIM) and rg.breach([1e9], 1e9 * (0.85 + 1e-11), LIM) is None


@pytest.mark.parametrize("rows", [None, [("2026-02-25", 1e9, 1e9, 0), ("2026-02-26", 1e9, 1e9, 0)]])
def test_nav_history_lost_when_the_last_processed_session_has_no_row(tmp_path, rows):
    if rows is not None:
        _nav_csv(tmp_path, rows)
    h, why = rg.read_nav_history(tmp_path, "2026-03-02", 9e8, last_date="2026-02-27", initial_cash=1e9)
    assert h is None and "mất lịch sử NAV" in why and "2026-02-27" in why
    g = _check(market=_market(nav_history=h, nav_history_problem=why))
    assert g["verdict"] == "FAIL" and "mất lịch sử NAV" in g["reasons"][0] and not g["cash_wait_owner"]


def test_lost_nav_history_still_gives_a_lower_bound_for_breach_detection(tmp_path):
    _nav_csv(tmp_path, [("2026-02-20", 1.2e9, 0, 5), ("2026-02-25", 1e9, 1e9, 0)])
    assert rg.read_nav_history(tmp_path, "2026-03-02", 1e9, last_date="2026-02-27", initial_cash=1e9)[0] is None
    h, why = rg.read_nav_history(tmp_path, "2026-03-02", 1e9, last_date="2026-02-27", initial_cash=1e9, lower_bound=True)
    assert h == [1.2e9, 1e9, 1e9] and "mất lịch sử NAV" in why and rg.breach(h, 1e9, LIM)
    (tmp_path / "paper" / "nav.csv").unlink()                  # mất cả tệp: không thêm vốn ban đầu, không có gì để so
    h, why = rg.read_nav_history(tmp_path, "2026-03-02", 5e8, last_date="2026-02-27", initial_cash=1e9, lower_bound=True)
    assert h == [5e8] and "mất lịch sử NAV" in why
    (tmp_path / "paper" / "nav.csv").write_text("date,nav\n2026-02-20,abc\n", encoding="utf-8")
    assert rg.read_nav_history(tmp_path, "2026-03-02", 5e8, last_date=None, initial_cash=1e9, lower_bound=True)[0] is None


def test_paper_locks_on_a_breach_proven_by_the_rows_left_after_history_loss(tmp_path, monkeypatch):
    """Sổ đã chạy tới 2026-02-26 nhưng nav.csv chỉ còn dòng 1,2 tỷ (2026-01-05): mất lịch sử, cổng không PASS được; nhưng
    ngay dòng còn lại đã cho thấy sụt 16,67% ≥ 15%, nên khóa."""
    st = {"cash": 1e9, "positions": {}, "pending": None, "last_rebalance": None, "costs_paid": 0.0, "n_rebalance": 0,
          "last_date": "2026-02-26"}
    d, s, _ = _run_paper(tmp_path, monkeypatch, volume=1e6, nav_hist=[1.2e9], state=st)
    assert d["action"] == "RISK_CASH_WAIT_OWNER" and "16.67%" in s["risk_lock"]["reason"]


def test_nav_history_ignores_rows_after_as_of(tmp_path):
    _nav_csv(tmp_path, [("2026-02-26", 1e9, 1e9, 0), ("2026-02-27", 1e9, 1e9, 0), ("2026-03-02", 1.1e9, 0, 5),
                        ("2026-03-03", 2e9, 0, 5)])               # dòng của as_of (chạy lại) và dòng sau as_of
    h, why = rg.read_nav_history(tmp_path, "2026-03-02", 9e8, last_date="2026-03-03", initial_cash=1e9)
    assert (h, why) == ([1e9, 1e9, 9e8], None)
    assert rg.breach(h, 9e8, LIM) is None                       # nếu tính cả dòng 2e9 thì sụt 55% và khóa nhầm


def test_nav_history_since_owner_release_uses_rows_from_that_day(tmp_path):
    _nav_csv(tmp_path, [("2026-02-20", 2e9, 0, 5), ("2026-02-26", 1e9, 1e9, 0), ("2026-02-27", 1e9, 1e9, 0)])
    h, _ = rg.read_nav_history(tmp_path, "2026-03-02", 9e8, last_date="2026-02-27", initial_cash=1e9, since="2026-02-26")
    assert h == [1e9, 1e9, 9e8]
    h, _ = rg.read_nav_history(tmp_path, "2026-03-02", 9e8, last_date="2026-02-27", initial_cash=1e9, since="2026-03-02")
    assert h == [9e8]


@pytest.mark.parametrize("text", ["date,nav\n27/02/2026,1000\n", "date,nav\n2026-02-27,abc\n", "date,nav\n2026-02-27,\n",
                                  "date,nav\n2026-02-27,0\n", "date,nav\n2026-02-27,-5\n", "date,cash\n2026-02-27,1\n",
                                  "date,nav\n2026-02-27,inf\n"])
def test_nav_history_corrupt_file_fails(tmp_path, text):
    (tmp_path / "paper").mkdir()
    (tmp_path / "paper" / "nav.csv").write_text(text, encoding="utf-8")
    h, why = rg.read_nav_history(tmp_path, "2026-03-02", 9e8, last_date="2026-02-27", initial_cash=1e9)
    assert h is None and why


@pytest.mark.parametrize("cash", [None, 0, -1, float("nan"), True, "1e9"])
def test_nav_history_needs_a_valid_initial_cash(tmp_path, cash):
    h, why = rg.read_nav_history(tmp_path, "2026-03-02", 9e8, last_date=None, initial_cash=cash)
    assert h is None and "initial_cash" in why


@pytest.mark.parametrize("bad", [None, float("nan"), float("inf"), 0.0, -1.0, True, "1e9"])
def test_invalid_values_in_nav_history_fail_instead_of_being_dropped(bad):
    g = _check(market=_market(nav_history=[NAV * 2, bad]))      # bản trước bỏ qua giá trị hỏng rồi so với đỉnh còn lại
    assert g["verdict"] == "FAIL" and "không hợp lệ" in g["reasons"][0] and not g["cash_wait_owner"]


def test_paper_with_lost_nav_history_opens_no_position(tmp_path, monkeypatch):
    st = {"cash": 1e9, "positions": {}, "pending": None, "last_rebalance": None, "costs_paid": 0.0, "n_rebalance": 0,
          "last_date": "2026-02-26"}
    d, s, _ = _run_paper(tmp_path, monkeypatch, volume=1e6, state=st)
    assert d["action"] == "RISK_GATE_FAIL" and d["targets"] == "" and "mất lịch sử NAV" in d["models"]
    assert s["pending"] is None and s["positions"] == {} and "risk_lock" not in s


# ---------- 10. Lỗi 4: ADV đúng adv_sessions phiên cuối, thiếu thì FAIL, không lùi cửa sổ ----------

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
    snap = rg.market_snapshot(idx[-1], T5, LIM, root=tmp_path, frozen=False, nav_history=[NAV])
    assert snap["adv_value"] == {} and all(str(gone.date()) in snap["adv_problem"][t] for t in T5)
    (tmp_path / "data" / "trading_calendar.csv").unlink()        # không có lịch: dự phòng theo ngày của kho giá
    snap = rg.market_snapshot(idx[-1], T5, LIM, root=tmp_path, frozen=False, nav_history=[NAV])
    assert set(snap["adv_value"]) == set(T5)


def test_session_axis_adds_calendar_sessions_missing_from_prices():
    days = pd.bdate_range("2026-03-02", periods=5)
    cal = {d.date().isoformat(): 1 for d in pd.bdate_range("2026-03-02", periods=7)}
    axis = rg.session_axis(days.delete(2), cal, until=days[-1])
    assert list(axis) == list(days)
    assert list(rg.session_axis(days.delete(2), cal)) == list(days)
    assert len(rg.session_axis(days, cal, until=pd.Timestamp("2026-03-10"))) == 7


# ---------- 11. Lỗi 5: lịch HOSE có mà hỏng thì FAIL; không có thì dự phòng ----------

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
    snap = rg.market_snapshot(idx[t_pos], ["X", "Y"], LIM, root=tmp_path, frozen=False, nav_history=[NAV])
    assert ("X" in snap["quarantined"]) is hit and "Y" not in snap["quarantined"], snap["quarantined"]


@pytest.mark.parametrize("name", sorted(CORRUPT))
def test_corrupt_calendar_makes_the_snapshot_fail_instead_of_falling_back(tmp_path, monkeypatch, name):
    idx = _boundary_store(tmp_path)
    _calendar(tmp_path, "2026-01-01", "2026-12-31", holidays={idx[60].date().isoformat()}, mutate=CORRUPT[name][0])
    monkeypatch.setattr(va, "verify_events", lambda *a, **kw: _NO_EVENTS)
    snap = rg.market_snapshot(idx[131], ["X", "Y"], LIM, root=tmp_path, frozen=False, nav_history=[NAV])
    assert snap["quarantined"] is None and snap["adv_value"] == {} and "lịch phiên HOSE" in snap["errors"][0]
    g = rg.check(["X", "Y"], _book(), {**snap, "price": {"X": 1e4, "Y": 1e4}}, dict(LIM, max_weight=0.6))
    assert g["verdict"] == "FAIL" and "lịch phiên HOSE" in g["reasons"][0]


def test_config_has_no_owner_release_by_default():
    assert config.CFG["paper"]["risk_lock_release"] is None


# ---------- 12. Vòng chấm 2 (L-09), lỗi 1: lệnh mua chờ qua lại cổng ở phiên khớp ----------

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


def test_pending_buys_blocked_when_nav_history_is_lost_before_the_fill(tmp_path, monkeypatch):
    st, dec, trd, t1 = _two_sessions(tmp_path, monkeypatch, lambda r: (r / "paper" / "nav.csv").unlink())
    _no_buy(st, dec, trd, t1, "mất lịch sử NAV")
    assert "risk_lock" not in st                               # không đo được thì không mua, không tự bán hết


@pytest.mark.parametrize("bad", [None, {**LIM, "max_drawdown": "TODO"}, {**LIM, "adv_sessions": 0}])
def test_pending_buys_blocked_when_limits_break_before_the_fill(tmp_path, monkeypatch, bad):
    def between(r):
        monkeypatch.setitem(config.CFG["paper"], "risk_limits", bad)
    st, dec, trd, t1 = _two_sessions(tmp_path, monkeypatch, between)
    _no_buy(st, dec, trd, t1, "risk_limits" if bad is None else ("TODO" if bad.get("max_drawdown") == "TODO" else "adv_sessions"))


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


# ---------- 13. Vòng chấm 2, lỗi 2: sụt giảm ở các phiên giữa hai lần chạy (vòng học chạy hằng tuần) ----------

def _held_book(root, monkeypatch, a_path, last_i=34, as_i=38, pending=None, lock=None, nav_rows=None):
    """Sổ giữ 100.000 cổ phiếu A, không tiền mặt. Lần chạy trước ở idx[last_i]; lần này ở idx[as_i]; giá A theo a_path từ
    idx[last_i]. Các mã khác phẳng."""
    monkeypatch.setattr(config, "ROOT", root)
    monkeypatch.setattr(paper, "ROOT", root)
    idx, tickers = _store(root, volume=1e9)
    close = pd.DataFrame({t: 10_000.0 for t in tickers}, index=idx)
    close.loc[idx[last_i:last_i + len(a_path)], "A"] = a_path
    close.loc[idx[last_i + len(a_path):], "A"] = a_path[-1]
    (root / "paper").mkdir(parents=True, exist_ok=True)
    st = {"cash": 0.0, "positions": {"A": 100_000}, "pending": pending, "last_rebalance": str(idx[last_i].date()),
          "costs_paid": 0.0, "n_rebalance": 1, "last_date": str(idx[last_i].date())}
    if lock:
        st["risk_lock"] = lock
    (root / "paper" / "state.json").write_text(json.dumps(st), encoding="utf-8")
    rows = nav_rows or [(str(idx[last_i].date()), 100_000 * a_path[0])]
    pd.DataFrame(rows, columns=["date", "nav"]).assign(cash=0, n_positions=1).to_csv(root / "paper" / "nav.csv", index=False)
    preds = pd.DataFrame([(idx[as_i], "M", t, float(k)) for k, t in enumerate(tickers)],
                         columns=["date", "model_id", "ticker", "score"])
    _, decision = paper.run(str(idx[as_i].date()), close, preds, {"M": {"state": "ACTIVE", "backtest": {"ic_t": 3.0}}}, idx)
    st = json.loads((root / "paper" / "state.json").read_text(encoding="utf-8"))
    trd = _read(root, "trades.csv") if (root / "paper" / "trades.csv").exists() else pd.DataFrame(columns=["side", "asset"])
    return decision, st, trd, idx


DIP = [10_000.0, 9_350.0, 8_750.0, 8_200.0, 8_450.0, 8_700.0]          # giá A từ idx[34] (thứ Sáu) tới idx[39] (thứ Sáu)


def test_drawdown_between_two_weekly_runs_locks_before_any_fill(tmp_path, monkeypatch):
    """Lần chạy trước thứ Sáu 2026-02-20 (NAV 1 tỷ). Thứ Tư 2026-02-25 sụt 18%; thứ Sáu 2026-02-27 hồi còn sụt 13%."""
    d, st, trd, idx = _held_book(tmp_path, monkeypatch, DIP, as_i=39, pending=["B"])
    assert d["action"] == "RISK_CASH_WAIT_OWNER" and 1 - DIP[-1] / DIP[0] < 0.15
    assert "18.00% ≥ ngưỡng 15.00% ở phiên 2026-02-25, giữa hai lần chạy" in st["risk_lock"]["reason"]
    assert st["risk_lock"]["since"] == "2026-02-27"
    assert trd[trd.side == "BUY"].empty and trd[trd.side == "SELL"].asset.tolist() == ["A"] and st["positions"] == {}


def test_drawdown_between_runs_also_sells_when_nothing_was_pending(tmp_path, monkeypatch):
    d, st, trd, _ = _held_book(tmp_path, monkeypatch, DIP, as_i=39)
    assert d["action"] == "RISK_CASH_WAIT_OWNER" and trd.side.tolist() == ["SELL"] and st["positions"] == {}


def test_drawdown_between_runs_is_caught_even_when_the_last_nav_row_is_lost(tmp_path, monkeypatch):
    """nav.csv thiếu dòng của lần chạy trước 2026-02-20 nhưng còn dòng 1 tỷ ngày 2026-02-13: vẫn đủ chứng minh chạm ngưỡng."""
    d, st, trd, _ = _held_book(tmp_path, monkeypatch, DIP, as_i=39, nav_rows=[("2026-02-13", 1e9)])
    assert d["action"] == "RISK_CASH_WAIT_OWNER" and "ở phiên 2026-02-25, giữa hai lần chạy" in st["risk_lock"]["reason"]


def test_no_lock_when_no_session_between_runs_breaches(tmp_path, monkeypatch):
    d, st, trd, _ = _held_book(tmp_path, monkeypatch, [10_000.0, 9_350.0, 8_750.0, 8_700.0, 8_700.0, 8_700.0], as_i=39)
    assert "risk_lock" not in st and d is None and trd.empty                  # sâu nhất 13%: dưới ngưỡng


@pytest.mark.parametrize("path,where", [
    ([10_000.0, 10_600.0, 11_200.0, 10_450.0, 9_750.0, 9_500.0, 9_600.0], "ở phiên 2026-02-26, giữa hai lần chạy"),
    ([10_000.0, 10_600.0, 11_200.0, 10_450.0, 9_750.0, 9_700.0, 9_500.0], None)])
def test_peak_inside_the_gap_counts(tmp_path, monkeypatch, path, where):
    """Đỉnh 11.200 nằm giữa hai lần chạy, chỉ sụt 5% so với NAV đã ghi. Ca 1: sụt 15,2% so với đỉnh đó ở 2026-02-26 (giữa hai
    lần chạy). Ca 2: các phiên giữa chưa chạm; chính phiên chạy 2026-02-27 sụt 15,2% so với đỉnh giữa hai lần chạy."""
    d, st, trd, _ = _held_book(tmp_path, monkeypatch, path, last_i=33, as_i=39)
    assert d["action"] == "RISK_CASH_WAIT_OWNER" and "15.18% ≥ ngưỡng 15.00%" in st["risk_lock"]["reason"]
    assert (where in st["risk_lock"]["reason"]) if where else ("giữa hai lần chạy" not in st["risk_lock"]["reason"])


def test_sessions_before_an_owner_release_do_not_relock(tmp_path, monkeypatch):
    """Khóa từ 2026-02-13, vị thế còn giữ. Owner gỡ ở lần chạy 2026-02-27. Giữa hai lần chạy giá lên đỉnh rồi rơi 18%: các
    phiên đó trước phiên gỡ, nên không khóa lại."""
    monkeypatch.setitem(config.CFG["paper"], "risk_lock_release", "2026-02-13")
    path = [10_000.0, 10_600.0, 11_200.0, 10_450.0, 9_800.0, 9_200.0, 9_200.0, 9_200.0, 9_200.0, 9_200.0]
    d, st, trd, idx = _held_book(tmp_path, monkeypatch, path, last_i=30, as_i=39, pending=[],
                                 lock={"since": "2026-02-13", "reason": "thử"})
    assert "risk_lock" not in st and st["risk_lock_released"] == {"since": "2026-02-13", "on": "2026-02-27"}


def test_tests_do_not_touch_the_repo():
    assert subprocess.check_output(["git", "status", "--porcelain", "--", "paper", "state"], cwd=REPO) == b""
