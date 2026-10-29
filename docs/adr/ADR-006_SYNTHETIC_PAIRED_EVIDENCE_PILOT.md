# ADR-006 — Synthetic paired evaluation pilot for tabular classification

Date: 2026-10-30
Status: **CANDIDATE / NOT MERGED / NOT PRODUCTION**
Parent: draft PR #5 (AUTO-04A), which is itself stacked on draft Factory migration PR #2.
Scope: tabular classification task template only, no finance/runtime integration.

## Problem and decision

The Factory already has a generic `learning_governance.compare_parent_candidate`
that checks a frozen metric packet, guardrail regressions and declared integrity
failures. A second comparator would multiply authority. The missing small piece
is an *offline*, task-local way to compute metrics from case-level predictions,
rather than trusting self-reported scores. Add the pure/read-only
`task_templates/tabular_classification/evidence_pilot.py` with test fixtures.

It accepts a 12..128-row **synthetic-only**, balanced binary classification
fixture, exactly two frozen metrics (accuracy as primary, critical-case error
rate as guardrail), externally passed packet SHA-256, one baseline run and one
challenger run. It verifies identical case-ID coverage; checks declared feature
allowlists, exact shape, explicit critical failure counters and distinct run
references. It computes both metrics and paired wins/losses from the raw
synthetic prediction labels and then invokes the *existing* governance comparator.
Responses can be `SYNTHETIC_REVIEW_ELIGIBLE` or
`SYNTHETIC_NOT_ELIGIBLE` only. Neither is model acceptance.

## Adversarial cases

The synthetic fixture deliberately demonstrates:
- no performance improvement; label-flipped negative control;
- higher overall accuracy but worse critical-case error rate;
- a perfect-scoring challenger using forbidden label leakage;
- post-registration changes to metrics or ground truth;
- missing, duplicated or out-of-fixture case predictions;
- malformed/NaN thresholds, fake claims of accuracy and integrity faults;
- packet and case hashes treated as byte consistency, not identity proof.

The guardrail choice and value are task-template policy, NOT universal ML
metrics. Declared `features_used` and `critical_failures` can be dishonest
without authenticated execution and trusted data access; these checks
therefore cannot establish no leakage or genuine independence.

## Boundaries, acceptance and rollback

No external APIs, real datasets, new provider router, model training, dataset
ingestion, knowledge self-promotion, automatic deployment or retraining. No
source material from the private Project Library is published. No modification
to legacy finance main and no changes to the existing generic comparator.

Run `python -m unittest discover -s tests -p 'test_factory_*.py' -v` and
`python tools/validate_factory.py` in the PR branch. CI success validates
code/test behavior only. Independent review, real heldout evidence and an
authenticated Owner deployment gate remain separately required.

Revert this candidate PR to remove the bounded task pilot without changing
the previous Factory contracts or any production data. `main` remains
authoritative for finance until the migration is explicitly reconciled.
