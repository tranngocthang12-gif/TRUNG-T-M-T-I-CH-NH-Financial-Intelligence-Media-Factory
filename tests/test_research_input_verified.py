"""LỆNH E2a (QĐ-1, QĐ-3 của ADR-0016): đầu vào nghiên cứu đã kiểm — load_market(research_input="verified"), mặt nạ cửa sổ
quanh sự kiện quyền chưa kiểm, và features nhận `exclude`.

Không mạng. Không ghi kho: fixture tổng hợp ghi vào tmp_path; phần kho thật chỉ ĐỌC."""
import hashlib
import json
import pathlib
import pickle
import subprocess
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from engine import adjust, config, data, features, verified_adjust as va

REPO = pathlib.Path(__file__).resolve().parents[1]
IDX = pd.bdate_range("2023-01-02", periods=420)
OFF = 300                                   # phiên không hưởng quyền chính thức của AAA trong fixture
W = 7                                       # số phiên nguồn đã chia sẵn trước ngày đó (điều chỉnh một phần)
R = 2.0
TICKERS = ["AAA", "BBB", "CCC", "DDD"]
OBS = "2026-09-26"
H = config.CFG["horizon_days"]
OLD_KEYS = ("close", "volume", "raw_close", "bad", "events", "quality", "flags")
NONE = pd.DataFrame(columns=adjust.EV_COLS)


def _walk(seed=7):
    rng = np.random.default_rng(seed)
    r = rng.normal(0.0, 0.012, size=(len(IDX), len(TICKERS))).clip(-0.05, 0.05)
    return pd.DataFrame(100.0 * np.cumprod(1 + r, axis=0), index=IDX, columns=TICKERS)


def _true_raw():
    """Giá gốc chưa điều chỉnh: AAA giảm theo tỷ lệ R tại phiên chính thức."""
    c = _walk()
    c.iloc[OFF:, 0] = c.iloc[OFF:, 0] / R
    return c


def _partial():
    """Nguồn điều chỉnh một phần: W phiên liền trước phiên chính thức đã chia cho R (như TCB/VCB của kho thật)."""
    c = _true_raw()
    c.iloc[OFF - W:OFF, 0] = c.iloc[OFF - W:OFF, 0] / R
    return c


def _ev(rows):
    return pd.DataFrame([{"ticker": "AAA", "cash_per_share": np.nan, "note": "", **r} for r in rows], columns=adjust.EV_COLS)


def _yahoo(at=None):
    return _ev([{"ex_date": IDX[OFF] if at is None else at, "type": "stock_split", "ratio": R, "source": "yahoo",
                 "source_status": "TU_DONG"}])


def _manual(at, ratio=R, typ="stock_dividend", cash=np.nan):
    return _ev([{"ex_date": at, "type": typ, "ratio": ratio, "cash_per_share": cash, "source": "manual (fixture)",
                 "source_status": "CAN_DOI_CHIEU"}])


def _doc(home, published=None, **over):
    rel = "data/evidence/corporate_actions/fx-1/ban_goc.pdf"
    p = home / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    b = b"%PDF-1.4 ban goc gia lap (fixture E2a)"
    p.write_bytes(b)
    d = {"source_id": "fx-1", "url": "https://example.invalid/fx-1.pdf", "issuer": "So giao dich (gia lap)", "path": rel,
         "sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b), "ticker": "AAA", "event_type": "stock_split",
         "official_ex_date": str(IDX[OFF].date()),
         "published_at": published or str((IDX[OFF] - pd.Timedelta(days=8)).date()), "official_ratio": R}
    d.update(over)
    return d


def _home(tmp, close, manual=None, yahoo=None, docs=None, manifest="EVIDENCE_MANIFEST_FX.json", vol=None):
    vol = pd.DataFrame(1e6, index=close.index, columns=close.columns) if vol is None else vol
    rows = [{"date": d.strftime("%Y-%m-%d"), "ticker": t, "open": close.at[d, t], "high": close.at[d, t],
             "low": close.at[d, t], "close": close.at[d, t], "volume": float(vol.at[d, t]), "observed_at": OBS,
             "source": "fixture"} for d in close.index for t in close.columns if pd.notna(close.at[d, t])]
    assert data.save_store(pd.DataFrame(rows, columns=data.COLS), root=tmp) > 0
    for key, df in (("manual", NONE if manual is None else manual), ("yahoo_cache", NONE if yahoo is None else yahoo)):
        p = tmp / config.CFG["corporate_actions"][key]
        p.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(p, index=False)
    if docs is not None:
        m = tmp.joinpath(*data.EVIDENCE_DIR) / manifest
        m.parent.mkdir(parents=True, exist_ok=True)
        m.write_text(json.dumps({"source_documents": docs}, ensure_ascii=False), encoding="utf-8")
    return tmp


def _market(home, as_of=None, cfg=None, **kw):
    with patch.object(config, "ROOT", home), patch.object(adjust, "ROOT", home), patch.dict(config.CFG, cfg or {}):
        return data.load_market(as_of, **kw)


def _h(x):
    """Hash từng byte của một giá trị trả về (bảng: nội dung CSV đầy đủ + kiểu cột + chỉ mục)."""
    if isinstance(x, pd.DataFrame):
        return hashlib.sha256(pickle.dumps((x.to_csv(), [str(t) for t in x.dtypes], str(x.index.dtype)))).hexdigest()
    return hashlib.sha256(json.dumps(x, sort_keys=True, default=str, ensure_ascii=False).encode()).hexdigest()


def _legacy_reference(as_of=None):
    """Bản sao nguyên văn thân load_market trên main trước E2a (8550622…1fdb3e0): mốc so 'không đổi một byte'."""
    s = data.load_store()
    if as_of is not None:
        s = s[s.date <= pd.Timestamp(as_of)]
    raw = s.pivot(index="date", columns="ticker", values="close").sort_index()
    vol = s.pivot(index="date", columns="ticker", values="volume").sort_index()
    obs = s.pivot(index="date", columns="ticker", values="observed_at").sort_index()
    keep = raw.columns[raw.notna().sum() > 250]
    raw, vol, obs = raw[keep], vol[keep], obs[keep]
    events = adjust.build_events(raw, obs, adjust.load_manual(), adjust.load_yahoo())
    F, S = adjust.factors(raw.index, raw.columns, events)
    adj = raw * F
    bad, rep, flags = adjust.quality(adj)
    rep["events"] = events.status.value_counts().to_dict() if len(events) else {}
    rep["events_not_applied"] = [f"{e.ticker} {e.ex_date.date()} {e.type} ({e.source}): {e.status}"
                                 for e in events.itertuples() if e.status not in ("APPLIED", "CHUA_DEN_HAN",
                                                                                  "DA_NAM_TRONG_GIA_NGUON")]
    rep["events_applied"] = [f"{e.ticker} {e.trade_date.date()} {e.type} ({e.source}, {e.source_status}): "
                             f"gốc {e.raw_return:+.2%} → điều chỉnh {e.adj_return:+.2%}"
                             for e in events.itertuples() if e.status == "APPLIED"]
    return {"close": adj.ffill(limit=5), "volume": (vol / S).fillna(0), "raw_close": raw, "bad": bad,
            "events": events, "quality": rep, "flags": flags}


# ---------- 1. legacy: không đổi một byte ----------

def _assert_legacy_unchanged(home, as_of=None):
    with patch.object(config, "ROOT", home), patch.object(adjust, "ROOT", home):
        new, old = data.load_market(as_of), _legacy_reference(as_of)
    # E2c (Owner cho sửa assert, 22/11/2026): chế độ mặc định sessions="keep" thêm đúng một khóa quality.sessions (liệt kê
    # ngày không phải phiên, không bỏ ngày nào); mọi phần khác vẫn so từng byte với bản trước E2a
    q = dict(new["quality"])
    sess = q.pop("sessions")
    assert sess["mode"] == "keep" and sess["dropped"] == 0
    cur = {**new, "quality": q}
    assert {k: _h(cur[k]) for k in OLD_KEYS} == {k: _h(old[k]) for k in OLD_KEYS}
    assert set(new) == set(OLD_KEYS) | {"research_input", "derivation_id", "pit_label", "pit_gaps"}
    assert new["research_input"] == "legacy" and new["pit_label"] == "RETROSPECTIVE"
    assert any("sự kiện quyền chưa kiểm" in g for g in new["pit_gaps"])
    return new


def test_legacy_is_byte_identical_on_a_fixture_with_an_unverified_event(tmp_path):
    home = _home(tmp_path, _partial(), manual=_manual(IDX[OFF - W]), docs=[_doc(tmp_path)])
    mk = _assert_legacy_unchanged(home)
    assert "APPLIED" in mk["events"].status.tolist()                       # legacy vẫn áp sự kiện chưa kiểm
    _assert_legacy_unchanged(home, as_of=str(IDX[OFF + 30].date()))


def test_legacy_is_byte_identical_on_the_real_store():
    _assert_legacy_unchanged(config.ROOT)
    _assert_legacy_unchanged(config.ROOT, as_of="2025-06-30")


def test_features_without_exclude_are_byte_identical(tmp_path):
    close = _walk()
    vol = pd.DataFrame(1e6, index=IDX, columns=TICKERS)
    ref = features.dataset(close, vol, H)
    assert _h(features.dataset(close, vol, H, exclude=None)) == _h(ref)
    assert _h(features.dataset(close, vol, H, None, pd.DataFrame(False, index=IDX, columns=TICKERS))) == _h(ref)


@pytest.mark.parametrize("text", ["{khong phai json", '{"source_documents": [', "", "\x00\x01"])
def test_legacy_ignores_a_broken_manifest_but_verified_refuses_it(tmp_path, text):
    """Vòng chấm 1, BLOCKER 1: manifest bản gốc hỏng không được làm đường mặc định dừng, vì legacy không dùng bản gốc. Đầu ra
    cũ của legacy vẫn trùng từng byte bản trước E2a; chế độ verified thì dừng (không chạy với bản gốc hỏng)."""
    home = _home(tmp_path, _partial(), manual=_manual(IDX[OFF - W]), docs=[_doc(tmp_path)])
    ok = _market(home)["derivation_id"]
    (home.joinpath(*data.EVIDENCE_DIR) / "EVIDENCE_MANIFEST_HONG.json").write_text(text, encoding="utf-8")
    mk = _assert_legacy_unchanged(home)
    assert mk["derivation_id"] == ok                                    # legacy không phụ thuộc manifest
    with pytest.raises(ValueError):                                     # json.JSONDecodeError là ValueError
        _market(home, research_input="verified")


def test_unknown_research_input_is_rejected(tmp_path):
    home = _home(tmp_path, _walk())
    for bad in ("Verified", "", None, "pit"):
        with pytest.raises(ValueError, match="research_input"):
            _market(home, research_input=bad)


# ---------- 2. verified: chỉ sự kiện đã kiểm được áp; bản gốc đọc từ mọi manifest ----------

def test_verified_applies_only_events_in_the_verified_chain(tmp_path):
    """Sự kiện chưa kiểm (tay, CAN_DOI_CHIEU, không bản gốc) và cổ tức tiền: legacy APPLIED, verified không."""
    man = pd.concat([_manual(IDX[OFF]), _manual(IDX[100], ratio=np.nan, typ="cash_dividend", cash=1.0)], ignore_index=True)
    home = _home(tmp_path, _true_raw(), manual=man)
    assert set(_market(home)["events"].status) == {"APPLIED"}
    mk = _market(home, research_input="verified")
    assert "APPLIED" not in set(mk["events"].status) and set(mk["events"].status) == {data.NOT_IN_CHAIN}
    assert list(mk["events"].columns) == list(_market(home)["events"].columns)
    assert not mk["event_checks"].in_verified_chain.any()
    assert mk["raw_close"].equals(_market(home)["raw_close"])
    assert np.allclose(mk["close"]["AAA"].iloc[OFF:], mk["raw_close"]["AAA"].iloc[OFF:])
    assert (mk["close"]["AAA"].iloc[:OFF] == mk["raw_close"]["AAA"].iloc[:OFF]).all()  # không hệ số: chuỗi kiểm = giá gốc


def test_verified_applies_a_verified_event_and_reads_every_manifest(tmp_path):
    """Bản gốc nằm ở manifest thứ hai (không phải EVIDENCE_MANIFEST.json): vẫn được đọc, sự kiện vào chuỗi và được áp.
    Giá gốc chưa điều chỉnh, sự kiện nhập tay đúng ngày và tỷ lệ: engine APPLIED, cổng chứng minh giả thuyết "chưa điều chỉnh"."""
    home = _home(tmp_path, _true_raw(), manual=_manual(IDX[OFF]), docs=[_doc(tmp_path)], manifest="EVIDENCE_MANIFEST_ZZ.json")
    (home.joinpath(*data.EVIDENCE_DIR) / "EVIDENCE_MANIFEST.json").write_text('{"source_documents": []}', encoding="utf-8")
    mk = _market(home, research_input="verified")
    assert mk["event_checks"].verify_state.tolist() == [va.OK] and mk["events"].status.tolist() == ["APPLIED"]
    np.testing.assert_allclose(mk["close"]["AAA"].values, _walk()["AAA"].values / R)   # hệ số chia tách đã áp
    assert not mk["exclude"].values.any() and mk["eligible"].values.all()


def test_evidence_docs_reads_all_manifests_sorted_by_name(tmp_path):
    d = tmp_path.joinpath(*data.EVIDENCE_DIR)
    d.mkdir(parents=True)
    for name, sid in (("EVIDENCE_MANIFEST_B.json", "b"), ("EVIDENCE_MANIFEST.json", "0"), ("EVIDENCE_MANIFEST_A.json", "a"),
                      ("KHAC.json", "x")):
        (d / name).write_text(json.dumps({"source_documents": [{"source_id": sid}]}), encoding="utf-8")
    assert [x["source_id"] for x in data.evidence_docs(tmp_path)] == ["0", "a", "b"]
    assert data.evidence_docs(tmp_path / "khong_co") == []


@pytest.mark.parametrize("swap", [False, True])
def test_publication_after_the_cut_keeps_the_event_out_of_the_chain(tmp_path, swap):
    """Cùng sự kiện, cùng ngày cắt. Bản gốc công bố SAU ngày cắt: không vào chuỗi (CONG_BO_SAU_NGAY_CAT), không APPLIED.
    Bản gốc công bố trước ngày cắt: vào chuỗi và được áp. Vì kho giá bị cắt cùng ngày, một sự kiện có trong dữ liệu luôn có
    ngày không hưởng quyền không muộn hơn ngày cắt; test chỉ đổi ngày công bố để cô lập phép kiểm theo ngày cắt."""
    cut = IDX[OFF + 30]
    late = str((cut + pd.Timedelta(days=3)).date())
    home = _home(tmp_path, _true_raw(), manual=_manual(IDX[OFF]), docs=[_doc(tmp_path, published=None if swap else late)])
    mk = _market(home, as_of=str(cut.date()), research_input="verified")
    if swap:
        assert mk["event_checks"].verify_state.tolist() == [va.OK] and mk["events"].status.tolist() == ["APPLIED"]
    else:
        assert mk["event_checks"].verify_state.tolist() == [va.Q + "CONG_BO_SAU_NGAY_CAT"]
        assert mk["events"].status.tolist() == [data.NOT_IN_CHAIN]
        assert mk["exclude"]["AAA"].iloc[OFF - 21:].all()                 # bị cách ly nên vào cửa sổ loại


# ---------- 3. mặt nạ cửa sổ QĐ-3 ----------

def test_window_bounds_match_config_and_the_risk_gate():
    before, after = data.window_bounds()
    assert (before, after) == (config.CFG["horizon_days"] + 1, config.CFG["quality"]["feature_lookback"] - 1) == (21, 120)
    lim = config.CFG["paper"]["risk_limits"]
    assert (lim["quarantine_sessions_before"], lim["quarantine_sessions_after"]) == (before, after)


AX = pd.bdate_range("2024-01-01", periods=400)


def _checks(**r):
    row = {"ticker": "X", "trade_date": AX[200], "official_trade_date": pd.NaT, "official_ex_date": pd.NaT, "taints": True}
    row.update(r)
    return pd.DataFrame([row])


@pytest.mark.parametrize("pos,hit", [(200 - 21, True), (200 - 22, False), (200 + 120, True), (200 + 121, False),
                                     (200, True)])
def test_window_boundaries(pos, hit):
    m = data.window_exclude(AX, ["X", "Y"], _checks(), 21, 120)
    assert bool(m.at[AX[pos], "X"]) is hit and not m["Y"].any()
    assert int(m["X"].sum()) == 21 + 1 + 120


def test_window_ignores_events_that_do_not_taint_and_unknown_tickers():
    assert not data.window_exclude(AX, ["X"], _checks(taints=False), 21, 120).values.any()
    assert not data.window_exclude(AX, ["Y"], _checks(), 21, 120).values.any()


def test_window_of_a_misdated_event_is_the_union_around_both_dates():
    m = data.window_exclude(AX, ["X"], _checks(official_trade_date=AX[207]), 21, 120)["X"]
    assert m.iloc[200 - 21:207 + 121].all() and not m.iloc[200 - 22] and not m.iloc[207 + 121]
    m2 = data.window_exclude(AX, ["X"], _checks(official_ex_date=AX[207]), 21, 120)["X"]     # chỉ có ngày chính thức
    assert m2.equals(m)


def test_window_near_the_axis_edges():
    m = data.window_exclude(AX, ["X"], _checks(trade_date=AX[10]), 21, 120)["X"]
    assert m.iloc[:131].all() and not m.iloc[131]
    m = data.window_exclude(AX, ["X"], _checks(trade_date=AX[-1] + pd.Timedelta(days=30)), 21, 120)["X"]
    assert m.iloc[-21:].all() and not m.iloc[-22]                      # ngày sau trục: vị trí len(trục)


def test_misdated_real_pattern_end_to_end(tmp_path):
    """Kiểu TCB/VCB: sự kiện tay ở ngày chuỗi gãy (W phiên trước ngày chính thức), bản gốc ghi ngày chính thức. LECH_NGAY:
    cửa sổ là hợp của hai cửa sổ."""
    home = _home(tmp_path, _partial(), manual=_manual(IDX[OFF - W]), docs=[_doc(tmp_path)])
    mk = _market(home, research_input="verified")
    r = mk["event_checks"].iloc[0]
    assert r.verify_state == va.Q + "LECH_NGAY" and r.trade_date == IDX[OFF - W] and r.official_trade_date == IDX[OFF]
    ex = mk["exclude"]["AAA"]
    assert ex.iloc[OFF - W - 21:].all() and not ex.iloc[:OFF - W - 21].any()
    assert not mk["exclude"][TICKERS[1:]].values.any()
    assert mk["eligible"].equals(mk["raw_close"].notna() & ~mk["exclude"])


# ---------- 4. đi trọn load_market("verified") → dataset(exclude=...) ----------

@pytest.fixture
def verified_partial(tmp_path):
    home = _home(tmp_path, _partial(), yahoo=_yahoo(), docs=[_doc(tmp_path)])
    mk = _market(home, research_input="verified")
    assert mk["event_checks"].verify_state.tolist() == [va.Q + "GIA_GAY_TRUOC_NGAY_HUONG_QUYEN"]
    return mk


def test_dataset_masks_window_cells_and_keeps_dates_without_exclusion(verified_partial):
    mk = verified_partial
    ex = mk["exclude"]
    assert ex["AAA"].iloc[OFF - 21:].all() and not ex["AAA"].iloc[:OFF - 21].any()
    ds = features.dataset(mk["close"], mk["volume"], H, mk["bad"], exclude=ex)
    ref = features.dataset(mk["close"], mk["volume"], H, mk["bad"])
    inside = ds.xs("AAA", level="ticker").loc[IDX[OFF - 21]:]
    assert inside.isna().all().all()                                    # mọi đặc trưng và nhãn của ô bị loại là NaN
    clean = [d for d in IDX if not ex.loc[d].any()]
    pd.testing.assert_frame_equal(ds.loc[clean], ref.loc[clean])        # ngày không mã nào bị loại: giữ nguyên


def test_other_tickers_equal_the_result_with_the_excluded_ticker_absent(verified_partial):
    mk = verified_partial
    ex = mk["exclude"]
    ds = features.dataset(mk["close"], mk["volume"], H, mk["bad"], exclude=ex)
    others = TICKERS[1:]
    alone = features.dataset(mk["close"][others], mk["volume"][others], H, mk["bad"][others])
    days = [d for d in IDX if ex.at[d, "AAA"]]
    got = ds.loc[(days, others), :]
    want = alone.loc[(days, others), :]
    pd.testing.assert_frame_equal(got, want)
    assert got["rel_mom_20"].notna().any() and got["y"].notna().any()   # có giá trị thật để so, không phải toàn NaN


# ---------- 5. derivation_id, pit_label, pit_gaps ----------

def _ids(home, **kw):
    return _market(home, **kw)["derivation_id"]


def test_derivation_id_depends_only_on_inputs(tmp_path):
    home = _home(tmp_path, _partial(), yahoo=_yahoo(), docs=[_doc(tmp_path)])
    a = _ids(home, research_input="verified")
    assert a.startswith("RI-") and a == _ids(home, research_input="verified")
    assert a != _ids(home) and a != _ids(home, as_of=str(IDX[-2].date()), research_input="verified")
    assert a != _ids(home, cfg={"horizon_days": 10}, research_input="verified")
    m = home.joinpath(*data.EVIDENCE_DIR) / "EVIDENCE_MANIFEST_FX.json"
    j = json.loads(m.read_text(encoding="utf-8"))
    j["source_documents"][0]["issuer"] += " "
    m.write_text(json.dumps(j, ensure_ascii=False), encoding="utf-8")
    b = _ids(home, research_input="verified")
    assert b != a
    p = home / config.CFG["corporate_actions"]["manual"]
    p.write_bytes(p.read_bytes() + b"\n")
    c = _ids(home, research_input="verified")
    assert c != b
    f = sorted((home / config.CFG["data"]["store_dir"]).glob("*.csv"))[-1]
    f.write_bytes(f.read_bytes().replace(b"fixture", b"fixturE", 1))
    assert _ids(home, research_input="verified") != c


def test_legacy_derivation_id_does_not_depend_on_unused_evidence(tmp_path):
    home = _home(tmp_path, _walk(), docs=[_doc(tmp_path)])
    a = _ids(home)
    (home.joinpath(*data.EVIDENCE_DIR) / "EVIDENCE_MANIFEST_FX.json").write_text('{"source_documents": []}', encoding="utf-8")
    assert _ids(home) == a


def _code_copies(tmp, edit=None):
    out = []
    for f in data.CODE_FILES:
        q = tmp / "ma" / f.name
        q.parent.mkdir(parents=True, exist_ok=True)
        b = f.read_bytes()
        q.write_bytes(edit(f.name, b) if edit else b)
        out.append(q)
    return tuple(out)


def test_derivation_id_changes_with_the_algorithm_version_when_data_is_unchanged(tmp_path, monkeypatch):
    """Vòng chấm 1, BLOCKER 2: cùng giá gốc, config, sự kiện và bản gốc; chỉ đổi mã tạo dữ liệu (ví dụ window_exclude) thì
    derivation_id phải đổi. Bản sao giống hệt mã thì id giữ nguyên (dấu vân tay theo nội dung, không theo đường dẫn)."""
    home = _home(tmp_path / "nha", _partial(), yahoo=_yahoo(), docs=[_doc(tmp_path / "nha")])
    ids = {}
    for mode in ("legacy", "verified"):
        ids[mode] = _ids(home, research_input=mode)
        monkeypatch.setattr(data, "CODE_FILES", _code_copies(tmp_path / mode))
        assert _ids(home, research_input=mode) == ids[mode]
        changed = _code_copies(tmp_path / (mode + "_doi"), lambda n, b: b.replace(b"pos - before", b"pos-before", 1)
                               if n == "data.py" else b)
        monkeypatch.setattr(data, "CODE_FILES", changed)
        assert _ids(home, research_input=mode) != ids[mode]
        monkeypatch.undo()
    assert data.code_fingerprint().startswith("code-sha256:")
    m = va.derivation_manifest(root=home, cfg=config.CFG, as_of=IDX[-1], docs=[], ev=NONE, code_commit=data.code_fingerprint())
    assert m["code_commit"] == data.code_fingerprint()                 # dấu vân tay nằm ở trường code_commit (ADR-0009)


def test_publication_date_comes_only_from_pinned_evidence(tmp_path):
    """Làm rõ C2 (vòng chấm 1): cột published_at trong CSV sự kiện tay không được đọc (adjust giữ EV_COLS), nên C2 đạt vì sự
    kiện không có bản gốc ghim (THIEU_BANG_CHUNG). Ngày công bố chỉ lấy từ bản gốc đã ghim; với bản gốc công bố sau ngày cắt
    thì trạng thái là CONG_BO_SAU_NGAY_CAT, như test_publication_after_the_cut_keeps_the_event_out_of_the_chain."""
    cut = IDX[OFF + 30]
    m = _manual(IDX[OFF]).assign(published_at=str(IDX[-1].date()))
    home = _home(tmp_path, _true_raw(), manual=m)
    with patch.object(config, "ROOT", home), patch.object(adjust, "ROOT", home):
        assert "published_at" not in adjust.load_manual().columns
    mk = _market(home, as_of=str(cut.date()), research_input="verified")
    assert mk["event_checks"].verify_state.tolist() == [va.Q + "THIEU_BANG_CHUNG"]
    m2 = home.joinpath(*data.EVIDENCE_DIR) / "EVIDENCE_MANIFEST_FX.json"
    m2.parent.mkdir(parents=True, exist_ok=True)
    m2.write_text(json.dumps({"source_documents": [_doc(home, published=str(IDX[-1].date()))]}), encoding="utf-8")
    mk = _market(home, as_of=str(cut.date()), research_input="verified")
    assert mk["event_checks"].verify_state.tolist() == [va.Q + "CONG_BO_SAU_NGAY_CAT"]


def test_pit_label_and_gaps(tmp_path):
    home = _home(tmp_path, _walk())
    leg, ver = _market(home), _market(home, research_input="verified")
    assert leg["pit_label"] == ver["pit_label"] == "RETROSPECTIVE"
    assert ver["research_input"] == "verified" and not any("chưa kiểm" in g for g in ver["pit_gaps"])
    for g in ("rổ theo cấu hình", "chưa lọc ngày nghỉ"):
        assert any(g in x for x in leg["pit_gaps"]) and any(g in x for x in ver["pit_gaps"])


def test_real_store_verified_runs_and_is_reported():
    mk = data.load_market(research_input="verified")
    ch = mk["event_checks"]
    assert int(ch.in_verified_chain.sum()) >= 16 and mk["pit_label"] == "RETROSPECTIVE"
    assert not ((mk["events"].status == "APPLIED") & ~ch.in_verified_chain.astype(bool)).any()
    assert mk["eligible"].shape == mk["raw_close"].shape


def test_tests_do_not_touch_the_repo():
    assert subprocess.check_output(["git", "status", "--porcelain", "--", "data", "paper", "state", "reports"],
                                   cwd=REPO) == b""
