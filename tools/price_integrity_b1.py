"""PRICE-INTEGRITY B1: đo đường giá nghiên cứu, CHỈ ĐỌC. In JSON ra stdout; không ghi tệp, không gọi mạng, không fit mô hình,
không đăng ký lần thử (L-06 không áp vì không có giả thuyết đầu tư nào được kiểm).

Đo bốn việc trên kho giá thật tại --as-of (mặc định 2026-11-20):
  1. inputs: sha256 các tệp đầu vào (kho giá, sự kiện tay, sự kiện Yahoo tải lại mỗi vòng, manifest bằng chứng).
  2. partial_window: bước giá ngoài biên trong 15 phiên trước mỗi sự kiện cổ phiếu mà tỷ lệ giải thích được; và phép thử lưới
     bước giá/lô cho cửa sổ TCB 2024 và VCB 2025 (bước giá HOSE <10.000: 10; <50.000: 50; còn lại 100 đồng — quy định
     chưa ghim văn bản gốc trong kho, dùng như giả định kiểm tra, không như bằng chứng pháp lý).
  3. policies: tác động lên cờ chất lượng, ô feature, ô nhãn của bốn cách xử lý sự kiện chưa xác minh (P0 hiện hành, P1a bỏ sự
     kiện tay chưa đối chiếu, P1b bỏ mọi sự kiện chưa DA_KIEM_CHUNG, P2 dời ngày sang ngày HOSE, P3 chuỗi kiểm chứng + nhiễm ô);
     và độ nhạy khi tỷ lệ VCB sai trong biên.
  4. calendar: các ngày mà MỌI dòng có khối lượng 0 (giá thường giữ nguyên) — dòng của nguồn vào ngày không giao dịch.
"Phiên suy từ dữ liệu" (khóa JSON `sessions_inferred_from_data`, `*_inferred_sessions*`) là số ngày trên trục ngày của panel
SAU KHI bỏ các ngày mọi mã có dòng đều có khối lượng 0. Đó là số suy từ dữ liệu nguồn, KHÔNG phải lịch giao dịch HOSE (lịch
gốc chưa ghim trong kho); ngày nghỉ mà nguồn không có dòng, hay ngày giao dịch mà nguồn mất dữ liệu, đều không được nhận ra.
Dùng: python tools/price_integrity_b1.py [--as-of YYYY-MM-DD]"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

from engine import adjust, data, features, verified_adjust as va
from engine.config import CFG, ROOT

MANIFESTS = ["data/evidence/corporate_actions/EVIDENCE_MANIFEST.json",
             "data/evidence/corporate_actions/EVIDENCE_MANIFEST_2026H2.json"]
WINDOWS = [("TCB", 2.0, "2024-06-11", "2024-06-20"), ("VCB", 1.495, "2025-03-03", "2025-03-12")]
# Cửa sổ lợi suất qua sự kiện dùng để so các phương án. Độ dài là số bước giữa hai ngày trên trục ngày của panel; công cụ
# in ra số đó cùng số phiên suy từ dữ liệu (bỏ ngày mọi mã khối lượng 0; không phải lịch HOSE), không gọi chung là "20 phiên".
SESSION_DEFINITION = ("Phiên suy từ dữ liệu: ngày trên trục ngày của panel, bỏ ngày mà mọi mã có dòng đều có khối lượng 0. "
                      "Số suy từ dữ liệu nguồn, KHÔNG phải lịch giao dịch HOSE (lịch gốc chưa ghim trong kho).")
RETURN_WINDOWS = [("TCB", "2024-06-04", "2024-06-26"), ("VCB", "2025-02-25", "2025-03-17")]


def _all_zero_volume_days(raw, vol):
    present = raw.notna()
    zero = (vol == 0) & present
    return [d for d in raw.index if present.loc[d].any() and zero.loc[d][present.loc[d]].all()]


def window_len(index, a, b, skip=()):
    """(số bước trên trục ngày, số phiên suy từ dữ liệu — không phải lịch HOSE) từ ngày a tới ngày b, không tính a."""
    a, b = pd.Timestamp(a), pd.Timestamp(b)
    days = index[(index > a) & (index <= b)]
    return int(len(days)), int(sum(d not in skip for d in days))


def _sha(rel):
    p = ROOT / rel
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


def _tick(p):
    return 10 if p < 10000 else (50 if p < 50000 else 100)


def _on(x, step, tol=0.02):
    q = x / step
    return bool(abs(q - round(q)) < tol)


def panel(as_of):
    s = data.load_store()
    s = s[s.date <= as_of]
    piv = {c: s.pivot(index="date", columns="ticker", values=c).sort_index() for c in ("close", "volume", "observed_at")}
    keep = piv["close"].columns[piv["close"].notna().sum() > 250]
    return piv["close"][keep], piv["volume"][keep], piv["observed_at"][keep]


def partial_window(raw, vol, obs):
    ev = adjust.build_events(raw, obs, adjust.load_manual(), adjust.load_yahoo())
    L = adjust.limits(raw.index, raw.columns)
    _, K = adjust.obs_returns(raw)
    hits = []
    for e in ev[ev.type.isin(adjust.STOCK) & ev.trade_date.notna()].itertuples():
        sr = raw[e.ticker].dropna()
        pos = sr.index.get_loc(e.trade_date)
        for j in range(max(1, pos - 15), pos + 1):
            d = sr.index[j]
            x = sr.iloc[j] / sr.iloc[j - 1] - 1
            up, dn = adjust.bands(L.at[d, e.ticker], K.at[d, e.ticker])
            if not (-dn <= x <= up) and (-dn <= (1 + x) * float(e.ratio) - 1 <= up):
                hits.append({"ticker": e.ticker, "event_ex_date": str(e.ex_date.date()), "source": str(e.source)[:40],
                             "source_status": e.source_status, "engine_status": e.status, "ratio": float(e.ratio),
                             "break_date": str(d.date()), "break_raw_return": round(float(x), 4),
                             "sessions_before_event_trade_date": int(pos - j)})
    grid = {}
    for t, ratio, a, b in WINDOWS:
        sr, v = raw[t].dropna(), vol[t]
        ia, ib = sr.index.get_loc(pd.Timestamp(a)), sr.index.get_loc(pd.Timestamp(b))
        seg = {}
        for k, x in {"pre20": sr.iloc[ia - 20:ia], "window": sr.iloc[ia:ib], "post20": sr.iloc[ib:ib + 20]}.items():
            vv = v.loc[x.index]
            seg[k] = {"sessions": int(len(x)), "from": str(x.index[0].date()), "to": str(x.index[-1].date()),
                      "close_on_tick_grid": int(sum(_on(p, _tick(p)) for p in x)),
                      "close_x_ratio_on_tick_grid": int(sum(_on(p * ratio, _tick(p * ratio)) for p in x)),
                      "volume_on_lot_100": int(sum(_on(q, 100) for q in vv)),
                      "volume_div_ratio_on_lot_100": int(sum(_on(q / ratio, 100) for q in vv)),
                      "median_volume": int(vv.median())}
        seg["raw_step_at_window_start"] = round(float(sr.iloc[ia] / sr.iloc[ia - 1] - 1), 4)
        seg["raw_step_at_hose_ex_date"] = round(float(sr.iloc[ib] / sr.iloc[ib - 1] - 1), 4)
        grid[t] = seg
    return hits, grid


def _run(raw, vol, obs, manual, yahoo, mask=None, factors=None):
    ev = adjust.build_events(raw, obs, manual, yahoo)
    F, S = factors if factors is not None else adjust.factors(raw.index, raw.columns, ev)
    adj = raw * F
    bad, _, flags = adjust.quality(adj)
    ds = features.dataset(adj.ffill(limit=5), (vol / S).fillna(0), CFG["horizon_days"], bad)
    if mask is not None:
        ds.loc[mask.reindex(index=adj.index, columns=adj.columns).fillna(False).values.ravel(), :] = np.nan
    return ev, adj, flags, ds


def _summary(name, ev, adj, flags, ds, base=None, chain_events=None, skip=()):
    fc = list(features.FEATURES)
    feat, lab = ds[fc], ds["y"]
    complete = feat.notna().all(axis=1) & lab.notna()
    r = {"policy": name,
         "stock_events_in_chain": int(((ev.status == "APPLIED") & ev.type.isin(adjust.STOCK)).sum()) if chain_events is None else chain_events,
         "quality_flags": len(flags),
         "flags_tcb_vcb_2024_2025": [f"{f['ticker']} {f['date']} {f['return']:+.4f}" for f in flags
                                     if f["ticker"] in ("TCB", "VCB") and f["date"][:4] in ("2024", "2025")],
         "feature_cells_valid": int(feat.notna().values.sum()), "label_cells_valid": int(lab.notna().sum()),
         "rows_complete": int(complete.sum())}
    r["returns_across_event"] = []
    for t, a, b in RETURN_WINDOWS:
        steps, real = window_len(adj.index, a, b, skip)
        r["returns_across_event"].append({"ticker": t, "from": a, "to": b, "panel_steps": steps, "sessions_inferred_from_data": real,
                                          "return": round(float(adj.at[pd.Timestamp(b), t] / adj.at[pd.Timestamp(a), t] - 1), 4)})
    if base is not None:
        both = base["y"].notna() & lab.notna()
        d = (base["y"][both] - lab[both]).abs()
        bc = base[fc].notna().all(axis=1) & base["y"].notna()
        r.update({"label_cells_changed_vs_P0": int((d > 1e-9).sum()),
                  "label_max_abs_change_vs_P0": round(float(d.max()), 4) if len(d) else 0.0,
                  "label_cells_lost_vs_P0": int((base["y"].notna() & lab.isna()).sum()),
                  "feature_cells_lost_vs_P0": int((base[fc].notna() & feat.isna()).values.sum()),
                  "rows_complete_lost_vs_P0": {t: int((bc & ~complete)[ds.index.get_level_values(1) == t].sum())
                                               for t in ("TCB", "VCB")}})
    return r


def policies(raw, vol, obs, as_of):
    man, yah = adjust.load_manual(), adjust.load_yahoo()
    skip = set(_all_zero_volume_days(raw, vol))
    ev0, adj0, fl0, ds0 = _run(raw, vol, obs, man, yah)
    out = [_summary("P0_hien_hanh", ev0, adj0, fl0, ds0, skip=skip)]
    m_ok = man[man.source_status == "DA_KIEM_CHUNG"]
    out.append(_summary("P1a_bo_su_kien_tay_chua_doi_chieu", *_run(raw, vol, obs, m_ok, yah), base=ds0, skip=skip))
    out.append(_summary("P1b_bo_moi_su_kien_chua_DA_KIEM_CHUNG", *_run(raw, vol, obs, m_ok,
                                                                        yah[yah.source_status == "DA_KIEM_CHUNG"]), base=ds0, skip=skip))
    m2 = man.copy()
    m2.loc[m2.ticker == "TCB", "ex_date"] = pd.Timestamp("2024-06-20")
    m2.loc[m2.ticker == "VCB", "ex_date"] = pd.Timestamp("2025-03-12")
    r2 = _run(raw, vol, obs, m2, yah)
    s2 = _summary("P2_doi_ngay_su_kien_tay_sang_ngay_HOSE", *r2, base=ds0, skip=skip)
    e2 = r2[0]
    s2["manual_events_after_redate"] = e2[~e2.source.astype(str).str.startswith("yahoo") & e2.type.isin(adjust.STOCK)][
        ["ticker", "ex_date", "status"]].astype(str).values.tolist()
    out.append(s2)
    docs = va.load_evidence([ROOT / m for m in MANIFESTS])
    evv = va.verify_events(ev0, raw, docs, evidence_root=ROOT, as_of=as_of)
    taint = va.taint_mask(raw.index, raw.columns, evv)
    s3 = _summary("P3_chuoi_kiem_chung_cong_nhiem_o", *_run(raw, vol, obs, man, yah, mask=taint,
                                                            factors=va.verified_factors(raw.index, raw.columns, evv)),
                  base=ds0, chain_events=int(evv.in_verified_chain.sum()), skip=skip)
    s3["verify_states"] = {k: int(v) for k, v in evv[evv.type.isin(va.STOCK)].verify_state.value_counts().sort_index().items()}
    s3["tainted_cell_share"] = round(float(taint.values.mean()), 4)
    s3["tickers_tainted_last_252"] = int(taint.iloc[-252:].any().sum())
    out.append(s3)
    steps, real = window_len(raw.index, "2025-02-25", "2025-03-17", skip)
    sens = {"window": {"ticker": "VCB", "from": "2025-02-25", "to": "2025-03-17", "panel_steps": steps,
                       "sessions_inferred_from_data": real}, "rows": []}
    for rr in (1.40, 1.45, 1.495, 1.54, 1.60):
        mm = man.copy()
        mm.loc[mm.ticker == "VCB", "ratio"] = rr
        e = adjust.build_events(raw, obs, mm, yah)
        row = e[(e.ticker == "VCB") & (e.ex_date == pd.Timestamp("2025-03-03"))].iloc[0]
        F, _ = adjust.factors(raw.index, raw.columns, e)
        a = raw["VCB"] * F["VCB"]
        sens["rows"].append({"ratio": rr, "engine_status": row.status, "adjusted_step_at_break": round(float(row.adj_return), 4),
                             "return": round(float(a[pd.Timestamp("2025-03-17")] / a[pd.Timestamp("2025-02-25")] - 1), 4)})
    return out, sens


def calendar(raw, vol):
    present = raw.notna()
    zero = (vol == 0) & present
    days = _all_zero_volume_days(raw, vol)
    same = (raw == raw.ffill().shift(1)) & present
    # Nhãn tại t đo lợi suất từ đóng cửa t+1 tới t+1+h (features.labels_wide): h bước trên trục ngày. Đếm số bước là phiên suy
    # từ dữ liệu (SESSION_DEFINITION; không phải lịch HOSE), để thấy nhãn "h phiên" dài bao nhiêu phiên như vậy.
    h = int(CFG["horizon_days"])
    inferred = (~raw.index.isin(days)).astype(int)
    steps = pd.Series(inferred, index=raw.index).rolling(h).sum().shift(-(1 + h)).dropna().astype(int)
    short = steps[steps < h]
    label_windows = {"horizon_steps": h, "windows": int(len(steps)), "windows_with_fewer_inferred_sessions": int(len(short)),
                     "min_inferred_sessions": int(steps.min()) if len(steps) else None,
                     "inferred_sessions_distribution_when_short": {str(k): int(v) for k, v in short.value_counts().sort_index().items()}}
    return {"sessions_in_store": int(len(raw)), "all_zero_volume_days": len(days), "label_windows": label_windows,
            "all_zero_volume_days_with_unchanged_close": int(sum(bool(same.loc[d][present.loc[d]].all()) for d in days)),
            "by_year": {str(k): int(v) for k, v in pd.Series([d.year for d in days]).value_counts().sort_index().items()},
            "days": [str(d.date()) for d in days], "zero_volume_rows": int(zero.values.sum()),
            "rows": int(present.values.sum())}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--as-of", default="2026-11-20")
    a = ap.parse_args()
    as_of = pd.Timestamp(a.as_of)
    raw, vol, obs = panel(as_of)
    hits, grid = partial_window(raw, vol, obs)
    pol, sens = policies(raw, vol, obs, as_of)
    rels = [CFG["data"]["store"], CFG["corporate_actions"]["manual"], CFG["corporate_actions"]["yahoo_cache"], *MANIFESTS]
    out = {"tool": "tools/price_integrity_b1.py", "as_of": str(as_of.date()), "panel_sessions_x_tickers": list(raw.shape),
           "session_definition": SESSION_DEFINITION,
           "inputs_sha256": {r: _sha(r) for r in rels},
           "note": "Chỉ đọc. data/derived/yahoo_actions.csv được tải lại mỗi vòng học; số đo P0-P3 phụ thuộc bản tại sha256 trên.",
           "partial_window_candidates": hits, "tick_lot_grid": grid, "policies": pol, "vcb_ratio_sensitivity": sens,
           "calendar": calendar(raw, vol)}
    print(json.dumps(out, ensure_ascii=False, indent=1, sort_keys=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
