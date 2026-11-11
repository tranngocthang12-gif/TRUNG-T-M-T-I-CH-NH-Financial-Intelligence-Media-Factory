# ADR-CANDIDATE UMLF-Q04: Provisional Data Contract v1

**Status:** PROVISIONAL / REVIEW ONLY / NOT ACCEPTED / NO OWNER APPROVAL.
**Date:** 2026-11-12. **Queue:** [#24](https://github.com/tranngocthang12-gif/TRUNG-T-M-T-I-CH-NH-Financial-Intelligence-Media-Factory/issues/24).
**Source main SHA:** `3dd296877d43276acfbfb406deeb3c90ff084d4e`.
**Predecessor:** [Q03 PR #25](https://github.com/tranngocthang12-gif/TRUNG-T-M-T-I-CH-NH-Financial-Intelligence-Media-Factory/pull/25), not independently accepted or merged.
**Separation:** Q04 imports neither Q03 code nor any Finance module; no combined execution.

## Context and decision
The Universal Factory needs a provider-neutral, non-writing in-memory Data
Contract, prior to feature engineering or training. Propose a pure Python
`data_contract` with frozen structural `umlf-data/v1` declaration, canonical
row snapshot digest, stable identities, exact fields, declared source-rights
basis, event/decision/observation timestamps, per-cell missing reason, and
evidence-only receipt.

The caller supplies rows. The validator neither reads an external file nor
authenticates a checksum. It recomputes row SHA-256 and compares it to the
declared frozen digest to detect changes relative to the supplied declaration.
It rejects NaN/Infinity; duplicate row keys or entity+event keys; absent time
zones; feature observations later than per-row decision time; targets observed
after snapshot freeze; undecided missingness; unsupported rights basis; and
unexpected columns and claims of runtime authority.

## Freeze and time semantics
- `event_at <= decision_at <= frozen_at`.
- Nonmissing feature `observed_at <= decision_at` and `<= frozen_at`.
- Nonmissing target may be observed after decision but no later than freeze.
- Per-cell `missing_reason` is one of
  `NOT_OBSERVED`, `SOURCE_MISSING`, `REDACTED` when value is null; an observed
  value must not carry missing reason.
- Canonical JSON byte digest pins **the supplied rows**, not their real-world
  provenance, original wire bytes, ordering-neutral dataset identity, or rights.
- Datetime comparison honors UTC offsets; exact entity-event duplicate checks
  compare normalized instants. Identity is per declared snapshot.
- Row limit is synthetic safety bound 10k; 512 max features. No streaming yet.

## Nonclaims and future bounds
All receipts explicitly set
`source_rights_verified=False`,
`source_authenticity_proven=False`,
`availability_metadata_authenticated=False`,
`semantic_leakage_excluded=False`,
`training_authorized=False`, `deployment_authorized=False`,
`retraining_authorized=False`, and `owner_approval_proven=False`.

Real source rights, label semantics, feature availability trust, row-level
lineage, holdout identity/group isolation and semantic leakage review need
separate provenance and Task Template adapters (Q05 onwards).
A genuine data hash requires independently acquired source bytes. `rights_ref`
is only a declaration and cannot confer rights. Missing-target rows remain
described but cannot be silently used as supervised labels.

## Boundaries and acceptance
The review branch changes exactly five new paths: `data_contract/` core and
init, one synthetic negative-test file, one read-only scope-gated CI workflow,
and this ADR. Existing Finance source, state, schedule and permissions remain
untouched. The workflow uses a no-renames name-status gate permitting only
five additions, with negative rename and positive addition fixtures.

Q04 is **provisional** because Q03 has not passed authenticated independent
L-09 plus Owner L-10 gates. A green Q04 CI confirms only structural behavior;
it must not close Q04 as accepted or trigger downstream work or merge. Future
review must check these precise claims on an exact head SHA.

Rollback: close the candidate PR/branch with no impact to `main`.
