# Learning Governance Core v0.1 (bounded reference architecture)

## Role and scope

This subsystem implements the decision and evidence discipline from Universal ML Factory Laws 16-26. It is **not** an AI model, memory service, task trainer, deployment service, autonomous writer, or independent reviewer. It is intended to sit between new observations and any externally authorized knowledge/ML change gate:

`Data/Source Adapter -> Evidence Snapshot -> Knowledge Record -> Semantic Guard -> Evaluation + Independent Critique -> Review Eligibility -> External Acceptance -> Registry (out of scope)`

For model selection:

`Task Adapter (frozen dataset/split/metric/leakage contract) -> Parent + Candidate results -> Bounded Comparator -> External Review -> Deployment Gate (out of scope)`

## Exported interfaces

- `validate_record(record)` - structural knowledge/evidence/lifecycle validation.
- `check_dependency_closure(records, target, root_states=("CURRENT",))` - exact ID/version and freshness policy; reject cycles/ambiguous duplicates.
- `check_scope(record, runtime_context)` - exact provider+version and task/domain scope; no inherited provider alias support.
- `invalidation_impact(records, changed, event=None)` - returns affected lineage; **no state mutations**.
- `inspect_promotion(records, target, evidence_snapshots, evaluation, review, runtime_context)` - eligibility to request external approval only; exact target source/eval/critic bindings required.
- `compare_parent_candidate(frozen_packet, parent, challenger)` - task-supplied metric specs with no-regression checks and frozen evaluation packet; review eligibility only.
- `score_critic_canary(cases, contract)` - frozen single-use canary count/role/uncertainty gates; not proof of critic independence.

## Evidence and semantics

Knowledge states: `UNVERIFIED`, `EXPERIMENTAL`, `CURRENT`, `STALE`, `RECHECK_REQUIRED`, `BLOCKED`, `SUPERSEDED`, `RETIRED`.

The supplied `CURRENT` label is not audited automatically. An externally accepted record must have `acceptance_ref`, and an external system must authenticate it. Dependencies must be explicitly pinned by `{id, version}`; the core does not silently follow a successor or implicitly adopt a new provider/model version.

The source hash must match raw bytes supplied at promotion inspection, while storage authenticity, clock correctness, external source rights, and provider identity are **not verified** by this module. Real tasks need a trusted ingress/evaluation provider and signed or otherwise verified reviewer/acceptance provenance.

An evaluation result is not an experiment merely because a JSON field says PASS. A production connection needs frozen data, leakage-safe split, holdout secrecy, evaluator isolation, operator permissions, trusted metric receipts, and monitored deployments.

## Universal Core vs task adapter

Core: record contract, versioning, source snapshots, semantic closure/invalidation, review gates, parent/challenger comparison, canary evaluation, no silent promotion.

Task adapter, later:

- Tabular Classification: train/validation/test identity leakage, target leakage, calibration and PR-AUC/cost.
- Time Series Forecasting: temporal split, forecast horizon, as-of feature availability, MAE/MASE and latency.
- Image Classification: entity/group and near-duplicate leakage, image acquisition time, balanced accuracy and serving cost.

All task-specific metrics and data rules enter as frozen external contracts, never as hard-coded Factory Core constants.

## Gate ordering

1. Validate knowledge structure and evidence source identity.
2. Pin scope and record versions, check semantic dependency graph.
3. Inspect evaluation packet and baseline, with preregistered requirements and exact target hash.
4. Run reviewer and canary assessment externally; attach exact reviewer evidence and dispose material findings.
5. Emit a read-only approval candidate.
6. An externally authorized approver may later request an append-only state transition. **Not implemented here.**
7. Separately require production readiness, monitoring, drift and retraining gates for model deployments.

## Known gaps and future work

- Project-level `PROJECT_CHARTER.md`, complete `ARCHITECTURE.md`, and runtime GitHub integration target were not present among the examined Factory Library assets.
- No real independent critic run, source authentication, semantics-of-prose validation or held-out behavioral learning trial.
- No scheduler, durable event log, model registry, deployment integration or automatic retraining.
- Canary floors are initial conservative **contract floors**. They do not replace study-specific power analysis or statistical design.
- Provenance-gated meta-learning intentionally deferred because upstream MINH TRI critics found unaudited resolution eligibility risks. Do not activate proposal/adaptation based on mere score fields.

This reference is ready for *external review and controlled adapter integration*, not production.
