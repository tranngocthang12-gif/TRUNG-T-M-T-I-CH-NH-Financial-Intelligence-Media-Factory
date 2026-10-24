# Universal ML Factory - Architecture (migration candidate v0.2)

Status: MIGRATION CANDIDATE, not production-ready. Date: 2026-10-09.

## Bounded top-level flow

Problem Configuration -> Problem Adapter -> Data Adapter -> Data Contract & Validation
-> Feature/Representation Adapter -> Task Template -> Baseline
-> Model/Trainer Adapter -> Frozen Evaluation -> Error Analysis
-> Read-only Governance and Challenger Comparison -> External Approval
-> Model Registry -> Packaging/Deployment Adapter -> Monitoring/Drift
-> Retraining Proposal -> Re-evaluation -> External Deployment Gate.

Data contracts, evaluation packets, versions, task metrics, leakage rules and deployment permissions are explicit interfaces. No task is allowed to silently select a production model based on an internally computed backtest score.

## The three layers

**Universal Core**: immutable authority boundaries, evidence/provenance, reproducibility, knowledge lifecycle, dependency guards, split freeze contracts, external acceptance contracts, versioned experiments, traceability, monitoring gates. The domain-neutral `learning_governance` package is a read-only subset of this layer.

**Task Templates**: classification/regression, time-series forecasting, anomaly detection, image tasks and other task-specific learning semantics. The first bounded slice is `task_templates/tabular_classification`. Its baseline/split validation is not a universal proof against semantic data leakage.

**Domain Configurations and Adapters**: finance and all future domains bring data acquisition, feature availability, domain-specific risk, objective weights and operational constraints. No finance symbols, brokerage API, stock fees, paper positions, or finance LLM prompts may enter Universal Core.

## Migration map for this repository

| Existing financial subsystem | Disposition | Reason |
|---|---|---|
| `engine/adjust.py`, `engine/data.py` | RETAIN AS LEGACY; future finance Data Adapter | Point-in-time adjustments and data-quality evidence are useful, but Vietnam equity-specific. |
| `engine/features.py`, `engine/research.py` | RETAIN AS LEGACY; extract leakage-safe evaluation concepts into Task Templates | Walk-forward is useful, but global finance `CFG` and price targets are not universal. |
| `engine/ledger.py`, `engine/attribution.py` | RETAIN AS LEGACY; design generic prediction/evaluation receipts separately | Deterministic pre-outcome record and attribution are reusable patterns. |
| `engine/meta.py` | EXCLUDED FROM CORE AND AUTOMATIC ROUTING | Backtest classification reward is not externally audited longitudinal method utility. |
| `engine/knowledge.py` | EXCLUDED FROM GENERIC PROMOTION AUTHORITY | It can auto-mark models ACTIVE based on backtest rank. |
| `engine/paper.py`, `experts/`, `media/` | FINANCE DOMAIN ONLY | Domain-specific trading, investment judgment and publication. |
| `governance/OWNER_MISSION.md`, `SAFETY_STATE.yaml`, `GOVERNOR_POLICY.yaml` | IMMUTABLE LEGACY OWNER RECORDS | Preserve original boundaries; never reinterpret as Factory permission grants. |
| `.github/workflows/daily_cycle.yml` | REPLACED ON CANDIDATE WITH NON-WRITING MANUAL STUB | Avoid unattended scheduled research, spend, state mutation and push. |
| `learning_governance/` | NEW BOUNDED CORE | Source/event evidence checks, scope/dependency guards, review eligibility, model comparator, critic canary. |
| `task_templates/tabular_classification/` | NEW TASK TEMPLATE | Frozen heldout/identity/time split checks and training-only majority baseline. |

All pre-migration source files remain in Git history at the documented pre-migration commit. No finance data is copied into the new universal core. Existing financial directories remain in place during this first non-destructive review slice.

## Independent gates (must not be conflated)

1. Structural validity: schemas, source-byte digests, dependency graph and frozen holdout.
2. Experimental validity: representative data, baseline, robust leakage review, preregistered comparisons and repeatability.
3. Critic validity: externally verified distinct reviewer, frozen canary, sample sufficiency, false-acceptance confidence bounds.
4. Approval authority: authenticated Owner/delegate acceptance, exact artifact hash and audit receipt.
5. Production readiness: rollback, observability, security/privacy/rights, drift response, deployment adapter and retraining gates.

The reference package implements parts of Gate 1 and structural proposals for Gates 2/3. It cannot perform Gates 4/5. A CI `PASS` means unit tests passed; it does not upgrade any of these gates automatically.

## Known gaps

- Full ML Factory runtime, model registry, packaging, deployment, monitoring and retraining controller are not yet implemented.
- Trusted external critic, source rights/authentication and real-data held-out evaluation are pending.
- Existing financial engine and datasets have not yet been verified as a safe domain adapter; the current snapshot carries known point-in-time, source-quality and survivorship limitations.
- The repository is publicly visible at the time of the handoff. No private Library data, secrets or sensitive owner fields should be pushed by automated migration.
- This draft PR must be reviewed before its schedule-safety change reaches default `main`. Existing scheduled financial automation on `main` remains unchanged until merge or authorized operator action.
