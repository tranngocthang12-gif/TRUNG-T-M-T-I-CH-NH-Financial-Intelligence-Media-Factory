"""End-to-end A->B->C negative controls; deterministic and offline."""
import copy
import unittest
from capability_contracts.evidence_router import SCHEMA as ROUTER_SCHEMA, _digest
from task_templates.tabular_classification.evidence_pilot import SCHEMA as EVAL_SCHEMA, freeze_synthetic_cases
from learning_governance import digest
from factory_review.evidence_bridge import BridgeContractError, inspect_synthetic_chain


def fixture():
    cases = [{"case_id": f"case-{i:02d}", "label": 0 if i < 10 else 1,
              "critical": i in (0, 1, 10, 11)} for i in range(20)]
    packet = {
        "schema": EVAL_SCHEMA, "frozen": True, "evidence_mode": "SYNTHETIC_ONLY",
        "task_family": "TABULAR_CLASSIFICATION", "dataset_version": "synthetic-bridge-v1",
        "cases_sha256": freeze_synthetic_cases(cases), "allowed_features": ["signal"],
        "metric_specs": [
            {"name": "accuracy", "direction": "MAX", "role": "PRIMARY", "min_improvement": 0.1},
            {"name": "critical_error_rate", "direction": "MIN", "role": "GUARDRAIL", "min_improvement": 0},
        ],
    }
    failures = {key: 0 for key in ("leakage", "security", "reproducibility", "authority", "data_contract")}
    baseline = {
        "run_ref": "baseline-bridge-v1", "features_used": [],
        "predictions": [{"case_id": x["case_id"], "predicted": 0} for x in cases],
        "critical_failures": failures.copy(),
    }
    challenger = copy.deepcopy(baseline)
    challenger["run_ref"] = "challenger-bridge-v1"
    challenger["features_used"] = ["signal"]
    for row in challenger["predictions"]:
        if row["case_id"] in {"case-10", "case-11", "case-12", "case-13", "case-14"}:
            row["predicted"] = 1
    request = {
        "schema": "umlf-capability-request/v1", "request_id": "request-bridge-v1",
        "capability": "analyze_errors",
        "context": {"task_family": "TABULAR_CLASSIFICATION", "domain": "synthetic",
                    "dataset_version": "synthetic-bridge-v1", "data_role": "SYNTHETIC"},
        "constraints": {"allow_network": False, "allow_mutation": False, "max_cost_usd": 0},
        "payload": {"cases": [{"case_id": x["case_id"], "actual": x["label"],
                               "predicted": 0} for x in cases]},
    }
    router = {
        "schema": ROUTER_SCHEMA, "frozen": True, "mode": "SYNTHETIC_ONLY",
        "task_family": "TABULAR_CLASSIFICATION", "dataset_version": "synthetic-bridge-v1",
        "evaluator_sha256": digest({"evaluation_schema": EVAL_SCHEMA, "version": "v1"}),
        "case_set_sha256": freeze_synthetic_cases(cases), "case_count": 20,
        "min_accuracy": .7, "max_critical_error_rate": .25,
        "max_latency_ms": 100, "max_cost_usd": 0, "min_coverage": 1.0,
    }
    return request, cases, baseline, challenger, packet, router


def inspect(f=None, **kwargs):
    vals = fixture() if f is None else f
    req, cases, base, chal, evaluation_packet, router = vals
    return inspect_synthetic_chain(
        req, cases, base, chal, evaluation_packet, router,
        expected_evaluation_sha256=kwargs.get("evaluation_pin", digest(evaluation_packet)),
        expected_router_sha256=kwargs.get("router_pin", _digest(router)),
        expected_provider_id=kwargs.get("provider", "mock-gpt"))


class IntegratedFactoryReviewTests(unittest.TestCase):
    def test_valid_synthetic_flow_is_proposal_only(self):
        x = inspect()
        self.assertEqual(x["status"], "SYNTHETIC_CHAIN_PROPOSAL_ONLY")
        self.assertEqual(x["mock_receipt"]["provider_id"], "mock-gpt")
        self.assertEqual(x["mock_receipt"]["status"], "SIMULATED_ONLY")
        self.assertEqual(x["evaluation"]["challenger_metrics"]["accuracy"], .75)
        self.assertEqual(x["router_result"]["proposed_provider_id"], "mock-gpt")
        self.assertFalse(x["api_called"])
        self.assertFalse(x["provider_authenticity_proven"])
        self.assertFalse(x["benchmark_provenance_authenticated"])
        self.assertFalse(x["deployment_approved"])
        self.assertTrue(x["external_review_required"])

    def test_all_four_mock_labels_supported_but_no_real_provider(self):
        for provider in ("mock-gpt", "mock-claude", "mock-gemini", "mock-grok"):
            with self.subTest(provider=provider):
                x = inspect(provider=provider)
                self.assertEqual(x["router_result"]["proposed_provider_id"], provider)

    def test_no_performance_gain_blocks_router(self):
        f = fixture()
        f[3]["predictions"] = copy.deepcopy(f[2]["predictions"])
        x = inspect(f)
        self.assertEqual(x["status"], "BLOCKED_BY_EVALUATION")
        self.assertIsNone(x["router_result"])

    def test_bad_integrity_counter_blocks_router(self):
        f = fixture(); f[3]["critical_failures"]["leakage"] = 1
        self.assertEqual(inspect(f)["status"], "BLOCKED_BY_EVALUATION")

    def test_bad_mock_payload_cannot_bridge(self):
        f = fixture(); f[0]["payload"]["cases"][10]["actual"] = 0
        with self.assertRaises(BridgeContractError): inspect(f)

    def test_wrong_provider_context_fails_closed(self):
        with self.assertRaises(BridgeContractError): inspect(provider="real-claude")

    def test_ground_truth_tampering_rejected(self):
        f = fixture(); f[1][0]["label"] = 1
        with self.assertRaises(BridgeContractError): inspect(f)

    def test_evaluation_pin_mismatch_rejected(self):
        with self.assertRaises(BridgeContractError):
            inspect(evaluation_pin="f"*64)

    def test_router_pin_mismatch_rejected(self):
        with self.assertRaises(BridgeContractError):
            inspect(router_pin="e"*64)

    def test_router_case_set_mismatch_rejected(self):
        f = fixture(); f[5]["case_set_sha256"] = "c"*64
        with self.assertRaises(BridgeContractError): inspect(f)

    def test_router_quality_guardrail_blocks(self):
        f = fixture(); f[5]["min_accuracy"] = .99
        self.assertEqual(inspect(f)["status"], "ROUTER_REJECTED")

    def test_no_side_effect_on_input(self):
        f=fixture(); frozen=copy.deepcopy(f)
        inspect(f)
        self.assertEqual(f,frozen)

    def test_no_network_or_spending(self):
        f=fixture(); f[0]["constraints"]["allow_network"] = True
        with self.assertRaises(BridgeContractError): inspect(f)
        f=fixture(); f[0]["constraints"]["max_cost_usd"] = 1
        with self.assertRaises(BridgeContractError): inspect(f)


if __name__ == "__main__":
    unittest.main()
