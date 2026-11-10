# FINANCE P1 — PIT vintage, trial registry and prospective calibration pilot

**Status:** REVIEW CANDIDATE / NOT OWNER-APPROVED / NO LIVE SOURCE. **Date:** 2026-11-11.
**Dependency:** Finance P0 Ledger #19 must merge and receive independent acceptance before a live prospective pilot. This file is a plan, not a generated market signal.

## Existing source contracts (avoid duplication)

Reuse `contracts/market_data_contract.schema.json` and `contracts/hypothesis.schema.json`; neither alone proves first market availability nor preregistration. The read-only `tools/research_integrity.py` candidate checks two *small envelopes*, not a new generic Factory subsystem.

### PIT vintage envelope

For each material value store:
- `source_id, series_id, entity_id, revision_id, unit, raw_sha256, dataset_vintage_sha256`;
- `event_effective_at` (economic applicability), `published_at` (issuer disclosure), `market_available_at` (feasible market access), `first_seen_at` (first locally observed), `ingested_at` (ingestion);
- `license_status=APPROVED_FOR_THIS_USE`, `quality=VERIFIED_SOURCE` only after independent source review.

These timestamps are **different**. Preliminary algorithm: issuer publication <= market availability <= first observed <= ingestion <= prediction decision. Event-effective time is not always publication time and may legitimately be later. If source was fetched only after a historical decision time, DO NOT certify a point-in-time backtest based on today's revised values. A later archival source needs a separate externally verified historical-vintage attestation; the initial validator refuses it.

**Archive rule:** Retain immutable raw vendor bytes and the issuer's dated publication/revision history. `raw_sha256` is an integrity checksum, not an authority certificate. Store revision lineage instead of silently overwriting corrected BCTC/prices. As-of joins must choose revisions visible at decision time.

**Corporate actions:** Keep pre-adjustment prices separately; derived adjusted/total-return series must retain factor version, event/ex-date, adjustment-run time and issuer source. Historical membership must use an `universe_as_of` snapshot; today's VN30 list cannot stand in for historical membership.

### Prospective trial registry

A proposed `research/trial_registry.jsonl` line must bind:
- `trial_id`, `registered_at`, `spec_sha256`, causal hypothesis + failure mechanism + kill criteria;
- `dataset_vintage_sha256`, `universe_snapshot_sha256`, exact baseline, metric and cost model;
- declared split + embargo, immutable holdout policy;
- `experiment_family_id`, family-wise alpha and **cumulative prior trials count**.

Enforce `registered_at < experiment_started_at`, closed holdout, family budget and deterministic hash links **before** any new trial. Do not retroactively call the 192 historical tests preregistered. Existing finance engine auto-research and automatic candidate promotion must not be promoted into Universal ML Factory or production authority. Turning off/altering scheduled execution is a separate Owner-gated operational change.

The prototype validation routines are **read-only**. They cannot authenticate publication dates, GitHub actor identities, stored bytes or Owner acceptance. There is no `trial_registry.jsonl` writer in this slice, and no new trial has been registered.

### Prospective Pilot v0 — research-only

**Unit:** predeclared yes/no questions on observable future financial indicators (initial domain: published Vietnamese bank financial-statement line items) with official public resolution locator. No price target recommendation or trading.

**Plan:** create 10 paired A/B questions to smoke-test the workflow, each with an exact `question_id`, immutable question text, unit, numeric threshold, `resolve_at`, source, falsifier, both probabilities and baseline before outcome. Require A and B generated independently; the auditor must not author either outcome. First 10 are **pipeline diagnostic only**, not a skill verdict.

**Gate to grading:** (1) sources objectively observable and versioned; (2) question and answer must be registered before `resolve_at`; (3) freeze complete input prompt hashes, model provenance and data cutoff; (4) outcome adjudication by independent code/source reviewer; (5) retain DISPUTED/VOID separately; (6) compare Brier, log loss and predeclared baseline only after enough resolved cases. Report sample size, confidence intervals and A/B discordant subset. Never use LLM backtests over old outcomes to claim future skill.

**Status transitions:** DRAFT -> REGISTERED -> PENDING_RESULT -> RESOLVED/VOID/DISPUTED -> SCORED. Never transition directly from a synthetic test to LIVE CAPITAL. Enrollment is not authorized by this proposal.

### Acceptance and rollback

1. Confirm Finance P0 PR #19 blocking exact-head CI and independent full-diff critique.
2. Validate the PIT/prereg prototype with adverse synthetic tests; no source-authenticity claim.
3. Introduce an official-source proof for two revisions of one public line item (one original, one restated) and show correct historical as-of joins.
4. Require a measured, immutable trial registration, heldout custody and an Owner decision before wiring the current engine to this gate.
5. Revert this P1 candidate freely; it contains no live source, state mutation, automatic scheduler or trading change.

**Explicit deferrals:** Real-vintage ingestion, dataset/policy rights verification, partial-day exchange availability, Deflated Sharpe implementation, multiple hypothesis adjustment across all 192 trials, authenticated blind outcome issuer and calibration sample sufficiency.
