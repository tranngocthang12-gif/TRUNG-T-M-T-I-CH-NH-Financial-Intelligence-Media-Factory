"""Read-only investigation of TCB/VCB Yahoo/raw discontinuities.

Prints a JSON diagnostic for dates *in the stored raw data*, not an endorsement
of any exchange event. Never changes event status, source config, or raw files.

Usage: python tools/b1_price_evidence.py
"""
from __future__ import annotations

import json

import pandas as pd

from engine import data

CASES = {
    "TCB": {"raw_jump_date": "2024-06-11", "secondary_pdf_ex_date": "2024-06-20"},
    "VCB": {"raw_jump_date": "2025-03-03", "secondary_pdf_ex_date": "2025-03-12"},
}


def audit(store=None):
    if store is None:
        store = data.load_store()
    result = {"classification": "RAW_OBSERVATION_ONLY_NOT_HOSE_VERIFIED",
              "cases": {}, "missing_source_proof": True}
    for ticker, dates in CASES.items():
        frame = store.loc[store["ticker"] == ticker].copy().sort_values("date")
        frame["date"] = pd.to_datetime(frame["date"])
        frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
        event_rows = {}
        for label, day in dates.items():
            date = pd.Timestamp(day)
            prior = frame.loc[frame.date < date].tail(1)
            on_or_after = frame.loc[frame.date >= date].head(1)
            def simplify(q):
                if q.empty:
                    return None
                r = q.iloc[0]
                return {
                    "date": str(pd.Timestamp(r["date"]).date()),
                    "close": float(r["close"]) if pd.notna(r["close"]) else None,
                    "source": str(r.get("source", "")),
                    "observed_at": str(r.get("observed_at", "")),
                }
            before, after = simplify(prior), simplify(on_or_after)
            change = None
            if before and after and before["close"] and after["close"] is not None:
                change = round(after["close"] / before["close"] - 1, 7)
            event_rows[label] = {"requested_date": day, "last_before": before,
                                 "first_on_or_after": after, "raw_close_return": change}
        result["cases"][ticker] = event_rows
    return result


def main():
    print(json.dumps(audit(), ensure_ascii=False, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
