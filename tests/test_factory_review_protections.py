"""Adversarial, offline checks for the exact-source finance/Factory integration guard."""
import unittest

from tools.validate_factory_review import (
    FACTORY_ADDITIONS,
    FINANCE_PINNED_PATCH,
    INTEGRATION_DELTA,
    AUTO07B_DELTA,
    check_changes,
    check_auto07b_delta,
    check_integration_delta,
    check_pinned_blobs,
)


class FactoryProtectionTests(unittest.TestCase):
    def test_complete_pinned_integration_is_allowed(self):
        baseline_diff = [f"A\t{path}" for path in sorted(FACTORY_ADDITIONS)]
        baseline_diff += [f"{status}\t{path}" for path, (status, _sha)
                          in FINANCE_PINNED_PATCH.items()]
        self.assertEqual(check_changes(baseline_diff), [])
        self.assertEqual(check_integration_delta(
            [f"{status}\t{path}" for path, status in INTEGRATION_DELTA.items()]
        ), [])
        self.assertEqual(check_pinned_blobs({
            path: ("100644", "blob", sha)
            for path, (_status, sha) in FINANCE_PINNED_PATCH.items()
        }), [])

    def test_auto07b_scoped_changes_reject_unreviewed_paths(self):
        expected = [f"{status}\t{path}" for path, status in AUTO07B_DELTA.items()]
        self.assertEqual(check_auto07b_delta(expected), [])
        self.assertTrue(check_auto07b_delta(expected[:-1]))
        for rogue in ("M\ttests/test_laws_validate.py",
                      "M\tgovernance/LAWS.md",
                      "M\tengine/adjust.py",
                      "A\tnew_competing_governor.py",
                      "M\trequirements.txt"):
            with self.subTest(path=rogue):
                self.assertTrue(check_auto07b_delta(expected + [rogue]))

    def test_required_finance_change_cannot_be_omitted(self):
        self.assertTrue(check_changes(["A\tfactory_review/evidence_bridge.py"]))
        self.assertTrue(check_integration_delta(["M\tengine/adjust.py"]))

    def test_unknown_finance_or_test_modification_is_denied(self):
        for path in (
            "requirements.txt", "config.yaml", "tools/ledger_intake.py",
            "tests/test_laws_validate.py", "tests/test_no_lookahead.py",
            "engine/data.py", "BOOT.md", "governance/LAWS.md",
            ".github/workflows/daily_cycle.yml",
            "tests/test_finance_backdoor.py",
        ):
            with self.subTest(path=path):
                self.assertTrue(check_changes(["M\t" + path]))
                self.assertTrue(check_integration_delta(["M\t" + path]))

    def test_unapproved_new_factory_or_core_edit_is_denied(self):
        self.assertTrue(check_changes(["A\tfactory_review/unauthorized_policy.py"]))
        self.assertTrue(check_integration_delta(["M\tcapability_contracts/core.py"]))
        self.assertTrue(check_integration_delta(["M\tlearning_governance/core.py"]))

    def test_source_patch_status_is_frozen(self):
        self.assertTrue(check_changes(["D\tengine/adjust.py"]))
        self.assertTrue(check_changes(["A\tengine/adjust.py"]))
        self.assertTrue(check_changes(["M\ttests/conftest.py"]))
        self.assertTrue(check_integration_delta(["D\tengine/adjust.py"]))

    def test_counterfeit_or_missing_finance_blobs_denied(self):
        valid = {path: ("100644", "blob", sha)
                 for path, (_status, sha) in FINANCE_PINNED_PATCH.items()}
        self.assertEqual(check_pinned_blobs(valid), [])
        for path in valid:
            with self.subTest(path=path):
                tampered = dict(valid)
                tampered[path] = ("100644", "blob", "0" * 40)
                self.assertTrue(check_pinned_blobs(tampered))
                tampered = dict(valid)
                tampered[path] = ("120000", "blob", valid[path][2])
                self.assertTrue(check_pinned_blobs(tampered))
                tampered = dict(valid)
                tampered.pop(path)
                self.assertTrue(check_pinned_blobs(tampered))

    def test_delete_rename_duplicate_or_malformed_delta_denied(self):
        for diff in (
            ["D\tconfig.yaml"], ["R100\tBOOT.md\tother.md"], ["bad_record"],
            ["A\ttests/test_finance_missing_ticker.py",
             "A\ttests/test_finance_missing_ticker.py"],
        ):
            self.assertTrue(check_changes(diff))
            self.assertTrue(check_integration_delta(diff))

    def test_approved_and_unauthorized_in_same_diff_still_fail(self):
        diff = [f"{status}\t{path}"
                for path, (status, _sha) in FINANCE_PINNED_PATCH.items()]
        diff += ["A\tfactory_review/evidence_bridge.py", "M\ttests/test_laws_validate.py"]
        self.assertTrue(check_changes(diff))


if __name__ == "__main__":
    unittest.main()
