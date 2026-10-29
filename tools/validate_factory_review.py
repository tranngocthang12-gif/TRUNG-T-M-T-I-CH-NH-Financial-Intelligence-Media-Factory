"""Read-only checks ensuring finance main files are untouched by Factory review."""
import pathlib
import subprocess
import sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
FINANCE_BASE = "6bace5fe82ef92393c81d44af714a087e37869d3"
PROTECTED = (
    "BOOT.md", "architecture/", "governance/", "engine/", "contracts/",
    "ledger/", "state/", "data/", "research/", "paper/", "reports/",
    ".github/workflows/daily_cycle.yml", ".github/workflows/ledger_intake.yml",
    ".github/workflows/tests.yml", "tools/validate.py", "tools/laws_checks.py",
)
REQUIRED_REVIEW = (
    "factory_review/adr/ADR-008_AUTO05A_FINANCE_RECONCILIATION.md",
    "factory_review/adr/ADR-009_AUTO05BC_EVIDENCE_BRIDGE.md",
    "factory_review/evidence_bridge.py",
    "capability_contracts/core.py", "capability_contracts/evidence_router.py",
    "task_templates/tabular_classification/evidence_pilot.py",
    "learning_governance/core.py",
    "tests/test_factory_integrated_review.py",
)


def main():
    missing = [p for p in REQUIRED_REVIEW if not (ROOT / p).is_file()]
    if missing:
        print("FAIL: missing reviewed Factory files", missing)
        return 1
    p = subprocess.run(
        ["git", "diff", "--name-only", FINANCE_BASE, "HEAD", "--", *PROTECTED],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    if p.returncode:
        print("FAIL: unable to compare protected finance files", p.stderr)
        return 1
    changed = [s for s in p.stdout.splitlines() if s.strip()]
    if changed:
        print("FAIL: protected finance paths were modified", changed)
        return 1
    print("PASS: review files present; protected finance main paths unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
