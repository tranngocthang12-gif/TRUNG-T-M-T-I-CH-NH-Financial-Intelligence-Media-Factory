"""F1b (QĐ-11, QĐ-11a, QĐ-5a của ADR-0016): bộ chạy sổ FWD theo phiên, ba sổ đối chứng — engine/fwd.py.

Fixture tổng hợp: 7 mã (AAA…GGG) trong kho giá, lịch phiên HOSE giả phủ cả khoảng dữ liệu, rổ theo ngày (AAA…FFF từ đầu;
phiên R1: FFF rời rổ, GGG vào rổ), sự kiện quyền nhập tay. Đặc tả đăng ký trong research/trial_registry.jsonl của thư mục tạm;
để test ngắn, kỳ dài 3 phiên và có 2 kỳ (quyết định k = 0, 1, 2 ở D0, D0+3, D0+6; phép thử xong ở phiên khớp D0+7).
Robot chạy "từng ngày" bằng as_of tăng dần; hàm xác minh lượt chạy là bản giả (không mạng). config.ROOT và adjust.ROOT được vá.
"""
from __future__ import annotations

import ast
import hashlib
import json
import pathlib
import sys

import numpy as np
import pandas as pd
import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from engine import adjust, config, data, fwd  # noqa: E402

IDX = pd.bdate_range("2025-01-02", periods=300)            # 2025-01-02 … 2026-02-24
TICK = ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF", "GGG"]
D0, R1 = 285, 287                                           # D0 đăng ký 2026-02-05; FFF rời rổ, GGG vào rổ 2026-02-09
CAP = 10_000_000_000
C = config.CFG["costs"]
LOT = int(config.CFG["lot_size"])
S = [str(d.date()) for d in IDX]
SPEC = {"kind": "forward_test", "trial_id": "FWD-001", "d0": S[D0], "books": list(fwd.BOOKS), "capital": CAP,
        "period_sessions": 3, "periods": 2, "max_weight": 0.20, "buy_budget": 0.995, "drawdown_record": 0.15,
        "seal_deadline_local": "09:00", "s1": {"model": "fixture"}, "s2": {"model": "fixture"}, "train_input": "verified",
        "score_input": "verified", "protocol_sha256": "0" * 64, "adr_commit": "a" * 40}
OK = {"path": fwd.WORKFLOW, "branch": "main", "event": "schedule", "conclusion": "success"}


def _prices(seed=5):
    rng = np.random.default_rng(seed)
    r = rng.normal(0.0, 0.004, size=(len(IDX), len(TICK))).clip(-0.02, 0.02)       # không chạm biên độ
    return pd.DataFrame(20000.0 * np.cumprod(1 + r, axis=0), index=IDX, columns=TICK).round(-1)


def _ev(rows):
    return pd.DataFrame([{"cash_per_share": np.nan, "ratio": np.nan, "source": "manual (fixture)",
                          "source_status": "CAN_DOI_CHIEU", "note": "", **r} for r in rows], columns=adjust.EV_COLS)


def _write_events(home, rows=()):
    p = home / config.CFG["corporate_actions"]["manual"]
    p.parent.mkdir(parents=True, exist_ok=True)
    _ev(rows).to_csv(p, index=False)


def _home(tmp, close=None, vol=None, drop=(), events=(), calendar=True, unann=(), register=True, **spec):
    """Kho tạm. drop: các (ngày, mã) không có dòng giá (mã None = mọi mã); unann: ngày lịch ghi CHUA_CO_THONG_BAO."""
    home = pathlib.Path(tmp)
    close = _prices() if close is None else close
    vol = pd.DataFrame(1e6, index=IDX, columns=TICK) if vol is None else vol
    gone = {(pd.Timestamp(d), t) for d, t in drop}
    rows = [{"date": d.strftime("%Y-%m-%d"), "ticker": t, "open": close.at[d, t], "high": close.at[d, t],
             "low": close.at[d, t], "close": close.at[d, t], "volume": float(vol.at[d, t]), "observed_at": "2026-03-01",
             "source": "fixture"} for d in IDX for t in TICK if (d, t) not in gone and (d, None) not in gone]
    assert data.save_store(pd.DataFrame(rows, columns=data.COLS), root=home) > 0
    _write_events(home, events)
    p = home / config.CFG["corporate_actions"]["yahoo_cache"]
    p.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(columns=adjust.EV_COLS).to_csv(p, index=False)
    (home / "data").mkdir(parents=True, exist_ok=True)
    if calendar:
        un = {pd.Timestamp(d) for d in unann}
        lines = ["date,is_session,source_id"]
        for d in pd.date_range("2025-01-01", "2026-12-31", freq="D"):
            lines.append(f"{d.date()},0,WEEKEND" if d.weekday() >= 5 else
                         f"{d.date()},1,{data.UNANNOUNCED if d in un else 'HOSE_DEFAULT'}")
        (home / "data" / "trading_calendar.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    hist = "effective_date,ticker,action,source_id\n" + "".join(f"{S[0]},{t},ADD,fx-0\n" for t in TICK[:6])
    hist += f"{S[R1]},FFF,REMOVE,fx-1\n{S[R1]},GGG,ADD,fx-1\n"
    (home / data.VN30_HISTORY).write_text(hist, encoding="utf-8")
    reg = home / "research" / "trial_registry.jsonl"
    reg.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps({"kind": "legacy_anchor", "trial_id": "LEGACY-ANCHOR", "hash": "x", "prev_hash": "GENESIS"}),
             json.dumps({"trial_id": "T00001", "cycle_date": S[100], "hash": "y", "prev_hash": "x"})]
    if register:
        lines.append(json.dumps({**SPEC, **spec}))
    reg.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return home


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "ROOT", tmp_path)
    monkeypatch.setattr(adjust, "ROOT", tmp_path)
    return tmp_path


class Robot:
    """Robot chạy từng ngày. Mỗi lần chạy có mã lượt "i.1"; bản giả của API trả lượt hợp lệ kết thúc 18:30 giờ VN cùng ngày,
    trừ khi `runs` được sửa (lỗi API, trễ, workflow/nhánh/kết luận khác)."""

    def __init__(self, home, scorer=None):
        self.home, self.scorer, self.runs, self.calls = home, scorer, {}, []

    def verify(self, rid):
        self.calls.append(rid)
        x = self.runs[rid]
        if isinstance(x, Exception):
            raise x
        return x

    def day(self, i, now=None, **info):
        rid = f"{i}.1"
        self.runs[rid] = {**OK, "finished_at": f"{S[i]}T11:30:00Z", **info}
        return fwd.run(S[i], root=self.home, verify=self.verify, scorer=self.scorer, run_id=rid,
                       now=now or f"{S[i]}T11:00:00Z")

    def days(self, a, b):
        for i in range(a, b + 1):
            self.day(i)


def _dir(home):
    return fwd.book_dir(home, "FWD-001")


def _csv(home, name):
    p = _dir(home) / name
    return pd.read_csv(p, dtype=str, keep_default_na=False) if p.exists() else pd.DataFrame(columns=fwd.COLS[name])


def _state(home):
    return json.loads((_dir(home) / "state.json").read_text(encoding="utf-8"))


def _want(nav, n, p, cap=0.20, budget=0.995):
    """Số cổ phiếu mục tiêu theo mục 2 của giao thức, tính độc lập với mã."""
    alloc = min(nav / n, cap * nav) * budget
    return int(alloc // (p * (1 + C["slippage"]) * (1 + C["buy_fee"]))) // LOT * LOT


def _pos(home, book, upto):
    """Vị thế của sổ sau mọi giao dịch có ngày ≤ upto, dựng lại từ trades.csv."""
    t = _csv(home, "trades.csv")
    t = t[(t.book == book) & (t.date <= upto)]
    out = {}
    for r in t.itertuples(index=False):
        sign = {"BUY": 1, "SELL": -1, "STOCK_ADJUST": 1}.get(r.side)
        if sign:
            out[r.asset] = out.get(r.asset, 0) + sign * int(r.quantity)
    return {k: v for k, v in out.items() if v}


def _snapshot(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


# ---------- 1. chưa đăng ký ----------

def test_unregistered_creates_no_file_and_changes_no_byte(env):
    home = _home(env, register=False)
    before = _snapshot(home)
    for i in range(D0, D0 + 4):
        assert fwd.run(S[i], root=home, verify=lambda r: pytest.fail("không được xác minh"), now=f"{S[i]}T11:00:00Z",
                       run_id="1.1") is None
    assert _snapshot(home) == before and not (home / "paper").exists()
    (home / "research" / "trial_registry.jsonl").unlink()                 # không có sổ đăng ký
    assert fwd.run(S[D0], root=home) is None and fwd.load_registration(home, "FWD-001") is None
    (home / "research" / "trial_registry.jsonl").write_text(
        "không phải json\n" + json.dumps({**SPEC, "kind": "trial"}) + "\n" + json.dumps({**SPEC, "trial_id": "FWD-002"})
        + "\n", encoding="utf-8")
    assert fwd.load_registration(home, "FWD-001") is None and fwd.load_registration(home, "FWD-002")["trial_id"] == "FWD-002"


def test_run_cycle_calls_fwd_once_after_the_paper_book_in_both_modes():
    """Lệnh: engine/run_cycle.py chỉ thêm một lời gọi fwd.run sau paper.run, ở cả ops và research (cùng một đường chạy)."""
    tree = ast.parse((REPO / "engine" / "run_cycle.py").read_text(encoding="utf-8"))
    cyc = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "cycle")
    calls = [n for n in ast.walk(cyc) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
             and isinstance(n.func.value, ast.Name) and n.func.value.id == "fwd"]
    assert len(calls) == 1 and calls[0].func.attr == "run" and [ast.unparse(a) for a in calls[0].args] == ["as_of"]
    top = [n for n in cyc.body if isinstance(n, (ast.Expr, ast.Assign))]
    i_fwd = next(i for i, n in enumerate(top) if "fwd.run(" in ast.unparse(n))
    i_paper = next(i for i, n in enumerate(top) if "paper.run(" in ast.unparse(n))
    assert i_fwd == i_paper + 1                                          # ngay sau paper.run, ngoài mọi nhánh if ops


# ---------- 2. ba sổ đối chứng (mục 1, 2 của giao thức) ----------

def test_ew_hold_cash_follow_the_protocol_including_a_leaver_and_the_weight_cap(env):
    home, px = _home(env), _prices()
    Robot(home).days(D0, D0 + 8)
    per = _csv(home, "periods.csv")
    assert per.decision_session.tolist() == [S[D0], S[D0 + 3], S[D0 + 6]]
    assert per.fill_session.tolist() == [S[D0 + 1], S[D0 + 4], S[D0 + 7]] and set(per.status) == {"SEALED"}
    dec = _csv(home, "decisions.csv")
    tg0 = json.loads(dec[dec.k == "0"].targets.item())
    assert tg0 == {"FWD-CASH": [], "FWD-EW": TICK[:6], "FWD-HOLD": TICK[:6]}            # không hàm chấm: không sổ bóng
    # D0: EW và HOLD mua chia đều 6 mã đủ điều kiện ở giá đóng cửa D0+1; CASH không giao dịch
    for b in ("FWD-EW", "FWD-HOLD"):
        assert _pos(home, b, S[D0 + 1]) == {t: _want(CAP, 6, px.at[IDX[D0 + 1], t]) for t in TICK[:6]}
    trd = _csv(home, "trades.csv")
    assert trd[trd.book == "FWD-CASH"].empty
    nav = _csv(home, "nav.csv")
    assert nav[nav.book == "FWD-CASH"].nav.astype(float).eq(CAP).all() and nav.date.unique().tolist() == S[D0:D0 + 8]
    # k=1 (D0+3, sau khi FFF rời rổ): HOLD chỉ bán FFF, không mua GGG; EW bán FFF, mua GGG, đưa mọi mã về đúng phần vốn
    k1 = trd[trd.date == S[D0 + 4]]
    hold = k1[k1.book == "FWD-HOLD"]
    assert hold[["asset", "side"]].values.tolist() == [["FFF", "SELL"]]
    assert int(hold.quantity.item()) == _pos(home, "FWD-HOLD", S[D0 + 3])["FFF"]
    assert _pos(home, "FWD-HOLD", S[D0 + 4]) == {t: n for t, n in _pos(home, "FWD-HOLD", S[D0 + 3]).items() if t != "FFF"}
    ew_before = _pos(home, "FWD-EW", S[D0 + 3])
    p4 = px.loc[IDX[D0 + 4]]
    cash3 = float(nav[(nav.book == "FWD-EW") & (nav.date == S[D0 + 3])].cash.item())
    nav4 = cash3 + sum(n * p4[t] for t, n in ew_before.items())              # NAV ở phiên khớp, trước giao dịch
    want = {t: _want(nav4, 6, p4[t]) for t in TICK[:5] + ["GGG"]}
    after = _pos(home, "FWD-EW", S[D0 + 4])
    assert "FFF" not in after and after["GGG"] == want["GGG"]
    for t in TICK[:5]:                                                       # sai lệch chỉ do làm tròn lô
        assert abs(after[t] - want[t]) < LOT, t
    assert _state(home)["done"] is True
    n_rows = len(_csv(home, "nav.csv"))
    Robot(home).day(D0 + 9)                                                  # xong 2 kỳ: không ghi gì thêm
    assert len(_csv(home, "nav.csv")) == n_rows


def test_allocation_rule_caps_each_name_at_the_weight_limit():
    price = {"AAA": 20000.0, "BBB": 30000.0, "CCC": 10000.0, "DDD": 25000.0, "EEE": 15000.0, "FFF": 12000.0}.get
    bk = {"cash": float(CAP), "positions": {}}
    three = fwd._legs("FWD-EW", 0, ["AAA", "BBB", "CCC"], bk, CAP, price, SPEC)
    assert three == {t: _want(CAP, 3, price(t)) for t in ("AAA", "BBB", "CCC")}
    assert all(three[t] * price(t) <= 0.20 * 0.995 * CAP for t in three)                 # min(NAV/3, 20% NAV) × 0,995
    six = fwd._legs("FWD-S1", 0, list("ABCDEF"), bk, CAP, lambda t: 10000.0, SPEC)
    assert set(six.values()) == {_want(CAP, 6, 10000.0)}
    held = {"cash": 0.0, "positions": {"AAA": 1000, "BBB": 2000}}
    assert fwd._legs("FWD-HOLD", 1, ["AAA"], held, 1e8, price, SPEC) == {"BBB": 0}          # chỉ bán mã rời rổ
    assert fwd._legs("FWD-HOLD", 1, ["AAA", "CCC"], held, 1e8, price, SPEC) == {"BBB": 0}   # không mua mã mới
    assert fwd._legs("FWD-CASH", 0, ["AAA"], bk, CAP, price, SPEC) == {}


# ---------- 3. lượt bị bỏ, phiên tái cơ cấu bị lỡ ----------

def test_a_skipped_run_fills_at_the_close_of_t_plus_1(env):
    home, px = _home(env), _prices()
    rb = Robot(home)
    rb.day(D0)
    rb.day(D0 + 2)                                                           # lượt D0+1 bị bỏ
    trd = _csv(home, "trades.csv")
    buys = trd[trd.side == "BUY"]
    assert set(buys.date) == {S[D0 + 1]} and len(buys) == 12
    for r in buys.itertuples(index=False):
        assert float(r.price) == round(px.at[IDX[D0 + 1], r.asset] * (1 + C["slippage"]), 2)
    assert _csv(home, "nav.csv").date.unique().tolist() == S[D0:D0 + 3]
    assert _csv(home, "periods.csv").fill_session.tolist() == [S[D0 + 1]]


def test_a_missed_rebalance_session_is_late_void_and_is_not_decided_late(env):
    home = _home(env)
    rb = Robot(home)
    rb.days(D0, D0 + 2)
    rb.day(D0 + 4)                                                           # lượt của phiên tái cơ cấu D0+3 bị bỏ
    dec = _csv(home, "decisions.csv")
    late = dec[dec.action == "LATE_VOID"]
    assert late.date.tolist() == [S[D0 + 3]] and late.k.tolist() == ["1"] and "không quyết định muộn" in late.note.item()
    assert dec[(dec.action == "DECIDE") & (dec.k == "1")].empty
    per = _csv(home, "periods.csv")
    assert per[per.k == "1"][["decision_session", "fill_session", "status"]].values.tolist() == \
        [[S[D0 + 3], S[D0 + 4], "LATE_VOID"]]
    trd = _csv(home, "trades.csv")
    assert trd[trd.date == S[D0 + 4]].empty and "FFF" in _pos(home, "FWD-EW", S[D0 + 4])   # danh mục giữ nguyên
    rb.days(D0 + 5, D0 + 7)                                                  # kỳ sau vẫn theo lịch D0 + 6
    dec = _csv(home, "decisions.csv")
    assert dec[dec.action == "DECIDE"].date.tolist() == [S[D0], S[D0 + 6]]


# ---------- 4. niêm phong: xác minh lượt chạy ----------

def test_verify_error_waits_then_fills_at_t_plus_1_on_a_later_run(env):
    home, px = _home(env), _prices()
    rb = Robot(home)
    rb.day(D0)
    real = rb.runs[f"{D0}.1"]
    rb.runs[f"{D0}.1"] = OSError("API GitHub lỗi")
    res = rb.day(D0 + 1)
    assert res["stopped"] == "VERIFY_WAIT" and res["processed"] == []
    assert _csv(home, "decisions.csv").action.tolist() == ["DECIDE", "VERIFY_WAIT"]
    assert _csv(home, "trades.csv").empty and _state(home)["last"] == S[D0]
    rb.runs[f"{D0}.1"] = real
    rb.day(D0 + 2)
    buys = _csv(home, "trades.csv").query("side == 'BUY'")
    assert set(buys.date) == {S[D0 + 1]}
    assert all(float(r.price) == round(px.at[IDX[D0 + 1], r.asset] * (1 + C["slippage"]), 2)
               for r in buys.itertuples(index=False))


@pytest.mark.parametrize("info, why", [
    ({"finished_at": "{t1}T02:00:00Z"}, "không trước hạn"),                 # 09:00 giờ VN của phiên khớp: trễ
    ({"finished_at": "{t1}T03:15:00Z"}, "không trước hạn"),
    ({"path": ".github/workflows/tests.yml"}, "workflow"),
    ({"branch": "claude/x"}, "nhánh"),
    ({"event": "push"}, "sự kiện"),
    ({"conclusion": "failure"}, "kết luận"),
])
def test_a_late_or_invalid_run_voids_the_rebalance(env, info, why):
    home = _home(env)
    rb = Robot(home)
    rb.days(D0, D0 + 2)
    rb.day(D0 + 3, **{k: v.format(t1=S[D0 + 4]) for k, v in info.items()})
    rb.day(D0 + 4)
    per = _csv(home, "periods.csv")
    row = per[per.k == "1"]
    assert row.status.item() == "LATE_VOID" and why in row.note.item() and row.fill_session.item() == S[D0 + 4]
    assert _csv(home, "trades.csv").query("date == @S[@D0 + 4]").empty
    assert "FFF" in _pos(home, "FWD-EW", S[D0 + 4]) and "FFF" in _pos(home, "FWD-HOLD", S[D0 + 4])


def test_a_late_d0_moves_d0_to_the_next_session(env):
    home = _home(env)
    rb = Robot(home)
    rb.day(D0 + 1)                                                           # lượt đầu tiên sau D0 đã đăng ký
    dec = _csv(home, "decisions.csv")
    assert dec[["date", "action"]].values.tolist() == [[S[D0], "D0_LATE"], [S[D0 + 1], "DECIDE"]]
    rb.runs[f"{D0 + 1}.1"]["finished_at"] = f"{S[D0 + 2]}T03:00:00Z"        # lượt ghi quyết định D0 kết thúc 10:00 VN
    rb.days(D0 + 2, D0 + 4)
    dec = _csv(home, "decisions.csv")
    assert dec[dec.action == "D0_LATE"].date.tolist() == [S[D0], S[D0 + 2]]   # trễ lúc khớp: D0 dời sang phiên khớp
    assert dec[dec.action == "DECIDE"].date.tolist() == [S[D0 + 1], S[D0 + 2]]
    per = _csv(home, "periods.csv")
    assert per[["k", "decision_session", "fill_session", "status"]].values.tolist() == \
        [["0", S[D0 + 2], S[D0 + 3], "SEALED"]]
    assert _state(home)["d0"] == S[D0 + 2] and set(_csv(home, "trades.csv").date) == {S[D0 + 3]}


def test_the_machine_clock_past_the_deadline_refuses_the_decision(env):
    home = _home(env)
    rb = Robot(home)
    rb.day(D0, now=f"{S[D0 + 1]}T02:30:00Z")                                 # 09:30 giờ VN của phiên kế
    dec = _csv(home, "decisions.csv")
    assert dec.action.tolist() == ["D0_LATE"] and "tự từ chối" in dec.note.item()
    rb.days(D0 + 1, D0 + 2)
    rb.day(D0 + 4, now=f"{S[D0 + 5]}T01:59:00Z")                             # 08:59: còn hạn (D0 thực tế là D0+1)
    assert _csv(home, "decisions.csv").query("k == '1'").action.tolist() == ["DECIDE"]


def test_limit_locked_orders_wait_for_the_next_session(env):
    """Khóa biên độ như paper.locked, trên bảng giá đã điều chỉnh của chế độ verified: BBB tăng 6,9% ở phiên khớp D0+1 (khóa
    trần) → mua ở D0+2; FFF giảm 6,9% ở phiên khớp D0+4 (khóa sàn) → bán ở D0+5."""
    px = _prices()
    px.loc[IDX[D0 + 1]:, "BBB"] = (px.loc[IDX[D0 + 1]:, "BBB"] * 1.069).round(-1)
    px.loc[IDX[D0 + 4]:, "FFF"] = (px.loc[IDX[D0 + 4]:, "FFF"] * 0.931).round(-1)
    home = _home(env, close=px)
    Robot(home).days(D0, D0 + 5)
    trd = _csv(home, "trades.csv")
    b = trd[(trd.asset == "BBB") & (trd.book == "FWD-HOLD")]
    assert b[["date", "side"]].values.tolist() == [[S[D0 + 1], "UNFILLED_LIMIT_UP"], [S[D0 + 2], "BUY"]]
    assert float(b.price.iloc[1]) == round(px.at[IDX[D0 + 2], "BBB"] * (1 + C["slippage"]), 2)
    f = trd[(trd.asset == "FFF") & (trd.book == "FWD-HOLD") & (trd.date > S[D0 + 1])]
    assert f[["date", "side"]].values.tolist() == [[S[D0 + 4], "UNFILLED_LIMIT_DOWN"], [S[D0 + 5], "SELL"]]
    # EW: FFF chưa bán được ở D0+4 nên tiền mua GGG bị giới hạn bởi tiền mặt; tiền mặt không bao giờ âm
    nav = _csv(home, "nav.csv")
    assert nav.cash.astype(float).min() >= 0
    g = trd[(trd.asset == "GGG") & (trd.book == "FWD-EW") & (trd.side == "BUY")]
    ew3 = nav[(nav.book == "FWD-EW") & (nav.date == S[D0 + 3])]
    assert g.date.tolist() == [S[D0 + 4]] and int(g.quantity.item()) < _want(float(ew3.nav.item()), 6, px.at[IDX[D0 + 4], "GGG"])


# ---------- 5. thiếu giá ----------

def test_a_missing_price_is_stale_and_retried_and_a_session_without_prices_stops(env):
    """AAA không giao dịch ở phiên khớp D0+1 (dòng giá khối lượng 0, như mã ngừng giao dịch: không có giá theo QĐ-11a). Dòng
    giá thiếu hẳn thì cổng R1a không đo được giá trị giao dịch bình quân và FAIL cả sổ (ngữ nghĩa paper.run), nên phép thử
    «thử lại» dùng khối lượng 0. Phiên D0+5: kho không có dòng nào."""
    vol = pd.DataFrame(1e6, index=IDX, columns=TICK)
    vol.loc[IDX[D0 + 1], "AAA"] = 0.0
    home, px = _home(env, vol=vol, drop=[(IDX[D0 + 5], None)]), _prices()
    rb = Robot(home)
    rb.days(D0, D0 + 2)
    trd = _csv(home, "trades.csv")
    stale = trd[trd.side == "STALE_PRICE"]
    assert stale[["date", "book", "asset"]].values.tolist() == [[S[D0 + 1], "FWD-EW", "AAA"], [S[D0 + 1], "FWD-HOLD", "AAA"]]
    aaa = trd[(trd.asset == "AAA") & (trd.side == "BUY")]
    assert aaa.date.tolist() == [S[D0 + 2]] * 2 and float(aaa.price.iloc[0]) == round(px.at[IDX[D0 + 2], "AAA"] * 1.001, 2)
    nav = _csv(home, "nav.csv")
    assert set(nav[(nav.date == S[D0 + 1]) & (nav.book != "FWD-CASH")].stale) == {""}           # AAA chưa có trong sổ
    rb.days(D0 + 3, D0 + 4)
    res = rb.day(D0 + 6)                                                     # phiên D0+5: không mã nào có giá
    assert res["stopped"] == "WAIT_PRICES" and _state(home)["last"] == S[D0 + 4]
    assert _csv(home, "decisions.csv").action.tolist()[-1] == "WAIT_PRICES"
    assert _csv(home, "nav.csv").date.max() == S[D0 + 4]


def test_a_held_name_without_a_price_is_valued_at_its_last_raw_close(env):
    home, px = _home(env, drop=[(IDX[D0 + 2], "BBB")]), _prices()
    Robot(home).days(D0, D0 + 2)
    nav = _csv(home, "nav.csv").query("date == @S[@D0 + 2] and book == 'FWD-EW'")
    pos = _pos(home, "FWD-EW", S[D0 + 2])
    expect = float(nav.cash.item()) + sum(n * (px.at[IDX[D0 + 1], t] if t == "BBB" else px.at[IDX[D0 + 2], t])
                                          for t, n in pos.items())
    assert nav.stale.item() == "BBB" and abs(float(nav.nav.item()) - expect) <= 1


def test_an_unannounced_day_without_prices_is_not_a_session(env):
    off = IDX[D0 + 2]
    vol = pd.DataFrame(1e6, index=IDX, columns=TICK)
    vol.loc[off] = 0.0
    home = _home(env, vol=vol, unann=[off])
    Robot(home).days(D0, D0 + 3)
    nav = _csv(home, "nav.csv")
    assert S[D0 + 2] not in set(nav.date) and nav.date.unique().tolist() == [S[D0], S[D0 + 1], S[D0 + 3]]


# ---------- 6. sự kiện quyền ----------

def test_corporate_actions_cash_stock_unverified_late_and_not_for_shares_bought_that_session(env):
    px = _prices()
    px.loc[IDX[D0 + 3]:, "BBB"] = (px.loc[IDX[D0 + 3]:, "BBB"] / 1.5).round(-1)          # cổ tức cổ phiếu 3:2 của BBB
    home = _home(env, close=px, events=[
        {"ticker": "DDD", "ex_date": S[D0 + 1], "type": "cash_dividend", "cash_per_share": 700.0},  # ngày mua của D0
        {"ticker": "AAA", "ex_date": S[D0 + 2], "type": "cash_dividend", "cash_per_share": 1000.0}])
    rb = Robot(home)
    rb.days(D0, D0 + 2)
    _write_events(home, [
        {"ticker": "DDD", "ex_date": S[D0 + 1], "type": "cash_dividend", "cash_per_share": 700.0},
        {"ticker": "AAA", "ex_date": S[D0 + 2], "type": "cash_dividend", "cash_per_share": 1000.0},
        {"ticker": "BBB", "ex_date": S[D0 + 3], "type": "stock_dividend", "ratio": 1.5}])
    rb.day(D0 + 3)
    _write_events(home, [
        {"ticker": "DDD", "ex_date": S[D0 + 1], "type": "cash_dividend", "cash_per_share": 700.0},
        {"ticker": "AAA", "ex_date": S[D0 + 2], "type": "cash_dividend", "cash_per_share": 1000.0},
        {"ticker": "BBB", "ex_date": S[D0 + 3], "type": "stock_dividend", "ratio": 1.5},
        {"ticker": "CCC", "ex_date": S[D0 + 2], "type": "cash_dividend", "cash_per_share": 400.0},    # biết muộn
        {"ticker": "EEE", "ex_date": S[D0 + 1], "type": "cash_dividend", "cash_per_share": 500.0}])   # biết muộn, ngày mua
    rb.day(D0 + 4)
    assert "FFF" not in _pos(home, "FWD-HOLD", S[D0 + 4])                    # FFF rời rổ, đã bán ở D0+4
    _write_events(home, [
        {"ticker": "DDD", "ex_date": S[D0 + 1], "type": "cash_dividend", "cash_per_share": 700.0},
        {"ticker": "AAA", "ex_date": S[D0 + 2], "type": "cash_dividend", "cash_per_share": 1000.0},
        {"ticker": "BBB", "ex_date": S[D0 + 3], "type": "stock_dividend", "ratio": 1.5},
        {"ticker": "CCC", "ex_date": S[D0 + 2], "type": "cash_dividend", "cash_per_share": 400.0},
        {"ticker": "EEE", "ex_date": S[D0 + 1], "type": "cash_dividend", "cash_per_share": 500.0},
        {"ticker": "FFF", "ex_date": S[D0 + 3], "type": "cash_dividend", "cash_per_share": 300.0}])   # biết muộn, đã bán
    rb.day(D0 + 5)
    trd = _csv(home, "trades.csv")
    ca = trd[trd.side.isin(["CASH_DIVIDEND", "STOCK_ADJUST"])]
    assert not {"DDD", "EEE"} & set(ca.asset)            # cổ phiếu mua ở đóng cửa phiên GDKHQ không hưởng quyền
    tax = C["dividend_tax"]
    for b in ("FWD-EW", "FWD-HOLD"):
        held1 = _pos(home, b, S[D0 + 1])
        a = ca[(ca.book == b) & (ca.asset == "AAA")]
        assert a[["date", "side", "flags"]].values.tolist() == [[S[D0 + 2], "CASH_DIVIDEND", ""]]
        assert int(a.quantity.item()) == held1["AAA"] and float(a.value.item()) == round(held1["AAA"] * 1000 * (1 - tax), 2)
        assert a.event.item() == f"AAA|{S[D0 + 2]}|cash_dividend"
        bb = ca[(ca.book == b) & (ca.asset == "BBB")]
        assert bb[["date", "side", "flags"]].values.tolist() == [[S[D0 + 3], "STOCK_ADJUST", "CA_UNVERIFIED"]]
        assert int(bb.quantity.item()) == int(held1["BBB"] * 1.5) - held1["BBB"] and float(bb.value.item()) == 1.5
        c = ca[(ca.book == b) & (ca.asset == "CCC")]
        assert c[["date", "flags"]].values.tolist() == [[S[D0 + 4], "CA_LATE"]]
        assert int(c.quantity.item()) == held1["CCC"]                       # cơ sở: số cổ phiếu trước phiên D0+2
        f = ca[(ca.book == b) & (ca.asset == "FFF")]                        # cơ sở theo ngày GDKHQ, không theo vị thế hôm nay
        assert f[["date", "flags"]].values.tolist() == [[S[D0 + 5], "CA_LATE"]]
        assert int(f.quantity.item()) == held1["FFF"] and float(f.value.item()) == round(held1["FFF"] * 300 * (1 - tax), 2)
    nav = _csv(home, "nav.csv")
    for i in (D0 + 2, D0 + 3):                                               # định giá theo giá gốc, sau sự kiện
        r = nav[(nav.date == S[i]) & (nav.book == "FWD-HOLD")]
        pos = _pos(home, "FWD-HOLD", S[i])
        assert abs(float(r.nav.item()) - (float(r.cash.item()) + sum(n * px.at[IDX[i], t] for t, n in pos.items()))) <= 1
    cash2 = nav[(nav.date == S[D0 + 2]) & (nav.book == "FWD-HOLD")].cash.astype(float).item()
    cash1 = nav[(nav.date == S[D0 + 1]) & (nav.book == "FWD-HOLD")].cash.astype(float).item()
    assert abs(cash2 - cash1 - _pos(home, "FWD-HOLD", S[D0 + 1])["AAA"] * 1000 * (1 - tax)) <= 1


# ---------- 7. sụt giảm: chỉ ghi nhận ----------

def test_a_drawdown_breach_is_only_recorded_and_nothing_is_sold(env):
    px = _prices()
    for i in (D0 + 2, D0 + 3, D0 + 4):                                       # −6%/phiên ba phiên: < biên độ, NAV −17%
        px.loc[IDX[i]:] = (px.loc[IDX[i]:] * 0.94).round(-1)
    home = _home(env, close=px, period_sessions=10)
    Robot(home).days(D0, D0 + 7)
    dec = _csv(home, "decisions.csv")
    br = dec[dec.action == "DRAWDOWN_BREACH"]
    assert br[["date", "book"]].values.tolist() == [[S[D0 + 4], "FWD-EW"], [S[D0 + 4], "FWD-HOLD"]]   # một lần mỗi sổ
    assert "không khóa, không bán" in br.note.iloc[0]
    trd = _csv(home, "trades.csv")
    assert set(trd.side) == {"BUY"} and set(trd.date) == {S[D0 + 1]}        # không bán gì sau khi chạm ngưỡng
    st = _state(home)
    assert st["books"]["FWD-EW"]["positions"] == _pos(home, "FWD-EW", S[D0 + 1]) and st["books"]["FWD-EW"]["in_breach"]
    dd = _csv(home, "drawdown.csv").query("book == 'FWD-EW' and date == @S[@D0 + 4]")
    assert float(dd.drawdown.item()) >= 0.15


# ---------- 8. dựng lại ----------

@pytest.mark.parametrize("case", ["plain", "events_stale_late"])
def test_replay_from_d0_matches_the_daily_run_row_for_row(env, case):
    if case == "plain":
        home = _home(env)
        rb = Robot(home)
        rb.days(D0, D0 + 8)
    else:
        px = _prices()
        px.loc[IDX[D0 + 3]:, "BBB"] = (px.loc[IDX[D0 + 3]:, "BBB"] / 1.5).round(-1)
        evs = [{"ticker": "AAA", "ex_date": S[D0 + 2], "type": "cash_dividend", "cash_per_share": 1000.0},
               {"ticker": "BBB", "ex_date": S[D0 + 3], "type": "stock_dividend", "ratio": 1.5}]
        vol = pd.DataFrame(1e6, index=IDX, columns=TICK)
        vol.loc[IDX[D0 + 1], "CCC"] = vol.loc[IDX[D0 + 4], "EEE"] = 0.0
        home = _home(env, close=px, vol=vol, events=evs[:1])
        rb = Robot(home)
        rb.days(D0, D0 + 2)
        _write_events(home, evs)
        rb.day(D0 + 4)                                                       # lượt D0+3 (tái cơ cấu) bị bỏ
        rb.days(D0 + 5, D0 + 8)
        assert "LATE_VOID" in set(_csv(home, "periods.csv").status)
        sides = set(_csv(home, "trades.csv").side)
        assert {"BUY", "SELL", "CASH_DIVIDEND", "STOCK_ADJUST", "STALE_PRICE"} <= sides
    nav = _csv(home, "nav.csv")[["date", "book", "nav"]].reset_index(drop=True)
    got = fwd.replay(home, SPEC, S[D0 + 8]).astype(str).reset_index(drop=True)
    assert len(nav) > 20 and got.equals(nav)


# ---------- 9. nhãn PIT, cổng R1a, đặc tả, chạy lại ----------

def test_a_label_other_than_pit_modes_only_processes_no_session(env):
    home = _home(env, calendar=False)                                        # không có lịch: RETROSPECTIVE
    res = Robot(home).day(D0)
    assert res["stopped"] == "PIT_REJECTED"
    dec = _csv(home, "decisions.csv")
    assert dec.action.tolist() == ["PIT_REJECTED"] and "RETROSPECTIVE" in dec.note.item()
    assert sorted(p.name for p in _dir(home).iterdir()) == ["decisions.csv"]


def test_the_risk_gate_applies_at_the_decision_and_at_the_fill(env, monkeypatch):
    home = _home(env)
    lim = config.CFG["paper"]["risk_limits"]
    monkeypatch.setitem(lim, "max_participation", 0.001)                    # thoát vị thế cần > 3 phiên: FAIL
    rb = Robot(home)
    rb.day(D0)
    dec = _csv(home, "decisions.csv")
    tg = json.loads(dec.targets.item())
    assert tg["FWD-EW"] == [] and tg["FWD-HOLD"] == [] and "FWD-EW: cổng rủi ro FAIL" in dec.note.item()
    rb.day(D0 + 1)
    assert _csv(home, "trades.csv").empty
    monkeypatch.setitem(lim, "max_participation", 0.10)
    rb.day(D0 + 2)                                                           # D0 thực tế là D0 ... kỳ 1 ở D0+3
    rb.day(D0 + 3)
    assert json.loads(_csv(home, "decisions.csv").query("k == '1'").targets.item())["FWD-EW"] == TICK[:5] + ["GGG"]
    monkeypatch.setitem(lim, "max_participation", 0.001)                    # cổng hỏng ở phiên khớp: không mua mã nào
    rb.day(D0 + 4)
    rb.day(D0 + 5)
    trd = _csv(home, "trades.csv")
    assert set(trd.side) == {"UNFILLED_RISK_GATE"} and set(trd.date) == {S[D0 + 4]}      # không thử lại
    assert trd.book.tolist() == ["FWD-EW"] * 6                       # HOLD: D0 không mua được nên không có gì để giữ
    monkeypatch.setitem(lim, "max_participation", 0.10)                     # replay dùng dòng cổng đã ghi, không tính lại
    nav = _csv(home, "nav.csv")[["date", "book", "nav"]].reset_index(drop=True)
    assert fwd.replay(home, SPEC, S[D0 + 5]).astype(str).reset_index(drop=True).equals(nav)


@pytest.mark.parametrize("over, why", [({"capital": 0}, "capital"), ({"books": ["FWD-EW"]}, "books"),
                                       ({"period_sessions": 0}, "period_sessions"), ({"d0": "05/02/2026"}, "d0"),
                                       ({"seal_deadline_local": "9h"}, "seal_deadline_local")])
def test_a_broken_spec_is_recorded_and_processes_nothing(env, over, why):
    home = _home(env, **over)
    res = Robot(home).day(D0)
    dec = _csv(home, "decisions.csv")
    assert res["stopped"] == "SPEC_INVALID" and dec.action.tolist() == ["SPEC_INVALID"] and why in dec.note.item()
    spec = {k: v for k, v in SPEC.items() if k != "adr_commit"}
    assert "adr_commit" in fwd.spec_problem(spec)


def test_running_the_same_session_twice_writes_nothing_new(env):
    home = _home(env)
    rb = Robot(home)
    rb.days(D0, D0 + 1)
    snap = _snapshot(_dir(home))
    assert rb.day(D0 + 1)["processed"] == [] and _snapshot(_dir(home)) == snap
