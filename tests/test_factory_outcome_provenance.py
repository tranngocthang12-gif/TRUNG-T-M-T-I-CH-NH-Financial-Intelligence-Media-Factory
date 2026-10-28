"""Synthetic-only negative and positive tests for prospective outcome receipts."""
from __future__ import annotations

import copy
import hashlib
import unittest

from learning_governance.outcome_provenance import inspect_prospective_outcome

RAW = b"synthetic raw label source; no real data"
SHA = hashlib.sha256(RAW).hexdigest()


def specimen() -> dict:
    return {
        "schema": "umlf-prospective-outcome/v1", "mode": "PROSPECTIVE",
        "task_family": "TIME_SERIES_FORECASTING", "dataset_version": "synthetic-v1",
        "source_locator": "fixture://future-actual-v1",
        "prediction_actor_id": "model-batch-a", "resolver_actor_id": "blind-label-seat-b",
        "frozen_evaluation_packet_sha256": "a" * 64,
        "frozen_extraction_rule_sha256": "b" * 64,
        "prediction_artifact_sha256": "c" * 64,
        "raw_outcome_snapshot_sha256": SHA,
        "evaluation_packet_frozen_at": "2026-10-01T00:00:00Z",
        "prediction_frozen_at": "2026-10-02T00:00:00+00:00",
        "outcome_first_available_at": "2026-10-03T00:00:00Z",
        "raw_outcome_captured_at": "2026-10-03T01:00:00Z",
        "blind_label_extracted_at": "2026-10-03T01:30:00Z",
        "outcome_source_kind": "RAW_SOURCE_SNAPSHOT",
        "outcome_source_transform": "NONE",
        "resolver_input_contract": "FROZEN_RULE_PLUS_RAW_SOURCE_ONLY",
        "resolver_saw_prediction": False,
        "resolver_saw_model_trace": False,
        "resolver_saw_prior_resolution": False,
    }


class ProspectiveOutcomeContractTests(unittest.TestCase):
    def check(self, record=None, raw=RAW):
        return inspect_prospective_outcome(specimen() if record is None else record,
                                           raw_outcome_bytes=raw)

    def test_valid_structure_not_independent_proof(self):
        result = self.check()
        self.assertEqual(result["status"], "STRUCTURALLY_ELIGIBLE_FOR_REVIEW")
        self.assertTrue(result["external_review_required"])
        self.assertFalse(result["reviewer_independence_proven"])
        self.assertFalse(result["production_ready"])

    def test_raw_bytes_mismatch(self):
        self.assertIn("digest mismatch", " ".join(self.check(raw=b"tamper")["reasons"]))

    def test_raw_source_missing(self):
        self.assertEqual(self.check(raw=None)["status"], "BLOCKED")

    def test_outcome_known_before_prediction(self):
        r = specimen(); r["prediction_frozen_at"] = "2026-10-04T00:00:00Z"
        self.assertEqual(self.check(r)["status"], "BLOCKED")

    def test_outcome_captured_before_available(self):
        r = specimen(); r["raw_outcome_captured_at"] = "2026-10-02T00:00:00Z"
        self.assertEqual(self.check(r)["status"], "BLOCKED")

    def test_extraction_before_raw_capture(self):
        r = specimen(); r["blind_label_extracted_at"] = "2026-10-02T00:00:00Z"
        self.assertEqual(self.check(r)["status"], "BLOCKED")

    def test_evaluator_frozen_after_prediction(self):
        r = specimen(); r["evaluation_packet_frozen_at"] = "2026-10-02T00:00:01Z"
        self.assertEqual(self.check(r)["status"], "BLOCKED")

    def test_naive_timestamp_rejected(self):
        r = specimen(); r["prediction_frozen_at"] = "2026-10-02T00:00:00"
        self.assertEqual(self.check(r)["status"], "BLOCKED")

    def test_same_actor_different_case_rejected(self):
        r = specimen(); r["resolver_actor_id"] = " MODEL-BATCH-A "
        self.assertEqual(self.check(r)["status"], "BLOCKED")

    def test_blind_resolver_exposed_to_prediction(self):
        r = specimen(); r["resolver_saw_prediction"] = True
        self.assertEqual(self.check(r)["status"], "BLOCKED")

    def test_blind_resolver_exposed_to_prior_resolution(self):
        r = specimen(); r["resolver_saw_prior_resolution"] = 0
        self.assertEqual(self.check(r)["status"], "BLOCKED")

    def test_not_historical_offline_holdout_gate(self):
        r = specimen(); r["mode"] = "HISTORICAL"
        self.assertEqual(self.check(r)["status"], "BLOCKED")

    def test_model_summary_not_raw_source(self):
        r = specimen(); r["outcome_source_kind"] = "MODEL_SUMMARY"
        self.assertEqual(self.check(r)["status"], "BLOCKED")

    def test_source_transformation_not_allowed(self):
        r = specimen(); r["outcome_source_transform"] = "UNFROZEN_CLEANUP"
        self.assertEqual(self.check(r)["status"], "BLOCKED")

    def test_invalid_hash_and_missing_field(self):
        r = specimen(); r["prediction_artifact_sha256"] = "invalid"
        r.pop("frozen_extraction_rule_sha256")
        self.assertEqual(self.check(r)["status"], "BLOCKED")

    def test_readonly_does_not_mutate_receipt(self):
        r = specimen(); before = copy.deepcopy(r)
        self.check(r)
        self.assertEqual(r, before)


if __name__ == "__main__":
    unittest.main()
