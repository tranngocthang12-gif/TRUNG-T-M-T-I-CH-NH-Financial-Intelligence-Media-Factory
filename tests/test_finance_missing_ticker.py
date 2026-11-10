"""Regression for missing price ticker and live-config event roots."""
import pathlib

import numpy as np
import pandas as pd

from engine import adjust


def test_event_for_unknown_price_ticker_does_not_compare_rangeindex_with_timestamp():
    index = pd.bdate_range("2024-01-01", periods=30)
    close = pd.DataFrame({"S00": [100.0] * 30}, index=index)
    observed = pd.DataFrame({"S00": index}, index=index)
    manual = pd.DataFrame([{
        "ticker": "TCB", "ex_date": pd.Timestamp("2024-01-10"),
        "type": "stock_split", "ratio": 2.0, "cash_per_share": np.nan,
        "source": "synthetic", "source_status": "TEST", "note": "",
    }])
    empty = pd.DataFrame(columns=manual.columns)
    got = adjust.build_events(close, observed, manual, empty)
    assert len(got) == 1
    assert got.iloc[0]["ticker"] == "TCB"
    assert got.iloc[0]["status"] == "KHONG_CO_MA"


def test_event_file_respects_runtime_root_after_configuration_reassignment(tmp_path, monkeypatch):
    csv = tmp_path / "synthetic_actions.csv"
    pd.DataFrame([{"ticker": "ABC", "ex_date": "2024-01-10",
                   "type": "stock_split", "ratio": 2.0}]).to_csv(csv, index=False)
    monkeypatch.setattr(adjust._runtime_config, "ROOT", pathlib.Path(tmp_path))
    got = adjust._read_events(csv.name)
    assert got.loc[0, "ticker"] == "ABC"
