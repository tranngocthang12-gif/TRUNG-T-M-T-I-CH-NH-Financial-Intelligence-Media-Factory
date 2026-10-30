"""Review guard: only explicitly approved Factory additions are permitted against finance main.

A protected-path blacklist is incomplete by construction; this exact allowlist
fails closed if ANY existing finance file, CI gate, dependency or config changes.
"""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
FINANCE_BASE = "6bace5fe82ef92393c81d44af714a087e37869d3"
ALLOWED_ADDITIONS = frozenset({
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
    "factory_review/adr/ADR-011_EVALUATOR_SOURCE_BINDING.md",
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
REQUIRED_REVIEW = (
    "factory_review/adr/ADR-008_AUTO05A_FINANCE_RECONCILIATION.md",
    "factory_review/adr/ADR-009_AUTO05BC_EVIDENCE_BRIDGE.md",
    "factory_review/evidence_bridge.py",
    "capability_contracts/core.py",
    "capability_contracts/evidence_router.py",
    "task_templates/tabular_classification/evidence_pilot.py",
    "learning_governance/core.py",
    "tests/test_factory_integrated_review.py",
)


def check_changes(diff_lines):
    """Return every violation. Each changed path must be an approved addition."""
    violations = []
    for line in diff_lines:
        columns = line.split("\t")
        if len(columns) != 2:
            violations.append("unexpected git diff record: " + line)
            continue
        status, path = columns
        if status != "A" or path not in ALLOWED_ADDITIONS:
            violations.append(f"{status}: {path}")
    return violations


def main():
    missing = [p for p in REQUIRED_REVIEW if not (ROOT / p).is_file()]
    if missing:
        print("FAIL: missing reviewed Factory files", missing)
        return 1
    base = subprocess.run(
        ["git", "merge-base", "--is-ancestor", FINANCE_BASE, "HEAD"],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    if base.returncode:
        print("FAIL: expected finance baseline is not an ancestor", base.stderr)
        return 1
    run = subprocess.run(
        ["git", "diff", "--name-status", "--no-renames", FINANCE_BASE, "HEAD"],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    if run.returncode:
        print("FAIL: unable to compare finance baseline", run.stderr)
        return 1
    violations = check_changes(run.stdout.splitlines())
    if violations:
        print("FAIL: changes outside approved Factory additions", violations)
        return 1
    print("PASS: ONLY approved Factory files added; all existing finance files unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
