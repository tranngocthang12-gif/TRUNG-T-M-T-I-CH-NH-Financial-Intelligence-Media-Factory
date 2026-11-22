"""E2c (QĐ-1 của ADR-0016): trục phiên của đầu vào nghiên cứu — `load_market(..., sessions="keep"|"calendar")`.

«Có giá» của một ngày: ít nhất một thành viên rổ có dòng giá với khối lượng > 0 (QĐ-11a; Owner xác nhận 22/11/2026).
Ngày không phải phiên (data.non_session_days):
  - trong vùng data/trading_calendar.csv phủ: ngày lịch ghi is_session=0; ngày lịch ghi CHUA_CO_THONG_BAO mà không có giá;
  - ngoài vùng đó, hoặc khi không có tệp lịch: ngày không có giá;
  - lịch hỏng: lỗi ở cả hai chế độ.
Phiên chính thức (is_session=1, nguồn HOSE hoặc HOSE_DEFAULT) không có giá vẫn là phiên: liệt kê ở missing_sessions; chế độ
"calendar" thêm vào trục (giá NaN) ngày kho không có dòng nào.
"keep" (mặc định) giữ trục ngày và chỉ liệt kê ở `quality.sessions`; khóa này không vào ENGINE_STATE, nên đầu ra vòng học
không đổi. "calendar" dựng trục phiên trước mọi phép tính: kết quả bằng đúng kết quả của một kho không có các dòng bị bỏ.
pit_label = PIT_MODES_ONLY chỉ khi research_input="verified", universe "historical", sessions="calendar" và có tệp lịch đọc
được; không trường hợp nào trả POINT_IN_TIME (Owner xác nhận 22/11/2026).

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
X = "ZZZ"                                                   # mã trong kho, không thuộc rổ (không thuộc universe)
OBS = "2026-10-12"
NONE = pd.DataFrame(columns=adjust.EV_COLS)
COV = ("2026-01-01", "2026-12-31")                          # vùng lịch giả phủ
T = pd.Timestamp
HOL = [T("2026-01-01"), T("2026-01-02"), T("2026-02-16"), T("2026-02-17"), T("2026-02-18")]   # lịch nghỉ, khối lượng 0
CALV = T("2026-04-30")                                      # lịch nghỉ nhưng kho có khối lượng > 0
ZS = T("2026-03-10")                                        # phiên chính thức, mọi mã khối lượng 0: thiếu giá, vẫn là phiên
MISS = T("2026-05-20")                                      # phiên chính thức, kho không có dòng nào: thiếu giá, vẫn là phiên
ZV = [IDX[40], IDX[41], IDX[42]]                            # 2025-04-28…30: ngoài vùng lịch, mọi mã khối lượng 0
ZM = IDX[60]                                                # 2025-05-26: 2 mã khối lượng 0, 2 mã không có dòng
PZ = IDX[75]                                                # 2025-06-16: chỉ 2 trong 4 mã khối lượng 0
NM = IDX[90]                                                # 2025-07-07: thành viên rổ khối lượng 0, chỉ ZZZ giao dịch
UNANN = T("2026-06-01")                                     # CHUA_CO_THONG_BAO, có giá: là phiên
UNANN_NT = T("2026-07-01")                                  # CHUA_CO_THONG_BAO, mọi mã khối lượng 0: không phải phiên
UNANN_NR = T("2026-08-03")                                  # CHUA_CO_THONG_BAO, kho không có dòng: không lên trục
UNANN_OUT = T("2026-12-28")                                 # CHUA_CO_THONG_BAO, sau ngày cuối của dữ liệu
UNANN_ALL = (UNANN, UNANN_NT, UNANN_NR, UNANN_OUT)
CAL_OFF = sorted(HOL + [CALV])
VOL_OFF = sorted(ZV + [ZM, NM])
OFF = sorted(CAL_OFF + [UNANN_NT] + VOL_OFF)
MISSING = [ZS, MISS]
NO_ROWS = {MISS, UNANN_NR}
KEYS = ("close", "volume", "raw_close", "bad", "events", "flags")


def _iso(days):
    return [str(pd.Timestamp(d).date()) for d in days]


def _prices(seed=11):
    rng = np.random.default_rng(seed)
    cols = U + [X]
    r = rng.normal(0.0, 0.012, size=(len(IDX), len(cols))).clip(-0.05, 0.05)
    close = pd.DataFrame(20000.0 * np.cumprod(1 + r, axis=0), index=IDX, columns=cols).round(-1)
    vol = pd.DataFrame(1e6, index=IDX, columns=cols)
    for d in HOL + ZV + [ZS, ZM, NM, UNANN_NT]:             # ngày nghỉ: giá giữ nguyên phiên trước, khối lượng 0
        close.loc[d] = close.iloc[IDX.get_loc(d) - 1].values
        vol.loc[d] = 0.0
    vol.loc[NM, X] = 1e6                                    # chỉ mã ngoài rổ giao dịch
    vol.loc[PZ, U[:2]] = 0.0
    close.loc[ZM, U[2:]] = np.nan                           # hai mã không có dòng ngày ZM
    close.loc[list(NO_ROWS)] = np.nan                       # kho không có dòng nào
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


def _calendar(off=CAL_OFF, unann=UNANN_ALL, lo=COV[0], hi=COV[1]):
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
                 "non_session_unannounced": _iso([UNANN_NT]), "non_session_zero_volume": _iso(VOL_OFF),
                 "missing_sessions": _iso(MISSING), "inserted": [], "dropped": 0,
                 "unannounced": _iso([UNANN, UNANN_NT, UNANN_NR])}
    assert str(PZ.date()) not in json.dumps(q) and str(UNANN.date()) not in json.dumps(q["missing_sessions"])
    assert MISS not in mk["close"].index                                  # keep: trục giữ nguyên, chỉ liệt kê
    assert "trục ngày chưa lọc ngày nghỉ theo lịch phiên HOSE" in mk["pit_gaps"]


def test_keep_changes_nothing_but_the_session_report(tmp_path):
    """Cùng kho: mọi khóa trả về (kể cả quality trừ `sessions`, derivation_id, pit_gaps) giống từng byte với lượt mà phép tìm
    ngày không phải phiên không tìm thấy ngày nào (giữ nguyên vùng lịch phủ)."""
    home = _home(tmp_path, manual=_manual(IDX[50]))
    real = data.non_session_days

    def empty(*a, **k):
        r = real(*a, **k)
        return {**{key: [] for key in r if key != "coverage"}, "coverage": r["coverage"]}
    for kw in ({}, {"research_input": "verified"}, {"universe": "historical"}):
        a = _market(home, **kw)
        with patch.object(data, "non_session_days", empty):
            b = _market(home, **kw)
        assert set(a) == set(b)
        a["quality"].pop("sessions"), b["quality"].pop("sessions")
        for k in a:
            assert _h(a[k]) == _h(b[k]), (kw, k)


# ---------- calendar ----------------------------------------------------------------------------------------------------

def test_calendar_drops_non_sessions_and_keeps_every_official_session(tmp_path):
    home = _home(tmp_path)
    mk = _market(home, sessions="calendar")
    axis = list(mk["close"].index)
    assert axis == sorted([d for d in _store_dates(home) if d not in set(OFF)] + [MISS])
    assert {ZS, MISS, PZ, UNANN} <= set(axis) and UNANN_NR not in axis     # phiên thiếu giá ở lại; có giá thì là phiên
    assert not set(OFF) & set(axis)
    assert mk["raw_close"].loc[MISS].isna().all() and (mk["volume"].loc[MISS] == 0).all()
    q = mk["quality"]["sessions"]
    assert (q["mode"], q["dropped"], q["inserted"], q["missing_sessions"]) == ("calendar", len(OFF), _iso([MISS]),
                                                                               _iso(MISSING))
    assert (q["non_session_calendar"], q["non_session_unannounced"], q["non_session_zero_volume"]) == \
        (_iso(CAL_OFF), _iso([UNANN_NT]), _iso(VOL_OFF))
    assert any("2 phiên chính thức" in g and str(MISS.date()) in g for g in mk["pit_gaps"])
    assert X not in mk["close"].columns                                  # mã ngoài rổ không làm NM thành phiên


def test_historical_basket_before_the_first_effective_date_uses_the_table_tickers(tmp_path):
    mk = _market(_home(tmp_path), universe="historical", sessions="calendar")
    axis = set(mk["close"].index)
    assert set(IDX[:20]) <= axis                                         # trước ngày hiệu lực đầu tiên vẫn có phiên
    assert not set(ZV) & axis and NM not in axis


@pytest.mark.parametrize("kw", [{}, {"research_input": "verified"}, {"universe": "historical"},
                                {"research_input": "verified", "universe": "historical"}])
def test_calendar_equals_a_store_without_those_rows(tmp_path, kw):
    """Bỏ TRƯỚC khi tính hệ số, mặt nạ cửa sổ QĐ-3 và báo cáo chất lượng: kết quả bằng đúng kho không có các dòng đó. Sự kiện
    cách ly ở IDX[50] có cửa sổ −21/+120 phiên phủ ba ngày ZV và ngày ZM, nên cửa sổ đếm trên trục đã bỏ."""
    ev = _manual(IDX[50])
    a = _market(_home(tmp_path / "a", manual=ev), sessions="calendar", **kw)
    b = _market(_home(tmp_path / "b", manual=ev, skip=set(OFF)), sessions="calendar", **kw)   # chỉ còn thêm MISS
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


def test_an_official_session_without_rows_counts_in_the_quarantine_window(tmp_path):
    """MISS (phiên chính thức, kho không có dòng) nằm trong 21 phiên trước sự kiện cách ly EV2: cửa sổ QĐ-3 đếm cả MISS."""
    ev2 = T("2026-06-08")
    mk = _market(_home(tmp_path, manual=_manual(ev2)), research_input="verified", sessions="calendar")
    official = sorted((set(_store_dates(tmp_path)) - set(OFF)) | {MISS})   # trục phiên dựng độc lập với mã
    before, _ = data.window_bounds()
    first = official[official.index(ev2) - before]
    x = mk["exclude"][U[0]]
    assert MISS in x.index and x.loc[MISS] and first < MISS
    assert x[x].index[0] == first


def test_without_a_calendar_file_the_zero_volume_rule_covers_every_day(tmp_path):
    home = _home(tmp_path, calendar=False)
    mk = _market(home, sessions="calendar")
    zero = sorted(HOL + ZV + [ZS, ZM, NM, UNANN_NT])                 # CALV có khối lượng: không bỏ
    q = mk["quality"]["sessions"]
    assert (q["calendar_coverage"], q["non_session_calendar"], q["non_session_zero_volume"], q["unannounced"],
            q["missing_sessions"], q["inserted"]) == (None, [], _iso(zero), [], [], [])
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
    assert mk["quality"]["sessions"]["unannounced"] == _iso([UNANN, UNANN_NT, UNANN_NR])              # UNANN_OUT ngoài dữ liệu
    assert any(data.UNANNOUNCED in g and g.startswith("3 ngày") for g in mk["pit_gaps"])


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
        assert mk["pit_label"] == "PIT_MODES_ONLY"
        assert mk["pit_from"] == str(IDX[20].date())                 # ngày hiệu lực đầu tiên của data/vn30_history.csv
    else:
        assert mk["pit_label"] == "RETROSPECTIVE" and "pit_from" not in mk
    for g in data.PIT_EVIDENCE_GAPS:                                   # giá không có vintage; PIT-001 NOT_READY
        assert g in mk["pit_gaps"]
    assert any("ADR-0009 mục 4" in g for g in mk["pit_gaps"]) and any("PIT-001 NOT_READY" in g for g in mk["pit_gaps"])


def test_three_modes_without_a_calendar_file_are_retrospective(tmp_path):
    mk = _market(_home(tmp_path, calendar=False), research_input="verified", universe="historical", sessions="calendar")
    assert mk["pit_label"] == "RETROSPECTIVE" and "pit_from" not in mk
    assert any("không có data/trading_calendar.csv" in g for g in mk["pit_gaps"])


def test_no_code_returns_point_in_time():
    assert data.PIT_MODES_ONLY == "PIT_MODES_ONLY"
    src = (REPO / "engine" / "data.py").read_text(encoding="utf-8")
    assert 'pit_label="POINT_IN_TIME"' not in src and '= "POINT_IN_TIME"' not in src


def test_derivation_id_carries_the_session_mode_and_the_calendar(tmp_path):
    home = _home(tmp_path)
    keep, cal = _market(home), _market(home, sessions="calendar")
    assert keep["derivation_id"] != cal["derivation_id"]
    p = home / "data" / "trading_calendar.csv"
    p.write_text(p.read_text(encoding="utf-8").replace("HOSE_DEFAULT", "HOSE_DEFAULT2"), encoding="utf-8")
    assert _market(home)["derivation_id"] == keep["derivation_id"]                 # keep: khóa cũ, không đọc sha lịch
    cal2 = _market(home, sessions="calendar")["derivation_id"]
    assert cal2 != cal["derivation_id"]
    (tmp_path / "code").mkdir()
    code = tmp_path / "code" / "risk_gate.py"                      # mã đọc lịch đổi → id của chế độ calendar đổi
    code.write_bytes((REPO / "engine" / "risk_gate.py").read_bytes())
    with patch.object(data, "CALENDAR_CODE_FILES", (code,)):
        assert _market(home, sessions="calendar")["derivation_id"] == cal2
        code.write_text(code.read_text(encoding="utf-8") + "\n# đổi\n", encoding="utf-8")
        assert _market(home, sessions="calendar")["derivation_id"] != cal2
        assert _market(home)["derivation_id"] == keep["derivation_id"]          # keep không phụ thuộc mã đọc lịch


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
        empty = {"calendar": [], "unannounced_no_price": [], "zero_volume": [], "missing": [], "unannounced": [],
                 "coverage": None}
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
