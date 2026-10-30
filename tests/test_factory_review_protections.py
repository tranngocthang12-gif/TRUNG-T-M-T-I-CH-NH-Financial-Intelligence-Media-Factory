"""Adversarial tests for the exact-path finance boundary on the Factory review branch."""
import unittest
from tools.validate_factory_review import check_changes


class FactoryProtectionTests(unittest.TestCase):
    def test_approved_factory_addition(self):
        self.assertEqual(check_changes(["A\tfactory_review/evidence_bridge.py"]), [])

    def test_critical_finance_configuration_never_allowed(self):
        for path in ("requirements.txt", "config.yaml", "tools/ledger_intake.py",
                     "tests/test_laws_validate.py", "tests/test_no_lookahead.py",
                     "engine/adjust.py", "BOOT.md", ".github/workflows/daily_cycle.yml"):
            with self.subTest(path=path):
                self.assertTrue(check_changes(["M\t" + path]))

    def test_unexpected_new_file_blocked(self):
        self.assertTrue(check_changes(["A\ttests/test_finance_backdoor.py"]))
        self.assertTrue(check_changes(["A\tfactory_review/unauthorized_policy.py"]))

    def test_deletes_renames_and_modifications_are_blocked(self):
        self.assertTrue(check_changes(["D\tconfig.yaml"]))
        self.assertTrue(check_changes(["M\tcapability_contracts/core.py"]))
        self.assertTrue(check_changes(["R100\tBOOT.md\tother.md"]))

    def test_unauthorized_and_valid_in_same_commit_still_fail(self):
        self.assertTrue(check_changes([
            "A\tfactory_review/evidence_bridge.py",
            "M\ttests/test_laws_validate.py",
        ]))


if __name__ == "__main__":
    unittest.main()
