# ADR-010 — P1 review response: no self-approval and deny finance mutations

Date: 2026-10-30
Status: DRAFT REVIEW CANDIDATE — NOT MERGED OR OWNER-APPROVED.
Source audit: independent exact-head PR #9 review `2f8c4315c8d0e77152b87d89bfc2469cac2df987`.
Finance legacy fixes are handled on separate review branch and PR, never in this Factory PR.

## Decision and reasons

1. Read-only `inspect_promotion` no longer sets
   `ready_for_external_approval=True` based only on caller-controlled reviewer
   identifiers, snapshots and receipt fields. The offline comparator returns
   `structurally_eligible_for_external_review` instead. The existing
   `ready_for_external_approval` field remains but is always `False`
   until independent identity, reviewer and issuer authentication are introduced
   under a separately authorized gate. All state mutation and production flags
   remain `False`. This changes a positive test expectation intentionally.
2. Replace the incomplete finance-path blacklist with a fail-closed **exact
   allowlist of added files**, relative to the frozen finance baseline SHA.
   Every path change outside the approved Factory subset, including new changes
   to `requirements.txt`, finance CI tests, finance code, config or workflow,
   fails the guard. The guard also checks that the baseline is a Git ancestor.
3. Router v1 supports **100% case coverage only**. Reject policies claiming
   a smaller minimum and remove unreachable coverage logic. Partial benchmarks
   must be blocked, not quietly described as coverage-policy compliant.

## Non-goals and retained concerns

- This is not external critic attestation; no signature/identity custody,
  real benchmark evidence, model deployment, paid provider, registry promotion
  or retraining runtime is introduced.
- Task-specific A, B and C remain synthetic proposals. A self-consistent hash
  does not authenticate issuer or label custody.
- The mock-case limit (64) differs from B's 128 maximum; the bridge must fail
  closed for inputs outside their shared supported range. A future contract
  revision can unify limits after separate review.
- `factory_review/PROJECT_STATE.json` is an internal draft checkpoint, not CI
  attestation. The exact new HEAD must be verified from GitHub Actions run data.
- Finance full-suite failures need their own finance PR and exact-head validation;
  this Factory PR does not change finance behavior or authority.

## Acceptance

On this branch, the Factory synthetic suite plus adversarial protection tests
must pass, and exact-head GitHub CI must report successful required gates.
Review the new SHA independently after any changes; PR merge stays HOLD.
Rollback means close this draft PR; finance main and existing PR #9 are unchanged.
