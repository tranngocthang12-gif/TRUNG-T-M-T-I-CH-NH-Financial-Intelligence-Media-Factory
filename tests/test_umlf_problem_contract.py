"""Q03 adversarial tests: no authority follows from structural correctness."""
import copy
import unittest

from problem_contract import ProblemContractError, problem_receipt, validate_problem


def valid():
    return {
        "schema": "umlf-problem/v1",
        "problem": {"task_family": "TABULAR_CLASSIFICATION", "domain": "synthetic_demo",
                    "objective": "Predict label from training-only features"},
        "data": {"dataset_id": "demo-001", "version": "v1",
                 "snapshot_sha256": "a" * 64, "source_locator": "fixture://demo"},
        "target": {"name": "label", "kind": "BINARY"},
        "metrics": {"primary": "balanced_accuracy", "direction": "MAXIMIZE",
                    "baseline": "majority_training_label"},
        "constraints": {"privacy_level": "PUBLIC_SYNTHETIC", "max_compute_seconds": 60},
        "deployment": {"mode": "OFFLINE_ONLY", "owner_gate": True},
        "retraining": {"mode": "PROPOSAL_ONLY", "owner_gate": True},
    }


class ProblemContractTests(unittest.TestCase):
    def test_deterministic_receipt_for_reordered_keys(self):
        p = valid()
        receipt = problem_receipt(p)
        reordered = dict(reversed(list(p.items())))
        self.assertEqual(receipt, problem_receipt(reordered))
        self.assertEqual(receipt["validation"], "STRUCTURAL_ONLY")
        self.assertEqual(receipt["dataset_snapshot_sha256"], "a" * 64)
        for gate in ("training_authorized", "deployment_authorized",
                     "retraining_authorized", "external_review_proven",
                     "owner_approval_proven"):
            self.assertFalse(receipt[gate])

    def test_receipt_changes_if_relevant_spec_changes(self):
        p = valid()
        old = problem_receipt(p)["contract_sha256"]
        p["metrics"]["primary"] = "f1"
        self.assertNotEqual(old, problem_receipt(p)["contract_sha256"])

    def test_no_mutation_of_caller(self):
        p = valid()
        before = copy.deepcopy(p)
        normalized = validate_problem(p)
        normalized["problem"]["domain"] = "other_domain"
        self.assertEqual(p, before)

    def test_missing_or_extra_top_level_fails(self):
        p = valid()
        del p["retraining"]
        with self.assertRaises(ProblemContractError):
            validate_problem(p)
        p = valid()
        p["auto_promote"] = True
        with self.assertRaises(ProblemContractError):
            validate_problem(p)

    def test_wildcard_scope_rejected(self):
        for field in ("task_family", "domain"):
            p = valid()
            p["problem"][field] = "*"
            with self.subTest(field=field), self.assertRaises(ProblemContractError):
                problem_receipt(p)

    def test_malformed_or_ambiguous_scope_rejected(self):
        for bad in ("", " finance", "finance ", None, "finance*"):
            p = valid()
            p["problem"]["domain"] = bad
            if bad == "finance*":
                with self.assertRaises(ProblemContractError):
                    problem_receipt(p)
            else:
                with self.assertRaises(ProblemContractError):
                    problem_receipt(p)

    def test_missing_data_snapshot_and_uncanonical_digest_rejected(self):
        for bad in ("", "f" * 63, "G" * 64, None):
            p = valid()
            p["data"]["snapshot_sha256"] = bad
            with self.assertRaises(ProblemContractError):
                problem_receipt(p)

    def test_missing_data_source_and_version_rejected(self):
        for key in ("dataset_id", "version", "source_locator"):
            p = valid()
            p["data"][key] = ""
            with self.subTest(key=key), self.assertRaises(ProblemContractError):
                problem_receipt(p)

    def test_data_extra_authority_rejected(self):
        p = valid()
        p["data"]["download_and_cache"] = True
        with self.assertRaises(ProblemContractError):
            problem_receipt(p)

    def test_metric_direction_rejected(self):
        p = valid()
        p["metrics"]["direction"] = "LOWER"
        with self.assertRaises(ProblemContractError):
            problem_receipt(p)

    def test_missing_baseline_rejected(self):
        p = valid()
        p["metrics"]["baseline"] = None
        with self.assertRaises(ProblemContractError):
            problem_receipt(p)

    def test_unbounded_or_noninteger_cost_rejected(self):
        for value in (-1, 0, True, 1.5, 86401):
            p = valid()
            p["constraints"]["max_compute_seconds"] = value
            with self.subTest(value=value), self.assertRaises(ProblemContractError):
                problem_receipt(p)

    def test_nan_or_non_json_object_rejected(self):
        for value in (float("nan"), object()):
            p = valid()
            p["problem"]["objective"] = value
            with self.subTest(value=repr(value)), self.assertRaises(ProblemContractError):
                problem_receipt(p)

    def test_deployment_must_remain_offline(self):
        for mode in ("PRODUCTION", "CANARY", "AUTO", "*", None):
            p = valid()
            p["deployment"]["mode"] = mode
            with self.subTest(mode=mode), self.assertRaises(ProblemContractError):
                problem_receipt(p)

    def test_cannot_disable_owner_gate(self):
        for key in ("deployment", "retraining"):
            p = valid()
            p[key]["owner_gate"] = False
            with self.subTest(key=key), self.assertRaises(ProblemContractError):
                problem_receipt(p)

    def test_retraining_cannot_be_automatic(self):
        p = valid()
        p["retraining"]["mode"] = "AUTO_ON_NEW_DATA"
        with self.assertRaises(ProblemContractError):
            problem_receipt(p)

    def test_unknown_schema_is_not_upgraded_silently(self):
        p = valid()
        p["schema"] = "umlf-problem/v2"
        with self.assertRaises(ProblemContractError):
            problem_receipt(p)


if __name__ == "__main__":
    unittest.main()
