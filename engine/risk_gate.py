"""Cổng rủi ro bằng mã cho sổ giấy (LỆNH R1, QĐ-5 của ADR-0016).

`check` là HÀM THUẦN: nhận danh mục mục tiêu, trạng thái sổ, thị trường và giới hạn; trả PASS hoặc FAIL kèm lý do. Không đọc,
không ghi tệp, không gọi mạng. FAIL thì sổ không mở vị thế mới. Năm điều kiện:
  1. tỷ trọng mỗi mã tại lúc quyết định (giá trị đang giữ, hoặc phần vốn sổ giấy sẽ cấp cho mã mới) ≤ max_weight × NAV;
  2. số phiên thoát vị thế = giá trị vị thế / (max_participation × giá trị giao dịch bình quân adv_sessions phiên)
     ≤ max_exit_days; thiếu giá trị giao dịch bình quân thì không đo được, nên FAIL;
  3. sụt giảm NAV từ đỉnh ≥ max_drawdown thì về tiền mặt và chờ Owner (mục tiêu rỗng); thiếu hay hỏng lịch sử NAV thì FAIL;
  4. cửa sổ loại mã theo QĐ-3 (ADR-0016): mã bị loại khỏi mục tiêu khi phiên quyết định t nằm trong
     [k − quarantine_sessions_before, k + quarantine_sessions_after] phiên, với k là phiên áp dụng của một sự kiện cổ phiếu
     đang bị cách ly (chưa vào chuỗi verified-adjusted của engine.verified_adjust); rồi mới xét 1 và 2;
  5. dữ liệu bị đóng băng thì không ra quyết định.
Giới hạn thiếu, còn chữ TODO hoặc không phải số hợp lệ thì FAIL. Giá trị mặc định ở config.yaml (paper.risk_limits) là tham số
thí nghiệm danh nghĩa, không phải khẩu vị rủi ro của Owner.

Điều kiện 3 còn chạy ở MỌI phiên định giá, không chỉ ở kỳ tái cơ cấu: engine.paper gọi `breach` sau khi định giá; chạm ngưỡng
thì sổ ghi khóa rủi ro bền vững (xem engine.paper). `check` chỉ chạy khi sổ ra quyết định.

`read_nav_history` (CHỈ ĐỌC paper/nav.csv) và `market_snapshot` (CHỈ ĐỌC kho giá, manifest bằng chứng, lịch phiên HOSE) dựng
đầu vào cho `check`.

Giới hạn về thời điểm dữ liệu (chưa phải PIT): `market_snapshot` lọc kho giá theo `date ≤ as_of`, KHÔNG lọc theo
`observed_at`; bảng sự kiện quyền đọc từ bộ nhớ đệm tại lúc chạy. Khi sổ chạy hằng ngày với as_of là phiên vừa đóng cửa, dữ
liệu này là dữ liệu có tại lúc ra quyết định. Chạy lại một phiên quá khứ thì không như vậy: kết quả của cổng khi chạy lại là
kiểm tra hồi cứu, KHÔNG phải bằng chứng PIT, và không được dùng làm bằng chứng cho FWD-001. FWD-001 cần cổng phiên bản dữ liệu
(vintage) riêng; việc đó ngoài phạm vi R1.
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


def session_axis(price_dates, calendar=None, until=None):
    """Trục phiên: các ngày của bảng giá, bỏ ngày mà lịch phiên HOSE (data/trading_calendar.csv) ghi is_session=0, khi lịch
    có và phủ ngày đó; thêm mọi ngày lịch ghi is_session=1 từ ngày đầu của bảng giá tới `until` (mặc định: ngày cuối của bảng
    giá) mà bảng giá không có dòng. Nhờ vậy phiên HOSE bị thiếu trong kho vẫn được đếm, và cửa sổ ADV không lùi qua nó.
    `calendar`: {ngày ISO: 0 hoặc 1} hoặc None."""
    days = pd.DatetimeIndex(sorted(set(pd.to_datetime(list(price_dates)))))
    if calendar and len(days):
        days = days[[calendar.get(d.date().isoformat(), 1) != 0 for d in days]]
        lo = pd.Timestamp(min(pd.to_datetime(list(price_dates))))
        hi = pd.Timestamp(until) if until is not None else pd.Timestamp(max(pd.to_datetime(list(price_dates))))
        extra = [pd.Timestamp(d) for d, x in calendar.items() if x == 1 and lo <= pd.Timestamp(d) <= hi]
        days = pd.DatetimeIndex(sorted(set(days) | set(extra)))
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


CALENDAR = ("data", "trading_calendar.csv")


def load_calendar(root):
    """{ngày ISO: is_session} từ data/trading_calendar.csv dưới root.

    KHÔNG có tệp thì trả None: đếm phiên theo ngày của bảng giá và thứ Hai–thứ Sáu (dự phòng được phép). Tệp CÓ mà hỏng thì
    ném ValueError, không dự phòng âm thầm: nơi gọi phải FAIL. Hỏng là: không đọc được; thiếu cột date hay is_session; rỗng;
    ngày không đúng dạng YYYY-MM-DD hay trùng; is_session khác 0 và 1; các ngày không liền nhau từ ngày đầu tới ngày cuối."""
    p = pathlib.Path(root).joinpath(*CALENDAR)
    if not p.exists():
        return None
    try:
        cal = pd.read_csv(p, dtype=str, keep_default_na=False)
    except Exception as e:                  # noqa: BLE001 — mọi lỗi đọc đều là lịch hỏng
        raise ValueError(f"lịch phiên HOSE {p.name} không đọc được ({type(e).__name__})") from e
    if not {"date", "is_session"} <= set(cal.columns) or not len(cal):
        raise ValueError(f"lịch phiên HOSE {p.name} thiếu cột date/is_session hoặc rỗng")
    days = pd.to_datetime(cal["date"], format="%Y-%m-%d", errors="coerce")
    if days.isna().any() or (days.dt.strftime("%Y-%m-%d") != cal["date"]).any():
        raise ValueError(f"lịch phiên HOSE {p.name} có ngày không đúng dạng YYYY-MM-DD")
    if days.duplicated().any():
        raise ValueError(f"lịch phiên HOSE {p.name} có ngày trùng")
    if not cal["is_session"].isin(["0", "1"]).all():
        raise ValueError(f"lịch phiên HOSE {p.name} có is_session khác 0 và 1")
    if len(days) != (days.max() - days.min()).days + 1:
        raise ValueError(f"lịch phiên HOSE {p.name} không liền ngày từ {days.min().date()} tới {days.max().date()}")
    return {d: int(x) for d, x in zip(cal["date"], cal["is_session"])}


def adv_values(raw, vol, axis, tickers, n):
    """→ ({mã: giá trị giao dịch bình quân}, {mã: lý do không đo được}) (hàm thuần).

    Cửa sổ là ĐÚNG n phiên cuối của trục phiên `axis` (đã cắt tới as_of). Mọi phiên trong cửa sổ phải có giá đóng cửa GỐC > 0
    và khối lượng ≥ 0, hữu hạn. Thiếu dù một phiên thì mã đó không có giá trị (check sẽ FAIL), không lùi cửa sổ để bù."""
    win = pd.DatetimeIndex(axis)[-n:] if n > 0 else pd.DatetimeIndex([])
    adv, why = {}, {}
    for t in tickers:
        if len(win) < n:
            why[t] = f"trục phiên chỉ có {len(win)} phiên, cần {n}"
            continue
        if t not in raw.columns or t not in vol.columns:
            why[t] = "không có trong kho giá"
            continue
        p = pd.to_numeric(raw[t].reindex(win), errors="coerce").astype(float).to_numpy()
        v = pd.to_numeric(vol[t].reindex(win), errors="coerce").astype(float).to_numpy()
        bad = ~(np.isfinite(p) & (p > 0) & np.isfinite(v) & (v >= 0))
        if bad.any():
            days = ", ".join(str(d.date()) for d in win[bad][:3])
            why[t] = f"thiếu giá hoặc khối lượng ở {int(bad.sum())}/{n} phiên của cửa sổ ({days})"
            continue
        adv[t] = float((p * v).mean())
    return adv, why


NAV_FILE = ("paper", "nav.csv")


def read_nav_history(root, as_of, nav_now, *, last_date, initial_cash, since=None, lower_bound=False):
    """→ (danh sách NAV để tính đỉnh, kết thúc bằng `nav_now`; hoặc None, lý do). CHỈ ĐỌC paper/nav.csv dưới `root`.

    - Chỉ dùng dòng có ngày TRƯỚC as_of (dòng của chính as_of là `nav_now`; dòng sau as_of bị bỏ khi chạy lại phiên cũ).
    - `last_date`: phiên gần nhất sổ đã xử lý TRƯỚC lần chạy này (state.json), hoặc None khi sổ chưa chạy phiên nào.
    - NAV khởi tạo hợp lệ: chưa có dòng nào trước as_of mà sổ cũng không ghi đã chạy phiên nào trước as_of. Khi đó lịch sử là
      [vốn ban đầu `initial_cash`, nav_now].
    - Mất lịch sử: sổ ghi đã chạy tới `last_date` < as_of mà không có nav.csv, hoặc nav.csv không có dòng của `last_date`.
      Hỏng: không đọc được, thiếu cột, ngày sai dạng, NAV không phải số dương hữu hạn. Cả hai trả None.
    - `since`: ngày Owner gỡ khóa rủi ro gần nhất (engine.paper); chỉ dùng dòng từ ngày đó, và không thêm vốn ban đầu.
    - `lower_bound=True` (chỉ để dò chạm ngưỡng): mất lịch sử thì vẫn trả các dòng hợp lệ còn lại (không thêm vốn ban đầu),
      kèm lý do mất. Các dòng còn lại là NAV thật của sổ, nên đỉnh thật không thấp hơn chúng và sụt giảm đo được là CẬN DƯỚI
      của sụt giảm thật: chạm ngưỡng trên đó là chạm thật. Không dùng cách này để cho PASS. Tệp hỏng vẫn trả None."""
    t0 = pd.Timestamp(as_of).normalize()
    last = pd.Timestamp(last_date) if last_date is not None else None
    if isinstance(initial_cash, bool) or not isinstance(initial_cash, (int, float)) or not math.isfinite(initial_cash) \
            or initial_cash <= 0:
        return None, f"vốn ban đầu paper.initial_cash không hợp lệ ({initial_cash!r})"
    p = pathlib.Path(root).joinpath(*NAV_FILE)
    lost = None
    if not p.exists():
        if last is not None and last < t0:
            lost = f"không có paper/nav.csv trong khi sổ đã chạy tới phiên {last.date()} — mất lịch sử NAV"
        dates, navs = pd.DatetimeIndex([]), np.array([], dtype=float)
    else:
        try:
            df = pd.read_csv(p, dtype={"date": str})
            dates = pd.DatetimeIndex(pd.to_datetime(df["date"], format="%Y-%m-%d"))
            navs = pd.to_numeric(df["nav"], errors="raise").astype(float).to_numpy()
        except Exception as e:              # noqa: BLE001 — mọi lỗi đọc đều là lịch sử hỏng
            return None, f"paper/nav.csv hỏng ({type(e).__name__}) — không đo được sụt giảm từ đỉnh"
        if last is not None and last < t0 and not (dates == last).any():
            lost = f"paper/nav.csv thiếu dòng của phiên đã xử lý gần nhất {last.date()} — mất lịch sử NAV"
    if lost and not lower_bound:
        return None, lost
    prior = dates < t0
    if since is not None:
        prior &= dates >= pd.Timestamp(since)
    vals = navs[np.asarray(prior)]
    if not (np.isfinite(vals) & (vals > 0)).all():
        return None, "paper/nav.csv có NAV không phải số dương hữu hạn — không đo được sụt giảm từ đỉnh"
    base = [float(initial_cash)] if since is None and not lost and not np.asarray(dates < t0).any() else []
    return base + [float(x) for x in vals] + [float(nav_now)], lost


def _drawdown(nav_history, nav):
    """Sụt giảm từ đỉnh (số trong [0, 1)) hoặc chuỗi lý do khi không đo được."""
    if nav_history is None:
        return "không đọc được lịch sử NAV — không đo được sụt giảm từ đỉnh"
    hist = []
    for x in list(nav_history) + [nav]:
        if isinstance(x, bool) or not isinstance(x, (int, float, np.floating)) or not math.isfinite(x) or x <= 0:
            return f"lịch sử NAV có giá trị không hợp lệ ({x!r}) — không đo được sụt giảm từ đỉnh"
        hist.append(float(x))
    return 1 - float(nav) / max(hist)


def breach(nav_history, nav, limits):
    """Lý do (chuỗi) khi sụt giảm NAV từ đỉnh ĐO ĐƯỢC và ≥ max_drawdown; ngoài ra None (hàm thuần).

    Không đo được (giới hạn hỏng, thiếu hay hỏng lịch sử NAV) thì trả None ở đây: `check` FAIL ở lần ra quyết định, sổ không mở
    vị thế mới."""
    if limits_problem(limits):
        return None
    dd = _drawdown(nav_history, nav)
    if isinstance(dd, str) or dd < limits["max_drawdown"] - EPS:
        return None
    return f"sụt giảm NAV từ đỉnh {dd:.2%} ≥ ngưỡng {limits['max_drawdown']:.2%}"


def check(targets, book, market, limits) -> dict:
    """→ {"verdict": "PASS"|"FAIL", "reasons": [...], "targets": [...], "excluded": {...}, "cash_wait_owner": bool}.

    targets: danh sách mã mục tiêu. book: {"nav": số, "positions": {mã: số cổ phiếu}}. market: {"price": {mã: giá},
    "adv_value": {mã: giá trị giao dịch bình quân}, "adv_problem": {mã: lý do}, "nav_history": [NAV theo thời gian, gồm NAV
    hiện tại], "nav_history_problem": lý do, "quarantined": {mã: lý do}, "frozen": bool, "errors": [...]}. Thiếu nav_history
    hay quarantined (None: không đọc/không kiểm được), hoặc lịch sử NAV có giá trị không hợp lệ, thì FAIL. `targets` trả về là
    mục tiêu sau khi loại mã bị cách ly; khi FAIL vì sụt giảm thì là danh sách rỗng."""
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
    dd = _drawdown(market.get("nav_history"), nav)
    if isinstance(dd, str):
        why = market.get("nav_history_problem")
        out["reasons"].append(dd + (f": {why}" if why else ""))
        return out
    if dd >= limits["max_drawdown"] - EPS:
        out.update(targets=[], cash_wait_owner=True)
        out["reasons"].append(f"sụt giảm NAV từ đỉnh {dd:.2%} ≥ ngưỡng {limits['max_drawdown']:.2%} — về tiền mặt và chờ Owner")
        return out
    quarantined = market.get("quarantined")
    if quarantined is None:
        errs = "; ".join(market.get("errors") or [])
        out["reasons"].append("không kiểm được sự kiện quyền bị cách ly — không ra quyết định mở vị thế"
                              + (f" ({errs})" if errs else ""))
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
    adv_why = market.get("adv_problem") or {}
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
            fails.append(f"{t}: thiếu giá trị giao dịch bình quân {int(limits['adv_sessions'])} phiên — không đo được thanh khoản"
                         + (f" ({adv_why[t]})" if adv_why.get(t) else ""))
            continue
        days = value / (limits["max_participation"] * float(a))
        if days > limits["max_exit_days"] + EPS:
            fails.append(f"{t}: cần {days:.1f} phiên để thoát vị thế > giới hạn {limits['max_exit_days']} phiên "
                         f"(tham gia {limits['max_participation']:.0%} giá trị giao dịch bình quân)")
    out["reasons"] += fails
    if not fails:
        out["verdict"] = "PASS"
    return out


def market_snapshot(as_of, tickers, limits, *, root, frozen, nav_history, nav_history_problem=None):
    """Đầu vào thị trường cho `check`, CHỈ ĐỌC từ kho giá, manifest bằng chứng và lịch phiên HOSE dưới `root`.

    - Trục phiên: session_axis(ngày của kho giá tới as_of, lịch HOSE, until=as_of). Lịch HOSE không có tệp thì đếm theo ngày
      của kho giá; tệp lịch có mà hỏng thì load_calendar ném lỗi, cả adv_value lẫn quarantined để trống, và `check` FAIL;
    - adv_value: bình quân giá × khối lượng GỐC (không điều chỉnh) của ĐÚNG adv_sessions phiên cuối của trục phiên (adv_values);
      phiên nào trong cửa sổ thiếu giá hay khối lượng thì mã đó không có giá trị, lý do ở adv_problem;
    - quarantined: cửa sổ QĐ-3 quanh sự kiện cổ phiếu đang bị cách ly, tức chưa vào chuỗi verified-adjusted
      (engine.verified_adjust; gồm CACH_LY_* và sự kiện chưa tới hạn đã có trong bảng sự kiện tại as_of), đếm phiên trên trục
      phiên;
    - nav_history: do nơi gọi đưa vào (read_nav_history), để cổng và khóa rủi ro mỗi phiên của engine.paper dùng CÙNG một lịch sử.
    Lỗi đọc dữ liệu không ném ra ngoài: phần đó để trống, lý do ở errors, và `check` sẽ FAIL vì thiếu dữ liệu.
    Kho giá lọc theo `date ≤ as_of`, không theo `observed_at` (xem giới hạn PIT ở đầu tệp)."""
    from . import adjust, data, verified_adjust as va

    root, t0 = pathlib.Path(root), pd.Timestamp(as_of)
    snap = {"frozen": bool(frozen), "adv_value": {}, "adv_problem": {}, "quarantined": None,
            "nav_history": None if nav_history is None else list(nav_history), "errors": []}
    if nav_history_problem:
        snap["nav_history_problem"] = nav_history_problem
    if limits_problem(limits) is not None:
        return snap
    try:
        cal = load_calendar(root)
        s = data.load_store(root=root)
        s = s[s.date <= t0]
        raw = s.pivot(index="date", columns="ticker", values="close").sort_index()
        vol = s.pivot(index="date", columns="ticker", values="volume").sort_index()
        axis = session_axis(raw.index, cal, until=t0)
        snap["adv_value"], snap["adv_problem"] = adv_values(raw, vol, axis, list(tickers), int(limits["adv_sessions"]))
        obs = s.pivot(index="date", columns="ticker", values="observed_at").sort_index()
        # Chỉ đưa sự kiện của mã có trong bảng giá: adjust.build_events ném lỗi với mã vắng mặt (chỉ mục rỗng).
        man, yh = adjust.load_manual(), adjust.load_yahoo()
        ev = adjust.build_events(raw, obs, man[man.ticker.isin(raw.columns)], yh[yh.ticker.isin(raw.columns)])
        docs = va.load_evidence(sorted((root / "data" / "evidence" / "corporate_actions").glob("EVIDENCE_MANIFEST*.json")))
        chk = va.verify_events(ev, raw, docs, evidence_root=root, as_of=t0)
        q = chk[chk.type.isin(adjust.STOCK) & ~chk.in_verified_chain.astype(bool) & chk.ticker.isin(list(tickers))]
        items = []
        for r in q.itertuples(index=False):
            k = r.trade_date if pd.notna(r.trade_date) else r.ex_date
            if pd.notna(k):
                items.append((r.ticker, k, f"sự kiện {r.type} ngày {pd.Timestamp(k).date()} bị cách ly ({r.verify_state})"))
        snap["quarantined"] = quarantine_window_hits(t0, axis, items, int(limits["quarantine_sessions_before"]),
                                                     int(limits["quarantine_sessions_after"]), cal)
    except Exception as e:                  # noqa: BLE001 — thiếu kho, lịch hỏng hay manifest hỏng: để trống, check sẽ FAIL
        snap["adv_value"], snap["quarantined"] = {}, None
        snap["errors"].append(f"{type(e).__name__}: {e}")
    return snap
