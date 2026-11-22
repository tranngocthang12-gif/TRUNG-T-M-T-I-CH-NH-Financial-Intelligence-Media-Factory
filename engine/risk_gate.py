"""Cổng rủi ro bằng mã cho sổ giấy (LỆNH R1, QĐ-5 của ADR-0016).

`check` là HÀM THUẦN: nhận danh mục mục tiêu, trạng thái sổ, thị trường và giới hạn; trả PASS hoặc FAIL kèm lý do. Không đọc,
không ghi tệp, không gọi mạng. FAIL thì sổ không mở vị thế mới. Năm điều kiện:
  1. tỷ trọng mỗi mã tại lúc quyết định (giá trị đang giữ, hoặc phần vốn sổ giấy sẽ cấp cho mã mới) ≤ max_weight × NAV;
  2. số phiên thoát vị thế = giá trị vị thế / (max_participation × giá trị giao dịch bình quân adv_sessions phiên)
     ≤ max_exit_days; thiếu giá trị giao dịch bình quân thì không đo được, nên FAIL;
  3. sụt giảm NAV từ đỉnh ≥ max_drawdown thì về tiền mặt và chờ Owner (mục tiêu rỗng);
  4. cửa sổ loại mã theo QĐ-3 (ADR-0016): mã bị loại khỏi mục tiêu khi phiên quyết định t nằm trong
     [k − quarantine_sessions_before, k + quarantine_sessions_after] phiên, với k là phiên áp dụng của một sự kiện cổ phiếu
     đang bị cách ly (chưa vào chuỗi verified-adjusted của engine.verified_adjust); rồi mới xét 1 và 2;
  5. dữ liệu bị đóng băng thì không ra quyết định.
Giới hạn thiếu, còn chữ TODO hoặc không phải số hợp lệ thì FAIL. Giá trị mặc định ở config.yaml (paper.risk_limits) là tham số
thí nghiệm danh nghĩa, không phải khẩu vị rủi ro của Owner.

`market_snapshot` (không thuần, CHỈ ĐỌC) dựng đầu vào thị trường cho `check` từ kho giá, các manifest bằng chứng và
paper/nav.csv dưới ROOT.
"""
from __future__ import annotations

import math
import pathlib

import numpy as np
import pandas as pd

LIMIT_KEYS = ("max_weight", "max_participation", "max_exit_days", "max_drawdown", "adv_sessions",
              "quarantine_sessions_before", "quarantine_sessions_after")
INT_KEYS = ("adv_sessions", "quarantine_sessions_before", "quarantine_sessions_after")
FRACTION_KEYS = ("max_weight", "max_participation", "max_drawdown")
BUY_BUDGET = 0.995          # cùng hệ số engine.paper dùng khi chia vốn cho mã mới: nav / số mã × 0,995
EPS = 1e-12


def limits_problem(limits):
    """Lý do giới hạn không dùng được, hoặc None."""
    if not isinstance(limits, dict):
        return "thiếu paper.risk_limits"
    for k in LIMIT_KEYS:
        v = limits.get(k)
        if isinstance(v, str) and "TODO" in v.upper():
            return f"giới hạn {k} còn TODO"
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v <= 0:
            return f"giới hạn {k} thiếu hoặc không phải số dương hữu hạn ({v!r})"
        if k in FRACTION_KEYS and v >= 1:
            return f"giới hạn {k} phải nhỏ hơn 1 ({v!r})"
    for k in INT_KEYS:
        if int(limits[k]) != limits[k]:
            return f"giới hạn {k} phải là số nguyên"
    return None


def session_axis(price_dates, calendar=None):
    """Trục phiên: các ngày của bảng giá, bỏ ngày mà lịch phiên HOSE (data/trading_calendar.csv) ghi is_session=0, khi lịch
    có và phủ ngày đó. `calendar`: {ngày ISO: 0 hoặc 1} hoặc None."""
    days = pd.DatetimeIndex(sorted(set(pd.to_datetime(list(price_dates)))))
    if calendar:
        days = days[[calendar.get(d.date().isoformat(), 1) != 0 for d in days]]
    return days


def _future_sessions(after, until, calendar=None):
    """Các phiên sau ngày `after` tới hết ngày `until`: theo lịch HOSE ở ngày lịch phủ, ngoài ra theo thứ Hai–thứ Sáu."""
    out = []
    for d in pd.date_range(after + pd.Timedelta(days=1), until, freq="D"):
        flag = calendar.get(d.date().isoformat()) if calendar else None
        if flag == 1 or (flag is None and d.weekday() < 5):
            out.append(d)
    return out


def quarantine_window_hits(t, axis, events, before, after, calendar=None) -> dict:
    """{mã: lý do} cho mã có ít nhất một sự kiện k với t trong [k − before, k + after] phiên (hàm thuần).

    `axis`: trục phiên tới t (session_axis). `events`: [(mã, ngày áp dụng k, mô tả)]. Vị trí của t là phiên cuối ≤ t; vị trí
    của k là phiên đầu ≥ k. Sự kiện sau ngày cuối của trục được đếm tiếp bằng _future_sessions; sự kiện trước ngày đầu của
    trục được đếm lùi theo thứ Hai–thứ Sáu."""
    t = pd.Timestamp(t)
    axis = pd.DatetimeIndex(axis)
    axis = axis[axis <= t]
    if not len(axis):
        return {}
    pos_t = len(axis) - 1
    hits = {}
    for ticker, k, desc in events:
        k = pd.Timestamp(k)
        if k > axis[-1]:
            pos_k = pos_t + len(_future_sessions(axis[-1], k - pd.Timedelta(days=1), calendar)) + 1
        elif k < axis[0]:
            pos_k = -len(pd.bdate_range(k, axis[0] - pd.Timedelta(days=1)))
        else:
            pos_k = int(axis.searchsorted(k))
        if pos_k - before <= pos_t <= pos_k + after:
            gap = pos_t - pos_k
            where = f"{gap} phiên sau" if gap >= 0 else f"{-gap} phiên trước"
            hits.setdefault(ticker, f"{desc}; phiên quyết định ở {where} phiên áp dụng {k.date()} "
                                    f"(cửa sổ −{before}/+{after} phiên, QĐ-3)")
    return hits


def load_calendar(root):
    """{ngày ISO: is_session} từ data/trading_calendar.csv dưới root, hoặc None khi không có tệp hay tệp hỏng."""
    p = pathlib.Path(root) / "data" / "trading_calendar.csv"
    try:
        cal = pd.read_csv(p, dtype={"date": str})
        return {d: int(x) for d, x in zip(cal["date"], cal["is_session"])}
    except Exception:                       # noqa: BLE001 — không có lịch thì đếm theo ngày của bảng giá
        return None


def check(targets, book, market, limits) -> dict:
    """→ {"verdict": "PASS"|"FAIL", "reasons": [...], "targets": [...], "excluded": {...}, "cash_wait_owner": bool}.

    targets: danh sách mã mục tiêu. book: {"nav": số, "positions": {mã: số cổ phiếu}}. market: {"price": {mã: giá},
    "adv_value": {mã: giá trị giao dịch bình quân}, "nav_history": [NAV theo thời gian, gồm NAV hiện tại],
    "quarantined": {mã: lý do}, "frozen": bool}. Thiếu nav_history hay quarantined (None: không đọc/không kiểm được) thì FAIL. `targets` trả về là mục tiêu sau khi loại mã bị cách ly; khi FAIL vì sụt
    giảm thì là danh sách rỗng."""
    out = {"verdict": "FAIL", "reasons": [], "targets": list(targets), "excluded": {}, "cash_wait_owner": False}
    bad = limits_problem(limits)
    if bad:
        out["reasons"].append(bad)
        return out
    if market.get("frozen", True):
        out["reasons"].append("dữ liệu bị đóng băng — không ra quyết định")
        return out
    nav = book.get("nav")
    if isinstance(nav, bool) or not isinstance(nav, (int, float, np.floating)) or not math.isfinite(nav) or nav <= 0:
        out["reasons"].append(f"NAV không hợp lệ ({nav!r})")
        return out
    if market.get("nav_history") is None:
        out["reasons"].append("không đọc được lịch sử NAV — không đo được sụt giảm từ đỉnh")
        return out
    hist = [float(x) for x in market["nav_history"] if x is not None and math.isfinite(float(x))]
    peak = max(hist + [float(nav)])
    dd = 1 - float(nav) / peak
    if dd >= limits["max_drawdown"] - EPS:
        out.update(targets=[], cash_wait_owner=True)
        out["reasons"].append(f"sụt giảm NAV từ đỉnh {dd:.2%} ≥ ngưỡng {limits['max_drawdown']:.2%} — về tiền mặt và chờ Owner")
        return out
    quarantined = market.get("quarantined")
    if quarantined is None:
        out["reasons"].append("không kiểm được sự kiện quyền bị cách ly — không ra quyết định mở vị thế")
        return out
    kept = []
    for t in targets:
        if t in quarantined:
            out["excluded"][t] = quarantined[t]
        else:
            kept.append(t)
    out["targets"] = kept
    for t, why in out["excluded"].items():
        out["reasons"].append(f"loại {t}: {why}")
    positions, price, adv = book.get("positions") or {}, market.get("price") or {}, market.get("adv_value") or {}
    per = nav / max(1, len(kept)) * BUY_BUDGET
    fails = []
    for t in kept:
        px = price.get(t)
        held = positions.get(t)
        if held:
            if px is None or not math.isfinite(float(px)) or px <= 0:
                fails.append(f"{t}: không có giá để định giá vị thế đang giữ")
                continue
            value = held * float(px)
        else:
            value = per
        w = value / nav
        if w > limits["max_weight"] + EPS:
            fails.append(f"{t}: tỷ trọng {w:.2%} > giới hạn {limits['max_weight']:.2%}")
        a = adv.get(t)
        if a is None or not math.isfinite(float(a)) or a <= 0:
            fails.append(f"{t}: thiếu giá trị giao dịch bình quân {int(limits['adv_sessions'])} phiên — không đo được thanh khoản")
            continue
        days = value / (limits["max_participation"] * float(a))
        if days > limits["max_exit_days"] + EPS:
            fails.append(f"{t}: cần {days:.1f} phiên để thoát vị thế > giới hạn {limits['max_exit_days']} phiên "
                         f"(tham gia {limits['max_participation']:.0%} giá trị giao dịch bình quân)")
    out["reasons"] += fails
    if not fails:
        out["verdict"] = "PASS"
    return out


def market_snapshot(as_of, tickers, limits, *, root, frozen, nav_now):
    """Đầu vào thị trường cho `check`, CHỈ ĐỌC từ kho giá, manifest bằng chứng và paper/nav.csv dưới `root`.

    - adv_value: bình quân giá × khối lượng GỐC (không điều chỉnh) của adv_sessions phiên gần nhất có dòng giá tới as_of;
    - quarantined: cửa sổ QĐ-3 quanh sự kiện cổ phiếu đang bị cách ly, tức chưa vào chuỗi verified-adjusted
      (engine.verified_adjust; gồm CACH_LY_* và sự kiện chưa tới hạn đã có trong bảng sự kiện tại as_of), đếm phiên theo
      session_axis với lịch HOSE data/trading_calendar.csv;
    - nav_history: cột nav của paper/nav.csv cộng NAV hiện tại.
    Lỗi đọc dữ liệu không ném ra ngoài: phần đó để trống, và `check` sẽ FAIL vì thiếu dữ liệu."""
    from . import adjust, data, verified_adjust as va

    root, t0 = pathlib.Path(root), pd.Timestamp(as_of)
    snap = {"frozen": bool(frozen), "adv_value": {}, "quarantined": None, "nav_history": [float(nav_now)], "errors": []}
    ok_limits = limits_problem(limits) is None
    try:
        s = data.load_store(root=root)
        s = s[s.date <= t0]
        raw = s.pivot(index="date", columns="ticker", values="close").sort_index()
        vol = s.pivot(index="date", columns="ticker", values="volume").sort_index()
        if ok_limits:
            n = int(limits["adv_sessions"])
            for t in tickers:
                if t in raw.columns:
                    v = (raw[t] * vol[t]).dropna().tail(n)
                    if len(v) == n:
                        snap["adv_value"][t] = float(v.mean())
            obs = s.pivot(index="date", columns="ticker", values="observed_at").sort_index()
            # Chỉ đưa sự kiện của mã có trong bảng giá: adjust.build_events ném lỗi với mã vắng mặt (chỉ mục rỗng).
            man, yh = adjust.load_manual(), adjust.load_yahoo()
            ev = adjust.build_events(raw, obs, man[man.ticker.isin(raw.columns)], yh[yh.ticker.isin(raw.columns)])
            docs = va.load_evidence(sorted((root / "data" / "evidence" / "corporate_actions").glob("EVIDENCE_MANIFEST*.json")))
            chk = va.verify_events(ev, raw, docs, evidence_root=root, as_of=t0)
            cal = load_calendar(root)
            q = chk[chk.type.isin(adjust.STOCK) & ~chk.in_verified_chain.astype(bool) & chk.ticker.isin(list(tickers))]
            items = []
            for r in q.itertuples(index=False):
                k = r.trade_date if pd.notna(r.trade_date) else r.ex_date
                if pd.notna(k):
                    items.append((r.ticker, k, f"sự kiện {r.type} ngày {pd.Timestamp(k).date()} bị cách ly ({r.verify_state})"))
            snap["quarantined"] = quarantine_window_hits(t0, session_axis(raw.index, cal), items,
                                                         int(limits["quarantine_sessions_before"]),
                                                         int(limits["quarantine_sessions_after"]), cal)
    except Exception as e:                  # noqa: BLE001 — thiếu kho hay manifest hỏng: để trống, check sẽ FAIL
        snap["errors"].append(f"{type(e).__name__}: {e}")
    try:
        p = root / "paper" / "nav.csv"
        if p.is_file():
            hist = pd.read_csv(p)["nav"].astype(float).tolist()
            snap["nav_history"] = [x for x in hist if np.isfinite(x)] + [float(nav_now)]
    except Exception as e:                  # noqa: BLE001 — nav.csv hỏng: không đo được sụt giảm, check sẽ FAIL
        snap["nav_history"] = None
        snap["errors"].append(f"nav.csv: {type(e).__name__}")
    return snap
