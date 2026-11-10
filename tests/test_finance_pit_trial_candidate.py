"""Synthetic-only PIT/prereg candidate checks; no live data or Owner approval."""
import copy
import pytest
from tools.research_integrity import (
    IntegrityError, validate_vintage, validate_trial_preregistration,
    validate_vintage_link,
)

H = "a" * 64
J = "b" * 64


def vintage():
    return {
        "source_id": "SYNTHETIC-OFFICIAL",
        "series_id": "SYNTHETIC-QUARTER",
        "entity_id": "SYNTHETIC-ENTITY",
        "revision_id": "REV-1",
        "unit": "VND",
        "raw_sha256": H,
        "dataset_vintage_sha256": J,
        "event_effective_at": "2026-09-30T00:00:00+07:00",
        "published_at": "2026-10-10T09:00:00+07:00",
        "market_available_at": "2026-10-10T09:02:00+07:00",
        "first_seen_at": "2026-10-10T09:04:00+07:00",
        "ingested_at": "2026-10-10T09:05:00+07:00",
        "quality": "VERIFIED_SOURCE",
        "license_status": "APPROVED_FOR_THIS_USE",
    }


def trial():
    return {
        "trial_id": "T-SYNTH-0001",
        "hypothesis": "Synthetic lagged factor precedes change in a mock target",
        "causal_mechanism": "Synthetic demand changes affect later mock revenue",
        "failure_mechanism": "Change is only correlated or data is late",
        "baseline_id": "NO_SIGNAL",
        "metric_id": "BRIER",
        "cost_model_id": "VND_COSTS_FROZEN",
        "split_plan_id": "PURGED_WALK_FORWARD",
        "holdout_policy_id": "SEALED_HOLDOUT",
        "experiment_family_id": "SYNTHETIC_TEST_FAMILY",
        "kill_criteria": "Fail predeclared holdout score",
        "dataset_vintage_sha256": J,
        "universe_snapshot_sha256": H,
        "spec_sha256": H,
        "registered_at": "2026-10-10T09:06:00+07:00",
        "status": "PREREGISTERED_RESEARCH_ONLY",
        "holdout_access": "DENIED_UNTIL_EVALUATION",
        "prior_trials_count": 0,
        "max_trials_in_family": 10,
        "family_alpha": 0.05,
    }


def test_valid_synthetic_vintage_and_prereg():
    assert validate_vintage(vintage(), "2026-10-10T10:00:00+07:00")["eligible"]
    assert validate_trial_preregistration(trial(), "2026-10-11T00:00:00+07:00")["remaining_family_slots"] == 9
    assert validate_vintage_link(trial(), vintage(), "2026-10-10T10:00:00+07:00")["eligible"]


def test_lookahead_vintage_detected():
    v = vintage()
    v["first_seen_at"] = "2026-10-11T09:04:00+07:00"
    v["ingested_at"] = "2026-10-11T09:05:00+07:00"
    with pytest.raises(IntegrityError, match="look-ahead"):
        validate_vintage(v, "2026-10-10T10:00:00+07:00")


def test_future_effective_event_permitted_when_announced():
    v = vintage()
    v["event_effective_at"] = "2026-12-01T00:00:00+07:00"
    assert validate_vintage(v, "2026-10-10T10:00:00+07:00")["eligible"]


def test_source_provenance_and_rights_fail_closed():
    for mutate in [
        lambda x: x.update(raw_sha256="unknown"),
        lambda x: x.update(license_status="UNKNOWN"),
        lambda x: x.update(quality="REVIEW_REQUIRED"),
    ]:
        v = vintage()
        mutate(v)
        with pytest.raises(IntegrityError):
            validate_vintage(v, "2026-10-10T10:00:00+07:00")


def test_prepublication_vintage_is_not_accepted():
    v = vintage()
    v["market_available_at"] = "2026-10-09T09:02:00+07:00"
    with pytest.raises(IntegrityError, match="chronology"):
        validate_vintage(v, "2026-10-10T10:00:00+07:00")


def test_unregistered_or_future_trial_rejected():
    t = trial()
    with pytest.raises(IntegrityError, match="not registered"):
        validate_trial_preregistration(t, "2026-10-10T09:00:00+07:00")
    t = trial()
    t["registered_at"] = "2026-10-11T00:00:00"
    with pytest.raises(IntegrityError, match="timezone"):
        validate_trial_preregistration(t, "2026-10-12T00:00:00+07:00")


def test_experiment_budget_and_alpha_fail_closed():
    t = trial()
    t["prior_trials_count"] = 10
    with pytest.raises(IntegrityError, match="budget"):
        validate_trial_preregistration(t, "2026-10-11T00:00:00+07:00")
    t = trial()
    t["family_alpha"] = 0.5
    with pytest.raises(IntegrityError, match="alpha"):
        validate_trial_preregistration(t, "2026-10-11T00:00:00+07:00")


def test_open_holdout_rejected():
    t = trial()
    t["holdout_access"] = "OPEN"
    with pytest.raises(IntegrityError, match="holdout"):
        validate_trial_preregistration(t, "2026-10-11T00:00:00+07:00")


def test_vintage_trial_digest_mismatch_rejected():
    t = trial()
    t["dataset_vintage_sha256"] = H
    with pytest.raises(IntegrityError, match="different dataset"):
        validate_vintage_link(t, vintage(), "2026-10-10T10:00:00+07:00")


def test_declared_prereg_not_auto_proven():
    t = trial()
    t["status"] = "PRODUCTION_READY"
    with pytest.raises(IntegrityError, match="not eligible"):
        validate_trial_preregistration(t, "2026-10-11T00:00:00+07:00")
