"""Chuỗi 'verified-adjusted': CỔNG BẰNG CHỨNG cho sự kiện quyền cổ phiếu (ADR-0009 điều 2, 3 và 7).

Module này CHỈ ĐỌC. Nó không sửa `engine/adjust.py`, không sửa kho raw, không ghi đĩa, không gọi mạng.
Chuỗi điều chỉnh hiện hành (`adjust.build_events` / `adjust.factors`) giữ nguyên nghĩa của nó: ở đó `ex_date` là ngày
CHUỖI GIÁ GỐC GÃY trong kho, chưa chắc là ngày giao dịch không hưởng quyền chính thức, và trạng thái `source_status`
(ví dụ CAN_DOI_CHIEU) chỉ được chép sang kết quả, KHÔNG tham gia quyết định APPLIED. Quyết định APPLIED chỉ dựa vào việc
biên độ giá sau điều chỉnh nằm trong sàn. Đó là nguyên nhân một sự kiện chưa đối chiếu vẫn thành APPLIED.

Cổng này dựng một chuỗi RIÊNG. Một sự kiện cổ phiếu chỉ vào chuỗi đó khi đủ cả sáu điều kiện:
  1. có bản gốc đã ghim trong manifest (source_id, url, issuer, path, sha256 đều là chuỗi không rỗng), tệp tồn tại, đúng
     sha256 và số byte; loại sự kiện in trên văn bản (`event_type`) TRÙNG ĐÚNG loại của sự kiện engine (không coi
     `stock_split` và `stock_dividend` là một);
  2. có ngày công bố (`published_at`) hợp lệ: có mặt, không muộn hơn ngày cắt `as_of`, sớm hơn ngày không hưởng quyền;
  3. tỷ lệ in trên văn bản (`official_ratio`) là số hữu hạn dương và trùng tỷ lệ của sự kiện;
  4. NGÀY GIAO DỊCH mà engine đang áp sự kiện trùng ngày giao dịch của ngày không hưởng quyền chính thức;
  5. không có sự kiện nào khác của cùng bản gốc được engine áp ở ngày khác; "cùng bản gốc" xét theo cả `source_id` lẫn
     sha256 của tệp, nên đổi hay bỏ `source_id` không lách được kiểm tra này;
  6. trạng thái engine nằm trong danh sách cho phép VERIFIABLE = APPLIED hoặc DA_NAM_TRONG_GIA_NGUON (giá gốc đã chứa
     điều chỉnh). Mọi trạng thái khác, kể cả trạng thái engine chưa biết, đều bị cách ly.
Không đạt thì CÁCH LY: không đưa vào hệ số của chuỗi kiểm chứng, và mọi ô giá của mã đó TRƯỚC ngày giao dịch của sự kiện bị
đánh dấu TAINTED (không bảo đảm so sánh được qua sự kiện). Cổng KHÔNG đổi ngày hộ và KHÔNG suy ngày đúng từ bước nhảy giá.
Sự kiện tiền mặt chưa có bằng chứng ghim nên chưa được xét; chuỗi kiểm chứng là chuỗi giá gốc cộng các sự kiện cổ phiếu
đã kiểm, KHÔNG điều chỉnh cổ tức tiền mặt.
Module chưa được nối vào vòng học hay `data.sources` (ADR-0009 điều 7)."""
from __future__ import annotations

import hashlib
import json
import pathlib

import numpy as np
import pandas as pd

from . import adjust

STOCK = adjust.STOCK
IMPACT = ("APPLIED", "KHONG_KHOP", "DA_NAM_TRONG_GIA_NGUON", "LOI_TY_LE")   # trạng thái engine cho thấy có chỗ gãy dữ liệu thật
NO_DATA = ("KHONG_CO_MA", "CHUA_DEN_HAN", "NGOAI_DU_LIEU")                   # không có cửa sổ giá để so
VERIFIABLE = ("APPLIED", "DA_NAM_TRONG_GIA_NGUON")                           # danh sách cho phép: chỉ hai trạng thái này được kiểm
DOC_REQUIRED = ("source_id", "url", "issuer", "path", "sha256")
WINDOW_DAYS = 45          # bản gốc phải có ngày không hưởng quyền cách ngày engine không quá ngần này ngày lịch
RATIO_TOL = 1e-9

OK = "DA_KIEM_CHUNG"
NA_NODATA = "KHONG_ANH_HUONG"
NA_CASH = "KHONG_XET_TIEN_MAT"
Q = "CACH_LY_"
STATES = (OK, NA_NODATA, NA_CASH, Q + "THIEU_BANG_CHUNG", Q + "BANG_CHUNG_HONG", Q + "THIEU_NGAY_CONG_BO",
          Q + "CONG_BO_SAU_NGAY_CAT", Q + "CONG_BO_SAU_NGAY_HUONG_QUYEN", Q + "TY_LE_LECH", Q + "LECH_NGAY",
          Q + "XUNG_DOT_NGAY", Q + "GIA_KHONG_KHOP_TY_LE", Q + "LOAI_SU_KIEN_LECH",
          Q + "TRANG_THAI_ENGINE_KHONG_HOP_LE")

NEW_COLS = ["verify_state", "verify_reason", "evidence_id", "official_ex_date", "official_trade_date",
            "session_offset", "in_verified_chain", "taints"]


def _ts(x):
    if x is None:
        return pd.NaT
    try:
        v = pd.to_datetime(x, errors="coerce")
    except Exception:                       # noqa: BLE001
        return pd.NaT
    return v if isinstance(v, pd.Timestamp) else pd.NaT


def sha256_file(p) -> str:
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def load_evidence(manifest_paths) -> list[dict]:
    """Đọc các EVIDENCE_MANIFEST.json (lược đồ `source_documents[]`, ADR-0009 điều 2). Không có tệp thì trả về danh sách rỗng."""
    docs = []
    for mp in manifest_paths or []:
        p = pathlib.Path(mp)
        if not p.is_file():
            continue
        j = json.loads(p.read_text(encoding="utf-8"))
        for d in j.get("source_documents", []):
            docs.append({**d, "_manifest": p.name})
    return docs


def _positive_number(x):
    """Số hữu hạn dương (không nhận bool, chuỗi, None, NaN, vô cực, 0, số âm)."""
    if isinstance(x, bool) or not isinstance(x, (int, float, np.integer, np.floating)):
        return None
    v = float(x)
    return v if np.isfinite(v) and v > 0 else None


def _doc_problem(d, base):
    for k in DOC_REQUIRED:
        v = d.get(k)
        if not isinstance(v, str) or not v.strip():
            return f"mục manifest thiếu trường {k} (phải là chuỗi không rỗng)"
    p = pathlib.Path(base) / d["path"]
    if not p.is_file():
        return "tệp bản gốc không tồn tại tại đường dẫn đã ghi"
    b = p.read_bytes()
    if hashlib.sha256(b).hexdigest() != d["sha256"]:
        return "sha256 của tệp không khớp manifest"
    if d.get("bytes") is not None and len(b) != int(d["bytes"]):
        return "số byte của tệp không khớp manifest"
    return None


def _match(ticker, ex_date, typ, docs):
    """Bản gốc cổ phiếu của cùng mã có ngày không hưởng quyền gần ngày của sự kiện nhất, trong WINDOW_DAYS ngày lịch.

    Bản gốc khác loại vẫn được ghép (ưu tiên bản cùng loại khi cùng khoảng cách) để `_judge` CÁCH LY với lý do rõ ràng
    và để bản gốc đó vẫn tham gia kiểm tra trùng ngày, thay vì bị bỏ qua lặng lẽ."""
    best = None
    for d in docs:
        if d.get("ticker") != ticker or d.get("event_type") not in STOCK:
            continue
        od = _ts(d.get("official_ex_date"))
        if pd.isna(od) or pd.isna(ex_date):
            continue
        key = (abs((od - ex_date).days), d.get("event_type") != typ)
        if key[0] <= WINDOW_DAYS and (best is None or key < best[0]):
            best = (key, d)
    return best[1] if best else None


def _judge(r, d, close, base, as_of):
    """(state, reason, official_trade_date, offset) cho một sự kiện cổ phiếu đã khớp bản gốc d."""
    bad = _doc_problem(d, base)
    if bad:
        return Q + "BANG_CHUNG_HONG", bad, pd.NaT, np.nan
    if d.get("event_type") != r["type"]:
        return (Q + "LOAI_SU_KIEN_LECH", f"văn bản là {d.get('event_type')}, engine ghi sự kiện là {r['type']}; "
                "không coi hai loại là một", pd.NaT, np.nan)
    pub, off = _ts(d.get("published_at")), _ts(d.get("official_ex_date"))
    if pd.isna(pub):
        return Q + "THIEU_NGAY_CONG_BO", "bản gốc không có published_at; không lấy ngày hưởng quyền thay ngày công bố", pd.NaT, np.nan
    if pub > as_of:
        return Q + "CONG_BO_SAU_NGAY_CAT", f"công bố {pub.date()} sau ngày cắt {as_of.date()}", pd.NaT, np.nan
    if pub >= off:
        return Q + "CONG_BO_SAU_NGAY_HUONG_QUYEN", f"công bố {pub.date()} không sớm hơn ngày không hưởng quyền {off.date()}", pd.NaT, np.nan
    ro, rv = d.get("official_ratio"), r["ratio"]
    fo, fv = _positive_number(ro), _positive_number(rv)
    if fo is None or fv is None:
        return Q + "TY_LE_LECH", f"tỷ lệ không hợp lệ (văn bản {ro!r}, sự kiện {rv!r}); phải là số hữu hạn dương", pd.NaT, np.nan
    if not abs(fo - fv) <= RATIO_TOL:
        return Q + "TY_LE_LECH", f"tỷ lệ in trên văn bản {ro} khác tỷ lệ sự kiện {rv}", pd.NaT, np.nan
    sess = close[r["ticker"]].dropna().index
    pos = int(sess.searchsorted(off))
    if pos >= len(sess):
        return Q + "LECH_NGAY", f"ngày không hưởng quyền chính thức {off.date()} nằm sau dữ liệu giá hiện có", pd.NaT, np.nan
    otd, td = sess[pos], r["trade_date"]
    if td != otd:
        offset = int(sess.get_loc(td)) - pos if td in sess else np.nan
        return (Q + "LECH_NGAY",
                f"engine áp ngày {td.date()}, ngày không hưởng quyền chính thức {off.date()} (phiên {otd.date()}); "
                f"lệch {offset:+d} phiên" if offset == offset else f"engine áp ngày {td.date()} khác phiên {otd.date()}",
                otd, offset)
    if r["status"] == "KHONG_KHOP":
        return Q + "GIA_KHONG_KHOP_TY_LE", "ngày và tỷ lệ khớp bản gốc nhưng bước giá không giải thích được bằng tỷ lệ", otd, 0.0
    if r["status"] not in VERIFIABLE:
        return (Q + "TRANG_THAI_ENGINE_KHONG_HOP_LE", f"trạng thái engine {r['status']} không nằm trong danh sách cho phép "
                f"{', '.join(VERIFIABLE)}", otd, 0.0)
    return OK, "bản gốc ghim hợp lệ, ngày công bố hợp lệ, tỷ lệ và ngày áp dụng khớp", otd, 0.0


def verify_events(events, close, docs, *, evidence_root, as_of) -> pd.DataFrame:
    """Gắn trạng thái kiểm chứng cho từng sự kiện của `adjust.build_events`. Không đổi các cột gốc."""
    as_of = pd.Timestamp(as_of)
    recs, matched = [], []
    for r in events.to_dict("records"):
        r.update(verify_state=None, verify_reason="", evidence_id="", official_ex_date=pd.NaT,
                 official_trade_date=pd.NaT, session_offset=np.nan)
        d = None
        if r["type"] not in STOCK:
            r["verify_state"], r["verify_reason"] = NA_CASH, "sự kiện tiền mặt: chưa có bằng chứng ghim, không vào chuỗi kiểm chứng"
        elif r["status"] in NO_DATA:
            r["verify_state"], r["verify_reason"] = NA_NODATA, f"trạng thái engine {r['status']}: không có cửa sổ giá để so"
        else:
            d = _match(r["ticker"], r["ex_date"], r["type"], docs)
            if d is None:
                r["verify_state"], r["verify_reason"] = Q + "THIEU_BANG_CHUNG", "không có bản gốc ghim cho sự kiện này trong manifest"
            else:
                r["evidence_id"], r["official_ex_date"] = d.get("source_id", ""), _ts(d.get("official_ex_date"))
                r["verify_state"], r["verify_reason"], r["official_trade_date"], r["session_offset"] = \
                    _judge(r, d, close, evidence_root, as_of)
        recs.append(r)
        matched.append(d)
    # một bản gốc mà engine áp ở hơn một ngày: không bên nào được coi là đã kiểm. Khóa nhận dạng bản gốc gồm source_id
    # (nếu có) VÀ sha256 nội dung khai báo, nên một bản gốc thiếu source_id, hoặc cùng tệp khai hai source_id, vẫn bị bắt.
    def _keys(d):
        if d is None:
            return []
        return [("sid", v.strip()) if k == "source_id" else ("sha", v.strip().lower())
                for k in ("source_id", "sha256") if isinstance((v := d.get(k)), str) and v.strip()]

    by_doc: dict[tuple, set] = {}
    for r, d in zip(recs, matched):
        if pd.notna(r["trade_date"]):
            for k in _keys(d):
                by_doc.setdefault(k, set()).add(r["trade_date"])
    for r, d in zip(recs, matched):
        dates = set().union(*[by_doc.get(k, set()) for k in _keys(d)]) if d is not None else set()
        if r["verify_state"] == OK and len(dates) > 1:
            r["verify_state"] = Q + "XUNG_DOT_NGAY"
            r["verify_reason"] = ("cùng bản gốc nhưng engine áp ở nhiều ngày: "
                                  + ", ".join(sorted(str(x.date()) for x in dates)))
    out = pd.DataFrame(recs, columns=list(events.columns) + [c for c in NEW_COLS if c not in ("in_verified_chain", "taints")])
    # Phòng thủ hai lớp: vào chuỗi kiểm chứng chỉ khi trạng thái kiểm là OK VÀ trạng thái engine nằm trong danh sách cho phép.
    out["in_verified_chain"] = (out["verify_state"] == OK) & out["status"].isin(VERIFIABLE)
    # Đóng khi nghi ngờ: mọi sự kiện bị cách ly có ngày giao dịch đều nhiễm ô trước nó, trừ khi engine báo không có cửa sổ giá.
    # (Trạng thái engine chưa biết cũng nhiễm.)
    out["taints"] = (out["verify_state"].str.startswith(Q) & ~out["status"].isin(NO_DATA)
                     & out["trade_date"].notna())
    return out


def verified_factors(index, columns, ev):
    """Hệ số giá/chia tách của chuỗi kiểm chứng: cùng công thức `adjust.factors`, nhưng chỉ sự kiện đã kiểm và APPLIED."""
    e = ev.copy()
    e["status"] = np.where(e["in_verified_chain"] & (e["status"] == "APPLIED"), "APPLIED", "KHONG_VAO_CHUOI_KIEM_CHUNG")
    return adjust.factors(index, columns, e)


def taint_mask(index, columns, ev) -> pd.DataFrame:
    """True ở ô (ngày, mã) nằm TRƯỚC ngày giao dịch của một sự kiện bị cách ly có chỗ gãy dữ liệu thật."""
    m = pd.DataFrame(False, index=index, columns=columns)
    for r in ev[ev["taints"]].itertuples(index=False):
        if r.ticker in m.columns:
            m.loc[m.index < r.trade_date, r.ticker] = True
    return m


def coverage(ev, taint, window=252) -> dict:
    stock = ev[ev["type"].isin(STOCK)]
    w = taint.iloc[-window:] if len(taint) else taint
    return {"stock_events": int(len(stock)), "cash_events_not_assessed": int((ev["verify_state"] == NA_CASH).sum()),
            "by_state": {k: int(v) for k, v in stock["verify_state"].value_counts().sort_index().items()},
            "in_verified_chain": int(ev["in_verified_chain"].sum()),
            "tickers": int(taint.shape[1]), "tickers_tainted_in_window": int(w.any().sum()) if w.size else 0,
            "tainted_share_all": round(float(taint.values.mean()), 4) if taint.size else 0.0,
            "tainted_share_window": round(float(w.values.mean()), 4) if w.size else 0.0, "window_sessions": int(window)}


def _files_hash(root, rels):
    h = hashlib.sha256()
    for rel in rels:
        h.update(f"{rel}:{sha256_file(pathlib.Path(root) / rel)}\n".encode())
    return h.hexdigest()


def derivation_manifest(*, root, cfg, as_of, docs, ev, code_commit, created_at=None) -> dict:
    """Manifest dẫn xuất theo ADR-0009 điều 2. `derivation_id` chỉ phụ thuộc đầu vào, không phụ thuộc `created_at`."""
    root = pathlib.Path(root)
    raw_rels = [p for p in [cfg["data"]["store"]] if (root / p).is_file()]
    d = root / cfg["data"]["store_dir"]
    raw_rels += sorted(str(p.relative_to(root)) for p in d.glob("*.csv")) if d.is_dir() else []
    ce = [cfg["corporate_actions"]["manual"], cfg["corporate_actions"]["yahoo_cache"]]
    ce = [p for p in ce if (root / p).is_file()]
    cfg_p = root / "config.yaml"
    srcs = [{k: d_.get(k) for k in ("source_id", "url", "issuer", "published_at", "sha256", "bytes")} for d_ in docs]
    srcs.sort(key=lambda x: str(x["source_id"]))
    core = ev[["ticker", "ex_date", "type", "status", "verify_state", "trade_date", "in_verified_chain"]]
    digest = hashlib.sha256(core.to_csv(index=False).encode()).hexdigest()
    m = {"derivation_id": "", "created_at": created_at, "as_of": str(pd.Timestamp(as_of).date()),
         "raw_snapshot_hash": _files_hash(root, raw_rels), "raw_snapshot_files": raw_rels, "code_commit": code_commit,
         "config_hash": sha256_file(cfg_p) if cfg_p.is_file() else "", "corporate_events_hash": _files_hash(root, ce),
         "source_documents": srcs, "events_verification_digest": digest,
         "validity_scope": "RETROSPECTIVE — dựng lại từ bản gốc đã ghim; không có vintage; không phải point-in-time đầy đủ (ADR-0009 điều 4)",
         "chain": "verified-adjusted: giá gốc + sự kiện cổ phiếu đã kiểm; KHÔNG điều chỉnh cổ tức tiền mặt", "supersedes": None}
    key = {k: m[k] for k in ("as_of", "raw_snapshot_hash", "code_commit", "config_hash", "corporate_events_hash",
                              "source_documents", "events_verification_digest")}
    m["derivation_id"] = "VA-" + hashlib.sha256(json.dumps(key, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]
    return m
