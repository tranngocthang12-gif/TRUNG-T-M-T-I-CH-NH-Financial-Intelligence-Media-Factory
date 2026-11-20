"""Đo lệch ngày quyền VCB, TCB, FPT. Chỉ đọc kho. Chỉ ghi file --out. Không gọi mạng.

Ngày chính thức lấy từ manifest đã ghim, không lấy từ báo chí.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pandas as pd

from engine import adjust
from engine.data import load_store

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "evidence" / "corporate_actions" / "EVIDENCE_MANIFEST.json"
AS_OF = "2026-11-16"
HORIZONS = (20, 60, 120, 252)
STOCK = ("stock_split", "stock_dividend")
NEAR_DAYS = 45


def _docs():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    docs = [d for d in manifest["source_documents"] if d.get("official_ex_date")]
    return sorted(docs, key=lambda d: (d["ticker"], d["official_ex_date"], d["source_id"]))


def _fmt(value, digits=6):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "không có"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def _sessions(store, ticker):
    frame = store.loc[store["ticker"] == ticker, ["date", "close"]].copy()
    frame["date"] = pd.to_datetime(frame["date"])
    frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
    frame = frame.dropna(subset=["close"]).sort_values("date").drop_duplicates("date")
    return frame.reset_index(drop=True)


def _anchor(dates, day):
    day = pd.Timestamp(day)
    i = int(dates.searchsorted(day, side="left"))
    if i < len(dates) and dates[i] == day:
        return i
    if i >= len(dates):
        return len(dates) - 1
    if i == 0:
        return 0
    before, after = dates[i - 1], dates[i]
    return i - 1 if (day - before) <= (after - day) else i


def _gap(dates, left, right):
    """Số phiên của mã từ ngày trái tới ngày phải: chỉ số phiên >= ngày phải trừ chỉ số phiên >= ngày trái."""
    if left is None or right is None or (isinstance(left, float) and pd.isna(left)):
        return None
    a = int(dates.searchsorted(pd.Timestamp(left), side="left"))
    b = int(dates.searchsorted(pd.Timestamp(right), side="left"))
    return b - a


def _measure_one(store, manual, yahoo, doc):
    ticker = doc["ticker"]
    official = pd.Timestamp(doc["official_ex_date"])
    sessions = _sessions(store, ticker)
    dates = pd.DatetimeIndex(sessions["date"])
    anchor = _anchor(dates, official)
    lo, hi = max(0, anchor - 15), min(len(sessions) - 1, anchor + 15)
    best = None
    for i in range(max(1, lo), hi + 1):
        prev, cur = float(sessions.at[i - 1, "close"]), float(sessions.at[i, "close"])
        if prev == 0:
            continue
        ret = cur / prev - 1
        if best is None or abs(ret) > abs(best["return"]):
            best = {"date": str(sessions.at[i, "date"].date()), "return": ret,
                    "close": cur, "previous_close": prev}
    manual_dates = []
    if len(manual):
        hit = manual[(manual["ticker"] == ticker) & (manual["type"].isin(STOCK))]
        manual_dates = [str(pd.Timestamp(d).date()) for d in hit["ex_date"]]
    yahoo_dates = []
    if len(yahoo):
        hit = yahoo[(yahoo["ticker"] == ticker) & (yahoo["type"].isin(STOCK))]
        near = hit[(pd.to_datetime(hit["ex_date"]) - official).abs() <= pd.Timedelta(days=NEAR_DAYS)]
        yahoo_dates = [str(pd.Timestamp(d).date()) for d in near["ex_date"]]
    jump = None if best is None else best["date"]
    start, end = sorted([pd.Timestamp(jump), official]) if jump else (official, official)
    window = sessions[(sessions["date"] >= start) & (sessions["date"] <= end)]
    non_integer = int((window["close"].map(lambda c: abs(float(c) - round(float(c))) > 1e-4)).sum())
    return {
        "ticker": ticker,
        "official_ex_date": str(official.date()),
        "official_record_date": doc.get("official_record_date"),
        "official_ratio": doc.get("official_ratio"),
        "official_ratio_text": doc.get("official_ratio_text"),
        "source_id": doc["source_id"],
        "jump_date": jump,
        "jump_return": None if best is None else best["return"],
        "manual_dates": manual_dates,
        "yahoo_dates": yahoo_dates,
        "gap_manual": [_gap(dates, official, d) for d in manual_dates],
        "gap_yahoo": [_gap(dates, official, d) for d in yahoo_dates],
        "gap_jump": _gap(dates, official, jump),
        "non_integer_rows": non_integer,
        "window_from": str(start.date()),
        "window_to": str(end.date()),
    }


def _with_official_dates(frame, docs):
    out = frame.copy()
    if out.empty:
        return out
    out["ex_date"] = pd.to_datetime(out["ex_date"])
    for doc in docs:
        official = pd.Timestamp(doc["official_ex_date"])
        mask = (out["ticker"] == doc["ticker"]) & (out["type"].isin(STOCK))
        mask &= (out["ex_date"] - official).abs() <= pd.Timedelta(days=NEAR_DAYS)
        out.loc[mask, "ex_date"] = official
    return out


def _series_at(close, ticker):
    if ticker not in close.columns:
        return None
    series = close[ticker].dropna()
    series = series[series.index <= pd.Timestamp(AS_OF)]
    return series


def _ret(series, n):
    if series is None or len(series) <= n:
        return None
    start, end = float(series.iloc[-1 - n]), float(series.iloc[-1])
    if start == 0:
        return None
    return end / start - 1


def _adjust_compare(store, docs):
    """Gọi engine.adjust trên bản sao trong bộ nhớ. Không ghi đĩa."""
    try:
        manual, yahoo = adjust.load_manual(), adjust.load_yahoo()
    except Exception as exc:  # hàm không gọi được
        return None, f"Không đọc được sự kiện để gọi adjust: {exc}"
    frame = store[store["date"] <= pd.Timestamp(AS_OF)].copy()
    raw = frame.pivot(index="date", columns="ticker", values="close").sort_index()
    obs = frame.pivot(index="date", columns="ticker", values="observed_at").sort_index()
    try:
        base_events = adjust.build_events(raw, obs, manual, yahoo)
        base_f, _ = adjust.factors(raw.index, raw.columns, base_events)
        off_events = adjust.build_events(raw, obs, _with_official_dates(manual, docs),
                                          _with_official_dates(yahoo, docs))
        off_f, _ = adjust.factors(raw.index, raw.columns, off_events)
    except Exception as exc:
        return None, f"engine.adjust không chạy độc lập được: {exc}"
    base_adj, off_adj = raw * base_f, raw * off_f
    rows = []
    for doc in docs:
        ticker = doc["ticker"]
        base_s, off_s = _series_at(base_adj, ticker), _series_at(off_adj, ticker)
        official = pd.Timestamp(doc["official_ex_date"])
        before = None
        if base_s is not None and len(base_s[base_s.index < official]):
            day = base_s[base_s.index < official].index[-1]
            before = {"date": str(day.date()),
                      "baseline": float(base_s.loc[day]),
                      "official_date": float(off_s.loc[day])}
        def statuses(events):
            hit = events[(events["ticker"] == ticker) & (events["type"].isin(STOCK))]
            near = hit[(pd.to_datetime(hit["ex_date"]) - official).abs() <= pd.Timedelta(days=NEAR_DAYS)]
            return [f"{pd.Timestamp(e.ex_date).date()} {e.source} {e.status}" for e in near.itertuples()]
        applied = base_events[(base_events["ticker"] == ticker)
                              & (base_events["status"] == "APPLIED")
                              & (base_events["type"].isin(STOCK))]
        pre_applied = None
        if len(applied) and base_s is not None and off_s is not None:
            trade = pd.to_datetime(applied["trade_date"]).min()
            earlier = base_s[base_s.index < trade]
            if len(earlier):
                day = earlier.index[-1]
                pre_applied = {"date": str(day.date()),
                               "baseline": float(base_s.loc[day]),
                               "official_date": float(off_s.loc[day])}
        price_base = None if base_s is None or base_s.empty else float(base_s.iloc[-1])
        price_off = None if off_s is None or off_s.empty else float(off_s.iloc[-1])
        rows.append({
            "ticker": ticker,
            "as_of": AS_OF,
            "price_baseline": price_base,
            "price_official_ex_date": price_off,
            "price_diff": None if price_base is None or price_off is None else price_off - price_base,
            "returns": {str(n): {"baseline": _ret(base_s, n), "official_ex_date": _ret(off_s, n),
                                 "diff": None if _ret(base_s, n) is None or _ret(off_s, n) is None
                                 else _ret(off_s, n) - _ret(base_s, n)}
                        for n in HORIZONS},
            "price_before_official_ex_date": before,
            "price_before_applied_trade_date": pre_applied,
            "status_baseline": statuses(base_events),
            "status_official_ex_date": statuses(off_events),
        })
    return rows, None


def build_report(store=None):
    docs = _docs()
    if store is None:
        store = load_store()
    store = store.copy()
    store["date"] = pd.to_datetime(store["date"])
    manual, yahoo = adjust.load_manual(), adjust.load_yahoo()
    measured = [_measure_one(store, manual, yahoo, doc) for doc in docs]
    compared, adjust_error = _adjust_compare(store, docs)
    by_ticker = {row["ticker"]: row for row in (compared or [])}
    lines = ["# Bằng chứng sự kiện quyền VCB, TCB, FPT — 19/11/2026", "",
             "Chỉ số liệu đọc từ bản gốc HOSE đã ghim sha256 và từ kho hiện có. Không lấy ngày hay tỷ lệ từ báo chí.",
             "Công cụ không sửa kho và không sửa mã điều chỉnh.", ""]
    lines += ["## (a) Bản gốc đã ghim", ""]
    lines += ["Ngày ký in trên văn bản không phải ngày HOSE công bố. Loại sự kiện theo văn bản tách khỏi loại kỹ thuật "
              "của engine; ánh xạ chưa chứng minh ghi CHUA_XAC_MINH và không đưa vào `event_type` (trường cổng "
              "verified-adjusted đọc).", ""]
    for doc in docs:
        published = (f"ngày công bố {doc['published_at']}" if doc.get("published_at")
                     else f"ngày công bố CHƯA XÁC MINH ({doc.get('published_at_note', '')})")
        lines.append(
            f"- {doc['ticker']} ({doc['source_id']}): ngày ký {doc.get('signed_date')}; {published}; "
            f"ngày giao dịch không hưởng quyền {doc['official_ex_date']}; "
            f"ngày đăng ký cuối cùng {doc.get('official_record_date')}; tỷ lệ in trên văn bản "
            f"{doc.get('official_ratio_text')} (hệ số (cổ cũ + cổ mới) / cổ cũ = {doc.get('official_ratio')}); "
            f"loại theo văn bản {doc.get('source_event_class')} («{doc.get('source_event_text')}»); "
            f"ánh xạ kỹ thuật {doc.get('technical_event_type')} ({doc.get('technical_mapping_status')}): "
            f"{doc.get('technical_mapping_note')} {doc.get('note', '')}"
        )
    lines += ["", "## (b) Đo trên kho", "",
              "Bước nhảy là lợi suất đóng cửa lớn nhất trong ±15 phiên của chính mã quanh ngày không hưởng quyền chính thức. "
              "Số phiên lệch là số phiên của mã đó tính từ ngày chính thức tới ngày kia (dương nếu ngày kia muộn hơn).", ""]
    for row in measured:
        lines.append(
            f"- {row['ticker']}: bước nhảy lớn nhất {row['jump_date']} ({_fmt(row['jump_return'])}). "
            f"Ngày trong corporate_actions.csv: {', '.join(row['manual_dates']) or 'không có'}; "
            f"lệch phiên {row['gap_manual'] or 'không có'}. "
            f"Ngày stock trong yahoo_actions.csv cách ngày chính thức không quá {NEAR_DAYS} ngày: "
            f"{', '.join(row['yahoo_dates']) or 'không có'}; lệch phiên {row['gap_yahoo'] or 'không có'}. "
            f"Lệch phiên giữa ngày chính thức và ngày bước nhảy: {row['gap_jump']}. "
            f"Số dòng giá đóng cửa không nguyên từ {row['window_from']} tới {row['window_to']}: {row['non_integer_rows']}."
        )
    lines += ["", "## (c) Điều chỉnh trong bộ nhớ", ""]
    if adjust_error:
        lines.append(f"Dừng ở mục (b). {adjust_error}")
    else:
        lines.append(
            "Gọi `engine.adjust.build_events` và `engine.adjust.factors` trên bản sao trong bộ nhớ, "
            f"cắt tới {AS_OF}. Cách thứ hai chỉ đổi `ex_date` của dòng cổ phiếu cùng mã nằm trong "
            f"{NEAR_DAYS} ngày quanh ngày chính thức. Không đổi tỷ lệ, không đổi nguồn, không ghi đĩa."
        )
        lines.append("")
        for row in compared:
            bits = [f"giá điều chỉnh tại {AS_OF}: cách hiện có {_fmt(row['price_baseline'])}, "
                    f"ngày chính thức {_fmt(row['price_official_ex_date'])}, chênh {_fmt(row['price_diff'])}"]
            for n in HORIZONS:
                item = row["returns"][str(n)]
                bits.append(f"lợi suất {n} phiên: chênh {_fmt(item['diff'])}")
            before = row["price_before_official_ex_date"]
            if before:
                bits.append(
                    f"giá điều chỉnh phiên {before['date']} (liền trước ngày chính thức): "
                    f"cách hiện có {_fmt(before['baseline'])}, ngày chính thức {_fmt(before['official_date'])}, "
                    f"chênh {_fmt(before['official_date'] - before['baseline'])}"
                )
            earlier = row.get("price_before_applied_trade_date")
            if earlier:
                bits.append(
                    f"giá điều chỉnh phiên {earlier['date']} (liền trước ngày đang áp hệ số): "
                    f"cách hiện có {_fmt(earlier['baseline'])}, ngày chính thức {_fmt(earlier['official_date'])}, "
                    f"chênh {_fmt(earlier['official_date'] - earlier['baseline'])}"
                )
            bits.append("trạng thái cách hiện có: " + ("; ".join(row["status_baseline"]) or "không có"))
            bits.append("trạng thái khi đưa ngày chính thức: " + ("; ".join(row["status_official_ex_date"]) or "không có"))
            lines.append(f"- {row['ticker']}: " + ". ".join(bits) + ".")
    lines += ["", "## (d) Kết luận", ""]
    for row in measured:
        comp = by_ticker.get(row["ticker"])
        price_note = "không đo được" if comp is None else (
            f"tại {AS_OF} giá điều chỉnh chênh {_fmt(comp['price_diff'])}; "
            + ", ".join(f"{n} phiên chênh {_fmt(comp['returns'][str(n)]['diff'])}" for n in HORIZONS)
            + ". Trạng thái cách hiện có: " + ("; ".join(comp["status_baseline"]) or "không có")
            + ". Trạng thái khi đưa ngày chính thức: " + ("; ".join(comp["status_official_ex_date"]) or "không có")
        )
        earlier = None if comp is None else comp.get("price_before_applied_trade_date")
        if earlier:
            price_note += (
                f". Phiên {earlier['date']} liền trước ngày đang áp hệ số: giá điều chỉnh chênh "
                f"{_fmt(earlier['official_date'] - earlier['baseline'])}"
            )
        lines.append(
            f"- {row['ticker']}: ngày chính thức {row['official_ex_date']} "
            f"(đăng ký cuối cùng {row['official_record_date']}, tỷ lệ {row['official_ratio_text']}). "
            f"Ngày đang ghi trong corporate_actions.csv: {', '.join(row['manual_dates']) or 'không có'}. "
            f"Ngày stock gần đó trong yahoo_actions.csv: {', '.join(row['yahoo_dates']) or 'không có'}. "
            f"Bước nhảy trong kho: {row['jump_date']}. {price_note}."
        )
    lines += ["",
              "Đề xuất sửa ngày trong dữ liệu hoặc sửa mã điều chỉnh chỉ là đề xuất. "
              "Cần Owner theo ADR-0009 điều 7 và một PR riêng. Không đề xuất nâng trạng thái lên DA_KIEM_CHUNG.",
              ""]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    text = build_report()
    path = pathlib.Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
