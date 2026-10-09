"""Fail-closed split contract and training-only majority baseline.

This is a Task Adapter, not a universal split policy. It checks declared
row/group/temporal leakage. Unknown semantic or near-duplicate leakage remains
an independent evaluation obligation. It cannot promote or deploy models.
"""
from __future__ import annotations
import hashlib
import json
from collections import Counter
from datetime import datetime
from typing import Any, Mapping, Sequence

SCHEMA = "umlf-tabular-classification/v1"


class ContractError(ValueError):
    pass


def _json_bytes(obj: Any) -> bytes:
    try:
        return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (ValueError, TypeError, OverflowError) as exc:
        raise ContractError("rows must be JSON serializable without NaN") from exc


def freeze_rows(rows: Sequence[Mapping[str, Any]], id_key: str = "row_id") -> str:
    """Stable digest of held-out rows, including target and all metadata."""
    if not isinstance(rows, (tuple, list)) or not rows:
        raise ContractError("rows must be a nonempty list")
    if not isinstance(id_key, str) or not id_key:
        raise ContractError("invalid row identifier")
    if any(not isinstance(row, dict) or id_key not in row for row in rows):
        raise ContractError("each row must be a mapping with an id")
    try:
        ids = [str(row[id_key]) for row in rows]
        if len(set(ids)) != len(ids):
            raise ContractError("duplicate row identifier")
        blob = _json_bytes(sorted(rows, key=lambda row: str(row[id_key])))
    except (TypeError, ValueError) as exc:
        if isinstance(exc, ContractError):
            raise
        raise ContractError("unsupported identifier") from exc
    return hashlib.sha256(blob).hexdigest()


def _clock(value: Any, label: str) -> datetime:
    if not isinstance(value, str):
        raise ContractError(label + ": time must be an ISO8601 string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractError(label + ": invalid ISO8601 time") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ContractError(label + ": timezone required")
    return parsed


def _identifier(value: Any) -> str:
    if not isinstance(value, (str, int)) or isinstance(value, bool) or not str(value).strip():
        raise ContractError("row and group identifiers must be nonempty strings/integers")
    return str(value)


def _contract(spec: Any) -> dict[str, Any]:
    if not isinstance(spec, dict) or spec.get("schema") != SCHEMA:
        raise ContractError("unsupported task contract schema")
    target, features, id_key = spec.get("target"), spec.get("features"), spec.get("id_key")
    if not isinstance(target, str) or not target or not isinstance(id_key, str) or not id_key:
        raise ContractError("target and id_key required")
    if not isinstance(features, list) or not features or any(not isinstance(x, str) or not x for x in features):
        raise ContractError("nonempty feature name list required")
    if len(set(features)) != len(features) or target in features or id_key in features:
        raise ContractError("feature names must be unique and exclude target and identifiers")
    kind = spec.get("split_kind")
    if kind == "GROUP":
        key = spec.get("group_key")
        if not isinstance(key, str) or not key or key in features or key in (target, id_key):
            raise ContractError("GROUP requires a separate group_key outside features")
    elif kind == "TEMPORAL":
        keys = [spec.get(k) for k in ("time_key", "feature_available_at_key", "label_available_at_key")]
        if any(not isinstance(x, str) or not x for x in keys) or len(set(keys)) != 3:
            raise ContractError("TEMPORAL requires distinct event, feature and label availability times")
        if any(x in features or x in (target, id_key) for x in keys):
            raise ContractError("temporal metadata cannot be model features")
    else:
        raise ContractError("split_kind must be GROUP or TEMPORAL")
    seal = spec.get("frozen_holdout_sha256")
    if not isinstance(seal, str) or len(seal) != 64 or any(c not in "0123456789abcdef" for c in seal):
        raise ContractError("frozen_holdout_sha256 required before evaluation")
    return spec


def validate_split(spec: Mapping[str, Any], train: Sequence[Mapping[str, Any]],
                   heldout: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Check exact declared split; raise on ambiguity rather than silently fix it."""
    s = _contract(spec)
    if not isinstance(train, (list, tuple)) or not train or not isinstance(heldout, (list, tuple)) or not heldout:
        raise ContractError("train and heldout must be nonempty lists")
    target, id_key, features = s["target"], s["id_key"], s["features"]
    required = set(features) | {target, id_key}
    for label, rows in (("train", train), ("heldout", heldout)):
        if any(not isinstance(row, dict) or not required.issubset(row.keys()) for row in rows):
            raise ContractError(label + ": missing required column")
        keys = [_identifier(row[id_key]) for row in rows]
        if len(set(keys)) != len(keys):
            raise ContractError(label + ": duplicate row ids")
        if any(not isinstance(row[target], (int, str, bool)) for row in rows):
            raise ContractError(label + ": unsupported target values")
    if set(_identifier(row[id_key]) for row in train) & set(_identifier(row[id_key]) for row in heldout):
        raise ContractError("train/heldout row identity leakage")
    observed = freeze_rows(heldout, id_key)
    if observed != s["frozen_holdout_sha256"]:
        raise ContractError("frozen heldout digest does not match")
    if s["split_kind"] == "GROUP":
        key = s["group_key"]
        if any(key not in row for row in (*train, *heldout)):
            raise ContractError("missing group_key")
        if set(_identifier(r[key]) for r in train) & set(_identifier(r[key]) for r in heldout):
            raise ContractError("train/heldout entity leakage")
    else:
        t, f, l = (s[k] for k in ("time_key", "feature_available_at_key", "label_available_at_key"))
        records = []
        for name, rows in (("train", train), ("heldout", heldout)):
            for row in rows:
                if any(k not in row for k in (t, f, l)):
                    raise ContractError(name + ": temporal metadata missing")
                when = _clock(row[t], name + ".event")
                feature_at = _clock(row[f], name + ".feature")
                label_at = _clock(row[l], name + ".label")
                if feature_at > when:
                    raise ContractError(name + ": feature unavailable at prediction time")
                records.append((name, when, label_at))
        ttrain = [event for group, event, label in records if group == "train"]
        ttest = [event for group, event, label in records if group == "heldout"]
        first_heldout = min(ttest)
        if max(ttrain) >= first_heldout:
            raise ContractError("temporal train/heldout order violated")
        if any(label > first_heldout for group, event, label in records if group == "train"):
            raise ContractError("training label not known at test start")
    return {"status": "STRUCTURAL_SPLIT_PASS_ONLY", "frozen_holdout_sha256": observed,
            "train_n": len(train), "heldout_n": len(heldout),
            "limitations": ["semantic target leakage not established", "trusted source identity not established",
                            "metric selection and business cost not independently reviewed"]}


def majority_baseline(spec: Mapping[str, Any], train: Sequence[Mapping[str, Any]],
                      heldout: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Train-label-only baseline, not a proposed production model."""
    contract = validate_split(spec, train, heldout)
    target = spec["target"]
    counts = Counter(str(row[target]) for row in train)
    majority = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]
    actual = [str(row[target]) for row in heldout]
    label_set = sorted(set(actual))
    accuracy = sum(y == majority for y in actual) / len(actual)
    recalls = [sum(y == majority for y in actual if y == c) / actual.count(c) for c in label_set]
    balanced = sum(recalls) / len(recalls)
    return {"schema": "umlf-tabular-baseline/v1", "status": "BASELINE_ONLY_NOT_APPROVED",
            "model": "TRAIN_ONLY_MAJORITY_CLASS", "majority_class": majority,
            "metrics": {"accuracy": accuracy, "balanced_accuracy": balanced},
            "split": contract, "production_ready": False, "approval_performed": False}
