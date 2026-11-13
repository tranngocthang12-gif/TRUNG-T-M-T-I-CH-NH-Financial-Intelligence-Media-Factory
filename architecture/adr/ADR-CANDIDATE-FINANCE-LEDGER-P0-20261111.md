# ADR-CANDIDATE-LEDGER-P0 — Restore a measurable prospective Forecast Ledger

**Status:** DRAFT / REVIEW ONLY (11 Nov 2026). Not Owner-approved and not a deployment release.
**Repository boundary:** Finance `main` v3.0; no Universal ML Factory migration or superseding governance.
**Owner action:** Review and merge only after independent exact-head review and passing blocking CI.

## Problem and observed evidence

The Finance v3.0 Issue intake writes `p` and string `resolution_rule`; the existing engine resolver expects `probability` and object `resolution_rule`. Both operate on `ledger/predictions.jsonl`. At inspection the 10 Nov 2026 scorecard had zero forecasts/resolutions; successful Issue-to-Scorecard integration had not been proven. The current `issues: [opened, labeled]` workflow can register a late-labeled/modified Issue under its old creation timestamp. This is not acceptable for a prospective calibration ledger.

## Chosen bounded remediation

1. Add `engine/forecast_bridge.py` as a read-only, deterministic view of two existing row formats; do not rewrite or re-hash legacy entries.
2. Freeze new Forecast Issues only via the Owner-created `issues.opened` event, reject edited or later-labeled records, duplicate keys and malformed fields, and retain server timestamps plus a SHA-256 of event body. A local hash of data is NOT a trusted issuer timestamp or proof of outside-source authenticity.
3. Require explicit `ticker` + `horizon` for `excess_return_positive`; retain the current event/numeric/comparison Issue form rules, but mark them `SOURCE_RESOLVER_NOT_IMPLEMENTED` until an independent official-source evaluator exists. No fabricated or inferred outcomes.
4. For price outcomes, require the declared due date and the exit session to have elapsed, plus the existing corporate-action/data-quality gates. Store resolution separately; preserve historical outcomes and hash chain.
5. Report raw count, eligible count, blocked reasons, VOID and actual scored outcomes separately. Keep the existing 30-outcome minimum before a procedure verdict.
6. Make the isolated E2E and adverse tests blocking in PR CI, while preserving the original finance daily schedule and Owner-controlled spending/trading flags.

## Adversarial and remaining limitations

- The input Issue is not itself independent financial evidence, and a hash only binds bytes recorded in the ledger.
- User-declared `resolution_source` is NOT yet independently authenticated.
- An Issue forecast is not validated as useful investment advice; this system is research-only.
- Price history source is temporary Yahoo; point-in-time corporate actions, historical universe, restatements and cross-provider validation remain P1 blockers before a real market performance claim.
- Existing legacy prediction rows are read without rewriting, but their original timing/provenance limits remain.
- Matching A/B predictions still requires independent control on question, baseline, model isolation and outcome custody; Brier alone does not establish advantage.
- Issue workflow has repository write authority as before; security review should separately consider moving writes through protected PRs. Do not interpret this review branch as authorization to change it.
- A passing synthetic test cannot prove source authenticity, forecast calibration, independence, or deployment readiness.

## Next gates and scoped pilot

**Gate P0-1:** Exact new-head CI success plus direct synthetic replay covering Issue open -> hash chain -> normalized view -> pre-due WAIT -> final-price outcome/VOID -> scorecard, duplicates, malicious late edit and late label.

**Gate P0-2:** Distinct independent review of this full commit SHA and a recorded Owner decision. Do not merge otherwise.

**Gate P1-A:** A point-in-time vintage contract records `event_effective_at`, `published_at`, `available_at`, `observed_at`, `revised_at`, `source_sha256`, `corporate_action_id` and `universe_as_of`; fail closed on future evidence. Replay corrected/restated prices in frozen snapshots.

**Gate P1-B:** Prospective immutable trial manifest: hypothesis, causal rationale, baseline, dataset/vintage hashes, window/embargo, alpha-spend/multiple-testing ledger, cancellation criteria, decision timestamp; existing 192 historic trials are NOT retroactively certified as preregistered.

**Gate P1-C (pilot):** Start only after P0 gates; use predeclared prospective A/B questions (same exact text, threshold, sources, deadline) and a separate outcome adjudicator, initially paper/research only. Track registered/eligible/resolved/VOID, proper scores, Brier versus fixed baseline and confidence intervals. Report `INSUFFICIENT_SAMPLE` until sample conditions are met. No API, trade, finance publication or autonomous decision.

## Rollback

Revert this bounded commit series/PR. Do not delete Ledger, resolutions or prior historical finance material. Previously recorded new Issue rows are retained for audit, but the legacy resolver must not be asked to consume new-format rows after a rollback without bridge; apply the compatibility guard or stop the scheduler. Revalidate the hash chain and compare exact existing-finance source bytes. Changes to `main`, trading, spending or deployment require separate Owner authorization.
