"""Read/write integration with the REAL Finance engine, using a strictly temporary raw store.

This is a synthetic, offline bridge test. It does not verify real TCB/VCB disclosures,
does not authenticate a broker, and does not activate a data source.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

from engine import adjust, config, data


def test_real_engine_raw_store_and_adjustment_are_isolated(tmp_path):
    idx = pd.bdate_range("2024-01-02", periods=285)
    ex = idx[263]
    original = []
    for d in idx:
        for ticker in ("TCB", "VCB"):
            price = 50.0 if ticker == "TCB" and d >= ex else (100.0 if ticker == "TCB" else 200.0)
            original.append({
                "date": d.strftime("%Y-%m-%d"), "ticker": ticker,
                "open": price, "high": price, "low": price, "close": price,
                "volume": 100000, "observed_at": d.strftime("%Y-%m-%dT16:00:00"),
                "source": "mock_ssi",
            })
    rows = pd.DataFrame(original, columns=data.COLS)
    corporate_path = tmp_path / config.CFG["corporate_actions"]["manual"]
    corporate_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([{
        "ticker": "TCB", "ex_date": str(ex.date()), "type": "stock_dividend",
        "ratio": 2.0, "cash_per_share": np.nan, "source": "synthetic_fixture",
        "source_status": "DA_KIEM_CHUNG", "note": "TEST-ONLY synthetic 2:1 split",
    }]).to_csv(corporate_path, index=False)
    yahoo_path = tmp_path / config.CFG["corporate_actions"]["yahoo_cache"]
    yahoo_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(columns=adjust.EV_COLS).to_csv(yahoo_path, index=False)
    assert data.save_store(rows, root=tmp_path) == len(rows)
    saved = sorted((tmp_path / config.CFG["data"]["store_dir"]).glob("*.csv"))
    assert saved
    before = {p.name: p.read_bytes() for p in saved}
    store = data.load_store(root=tmp_path)
    assert len(store) == len(rows)
    pd.testing.assert_frame_equal(
        store.sort_values(["date", "ticker"]).reset_index(drop=True)[data.COLS],
        store[data.COLS].sort_values(["date", "ticker"]).reset_index(drop=True),
    )
    with patch.object(config, "ROOT", tmp_path), patch.object(adjust, "ROOT", tmp_path):
        earlier = data.load_market(str(idx[255].date()))
        later = data.load_market(str(idx[-1].date()))
    assert "TCB" in earlier["raw_close"] and "VCB" in later["raw_close"]
    assert earlier["raw_close"].at[idx[0], "TCB"] == 100
    assert earlier["close"].at[idx[0], "TCB"] == 100
    assert later["raw_close"].at[idx[0], "TCB"] == 100
    assert later["close"].at[idx[0], "TCB"] == 50
    assert later["close"].at[idx[-1], "TCB"] == 50
    assert later["events"].loc[later["events"].ticker == "TCB", "status"].tolist() == ["APPLIED"]
    assert earlier["events"].loc[earlier["events"].ticker == "TCB", "status"].tolist() == ["CHUA_DEN_HAN"]
    assert all(p.read_bytes() == before[p.name] for p in saved)
    assert data.save_store(rows, root=tmp_path) == 0
    assert all(p.read_bytes() == before[p.name] for p in saved)
    assert not (tmp_path / config.CFG["data"]["store"]).exists()


def test_b1_source_is_not_enabled_in_live_config():
    assert config.CFG["data"]["sources"] == ["yahoo"]
    assert "ssi" not in config.CFG["data"]["sources"]
    assert "dnse" not in config.CFG["data"]["sources"]
