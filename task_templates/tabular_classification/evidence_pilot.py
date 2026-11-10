"""Read-only synthetic paired-evaluation pilot for tabular binary classification.

Computes metrics from per-case predictions, then delegates decision thresholds
and guardrails to the existing Factory governance comparator. Synthetic only:
no training, no use of production holdouts, no independent provenance proof.
"""
from __future__ import annotations

import re
from typing import Any

from learning_governance import compare_parent_candidate, digest

SCHEMA = "umlf-classification-evidence-pilot/v1"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
IDENT = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,79}$")
INTEGRITY_KEYS = frozenset({"leakage", "security", "reproducibility", "authority", "data_contract"})
FORBIDDEN_FEATURES = frozenset({"label", "target", "case_id", "post_outcome", "future_label"})


class EvidencePilotError(ValueError):
    """Reject malformed, unfrozen or non-synthetic evidence instead of guessing."""


def _exact(record: Any, required: set[str], name: str) -> None:
    if type(record) is not dict or set(record) != required:
        raise EvidencePilotError(name + " fields invalid")


def _id(value: Any, name: str) -> None:
    if type(value) is not str or IDENT.fullmatch(value) is None:
        raise EvidencePilotError(name + " must be a nonempty bounded identifier")


def _binary(value: Any, name: str) -> None:
    if type(value) is not int or value not in (0, 1):
        raise EvidencePilotError(name + " must be integer 0 or 1")


def _validated_cases(cases: Any) -> list[dict[str, Any]]:
    if type(cases) is not list or not 12 <= len(cases) <= 128:
        raise EvidencePilotError("synthetic cases require 12..128 rows")
    ids: set[str] = set()
    for row in cases:
        _exact(row, {"case_id", "label", "critical"}, "case")
        _id(row["case_id"], "case_id")
        _binary(row["label"], "label")
        if type(row["critical"]) is not bool:
            raise EvidencePilotError("critical must be boolean")
        if row["case_id"] in ids:
            raise EvidencePilotError("duplicate case_id")
        ids.add(row["case_id"])
    if {row["label"] for row in cases} != {0, 1}:
        raise EvidencePilotError("both label classes required")
    if sum(row["critical"] for row in cases) < 2:
        raise EvidencePilotError("at least two critical cases required")
    return sorted(cases, key=lambda row: row["case_id"])


def freeze_synthetic_cases(cases: Any) -> str:
    """Byte-stable ground-truth fixture digest, not real source attestation."""
    return digest(_validated_cases(cases))


def _validate_packet(packet: Any, cases: Any, expected_sha256: Any) -> tuple[str, list[dict[str, Any]]]:
    _exact(packet, {"schema", "frozen", "evidence_mode", "task_family", "dataset_version",
                    "cases_sha256", "allowed_features", "metric_specs"}, "packet")
    if (packet["schema"] != SCHEMA or packet["frozen"] is not True or
            packet["evidence_mode"] != "SYNTHETIC_ONLY" or
            packet["task_family"] != "TABULAR_CLASSIFICATION"):
        raise EvidencePilotError("only frozen synthetic tabular classification packets are allowed")
    _id(packet["dataset_version"], "dataset_version")
    try:
        canonical_packet_sha = digest(packet)
    except (TypeError, ValueError, OverflowError) as exc:
        raise EvidencePilotError("frozen packet is not canonical JSON") from exc
    if (type(expected_sha256) is not str or SHA256.fullmatch(expected_sha256) is None or
            expected_sha256 != canonical_packet_sha):
        raise EvidencePilotError("packet does not match externally supplied pin")
    rows = _validated_cases(cases)
    if (type(packet["cases_sha256"]) is not str or SHA256.fullmatch(packet["cases_sha256"]) is None or
            packet["cases_sha256"] != digest(rows)):
        raise EvidencePilotError("frozen ground truth mismatch")
    features = packet["allowed_features"]
    if (type(features) is not list or not features or len(features) > 32 or
            any(type(f) is not str or IDENT.fullmatch(f) is None for f in features) or
            len(set(features)) != len(features) or
            set(features) & FORBIDDEN_FEATURES):
        raise EvidencePilotError("invalid allowed feature contract")
    specs = packet["metric_specs"]
    if type(specs) is not list or len(specs) != 2:
        raise EvidencePilotError("exactly one primary and one critical guardrail required")
    metrics = {}
    for spec in specs:
        _exact(spec, {"name", "direction", "role", "min_improvement"}, "metric spec")
        name = spec["name"]
        if type(name) is not str or name in metrics:
            raise EvidencePilotError("invalid or repeated metric")
        if (type(spec["min_improvement"]) not in (int, float) or
                not 0 <= spec["min_improvement"] <= 1):
            raise EvidencePilotError("metric improvement margin invalid")
        metrics[name] = (spec["direction"], spec["role"], spec["min_improvement"])
    if (set(metrics) != {"accuracy", "critical_error_rate"} or
            metrics["accuracy"][:2] != ("MAX", "PRIMARY") or
            metrics["critical_error_rate"] != ("MIN", "GUARDRAIL", 0)):
        raise EvidencePilotError("metric semantics must remain task-specific and frozen")
    return expected_sha256, rows


def _check_run(run: Any, rows: list[dict[str, Any]], allowed_features: list[str]) -> tuple[dict, int, int]:
    _exact(run, {"run_ref", "features_used", "predictions", "critical_failures"}, "evaluation run")
    _id(run["run_ref"], "run_ref")
    features = run["features_used"]
    if (type(features) is not list or len(features) > 32 or
            any(type(f) is not str or f not in allowed_features for f in features) or
            len(set(features)) != len(features)):
        raise EvidencePilotError("run used unapproved, repeated or leaky features")
    critical = run["critical_failures"]
    if (type(critical) is not dict or set(critical) != INTEGRITY_KEYS or
            any(type(count) is not int or count < 0 for count in critical.values())):
        raise EvidencePilotError("missing or invalid declared integrity counters")
    predictions = run["predictions"]
    if type(predictions) is not list or len(predictions) != len(rows):
        raise EvidencePilotError("predictions must cover the entire frozen fixture")
    lookup: dict[str, int] = {}
    for row in predictions:
        _exact(row, {"case_id", "predicted"}, "prediction")
        _id(row["case_id"], "prediction case_id")
        _binary(row["predicted"], "prediction")
        if row["case_id"] in lookup:
            raise EvidencePilotError("duplicate prediction case_id")
        lookup[row["case_id"]] = row["predicted"]
    if set(lookup) != {row["case_id"] for row in rows}:
        raise EvidencePilotError("prediction IDs differ from frozen fixture")
    correct = sum(lookup[row["case_id"]] == row["label"] for row in rows)
    critical_rows = [row for row in rows if row["critical"]]
    critical_errors = sum(lookup[row["case_id"]] != row["label"] for row in critical_rows)
    scores = {"accuracy": correct / len(rows),
              "critical_error_rate": critical_errors / len(critical_rows)}
    return scores, correct, critical_errors


def inspect_synthetic_paired_trial(packet: Any, cases: Any, baseline: Any, challenger: Any,
                                   *, expected_packet_sha256: str) -> dict[str, Any]:
    """Compute paired metrics without trusting model-supplied scores or approving anything."""
    packet_sha, rows = _validate_packet(packet, cases, expected_packet_sha256)
    b_metrics, _, _ = _check_run(baseline, rows, packet["allowed_features"])
    c_metrics, _, _ = _check_run(challenger, rows, packet["allowed_features"])
    if baseline["run_ref"] == challenger["run_ref"]:
        raise EvidencePilotError("baseline and challenger must be separate runs")
    def receipt(run: dict, metrics: dict) -> dict:
        return {"packet_sha256": packet_sha, "run_ref": run["run_ref"],
                "metrics": metrics, "critical_failures": run["critical_failures"]}
    verdict = compare_parent_candidate(packet, receipt(baseline, b_metrics),
                                       receipt(challenger, c_metrics))
    baseline_by_id = {x["case_id"]: x["predicted"] for x in baseline["predictions"]}
    challenger_by_id = {x["case_id"]: x["predicted"] for x in challenger["predictions"]}
    wins = sum(baseline_by_id[r["case_id"]] != r["label"] and
               challenger_by_id[r["case_id"]] == r["label"] for r in rows)
    losses = sum(baseline_by_id[r["case_id"]] == r["label"] and
                 challenger_by_id[r["case_id"]] != r["label"] for r in rows)
    return {"schema": "umlf-classification-evidence-result/v1",
            "status": "SYNTHETIC_REVIEW_ELIGIBLE" if verdict["candidate_eligible_for_external_review"]
                      else "SYNTHETIC_NOT_ELIGIBLE",
            "dataset_version": packet["dataset_version"],
            "packet_sha256": packet_sha,
            "cases_sha256": packet["cases_sha256"],
            "case_count": len(rows), "critical_case_count": sum(r["critical"] for r in rows),
            "baseline_metrics": b_metrics, "challenger_metrics": c_metrics,
            "paired_wins": wins, "paired_losses": losses,
            "governance_verdict": verdict,
            "source_authenticity_proven": False,
            "holdout_access_isolation_proven": False,
            "integrity_declarations_authenticated": False,
            "real_world_improvement_proven": False,
            "model_promoted": False, "production_ready": False, "state_changed": False,
            "external_review_required": True}
