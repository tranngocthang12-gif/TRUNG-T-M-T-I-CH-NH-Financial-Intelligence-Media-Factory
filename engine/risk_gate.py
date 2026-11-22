"""Cổng rủi ro trước khi mua cho sổ giấy (LỆNH R1a, QĐ-5 của ADR-0016). Không giữ trạng thái.

`check` là HÀM THUẦN: nhận danh mục mục tiêu, trạng thái sổ, thị trường và giới hạn; trả PASS hoặc FAIL kèm lý do. Không đọc,
không ghi tệp, không gọi mạng. FAIL thì sổ không mở vị thế mới. Các điều kiện:
  1. tỷ trọng mỗi mã (giá trị đang giữ, hoặc phần vốn sổ giấy sẽ cấp cho mã mới) ≤ max_weight × NAV;
  2. số phiên thoát vị thế = giá trị vị thế / (max_participation × giá trị giao dịch bình quân adv_sessions phiên)
     ≤ max_exit_days; thiếu giá trị giao dịch bình quân thì không đo được, nên FAIL;
  3. cửa sổ loại mã theo QĐ-3 (ADR-0016): mã bị loại khỏi mục tiêu khi phiên t nằm trong
     [k − quarantine_sessions_before, k + quarantine_sessions_after] phiên, với k là phiên áp dụng của một sự kiện cổ phiếu
     đang bị cách ly (chưa vào chuỗi verified-adjusted của engine.verified_adjust); rồi mới xét 1 và 2. Không kiểm được thì
     FAIL;
  4. dữ liệu bị đóng băng thì không ra quyết định.
Giới hạn thiếu, còn chữ TODO hoặc không phải số hợp lệ thì FAIL. Giá trị mặc định ở config.yaml (paper.risk_limits) là tham số
thí nghiệm danh nghĩa, không phải khẩu vị rủi ro của Owner.

engine.paper gọi cổng ở hai thời điểm: lúc ra quyết định và lúc khớp lệnh mua đang chờ. Cổng không theo dõi giữa các lần chạy,
không ép bán hay giảm vị thế đang giữ.

Ngắt khi sụt giảm NAV (R1b; QĐ-5, QĐ-5a của ADR-0016; quyết định O-R của Owner, ngưỡng 15%) KHÔNG nằm trong `check` và không
thêm `max_drawdown` vào LIMIT_KEYS (R1a giữ nguyên). Mô-đun này chỉ cung cấp:
  - `drawdown_problem`: ngưỡng `paper.risk_limits.max_drawdown` dùng được hay không;
  - `drawdown_path`: HÀM THUẦN đo sụt giảm từng phiên, dùng chung cho sổ giấy chính (khóa) và sổ FWD ở F1b (chỉ ghi nhận);
  - `release_check`: điều kiện Owner gỡ khóa (giá trị `paper.risk_lock_release` và người gộp PR là chủ kho, qua API GitHub).
engine.paper giữ trạng thái đo, khóa và thanh lý.

`market_snapshot` (CHỈ ĐỌC kho giá, manifest bằng chứng, lịch phiên HOSE) dựng đầu vào thị trường cho `check`.

Giới hạn về thời điểm dữ liệu (chưa phải PIT): `market_snapshot` lọc kho giá theo `date ≤ as_of`, KHÔNG lọc theo
`observed_at`; bảng sự kiện quyền đọc từ bộ nhớ đệm tại lúc chạy. Khi sổ chạy với as_of là phiên vừa đóng cửa, dữ liệu này là
dữ liệu có tại lúc ra quyết định. Chạy lại một phiên quá khứ thì không như vậy: kết quả của cổng khi chạy lại là kiểm tra hồi
cứu, KHÔNG phải bằng chứng PIT, và không được dùng làm bằng chứng cho FWD-001.
"""
from __future__ import annotations

import json
import math
import os
import pathlib
import subprocess
import urllib.request

import numpy as np
import pandas as pd

LIMIT_KEYS = ("max_weight", "max_participation", "max_exit_days", "adv_sessions",
              "quarantine_sessions_before", "quarantine_sessions_after")
INT_KEYS = ("adv_sessions", "quarantine_sessions_before", "quarantine_sessions_after")
FRACTION_KEYS = ("max_weight", "max_participation")
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


def check(targets, book, market, limits) -> dict:
    """→ {"verdict": "PASS"|"FAIL", "reasons": [...], "targets": [...], "excluded": {...}}.

    targets: danh sách mã mục tiêu. book: {"nav": số, "positions": {mã: số cổ phiếu}}, với positions là các vị thế SẼ CÒN GIỮ
    sau bước đang xét (nơi gọi bỏ các mã sắp bán). market: {"price": {mã: giá}, "adv_value": {mã: giá trị giao dịch bình quân},
    "adv_problem": {mã: lý do}, "quarantined": {mã: lý do}, "frozen": bool, "errors": [...]}. quarantined là None (không kiểm
    được) thì FAIL. `targets` trả về là mục tiêu sau khi loại mã bị cách ly.

    Điều kiện 1 và 2 xét cả danh mục tồn dư: mọi vị thế trong book.positions không thuộc mục tiêu sau khi loại (ví dụ lệnh bán
    bị khóa sàn, hay mã đang giữ bị cách ly). Danh mục tồn dư vượt tỷ trọng hay khó thoát thì FAIL, không mua thêm mã nào."""
    out = {"verdict": "FAIL", "reasons": [], "targets": list(targets), "excluded": {}}
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
    residual = [t for t, sh in positions.items() if sh and t not in kept]      # danh mục tồn dư ngoài mục tiêu
    fails = []
    for t in kept + residual:
        name = t if t in kept else f"{t} (vị thế còn giữ ngoài mục tiêu)"
        px = price.get(t)
        held = positions.get(t)
        if held:
            if px is None or not math.isfinite(float(px)) or px <= 0:
                fails.append(f"{name}: không có giá để định giá vị thế đang giữ")
                continue
            value = held * float(px)
        else:
            value = per
        w = value / nav
        if w > limits["max_weight"] + EPS:
            fails.append(f"{name}: tỷ trọng {w:.2%} > giới hạn {limits['max_weight']:.2%}")
        a = adv.get(t)
        if a is None or not math.isfinite(float(a)) or a <= 0:
            fails.append(f"{name}: thiếu giá trị giao dịch bình quân {int(limits['adv_sessions'])} phiên — không đo được "
                         f"thanh khoản" + (f" ({adv_why[t]})" if adv_why.get(t) else ""))
            continue
        days = value / (limits["max_participation"] * float(a))
        if days > limits["max_exit_days"] + EPS:
            fails.append(f"{name}: cần {days:.1f} phiên để thoát vị thế > giới hạn {limits['max_exit_days']} phiên "
                         f"(tham gia {limits['max_participation']:.0%} giá trị giao dịch bình quân)")
    out["reasons"] += fails
    if not fails:
        out["verdict"] = "PASS"
    return out


def market_snapshot(as_of, tickers, limits, *, root, frozen):
    """Đầu vào thị trường cho `check`, CHỈ ĐỌC từ kho giá, manifest bằng chứng và lịch phiên HOSE dưới `root`.

    - Trục phiên: session_axis(ngày của kho giá tới as_of, lịch HOSE, until=as_of). Lịch HOSE không có tệp thì đếm theo ngày
      của kho giá; tệp lịch có mà hỏng thì load_calendar ném lỗi, cả adv_value lẫn quarantined để trống, và `check` FAIL;
    - adv_value: bình quân giá × khối lượng GỐC (không điều chỉnh) của ĐÚNG adv_sessions phiên cuối của trục phiên (adv_values);
      phiên nào trong cửa sổ thiếu giá hay khối lượng thì mã đó không có giá trị, lý do ở adv_problem;
    - quarantined: cửa sổ QĐ-3 quanh sự kiện cổ phiếu đang bị cách ly, tức chưa vào chuỗi verified-adjusted
      (engine.verified_adjust; gồm CACH_LY_* và sự kiện chưa tới hạn đã có trong bảng sự kiện tại as_of), đếm phiên trên trục
      phiên;
    Lỗi đọc dữ liệu không ném ra ngoài: phần đó để trống, lý do ở errors, và `check` sẽ FAIL vì thiếu dữ liệu.
    Kho giá lọc theo `date ≤ as_of`, không theo `observed_at` (xem giới hạn PIT ở đầu tệp)."""
    from . import adjust, data, verified_adjust as va

    root, t0 = pathlib.Path(root), pd.Timestamp(as_of)
    snap = {"frozen": bool(frozen), "adv_value": {}, "adv_problem": {}, "quarantined": None, "errors": []}
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


# ---------- R1b: ngắt khi sụt giảm NAV ----------

def drawdown_problem(limits):
    """Lý do ngưỡng `max_drawdown` không dùng được (thiếu, TODO, không phải số trong (0, 1)), hoặc None."""
    v = limits.get("max_drawdown") if isinstance(limits, dict) else None
    if isinstance(v, str) and "TODO" in v.upper():
        return "max_drawdown còn TODO"
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not 0 < v < 1:
        return f"max_drawdown thiếu hoặc không phải số trong (0, 1) ({v!r})"
    return None


def drawdown_path(navs, peak, threshold, peak_date=None):
    """Đo sụt giảm từng phiên (HÀM THUẦN). `navs`: [(phiên, NAV hoặc None)] theo thứ tự thời gian; `peak`: đỉnh hiện có;
    `threshold`: ngưỡng sụt giảm. Sụt giảm = 1 − NAV / đỉnh, đỉnh cập nhật khi NAV vượt đỉnh.

    Gặp phiên có NAV là None thì DỪNG ở phiên đó (`stopped_at`), không bỏ qua phiên đó để đo phiên sau.
    → {"rows": [{date, nav, peak, drawdown, verified}] của các phiên đã đo, "breach": dòng đầu tiên có sụt giảm ≥ ngưỡng hoặc
       None, "stopped_at": phiên không đo được hoặc None, "peak", "peak_date"}."""
    if not (isinstance(peak, (int, float)) and math.isfinite(peak) and peak > 0):
        raise ValueError(f"đỉnh NAV phải là số dương hữu hạn ({peak!r})")
    rows, first, stop = [], None, None
    for s, nav in navs:
        if nav is None:
            stop = s
            break
        if nav > peak:
            peak, peak_date = float(nav), s
        dd = 1.0 - float(nav) / peak
        row = {"date": s, "nav": float(nav), "peak": float(peak), "drawdown": dd, "verified": True}
        rows.append(row)
        if first is None and dd >= threshold - EPS:
            first = row
    return {"rows": rows, "breach": first, "stopped_at": stop, "peak": float(peak), "peak_date": peak_date}


def git_last_release_commit(root):
    """→ (sha, None) của commit mới nhất đổi dòng `risk_lock_release` trong config.yaml (`git log -1 -G risk_lock_release`),
    hoặc (None, lý do): kho nông (thiếu lịch sử), không có commit nào như vậy, git lỗi."""
    def git(*args):
        return subprocess.run(["git", *args], cwd=str(root), capture_output=True, text=True, timeout=30)
    r = git("rev-parse", "--is-shallow-repository")
    if r.returncode != 0:
        return None, "không đọc được lịch sử git"
    if r.stdout.strip() == "true":
        return None, "kho nông (shallow clone): thiếu lịch sử git để xác minh commit gỡ khóa"
    r = git("log", "-1", "-G", "risk_lock_release", "--format=%H", "--", "config.yaml")
    sha = r.stdout.strip()
    if r.returncode != 0 or not sha:
        return None, "không tìm thấy commit nào đổi dòng risk_lock_release trong config.yaml"
    return sha, None


def github_api(path):
    """GET https://api.github.com/repos/{GITHUB_REPOSITORY}/{path} với GITHUB_TOKEN. Lỗi thì ném ra (nơi gọi giữ khóa)."""
    repo, token = os.environ.get("GITHUB_REPOSITORY"), os.environ.get("GITHUB_TOKEN")
    if not repo or not token:
        raise RuntimeError("thiếu GITHUB_REPOSITORY hoặc GITHUB_TOKEN")
    req = urllib.request.Request(f"https://api.github.com/repos/{repo}/{path}",
                                 headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                                          "User-Agent": "ttc-engine"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def release_check(lock, release_value, *, root, git=None, api=None, owner=None):
    """Owner gỡ khóa sụt giảm được không → (True, căn cứ) hoặc (False, lý do); (False, None) khi chưa đặt giá trị gỡ.

    Đủ cả hai điều kiện mới gỡ:
      1. `paper.risk_lock_release` bằng đúng `risk_lock.since`;
      2. commit mới nhất đổi dòng `risk_lock_release` trong config.yaml thuộc một PR đã gộp vào `main`, và người gộp
         (`merged_by`) là chủ kho (`owner`, mặc định biến môi trường GITHUB_REPOSITORY_OWNER), xác minh qua API GitHub
         (`commits/{sha}/pulls` rồi `pulls/{số}`).
    `git(root)` → (sha, lý do) và `api(path)` → JSON được truyền vào để test; mặc định git_last_release_commit, github_api.
    Mọi lỗi (kho nông, không mạng, không token, API lỗi) đều là (False, lý do): giữ khóa."""
    if release_value is None:
        return False, None
    since = str(lock.get("since"))
    if str(release_value) != since:
        return False, f"paper.risk_lock_release = {release_value} khác risk_lock.since = {since}"
    owner = owner if owner is not None else os.environ.get("GITHUB_REPOSITORY_OWNER")
    if not owner:
        return False, "thiếu GITHUB_REPOSITORY_OWNER (chủ kho) để đối chiếu người gộp"
    git = git or git_last_release_commit
    api = api or github_api
    try:
        sha, why = git(root)
        if not sha:
            return False, why or "không xác định được commit gỡ khóa"
        pulls = api(f"commits/{sha}/pulls") or []
        merged = [p for p in pulls if p.get("merged_at") and (p.get("base") or {}).get("ref") == "main"]
        if not merged:
            return False, f"commit {sha[:7]} đổi risk_lock_release không thuộc PR nào đã gộp vào main"
        who = []
        for p in merged:
            pr = api(f"pulls/{p['number']}") or {}
            login = (pr.get("merged_by") or {}).get("login")
            if pr.get("merged") and pr.get("merged_at") and login == owner:
                return True, f"PR #{p['number']} gộp vào main bởi chủ kho {login}, commit {sha[:7]}"
            who.append(f"#{p['number']}: {login}")
        return False, f"người gộp không phải chủ kho {owner} ({', '.join(who)})"
    except Exception as e:                  # noqa: BLE001 — không xác minh được thì giữ khóa
        return False, f"không xác minh được qua API GitHub ({type(e).__name__}: {str(e)[:120]})"
