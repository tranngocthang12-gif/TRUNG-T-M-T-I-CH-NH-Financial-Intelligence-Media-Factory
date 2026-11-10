"""Negative controls for proposed provider routing; no real inference or API calls."""
import copy
import unittest
from capability_contracts.evidence_router import (
    SCHEMA, RouterContractError, _digest, inspect_router,
)

def fixture():
    packet = {
        "schema": SCHEMA, "frozen": True, "mode": "SYNTHETIC_ONLY",
        "task_family": "TABULAR_CLASSIFICATION", "dataset_version": "synthetic-v1",
        "evaluator_sha256": "a" * 64, "case_set_sha256": "b" * 64,
        "case_count": 20, "min_accuracy": 0.7,
        "max_critical_error_rate": 0.25, "max_latency_ms": 100,
        "max_cost_usd": 0, "min_coverage": 1.0,
    }
    def receipt(name, accuracy, latency):
        return {
            "provider_id": name, "packet_sha256": _digest(packet),
            "evaluator_sha256": packet["evaluator_sha256"],
            "case_set_sha256": packet["case_set_sha256"],
            "evaluated_case_count": 20, "accuracy": accuracy,
            "critical_error_rate": 0.0, "latency_ms": latency, "cost_usd": 0,
            "integrity_failures": {x: 0 for x in
                                   ("leakage", "security", "authority", "reproducibility", "data_contract")},
            "status": "SIMULATED_BENCHMARK", "evidence_mode": "SYNTHETIC_ONLY",
        }
    return packet, [
        receipt("mock-claude", .9, 50),
        receipt("mock-gemini", .8, 20),
        receipt("mock-grok", .8, 30),
        receipt("mock-gpt", .6, 10),
    ]

def run(p, r, pin=None):
    return inspect_router(p, r, trusted_packet_sha256=_digest(p) if pin is None else pin)

class RouterTests(unittest.TestCase):
    def test_selects_only_eligible_cheapest_fastest(self):
        p, r = fixture()
        x = run(p, r)
        self.assertEqual(x["status"], "SYNTHETIC_PROPOSAL_ONLY")
        self.assertEqual(x["proposed_provider_id"], "mock-gemini")
        self.assertEqual(x["eligible_provider_ids"], ["mock-gemini", "mock-grok", "mock-claude"])
        self.assertEqual(x["rejected"][0]["provider_id"], "mock-gpt")
        for k in ("api_called", "state_changed", "model_promoted", "deployment_approved",
                  "production_ready", "provider_identity_authenticated",
                  "benchmark_provenance_authenticated", "causal_improvement_proven"):
            self.assertFalse(x[k])
        self.assertTrue(x["external_review_required"])

    def test_no_candidate_fails_closed(self):
        p, r = fixture()
        p["min_accuracy"] = .99
        for item in r: item["packet_sha256"] = _digest(p)
        x = run(p, r)
        self.assertIsNone(x["proposed_provider_id"])
        self.assertEqual(x["status"], "NO_ELIGIBLE_CANDIDATE")

    def test_guardrail_excludes_high_accuracy(self):
        p, r = fixture()
        r[0]["critical_error_rate"] = .5
        x = run(p, r)
        self.assertEqual(x["proposed_provider_id"], "mock-gemini")
        self.assertIn("CRITICAL_ERROR_GUARDRAIL", x["rejected"][0]["reasons"])

    def test_latency_rejects(self):
        p, r = fixture()
        r[1]["latency_ms"] = 101
        self.assertEqual(run(p, r)["proposed_provider_id"], "mock-grok")

    def test_real_paid_cost_never_approved(self):
        p, r = fixture()
        r[1]["cost_usd"] = .01
        self.assertEqual(run(p, r)["proposed_provider_id"], "mock-grok")

    def test_integrity_failure_blocks(self):
        p, r = fixture()
        r[1]["integrity_failures"]["leakage"] = 1
        self.assertEqual(run(p, r)["proposed_provider_id"], "mock-grok")

    def test_frozen_packet_tamper_denied(self):
        p, r = fixture()
        original = _digest(p)
        p["max_latency_ms"] = 200
        with self.assertRaisesRegex(RouterContractError, "SHA"):
            run(p, r, original)

    def test_wrong_case_and_evaluator_digest_denied(self):
        for field in ("case_set_sha256", "evaluator_sha256", "packet_sha256"):
            p, r = fixture()
            r[0][field] = "c" * 64
            with self.subTest(field=field), self.assertRaisesRegex(RouterContractError, "bound"):
                run(p, r)

    def test_incomplete_benchmark_denied(self):
        p, r = fixture()
        r[0]["evaluated_case_count"] = 19
        with self.assertRaisesRegex(RouterContractError, "bound"):
            run(p, r)

    def test_duplicate_provider_denied(self):
        p, r = fixture()
        r[1]["provider_id"] = "mock-claude"
        with self.assertRaisesRegex(RouterContractError, "repeated"):
            run(p, r)

    def test_fake_or_real_provider_denied(self):
        p, r = fixture()
        r[0]["provider_id"] = "claude-opus-real"
        with self.assertRaises(RouterContractError): run(p, r)

    def test_bad_numbers_denied(self):
        for field, value in (("accuracy", 1.1), ("accuracy", True), ("latency_ms", -1),
                             ("latency_ms", float("nan")), ("cost_usd", float("inf"))):
            p, r = fixture()
            r[0][field] = value
            with self.subTest(field=field, value=str(value)), self.assertRaises(RouterContractError):
                run(p, r)

    def test_integrity_boolean_and_unknown_field_denied(self):
        p, r = fixture()
        r[0]["integrity_failures"]["authority"] = True
        with self.assertRaises(RouterContractError): run(p, r)
        p, r = fixture()
        r[0]["approved"] = True
        with self.assertRaises(RouterContractError): run(p, r)

    def test_non_synthetic_packet_denied(self):
        p, r = fixture()
        p["mode"] = "PRODUCTION"
        with self.assertRaises(RouterContractError): run(p, r)

    def test_bad_threshold_denied(self):
        p, r = fixture()
        p["min_accuracy"] = float("nan")
        with self.assertRaises(RouterContractError): run(p, r, "a"*64)

    def test_partial_coverage_policy_is_not_a_supported_v1_claim(self):
        p, receipts = fixture()
        p["min_coverage"] = 0.5
        with self.assertRaisesRegex(RouterContractError, "complete coverage"):
            run(p, receipts)

    def test_stable_under_input_reordering(self):
        p, r = fixture()
        self.assertEqual(run(p, r), run(p, list(reversed(r))))

    def test_no_mutation(self):
        p, r = fixture()
        frozen = copy.deepcopy((p, r))
        run(p, r)
        self.assertEqual((p, r), frozen)

    def test_unpinned_policy_denied(self):
        p, r = fixture()
        with self.assertRaises(RouterContractError):
            inspect_router(p, r, trusted_packet_sha256="")

if __name__ == "__main__":
    unittest.main()
