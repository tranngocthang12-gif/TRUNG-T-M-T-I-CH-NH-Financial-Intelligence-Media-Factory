# ADR-009 — AUTO-05B/C: bounded synthetic evidence handoff and dual regression gates

Date: 2026-10-30
Status: REVIEW CANDIDATE, NOT OWNER MERGE APPROVAL.
Supersedes no finance law and changes no live-provider adapter.

## Decision

The Factory's A, B and C pilots were separately green but had no authenticated
or tested handoff. Add an **audit-only** bridge under
`factory_review/evidence_bridge.py` and tests under
`tests/test_factory_integrated_review.py`.

It uses an A `analyze_errors` request that must match the exact synthetic
baseline case labels; verifies the returned mock receipt using a caller-supplied
expected mock identity; computes B baseline/challenger metrics from per-case
predictions through the existing `inspect_synthetic_paired_trial` and
`learning_governance.compare_parent_candidate`; and **only when B is
structurally review-eligible** constructs a C `SIMULATED_BENCHMARK`
receipt derived from B's computed challenger metrics and exact case-set pin.

The bridge **never** consumes a caller-supplied accuracy score, latency, model
cost or approval flag as credible evidence. Its 0 cost and latency are explicit
mock simulation constants, not real measurements. All outputs remain
`SYNTHETIC_*_ONLY`, `BLOCKED_BY_EVALUATION` or `ROUTER_REJECTED`.
Provider identity, evaluator origin, execution record, the caller's
cryptographic pin custody, and unobserved label access are **not authenticated**.
It is *not* safe to route real providers or use real holdouts.

No general second comparator, central orchestrator, retraining loop, provider
SDK, new financial domain adapter or second source of legal authority.
`capability_contracts`, `task_templates`, and `learning_governance` are
carried in read-only form from PR #7 at
`a67d0e03fff4aedcbdd71a2d59fec24ebc13fbe2`.

## AUTO-05C tests and gates

- A/B/C integration controls: positive mock-only chain, four adapter identities,
  negative evaluation/guardrail, label integrity, policy pins, case-set matching,
  denied network/spend and no mutation.
- Full Factory `test_factory_*.py` discovery, offline source-boundary checks.
- Finance workflow's blocking `tests/test_laws_validate.py`, lookahead and
  `tools/validate.py`, and full finance `pytest tests` as *informational*
  where existing finance policy marks it `continue-on-error`.
- The reconciled review branch must preserve all protected `main` files.
  A passing GitHub Action on a PR is **not** an independent auditor, source
  attestation, real-data benchmark, human decision or production go-ahead.

## Rollback / unresolved blockers

Close the review PR to abandon the proposal. No main changes, no finance
workflow alteration, no API spending or promotion occurred.
Unresolved gates: independent exact-head review, authenticity and trust boundary
on future benchmark receipts, real holdout/privacy/license rights, Owner's
explicit choice of future repository/canonical architecture. The previous
Draft stack remains separate and must not be merged directly into finance main.
