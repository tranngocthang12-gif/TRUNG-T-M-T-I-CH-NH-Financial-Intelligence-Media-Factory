# ADR-CANDIDATE-UMLF-CORE-SCOPE-GATE-20261111

Status: DRAFT / REVIEW-ONLY / NOT OWNER-APPROVED. Date: 2026-11-11.

## Context
Owner-approved architecture direction: UNIVERSAL CORE -> TASK TEMPLATE -> DOMAIN CONFIGURATION.
The Finance repository `main` at `846f4eba3ad3395f536e3d6d77aa9dd4ea114ee0`
is the immutable branch base for this review candidate. The AUTO-09 source at
`2b582e76d4addcbab2f98e84aa290eb98b55640f` contains read-only
`learning_governance`, a synthetic tabular split/baseline template, and tests,
but the whole branch carries unrelated Finance changes. Never merge either
AUTO-02 or AUTO-09 wholesale.

Grok's council findings: F-002 (AUTO-02 erroneously signalled ready_for_external_approval),
F-003 (wildcard task/domain and cross-domain dependency closure), F-008 (legacy
scheduled Finance writer). Neither CI success nor an AI council report grants
L-09 reviewer or L-10 Owner authority.

## Decision: minimal isolated Factory slice
Create a new review branch from exact Finance main and import just:
- `learning_governance/core.py` (AUTO-09, not AUTO-02), `learning_governance/__init__.py`;
- `task_templates/tabular_classification/contract.py`, package `__init__.py`;
- `tests/test_factory_governance.py` plus F-002/F-003 negative cases;
- `tests/test_factory_tabular.py`;
- `.github/workflows/factory_core_ci.yml` (read-only, no cron, no push);
- this ADR.

Three bounded F-003 changes inside `core.py` only:
1. `validate_record` rejects wildcard `task_family` or `domain`.
2. `check_scope` rejects wildcard even without a preceding validate call.
3. `check_dependency_closure` rejects direct or transitive dependencies
   whose `task_family` or `domain` differs from the root scope.
   Unrelated records are not invalidated by this check.

Keep `inspect_promotion.ready_for_external_approval=False`,
`state_changed=False`, `production_ready=False`; never import the AUTO-02
variant. The tabular contract remains synthetic-only: it does not prove semantic
leakage safety, external dataset authenticity, critic independence, task/domain
generality, model skill or approval readiness.

## Finance and operational boundary
This slice does not modify `BOOT.md`, `architecture/ARCHITECTURE.md`,
`engine/`, `governance/`, `data/`, `state/`,
`.github/workflows/daily_cycle.yml`, `config.yaml`, finance source or
financial permissions. The pre-existing scheduled Finance writer on main
remains unchanged; this is **not** permission to run, enable, disable or
reconfigure it. Do not import capability bridge/router, AUTO-09 validator,
provider parity, finance adapter, pilot, Model Registry, Monitor or Retraining
Controller in this slice.

## CI and acceptance
- Exact-head GitHub Actions `factory_core_ci` must PASS its two synthetic test
  modules, import-boundary guard and exact path allowlist against main.
- Audit PR changed-file list, protected-path blobs and job-level conclusions.
- Independent critic must inspect exact SHA, replicate cross-scope and spoofed
  approval tests, and record limitations. The author may not self-certify.
- Owner separately accepts/rejects merge. No automatic merge or production.
- The Factory suite does not cure legacy Finance full-suite collection failures;
  no claim of whole-repository production readiness.

## Rollback
Close the draft PR and delete its review branch; no Finance main files were
modified. If the proposed contract creates incompatible domain-use cases,
reassess the narrowly scoped policy under Owner review, not an automatic
relaxation to wildcard.