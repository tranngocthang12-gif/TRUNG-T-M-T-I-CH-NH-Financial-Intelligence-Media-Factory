"""Adversarial, offline checks for the exact-source finance/Factory integration guard."""
import unittest
import pathlib
import subprocess
import tempfile
from unittest.mock import patch

from tools import validate_factory_review as review_validator

from tools.validate_factory_review import (
    FACTORY_ADDITIONS,
    FINANCE_PINNED_PATCH,
    INTEGRATION_DELTA,
    AUTO07B_DELTA,
    AUTO08_DELTA,
    AUTO09_DELTA,
    check_auto09_delta,
    check_auto08_delta,
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

    def test_auto08_exact_diff_rejects_rogue_finance_or_factory_files(self):
        expected = [f"{status}\t{path}" for path, status in AUTO08_DELTA.items()]
        self.assertEqual(check_auto08_delta(expected), [])
        self.assertTrue(check_auto08_delta(expected[:-1]))
        for changed in ("M\tengine/adjust.py",
                        "M\trequirements.txt",
                        "M\tgovernance/LAWS.md",
                        "M\tlearning_governance/core.py",
                        "A\ttools/secret_promoter.py"):
            with self.subTest(changed=changed):
                self.assertTrue(check_auto08_delta(expected + [changed]))

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

    def test_auto09_exact_scope_denies_unrelated_paths(self):
        expected = [f"{status}\t{path}" for path, status in AUTO09_DELTA.items()]
        self.assertEqual(check_auto09_delta(expected), [])
        self.assertTrue(check_auto09_delta(expected[:-1]))
        for rogue in ("M\tengine/adjust.py", "M\tlearning_governance/core.py",
                      "M\t.github/workflows/daily_cycle.yml", "A\tsecrets.txt"):
            with self.subTest(rogue=rogue):
                self.assertTrue(check_auto09_delta(expected + [rogue]))

    def test_main_only_data_commit_is_not_attributed_to_review_pr(self):
        """A moving main cannot poison the exact PR-owned diff or hide a review edit."""
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)

            def git(*args):
                return subprocess.run(
                    ["git", *args], cwd=root, text=True,
                    capture_output=True, check=True,
                ).stdout.strip()

            git("init", "-b", "main")
            git("config", "user.name", "Synthetic Reviewer")
            git("config", "user.email", "synthetic@example.invalid")
            (root / "README.md").write_text("frozen base\n", encoding="utf-8")
            git("add", ".")
            git("commit", "-m", "frozen finance anchor")
            frozen = git("rev-parse", "HEAD")

            git("checkout", "-b", "review/test")
            (root / "factory_review").mkdir()
            (root / "factory_review" / "review.txt").write_text(
                "PR-owned source\n", encoding="utf-8")
            git("add", ".")
            git("commit", "-m", "review change")
            git("checkout", "main")
            (root / "data").mkdir()
            (root / "data" / "fresh.json").write_text(
                '{"synthetic":true}\n', encoding="utf-8")
            git("add", ".")
            git("commit", "-m", "unrelated main data")
            git("checkout", "review/test")

            with (patch.object(review_validator, "ROOT", root),
                  patch.object(review_validator, "FINANCE_BASE", frozen)):
                base, errors = review_validator._review_merge_base("main")
                owned, diff_errors = review_validator._diff(base)
                naive, naive_errors = review_validator._diff("main")
                self.assertEqual(errors + diff_errors + naive_errors, [])
                self.assertEqual(base, frozen)
                self.assertEqual(owned, ["A\tfactory_review/review.txt"])
                self.assertIn("D\tdata/fresh.json", naive)

                # A branch-borne unauthorized change is still visible.
                (root / "engine").mkdir()
                (root / "engine" / "unreviewed.py").write_text("pass\n", encoding="utf-8")
                git("add", ".")
                git("commit", "-m", "unauthorized branch change")
                branch_delta, delta_errors = review_validator._diff(base)
                self.assertEqual(delta_errors, [])
                self.assertIn("A\tengine/unreviewed.py", branch_delta)
                self.assertTrue(review_validator.check_changes(branch_delta))

                with patch.object(review_validator, "FINANCE_BASE", "f" * 40):
                    missing, blocked = review_validator._review_merge_base("main")
                self.assertIsNone(missing)
                self.assertTrue(blocked)


if __name__ == "__main__":
    unittest.main()
