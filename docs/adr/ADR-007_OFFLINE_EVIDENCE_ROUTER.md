# ADR-007 — Offline evidence-based provider routing proposal

Date: 2026-10-30
Status: **CANDIDATE / NOT ACCEPTED / NOT PRODUCTION**
Parent: draft PR #6 (Part B), stacked on draft #5 (Part A) and draft #2 (migration).

## Decision

Add the smallest possible *read-only* router proposal to
`capability_contracts/evidence_router.py`; no new orchestrator and no provider
SDK, paid API, external lookup, deployment or model state mutation. It examines
up to four **synthetic-only** benchmark receipt declarations for the four
existing mock adapter identities. It does **not** call those mock adapters.

A caller pins an immutable policy hash. Each receipt must reference the same
policy, evaluator and case-set digests, with complete declared case coverage.
The policy freezes minimum accuracy, maximum critical-case error rate, latency,
cost and coverage. Nonfinite, malformed or spoofed provider receipt fields fail
closed. Integrity counters must have exactly the declared keys, and any nonzero
counter makes a candidate ineligible. Eligible mock candidates are sorted
deterministically by lowest reported cost, then latency, then highest accuracy,
then provider identifier. If none qualifies, return NO_ELIGIBLE_CANDIDATE.

A SHA-256 digest establishes consistency with *supplied* bytes, **not**
independently authenticated benchmarking, model/provider identity, case-level
metric integrity, real-world causal benefit or an authenticated evaluator.
Receipt metrics and cost remain self-declarations. No successful proposal
promotes a model or authorizes a real API call, inference or production routing.

## Boundary and non-goals

This is an interface-policy pilot, not a second model-evaluation engine.
`learning_governance` retains evaluation/promotion boundaries; the tabular
Task Template retains task-local metric definitions and case-level evaluation.
Part C only tests the **routing decision on declared bounded receipts**.
The frozen packet does not create external trusted records. The existing
finance `main` remains unchanged; Owner decisions and external review stay
required for any production authority.

The prototype deliberately rejects any real provider IDs and any non-synthetic
mode. A real implementation needs trusted receipt issuers, independent
benchmark provenance, genuine measured costs and performance confidence
intervals, versioned routing rules, drift monitoring, rollback and explicit
authorization.

## Tests and rollback

The new `tests/test_factory_evidence_router.py` covers deterministic
selection, no eligible candidate, guardrail failure, latency/cost ceilings,
integrity counter failure, tampered policy, mismatched evaluator/case hash,
missing coverage, duplicate/fake providers, nonfinite metrics and read-only
operation. Validate the entire stacked Factory test suite in PR CI at exact
HEAD; CI pass is synthetic code-contract evidence only.

Rollback: close this Draft PR / remove the optional file, test and ADR.
No finance data, real model, registry, deployment or Owner authority is changed.
