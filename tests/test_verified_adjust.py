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

def _home(tmp_path, with_doc=True, tamper=False, break_idx=BRK, doc_over=None):
    """Dựng kho tổng hợp trong tmp (TTC_HOME): giá gốc, sự kiện nhập tay, bản gốc ghim."""
    home = tmp_path / "home"
    (home / "data/store").mkdir(parents=True)
    (home / "data/derived").mkdir(parents=True)
    close = _close(break_idx=break_idx)
    rows = [{"date": d.strftime("%Y-%m-%d"), "ticker": "AAA", "open": p, "high": p, "low": p, "close": p, "volume": 1000.0,
             "observed_at": "2026-01-01 00:00:00.000000", "source": "yahoo"} for d, p in close["AAA"].items()]
    pd.DataFrame(rows).to_csv(home / "data/store/prices.csv.gz", index=False)
    _ev("AAA", IDX[break_idx]).to_csv(home / "data/corporate_actions.csv", index=False)
    _none().to_csv(home / "data/derived/yahoo_actions.csv", index=False)
    if with_doc:
        d = _doc(home, ex=IDX[break_idx], **(doc_over or {}))
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


# ---------- 6. hồi quy phản biện L-09 (ChatGPT, PR #55, SHA ec47dc8): bốn phát hiện MEDIUM ----------------------------------

# MEDIUM-1: loại sự kiện phải trùng đúng. Bản gốc stock_dividend không kiểm được sự kiện engine stock_split và ngược lại.
@pytest.mark.parametrize("engine_typ,doc_typ", [("stock_split", "stock_dividend"), ("stock_dividend", "stock_split")])
def test_m1_event_type_mismatch_is_quarantined(tmp_path, engine_typ, doc_typ):
    close, _, ev = _run(tmp_path, _ev("AAA", IDX[BRK], typ=engine_typ), _none(), [_doc(tmp_path, typ=doc_typ)])
    r = ev.iloc[0]
    assert r.status == "APPLIED"                                           # cùng mã, ngày, tỷ lệ: chỉ khác loại
    assert r.verify_state == va.Q + "LOAI_SU_KIEN_LECH", r.verify_reason
    assert not r.in_verified_chain and r.taints and r.evidence_id == "hose-test-1"
    assert (va.verified_factors(close.index, close.columns, ev)[0].values == 1.0).all()


def test_m1_yahoo_already_adjusted_split_vs_dividend_document_is_quarantined(tmp_path):
    """Đúng ca FPT thật: Yahoo ghi stock_split (giá nguồn đã chứa điều chỉnh), văn bản HOSE là stock_dividend."""
    close = _close(ratio=1.0)
    yahoo = _ev("AAA", IDX[BRK], typ="stock_split", source="yahoo", status="TU_DONG")
    events = adjust.build_events(close, _obs(close, "2030-01-01"), _none(), yahoo)
    assert events.status.tolist() == ["DA_NAM_TRONG_GIA_NGUON"]
    ev = va.verify_events(events, close, [_doc(tmp_path, typ="stock_dividend")], evidence_root=tmp_path, as_of=AS_OF)
    assert ev.verify_state.tolist() == [va.Q + "LOAI_SU_KIEN_LECH"] and not ev.in_verified_chain.any()


def test_m1_same_type_document_preferred_over_other_type_at_same_distance(tmp_path):
    other = _doc(tmp_path, sid="hose-khac-loai", typ="stock_split", content=b"%PDF van ban khac loai")
    same = _doc(tmp_path, sid="hose-dung-loai", typ="stock_dividend", content=b"%PDF van ban dung loai")
    _, _, ev = _run(tmp_path, _ev("AAA", IDX[BRK], typ="stock_dividend"), _none(), [other, same])
    assert ev.verify_state.tolist() == [va.OK] and ev.evidence_id.tolist() == ["hose-dung-loai"]


# MEDIUM-2: danh sách cho phép trạng thái engine; tỷ lệ phải là số hữu hạn dương.
def test_m2_zero_ratio_event_with_zero_ratio_document_is_not_verified(tmp_path):
    """Ca phản biện nêu: sự kiện tỷ lệ 0 → engine LOI_TY_LE; manifest ghi official_ratio=0. Trước đây thành DA_KIEM_CHUNG."""
    close, events, ev = _run(tmp_path, _ev("AAA", IDX[BRK], ratio=0.0), _none(), [_doc(tmp_path, ratio=0)])
    assert events.status.tolist() == ["LOI_TY_LE"]
    r = ev.iloc[0]
    assert r.verify_state.startswith(va.Q) and r.verify_state != va.OK, r.verify_reason
    assert not r.in_verified_chain and r.taints
    assert (va.verified_factors(close.index, close.columns, ev)[0].values == 1.0).all()


@pytest.mark.parametrize("status", ["LOI_TY_LE", "LOAI_KHONG_HO_TRO", "LOAI_BAT_THUONG", "TRANG_THAI_MOI_CHUA_BIET"])
def test_m2_engine_status_outside_allow_list_is_quarantined(tmp_path, status):
    """Mọi điều kiện bằng chứng đều đạt; chỉ trạng thái engine nằm ngoài danh sách cho phép → vẫn cách ly và vẫn nhiễm."""
    close, events, _ = _run(tmp_path, _ev("AAA", IDX[BRK]), _none(), [])
    events = events.assign(status=status)
    ev = va.verify_events(events, close, [_doc(tmp_path)], evidence_root=tmp_path, as_of=AS_OF)
    r = ev.iloc[0]
    assert r.verify_state == va.Q + "TRANG_THAI_ENGINE_KHONG_HOP_LE", r.verify_reason
    assert not r.in_verified_chain and r.taints
    assert not va.taint_mask(close.index, close.columns, ev).iloc[BRK:].values.any()
    assert va.taint_mask(close.index, close.columns, ev).iloc[:BRK].values.all()


@pytest.mark.parametrize("bad", [0, -2.0, float("nan"), float("inf"), "2.0", True, [2.0]])
def test_m2_non_positive_or_non_numeric_document_ratio_is_quarantined(tmp_path, bad):
    _, _, ev = _run(tmp_path, _ev("AAA", IDX[BRK]), _none(), [_doc(tmp_path, official_ratio=bad)])
    assert ev.verify_state.tolist() == [va.Q + "TY_LE_LECH"] and not ev.in_verified_chain.any()


def test_m2_allow_list_is_exactly_two_states():
    assert va.VERIFIABLE == ("APPLIED", "DA_NAM_TRONG_GIA_NGUON")


# MEDIUM-3: source_id bắt buộc; kiểm tra trùng ngày không lách được bằng source_id rỗng hay khai trùng tệp.
def _two_dates(tmp_path, docs):
    """Dòng nhập tay ở ngày gãy (BRK) và dòng Yahoo ở ngày chính thức (BRK+7) cho cùng một văn bản."""
    official = IDX[BRK + 7]
    close = _close()
    return _run(tmp_path, _ev("AAA", IDX[BRK]), _ev("AAA", official, source="yahoo", status="TU_DONG"), docs,
                close=close, obs=_obs(close, "2030-01-01"))


@pytest.mark.parametrize("sid", ["", "   ", None])
def test_m3_missing_or_blank_source_id_cannot_bypass_duplicate_date_check(tmp_path, sid):
    d = _doc(tmp_path, ex=IDX[BRK + 7])
    if sid is None:
        d.pop("source_id")
    else:
        d["source_id"] = sid
    _, _, ev = _two_dates(tmp_path, [d])
    assert not ev.in_verified_chain.any(), ev[["source", "verify_state", "verify_reason"]].to_dict("records")
    assert set(ev.verify_state) <= {va.Q + "BANG_CHUNG_HONG"}


def test_m3_same_file_declared_under_two_source_ids_is_a_date_conflict(tmp_path):
    """Cùng một tệp (cùng sha256) khai thành hai mục có source_id khác nhau: vẫn là một bản gốc bị engine áp ở hai ngày."""
    a = _doc(tmp_path, ex=IDX[BRK], sid="hose-ban-a")
    b = {**a, "source_id": "hose-ban-b", "official_ex_date": str(IDX[BRK + 7].date())}
    _, _, ev = _two_dates(tmp_path, [a, b])
    assert not ev.in_verified_chain.any()
    assert (ev.verify_state == va.Q + "XUNG_DOT_NGAY").all(), ev.verify_reason.tolist()


def test_m3_source_id_with_valid_unique_document_still_verifies(tmp_path):
    """Không quá tay: một văn bản hợp lệ, một ngày engine, có source_id → vẫn DA_KIEM_CHUNG."""
    _, _, ev = _run(tmp_path, _ev("AAA", IDX[BRK]), _none(), [_doc(tmp_path)])
    assert ev.verify_state.tolist() == [va.OK]


# MEDIUM-4: chỉ xuất ra ngoài kho, không ghi đè.
def test_m4_refuses_output_inside_code_repo_even_outside_protected_dirs(tmp_path):
    home = _home(tmp_path)
    out = REPO / "reports" / "_verified_derivation_test_should_not_exist"
    assert not out.exists()
    r = _tool(home, out)
    assert r.returncode == 2 and "TỪ CHỐI" in r.stderr and not out.exists()


@pytest.mark.parametrize("sub", ["reports/verified", "khac/verified"])
def test_m4_refuses_output_anywhere_inside_data_home(tmp_path, sub):
    home = _home(tmp_path)
    before = _digest(home)
    r = _tool(home, home / sub)
    assert r.returncode == 2 and "TỪ CHỐI" in r.stderr and _digest(home) == before


def test_m4_rerun_into_existing_output_is_refused_and_bytes_kept(tmp_path):
    home = _home(tmp_path)
    out = tmp_path / "o"
    assert _tool(home, out).returncode == 0
    first = _digest(out)
    # đổi đầu vào để lần dựng sau ra bản khác: nếu ghi đè được thì bytes sẽ đổi
    (home / "data/evidence/corporate_actions/EVIDENCE_MANIFEST.json").unlink()
    r = _tool(home, out)
    assert r.returncode == 2 and "TỪ CHỐI" in r.stderr
    assert _digest(out) == first


@pytest.mark.parametrize("kind", ["empty_dir", "file", "dangling_symlink"])
def test_m4_any_existing_output_path_is_refused(tmp_path, kind):
    home = _home(tmp_path)
    out = tmp_path / "o"
    if kind == "empty_dir":
        out.mkdir()
    elif kind == "file":
        out.write_bytes(b"khong duoc ghi de")
    else:
        out.symlink_to(tmp_path / "chua_co")
    r = _tool(home, out)
    assert r.returncode == 2 and "TỪ CHỐI" in r.stderr
    if kind == "file":
        assert out.read_bytes() == b"khong duoc ghi de"
    if kind == "empty_dir":
        assert list(out.iterdir()) == []
    if kind == "dangling_symlink":
        assert not (tmp_path / "chua_co").exists()


def test_m4_symlink_parent_pointing_into_repo_is_refused(tmp_path):
    home = _home(tmp_path)
    link = tmp_path / "link_vao_kho"
    link.symlink_to(REPO / "reports")
    out = link / "_verified_derivation_test_should_not_exist"
    r = _tool(home, out)
    assert r.returncode == 2 and "TỪ CHỐI" in r.stderr
    assert not (REPO / "reports" / "_verified_derivation_test_should_not_exist").exists()


def _bvd():
    sys.path.insert(0, str(REPO / "tools"))
    import build_verified_derivation as bvd                                  # noqa: E402
    return bvd


def test_m4_build_refuses_out_dir_that_appeared_after_the_check(tmp_path):
    """Lớp hai (mkdir nguyên tử): thư mục xuất xuất hiện giữa lúc kiểm và lúc ghi, kể cả rỗng → `build` không ghi gì vào đó."""
    out = tmp_path / "race"
    out.mkdir()
    with pytest.raises(FileExistsError):
        _bvd().build(out, None, [], "2026-11-19T00:00:00Z", "testcommit")
    assert list(out.iterdir()) == []


@pytest.mark.parametrize("kind", ["empty_dir", "file", "dangling_symlink"])
def test_m4_out_check_alone_rejects_existing_paths(tmp_path, kind):
    """Lớp một (kiểm trước, không tạo gì): `out_is_protected` tự từ chối, không dựa vào mkdir."""
    out = tmp_path / "o"
    if kind == "empty_dir":
        out.mkdir()
    elif kind == "file":
        out.write_bytes(b"x")
    else:
        out.symlink_to(tmp_path / "chua_co")
    why = _bvd().out_is_protected(out)
    assert why and "đã tồn tại" in why


def test_m4_out_check_allows_fresh_path_outside_repo(tmp_path):
    assert _bvd().out_is_protected(tmp_path / "moi" / "chua_co") is None


@pytest.mark.parametrize("ratio", [0.0, -2.0])
def test_m2_ratio_check_alone_rejects_non_positive_even_if_engine_says_applied(tmp_path, ratio):
    """Lớp tỷ lệ độc lập với danh sách cho phép: bảng sự kiện bị sửa thành APPLIED với tỷ lệ không dương, văn bản ghi
    cùng tỷ lệ → vẫn TY_LE_LECH."""
    close, events, _ = _run(tmp_path, _ev("AAA", IDX[BRK]), _none(), [])
    events = events.assign(ratio=ratio, status="APPLIED")
    ev = va.verify_events(events, close, [_doc(tmp_path, ratio=ratio)], evidence_root=tmp_path, as_of=AS_OF)
    assert ev.verify_state.tolist() == [va.Q + "TY_LE_LECH"] and not ev.in_verified_chain.any()


def test_m4_create_helper_refuses_existing_file(tmp_path):
    """Lớp ba: từng tệp mở ở chế độ tạo-mới."""
    f = tmp_path / "manifest.json"
    f.write_text("ban cu", encoding="utf-8")
    with pytest.raises(FileExistsError):
        _bvd()._create(f)
    assert f.read_text(encoding="utf-8") == "ban cu"


# ---------- 7. hồi quy phản biện L-09 vòng 2 (ChatGPT, PR #55, SHA 5b0f588): MEDIUM-A và MEDIUM-B -------------------------

# MEDIUM-A: DA_NAM_TRONG_GIA_NGUON do engine đặt CHỈ theo nguồn yahoo + observed_at, không xét bước giá. Cổng phải tự chứng minh
# chuỗi giá gốc liên tục tại phiên sự kiện; không chứng minh được thì cách ly và nhiễm ô (đóng khi nghi ngờ).
def _yahoo_seen_after(close, ratio=RATIO, typ="stock_dividend"):
    yahoo = _ev("AAA", IDX[BRK], typ=typ, ratio=ratio, source="yahoo", status="TU_DONG")
    return adjust.build_events(close, _obs(close, "2030-01-01"), _none(), yahoo)


def test_ma_already_in_price_status_with_raw_break_is_quarantined_and_tainted(tmp_path):
    """Ca phản biện nêu: giá gốc giảm 50% tại sự kiện tỷ lệ 2,0; nguồn yahoo, observed_at sau ex_date; văn bản đúng loại, ngày,
    tỷ lệ, SHA. Engine đặt DA_NAM_TRONG_GIA_NGUON dù chuỗi còn bước gãy −50%."""
    close = _close()                                                  # bước gãy −50% tại BRK
    events = _yahoo_seen_after(close)
    assert events.status.tolist() == ["DA_NAM_TRONG_GIA_NGUON"]
    assert events.raw_return.iloc[0] == pytest.approx(-0.5, abs=0.01)
    ev = va.verify_events(events, close, [_doc(tmp_path)], evidence_root=tmp_path, as_of=AS_OF)
    r = ev.iloc[0]
    assert r.verify_state == va.Q + "GIA_CHUA_LIEN_TUC", r.verify_reason
    assert not r.in_verified_chain and r.taints
    m = va.taint_mask(close.index, close.columns, ev)
    assert m.iloc[:BRK].values.all() and not m.iloc[BRK:].values.any()
    assert (va.verified_factors(close.index, close.columns, ev)[0].values == 1.0).all()


def test_ma_already_in_price_with_raw_break_not_explained_by_ratio_is_quarantined(tmp_path):
    """Nhánh 'còn gãy' độc lập với nhánh 'mơ hồ': giá gốc gãy −50% nhưng văn bản và sự kiện ghi tỷ lệ 3,0, nên nhân tỷ lệ
    cũng ra +50% (ngoài biên). Không giả thuyết nào giải thích được bước giá → vẫn phải cách ly."""
    close = _close()
    events = _yahoo_seen_after(close, ratio=3.0)
    assert events.status.tolist() == ["DA_NAM_TRONG_GIA_NGUON"]
    ev = va.verify_events(events, close, [_doc(tmp_path, ratio=3.0)], evidence_root=tmp_path, as_of=AS_OF)
    r = ev.iloc[0]
    assert r.verify_state == va.Q + "GIA_CHUA_LIEN_TUC" and "bước gãy" in r.verify_reason, r.verify_reason
    assert r.taints and not r.in_verified_chain


def test_ma_already_in_price_ambiguous_small_ratio_is_quarantined(tmp_path):
    """Tỷ lệ nhỏ (1,02): cả giả thuyết 'giá đã điều chỉnh' lẫn 'giá chưa điều chỉnh' đều nằm trong biên độ, nên giá không
    chứng minh được nguồn đã điều chỉnh. Đóng khi nghi ngờ: cách ly."""
    close = _close(ratio=1.0)
    events = _yahoo_seen_after(close, ratio=1.02)
    assert events.status.tolist() == ["DA_NAM_TRONG_GIA_NGUON"]
    ev = va.verify_events(events, close, [_doc(tmp_path, ratio=1.02)], evidence_root=tmp_path, as_of=AS_OF)
    assert ev.verify_state.tolist() == [va.Q + "GIA_CHUA_LIEN_TUC"] and ev.taints.all() and not ev.in_verified_chain.any()


def test_ma_already_in_price_with_continuous_raw_still_verifies(tmp_path):
    """Không quá tay: giá liên tục và tỷ lệ 2,0 phân biệt rõ hai giả thuyết → vẫn DA_KIEM_CHUNG, không áp thêm hệ số."""
    close = _close(ratio=1.0)
    ev = va.verify_events(_yahoo_seen_after(close), close, [_doc(tmp_path)], evidence_root=tmp_path, as_of=AS_OF)
    assert ev.verify_state.tolist() == [va.OK] and ev.in_verified_chain.all() and not ev.taints.any()
    assert (va.verified_factors(close.index, close.columns, ev)[0].values == 1.0).all()


def test_ma_continuity_check_uses_close_not_the_events_raw_return_column(tmp_path):
    """Bảng sự kiện bị sửa cột raw_return thành 0 vẫn không qua cổng: cổng đo lại bước giá từ chuỗi giá gốc."""
    close = _close()
    events = _yahoo_seen_after(close).assign(raw_return=0.0)
    ev = va.verify_events(events, close, [_doc(tmp_path)], evidence_root=tmp_path, as_of=AS_OF)
    assert ev.verify_state.tolist() == [va.Q + "GIA_CHUA_LIEN_TUC"]


# MEDIUM-B: derivation_id phải đổi khi BẤT KỲ metadata chứng cứ nào đổi, kể cả khi trạng thái và ngày giao dịch không đổi.
MONDAY = next(i for i in range(BRK, len(IDX)) if IDX[i].weekday() == 0)


def _derive(home, out):
    r = _tool(home, out)
    assert r.returncode == 0, r.stderr
    return json.loads((out / "manifest.json").read_text(encoding="utf-8"))


def test_mb_weekend_official_date_change_changes_derivation_id(tmp_path):
    """Ca phản biện nêu: ngày chính thức Thứ Bảy hay Chủ Nhật đều rơi vào phiên Thứ Hai; DA_KIEM_CHUNG, trade_date giống nhau
    nhưng metadata nguồn khác → hai bản dẫn xuất phải có derivation_id khác, và manifest lưu ngày chính thức để kiểm toán."""
    sat, sun = IDX[MONDAY] - pd.Timedelta(days=2), IDX[MONDAY] - pd.Timedelta(days=1)
    pub = str((sat - pd.Timedelta(days=6)).date())
    hs = _home(tmp_path / "sat", break_idx=MONDAY, doc_over={"official_ex_date": str(sat.date()), "published_at": pub})
    hu = _home(tmp_path / "sun", break_idx=MONDAY, doc_over={"official_ex_date": str(sun.date()), "published_at": pub})
    ms, mu = _derive(hs, tmp_path / "os"), _derive(hu, tmp_path / "ou")
    assert ms["coverage"]["in_verified_chain"] == 1 and mu["coverage"]["in_verified_chain"] == 1
    es = pd.read_csv(tmp_path / "os/events_verification.csv")
    eu = pd.read_csv(tmp_path / "ou/events_verification.csv")
    assert es.trade_date.tolist() == eu.trade_date.tolist() and es.verify_state.tolist() == eu.verify_state.tolist()
    assert es.official_ex_date.tolist() != eu.official_ex_date.tolist()
    assert ms["derivation_id"] != mu["derivation_id"]
    assert ms["source_documents"][0]["official_ex_date"] == str(sat.date())
    assert mu["source_documents"][0]["official_ex_date"] == str(sun.date())


def _manifest_for(home, docs, ev):
    cfg = {"data": {"store": "data/store/prices.csv.gz", "store_dir": "data/store/prices"},
           "corporate_actions": {"manual": "data/corporate_actions.csv", "yahoo_cache": "data/derived/yahoo_actions.csv"}}
    return va.derivation_manifest(root=home, cfg=cfg, as_of=AS_OF, docs=docs, ev=ev, code_commit="c", created_at="t")


@pytest.mark.parametrize("field,value", [("event_type", "stock_split"), ("official_ex_date", "2099-01-01"),
                                         ("official_ratio", 3.0), ("path", "khac/ban_goc.pdf"), ("ticker", "BBB"),
                                         ("source_id", "hose-khac"), ("published_at", "2000-01-01"),
                                         ("url", "https://example.invalid/khac.pdf"), ("issuer", "khac"),
                                         ("sha256", "0" * 64), ("bytes", 1), ("ghi_chu_moi", "x")])
def test_mb_every_evidence_field_is_bound_into_derivation_id(tmp_path, field, value):
    """Cùng raw/code/config/sự kiện và cùng bảng kết quả kiểm; chỉ đổi một trường của văn bản → derivation_id phải đổi."""
    home = _home(tmp_path, with_doc=False)
    close, _, ev = _run(tmp_path, _ev("AAA", IDX[BRK]), _none(), [])
    d = _doc(tmp_path)
    a, b = _manifest_for(home, [d], ev), _manifest_for(home, [{**d, field: value}], ev)
    assert a["derivation_id"] != b["derivation_id"], field


@pytest.mark.parametrize("col,value", [("official_ex_date", pd.Timestamp("2099-01-01")),
                                       ("official_trade_date", pd.Timestamp("2099-01-02")), ("evidence_id", "hose-khac"),
                                       ("session_offset", 3.0), ("verify_reason", "ly do khac"), ("ratio", 9.0),
                                       ("source", "nguon-khac"), ("source_status", "TRANG_THAI_KHAC")])
def test_mb_events_digest_covers_provenance_columns(tmp_path, col, value):
    home = _home(tmp_path, with_doc=False)
    _, _, ev = _run(tmp_path, _ev("AAA", IDX[BRK]), _none(), [_doc(tmp_path)])
    a = _manifest_for(home, [], ev)
    b = _manifest_for(home, [], ev.assign(**{col: value}))
    assert a["events_verification_digest"] != b["events_verification_digest"], col
    assert a["derivation_id"] != b["derivation_id"], col

