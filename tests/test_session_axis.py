"""E2c (QĐ-1 của ADR-0016): trục phiên của đầu vào nghiên cứu — `load_market(..., sessions="keep"|"calendar")`.

Ngày không phải phiên (data.non_session_days):
  - trong vùng data/trading_calendar.csv phủ: ngày lịch ghi is_session=0 (chỉ lịch quyết định);
  - ngoài vùng đó, hoặc khi không có tệp lịch: ngày mà mọi mã trong kho có khối lượng bằng 0 hoặc thiếu;
  - lịch hỏng: lỗi ở cả hai chế độ.
"keep" (mặc định) giữ trục ngày và chỉ liệt kê các ngày đó ở `quality.sessions`; khóa này không vào ENGINE_STATE, nên đầu
ra vòng học không đổi. "calendar" bỏ các ngày đó khỏi kho trước mọi phép tính: kết quả bằng đúng kết quả của một kho không có
các dòng đó. pit_label = POINT_IN_TIME chỉ khi research_input="verified", universe "historical", sessions="calendar".

Fixture ghi vào thư mục tạm (config.ROOT và adjust.ROOT được vá); lượt chạy engine diễn ra trong tiến trình con với TTC_HOME
tạm. Không mạng, không ghi vào kho.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
import pathlib
import pickle
import shutil
import subprocess
import sys
import textwrap
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from engine import adjust, config, data  # noqa: E402

IDX = pd.bdate_range("2025-03-03", periods=420)            # 2025-03-03 … 2026-10-09
U = list(config.CFG["universe"][:4])
OBS = "2026-10-12"
NONE = pd.DataFrame(columns=adjust.EV_COLS)
COV = ("2026-01-01", "2026-12-31")                          # vùng lịch giả phủ
T = pd.Timestamp
HOL = [T("2026-01-01"), T("2026-01-02"), T("2026-02-16"), T("2026-02-17"), T("2026-02-18")]   # lịch nghỉ, khối lượng 0
CALV = T("2026-04-30")                                      # lịch nghỉ nhưng kho có khối lượng > 0
ZS = T("2026-03-10")                                        # lịch ghi là phiên, mọi mã khối lượng 0
ZV = [IDX[40], IDX[41], IDX[42]]                            # 2025-04-28…30: ngoài vùng lịch, mọi mã khối lượng 0
ZM = IDX[60]                                                # 2025-05-26: 2 mã khối lượng 0, 2 mã không có dòng
PZ = IDX[75]                                                # 2025-06-16: chỉ 2 trong 4 mã khối lượng 0
UNANN = T("2026-06-01")                                     # lịch ghi CHUA_CO_THONG_BAO, trong khoảng dữ liệu
UNANN_OUT = T("2026-12-28")                                 # CHUA_CO_THONG_BAO, sau ngày cuối của dữ liệu
CAL_OFF = sorted(HOL + [CALV])
VOL_OFF = sorted(ZV + [ZM])
OFF = sorted(CAL_OFF + VOL_OFF)
KEYS = ("close", "volume", "raw_close", "bad", "events", "flags")


def _iso(days):
    return [str(pd.Timestamp(d).date()) for d in days]


def _prices(seed=11):
    rng = np.random.default_rng(seed)
    r = rng.normal(0.0, 0.012, size=(len(IDX), len(U))).clip(-0.05, 0.05)
    close = pd.DataFrame(20000.0 * np.cumprod(1 + r, axis=0), index=IDX, columns=U).round(-1)
    vol = pd.DataFrame(1e6, index=IDX, columns=U)
    for d in HOL + ZV + [ZS, ZM]:                           # ngày nghỉ: giá giữ nguyên phiên trước, khối lượng 0
        close.loc[d] = close.iloc[IDX.get_loc(d) - 1].values
        vol.loc[d] = 0.0
    vol.loc[PZ, U[:2]] = 0.0
    close.loc[ZM, U[2:]] = np.nan                           # hai mã không có dòng ngày ZM
    return close, vol


def _rows(close, vol, skip=()):
    out = []
    for d in close.index:
        if d in skip:
            continue
        for t in close.columns:
            p = close.at[d, t]
            if pd.notna(p):
                out.append({"date": d.strftime("%Y-%m-%d"), "ticker": t, "open": p, "high": p, "low": p, "close": p,
                            "volume": float(vol.at[d, t]), "observed_at": OBS, "source": "fixture"})
    return pd.DataFrame(out, columns=data.COLS)


def _calendar(off=CAL_OFF, unann=(UNANN, UNANN_OUT), lo=COV[0], hi=COV[1]):
    lines = ["date,is_session,source_id"]
    for d in pd.date_range(lo, hi, freq="D"):
        if d.weekday() >= 5:
            lines.append(f"{d.date()},0,WEEKEND")
        elif d in set(off):
            lines.append(f"{d.date()},0,fx-hol")
        elif d in set(unann):
            lines.append(f"{d.date()},1,{data.UNANNOUNCED}")
        else:
            lines.append(f"{d.date()},1,HOSE_DEFAULT")
    return "\n".join(lines) + "\n"


def _history(start=IDX[20]):
    return "effective_date,ticker,action,source_id\n" + "".join(f"{start.date()},{t},ADD,fx\n" for t in U)


def _manual(at):
    return pd.DataFrame([{"ticker": U[0], "ex_date": at, "type": "stock_dividend", "ratio": 1.2, "cash_per_share": np.nan,
                          "source": "manual (fixture)", "source_status": "CAN_DOI_CHIEU", "note": ""}],
                        columns=adjust.EV_COLS)


def _home(tmp, skip=(), calendar=True, cal_text=None, history=True, manual=None):
    tmp = pathlib.Path(tmp)
    tmp.mkdir(parents=True, exist_ok=True)
    close, vol = _prices()
    assert data.save_store(_rows(close, vol, skip), root=tmp) > 0
    for key, df in (("manual", NONE if manual is None else manual), ("yahoo_cache", NONE)):
        p = tmp / config.CFG["corporate_actions"][key]
        p.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(p, index=False)
    (tmp / "data").mkdir(parents=True, exist_ok=True)
    if calendar:
        (tmp / "data" / "trading_calendar.csv").write_text(cal_text or _calendar(), encoding="utf-8")
    if history:
        (tmp / data.VN30_HISTORY).write_text(_history(), encoding="utf-8")
    return tmp


def _market(home, as_of=None, **kw):
    with patch.object(config, "ROOT", home), patch.object(adjust, "ROOT", home):
        return data.load_market(as_of, **kw)


def _h(x):
    if isinstance(x, pd.DataFrame):
        return hashlib.sha256(pickle.dumps((x.to_csv(), [str(t) for t in x.dtypes], str(x.index.dtype)))).hexdigest()
    return hashlib.sha256(json.dumps(x, sort_keys=True, default=str, ensure_ascii=False).encode()).hexdigest()


def _store_dates(home):
    return sorted(data.load_store(root=home)["date"].unique())


# ---------- keep (mặc định) ---------------------------------------------------------------------------------------------

def test_keep_is_the_default_keeps_the_axis_and_lists_the_non_sessions(tmp_path):
    home = _home(tmp_path)
    mk, keep = _market(home), _market(home, sessions="keep")
    assert list(mk["close"].index) == _store_dates(home)            # trục ngày không đổi
    for k in (*KEYS, "derivation_id", "pit_label", "pit_gaps"):
        assert _h(mk[k]) == _h(keep[k]), k
    assert _h(mk["quality"]) == _h(keep["quality"])
    q = mk["quality"]["sessions"]
    assert q == {"mode": "keep", "calendar_coverage": list(COV), "non_session_calendar": _iso(CAL_OFF),
                 "non_session_zero_volume": _iso(VOL_OFF), "dropped": 0, "unannounced": _iso([UNANN])}
    assert str(ZS.date()) not in json.dumps(q) and str(PZ.date()) not in json.dumps(q)   # lịch ghi phiên; có mã giao dịch
    assert "trục ngày chưa lọc ngày nghỉ theo lịch phiên HOSE" in mk["pit_gaps"]


def test_keep_changes_nothing_but_the_session_report(tmp_path):
    """Cùng kho: mọi khóa trả về (kể cả quality trừ `sessions`, derivation_id, pit_gaps) giống từng byte với lượt mà phép tìm
    ngày không phải phiên không tìm thấy ngày nào."""
    home = _home(tmp_path, manual=_manual(IDX[50]))
    for kw in ({}, {"research_input": "verified"}, {"universe": "historical"}):
        a = _market(home, **kw)
        empty = {"calendar": [], "zero_volume": [], "unannounced": [], "coverage": None}
        with patch.object(data, "non_session_days", lambda *x, **y: empty):
            b = _market(home, **kw)
        assert set(a) == set(b)
        a["quality"].pop("sessions"), b["quality"].pop("sessions")
        for k in a:
            assert _h(a[k]) == _h(b[k]), (kw, k)


# ---------- calendar ----------------------------------------------------------------------------------------------------

def test_calendar_drops_calendar_holidays_and_zero_volume_days_outside_the_calendar(tmp_path):
    home = _home(tmp_path)
    mk = _market(home, sessions="calendar")
    axis = list(mk["close"].index)
    assert axis == [d for d in _store_dates(home) if d not in set(OFF)]
    assert ZS in axis and PZ in axis                                 # lịch ghi phiên; có mã giao dịch
    assert not set(OFF) & set(axis)
    q = mk["quality"]["sessions"]
    assert (q["mode"], q["dropped"]) == ("calendar", len(OFF))
    assert (q["non_session_calendar"], q["non_session_zero_volume"]) == (_iso(CAL_OFF), _iso(VOL_OFF))


@pytest.mark.parametrize("kw", [{}, {"research_input": "verified"}, {"universe": "historical"},
                                {"research_input": "verified", "universe": "historical"}])
def test_calendar_equals_a_store_without_those_rows(tmp_path, kw):
    """Bỏ TRƯỚC khi tính hệ số, mặt nạ cửa sổ QĐ-3 và báo cáo chất lượng: kết quả bằng đúng kho không có các dòng đó. Sự kiện
    cách ly ở IDX[50] có cửa sổ −21/+120 phiên phủ ba ngày ZV và ngày ZM, nên cửa sổ đếm trên trục đã bỏ."""
    ev = _manual(IDX[50])
    a = _market(_home(tmp_path / "a", manual=ev), sessions="calendar", **kw)
    b = _market(_home(tmp_path / "b", manual=ev, skip=set(OFF)), **kw)
    keys = [k for k in (*KEYS, "exclude", "eligible", "event_checks", "members") if k in a]
    assert set(keys) == {k for k in (*KEYS, "exclude", "eligible", "event_checks", "members") if k in b}
    for k in keys:
        assert _h(a[k]) == _h(b[k]), k
    qa, qb = dict(a["quality"]), dict(b["quality"])
    assert qb.pop("sessions")["dropped"] == 0 and qa.pop("sessions")["dropped"] == len(OFF)
    assert _h(qa) == _h(qb)
    if kw.get("research_input") == "verified":
        x = a["exclude"][U[0]]
        k = list(a["close"].index).index(IDX[50])
        before, after = data.window_bounds()
        assert x.iloc[k - before:k + after + 1].all() and not x.iloc[:k - before].any()


def test_without_a_calendar_file_the_zero_volume_rule_covers_every_day(tmp_path):
    home = _home(tmp_path, calendar=False)
    mk = _market(home, sessions="calendar")
    zero = sorted(HOL + ZV + [ZS, ZM])                               # CALV có khối lượng: không bỏ
    q = mk["quality"]["sessions"]
    assert (q["calendar_coverage"], q["non_session_calendar"], q["non_session_zero_volume"], q["unannounced"]) == \
        (None, [], _iso(zero), [])
    assert list(mk["close"].index) == [d for d in _store_dates(home) if d not in set(zero)]
    assert any("không có data/trading_calendar.csv" in g for g in mk["pit_gaps"])


@pytest.mark.parametrize("sessions", ["keep", "calendar"])
@pytest.mark.parametrize("text", [
    "date,is_session,source_id\n2026-01-01,2,x\n",                   # is_session khác 0 và 1
    "date,is_session\n2026-01-01,1\n2026-01-03,1\n",                 # không liền ngày
    "ngay,phien\n2026-01-01,1\n",                                     # thiếu cột
    "date,is_session\n01/01/2026,1\n",                                # sai dạng ngày
])
def test_broken_calendar_raises_in_both_modes(tmp_path, sessions, text):
    home = _home(tmp_path, cal_text=text)
    with pytest.raises(ValueError, match="lịch phiên HOSE"):
        _market(home, sessions=sessions)


def test_unannounced_days_are_listed_only_inside_the_data_range(tmp_path):
    home = _home(tmp_path)
    assert _market(home, as_of=str(IDX[300].date()))["quality"]["sessions"]["unannounced"] == []     # 2026-04-27 < UNANN
    mk = _market(home, sessions="calendar")
    assert mk["quality"]["sessions"]["unannounced"] == _iso([UNANN])                                  # UNANN_OUT ngoài dữ liệu
    assert any(data.UNANNOUNCED in g and g.startswith("1 ngày") for g in mk["pit_gaps"])


def test_coverage_note_only_when_the_data_leaves_the_calendar(tmp_path):
    inside = _home(tmp_path / "in", cal_text=_calendar(lo=str(IDX[0].date()), hi="2026-12-31"))
    gaps = _market(inside, sessions="calendar")["pit_gaps"]
    assert not any("chỉ phủ" in g for g in gaps)
    gaps = _market(_home(tmp_path / "out"), sessions="calendar")["pit_gaps"]
    assert any("chỉ phủ 2026-01-01 – 2026-12-31" in g for g in gaps)


# ---------- pit_label ---------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("research_input", ["legacy", "verified"])
@pytest.mark.parametrize("universe", ["config", "historical"])
@pytest.mark.parametrize("sessions", ["keep", "calendar"])
def test_pit_label_for_each_combination(tmp_path, research_input, universe, sessions):
    mk = _market(_home(tmp_path), research_input=research_input, universe=universe, sessions=sessions)
    if (research_input, universe, sessions) == ("verified", "historical", "calendar"):
        assert mk["pit_label"] == "POINT_IN_TIME"
        assert mk["pit_from"] == str(IDX[20].date())                 # ngày hiệu lực đầu tiên của data/vn30_history.csv
    else:
        assert mk["pit_label"] == "RETROSPECTIVE" and "pit_from" not in mk
        assert mk["pit_gaps"]


def test_derivation_id_carries_the_session_mode_and_the_calendar(tmp_path):
    home = _home(tmp_path)
    keep, cal = _market(home), _market(home, sessions="calendar")
    assert keep["derivation_id"] != cal["derivation_id"]
    p = home / "data" / "trading_calendar.csv"
    p.write_text(p.read_text(encoding="utf-8").replace("HOSE_DEFAULT", "HOSE_DEFAULT2"), encoding="utf-8")
    assert _market(home)["derivation_id"] == keep["derivation_id"]                 # keep: khóa cũ, không đọc sha lịch
    assert _market(home, sessions="calendar")["derivation_id"] != cal["derivation_id"]


def test_rejects_an_unknown_session_mode(tmp_path):
    with pytest.raises(ValueError, match="sessions"):
        _market(_home(tmp_path), sessions="hose")


# ---------- vòng học: khóa mới không vào tệp đầu ra ---------------------------------------------------------------------

DRIVER = textwrap.dedent('''
    import datetime as _dt, json, sys
    from unittest import mock
    from engine import data, research, run_cycle
    class FixedDT(_dt.datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 1, 2, 3, 4, 5, tzinfo=tz)
    patches = [mock.patch.object(research, "datetime", FixedDT)]
    if sys.argv[1] == "empty":
        empty = {"calendar": [], "zero_volume": [], "unannounced": [], "coverage": None}
        patches.append(mock.patch.object(data, "non_session_days", lambda *a, **k: empty))
    for p in patches:
        p.start()
    seen = {}
    orig = data.load_market
    def spy(*a, **k):
        mk = orig(*a, **k)
        seen.update(mk["quality"]["sessions"])
        return mk
    data.load_market = spy
    sys.argv = ["engine.run_cycle", "--source", "store", "--mode", "ops", "--no-llm"]
    run_cycle.main()
    print("SESSIONS=" + json.dumps(seen))
''')


def _env(home):
    drop = ("TTC_HOME", "TTC_REGISTRY_PUSH", "TTC_PROVENANCE_ONLINE", "GITHUB_TOKEN", "ANTHROPIC_API_KEY",
            "GITHUB_REPOSITORY", "GIT_DIR", "GIT_WORK_TREE")
    e = {k: v for k, v in os.environ.items() if k not in drop}
    e.update({"TTC_HOME": str(home), "PYTHONHASHSEED": "0"})
    return e


def _drop_key(x, key):
    if isinstance(x, dict):
        return {k: _drop_key(v, key) for k, v in x.items() if k != key}
    if isinstance(x, list):
        return [_drop_key(v, key) for v in x]
    return x


def _files(home):
    """Mọi tệp đầu ra; bỏ dấu thời gian trong đầu gzip và khóa generated_at của reports/scorecard.json (giờ sinh tệp)."""
    out = {}
    for p in sorted(home.rglob("*")):
        if p.is_file():
            rel, b = p.relative_to(home).as_posix(), p.read_bytes()
            if rel.endswith(".gz"):
                b = gzip.decompress(b)
            if rel == "reports/scorecard.json":
                b = json.dumps(_drop_key(json.loads(b), "generated_at"), sort_keys=True, ensure_ascii=False).encode()
            out[rel] = b
    return out


def test_cycle_outputs_in_keep_mode_do_not_change_when_non_sessions_exist(tmp_path):
    """Kho tổng hợp có 5 ngày mọi mã khối lượng 0. Vòng học (ops) chạy hai lần trên hai bản sao: một lần bình thường (5 ngày
    được liệt kê ở quality.sessions), một lần phép tìm ngày không phải phiên trả rỗng. Mọi tệp đầu ra, kể cả
    state/ENGINE_STATE.json và báo cáo phiên, giống từng byte."""
    src = tmp_path / "src"
    src.mkdir()
    with patch.object(config, "ROOT", src):
        from engine.synthetic import make_store
        make_store(n_days=420)
    s = data.load_store(root=src)
    days = sorted(s["date"].unique())
    ghost = [days[i] for i in (200, 201, 202, 300, 301)]
    s.loc[s["date"].isin(ghost), "volume"] = 0.0
    homes = []
    for name in ("normal", "empty"):
        h = tmp_path / name
        h.mkdir()
        shutil.copy(REPO / "config.yaml", h / "config.yaml")
        assert data.save_store(s, root=h) == len(s)
        homes.append(h)
    seen = {}
    for h, mode in zip(homes, ("normal", "empty")):
        r = subprocess.run([sys.executable, "-c", DRIVER, mode], cwd=str(REPO), env=_env(h), capture_output=True, text=True)
        assert r.returncode == 0, r.stdout + r.stderr
        seen[mode] = json.loads(next(x for x in r.stdout.splitlines() if x.startswith("SESSIONS="))[len("SESSIONS="):])
    assert seen["normal"]["non_session_zero_volume"] == _iso(ghost) and seen["empty"]["non_session_zero_volume"] == []
    a, b = _files(homes[0]), _files(homes[1])
    assert set(a) == set(b) and "state/ENGINE_STATE.json" in a
    assert sorted(k for k in a if a[k] != b[k]) == []
    st = json.loads(a["state/ENGINE_STATE.json"])
    assert "sessions" not in st["data_quality"]
