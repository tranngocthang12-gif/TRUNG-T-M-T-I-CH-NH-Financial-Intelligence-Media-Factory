# Universal ML Factory — AUTO-05 review area

**REVIEW / NON-CANONICAL / OFFLINE ONLY.** This directory documents the
Owner-approved sequence AUTO-05A (finance reconciliation), AUTO-05B
(cross-stage evidence handoff) and AUTO-05C (dual regression validation).

The *current financial repository authority on main* remains at root
`BOOT.md`, `architecture/ARCHITECTURE.md` and `governance/LAWS.md`.
These proposed Factory files do not supersede finance instructions or grant
the Factory access to financial capital, data, workflows, deployment, APIs,
model activation, retraining or private Library materials.

The reviewed Factory core is a controlled **synthetic-only candidate**:
- `capability_contracts/`: mock provider capability and proposal router
- `task_templates/tabular_classification/`: split/baseline and task-local evidence
- `learning_governance/`: read-only review reference
- `factory_review/evidence_bridge.py`: read-only A→B→C demonstration only
- `tests/test_factory_*.py`: synthetic and adversarial tests

Review decisions and blockers: `factory_review/adr/`,
`factory_review/PROJECT_STATE.json`, `factory_review/PROJECT_HANDOFF.json`.

**No PR in the old stack is approved for finance main by these documents.**
