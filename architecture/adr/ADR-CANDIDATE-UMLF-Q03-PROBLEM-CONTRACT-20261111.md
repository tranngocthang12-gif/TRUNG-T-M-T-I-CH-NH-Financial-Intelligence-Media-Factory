# ADR-CANDIDATE — UMLF Q03 Problem Contract v1

**Status:** DRAFT / REVIEW ONLY / NOT OWNER-APPROVED. **Date:** 2026-11-11.
**Queue:** [Issue #24](https://github.com/tranngocthang12-gif/TRUNG-T-M-T-I-CH-NH-Financial-Intelligence-Media-Factory/issues/24), task Q03.
**Base:** `main` pinned `846f4eba3ad3395f536e3d6d77aa9dd4ea114ee0`; PR #23 remains separate, draft and unmerged.

## Context

The Owner's reusable ML Factory must normally accept
`problem + data + target + metrics + constraints + deployment + retraining`
without redesign. Problem definition precedes data ingestion and training.
Existing synthetic Factory PR #23 provides read-only governance and tabular
contracts but is not approved or merged. Q03 can be independently reviewed
and tested without importing PR #23 code or changing Finance.

## Decision

Implement one provider-neutral, standard-library-only `problem_contract`
package with an exact `umlf-problem/v1` configuration and read-only receipt.
It rejects missing/extra fields; ambiguous or wildcard task/domain;
unfrozen SHA-256 data snapshot; absent dataset identity/source/version;
absent baseline; unsupported metric direction; unbounded compute request;
production deployment; owner-gate bypass; automatic retraining; and
noncanonical JSON. Inputs are not mutated and receipt digests are reproducible.

Q03 is a **contract for declaration**, not evidence that the dataset contents
are authentic or lawful, not a runnable trainer and not a deployment
permission. `training_authorized=False`, `deployment_authorized=False`,
`retraining_authorized=False`, `external_review_proven=False`,
`owner_approval_proven=False` are fixed.

The declaration permits a restricted-data **description** but does not fetch,
view, transmit or train restricted data. `OFFLINE_ONLY` is the sole deployment
mode in this review slice, not production functionality.

## Tradeoffs

- Exact v1 fields keep this contract small; Q04 will introduce a richer
  versioned Data Contract for schema, timestamp, row provenance, labels and
  rights, without adding them prematurely here.
- Backend/model/framework routing remains future replaceable adapters, not
  hardcoded provider dependencies.
- A data SHA proves a declared identifier is syntactically well formed, not
  that the bytes were observed or legitimately acquired.
- Metric names are declared, not yet semantically evaluated; the Task Template
  owns task-specific validation and metric implementation.

## Security / migration

Only `problem_contract/`, one test, one read-only CI workflow and this draft
ADR are added. No `engine/`, `governance/`, financial datasets/ledger/state,
Finance scheduler, payment, trading, publication, secrets or production code is
modified. No private project Library documents or private repository source
is copied into this public repository.

## Acceptance / rollback

Pass exact-head isolated CI, negative tests and changed-file permit list.
Independent evaluator inspects exact commit and catches silent permission
escalation, wildcard and snapshot bypass. Owner alone approves merge via L-10;
a green CI, ADR or external AI recommendation is not approval.

Rollback: close the draft PR / discard branch; no Finance changes.
