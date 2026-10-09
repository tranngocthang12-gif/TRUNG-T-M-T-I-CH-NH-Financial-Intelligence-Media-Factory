"""Synthetic tests for an explicit, task-local split and baseline contract."""
import copy
import unittest
from task_templates.tabular_classification import ContractError, freeze_rows, validate_split, majority_baseline


def groups():
    train = [{"row_id": "a", "entity": "g1", "x": 1, "label": 0},
             {"row_id": "b", "entity": "g2", "x": 2, "label": 1},
             {"row_id": "c", "entity": "g3", "x": 2, "label": 1}]
    heldout = [{"row_id": "d", "entity": "g4", "x": 3, "label": 1},
               {"row_id": "e", "entity": "g5", "x": 0, "label": 0}]
    spec = {"schema": "umlf-tabular-classification/v1", "target": "label", "features": ["x"],
            "id_key": "row_id", "group_key": "entity", "split_kind": "GROUP",
            "frozen_holdout_sha256": freeze_rows(heldout)}
    return spec, train, heldout


def temporal():
    spec, train, heldout = groups()
    spec.update({"split_kind": "TEMPORAL", "time_key": "time",
                 "feature_available_at_key": "feature_at", "label_available_at_key": "label_at"})
    spec.pop("group_key")
    for i, r in enumerate(train):
        r.update(time=f"2026-01-{i+1:02d}T00:00:00Z", feature_at=f"2026-01-{i+1:02d}T00:00:00Z",
                 label_at=f"2026-01-{i+3:02d}T00:00:00Z")
    for i, r in enumerate(heldout):
        r.update(time=f"2026-02-{i+1:02d}T00:00:00Z", feature_at=f"2026-01-31T00:00:00Z",
                 label_at=f"2026-02-{i+2:02d}T00:00:00Z")
    spec["frozen_holdout_sha256"] = freeze_rows(heldout)
    return spec, train, heldout


class TabularFactoryTests(unittest.TestCase):
    def test_group_positive(self):
        s, a, b = groups(); self.assertEqual(validate_split(s, a, b)["train_n"], 3)

    def test_majority_uses_train(self):
        s, a, b = groups(); r = majority_baseline(s, a, b)
        self.assertEqual(r["majority_class"], "1")
        self.assertEqual(r["metrics"]["balanced_accuracy"], 0.5)
        self.assertFalse(r["approval_performed"])

    def test_permuting_holdout_preserves_hash(self):
        _, _, b = groups(); self.assertEqual(freeze_rows(b), freeze_rows(list(reversed(b))))

    def test_mutated_holdout_invalidates(self):
        s, a, b = groups(); b[0]["label"] = 0
        with self.assertRaisesRegex(ContractError, "digest"):
            validate_split(s, a, b)

    def test_group_leak_rejected(self):
        s, a, b = groups(); b[0]["entity"] = "g1"; s["frozen_holdout_sha256"] = freeze_rows(b)
        with self.assertRaisesRegex(ContractError, "entity leakage"):
            validate_split(s, a, b)

    def test_row_leak_rejected(self):
        s, a, b = groups(); b[0]["row_id"] = "a"; s["frozen_holdout_sha256"] = freeze_rows(b)
        with self.assertRaisesRegex(ContractError, "identity leakage"):
            validate_split(s, a, b)

    def test_duplicate_train_rejected(self):
        s, a, b = groups()
        with self.assertRaisesRegex(ContractError, "duplicate"):
            validate_split(s, a + [copy.deepcopy(a[0])], b)

    def test_target_leak_in_features_rejected(self):
        s, a, b = groups(); s["features"].append("label")
        with self.assertRaises(ContractError):
            validate_split(s, a, b)

    def test_group_key_in_features_rejected(self):
        s, a, b = groups(); s["features"].append("entity")
        with self.assertRaises(ContractError):
            validate_split(s, a, b)

    def test_holdout_requires_frozen_digest(self):
        s, a, b = groups(); s.pop("frozen_holdout_sha256")
        with self.assertRaises(ContractError):
            validate_split(s, a, b)

    def test_unknown_strategy_rejected(self):
        s, a, b = groups(); s["split_kind"] = "RANDOM"
        with self.assertRaises(ContractError):
            validate_split(s, a, b)

    def test_null_training_rejected(self):
        s, a, b = groups()
        with self.assertRaises(ContractError):
            validate_split(s, [], b)

    def test_unserializable_holdout_rejected(self):
        _, _, b = groups(); b[0]["x"] = float("nan")
        with self.assertRaises(ContractError):
            freeze_rows(b)

    def test_temporal_positive(self):
        s, a, b = temporal(); self.assertEqual(validate_split(s, a, b)["heldout_n"], 2)

    def test_future_feature_rejected(self):
        s, a, b = temporal(); a[0]["feature_at"] = "2026-03-01T00:00:00Z"
        with self.assertRaisesRegex(ContractError, "feature unavailable"):
            validate_split(s, a, b)

    def test_future_train_label_rejected(self):
        s, a, b = temporal(); a[-1]["label_at"] = "2026-03-01T00:00:00Z"
        with self.assertRaisesRegex(ContractError, "label not known"):
            validate_split(s, a, b)

    def test_temporal_order_rejected(self):
        s, a, b = temporal(); a[0]["time"] = "2026-03-01T00:00:00Z"
        with self.assertRaisesRegex(ContractError, "order violated"):
            validate_split(s, a, b)

    def test_naive_time_rejected(self):
        s, a, b = temporal(); a[0]["time"] = "2026-01-01T00:00:00"
        with self.assertRaisesRegex(ContractError, "timezone"):
            validate_split(s, a, b)

    def test_model_output_never_promoted(self):
        s, a, b = groups(); r = majority_baseline(s, a, b)
        self.assertEqual(r["status"], "BASELINE_ONLY_NOT_APPROVED")
        self.assertFalse(r["production_ready"])

    def test_missing_temporal_metadata_rejected(self):
        s, a, b = temporal(); del b[0]["label_at"]
        s["frozen_holdout_sha256"] = freeze_rows(b)
        with self.assertRaisesRegex(ContractError, "temporal metadata missing"):
            validate_split(s, a, b)


if __name__ == "__main__":
    unittest.main()
