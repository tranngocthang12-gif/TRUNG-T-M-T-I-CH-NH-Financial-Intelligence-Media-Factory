"""Bounded, read-only PIT-vintage and trial-preregistration validation.

Not an attestor of external source identity or a replacement for owner acceptance.
Historical data available only by *later reconstruction* is not certified here.
"""
from __future__ import annotations

from datetime import datetime, timezone
from math import isfinite
import re

_SHA = re.compile(r"^[0-9a-f]{64}$")


class IntegrityError(ValueError):
    pass


def _timestamp(value):
    if not isinstance(value, str):
        raise IntegrityError("missing timestamp")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise IntegrityError("invalid timestamp") from exc
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise IntegrityError("timestamp has no timezone")
    return dt.astimezone(timezone.utc)


def _require_sha(obj, key):
    if not _SHA.fullmatch(str(obj.get(key, ""))):
        raise IntegrityError("invalid or missing " + key)


def validate_vintage(row: dict, decision_at: str) -> dict:
    """A value may enter live research only if its exact vintage was known in time."""
    if not isinstance(row, dict):
        raise IntegrityError("vintage is not an object")
    for key in ("source_id", "series_id", "entity_id", "revision_id", "unit"):
        if not isinstance(row.get(key), str) or not row[key].strip():
            raise IntegrityError("missing " + key)
    _require_sha(row, "raw_sha256")
    _require_sha(row, "dataset_vintage_sha256")
    event = _timestamp(row.get("event_effective_at"))
    published = _timestamp(row.get("published_at"))
    available = _timestamp(row.get("market_available_at"))
    first_seen = _timestamp(row.get("first_seen_at"))
    ingested = _timestamp(row.get("ingested_at"))
    decision = _timestamp(decision_at)
    if published > available or available > first_seen or first_seen > ingested:
        raise IntegrityError("source temporal chronology inconsistent")
    if available > decision or first_seen > decision or ingested > decision:
        raise IntegrityError("look-ahead: vintage unknown at decision time")
    if row.get("quality") not in ("VERIFIED_SOURCE", "REVIEW_REQUIRED"):
        raise IntegrityError("unknown quality")
    if row.get("quality") != "VERIFIED_SOURCE":
        raise IntegrityError("source requires review; cannot enter research")
    if row.get("license_status") != "APPROVED_FOR_THIS_USE":
        raise IntegrityError("unapproved source rights")
    # event_effective_at can be before OR after publication (e.g. advance policy notice).
    return {"eligible": True, "source_id": row["source_id"],
            "revision_id": row["revision_id"], "event_effective_at": event.isoformat()}


def validate_trial_preregistration(trial: dict, started_at: str) -> dict:
    """Validate declared prereg order; DOES NOT certify signer, source or hash custody."""
    if not isinstance(trial, dict):
        raise IntegrityError("trial is not an object")
    for key in ("trial_id", "hypothesis", "causal_mechanism", "failure_mechanism",
                "baseline_id", "metric_id", "cost_model_id", "split_plan_id",
                "holdout_policy_id", "experiment_family_id", "kill_criteria"):
        if not isinstance(trial.get(key), str) or not trial[key].strip():
            raise IntegrityError("missing " + key)
    for key in ("dataset_vintage_sha256", "universe_snapshot_sha256", "spec_sha256"):
        _require_sha(trial, key)
    registered = _timestamp(trial.get("registered_at"))
    started = _timestamp(started_at)
    if registered >= started:
        raise IntegrityError("trial not registered before start")
    if trial.get("status") != "PREREGISTERED_RESEARCH_ONLY":
        raise IntegrityError("trial is not eligible for research")
    if trial.get("holdout_access") != "DENIED_UNTIL_EVALUATION":
        raise IntegrityError("holdout unsealed")
    if trial.get("prior_trials_count") is None or type(trial["prior_trials_count"]) is not int or trial["prior_trials_count"] < 0:
        raise IntegrityError("missing cumulative prior trials")
    if trial.get("max_trials_in_family") is None or type(trial["max_trials_in_family"]) is not int or trial["max_trials_in_family"] < 1:
        raise IntegrityError("missing family test budget")
    if trial["prior_trials_count"] >= trial["max_trials_in_family"]:
        raise IntegrityError("preregistered trial budget exceeded")
    alpha = trial.get("family_alpha")
    if type(alpha) not in (float, int) or not isfinite(alpha) or not 0 < alpha <= 0.05:
        raise IntegrityError("invalid preregistered alpha")
    return {"eligible": True, "trial_id": trial["trial_id"],
            "prior_trials_count": trial["prior_trials_count"],
            "remaining_family_slots": trial["max_trials_in_family"] - trial["prior_trials_count"] - 1}


def validate_vintage_link(trial: dict, vintage: dict, decision_at: str) -> dict:
    validate_vintage(vintage, decision_at)
    if trial.get("dataset_vintage_sha256") != vintage.get("dataset_vintage_sha256"):
        raise IntegrityError("trial references a different dataset vintage")
    return {"eligible": True, "trial_id": trial.get("trial_id")}
