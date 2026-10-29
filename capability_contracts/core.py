"""Offline-only, provider-neutral capability contract and deterministic mock adapters.

No provider SDKs, network, filesystem mutation, model training, approval or deployment.
Validating a shape is not evidence that a model's judgment is correct.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from typing import Any, Mapping

REQUEST_SCHEMA = "umlf-capability-request/v1"
RESULT_SCHEMA = "umlf-capability-result/v1"
CAPABILITIES = frozenset({"validate_data", "analyze_errors", "inspect_experiment"})
PROVIDERS = frozenset({"mock-claude", "mock-gemini", "mock-grok", "mock-gpt"})
DATA_ROLES = frozenset({"SYNTHETIC", "TRAINING"})
MAX_BYTES = 16384
_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,79}$")


class CapabilityContractError(ValueError):
    """An invalid or unauthorized offline capability call is rejected."""


def _json_bytes(value: Any) -> bytes:
    def walk(item: Any, depth: int) -> None:
        if depth > 10:
            raise CapabilityContractError("JSON nesting exceeds the permitted depth")
        if isinstance(item, dict):
            if len(item) > 100 or any(type(k) is not str for k in item):
                raise CapabilityContractError("JSON object keys/size invalid")
            for sub in item.values():
                walk(sub, depth + 1)
        elif isinstance(item, list):
            if len(item) > 100:
                raise CapabilityContractError("JSON array too long")
            for sub in item:
                walk(sub, depth + 1)
        elif type(item) is float:
            if not math.isfinite(item):
                raise CapabilityContractError("nonfinite JSON number")
        elif item is not None and type(item) not in (str, int, bool):
            raise CapabilityContractError("unsupported JSON value")

    walk(value, 0)
    try:
        raw = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, OverflowError) as exc:
        raise CapabilityContractError("not canonical JSON") from exc
    if len(raw) > MAX_BYTES:
        raise CapabilityContractError("capability packet exceeds byte limit")
    return raw


def _digest(value: Any) -> str:
    return hashlib.sha256(_json_bytes(value)).hexdigest()


def _exact(obj: Any, fields: set[str], label: str) -> None:
    if not isinstance(obj, dict) or set(obj) != fields:
        raise CapabilityContractError(label + " must contain exactly: " + ", ".join(sorted(fields)))


def _id(value: Any, label: str) -> None:
    if type(value) is not str or _ID.fullmatch(value) is None:
        raise CapabilityContractError(label + " has invalid identifier")


def _validate_payload(capability: str, payload: Any) -> None:
    if capability == "validate_data":
        _exact(payload, {"records", "required_fields"}, "validate_data payload")
        fields, records = payload["required_fields"], payload["records"]
        if (not isinstance(fields, list) or not 1 <= len(fields) <= 32 or
                any(type(x) is not str or _ID.fullmatch(x) is None for x in fields) or
                len(set(fields)) != len(fields)):
            raise CapabilityContractError("invalid required_fields")
        if (not isinstance(records, list) or not 1 <= len(records) <= 64 or
                any(not isinstance(row, dict) for row in records)):
            raise CapabilityContractError("invalid records")
    elif capability == "analyze_errors":
        _exact(payload, {"cases"}, "analyze_errors payload")
        cases = payload["cases"]
        if not isinstance(cases, list) or not 1 <= len(cases) <= 64:
            raise CapabilityContractError("invalid cases")
        ids = []
        for case in cases:
            _exact(case, {"case_id", "actual", "predicted"}, "case")
            _id(case["case_id"], "case_id")
            if any(type(case[k]) not in (str, int, bool) for k in ("actual", "predicted")):
                raise CapabilityContractError("case labels must be str/int/bool")
            ids.append(case["case_id"])
        if len(set(ids)) != len(ids):
            raise CapabilityContractError("duplicate case identifiers")
    elif capability == "inspect_experiment":
        _exact(payload, {"declarations"}, "inspect_experiment payload")
        _exact(payload["declarations"],
               {"preregistered", "baseline_present", "holdout_frozen"}, "declarations")
        if any(type(v) is not bool for v in payload["declarations"].values()):
            raise CapabilityContractError("experiment declarations must be booleans")
    else:
        raise CapabilityContractError("unsupported capability")


def validate_request(request: Any) -> None:
    """Fail closed on malformed inputs or any attempted external action."""
    _json_bytes(request)
    _exact(request, {"schema", "request_id", "capability", "context", "constraints", "payload"}, "request")
    if request["schema"] != REQUEST_SCHEMA:
        raise CapabilityContractError("unsupported request schema")
    _id(request["request_id"], "request_id")
    capability = request["capability"]
    if type(capability) is not str or capability not in CAPABILITIES:
        raise CapabilityContractError("unsupported capability")
    _exact(request["context"], {"task_family", "domain", "dataset_version", "data_role"}, "context")
    for key in ("task_family", "domain", "dataset_version"):
        _id(request["context"][key], key)
    if type(request["context"]["data_role"]) is not str or request["context"]["data_role"] not in DATA_ROLES:
        raise CapabilityContractError("holdout/unknown data roles forbidden in mocks")
    _exact(request["constraints"], {"allow_network", "allow_mutation", "max_cost_usd"}, "constraints")
    limits = request["constraints"]
    if (limits["allow_network"] is not False or limits["allow_mutation"] is not False or
            type(limits["max_cost_usd"]) is not int or limits["max_cost_usd"] != 0):
        raise CapabilityContractError("mock capabilities prohibit network, writes and spending")
    _validate_payload(capability, request["payload"])


def _evaluate(request: Mapping[str, Any]) -> dict[str, Any]:
    capability, payload = request["capability"], request["payload"]
    if capability == "validate_data":
        return {"checked_records": len(payload["records"]),
                "missing_by_field": {field: sum(field not in row or row[field] is None
                                                for row in payload["records"])
                                     for field in sorted(payload["required_fields"])}}
    if capability == "analyze_errors":
        failed = [case["case_id"] for case in payload["cases"]
                  if type(case["actual"]) is not type(case["predicted"]) or
                  case["actual"] != case["predicted"]]
        return {"checked_cases": len(payload["cases"]), "error_case_ids": sorted(failed)}
    declarations = payload["declarations"]
    missing = sorted(key for key, value in declarations.items() if value is False)
    return {"declared_missing_or_false": missing, "declared_complete": not bool(missing)}


@dataclass(frozen=True)
class MockCapabilityAdapter:
    """Provider-labelled simulation; every provider runs the SAME local evaluator."""
    provider_id: str

    def __post_init__(self) -> None:
        if type(self.provider_id) is not str or self.provider_id not in PROVIDERS:
            raise CapabilityContractError("unknown mock provider")

    def invoke(self, request: Any) -> dict[str, Any]:
        validate_request(request)
        output = _evaluate(request)
        result = {
            "schema": RESULT_SCHEMA,
            "request_id": request["request_id"],
            "request_sha256": _digest(request),
            "capability": request["capability"],
            "provider_id": self.provider_id,
            "status": "SIMULATED_ONLY",
            "output": output,
            "output_sha256": _digest(output),
            "api_calls": 0,
            "cost_usd": 0,
            "state_changed": False,
            "approval_performed": False,
            "model_promoted": False,
            "production_ready": False,
        }
        validate_mock_result(request, result)
        return result


def validate_mock_result(request: Any, result: Any) -> None:
    """Verify receipt invariants, but do not treat mock results as real evidence."""
    validate_request(request)
    _json_bytes(result)
    _exact(result, {"schema", "request_id", "request_sha256", "capability",
                    "provider_id", "status", "output", "output_sha256", "api_calls",
                    "cost_usd", "state_changed", "approval_performed", "model_promoted",
                    "production_ready"}, "mock result")
    if (result["schema"] != RESULT_SCHEMA or
            result["request_id"] != request["request_id"] or
            result["request_sha256"] != _digest(request) or
            result["capability"] != request["capability"] or
            (type(result["provider_id"]) is not str or result["provider_id"] not in PROVIDERS) or
            result["status"] != "SIMULATED_ONLY" or
            result["output"] != _evaluate(request) or
            result["output_sha256"] != _digest(result["output"])):
        raise CapabilityContractError("mock result is not bound to the exact request")
    if (type(result["api_calls"]) is not int or result["api_calls"] != 0 or
            type(result["cost_usd"]) is not int or result["cost_usd"] != 0 or
            any(result[k] is not False for k in
                ("state_changed", "approval_performed", "model_promoted", "production_ready"))):
        raise CapabilityContractError("mock result attempted to claim forbidden authority")


def make_mock_adapters() -> dict[str, MockCapabilityAdapter]:
    return {name: MockCapabilityAdapter(name) for name in sorted(PROVIDERS)}
