# ADR-004 — Transfer MINH TRI blinded resolution provenance to optional Factory evaluation

Date: 2026-10-28. Status: **CANDIDATE / NOT ACCEPTED / NOT CANONICAL**.
Scope: Factory migration candidate only; no production authorization.

## Evidence and motivation

MINH TRI protected main includes `src/minhtri/resolution_provenance.py` and
`tests/test_resolution_provenance.py`: raw-snapshot hashes, preregistered prediction
order, blind resolution declarations and negative controls. MINH TRI PR #480 also
merged a read-only post-merge reconciler with negative tests. These improve
inspection of reported scores but cannot authenticate identities, source facts
or independence in the real world.

Factory `learning_governance/core.py` already implements scoped knowledge,
dependency closure, minimal invalidation, baseline/challenger comparison and a
critic canary. Do not duplicate those mechanisms, import MINH TRI runtime or
give any new subsystem production authority.

## Bounded candidate decision

Add `learning_governance/outcome_provenance.py`: a **read-only**, optional
inspector for *prospective* task outcome receipts. The declared receipt binds
frozen evaluation rules, prediction artifact, outcome availability/capture
times, raw outcome snapshot SHA-256 bytes and declared blind label extraction.
Reject missing, contradictory or unblinded inputs. Success is solely
`STRUCTURALLY_ELIGIBLE_FOR_REVIEW`; never VERIFIED, deployment approval, model
promotion, trial activation, automatic learning or retraining.

**Applicability boundary:** `prediction_frozen_at < outcome_first_available_at`
is meaningful for prospective forecasts. It is NOT a general rule for offline
historical supervised classification, image tasks or historical backtesting.
Those require their own task-specific split, label-access and contamination
contracts. Do not let this optional inspector replace those evaluation gates.

Names, hashes and timestamps remain self-declarations; SHA-256 verifies byte
equality, not source authenticity, genuine preregistration or independent
review. A passing receipt proves neither semantic label correctness nor causal
model improvement.

## Verification and reconciliation

Synthetic-only tests cover ordering, altered/missing source bytes,
contamination of blind resolver, same-actor claims, historical-mode exclusion,
missing fields and immutable read-only input. Before promotion require exact
head independent review, real authorized prospective task evidence, externally
attested sources/times, negative controls and Task Adapter integration.

Finance `main` advanced independently after Factory draft PR #2; its
`architecture/ARCHITECTURE.md` v3.0 and legacy mission are not superseded.
This change is stacked on `auto/umlf-refactor-v0-2` using a separate
candidate branch. Owner-reviewed main reconciliation and the original
migration approval gates remain necessary. Do not merge this candidate into
finance main independently.

## Reversal

Drop the optional module, tests and this ADR from candidate. No default-main
state, finance runtime, training pipeline, deployed model or data is mutated.
