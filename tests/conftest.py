"""Keep legacy script-style integration tests out of pytest import/collection.

Each script is executed in a fresh interpreter by test_finance_script_isolation.py.
Importing them during pytest collection mutates TTC_HOME and module-global ROOT,
and may write synthetic fixtures into the repository data store.
"""
collect_ignore = [
    "test_adjustment.py",
    "test_ingest_errors.py",
    "test_ledger_pipeline.py",
    "test_quality_gate.py",
    "test_llm_review_budget.py",
]
