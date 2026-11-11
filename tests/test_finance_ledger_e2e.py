"""Offline synthetic regression: Issue ingest -> normalized Ledger -> resolver -> scorecard."""
import json
from datetime import datetime, timezone

import pandas as pd
import pytest
from engine import ledger
from engine.forecast_bridge import normalize_prediction, prepare_predictions
from tools import ledger_intake
from tools.laws_checks import check_ledger_chain, line_hash

CREATED = "2026-11-11T01:00:00Z"
UPDATED = "2026-11-11T01:00:02Z"
NOW = datetime(2026, 11, 11, 3, 0, tzinfo=timezone.utc)


def form(**changes):
    values = {
        "seat": "A",
        "question": "Will the synthetic FPT return exceed its synthetic peers?",
        "resolution_source": "SYNTHETIC_TEST_DATA_NOT_REAL_PRICES",
        "resolution_rule": "excess_return_positive",
        "ticker": "FPT",
        "horizon": "5",
        "resolve_at": "2026-11-22",
        "p": "0.6",
        "base_rate": "0.5",
        "invalidation_conditions": "Synthetic target does not outperform peers",
        "author_seat": "SYNTHETIC_TEST",
        "model_cutoff": "2026-01",
    }
    values.update(changes)
    return "\n".join("### " + key + "\n\n" + str(value) + "\n" for key, value in values.items())


def issue_row(**kwargs):
    raw = ledger_intake.parse_issue_form(form(**kwargs))
    assert raw["horizon"] == 5
    return {
        "issue_number": 101,
        "issue_created_at": CREATED,
        "issue_updated_at": UPDATED,
        "ingest_action": "opened",
        "registered_at": "2026-11-11T03:00:00Z",
        "raw_payload_sha256": "a" * 64,
        "benchmark_universe": ["FPT", "VNM"],
        **raw,
    }


def test_adapts_issue_without_mutating_hash_source():
    raw = issue_row()
    before = json.dumps(raw, sort_keys=True)
    view, blocked = normalize_prediction(raw)
    assert blocked is None and view["id"] == "I-101"
    assert view["probability"] == 0.6
    assert len(view["pair_key"]) == 64
    assert view["created_at"] == "2026-11-11"
    assert before == json.dumps(raw, sort_keys=True)


def test_legacy_is_preserved():
    row = {"id": "P-example", "created_at": "2026-11-11",
           "procedure": "news@v1", "probability": 0.6, "base_rate": 0.5,
           "resolution_rule": {"type": "excess_return_positive", "ticker": "FPT", "horizon": 5}}
    normalized, reason = normalize_prediction(row)
    assert normalized is row and reason is None


def test_late_edits_late_labels_and_untrusted_rules_blocked():
    raw = issue_row()
    raw["issue_updated_at"] = "2026-11-12T00:00:00Z"
    assert normalize_prediction(raw)[1] == "ISSUE_CHANGED_AFTER_OPEN"
    raw = issue_row()
    raw["ingest_action"] = "labeled"
    assert normalize_prediction(raw)[1] == "UNATTESTED_ISSUE_OPEN_EVENT"
    raw = issue_row(resolution_rule="numeric_range")
    assert normalize_prediction(raw)[1] == "SOURCE_RESOLVER_NOT_IMPLEMENTED"


def test_duplicate_and_bad_rows_are_counted():
    row = issue_row()
    accepted, blocked = prepare_predictions([row, dict(row), {"bad": True}])
    assert len(accepted) == 1
    assert blocked == {"DUPLICATE_FORECAST_ID": 1, "INVALID_LEGACY_ROW": 1}


def test_markdown_header_spoofing_fails():
    with pytest.raises(ValueError, match="duplicate"):
        ledger_intake.parse_issue_form(form() + "\n### p\n\n0.99\n")


def test_full_synthetic_ledger_resolution_and_brier(tmp_path, monkeypatch):
    monkeypatch.setattr(ledger, "ROOT", tmp_path)
    def local_path(rel):
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        return p
    monkeypatch.setattr(ledger, "path", local_path)
    monkeypatch.setattr(ledger, "save_json",
                        lambda rel, obj: local_path(rel).write_text(json.dumps(obj)))
    raw = issue_row()
    raw["prev_hash"] = "GENESIS"
    raw["hash"] = line_hash(raw)
    local_path("ledger/predictions.jsonl").write_text(json.dumps(raw) + "\n")
    assert check_ledger_chain(tmp_path) == []

    idx = pd.bdate_range("2026-11-12", periods=10)
    close = pd.DataFrame({"FPT": [100, 101, 102, 103, 104, 107, 108, 109, 110, 111],
                          "VNM": [100] * 10}, index=idx)

    assert ledger.resolve(close, "2026-11-19") == []  # declared due date pending
    assert ledger.scorecard("2026-11-19")["resolved"] == 0

    bad = pd.DataFrame(False, index=idx, columns=close.columns)
    bad.loc[idx[2], "FPT"] = True
    flagged = ledger.resolve(close, "2026-11-23", bad)
    assert len(flagged) == 1 and flagged[0]["outcome"] is None
    assert ledger.scorecard("2026-11-23")["void_data_error"] == 1

    # Independent pristine fixture: do not overwrite a settled VOID in production.
    (tmp_path / "ledger/resolutions.jsonl").unlink()
    passed = ledger.resolve(close, "2026-11-23", pd.DataFrame(False, index=idx, columns=close.columns))
    assert len(passed) == 1 and passed[0]["prediction_id"] == "I-101"
    assert passed[0]["outcome"] == 1
    assert ledger.resolve(close, "2026-11-23") == []
    sc = ledger.scorecard("2026-11-23")
    assert sc["total_predictions"] == sc["eligible_predictions"] == sc["resolved"] == 1
    assert sc["procedures"]["issue_A"]["brier"] == pytest.approx(0.16)
    assert sc["procedures"]["issue_A"]["verdict"] == "CHƯA ĐỦ MẪU"


def test_actual_intake_main_writes_single_hashed_issue(tmp_path, monkeypatch):
    from datetime import timedelta
    from tools import laws_checks
    now = datetime.now(timezone.utc)
    opened = (now - timedelta(seconds=3)).isoformat().replace("+00:00", "Z")
    due = (now + timedelta(days=45)).date().isoformat()
    target = tmp_path / "ledger" / "predictions.jsonl"
    monkeypatch.setattr(ledger_intake, "LEDGER", target)
    monkeypatch.setenv("ISSUE_NUMBER", "700")
    monkeypatch.setenv("ISSUE_CREATED_AT", opened)
    monkeypatch.setenv("ISSUE_UPDATED_AT", opened)
    monkeypatch.setenv("ISSUE_ACTION", "opened")
    monkeypatch.setenv("ISSUE_BODY", form(resolve_at=due))
    assert ledger_intake.main() == 0
    assert laws_checks.check_ledger_chain(tmp_path) == []
    stored = json.loads(target.read_text().splitlines()[0])
    assert normalize_prediction(stored)[1] is None
    from engine.config import CFG
    assert stored["benchmark_universe"] == CFG["universe"]
    assert ledger_intake.main() == 3
    assert len(target.read_text().splitlines()) == 1
    monkeypatch.setenv("ISSUE_ACTION", "labeled")
    assert ledger_intake.main() == 2
    assert len(target.read_text().splitlines()) == 1


def test_legacy_engine_and_issue_share_one_hash_chain(tmp_path, monkeypatch):
    monkeypatch.setattr(ledger, "ROOT", tmp_path)
    def local_path(rel):
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        return p
    monkeypatch.setattr(ledger, "path", local_path)
    old = {
        "id": "P-old", "created_at": "2026-11-11",
        "procedure": "news@v1", "probability": 0.5, "base_rate": 0.5,
        "resolution_rule": {"type": "excess_return_positive", "ticker": "FPT", "horizon": 5},
    }
    ledger._append_predictions([old])
    rows = ledger._load(ledger.PRED)
    assert len(rows) == 1
    candidate = issue_row()
    candidate["prev_hash"] = rows[-1]["hash"]
    candidate["hash"] = line_hash(candidate)
    ledger._append(ledger.PRED, [candidate])
    assert check_ledger_chain(tmp_path) == []
    normalized, reasons = prepare_predictions(ledger._load(ledger.PRED))
    assert reasons == {} and len(normalized) == 2
    with pytest.raises(ValueError, match="integrity failure"):
        rows = ledger._load(ledger.PRED)
        rows[0]["probability"] = 0.95
        local_path(ledger.PRED).write_text("\n".join(json.dumps(x) for x in rows) + "\n")
        ledger._append_predictions([old])

def test_delayed_issue_registration_cannot_backdate_price_entry():
    raw = issue_row()
    raw["registered_at"] = "2026-11-16T04:00:00Z"
    raw["resolve_at"] = "2026-11-25"
    view, blocked = normalize_prediction(raw)
    assert blocked is None
    assert view["created_at"] == "2026-11-16"
    assert view["original_issue_created_at"].startswith("2026-11-11")
    other = dict(raw)
    other["question"] = "Different prospectively fixed question"
    other_view, other_blocked = normalize_prediction(other)
    assert other_blocked is None
    assert view["pair_key"] != other_view["pair_key"]


@pytest.mark.parametrize("case", ["clean", "dirty_entry", "dirty_peers", "nan_peers", "missing_peer", "missing_mask", "both_drop_peer", "extra_price_peer", "extra_quality_peer", "invalid_snapshot", "missing_snapshot"])
def test_g001_no_shrinking_benchmark(tmp_path, monkeypatch, case):
    monkeypatch.setattr(ledger, "ROOT", tmp_path)
    monkeypatch.setattr(ledger, "path", lambda rel: tmp_path / rel)
    monkeypatch.setattr(ledger, "save_json", lambda rel, obj: (tmp_path / "scorecard.json").write_text(json.dumps(obj)))
    (tmp_path / "ledger").mkdir()
    raw = issue_row(resolve_at="2026-11-19")
    raw["benchmark_universe"] = ["FPT", "VNM", "HPG"]
    if case == "invalid_snapshot": raw["benchmark_universe"] = ["FPT", "FPT", "HPG"]
    if case == "missing_snapshot": raw.pop("benchmark_universe")
    (tmp_path / "ledger/predictions.jsonl").write_text(json.dumps(raw) + "\n")
    days = pd.bdate_range("2026-11-12", periods=6)
    close = pd.DataFrame({"FPT": [100]*5+[101], "VNM": [100]*5+[110], "HPG": [100]*5+[80]}, index=days)
    bad = pd.DataFrame(False, index=days, columns=close.columns)
    if case == "dirty_entry": bad.loc[days[0], "HPG"] = True
    if case == "dirty_peers": bad.loc[days[0], ["VNM", "HPG"]] = True
    if case == "nan_peers": close.loc[days[-1], ["VNM", "HPG"]] = float("nan")
    if case == "missing_peer": close = close.drop(columns="HPG")
    if case == "missing_mask": bad = bad.drop(columns="HPG")
    if case == "both_drop_peer":
        close = close.drop(columns="HPG")
        bad = bad.drop(columns="HPG")
    if case == "extra_price_peer": close["ACB"] = [100] * len(days)
    if case == "extra_quality_peer": bad["ACB"] = False
    out = ledger.resolve(close, "2026-11-19", bad)
    assert len(out) == 1
    if case == "clean":
        assert out[0]["excess_return"] == pytest.approx(0.04)
        assert out[0]["outcome"] == 1
    else:
        assert out[0]["excess_return"] is None and out[0]["outcome"] is None
        assert out[0]["void"]
    score = ledger.scorecard("2026-11-19")
    assert score["resolved"] == (1 if case == "clean" else 0)
    assert score["void_data_error"] == (0 if case == "clean" else 1)

def test_g001_old_prediction_without_frozen_basket_is_void(tmp_path, monkeypatch):
    """No retroactive invention of the universe for historical legacy rows."""
    monkeypatch.setattr(ledger, "ROOT", tmp_path)
    monkeypatch.setattr(ledger, "path", lambda rel: tmp_path / rel)
    monkeypatch.setattr(ledger, "save_json", lambda rel, obj: (tmp_path / "scorecard.json").write_text(json.dumps(obj)))
    (tmp_path / "ledger").mkdir()
    row = {"id": "P-legacy-unfrozen", "created_at": "2026-11-11",
           "procedure": "legacy", "probability": 0.6, "base_rate": 0.5,
           "resolution_rule": {"type": "excess_return_positive", "ticker": "FPT", "horizon": 5}}
    (tmp_path / "ledger/predictions.jsonl").write_text(json.dumps(row) + "\n")
    days = pd.bdate_range("2026-11-12", periods=6)
    close = pd.DataFrame({"FPT": [100]*5+[101], "VNM": [100]*5+[110]}, index=days)
    out = ledger.resolve(close, "2026-11-19")
    assert len(out) == 1 and out[0]["outcome"] is None and out[0]["void"]
    assert ledger.scorecard("2026-11-19")["resolved"] == 0

def test_f02_record_freezes_runtime_universe_and_rejects_mismatch(tmp_path, monkeypatch):
    """The basket used for audit, record and resolve is a single receipt."""
    monkeypatch.setattr(ledger, "ROOT", tmp_path)
    def local_path(rel):
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        return p
    monkeypatch.setattr(ledger, "path", local_path)
    idx = pd.bdate_range("2026-01-01", periods=62)
    prices = pd.DataFrame({"S01": [100.0] * 62, "S02": [101.0] * 62}, index=idx)
    p = {"procedure": "test", "ticker": "S01", "horizon": 5,
         "probability": 0.6, "claim": "synthetic forecast",
         "evidence_refs": ["E-01"]}
    accepted, rejected = ledger.record([p], "2026-01-15",
                                       list(prices.columns), {"E-01"}, prices)
    assert len(accepted) == 1 and rejected == []
    assert accepted[0]["benchmark_universe"] == ["S01", "S02"]
    assert check_ledger_chain(tmp_path) == []
    mismatched = ledger.record([p], "2026-01-15",
                               ["S01", "S02", "S03"], {"E-01"}, prices)
    assert mismatched[0] == [] and mismatched[1][0]["audit_errors"]
    assert len(ledger._load(ledger.PRED)) == 1


def test_f07_scorecard_dedupes_resolution_and_ignores_orphan(tmp_path, monkeypatch):
    monkeypatch.setattr(ledger, "ROOT", tmp_path)
    monkeypatch.setattr(ledger, "save_json",
                        lambda rel, obj: (tmp_path / "scorecard.json").write_text(json.dumps(obj)))
    (tmp_path / "ledger").mkdir()
    row = issue_row()
    (tmp_path / "ledger/predictions.jsonl").write_text(json.dumps(row) + "\n")
    one = {"prediction_id": "I-101", "outcome": 1}
    (tmp_path / "ledger/resolutions.jsonl").write_text("\n".join(map(json.dumps, [
        one, dict(one), {"prediction_id": "missing-id", "outcome": None}])) + "\n")
    sc = ledger.scorecard("2026-12-01")
    assert sc["resolved"] == 1
    assert sc["void_data_error"] == 0
    assert sc["duplicate_resolutions"] == 1
    assert sc["orphan_resolutions"] == 1
    assert sc["procedures"]["issue_A"]["n"] == 1


def test_f07_intake_rejects_corrupted_existing_chain(tmp_path, monkeypatch):
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    opened = (now - timedelta(seconds=3)).isoformat().replace("+00:00", "Z")
    due = (now + timedelta(days=45)).date().isoformat()
    target = tmp_path / "ledger" / "predictions.jsonl"
    target.parent.mkdir(parents=True)
    bad = {"issue_number": 600, "prev_hash": "GENESIS", "hash": "deadbeef"}
    target.write_text(json.dumps(bad) + "\n")
    before = target.read_bytes()
    monkeypatch.setattr(ledger_intake, "LEDGER", target)
    monkeypatch.setenv("ISSUE_NUMBER", "701")
    monkeypatch.setenv("ISSUE_CREATED_AT", opened)
    monkeypatch.setenv("ISSUE_UPDATED_AT", opened)
    monkeypatch.setenv("ISSUE_ACTION", "opened")
    monkeypatch.setenv("ISSUE_BODY", form(resolve_at=due))
    assert ledger_intake.main() == 2
    assert target.read_bytes() == before


def test_f1_missing_observation_reaches_ledger_without_forward_fill(tmp_path, monkeypatch):
    """Real load_market -> unfilled Ledger input: stale peer must VOID, never score."""
    from engine import data, adjust
    monkeypatch.setattr(ledger, "ROOT", tmp_path)
    monkeypatch.setattr(ledger, "path", lambda rel: tmp_path / rel)
    (tmp_path / "ledger").mkdir()
    dates = pd.bdate_range("2025-01-01", periods=290)
    # Both symbols qualify for load_market's >250 observed-session admission.
    rows = []
    for name in ("FPT", "VNM"):
        for k, day in enumerate(dates):
            if name == "VNM" and k == 286:
                continue  # One missing actual observation, inside the grading window.
            price = 101.0 if name == "FPT" and k == 289 else 100.0
            rows.append({"date": day, "ticker": name, "close": price,
                         "volume": 10000, "observed_at": day, "source": "synthetic"})
    store = pd.DataFrame(rows)
    monkeypatch.setattr(data, "load_store", lambda: store)
    empty_events = pd.DataFrame(columns=adjust.EV_COLS)
    monkeypatch.setattr(adjust, "load_manual", lambda: empty_events.copy())
    monkeypatch.setattr(adjust, "load_yahoo", lambda: empty_events.copy())
    mk = data.load_market(str(dates[-1].date()))
    assert pd.isna(mk["ledger_close"].at[dates[286], "VNM"])
    assert mk["close"].at[dates[286], "VNM"] == 100.0  # Feature ffill remains.
    assert not mk["bad"].at[dates[286], "VNM"]  # Reproduces the mask gap.
    prediction = {"id": "P-F1", "created_at": str(dates[283].date()),
                  "procedure": "synthetic", "probability": 0.6, "base_rate": 0.5,
                  "benchmark_universe": ["FPT", "VNM"],
                  "resolution_rule": {"type": "excess_return_positive",
                                      "ticker": "FPT", "horizon": 5}}
    (tmp_path / "ledger/predictions.jsonl").write_text(json.dumps(prediction) + "\n")
    # The known bad path would score 1 on the imputed feature data.
    # The product path MUST instead use the non-imputed adjusted close.
    outcome = ledger.resolve(mk["ledger_close"], str(dates[-1].date()), mk["bad"])
    assert len(outcome) == 1
    assert outcome[0]["outcome"] is None and outcome[0]["excess_return"] is None
    assert "void" in outcome[0]
