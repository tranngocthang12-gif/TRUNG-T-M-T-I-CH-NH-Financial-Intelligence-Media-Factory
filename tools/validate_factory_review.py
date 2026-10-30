"""Fail-closed integration guard for a PINNED Finance P1 + UMLF P1 review tree.

Never grants deployment, finance execution, Owner approval or external attestation.
The approved financial patch is verified by exact Git blob identities, not a
directory-wide exception. This guard must itself receive independent review.
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
FINANCE_BASE = "6bace5fe82ef92393c81d44af714a087e37869d3"
FACTORY_REVIEW_HEAD = "9140ee4e97c46dcc1c3523324997af20f3b4e070"
FINANCE_FIX_HEAD = "52972ff9e55dbe3e1c9c16f88a04fb52266cf8db"

FACTORY_ADDITIONS = frozenset({
    ".github/workflows/factory_review_ci.yml",
    "capability_contracts/__init__.py",
    "capability_contracts/contract_v1.schema.json",
    "capability_contracts/core.py",
    "capability_contracts/evidence_router.py",
    "factory_review/PROJECT_HANDOFF.json",
    "factory_review/PROJECT_STATE.json",
    "factory_review/README.md",
    "factory_review/adr/ADR-008_AUTO05A_FINANCE_RECONCILIATION.md",
    "factory_review/adr/ADR-009_AUTO05BC_EVIDENCE_BRIDGE.md",
    "factory_review/adr/ADR-010_INDEPENDENT_CRITIC_P1_REMEDIATION.md",
    "factory_review/adr/ADR-011_DUAL_DOMAIN_PINNED_INTEGRATION.md",
    "factory_review/evidence_bridge.py",
    "learning_governance/__init__.py",
    "learning_governance/core.py",
    "task_templates/tabular_classification/__init__.py",
    "task_templates/tabular_classification/contract.py",
    "task_templates/tabular_classification/evidence_pilot.py",
    "tests/test_factory_capabilities.py",
    "tests/test_factory_evidence_pilot.py",
    "tests/test_factory_evidence_router.py",
    "tests/test_factory_governance.py",
    "tests/test_factory_integrated_review.py",
    "tests/test_factory_review_protections.py",
    "tests/test_factory_tabular.py",
    "tools/validate_factory_review.py",
})

# Exact paths, diff status and blob IDs copied from immutable Finance PR #11 HEAD.
# Any other engine/test/workflow mutation is forbidden.
FINANCE_PINNED_PATCH = {
    ".github/workflows/finance_p1_review_ci.yml": ("A", "c0fc7ccd7342e0e1a541983194ed3e0828654dd1"),
    "engine/adjust.py": ("M", "d3e84f01748410336191553999063c6ded31e41c"),
    "tests/conftest.py": ("A", "d1167831bcac57b45ebb16f777a14aff9f5d2b4e"),
    "tests/test_adjustment.py": ("M", "06c66b2cde727cbcf096d13354567f51b236f680"),
    "tests/test_finance_missing_ticker.py": ("A", "047c0f93ebc1160ccf6d355ccb5c9b4567fee7ef"),
    "tests/test_finance_script_isolation.py": ("A", "abf9696187e7f5cbb0c590ef857117ed1e8948f9"),
}

# Exact deltas allowed relative to PR #12 (not a general editing license).
INTEGRATION_DELTA = {
    **{path: status for path, (status, _sha) in FINANCE_PINNED_PATCH.items()},
    ".github/workflows/factory_review_ci.yml": "M",
    "factory_review/PROJECT_HANDOFF.json": "M",
    "factory_review/PROJECT_STATE.json": "M",
    "factory_review/adr/ADR-011_DUAL_DOMAIN_PINNED_INTEGRATION.md": "A",
    "tests/test_factory_review_protections.py": "M",
    "tools/validate_factory_review.py": "M",
}

REQUIRED_REVIEW = (
    "factory_review/adr/ADR-008_AUTO05A_FINANCE_RECONCILIATION.md",
    "factory_review/adr/ADR-009_AUTO05BC_EVIDENCE_BRIDGE.md",
    "factory_review/adr/ADR-010_INDEPENDENT_CRITIC_P1_REMEDIATION.md",
    "factory_review/adr/ADR-011_DUAL_DOMAIN_PINNED_INTEGRATION.md",
    "factory_review/evidence_bridge.py",
    "capability_contracts/core.py",
    "capability_contracts/evidence_router.py",
    "task_templates/tabular_classification/evidence_pilot.py",
    "learning_governance/core.py",
    "tests/test_factory_integrated_review.py",
    "tests/test_finance_script_isolation.py",
    "tests/test_factory_review_protections.py",
)


def _parse_changes(lines):
    changes, errors, seen = [], [], set()
    for line in lines:
        fields = line.split("\t")
        if len(fields) != 2 or not fields[0] or not fields[1]:
            errors.append("malformed diff record: " + line)
            continue
        status, path = fields
        if path in seen:
            errors.append("duplicate changed path: " + path)
        seen.add(path)
        changes.append((status, path))
    return changes, errors


def check_changes(diff_lines):
    """Check complete diff from frozen finance main, without directory exceptions."""
    changes, errors = _parse_changes(diff_lines)
    found_finance = set()
    for status, path in changes:
        if status == "A" and path in FACTORY_ADDITIONS:
            continue
        pinned = FINANCE_PINNED_PATCH.get(path)
        if pinned is not None and status == pinned[0]:
            found_finance.add(path)
            continue
        errors.append("change outside frozen dual allowlist: " + status + " " + path)
    for missing in sorted(set(FINANCE_PINNED_PATCH) - found_finance):
        errors.append("required finance fix missing: " + missing)
    return errors


def check_integration_delta(diff_lines):
    """Prove the Factory PR #12 source was not silently edited during reconciliation."""
    changes, errors = _parse_changes(diff_lines)
    found = set()
    for status, path in changes:
        if INTEGRATION_DELTA.get(path) != status:
            errors.append("unapproved change against Factory head: " + status + " " + path)
        else:
            found.add(path)
    for missing in sorted(set(INTEGRATION_DELTA) - found):
        errors.append("required integration delta missing: " + missing)
    return errors


def check_pinned_blobs(observed):
    """Observed maps paths to (mode, type, git blob SHA)."""
    errors = []
    for path, (_status, blob_sha) in FINANCE_PINNED_PATCH.items():
        if observed.get(path) != ("100644", "blob", blob_sha):
            errors.append("finance content/mode differs from approved PR #11: " + path)
    return errors


def _git(*args):
    return subprocess.run(
        ["git", *args], cwd=ROOT, text=True, capture_output=True, check=False,
    )


def _diff(base):
    proc = _git("diff", "--name-status", "--no-renames", base, "HEAD")
    if proc.returncode:
        return None, ["git diff failed against " + base + ": " + proc.stderr.strip()]
    return proc.stdout.splitlines(), []


def _observed_finance_blobs():
    observed = {}
    for path in FINANCE_PINNED_PATCH:
        proc = _git("ls-tree", "HEAD", "--", path)
        if proc.returncode or not proc.stdout.strip():
            continue
        try:
            meta, actual_path = proc.stdout.strip().split("\t", 1)
            mode, kind, sha = meta.split()
            if actual_path == path:
                observed[path] = (mode, kind, sha)
        except ValueError:
            continue
    return observed


def main():
    errors = []
    errors.extend("required file missing: " + path
                  for path in REQUIRED_REVIEW if not (ROOT / path).is_file())

    for name, sha in (("finance main", FINANCE_BASE),
                      ("Factory PR #12", FACTORY_REVIEW_HEAD)):
        if _git("merge-base", "--is-ancestor", sha, "HEAD").returncode:
            errors.append("missing exact ancestry: " + name + " " + sha)

    finance_diff, diff_errors = _diff(FINANCE_BASE)
    errors.extend(diff_errors)
    if finance_diff is not None:
        errors.extend(check_changes(finance_diff))

    factory_diff, diff_errors = _diff(FACTORY_REVIEW_HEAD)
    errors.extend(diff_errors)
    if factory_diff is not None:
        errors.extend(check_integration_delta(factory_diff))

    errors.extend(check_pinned_blobs(_observed_finance_blobs()))
    if errors:
        for error in errors:
            print("FAIL:", error)
        return 1
    print("PASS: exact Finance #11 blobs + Factory #12 lineage; no other diff")
    print("REVIEW ONLY: not an authenticated critic or Owner merge approval")
    return 0


if __name__ == "__main__":
    sys.exit(main())
