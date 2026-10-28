"""Read-only provenance inspection for prospective ML outcome evaluation.

This is an optional, domain-neutral contract for tasks where predictions really
precede outcome availability. Historical offline holdouts require a different
contract. Declared identities, timestamps and hashes are not external proofs.
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any, Mapping

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_HASH_FIELDS = (
    "frozen_evaluation_packet_sha256",
    "frozen_extraction_rule_sha256",
    "prediction_artifact_sha256",
    "raw_outcome_snapshot_sha256",
)
_TIME_FIELDS = (
    "evaluation_packet_frozen_at",
    "prediction_frozen_at",
    "outcome_first_available_at",
    "raw_outcome_captured_at",
    "blind_label_extracted_at",
)
_REQUIRED = frozenset(_HASH_FIELDS + _TIME_FIELDS + (
    "schema", "mode", "task_family", "dataset_version", "source_locator",
    "prediction_actor_id", "resolver_actor_id", "outcome_source_kind",
    "outcome_source_transform", "resolver_input_contract",
    "resolver_saw_prediction", "resolver_saw_model_trace",
    "resolver_saw_prior_resolution",
))


def _parse_utc(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None or dt.utcoffset() is None:
        return None
    return dt.astimezone(timezone.utc)


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def inspect_prospective_outcome(
    receipt: Mapping[str, Any], *, raw_outcome_bytes: bytes | None
) -> dict[str, Any]:
    """Inspect a claimed blinded label extraction; never write or promote.

    It checks declared order, exact raw-byte digest and blind-input declarations.
    It cannot authenticate source, time, actor, evaluator or causal improvement.
    """
    errors: list[str] = []
    if not isinstance(receipt, Mapping):
        errors.append("receipt must be a mapping")
        receipt = {}
    missing = sorted(_REQUIRED - set(receipt))
    if missing:
        errors.append("missing fields: " + ",".join(missing))

    if receipt.get("schema") != "umlf-prospective-outcome/v1":
        errors.append("unsupported receipt schema")
    if receipt.get("mode") != "PROSPECTIVE":
        errors.append("contract applies only to prospective outcomes")
    for field in ("task_family", "dataset_version", "source_locator",
                  "prediction_actor_id", "resolver_actor_id"):
        if not _nonempty(receipt.get(field)):
            errors.append("invalid or missing " + field)
    if (_nonempty(receipt.get("prediction_actor_id")) and
        _nonempty(receipt.get("resolver_actor_id")) and
        receipt["prediction_actor_id"].strip().casefold() ==
            receipt["resolver_actor_id"].strip().casefold()):
        errors.append("prediction and blind outcome actors must be distinct")

    for field in _HASH_FIELDS:
        value = receipt.get(field)
        if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
            errors.append("invalid SHA-256: " + field)
    if not isinstance(raw_outcome_bytes, bytes):
        errors.append("raw outcome bytes unavailable")
    elif (isinstance(receipt.get("raw_outcome_snapshot_sha256"), str) and
          hashlib.sha256(raw_outcome_bytes).hexdigest() !=
              receipt["raw_outcome_snapshot_sha256"]):
        errors.append("raw outcome snapshot digest mismatch")

    times = {field: _parse_utc(receipt.get(field)) for field in _TIME_FIELDS}
    for field, value in times.items():
        if value is None:
            errors.append("invalid timezone-aware timestamp: " + field)
    if all(value is not None for value in times.values()):
        if not (times["evaluation_packet_frozen_at"] <=
                times["prediction_frozen_at"] <
                times["outcome_first_available_at"] <=
                times["raw_outcome_captured_at"] <=
                times["blind_label_extracted_at"]):
            errors.append("invalid preregistration/prediction/outcome ordering")

    if receipt.get("outcome_source_kind") != "RAW_SOURCE_SNAPSHOT":
        errors.append("outcome must use a raw source snapshot")
    if receipt.get("outcome_source_transform") != "NONE":
        errors.append("unregistered source transformations not permitted")
    if receipt.get("resolver_input_contract") != "FROZEN_RULE_PLUS_RAW_SOURCE_ONLY":
        errors.append("resolver input contract invalid")
    for field in ("resolver_saw_prediction", "resolver_saw_model_trace",
                  "resolver_saw_prior_resolution"):
        if receipt.get(field) is not False:
            errors.append("blind resolver exposure not excluded: " + field)

    return {
        "status": "STRUCTURALLY_ELIGIBLE_FOR_REVIEW" if not errors else "BLOCKED",
        "reasons": sorted(set(errors)),
        "read_only": True,
        "external_review_required": True,
        "source_authenticity_proven": False,
        "timestamp_authenticity_proven": False,
        "reviewer_independence_proven": False,
        "semantic_label_accuracy_proven": False,
        "causal_learning_improvement_proven": False,
        "model_promoted": False,
        "production_ready": False,
    }
