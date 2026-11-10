"""Read-only mock provider routing proposal. Never invokes providers or promotes models.

Trust boundary: a declared receipt is not authenticated benchmark provenance.
This prototype scores only a frozen *synthetic* set with explicit policy gates.
"""
from __future__ import annotations
import hashlib
import json
import math
import re
from typing import Any
from capability_contracts import PROVIDERS

SCHEMA = "umlf-evidence-router/v1"
_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,79}$")
_SHA = re.compile(r"^[0-9a-f]{64}$")
_MAX_BYTES = 32768


class RouterContractError(ValueError):
    pass


def _digest(value: Any) -> str:
    try:
        raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False,
                         ensure_ascii=False).encode("utf-8")
    except (TypeError, ValueError, OverflowError) as exc:
        raise RouterContractError("noncanonical input") from exc
    if len(raw) > _MAX_BYTES:
        raise RouterContractError("packet too large")
    return hashlib.sha256(raw).hexdigest()


def _fields(value: Any, names: set[str], label: str) -> None:
    if type(value) is not dict or set(value) != names:
        raise RouterContractError(label + " fields mismatch")


def _id(value: Any) -> bool:
    return type(value) is str and _ID.fullmatch(value) is not None


def _number(value: Any, *, low: float = 0, high: float = float("inf")) -> bool:
    return type(value) in (int, float) and math.isfinite(value) and low <= value <= high


def inspect_router(packet: Any, receipts: Any, *, trusted_packet_sha256: str) -> dict[str, Any]:
    """Return deterministic review *proposal*, not real routing authority."""
    _fields(packet, {"schema", "frozen", "mode", "task_family", "dataset_version",
                     "evaluator_sha256", "case_set_sha256", "case_count",
                     "min_accuracy", "max_critical_error_rate", "max_latency_ms",
                     "max_cost_usd", "min_coverage"}, "packet")
    if (packet["schema"] != SCHEMA or packet["frozen"] is not True or
            packet["mode"] != "SYNTHETIC_ONLY" or not _id(packet["task_family"]) or
            not _id(packet["dataset_version"]) or
            type(packet["case_count"]) is not int or not 12 <= packet["case_count"] <= 128 or
            any(type(packet[k]) is not str or _SHA.fullmatch(packet[k]) is None
                for k in ("evaluator_sha256", "case_set_sha256")) or
            any(not _number(packet[k], low=0, high=1)
                for k in ("min_accuracy", "max_critical_error_rate", "min_coverage")) or
            not _number(packet["max_latency_ms"]) or
            not _number(packet["max_cost_usd"])):
        raise RouterContractError("invalid frozen synthetic policy")
    # V1 requires full-case coverage. Partial counts must be rejected, not ranked.
    if packet["min_coverage"] != 1:
        raise RouterContractError("v1 requires complete coverage")
    expected = _digest(packet)
    if type(trusted_packet_sha256) is not str or trusted_packet_sha256 != expected:
        raise RouterContractError("packet SHA mismatch with caller pin")
    if type(receipts) is not list or not 1 <= len(receipts) <= 4:
        raise RouterContractError("one to four bounded receipts required")
    accepted = []
    rejected = []
    seen = set()
    for receipt in receipts:
        _fields(receipt, {"provider_id", "packet_sha256", "evaluator_sha256",
                          "case_set_sha256", "evaluated_case_count", "accuracy",
                          "critical_error_rate", "latency_ms", "cost_usd",
                          "integrity_failures", "status", "evidence_mode"}, "receipt")
        provider = receipt["provider_id"]
        if type(provider) is not str or provider not in PROVIDERS or provider in seen:
            raise RouterContractError("unknown or repeated provider")
        seen.add(provider)
        if (receipt["packet_sha256"] != expected or
                receipt["evaluator_sha256"] != packet["evaluator_sha256"] or
                receipt["case_set_sha256"] != packet["case_set_sha256"] or
                type(receipt["evaluated_case_count"]) is not int or
                receipt["evaluated_case_count"] != packet["case_count"] or
                receipt["status"] != "SIMULATED_BENCHMARK" or
                receipt["evidence_mode"] != "SYNTHETIC_ONLY"):
            raise RouterContractError("receipt not bound to frozen benchmark")
        for k in ("accuracy", "critical_error_rate"):
            if not _number(receipt[k], low=0, high=1):
                raise RouterContractError("invalid quality metric")
        for k in ("latency_ms", "cost_usd"):
            if not _number(receipt[k]):
                raise RouterContractError("invalid resource metric")
        failures = receipt["integrity_failures"]
        _fields(failures, {"leakage", "security", "authority", "reproducibility",
                           "data_contract"}, "integrity")
        if any(type(v) is not int or v < 0 for v in failures.values()):
            raise RouterContractError("invalid integrity counter")
        reasons = []
        if any(failures.values()):
            reasons.append("INTEGRITY_FAILURE")
        if receipt["accuracy"] < packet["min_accuracy"]:
            reasons.append("ACCURACY_BELOW_FLOOR")
        if receipt["critical_error_rate"] > packet["max_critical_error_rate"]:
            reasons.append("CRITICAL_ERROR_GUARDRAIL")
        if receipt["latency_ms"] > packet["max_latency_ms"]:
            reasons.append("LATENCY_LIMIT")
        if receipt["cost_usd"] > packet["max_cost_usd"]:
            reasons.append("COST_LIMIT")
        if reasons:
            rejected.append({"provider_id": provider, "reasons": reasons})
        else:
            accepted.append(receipt)
    # Only a proposal. Rank lowest declared cost, then latency, then highest quality.
    accepted.sort(key=lambda r: (r["cost_usd"], r["latency_ms"], -r["accuracy"], r["provider_id"]))
    return {
        "schema": "umlf-evidence-router-result/v1",
        "status": "SYNTHETIC_PROPOSAL_ONLY" if accepted else "NO_ELIGIBLE_CANDIDATE",
        "packet_sha256": expected,
        "proposed_provider_id": accepted[0]["provider_id"] if accepted else None,
        "eligible_provider_ids": [r["provider_id"] for r in accepted],
        "rejected": sorted(rejected, key=lambda x: x["provider_id"]),
        "receipt_count": len(receipts),
        "benchmark_provenance_authenticated": False,
        "provider_identity_authenticated": False,
        "causal_improvement_proven": False,
        "api_called": False,
        "state_changed": False,
        "model_promoted": False,
        "deployment_approved": False,
        "production_ready": False,
        "external_review_required": True,
    }
