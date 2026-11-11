"""Adversarial tests for read-only Q04 structural snapshot validation."""
import copy
import hashlib
import json
import unittest

from data_contract import DataContractError, validate_snapshot


def canonical_hash(rows):
    raw = json.dumps(rows, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def sample():
    rows = [
        {"row_id": "r1", "entity_id": "e1",
         "event_at": "2026-01-01T09:00:00Z",
         "decision_at": "2026-01-01T10:00:00Z",
         "features": {
             "signal": {"value": 1.0, "observed_at": "2026-01-01T09:30:00Z",
                        "missing_reason": None},
             "optional": {"value": None, "observed_at": None,
                          "missing_reason": "NOT_OBSERVED"}},
         "target": {"value": True, "observed_at": "2026-01-02T10:00:00Z",
                    "missing_reason": None}},
        {"row_id": "r2", "entity_id": "e2",
         "event_at": "2026-01-01T09:00:00Z",
         "decision_at": "2026-01-01T10:00:00Z",
         "features": {
             "signal": {"value": 0.0, "observed_at": "2026-01-01T09:40:00Z",
                        "missing_reason": None},
             "optional": {"value": "available", "observed_at": "2026-01-01T09:55:00Z",
                          "missing_reason": None}},
         "target": {"value": False, "observed_at": "2026-01-02T11:00:00Z",
                    "missing_reason": None}},
    ]
    contract = {
        "schema": "umlf-data/v1",
        "scope": {"task_family": "TABULAR_CLASSIFICATION", "domain": "demo"},
        "dataset": {"id": "fixture-001", "version": "v1"},
        "columns": {"target": "label", "features": ["signal", "optional"]},
        "source": {"locator": "fixture://synthetic", "rights_declaration": "OWNER_DECLARED",
                   "rights_ref": "fixture-rights-declaration"},
        "snapshot": {"frozen_at": "2026-01-03T00:00:00Z", "rows_sha256": canonical_hash(rows),
                     "row_count": len(rows)},
    }
    return contract, rows


def reseal(contract, rows):
    contract["snapshot"]["rows_sha256"] = canonical_hash(rows)
    contract["snapshot"]["row_count"] = len(rows)


class DataContractTests(unittest.TestCase):
    def test_valid_snapshot_has_no_runtime_authority(self):
        c, rows = sample()
        receipt = validate_snapshot(c, rows)
        self.assertEqual(receipt["row_count"], 2)
        self.assertEqual(receipt["rows_sha256"], c["snapshot"]["rows_sha256"])
        self.assertEqual(receipt["validation"], "STRUCTURAL_ONLY")
        for field in ("source_rights_verified", "source_authenticity_proven",
                      "availability_metadata_authenticated", "semantic_leakage_excluded",
                      "training_authorized", "deployment_authorized",
                      "retraining_authorized", "owner_approval_proven"):
            self.assertFalse(receipt[field])

    def test_reproducible_and_does_not_mutate(self):
        c, rows = sample()
        original = copy.deepcopy((c, rows))
        self.assertEqual(validate_snapshot(c, rows), validate_snapshot(c, rows))
        self.assertEqual((c, rows), original)

    def test_tampered_row_without_reseal_is_rejected(self):
        c, rows = sample()
        rows[0]["features"]["signal"]["value"] = 999
        with self.assertRaisesRegex(DataContractError, "hash mismatch"):
            validate_snapshot(c, rows)

    def test_valid_reseal_changes_receipt(self):
        c, rows = sample()
        first = validate_snapshot(c, rows)
        rows[0]["features"]["signal"]["value"] = 2
        reseal(c, rows)
        second = validate_snapshot(c, rows)
        self.assertNotEqual(first["rows_sha256"], second["rows_sha256"])

    def test_duplicate_row_id_rejected_even_with_hash_and_count_resealed(self):
        c, rows = sample()
        rows[1]["row_id"] = "r1"
        reseal(c, rows)
        with self.assertRaisesRegex(DataContractError, "duplicate"):
            validate_snapshot(c, rows)

    def test_duplicate_entity_event_rejected(self):
        c, rows = sample()
        rows[1]["entity_id"] = "e1"
        reseal(c, rows)
        with self.assertRaisesRegex(DataContractError, "duplicate"):
            validate_snapshot(c, rows)

    def test_same_entity_different_event_accepted(self):
        c, rows = sample()
        rows[1]["entity_id"] = "e1"
        rows[1]["event_at"] = "2026-01-01T09:01:00Z"
        reseal(c, rows)
        self.assertEqual(validate_snapshot(c, rows)["row_count"], 2)

    def test_feature_observed_after_decision_rejected_even_resealed(self):
        c, rows = sample()
        rows[0]["features"]["signal"]["observed_at"] = "2026-01-01T10:00:01Z"
        reseal(c, rows)
        with self.assertRaisesRegex(DataContractError, "not available at decision"):
            validate_snapshot(c, rows)

    def test_feature_observed_at_decision_accepted(self):
        c, rows = sample()
        rows[0]["features"]["signal"]["observed_at"] = rows[0]["decision_at"]
        reseal(c, rows)
        self.assertEqual(validate_snapshot(c, rows)["row_count"], 2)

    def test_target_after_decision_allowed_but_before_freeze(self):
        c, rows = sample()
        self.assertEqual(validate_snapshot(c, rows)["validation"], "STRUCTURAL_ONLY")

    def test_target_observed_after_frozen_snapshot_rejected(self):
        c, rows = sample()
        rows[0]["target"]["observed_at"] = "2026-01-04T00:00:00Z"
        reseal(c, rows)
        with self.assertRaisesRegex(DataContractError, "after frozen snapshot"):
            validate_snapshot(c, rows)

    def test_row_decision_after_snapshot_freeze_rejected(self):
        c, rows = sample()
        rows[0]["decision_at"] = "2026-01-04T00:00:00Z"
        reseal(c, rows)
        with self.assertRaisesRegex(DataContractError, "valid cutoff"):
            validate_snapshot(c, rows)

    def test_row_event_after_decision_rejected(self):
        c, rows = sample()
        rows[0]["event_at"] = "2026-01-01T10:00:01Z"
        reseal(c, rows)
        with self.assertRaisesRegex(DataContractError, "valid cutoff"):
            validate_snapshot(c, rows)

    def test_missing_observed_value_requires_reason_and_no_time(self):
        for reason, observed in [(None, None), ("NOT_OBSERVED", "2026-01-01T09:00:00Z"),
                                 ("UNKNOWN", None)]:
            c, rows = sample()
            cell = rows[0]["features"]["optional"]
            cell["missing_reason"], cell["observed_at"] = reason, observed
            reseal(c, rows)
            with self.subTest(reason=reason, observed=observed):
                with self.assertRaises(DataContractError):
                    validate_snapshot(c, rows)

    def test_observed_value_cannot_have_missing_reason(self):
        c, rows = sample()
        rows[0]["features"]["signal"]["missing_reason"] = "SOURCE_MISSING"
        reseal(c, rows)
        with self.assertRaises(DataContractError):
            validate_snapshot(c, rows)

    def test_nan_and_infinity_rejected(self):
        for val in (float("nan"), float("inf"), float("-inf")):
            c, rows = sample()
            rows[0]["features"]["signal"]["value"] = val
            with self.subTest(value=str(val)):
                with self.assertRaises(DataContractError):
                    validate_snapshot(c, rows)

    def test_timezone_required_for_decision_and_observation(self):
        for where in ("decision_at", "event_at"):
            c, rows = sample()
            rows[0][where] = "2026-01-01T10:00:00"
            reseal(c, rows)
            with self.subTest(where=where), self.assertRaisesRegex(DataContractError, "timezone"):
                validate_snapshot(c, rows)
        c, rows = sample()
        rows[0]["features"]["signal"]["observed_at"] = "2026-01-01T09:30:00"
        reseal(c, rows)
        with self.assertRaisesRegex(DataContractError, "timezone"):
            validate_snapshot(c, rows)

    def test_equivalent_timezone_formats_same_duplicate_entity_event(self):
        c, rows = sample()
        rows[1]["entity_id"] = "e1"
        rows[1]["event_at"] = "2026-01-01T10:00:00+01:00"
        reseal(c, rows)
        with self.assertRaisesRegex(DataContractError, "duplicate"):
            validate_snapshot(c, rows)

    def test_wildcard_domain_and_task_rejected(self):
        for field, val in (("task_family", "*"), ("domain", "fin*")):
            c, rows = sample()
            c["scope"][field] = val
            with self.subTest(field=field), self.assertRaises(DataContractError):
                validate_snapshot(c, rows)

    def test_missing_target_or_duplicate_feature_definition_rejected(self):
        c, rows = sample()
        c["columns"]["features"].append("signal")
        with self.assertRaises(DataContractError):
            validate_snapshot(c, rows)
        c, rows = sample()
        c["columns"]["features"].append("label")
        with self.assertRaises(DataContractError):
            validate_snapshot(c, rows)

    def test_missing_schema_columns_and_extra_input_rejected(self):
        for loc in ("contract", "row", "feature"):
            c, rows = sample()
            if loc == "contract":
                c["new_authority"] = True
            elif loc == "row":
                rows[0]["auto_train"] = True
            else:
                rows[0]["features"]["extra"] = {"value": True,
                    "observed_at": "2026-01-01T09:00:00Z", "missing_reason": None}
            if loc != "contract":
                reseal(c, rows)
            with self.subTest(loc=loc), self.assertRaises(DataContractError):
                validate_snapshot(c, rows)

    def test_source_rights_must_be_declared_but_are_not_verified(self):
        for val in ("UNKNOWN", "", None):
            c, rows = sample()
            c["source"]["rights_declaration"] = val
            with self.subTest(val=val), self.assertRaises(DataContractError):
                validate_snapshot(c, rows)

    def test_row_count_mismatch_or_empty_snapshot_rejected(self):
        c, rows = sample()
        c["snapshot"]["row_count"] += 1
        with self.assertRaises(DataContractError):
            validate_snapshot(c, rows)
        c, rows = sample()
        c["snapshot"]["row_count"] = 0
        with self.assertRaises(DataContractError):
            validate_snapshot(c, rows)

    def test_reject_unbounded_dataset_size(self):
        c, rows = sample()
        c["snapshot"]["row_count"] = 10001
        with self.assertRaises(DataContractError):
            validate_snapshot(c, rows)


if __name__ == "__main__":
    unittest.main()
