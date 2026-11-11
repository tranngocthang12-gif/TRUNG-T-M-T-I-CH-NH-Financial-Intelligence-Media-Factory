"""Q04 provisional, domain-neutral Data Contract v1.

Pure structural validation of in-memory row snapshots. This module does NOT
fetch data, authenticate sources or rights, prove semantic leakage safety,
train models, grant access, or deploy anything.
"""
from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime
from collections.abc import Mapping

SCHEMA = "umlf-data/v1"
RECEIPT_SCHEMA = "umlf-data-receipt/v1"
MAX_ROWS = 10000
MISSING_REASONS = frozenset({"NOT_OBSERVED", "SOURCE_MISSING", "REDACTED"})


class DataContractError(ValueError):
    """Declared data snapshot is structurally unsafe or inconsistent."""


def _object(value, keys, name):
    if not isinstance(value, Mapping) or set(value) != set(keys):
        raise DataContractError(f"{name}: expected exactly {sorted(keys)}")
    return value


def _text(value, name, *, scoped=False):
    if (not isinstance(value, str) or not value.strip()
            or value != value.strip() or len(value) > 256
            or (scoped and "*" in value)):
        raise DataContractError(f"{name}: explicit bounded text required")
    return value


def _timestamp(value, name):
    _text(value, name)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise DataContractError(f"{name}: invalid ISO-8601 time") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise DataContractError(f"{name}: timezone required")
    return parsed


def _scalar(value, name):
    if value is None:
        return
    if type(value) not in (str, int, float, bool):
        raise DataContractError(f"{name}: scalar or null required")
    if isinstance(value, float) and not math.isfinite(value):
        raise DataContractError(f"{name}: NaN/Infinity forbidden")
    if isinstance(value, str) and len(value) > 4096:
        raise DataContractError(f"{name}: excessive scalar length")


def _observed_cell(cell, name, *, cutoff, frozen_at, is_feature):
    _object(cell, ("value", "observed_at", "missing_reason"), name)
    value = cell["value"]
    _scalar(value, name + ".value")
    reason = cell["missing_reason"]
    observed = cell["observed_at"]
    if value is None:
        if reason not in MISSING_REASONS or observed is not None:
            raise DataContractError(f"{name}: missing value requires reason and null observation")
    else:
        if reason is not None:
            raise DataContractError(f"{name}: observed value cannot have missing reason")
        moment = _timestamp(observed, name + ".observed_at")
        if moment > frozen_at:
            raise DataContractError(f"{name}: observation after frozen snapshot")
        if is_feature and moment > cutoff:
            raise DataContractError(f"{name}: feature not available at decision time")


def _canonical_bytes(value, label):
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, OverflowError) as exc:
        raise DataContractError(f"{label}: noncanonical JSON") from exc


def validate_snapshot(contract, rows):
    """Return structural receipt, not training/rights/promotion authorization.

    Rows include availability metadata for each feature and optional target.
    Semantics, claimed times, source authenticity and consent are NOT verified.
    """
    c = _object(contract, ("schema", "scope", "dataset", "columns", "source", "snapshot"),
                "contract")
    if c["schema"] != SCHEMA:
        raise DataContractError("unsupported data schema")

    scope = _object(c["scope"], ("task_family", "domain"), "scope")
    for key in ("task_family", "domain"):
        _text(scope[key], "scope." + key, scoped=True)

    dataset = _object(c["dataset"], ("id", "version"), "dataset")
    for key in ("id", "version"):
        _text(dataset[key], "dataset." + key)

    cols = _object(c["columns"], ("target", "features"), "columns")
    target = _text(cols["target"], "columns.target")
    features = cols["features"]
    if (not isinstance(features, list) or not features or len(features) > 512
            or any(not isinstance(v, str) for v in features)):
        raise DataContractError("columns.features: nonempty string list required")
    for i, name in enumerate(features):
        _text(name, f"columns.features[{i}]")
    if len(set(features)) != len(features) or target in features:
        raise DataContractError("duplicate feature or target included among features")

    source = _object(c["source"], ("locator", "rights_declaration", "rights_ref"), "source")
    _text(source["locator"], "source.locator")
    _text(source["rights_ref"], "source.rights_ref")
    if source["rights_declaration"] not in (
            "OWNER_DECLARED", "LICENSE_DECLARED", "PUBLIC_DECLARED"):
        raise DataContractError("source.rights_declaration: explicit declared basis required")

    snapshot = _object(c["snapshot"], ("frozen_at", "rows_sha256", "row_count"), "snapshot")
    frozen_at = _timestamp(snapshot["frozen_at"], "snapshot.frozen_at")
    expected_hash = snapshot["rows_sha256"]
    if (not isinstance(expected_hash, str) or len(expected_hash) != 64
            or any(ch not in "0123456789abcdef" for ch in expected_hash)):
        raise DataContractError("snapshot.rows_sha256: lowercase SHA-256 required")
    expected_count = snapshot["row_count"]
    if type(expected_count) is not int or not 1 <= expected_count <= MAX_ROWS:
        raise DataContractError("snapshot.row_count: positive bounded integer required")

    if not isinstance(rows, list) or len(rows) != expected_count:
        raise DataContractError("row_count mismatch or rows not a list")
    seen_ids, seen_events = set(), set()
    for i, row in enumerate(rows):
        label = f"rows[{i}]"
        _object(row, ("row_id", "entity_id", "event_at", "decision_at", "features", "target"),
                label)
        row_id = _text(row["row_id"], label + ".row_id")
        entity_id = _text(row["entity_id"], label + ".entity_id")
        event = _timestamp(row["event_at"], label + ".event_at")
        cutoff = _timestamp(row["decision_at"], label + ".decision_at")
        if event > cutoff or cutoff > frozen_at:
            raise DataContractError(label + ": event/decision occurs after valid cutoff")
        if row_id in seen_ids or (entity_id, event) in seen_events:
            raise DataContractError(label + ": duplicate row identity or entity/event")
        seen_ids.add(row_id)
        seen_events.add((entity_id, event))

        observed_features = _object(row["features"], features, label + ".features")
        for feature in features:
            _observed_cell(observed_features[feature], label + ".features." + feature,
                           cutoff=cutoff, frozen_at=frozen_at, is_feature=True)
        _observed_cell(row["target"], label + ".target",
                       cutoff=cutoff, frozen_at=frozen_at, is_feature=False)

    raw = _canonical_bytes(rows, "rows")
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected_hash:
        raise DataContractError("snapshot hash mismatch; rows not pinned")
    contract_hash = hashlib.sha256(_canonical_bytes(c, "contract")).hexdigest()
    return {
        "schema": RECEIPT_SCHEMA,
        "contract_sha256": contract_hash,
        "rows_sha256": actual,
        "row_count": expected_count,
        "task_family": scope["task_family"],
        "domain": scope["domain"],
        "validation": "STRUCTURAL_ONLY",
        "source_rights_verified": False,
        "source_authenticity_proven": False,
        "availability_metadata_authenticated": False,
        "semantic_leakage_excluded": False,
        "training_authorized": False,
        "deployment_authorized": False,
        "retraining_authorized": False,
        "owner_approval_proven": False,
    }
