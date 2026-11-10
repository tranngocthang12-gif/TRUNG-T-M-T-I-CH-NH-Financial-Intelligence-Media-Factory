# ADR-CANDIDATE-PIT-TRIAL-P1 — Read-only financial vintage and trial gates

**Date:** 2026-11-11. **Status:** PROPOSED, REVIEW ONLY, NOT OWNER-APPROVED.
**Depends on:** finance Prediction Ledger P0 PR #19 for any prospective pilot.

## Decision proposed

Prefer the smallest coherent finance-only, fail-closed *validator* over new independent agents or a second ML governance stack:

- A PIT observation is eligible only when the precise source revision is known by the decision's timestamp and the exact data hash and usage rights are declared and later authenticated.
- A trial is eligible only when its full immutable specification and multiple-testing budget precede execution, and its holdout is still sealed.
- Validators have read-only authority and may reject; they may not write `trial_registry.jsonl`, elevate evidence, activate models, schedule retraining, allocate real capital or infer issuer authenticity.
- No retroactive preregistration for existing 192 historical tests; history is preserved separately.

The canonical Finance `architecture/ARCHITECTURE.md`, `governance/LAWS.md`, `state/PROJECT_STATE.yaml`, `SAFETY_STATE.yaml`, and `daily_cycle.yml` remain unchanged in this PR. The source adapter belongs to the Finance domain, not Universal ML Factory Core.

## Alternatives rejected

1. Auto-promotion when alpha/backtest threshold is positive: rejects the separation of experiment validity from deployment authority.
2. A new universal source/experiment governance stack inside Finance: duplicates the already planned Universal ML Factory boundary.
3. Automatically rewriting historical prices or backfilling `trial_registry.jsonl` from `research/trials.csv`: destroys provenance and creates false before-the-fact evidence.

## Evidence and limits

Synthetic unit tests only. No issuer-signed vintage, genuine OOS performance, multiple-testing correction over all historical trials, actual prospective paired A/B forecasts, or external critic attestation.

## Rollback and Owner gates

Revert this review PR without changing stored data, forecasts or research history. Prior to any merge, obtain exact-SHA CI and independent review. Before operational use: proof of source publication/availability, signed Owner research authority, immutable holdout and validator at experiment entry. Pilot starts only when PR #19 and these gates are accepted; never grants live trading.
