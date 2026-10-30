"""Audit-only A -> B -> C integration with strictly synthetic, non-authoritative receipts."""
from __future__ import annotations
from typing import Any
from capability_contracts import MockCapabilityAdapter, validate_mock_result
from capability_contracts.evidence_router import inspect_router, RouterContractError
from task_templates.tabular_classification.evidence_pilot import inspect_synthetic_paired_trial, EvidencePilotError
from learning_governance import digest

# The integrated mock A -> B -> C chain is limited by A's 64-case payload.
# The B pilot's standalone 128-case capability is not a bridge entitlement.
MAX_SYNTHETIC_CHAIN_CASES = 64


class BridgeContractError(ValueError):
    pass


def inspect_synthetic_chain(
    request: dict[str, Any], cases: list[dict[str, Any]], baseline: dict[str, Any],
    challenger: dict[str, Any], evaluation_packet: dict[str, Any],
    router_packet: dict[str, Any], *, expected_evaluation_sha256: str,
    expected_router_sha256: str, expected_provider_id: str,
) -> dict[str, Any]:
    """Recompute mock and paired metrics; never accept caller-provided benchmark scores.

    Frozen-packet pins and evaluator digests are caller-provided declarations.
    No external issuer, independent holdout, real execution or reviewer is
    authenticated here. All outcomes stay synthetic and non-authoritative.
    """
    if type(expected_provider_id) is not str:
        raise BridgeContractError("provider identity must be a trusted invocation argument")
    if type(request) is not dict or request.get("capability") != "analyze_errors":
        raise BridgeContractError("only the mock error-analysis capability is allowed")
    if type(evaluation_packet) is not dict or type(router_packet) is not dict:
        raise BridgeContractError("synthetic policies must be objects")
    if (type(cases) is not list or not 12 <= len(cases) <= MAX_SYNTHETIC_CHAIN_CASES
            or type(baseline) is not dict):
        raise BridgeContractError("invalid paired fixture or unsupported mock case count")
    context = request.get("context")
    if type(context) is not dict:
        raise BridgeContractError("mock request context must be an object")
    predicted = baseline.get("predictions")
    if not isinstance(predicted, list) or not isinstance(request.get("payload"), dict):
        raise BridgeContractError("invalid mock prediction payload")
    by_id = {}
    for item in predicted:
        if type(item) is not dict or set(item) != {"case_id", "predicted"}:
            raise BridgeContractError("malformed baseline prediction")
        if type(item["case_id"]) is not str:
            raise BridgeContractError("baseline case ID must be text")
        if item["case_id"] in by_id:
            raise BridgeContractError("duplicated baseline prediction")
        by_id[item["case_id"]] = item["predicted"]
    expected_cases = []
    for item in cases:
        if type(item) is not dict or set(item) != {"case_id", "label", "critical"}:
            raise BridgeContractError("malformed synthetic case")
        case_id = item["case_id"]
        if type(case_id) is not str:
            raise BridgeContractError("synthetic case ID must be text")
        if case_id not in by_id:
            raise BridgeContractError("incomplete baseline prediction coverage")
        expected_cases.append({"case_id": case_id, "actual": item["label"],
                               "predicted": by_id[case_id]})
    if len(by_id) != len(expected_cases):
        raise BridgeContractError("incomplete or foreign baseline predictions")
    if (request["payload"] != {"cases": expected_cases} or
            context.get("data_role") != "SYNTHETIC" or
            context.get("task_family") != "TABULAR_CLASSIFICATION" or
            context.get("dataset_version") != evaluation_packet.get("dataset_version")):
        raise BridgeContractError("mock request not bound to the exact synthetic baseline")
    try:
        adapter = MockCapabilityAdapter(expected_provider_id)
        mock_receipt = adapter.invoke(request)
        validate_mock_result(request, mock_receipt, expected_provider_id=expected_provider_id)
        evaluated = inspect_synthetic_paired_trial(
            evaluation_packet, cases, baseline, challenger,
            expected_packet_sha256=expected_evaluation_sha256)
    except (ValueError, TypeError, KeyError) as exc:
        raise BridgeContractError("invalid mock or evaluation evidence") from exc

    # Only a successful structural synthetic comparison may feed the demo router.
    if evaluated["status"] != "SYNTHETIC_REVIEW_ELIGIBLE":
        return {"status": "BLOCKED_BY_EVALUATION", "mock_receipt": mock_receipt,
                "evaluation": evaluated, "router_result": None,
                "provider_authenticity_proven": False,
                "benchmark_provenance_authenticated": False,
                "holdout_access_isolation_proven": False,
                "integrity_declarations_authenticated": False,
                "real_world_improvement_proven": False,
                "api_called": False, "state_changed": False,
                "model_promoted": False, "deployment_approved": False,
                "production_ready": False, "external_review_required": True}

    if (router_packet.get("mode") != "SYNTHETIC_ONLY" or
            router_packet.get("task_family") != evaluation_packet["task_family"] or
            router_packet.get("dataset_version") != evaluation_packet["dataset_version"] or
            router_packet.get("case_set_sha256") != evaluated["cases_sha256"] or
            router_packet.get("case_count") != evaluated["case_count"]):
        raise BridgeContractError("router policy does not match evaluated case set")
    receipt = {
        "provider_id": expected_provider_id,
        "packet_sha256": expected_router_sha256,
        "evaluator_sha256": router_packet.get("evaluator_sha256"),
        "case_set_sha256": evaluated["cases_sha256"],
        "evaluated_case_count": evaluated["case_count"],
        "accuracy": evaluated["challenger_metrics"]["accuracy"],
        "critical_error_rate": evaluated["challenger_metrics"]["critical_error_rate"],
        "latency_ms": 0, "cost_usd": 0,
        "integrity_failures": dict(challenger["critical_failures"]),
        "status": "SIMULATED_BENCHMARK",
        "evidence_mode": "SYNTHETIC_ONLY",
    }
    try:
        routed = inspect_router(router_packet, [receipt],
                                trusted_packet_sha256=expected_router_sha256)
    except (RouterContractError, TypeError, KeyError) as exc:
        raise BridgeContractError("router contract rejected linked receipt") from exc
    return {
        "status": "SYNTHETIC_CHAIN_PROPOSAL_ONLY" if routed["proposed_provider_id"]
                  else "ROUTER_REJECTED",
        "mock_receipt": mock_receipt, "evaluation": evaluated,
        "router_result": routed, "receipt_origin": "DERIVED_IN_THIS_SYNTHETIC_CALL",
        "provider_authenticity_proven": False,
        "benchmark_provenance_authenticated": False,
        "holdout_access_isolation_proven": False,
        "integrity_declarations_authenticated": False,
        "real_world_improvement_proven": False,
        "api_called": False, "state_changed": False,
        "model_promoted": False, "deployment_approved": False,
        "production_ready": False, "external_review_required": True,
    }
