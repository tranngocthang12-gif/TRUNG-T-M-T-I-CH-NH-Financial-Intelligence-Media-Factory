"""UMLF Q03: deterministic, read-only Problem Contract v1.

A valid receipt describes intent and immutable dataset identity. It does NOT
authorize fetching data, training, model promotion, spending or deployment.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from copy import deepcopy

SCHEMA = "umlf-problem/v1"
FIELDS = frozenset({"schema", "problem", "data", "target", "metrics", "constraints", "deployment", "retraining"})
RECEIPT_SCHEMA = "umlf-problem-receipt/v1"


class ProblemContractError(ValueError):
    """A user problem declaration cannot safely enter the ML Factory."""


def _text(value, label):
    if not isinstance(value, str) or not value.strip() or value != value.strip() or value == "*":
        raise ProblemContractError(f"{label}: explicit non-wildcard text required")
    return value


def _object(value, label, required):
    if not isinstance(value, Mapping) or set(value) != set(required):
        raise ProblemContractError(f"{label}: expected exactly {sorted(required)}")
    return value


def _sha(value, label):
    if (not isinstance(value, str) or len(value) != 64
            or any(ch not in "0123456789abcdef" for ch in value)):
        raise ProblemContractError(f"{label}: canonical lowercase SHA-256 required")
    return value


def validate_problem(spec: Mapping) -> dict:
    """Validate exact v1 schema; return a copy, never mutate caller input."""
    _object(spec, "problem declaration", FIELDS)
    if spec["schema"] != SCHEMA:
        raise ProblemContractError("unsupported problem schema")

    p = _object(spec["problem"], "problem", {"task_family", "domain", "objective"})
    for key in ("task_family", "domain", "objective"):
        _text(p[key], f"problem.{key}")
    if any(key in p["task_family"] for key in ("*", "/")) or "*" in p["domain"]:
        raise ProblemContractError("wildcard or ambiguous task/domain forbidden")

    d = _object(spec["data"], "data", {"dataset_id", "version", "snapshot_sha256", "source_locator"})
    for key in ("dataset_id", "version", "source_locator"):
        _text(d[key], f"data.{key}")
    _sha(d["snapshot_sha256"], "data.snapshot_sha256")

    t = _object(spec["target"], "target", {"name", "kind"})
    _text(t["name"], "target.name")
    _text(t["kind"], "target.kind")

    m = _object(spec["metrics"], "metrics", {"primary", "direction", "baseline"})
    _text(m["primary"], "metrics.primary")
    _text(m["baseline"], "metrics.baseline")
    if m["direction"] not in ("MINIMIZE", "MAXIMIZE"):
        raise ProblemContractError("metrics.direction: MINIMIZE or MAXIMIZE required")

    c = _object(spec["constraints"], "constraints", {"privacy_level", "max_compute_seconds"})
    if c["privacy_level"] not in ("PUBLIC_SYNTHETIC", "RESTRICTED"):
        raise ProblemContractError("constraints.privacy_level: unsupported")
    if (type(c["max_compute_seconds"]) is not int or not 1 <= c["max_compute_seconds"] <= 86400):
        raise ProblemContractError("constraints.max_compute_seconds: positive bounded integer required")

    dep = _object(spec["deployment"], "deployment", {"mode", "owner_gate"})
    if dep["mode"] != "OFFLINE_ONLY" or dep["owner_gate"] is not True:
        raise ProblemContractError("deployment authority is unavailable in Q03")

    retrain = _object(spec["retraining"], "retraining", {"mode", "owner_gate"})
    if retrain["mode"] not in ("DISABLED", "PROPOSAL_ONLY") or retrain["owner_gate"] is not True:
        raise ProblemContractError("automatic retraining is forbidden")

    # Deep-copy through a strict JSON round-trip to rule out NaN/Infinity,
    # arbitrary Python objects, hidden aliases and inconsistent digests.
    try:
        canonical = json.dumps(spec, ensure_ascii=False, sort_keys=True,
                               separators=(",", ":"), allow_nan=False)
        normalized = json.loads(canonical)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ProblemContractError("declaration is not canonical JSON") from exc
    return deepcopy(normalized)


def problem_receipt(spec: Mapping) -> dict:
    """Proof of structural validation only; never an approval or execution permit."""
    normalized = validate_problem(spec)
    encoded = json.dumps(normalized, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    return {
        "schema": RECEIPT_SCHEMA,
        "contract_sha256": hashlib.sha256(encoded).hexdigest(),
        "task_family": normalized["problem"]["task_family"],
        "domain": normalized["problem"]["domain"],
        "dataset_snapshot_sha256": normalized["data"]["snapshot_sha256"],
        "validation": "STRUCTURAL_ONLY",
        "training_authorized": False,
        "deployment_authorized": False,
        "retraining_authorized": False,
        "external_review_proven": False,
        "owner_approval_proven": False,
    }
