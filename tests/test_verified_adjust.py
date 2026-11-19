"""Cổng bằng chứng cho chuỗi 'verified-adjusted' (ADR-0009 điều 2, 3, 7), dữ liệu TỔNG HỢP, không mạng.

Chứng minh: (1) vì sao CAN_DOI_CHIEU vẫn thành APPLIED (nguyên nhân gốc, kiểm lại bằng test hồi quy); (2) sự kiện đủ bằng chứng
vào chuỗi kiểm chứng; (3) từng lý do bị cách ly; (4) cổng không đổi ngày hộ và không sửa chuỗi hiện hành; (5) công cụ dựng bản
dẫn xuất xác định, không sửa kho raw và từ chối ghi vào thư mục dữ liệu. Không xác minh sự kiện thật nào của TCB/VCB/FPT."""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from engine import adjust, verified_adjust as va   # noqa: E402

IDX = pd.bdate_range("2024-01-02", periods=300)
BRK = 200                                           # phiên chuỗi giá gốc gãy trong dữ liệu tổng hợp
AS_OF = IDX[-1]
RATIO = 2.0
EVCOLS = adjust.EV_COLS


def _close(break_idx=BRK, ratio=RATIO, tickers=("AAA",)):
    c = pd.DataFrame(100.0, index=IDX, columns=list(tickers))
    wob = np.where(np.arange(len(IDX)) % 2 == 0, 1.002, 0.998)       # dao động nhỏ, không phải đường phẳng
    c = c.mul(wob, axis=0)
    c.iloc[break_idx:] = c.iloc[break_idx:] / ratio
    return c


def _obs(close, when="2026-01-01"):
    return pd.DataFrame(pd.Timestamp(when), index=close.index, columns=close.columns)


def _ev(ticker, ex, typ="stock_dividend", ratio=RATIO, source="manual", status="CAN_DOI_CHIEU", cash=np.nan):
    return pd.DataFrame([{"ticker": ticker, "ex_date": pd.Timestamp(ex), "type": typ, "ratio": ratio, "cash_per_share": cash,
                          "source": source, "source_status": status, "note": ""}], columns=EVCOLS)


def _none():
    return pd.DataFrame(columns=EVCOLS)


def _doc(tmp_path, ticker="AAA", ex=None, ratio=RATIO, pub=None, sid="hose-test-1", content=b"%PDF-1.4 bien ban goc gia lap",
         typ="stock_dividend", **over):
    ex = pd.Timestamp(ex if ex is not None else IDX[BRK])
    pub = pd.Timestamp(pub if pub is not None else ex - pd.Timedelta(days=6))
    rel = f"data/evidence/corporate_actions/{sid}/ban_goc.pdf"
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(content)
    d = {"source_id": sid, "url": f"https://example.invalid/{sid}.pdf", "issuer": "Sở Giao dịch Chứng khoán (giả lập)",
         "published_at": str(pub.date()), "path": rel, "sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content),
         "ticker": ticker, "event_type": typ, "official_ex_date": str(ex.date()), "official_ratio": ratio}
    d.update(over)
    return {k: v for k, v in d.items() if v is not None}


def _run(tmp_path, manual, yahoo, docs, close=None, obs=None, as_of=AS_OF):
    close = _close() if close is None else close
    obs = _obs(close) if obs is None else obs
    events = adjust.build_events(close, obs, manual, yahoo)
    ev = va.verify_events(events, close, docs, evidence_root=tmp_path, as_of=as_of)
    return close, events, ev


# ---------- 1. nguyên nhân gốc ------------------------------------------------------------------------------------------

@pytest.mark.parametrize("status", ["CAN_DOI_CHIEU", "DA_KIEM_CHUNG", "TU_DONG", "CHUA_XAC_MINH"])
def test_root_cause_source_status_does_not_decide_applied(status):
    """Hồi quy: adjust.build_events bỏ qua `source_status`; chỉ biên độ giá quyết định APPLIED."""
    close = _close()
    events = adjust.build_events(close, _obs(close), _ev("AAA", IDX[BRK], status=status), _none())
    assert events.status.tolist() == ["APPLIED"]


# ---------- 2. đủ bằng chứng thì vào chuỗi kiểm chứng ------------------------------------------------------------------

def test_fully_evidenced_event_enters_verified_chain_with_same_factor(tmp_path):
    close, events, ev = _run(tmp_path, _ev("AAA", IDX[BRK]), _none(), [_doc(tmp_path)])
    r = ev.iloc[0]
    assert r.verify_state == va.OK and r.in_verified_chain and r.session_offset == 0
    Fv, _ = va.verified_factors(close.index, close.columns, ev)
    Fd, _ = adjust.factors(close.index, close.columns, events)
    assert np.allclose(Fv.values, Fd.values) and Fv.iloc[0, 0] == pytest.approx(1 / RATIO)
    assert not va.taint_mask(close.index, close.columns, ev).values.any()


def test_yahoo_already_adjusted_aligned_event_is_verified_without_factor(tmp_path):
    """Sự kiện Yahoo mà giá gốc đã chứa điều chỉnh (observed sau ngày hưởng quyền) và ngày khớp bản gốc: đã kiểm, không áp thêm hệ số."""
    close = _close(ratio=1.0)                                        # giá liên tục: nguồn đã điều chỉnh sẵn
    yahoo = _ev("AAA", IDX[BRK], source="yahoo", status="TU_DONG")
    events = adjust.build_events(close, _obs(close, "2030-01-01"), _none(), yahoo)
    assert events.status.tolist() == ["DA_NAM_TRONG_GIA_NGUON"]
    ev = va.verify_events(events, close, [_doc(tmp_path)], evidence_root=tmp_path, as_of=AS_OF)
    assert ev.verify_state.tolist() == [va.OK] and ev.in_verified_chain.tolist() == [True]
    Fv, _ = va.verified_factors(close.index, close.columns, ev)
    assert (Fv.values == 1.0).all() and not va.taint_mask(close.index, close.columns, ev).values.any()


# ---------- 3. từ chối ----------------------------------------------------------------------------------------------------

def test_no_evidence_is_quarantined_and_default_chain_unchanged(tmp_path):
    close, events, ev = _run(tmp_path, _ev("AAA", IDX[BRK]), _none(), [])
    assert ev.verify_state.tolist() == [va.Q + "THIEU_BANG_CHUNG"] and not ev.in_verified_chain.any()
    Fv, _ = va.verified_factors(close.index, close.columns, ev)
    assert (Fv.values == 1.0).all()                                      # không áp hệ số chưa kiểm
    m = va.taint_mask(close.index, close.columns, ev)
    assert m.iloc[:BRK].values.all() and not m.iloc[BRK:].values.any()   # ô TRƯỚC ngày giao dịch bị cách ly
    assert events.status.tolist() == ["APPLIED"]                         # chuỗi hiện hành không bị cổng đổi


def _tamper(tmp_path, d):
    (tmp_path / d["path"]).write_bytes(b"tep da bi sua")


def _tamper_same_size(tmp_path, d):
    """Sửa nội dung nhưng giữ NGUYÊN dung lượng: chỉ sha256 mới phát hiện được."""
    b = (tmp_path / d["path"]).read_bytes()
    (tmp_path / d["path"]).write_bytes(b[:-1] + bytes([b[-1] ^ 1]))


REJECT = [
    ("tep_bi_sua", lambda tp: _doc(tp), _tamper, "BANG_CHUNG_HONG"),
    ("tep_bi_sua_cung_dung_luong", lambda tp: _doc(tp), _tamper_same_size, "BANG_CHUNG_HONG"),
    ("tep_bi_xoa", lambda tp: _doc(tp), lambda tp, d: (tp / d["path"]).unlink(), "BANG_CHUNG_HONG"),
    ("thieu_url", lambda tp: _doc(tp, url=""), None, "BANG_CHUNG_HONG"),
    ("thieu_issuer", lambda tp: _doc(tp, issuer=""), None, "BANG_CHUNG_HONG"),
    ("sai_so_byte", lambda tp: _doc(tp, bytes=7), None, "BANG_CHUNG_HONG"),
    ("thieu_ngay_cong_bo", lambda tp: _doc(tp, published_at=None), None, "THIEU_NGAY_CONG_BO"),
    ("cong_bo_sau_ngay_cat", lambda tp: _doc(tp, published_at=str((AS_OF + pd.Timedelta(days=3)).date())), None, "CONG_BO_SAU_NGAY_CAT"),
    ("cong_bo_sau_huong_quyen", lambda tp: _doc(tp, pub=IDX[BRK] + pd.Timedelta(days=1)), None, "CONG_BO_SAU_NGAY_HUONG_QUYEN"),
    ("cong_bo_dung_ngay_huong_quyen", lambda tp: _doc(tp, pub=IDX[BRK]), None, "CONG_BO_SAU_NGAY_HUONG_QUYEN"),
    ("sai_ty_le", lambda tp: _doc(tp, ratio=1.5), None, "TY_LE_LECH"),
    ("thieu_ty_le", lambda tp: _doc(tp, official_ratio=None), None, "TY_LE_LECH"),
]


@pytest.mark.parametrize("name,make,mutate,state", REJECT, ids=[x[0] for x in REJECT])
def test_each_failed_evidence_condition_is_quarantined(tmp_path, name, make, mutate, state):
    d = make(tmp_path)
    if mutate:
        mutate(tmp_path, d)
    close, events, ev = _run(tmp_path, _ev("AAA", IDX[BRK]), _none(), [d])
    assert ev.verify_state.tolist() == [va.Q + state], ev.verify_reason.tolist()
    assert not ev.in_verified_chain.any() and ev.taints.all()
    assert (va.verified_factors(close.index, close.columns, ev)[0].values == 1.0).all()


def test_wrong_ticker_or_cash_document_does_not_count(tmp_path):
    for d in (_doc(tmp_path, ticker="BBB"), _doc(tmp_path, typ="cash_dividend")):
        _, _, ev = _run(tmp_path, _ev("AAA", IDX[BRK]), _none(), [d])
        assert ev.verify_state.tolist() == [va.Q + "THIEU_BANG_CHUNG"]


def test_date_mismatch_is_quarantined_with_offset_and_never_redated(tmp_path):
    """Giống VCB/TCB: ngày engine áp sớm 7 phiên so với ngày chính thức. Cổng không đổi ngày hộ, không áp, cách ly."""
    official = IDX[BRK + 7]
    close, events, ev = _run(tmp_path, _ev("AAA", IDX[BRK]), _none(), [_doc(tmp_path, ex=official)])
    r = ev.iloc[0]
    assert r.verify_state == va.Q + "LECH_NGAY" and r.session_offset == -7
    assert r.trade_date == IDX[BRK] and r.official_trade_date == official     # ngày engine giữ nguyên, ngày chính thức ghi riêng
    assert not r.in_verified_chain and r.taints
    assert (va.verified_factors(close.index, close.columns, ev)[0].values == 1.0).all()


def test_two_engine_dates_for_one_document_are_both_quarantined(tmp_path):
    """Giống TCB/VCB: một dòng nhập tay ở ngày gãy và một dòng Yahoo ở ngày chính thức cho cùng một bản gốc."""
    official = IDX[BRK + 7]
    close = _close()
    manual = _ev("AAA", IDX[BRK])
    yahoo = _ev("AAA", official, source="yahoo", status="TU_DONG")
    close, events, ev = _run(tmp_path, manual, yahoo, [_doc(tmp_path, ex=official)], close=close, obs=_obs(close, "2030-01-01"))
    states = dict(zip(ev.source.str[:5], ev.verify_state))
    assert states["manua"] == va.Q + "LECH_NGAY" and states["yahoo"] == va.Q + "XUNG_DOT_NGAY"
    assert not ev.in_verified_chain.any()


def test_price_jump_not_explained_by_ratio_is_quarantined_even_with_good_evidence(tmp_path):
    close = _close(ratio=1.0)                                        # không có bước nhảy giá
    manual = _ev("AAA", IDX[BRK], source="manual")
    events = adjust.build_events(close, _obs(close), manual, _none())
    assert events.status.tolist() == ["KHONG_KHOP"]
    ev = va.verify_events(events, close, [_doc(tmp_path)], evidence_root=tmp_path, as_of=AS_OF)
    assert ev.verify_state.tolist() == [va.Q + "GIA_KHONG_KHOP_TY_LE"] and ev.taints.all()


# ---------- 4. không ảnh hưởng / chưa xét ------------------------------------------------------------------------------------

def test_cash_dividend_is_not_assessed_and_not_in_chain(tmp_path):
    close = _close(ratio=1.0)
    cash = _ev("AAA", IDX[BRK], typ="cash_dividend", ratio=np.nan, cash=1.0, source="yahoo", status="TU_DONG")
    _, events, ev = _run(tmp_path, _none(), cash, [], close=close)
    assert events.status.tolist() == ["APPLIED"]
    assert ev.verify_state.tolist() == [va.NA_CASH] and not ev.in_verified_chain.any() and not ev.taints.any()


def test_event_after_the_data_window_has_no_effect(tmp_path):
    close, _, ev = _run(tmp_path, _ev("AAA", AS_OF + pd.Timedelta(days=30)), _none(), [])
    assert ev.verify_state.tolist() == [va.NA_NODATA]
    assert not va.taint_mask(close.index, close.columns, ev).values.any()


def test_coverage_counts_states(tmp_path):
    close, _, ev = _run(tmp_path, _ev("AAA", IDX[BRK]), _none(), [])
    cov = va.coverage(ev, va.taint_mask(close.index, close.columns, ev))
    assert cov["stock_events"] == 1 and cov["in_verified_chain"] == 0 and cov["by_state"] == {va.Q + "THIEU_BANG_CHUNG": 1}
    assert cov["tainted_share_all"] == pytest.approx(BRK / len(IDX), abs=1e-4)


# ---------- 5. công cụ dựng bản dẫn xuất ----------------------------------------------------------------------------------------

def _home(tmp_path, with_doc=True, tamper=False):
    """Dựng kho tổng hợp trong tmp (TTC_HOME): giá gốc, sự kiện nhập tay, bản gốc ghim."""
    home = tmp_path / "home"
    (home / "data/store").mkdir(parents=True)
    (home / "data/derived").mkdir(parents=True)
    close = _close()
    rows = [{"date": d.strftime("%Y-%m-%d"), "ticker": "AAA", "open": p, "high": p, "low": p, "close": p, "volume": 1000.0,
             "observed_at": "2026-01-01 00:00:00.000000", "source": "yahoo"} for d, p in close["AAA"].items()]
    pd.DataFrame(rows).to_csv(home / "data/store/prices.csv.gz", index=False)
    _ev("AAA", IDX[BRK]).to_csv(home / "data/corporate_actions.csv", index=False)
    _none().to_csv(home / "data/derived/yahoo_actions.csv", index=False)
    if with_doc:
        d = _doc(home)
        if tamper:
            (home / d["path"]).write_bytes(b"x")
        mp = home / "data/evidence/corporate_actions/EVIDENCE_MANIFEST.json"
        mp.write_text(json.dumps({"source_documents": [d]}, ensure_ascii=False), encoding="utf-8")
    return home


def _tool(home, out, *extra):
    env = {**os.environ, "TTC_HOME": str(home)}
    return subprocess.run([sys.executable, str(REPO / "tools/build_verified_derivation.py"), "--out", str(out), "--as-of",
                           str(AS_OF.date()), "--created-at", "2026-11-19T00:00:00Z", "--code-commit", "testcommit", *extra],
                          capture_output=True, text=True, env=env, cwd=str(REPO))


def _digest(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(pathlib.Path(root).rglob("*")) if p.is_file()}


def test_tool_is_deterministic_and_does_not_touch_raw(tmp_path):
    home = _home(tmp_path)
    before = _digest(home)
    r1, r2 = _tool(home, tmp_path / "o1"), _tool(home, tmp_path / "o2")
    assert r1.returncode == 0 and r2.returncode == 0, (r1.stderr, r2.stderr)
    assert _digest(home) == before                                               # kho raw, sự kiện, bản gốc: không đổi từng byte
    assert _digest(tmp_path / "o1") == _digest(tmp_path / "o2")                   # cùng đầu vào, cùng từng byte
    man = json.loads((tmp_path / "o1/manifest.json").read_text(encoding="utf-8"))
    assert man["derivation_id"].startswith("VA-") and man["code_commit"] == "testcommit" and man["supersedes"] is None
    assert man["coverage"]["in_verified_chain"] == 1 and man["source_documents"][0]["source_id"] == "hose-test-1"
    assert {"raw_snapshot_hash", "config_hash", "corporate_events_hash", "validity_scope"} <= set(man)
    assert {p.name for p in (tmp_path / "o1").iterdir()} == {"manifest.json", "events_verification.csv", "taint_by_ticker.csv", "before_after.md"}


def test_derivation_id_changes_when_evidence_changes(tmp_path):
    good, bad = _home(tmp_path / "g"), _home(tmp_path / "b", tamper=True)
    assert _tool(good, tmp_path / "og").returncode == 0 and _tool(bad, tmp_path / "ob").returncode == 0
    mg = json.loads((tmp_path / "og/manifest.json").read_text(encoding="utf-8"))
    mb = json.loads((tmp_path / "ob/manifest.json").read_text(encoding="utf-8"))
    assert mg["derivation_id"] != mb["derivation_id"]
    assert mg["coverage"]["in_verified_chain"] == 1 and mb["coverage"]["in_verified_chain"] == 0   # tệp bị sửa: cách ly


def test_tool_without_evidence_manifest_quarantines_everything(tmp_path):
    home = _home(tmp_path, with_doc=False)
    assert _tool(home, tmp_path / "o").returncode == 0
    man = json.loads((tmp_path / "o/manifest.json").read_text(encoding="utf-8"))
    assert man["coverage"]["in_verified_chain"] == 0 and man["coverage"]["by_state"] == {va.Q + "THIEU_BANG_CHUNG": 1}


@pytest.mark.parametrize("sub", ["data/derived/verified", "state/x", "engine/x", "ledger/x", "governance/x", "."])
def test_tool_refuses_protected_output_dirs(tmp_path, sub):
    home = _home(tmp_path)
    before = _digest(home)
    r = _tool(home, home / sub)
    assert r.returncode == 2 and "TỪ CHỐI" in r.stderr
    assert _digest(home) == before
