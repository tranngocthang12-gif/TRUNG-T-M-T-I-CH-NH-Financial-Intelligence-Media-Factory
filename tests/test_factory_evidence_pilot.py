"""Synthetic-only positive, baseline, guardrail and negative-control tests."""
import copy
import unittest

from learning_governance import digest
from task_templates.tabular_classification.evidence_pilot import (
    SCHEMA, EvidencePilotError, freeze_synthetic_cases, inspect_synthetic_paired_trial,
)


def fixture():
    rows = [{"case_id": f"case-{i:02d}", "label": int(i >= 10),
             "critical": i in (0, 1, 10, 11)} for i in range(20)]
    packet = {
        "schema": SCHEMA,
        "frozen": True,
        "evidence_mode": "SYNTHETIC_ONLY",
        "task_family": "TABULAR_CLASSIFICATION",
        "dataset_version": "synthetic-pilot-v1",
        "cases_sha256": freeze_synthetic_cases(rows),
        "allowed_features": ["synthetic_signal"],
        "metric_specs": [
            {"name": "accuracy", "direction": "MAX", "role": "PRIMARY", "min_improvement": 0.1},
            {"name": "critical_error_rate", "direction": "MIN", "role": "GUARDRAIL", "min_improvement": 0},
        ],
    }
    zero_failures = {"leakage": 0, "security": 0, "reproducibility": 0, "authority": 0, "data_contract": 0}
    baseline = {"run_ref": "baseline-001", "features_used": [],
                "predictions": [{"case_id": row["case_id"], "predicted": 0} for row in rows],
                "critical_failures": zero_failures.copy()}
    challenger = copy.deepcopy(baseline)
    challenger["run_ref"] = "candidate-001"
    challenger["features_used"] = ["synthetic_signal"]
    for row in challenger["predictions"]:
        if row["case_id"] in {"case-10", "case-11", "case-12", "case-13", "case-14"}:
            row["predicted"] = 1
    return packet, rows, baseline, challenger


def evaluate(packet=None, cases=None, baseline=None, challenger=None, expected_sha=None):
    p, rows, b, c = fixture()
    p = p if packet is None else packet
    rows = rows if cases is None else cases
    b = b if baseline is None else baseline
    c = c if challenger is None else challenger
    return inspect_synthetic_paired_trial(p, rows, b, c,
                                          expected_packet_sha256=digest(p) if expected_sha is None else expected_sha)


class EvidencePilotTests(unittest.TestCase):
    def test_positive_paired_trial_structurally_eligible_only(self):
        r = evaluate()
        self.assertEqual(r["status"], "SYNTHETIC_REVIEW_ELIGIBLE")
        self.assertEqual(r["baseline_metrics"], {"accuracy": .5, "critical_error_rate": .5})
        self.assertEqual(r["challenger_metrics"], {"accuracy": .75, "critical_error_rate": 0.})
        self.assertEqual((r["paired_wins"], r["paired_losses"]), (5, 0))
        self.assertTrue(r["governance_verdict"]["candidate_eligible_for_external_review"])
        for k in ("source_authenticity_proven", "holdout_access_isolation_proven",
                  "integrity_declarations_authenticated", "real_world_improvement_proven",
                  "model_promoted", "production_ready", "state_changed"):
            self.assertFalse(r[k], k)
        self.assertTrue(r["external_review_required"])

    def test_control_no_improvement_is_rejected(self):
        p, rows, b, c = fixture()
        c["predictions"] = copy.deepcopy(b["predictions"])
        result = evaluate(p, rows, b, c)
        self.assertEqual(result["status"], "SYNTHETIC_NOT_ELIGIBLE")
        self.assertTrue(any("no primary metric" in reason for reason in result["governance_verdict"]["reasons"]))

    def test_shuffled_ground_truth_negative_control(self):
        p, rows, b, c = fixture()
        for row in rows:
            row["label"] = 1 - row["label"]
        p["cases_sha256"] = freeze_synthetic_cases(rows)
        result = evaluate(p, rows, b, c)
        self.assertEqual(result["status"], "SYNTHETIC_NOT_ELIGIBLE")
        self.assertLess(result["challenger_metrics"]["accuracy"], result["baseline_metrics"]["accuracy"])

    def test_guardrail_regression_blocks_accuracy_gain(self):
        p, rows, b, c = fixture()
        c["predictions"] = copy.deepcopy(b["predictions"])
        for entry in c["predictions"]:
            if entry["case_id"] in {"case-12", "case-13", "case-14", "case-15", "case-16",
                                     "case-00", "case-01"}:
                entry["predicted"] = 1
        result = evaluate(p, rows, b, c)
        self.assertEqual(result["status"], "SYNTHETIC_NOT_ELIGIBLE")
        self.assertGreater(result["challenger_metrics"]["accuracy"], result["baseline_metrics"]["accuracy"])
        self.assertGreater(result["challenger_metrics"]["critical_error_rate"], result["baseline_metrics"]["critical_error_rate"])

    def test_leaky_feature_cannot_buy_perfect_accuracy(self):
        p, rows, b, c = fixture()
        c["features_used"] = ["label"]
        c["predictions"] = [{"case_id": row["case_id"], "predicted": row["label"]} for row in rows]
        with self.assertRaisesRegex(EvidencePilotError, "feature"):
            evaluate(p, rows, b, c)

    def test_unregistered_metric_change_fails(self):
        p, rows, b, c = fixture()
        old_sha = digest(p)
        p["metric_specs"][0]["min_improvement"] = 0.0
        with self.assertRaisesRegex(EvidencePilotError, "pin"):
            evaluate(p, rows, b, c, expected_sha=old_sha)

    def test_tampering_ground_truth_fails(self):
        p, rows, b, c = fixture()
        rows[3]["label"] = 1
        with self.assertRaisesRegex(EvidencePilotError, "ground truth"):
            evaluate(p, rows, b, c)

    def test_case_order_does_not_change_frozen_digest(self):
        p, rows, b, c = fixture()
        self.assertEqual(freeze_synthetic_cases(rows), freeze_synthetic_cases(list(reversed(rows))))
        self.assertEqual(evaluate(p, list(reversed(rows)), b, c)["status"], "SYNTHETIC_REVIEW_ELIGIBLE")

    def test_partial_holdout_prediction_is_rejected(self):
        p, rows, b, c = fixture()
        c["predictions"].pop()
        with self.assertRaisesRegex(EvidencePilotError, "entire"):
            evaluate(p, rows, b, c)

    def test_duplicate_prediction_id_is_rejected(self):
        p, rows, b, c = fixture()
        c["predictions"][0] = copy.deepcopy(c["predictions"][1])
        with self.assertRaisesRegex(EvidencePilotError, "duplicate"):
            evaluate(p, rows, b, c)

    def test_unknown_case_id_is_rejected(self):
        p, rows, b, c = fixture()
        c["predictions"][0]["case_id"] = "outside-case"
        with self.assertRaisesRegex(EvidencePilotError, "differ"):
            evaluate(p, rows, b, c)

    def test_integrity_failure_declaration_blocks(self):
        p, rows, b, c = fixture()
        c["critical_failures"]["leakage"] = 1
        result = evaluate(p, rows, b, c)
        self.assertFalse(result["governance_verdict"]["candidate_eligible_for_external_review"])
        self.assertTrue(any("leakage" in msg for msg in result["governance_verdict"]["reasons"]))

    def test_invalid_integrity_counter_rejected(self):
        p, rows, b, c = fixture()
        c["critical_failures"]["leakage"] = False
        with self.assertRaises(EvidencePilotError):
            evaluate(p, rows, b, c)

    def test_unregistered_packet_pin_mandatory(self):
        p, rows, b, c = fixture()
        with self.assertRaises(EvidencePilotError):
            evaluate(p, rows, b, c, expected_sha="0" * 64)

    def test_non_synthetic_mode_rejected(self):
        p, rows, b, c = fixture()
        p["evidence_mode"] = "PRODUCTION"
        with self.assertRaises(EvidencePilotError):
            evaluate(p, rows, b, c)

    def test_duplicated_frozen_case_id_rejected(self):
        p, rows, b, c = fixture()
        rows.append(copy.deepcopy(rows[-1]))
        with self.assertRaises(EvidencePilotError):
            evaluate(p, rows, b, c)

    def test_boolean_label_and_nan_metric_threshold_rejected(self):
        p, rows, b, c = fixture()
        rows[0]["label"] = True
        with self.assertRaises(EvidencePilotError):
            evaluate(p, rows, b, c)
        p, rows, b, c = fixture()
        p["metric_specs"][0]["min_improvement"] = float("nan")
        with self.assertRaises(EvidencePilotError):
            evaluate(p, rows, b, c, expected_sha="a" * 64)

    def test_unexpected_posthoc_metric_claim_rejected(self):
        p, rows, b, c = fixture()
        c["claimed_accuracy"] = 1.0
        with self.assertRaises(EvidencePilotError):
            evaluate(p, rows, b, c)

    def test_nonindependent_duplicate_run_ref_rejected(self):
        p, rows, b, c = fixture()
        c["run_ref"] = b["run_ref"]
        with self.assertRaisesRegex(EvidencePilotError, "separate"):
            evaluate(p, rows, b, c)

    def test_change_of_pre_registered_metric_semantics_rejected(self):
        p, rows, b, c = fixture()
        p["metric_specs"][0]["role"] = "GUARDRAIL"
        with self.assertRaises(EvidencePilotError):
            evaluate(p, rows, b, c)

    def test_fixture_not_modified(self):
        p, rows, b, c = fixture()
        originals = copy.deepcopy((p, rows, b, c))
        a = evaluate(p, rows, b, c)
        self.assertEqual((p, rows, b, c), originals)
        self.assertEqual(evaluate(p, rows, b, c), a)


if __name__ == "__main__":
    unittest.main()
