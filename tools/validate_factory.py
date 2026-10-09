"""Dependency-free Factory repo boundary check; runs offline and writes nothing."""
from __future__ import annotations
import ast
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    "PROJECT_CHARTER.md", "ARCHITECTURE.md", "PROJECT_STATE.json", "PROJECT_HANDOFF.json",
    "learning_governance/core.py", "task_templates/tabular_classification/contract.py",
    "docs/adr/ADR-003_FINANCE_REPO_REPURPOSING.md", "docs/ADVERSARIAL_REVIEW_AUTO02.md",
    "tests/test_factory_governance.py", "tests/test_factory_tabular.py",
    ".github/workflows/daily_cycle.yml", ".github/workflows/factory_ci.yml",
)


def validate():
    issues = []
    for file in REQUIRED:
        if not (ROOT / file).is_file():
            issues.append("Missing Factory contract: " + file)
    old = ROOT / ".github/workflows/daily_cycle.yml"
    if old.is_file():
        text = old.read_text(encoding="utf-8")
        if re.search(r"(?m)^\s*schedule\s*:", text):
            issues.append("Legacy finance scheduled workflow is still enabled")
        if re.search(r"(?m)^\s*contents\s*:\s*write\b", text):
            issues.append("Legacy finance workflow still has write permission")
        for forbidden in ("git push", "engine.run_cycle", "pip install -r requirements.txt"):
            # Comments and echo messages may mention forbidden operations; require command context.
            if re.search(r"(?m)^\s*(?:-\s+)?" + re.escape(forbidden), text):
                issues.append("Legacy workflow executes forbidden command: " + forbidden)
    core_path = ROOT / "learning_governance/core.py"
    if core_path.is_file():
        tree = ast.parse(core_path.read_text(encoding="utf-8"), filename=str(core_path))
        allowed = {"__future__", "hashlib", "json", "math", "re", "collections", "datetime", "typing"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module.split(".")[0]] if node.module else []
            else:
                continue
            for name in names:
                if name not in allowed:
                    issues.append("Unapproved dependency in universal governance core: " + name)
    return issues


if __name__ == "__main__":
    result = validate()
    for issue in result:
        print("FAIL:", issue)
    if result:
        sys.exit(1)
    print("PASS: Factory required contracts, source isolation and legacy workflow safety")
