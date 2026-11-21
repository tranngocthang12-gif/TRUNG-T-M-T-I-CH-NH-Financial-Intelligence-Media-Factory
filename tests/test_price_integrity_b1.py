"""PRICE-INTEGRITY B1 (21/11/2026): tái lập lỗi đường giá TCB/VCB trên fixture độc lập và kiểm thử đối kháng fail-closed.

Không mạng, không ghi vào kho. Fixture tổng hợp ghi vào tmp_path; phần D chỉ ĐỌC kho giá thật đã đóng băng (ADR-0006) để
tái lập số đo trong reports/PRICE_INTEGRITY_B1_20261121.md. Không xác minh sự kiện thật nào; không nâng source_status.

A. Cơ chế: nguồn giá chỉ điều chỉnh MỘT PHẦN (W phiên liền trước ngày không hưởng quyền), sự kiện nhập tay chưa đối chiếu
   đặt ở ngày chuỗi gãy (không phải ngày chính thức) che chỗ gãy. Đo ba phương án: giữ, bỏ, dời ngày.
B. Cổng verified-adjusted: DA_NAM_TRONG_GIA_NGUON không được chứng nhận khi còn bước gãy trước sự kiện (bản vá cùng PR).
C. Điều kiện PASS của PIT-001 viết thành test hành vi. Đánh dấu xfail(strict=True): engine CHƯA đạt; khi một PR engine được
   Owner duyệt (ADR-0009 điều 7, L-09, L-10) làm đạt, test chuyển XPASS và CI đỏ, buộc gỡ xfail — không âm thầm qua cổng.
   C1, C2 kiểm chế độ đầu vào đã kiểm chạy song song (research_input="verified"), không đòi đổi đường mặc định.
D. Bằng chứng trên kho thật: dấu hiệu điều chỉnh một phần của TCB 2024 và VCB 2025, chỉ đọc."""
from __future__ import annotations

import hashlib
import inspect
import json
import pathlib
import sys
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from engine import adjust, config, data, features, verified_adjust as va   # noqa: E402

IDX = pd.bdate_range("2023-01-02", periods=420)
OFF = 300                 # phiên không hưởng quyền chính thức trong fixture
W = 7                     # số phiên nguồn đã chia sẵn trước ngày đó (khớp kho thật TCB/VCB)
R = 2.0
TICKERS = ["AAA", "BBB", "CCC", "DDD"]
OBS = "2026-09-26"        # quan sát sau mọi ngày giá (như lần tải lô của kho thật)
H = config.CFG["horizon_days"]
LOOKBACK = config.CFG["quality"]["feature_lookback"]


def _walk(seed=7):
    rng = np.random.default_rng(seed)
    r = rng.normal(0.0, 0.012, size=(len(IDX), len(TICKERS))).clip(-0.05, 0.05)
    return pd.DataFrame(100.0 * np.cumprod(1 + r, axis=0), index=IDX, columns=TICKERS)


def _true_raw():
    """Giá gốc đúng: AAA rơi theo tỷ lệ R tại phiên chính thức."""
    c = _walk()
    c.iloc[OFF:, 0] = c.iloc[OFF:, 0] / R
    return c


def _partial(c=None, w=W):
    """Nguồn điều chỉnh một phần: chỉ w phiên liền trước phiên chính thức đã chia cho R."""
    c = _true_raw() if c is None else c.copy()
    c.iloc[OFF - w:OFF, 0] = c.iloc[OFF - w:OFF, 0] / R
    return c


def _obs(c):
    return pd.DataFrame(pd.Timestamp(OBS), index=c.index, columns=c.columns)


def _ev(rows):
    return pd.DataFrame([{"ticker": "AAA", "cash_per_share": np.nan, "note": "", **r} for r in rows], columns=adjust.EV_COLS)


def _manual(at, ratio=R, status="CAN_DOI_CHIEU"):
    return _ev([{"ex_date": at, "type": "stock_dividend", "ratio": ratio, "source": "manual (fixture)", "source_status": status}])


def _yahoo(at=None, ratio=R):
    return _ev([{"ex_date": IDX[OFF] if at is None else at, "type": "stock_split", "ratio": ratio, "source": "yahoo",
                 "source_status": "TU_DONG"}])


NONE = pd.DataFrame(columns=adjust.EV_COLS)


def _doc(tmp_path, ratio=R, typ="stock_split"):
    rel = "data/evidence/corporate_actions/fx-1/ban_goc.pdf"
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    b = b"%PDF-1.4 ban goc gia lap (fixture)"
    p.write_bytes(b)
    return {"source_id": "fx-1", "url": "https://example.invalid/fx-1.pdf", "issuer": "So giao dich (gia lap)", "path": rel,
            "sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b), "ticker": "AAA", "event_type": typ,
            "official_ex_date": str(IDX[OFF].date()), "published_at": str((IDX[OFF] - pd.Timedelta(days=8)).date()),
            "official_ratio": ratio}


def _chain(close, manual, yahoo):
    ev = adjust.build_events(close, _obs(close), manual, yahoo)
    F, _ = adjust.factors(close.index, close.columns, ev)
    adj = close * F
    bad, _, flags = adjust.quality(adj)
    return ev, adj, bad, flags


def _status(ev, at):
    return ev.loc[pd.to_datetime(ev.ex_date) == pd.Timestamp(at), "status"].tolist()


# ---------- A. cơ chế TCB/VCB và ba phương án -----------------------------------------------------------------------

def test_a1_unverified_event_at_source_break_patches_partial_window_not_a_corporate_action_date():
    """P0 hiện hành: sự kiện CAN_DOI_CHIEU đặt ở ngày chuỗi gãy (W phiên trước ngày chính thức) được APPLIED; chuỗi điều chỉnh
    liền mạch và không có cờ lỗi. Nó vá lỗi nguồn, không phải ngày sự kiện quyền: ngày áp khác ngày chính thức W phiên."""
    close = _partial()
    ev, adj, _, flags = _chain(close, _manual(IDX[OFF - W]), _yahoo())
    assert _status(ev, IDX[OFF - W]) == ["APPLIED"]
    assert _status(ev, IDX[OFF]) == ["DA_NAM_TRONG_GIA_NGUON"]          # engine tin nguồn đã điều chỉnh toàn bộ lịch sử
    assert not [f for f in flags if f["ticker"] == "AAA"]
    truth = _walk().pct_change()                                          # lợi suất đúng của chuỗi đã điều chỉnh
    assert np.allclose(adj.pct_change().values[1:], truth.values[1:], atol=1e-12)
    applied = ev.loc[ev.status == "APPLIED", "trade_date"].iloc[0]
    assert IDX.get_loc(IDX[OFF]) - IDX.get_loc(applied) == W


def test_a2_dropping_unverified_event_exposes_break_and_quality_gate_masks_features_and_labels():
    """P1 (bỏ sự kiện chưa xác minh): bước gãy nguồn lộ ra, bị cờ lỗi; feature AAA bị loại trong cửa sổ nhìn lại, nhãn có cửa
    sổ nắm giữ chứa bước gãy bị loại. Không có giá trị nhãn nào mang lợi suất −50% giả."""
    close = _partial()
    ev, adj, bad, flags = _chain(close, NONE, _yahoo())
    b = OFF - W
    aaa = [f for f in flags if f["ticker"] == "AAA"]
    assert [f["date"] for f in aaa] == [str(IDX[b].date())] and aaa[0]["return"] == pytest.approx(-0.5, abs=0.02)
    ds = features.dataset(adj, pd.DataFrame(1e6, index=IDX, columns=TICKERS), H, bad)
    f = ds.xs("AAA", level=1)
    fcols = list(features.FEATURES)
    assert f.loc[IDX[b]:IDX[min(b + LOOKBACK - 1, len(IDX) - 1)], fcols].isna().all().all()
    crossing = IDX[b - 1 - H: b - 1]                                     # nhãn t dùng (t+1, t+1+H]: chứa phiên gãy
    assert f.loc[crossing, "y"].isna().all()
    assert (f["y"].dropna().abs() < 0.4).all()


def test_a3_redating_unverified_event_to_official_date_without_explaining_source_is_not_applied():
    """P2 (dời ngày sang ngày chính thức, vẫn chưa xác minh): tại ngày chính thức giá gốc liên tục nên nhân tỷ lệ thành +100%:
    KHONG_KHOP, không áp; bước gãy nguồn vẫn còn và bị cờ. Kết quả giống hệt P1 — dời ngày không sửa được lỗi nguồn."""
    close = _partial()
    ev2, adj2, _, flags2 = _chain(close, _manual(IDX[OFF]), _yahoo())
    _, adj1, _, flags1 = _chain(close, NONE, _yahoo())
    assert "KHONG_KHOP" in _status(ev2, IDX[OFF])
    assert flags2 == flags1 and adj2.equals(adj1)


def test_a4_unverified_ratio_error_inside_price_band_is_applied_silently():
    """Rủi ro thật của sự kiện chưa xác minh: sai tỷ lệ 5% (1,9 thay vì 2,0) vẫn APPLIED vì bước giá sau điều chỉnh còn trong
    biên ±7,3%; không cờ lỗi; lợi suất qua sự kiện lệch ~5 điểm phần trăm. Cổng chất lượng không bắt được loại lỗi này."""
    close = _true_raw()
    ev, adj, _, flags = _chain(close, _manual(IDX[OFF], ratio=1.9), NONE)
    assert _status(ev, IDX[OFF]) == ["APPLIED"]
    assert not [f for f in flags if f["ticker"] == "AAA"]
    a, b = IDX[OFF - 5], IDX[OFF + 5]
    truth = _walk()["AAA"]
    err = adj.at[b, "AAA"] / adj.at[a, "AAA"] - truth[b] / truth[a]
    assert err == pytest.approx(-0.05 * truth[b] / truth[a], rel=0.05) and abs(err) > 0.04


# ---------- B. cổng verified-adjusted: điều chỉnh một phần ------------------------------------------------------------

def test_b1_already_in_price_with_partial_window_is_quarantined(tmp_path):
    """Trước bản vá: DA_KIEM_CHUNG, vào chuỗi kiểm chứng, không nhiễm ô, dù chuỗi còn bước −50% 7 phiên trước sự kiện."""
    close = _partial()
    ev = adjust.build_events(close, _obs(close), NONE, _yahoo())
    v = va.verify_events(ev, close, [_doc(tmp_path)], evidence_root=tmp_path, as_of=IDX[-1])
    r = v.iloc[0]
    assert r.verify_state == va.Q + "GIA_GAY_TRUOC_NGAY_HUONG_QUYEN", r.verify_reason
    assert f"{W} phiên trước" in r.verify_reason and "một phần" in r.verify_reason
    assert not r.in_verified_chain and r.taints
    m = va.taint_mask(close.index, close.columns, v)
    assert m["AAA"].iloc[:OFF].all() and not m["AAA"].iloc[OFF:].any() and not m[TICKERS[1:]].values.any()


def test_b2_already_in_price_with_clean_history_still_verifies(tmp_path):
    """Không quá tay: nguồn điều chỉnh toàn bộ (chuỗi liền mạch, dao động thường trong biên) → vẫn DA_KIEM_CHUNG."""
    close = _walk()
    ev = adjust.build_events(close, _obs(close), NONE, _yahoo())
    v = va.verify_events(ev, close, [_doc(tmp_path)], evidence_root=tmp_path, as_of=IDX[-1])
    assert v.verify_state.tolist() == [va.OK] and v.in_verified_chain.all() and not v.taints.any()


def test_b3_pre_event_break_not_explained_by_ratio_is_also_quarantined(tmp_path):
    close = _walk()
    close.iloc[OFF - 4:, 0] = close.iloc[OFF - 4:, 0] * 0.7               # lỗi dữ liệu −30% bốn phiên trước sự kiện
    ev = adjust.build_events(close, _obs(close), NONE, _yahoo())
    v = va.verify_events(ev, close, [_doc(tmp_path)], evidence_root=tmp_path, as_of=IDX[-1])
    assert v.verify_state.tolist() == [va.Q + "GIA_GAY_TRUOC_NGAY_HUONG_QUYEN"]
    assert "nhân tỷ lệ vẫn ngoài biên" in v.verify_reason.iloc[0]


def test_b4_break_outside_window_is_left_to_the_quality_gate(tmp_path):
    """Phạm vi cổng là WINDOW_DAYS ngày lịch. Bước gãy xa hơn không chặn chứng nhận sự kiện, nhưng lớp kiểm chất lượng vẫn cờ
    nó trên chuỗi kiểm chứng (phòng thủ hai lớp)."""
    close = _walk()
    far = OFF - 60
    assert (IDX[OFF] - IDX[far]).days > va.WINDOW_DAYS
    close.iloc[far:, 0] = close.iloc[far:, 0] * 0.7
    ev = adjust.build_events(close, _obs(close), NONE, _yahoo())
    v = va.verify_events(ev, close, [_doc(tmp_path)], evidence_root=tmp_path, as_of=IDX[-1])
    assert v.verify_state.tolist() == [va.OK]
    Fv, _ = va.verified_factors(close.index, close.columns, v)
    _, _, flags = adjust.quality(close * Fv)
    assert [f["date"] for f in flags if f["ticker"] == "AAA"] == [str(IDX[far].date())]


def test_b5_real_pair_manual_plus_yahoo_never_enters_verified_chain(tmp_path):
    """Đúng cặp của kho thật: sự kiện tay ở ngày gãy + sự kiện Yahoo ở ngày chính thức, cùng một bản gốc. Không bên nào vào
    chuỗi kiểm chứng; mọi ô AAA trước ngày chính thức bị nhiễm."""
    close = _partial()
    ev = adjust.build_events(close, _obs(close), _manual(IDX[OFF - W]), _yahoo())
    v = va.verify_events(ev, close, [_doc(tmp_path)], evidence_root=tmp_path, as_of=IDX[-1])
    assert not v.in_verified_chain.any() and v.verify_state.str.startswith(va.Q).all()
    assert va.taint_mask(close.index, close.columns, v)["AAA"].iloc[:OFF].all()


# ---------- C. điều kiện PASS của PIT-001 dưới dạng test hành vi (engine chưa đạt) -------------------------------------

def _rows(close, vol=None, observed=OBS):
    vol = pd.DataFrame(1e6, index=close.index, columns=close.columns) if vol is None else vol
    out = []
    for d in close.index:
        for t in close.columns:
            p = close.at[d, t]
            if pd.notna(p):
                out.append({"date": d.strftime("%Y-%m-%d"), "ticker": t, "open": p, "high": p, "low": p, "close": p,
                            "volume": float(vol.at[d, t]), "observed_at": observed, "source": "fixture"})
    return pd.DataFrame(out, columns=data.COLS)


def _home(tmp_path, close, manual=None, vol=None, extra=None):
    assert data.save_store(_rows(close, vol), root=tmp_path) > 0
    for key, df in (("manual", NONE if manual is None else manual), ("yahoo_cache", NONE)):
        p = tmp_path / config.CFG["corporate_actions"][key]
        p.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(p, index=False)
    for rel, text in (extra or {}).items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(text, encoding="utf-8")
    return tmp_path


def _market(home, as_of=None, cfg=None, **kw):
    with patch.object(config, "ROOT", home), patch.object(adjust, "ROOT", home), patch.dict(config.CFG, cfg or {}):
        return data.load_market(as_of, **kw)


def _verified_market(home, as_of=None):
    """Đầu vào nghiên cứu ở chế độ đã kiểm, chạy SONG SONG với đường mặc định. Test không đòi đổi đường mặc định: chọn
    phương án (A)/(B)/(C) ở reports/PRICE_INTEGRITY_B1_20261121.md mục 5 là quyết định của Owner."""
    assert "research_input" in inspect.signature(data.load_market).parameters, \
        "load_market chưa có tham số research_input (chế độ 'verified')"
    return _market(home, as_of, research_input="verified")


XF = dict(strict=True, raises=AssertionError)


@pytest.mark.xfail(reason="UNVERIFIED_EVENTS_IN_RESEARCH_CHAIN: chưa có chế độ đầu vào đã kiểm load_market(research_input="
                          "'verified'); không đòi đổi mặc định, Owner chọn A/B/C (ADR-0009 điều 7)", **XF)
def test_c1_verified_research_input_rejects_unverified_corporate_event(tmp_path):
    home = _home(tmp_path, _true_raw(), manual=_manual(IDX[OFF], ratio=1.9))
    mk = _verified_market(home)
    assert "APPLIED" not in _status(mk["events"], IDX[OFF])


@pytest.mark.xfail(reason="DECISION_TIME_OF_KNOWLEDGE: chế độ đầu vào đã kiểm chưa có, nên chưa có nơi đọc ngày công bố "
                          "của sự kiện quyền; không đòi đổi mặc định", **XF)
def test_c2_verified_research_input_ignores_event_published_after_decision_date(tmp_path):
    m = _manual(IDX[OFF], status="DA_KIEM_CHUNG").assign(published_at=str(IDX[-1].date()))
    home = _home(tmp_path, _true_raw(), manual=m)
    mk = _verified_market(home, as_of=str(IDX[OFF + 30].date()))          # quyết định trước ngày công bố
    assert "APPLIED" not in _status(mk["events"], IDX[OFF])


@pytest.mark.xfail(reason="PRICE_WINDOW_COVERAGE: mã thiếu lịch sử bị loại im lặng khỏi panel (load_market keep > 250)", **XF)
def test_c3_ticker_dropped_for_short_history_is_reported(tmp_path):
    close = _walk()
    close["EEE"] = np.nan
    close.iloc[-200:, close.columns.get_loc("EEE")] = 50.0                # mã mới vào, 200 phiên
    mk = _market(_home(tmp_path, close))
    assert "EEE" in mk["close"].columns or "EEE" in json.dumps(mk["quality"], default=str)


@pytest.mark.xfail(reason="ENGINE_UNIVERSE_MODE: engine không đọc data/vn30_history.csv (ADR-0008, cần PR riêng)", **XF)
def test_c4_historical_universe_excludes_ticker_after_exit(tmp_path):
    rows = ["effective_date,ticker,action,source_id"] + [f"{IDX[0].date()},{t},ADD,fx" for t in TICKERS] + \
           [f"{IDX[350].date()},DDD,REMOVE,fx"]
    home = _home(tmp_path, _walk(), extra={"data/vn30_history.csv": "\n".join(rows) + "\n"})
    mk = _market(home, cfg={"universe_basis": "HISTORICAL"})
    assert mk["close"]["DDD"].loc[IDX[351]:].isna().all()


@pytest.mark.xfail(reason="Lịch phiên: ngày nghỉ có dòng giá (volume 0, giá không đổi) bị tính là phiên giao dịch", **XF)
def test_c5_non_trading_rows_are_not_counted_as_sessions(tmp_path):
    close, vol = _walk(), pd.DataFrame(1e6, index=IDX, columns=TICKERS)
    ghost = IDX[200:205]                                                  # năm ngày nghỉ lễ giả: giá giữ nguyên, volume 0
    close.loc[ghost] = close.loc[IDX[199]].values
    vol.loc[ghost] = 0.0
    mk = _market(_home(tmp_path, close, vol=vol))
    rep = json.dumps(mk["quality"], default=str)
    assert not set(ghost) & set(mk["close"].index) or str(ghost[0].date()) in rep


@pytest.mark.xfail(reason="ADR-0009 tiêu chí 5: đầu vào nghiên cứu chưa mang derivation_id và nhãn mức point-in-time", **XF)
def test_c6_research_input_carries_derivation_id_and_pit_label(tmp_path):
    mk = _market(_home(tmp_path, _walk()))
    assert mk.get("derivation_id") and mk.get("pit_label") in ("RETROSPECTIVE", "POINT_IN_TIME")


# ---------- D. bằng chứng trên kho thật, chỉ đọc --------------------------------------------------------------------

def _tick(p):
    return 10 if p < 10000 else (50 if p < 50000 else 100)


def _on_grid(x, step, tol=0.02):
    q = x / step
    return abs(q - round(q)) < tol


REAL = [("TCB", "hose-1705374", "EVIDENCE_MANIFEST.json"), ("VCB", "hose-1753594", "EVIDENCE_MANIFEST.json")]


def test_d1_real_store_shows_partial_window_seven_sessions_before_official_ex_date():
    """Kho thật (đóng băng, ADR-0006): giá gốc liên tục tại ngày không hưởng quyền chính thức ghi trên bản HOSE đã ghim, và có
    đúng một bước ngoài biên trong 45 ngày trước đó, ở 7 phiên trước, được tỷ lệ in trên văn bản giải thích. Không sửa tệp nào."""
    files = [REPO / config.CFG["data"]["store"], REPO / "data/evidence/corporate_actions/EVIDENCE_MANIFEST.json"]
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    s = data.load_store(root=REPO)
    raw = s.pivot(index="date", columns="ticker", values="close").sort_index()
    vol = s.pivot(index="date", columns="ticker", values="volume").sort_index()
    for t, sid, man in REAL:
        doc = next(d for d in json.loads((REPO / "data/evidence/corporate_actions" / man).read_text(encoding="utf-8"))
                   ["source_documents"] if d["source_id"] == sid)
        ratio, off = float(doc["official_ratio"]), pd.Timestamp(doc["official_ex_date"])
        x = raw[t].dropna()
        ret = x.pct_change()
        i = x.index.get_loc(off)
        assert abs(ret.iloc[i]) < 0.073, (t, ret.iloc[i])
        win = ret[(ret.index >= off - pd.Timedelta(days=45)) & (ret.index < off)]
        out = win[(win < -0.073) | (win > 0.073)]
        assert len(out) == 1, (t, out)
        d = out.index[0]
        assert i - x.index.get_loc(d) == 7
        assert abs((1 + out.iloc[0]) * ratio - 1) < 0.073
        if t == "VCB":                                                   # dấu hiệu số học: giá/khối lượng đã chia cho tỷ lệ
            w = x.iloc[i - 7:i]
            assert sum(_on_grid(p, _tick(p)) for p in w) == 0
            assert sum(_on_grid(p * ratio, _tick(p * ratio)) for p in w) == 7
            assert sum(_on_grid(v / ratio, 100) for v in vol[t].loc[w.index]) == 7
            assert sum(_on_grid(p, _tick(p)) for p in x.iloc[i - 27:i - 7]) == 20
    assert before == {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
