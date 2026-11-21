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
       "quarantine_window_days": 45}
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
    """market_snapshot chỉ loại mã có sự kiện CACH_LY_* có ngày giao dịch trong quarantine_window_days ngày tới as_of."""
    _store(tmp_path, volume=1e6)
    as_of = pd.Timestamp("2026-03-02")
    rows = pd.DataFrame({"ticker": ["A", "B", "C", "D"], "type": ["stock_split"] * 4,
                         "trade_date": pd.to_datetime(["2026-02-20", "2026-01-05", "2026-02-25", "2026-03-03"]),
                         "verify_state": [va.Q + "THIEU_BANG_CHUNG", va.Q + "THIEU_BANG_CHUNG", va.OK, va.Q + "LECH_NGAY"]})
    monkeypatch.setattr(va, "verify_events", lambda *a, **k: rows)
    snap = rg.market_snapshot(as_of, ["A", "B", "C", "D"], LIM, root=tmp_path, frozen=False, nav_now=NAV)
    assert list(snap["quarantined"]) == ["A"], snap
    assert set(snap["adv_value"]) == {"A", "B", "C", "D"} and snap["nav_history"] == [NAV]


def test_snapshot_failure_leaves_inputs_empty_so_check_fails(tmp_path, monkeypatch):
    _store(tmp_path, volume=1e6)

    def boom(*a, **k):
        raise ValueError("manifest hỏng")
    monkeypatch.setattr(va, "verify_events", boom)
    snap = rg.market_snapshot(pd.Timestamp("2026-03-02"), T5, LIM, root=tmp_path, frozen=False, nav_now=NAV)
    assert snap["quarantined"] is None and snap["errors"]
    assert rg.check(T5, _book(), {**snap, "price": _market()["price"]}, LIM)["verdict"] == "FAIL"


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


def _run_paper(root, monkeypatch, volume, nav_hist=None, limits="default"):
    monkeypatch.setattr(config, "ROOT", root)
    monkeypatch.setattr(paper, "ROOT", root)
    if limits != "default":
        monkeypatch.setitem(config.CFG["paper"], "risk_limits", limits)
    idx, tickers = _store(root, volume)
    if nav_hist is not None:
        (root / "paper").mkdir(parents=True, exist_ok=True)
        pd.DataFrame({"date": "2026-01-05", "nav": nav_hist, "cash": nav_hist, "n_positions": 0}).to_csv(
            root / "paper" / "nav.csv", index=False)
    close = pd.DataFrame({t: [10_000.0 + 100 * j + 10 * i for i in range(len(idx))] for j, t in enumerate(tickers)}, index=idx)
    reg = {"M": {"state": "ACTIVE", "backtest": {"ic_t": 3.0}}}
    as_of = idx[-1]
    preds = pd.DataFrame([(as_of, "M", t, float(k)) for k, t in enumerate(tickers)],
                         columns=["date", "model_id", "ticker", "score"])
    nav, decision = paper.run(str(as_of.date()), close, preds, reg, idx)
    state = json.loads((root / "paper" / "state.json").read_text(encoding="utf-8"))
    return decision, state, (root / "paper" / "decisions.csv").read_text(encoding="utf-8")


def test_paper_output_unchanged_when_every_condition_passes(tmp_path, monkeypatch):
    """Mọi điều kiện đạt: quyết định, sổ và tệp đầu ra trùng từng ký tự với lúc cổng được thay bằng 'luôn PASS'."""
    d1, s1, f1 = _run_paper(tmp_path / "co_cong", monkeypatch, volume=1e6)
    assert d1["action"] == "REBALANCE" and d1["targets"] == "H;G;F;E;D" and "cổng rủi ro" not in d1["models"]
    monkeypatch.setattr(rg, "check", lambda targets, *a, **k: {"verdict": "PASS", "reasons": [], "targets": list(targets),
                                                                "excluded": {}, "cash_wait_owner": False})
    d2, s2, f2 = _run_paper(tmp_path / "khong_cong", monkeypatch, volume=1e6)
    assert (d1, s1, f1) == (d2, s2, f2)


def test_paper_fail_opens_no_new_position(tmp_path, monkeypatch):
    d, s, _ = _run_paper(tmp_path, monkeypatch, volume=1.0)
    assert d["action"] == "RISK_GATE_FAIL" and d["targets"] == "" and "phiên để thoát vị thế" in d["models"]
    assert s["pending"] is None and s["positions"] == {}


def test_paper_drawdown_goes_to_cash_and_waits_for_owner(tmp_path, monkeypatch):
    d, s, _ = _run_paper(tmp_path, monkeypatch, volume=1e6, nav_hist=[1.2e9])
    assert d["action"] == "RISK_CASH_WAIT_OWNER" and d["targets"] == "" and "chờ Owner" in d["models"]
    assert s["pending"] is None


def test_paper_fails_closed_without_limits(tmp_path, monkeypatch):
    d, s, _ = _run_paper(tmp_path, monkeypatch, volume=1e6, limits=None)
    assert d["action"] == "RISK_GATE_FAIL" and "risk_limits" in d["models"] and s["pending"] is None


def test_tests_do_not_touch_the_repo():
    assert subprocess.check_output(["git", "status", "--porcelain", "--", "paper", "state"], cwd=REPO) == b""
