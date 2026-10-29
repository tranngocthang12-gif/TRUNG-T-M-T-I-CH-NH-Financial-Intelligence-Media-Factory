"""Synthetic offline coverage for provider-neutral capabilities."""
import ast
import copy
import inspect
import json
import unittest
from pathlib import Path

from capability_contracts import (
    CAPABILITIES, PROVIDERS, REQUEST_SCHEMA, RESULT_SCHEMA,
    CapabilityContractError, MockCapabilityAdapter,
    make_mock_adapters, validate_mock_result,
)
import capability_contracts.core as core

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "capability_contracts" / "contract_v1.schema.json"


def specimen(capability="validate_data"):
    payloads = {
        "validate_data": {"records": [{"x": 1, "label": 0}, {"x": 2}],
                          "required_fields": ["x", "label"]},
        "analyze_errors": {"cases": [
            {"case_id": "c1", "actual": 0, "predicted": 0},
            {"case_id": "c2", "actual": 1, "predicted": 0}]},
        "inspect_experiment": {"declarations": {
            "preregistered": True, "holdout_frozen": True, "baseline_present": False}},
    }
    return {"schema": REQUEST_SCHEMA, "request_id": "req-001",
            "capability": capability,
            "context": {"task_family": "TABULAR_CLASSIFICATION", "domain": "demo",
                        "dataset_version": "data-v1", "data_role": "SYNTHETIC"},
            "constraints": {"allow_network": False, "allow_mutation": False,
                            "max_cost_usd": 0},
            "payload": copy.deepcopy(payloads[capability])}


class ContractTests(unittest.TestCase):
    def assert_blocked(self, obj):
        with self.assertRaises(CapabilityContractError):
            MockCapabilityAdapter("mock-gpt").invoke(obj)

    def test_four_mock_providers_same_contract_and_output(self):
        adapters = make_mock_adapters()
        self.assertEqual(set(adapters), PROVIDERS)
        for capability in CAPABILITIES:
            outputs = []
            for provider, adapter in adapters.items():
                request = specimen(capability)
                result = adapter.invoke(request)
                self.assertEqual(result["provider_id"], provider)
                self.assertEqual(result["status"], "SIMULATED_ONLY")
                self.assertEqual(result["api_calls"], 0)
                self.assertEqual(result["cost_usd"], 0)
                self.assertFalse(result["state_changed"])
                self.assertFalse(result["approval_performed"])
                self.assertFalse(result["model_promoted"])
                self.assertFalse(result["production_ready"])
                validate_mock_result(request, result, expected_provider_id=provider)
                outputs.append(result["output"])
            self.assertEqual(outputs, [outputs[0]] * 4)

    def test_data_checks_missing_only(self):
        out = MockCapabilityAdapter("mock-claude").invoke(specimen())["output"]
        self.assertEqual(out, {"checked_records": 2, "missing_by_field": {"label": 1, "x": 0}})

    def test_error_detection(self):
        out = MockCapabilityAdapter("mock-gemini").invoke(specimen("analyze_errors"))["output"]
        self.assertEqual(out, {"checked_cases": 2, "error_case_ids": ["c2"]})

    def test_bool_int_labels_are_distinct(self):
        r = specimen("analyze_errors")
        r["payload"]["cases"] = [{"case_id": "c3", "actual": False, "predicted": 0}]
        self.assertEqual(MockCapabilityAdapter("mock-grok").invoke(r)["output"]["error_case_ids"], ["c3"])

    def test_experiment_is_metadata_only(self):
        out = MockCapabilityAdapter("mock-gpt").invoke(specimen("inspect_experiment"))["output"]
        self.assertEqual(out, {"declared_missing_or_false": ["baseline_present"], "declared_complete": False})

    def test_deterministic_digest_reordered_keys(self):
        request = specimen()
        result1 = MockCapabilityAdapter("mock-gpt").invoke(request)
        reversed_request = dict(reversed(list(request.items())))
        result2 = MockCapabilityAdapter("mock-gpt").invoke(reversed_request)
        self.assertEqual(result1, result2)

    def test_input_not_mutated(self):
        request = specimen(); before = copy.deepcopy(request)
        MockCapabilityAdapter("mock-gpt").invoke(request)
        self.assertEqual(request, before)

    def test_wrong_provider_rejected(self):
        with self.assertRaises(CapabilityContractError):
            MockCapabilityAdapter("gpt-live")
        with self.assertRaises(CapabilityContractError):
            MockCapabilityAdapter({"name": "mock-gpt"})

    def test_unknown_capability_rejected(self):
        req = specimen(); req["capability"] = "deploy_model"
        self.assert_blocked(req)

    def test_network_and_mutation_denied(self):
        for key in ("allow_network", "allow_mutation"):
            req = specimen(); req["constraints"][key] = True
            self.assert_blocked(req)

    def test_spending_denied(self):
        for value in (1, 0.0, True):
            req = specimen(); req["constraints"]["max_cost_usd"] = value
            self.assert_blocked(req)

    def test_holdout_and_unrecognized_roles_denied(self):
        for role in ("HOLDOUT", "PRODUCTION", ["SYNTHETIC"], None):
            req = specimen(); req["context"]["data_role"] = role
            self.assert_blocked(req)

    def test_unknown_fields_and_missing_constraints_fail_closed(self):
        req = specimen(); req["force_deploy"] = True
        self.assert_blocked(req)
        req = specimen(); del req["constraints"]["allow_mutation"]
        self.assert_blocked(req)

    def test_invalid_schema_version(self):
        req = specimen(); req["schema"] = "umlf-capability-request/v2"
        self.assert_blocked(req)

    def test_duplicate_data_fields(self):
        req = specimen(); req["payload"]["required_fields"] = ["x", "x"]
        self.assert_blocked(req)

    def test_invalid_records(self):
        req = specimen(); req["payload"]["records"] = [None]
        self.assert_blocked(req)

    def test_duplicate_error_case_ids(self):
        req = specimen("analyze_errors")
        req["payload"]["cases"].append(copy.deepcopy(req["payload"]["cases"][0]))
        self.assert_blocked(req)

    def test_invalid_labels(self):
        req = specimen("analyze_errors"); req["payload"]["cases"][0]["actual"] = None
        self.assert_blocked(req)

    def test_experiment_declarations_bool_not_int(self):
        req = specimen("inspect_experiment"); req["payload"]["declarations"]["preregistered"] = 1
        self.assert_blocked(req)

    def test_nonfinite_and_unserializable_blocked(self):
        for bad in (float("nan"), {1, 2}):
            req = specimen(); req["payload"]["records"][0]["x"] = bad
            self.assert_blocked(req)

    def test_packet_size_cap(self):
        req = specimen(); req["payload"]["records"][0]["long"] = "x" * 20000
        self.assert_blocked(req)

    def test_packet_depth_cap(self):
        req = specimen(); nested = {}; cursor = nested
        for i in range(12):
            cursor["child"] = {}; cursor = cursor["child"]
        req["payload"]["records"][0]["deep"] = nested
        self.assert_blocked(req)

    def test_tamper_request_hash_is_detected(self):
        req = specimen(); result = MockCapabilityAdapter("mock-gpt").invoke(req)
        result["request_sha256"] = "a" * 64
        with self.assertRaises(CapabilityContractError):
            validate_mock_result(req, result, expected_provider_id="mock-gpt")

    def test_tamper_output_is_detected(self):
        req = specimen(); result = MockCapabilityAdapter("mock-gpt").invoke(req)
        result["output"]["checked_records"] = 99
        with self.assertRaises(CapabilityContractError):
            validate_mock_result(req, result, expected_provider_id="mock-gpt")

    def test_cannot_forge_approval_or_network_calls(self):
        req = specimen(); before = MockCapabilityAdapter("mock-gpt").invoke(req)
        for key, bad in (("approval_performed", True), ("production_ready", True),
                         ("model_promoted", True), ("state_changed", True),
                         ("api_calls", 1), ("cost_usd", 1)):
            result = copy.deepcopy(before); result[key] = bad
            with self.subTest(key=key), self.assertRaises(CapabilityContractError):
                validate_mock_result(req, result, expected_provider_id="mock-gpt")

    def test_provider_relabeling_requires_trusted_call_context(self):
        req = specimen()
        result = MockCapabilityAdapter("mock-claude").invoke(req)
        result["provider_id"] = "mock-gpt"
        with self.assertRaises(CapabilityContractError):
            validate_mock_result(req, result, expected_provider_id="mock-claude")

    def test_missing_or_invalid_provider_context_fails_closed(self):
        req = specimen()
        result = MockCapabilityAdapter("mock-gpt").invoke(req)
        with self.assertRaises(TypeError):
            validate_mock_result(req, result)
        for provider_id in (None, "gpt", ["mock-gpt"], True):
            with self.subTest(provider_id=provider_id), self.assertRaises(CapabilityContractError):
                validate_mock_result(req, result, expected_provider_id=provider_id)

    def test_schema_declares_exact_contract_versions(self):
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        request = schema["$defs"]["request"]
        result = schema["$defs"]["result"]
        self.assertEqual(request["properties"]["schema"]["const"], REQUEST_SCHEMA)
        self.assertEqual(result["properties"]["schema"]["const"], RESULT_SCHEMA)
        self.assertEqual(set(request["properties"]["capability"]["enum"]), CAPABILITIES)
        self.assertEqual(set(result["properties"]["provider_id"]["enum"]), PROVIDERS)
        self.assertFalse(request["additionalProperties"])
        self.assertFalse(result["additionalProperties"])

    def test_no_network_or_provider_imports_in_mock_core(self):
        tree = ast.parse(inspect.getsource(core))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name.partition(".")[0] for alias in node.names)
            if isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module.partition(".")[0])
        self.assertEqual(set(imports) - {"__future__", "hashlib", "json", "math", "re", "dataclasses", "typing"}, set())


if __name__ == "__main__":
    unittest.main()
