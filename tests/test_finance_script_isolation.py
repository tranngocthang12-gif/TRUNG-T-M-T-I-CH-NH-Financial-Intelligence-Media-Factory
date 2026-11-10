"""Run legacy integration checks as scripts, each in its own isolated Python process.

Script source remains intact (besides point-event correction) while this test
enforces process isolation and checks that tracked finance data was not changed.
"""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = (
    "test_adjustment",
    "test_ingest_errors",
    "test_ledger_pipeline",
    "test_quality_gate",
    "test_llm_review_budget",
)


@pytest.mark.parametrize("module", SCRIPTS)
def test_legacy_script_isolated(module: str) -> None:
    env = dict(os.environ)
    env.pop("TTC_HOME", None)
    env.pop("TTC_MOCK_LLM", None)
    env.pop("ANTHROPIC_API_KEY", None)
    p = subprocess.run(
        [sys.executable, "-m", "tests." + module],
        cwd=REPO, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, timeout=120, check=False,
    )
    assert p.returncode == 0, f"{module} exit {p.returncode}:\n{p.stdout[-7000:]}"
