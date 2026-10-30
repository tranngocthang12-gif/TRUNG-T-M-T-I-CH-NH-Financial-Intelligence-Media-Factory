# ADR-011 — Evaluator source-byte binding for synthetic A-B-C bridge

Date: 2026-10-30
Status: DRAFT REVIEW CANDIDATE — NOT OWNER-APPROVED / NOT MERGED.
Finding: independent Claude review of PR #9 at `2f8c4315c8d0e77152b87d89bfc2469cac2df987`, REV-P1-004.

## Context

The synthetic bridge copied `router_packet.evaluator_sha256` into a receipt.
A caller controlling the packet and hash could provide any 64-hex value.
This was not even a binding to the actual evaluator code. The source is public
and the prototype does not have a trusted external evaluator, issuer, training
trace, or holdout custody.

## Decision

- Derive `evaluator_source_sha256()` from the actual bytes of the imported
  `task_templates/tabular_classification/evidence_pilot.py` and
  `learning_governance/core.py`, with the relative path and per-file SHA-256
  digest included in deterministic canonical JSON.
- Verify each imported module resolves to the expected repository file before
  hashing. Require two independent input constraints:
  `expected_evaluator_sha256` passed explicitly to the bridge, and
  `router_packet.evaluator_sha256`. Both must match the observed source-byte
  commitment. The caller is responsible for *trusting* and pinning the expected
  digest; a caller who supplies or alters both packet and expected pin can still
  lie about benchmark performance, labels and execution.
- The bridge rejects malformed policy/evaluation packet objects with
  `BridgeContractError` instead of leaking `AttributeError`.
- Even when evaluation blocks routing, return all negative authority flags.
  Both success and blocked responses explicitly say that external source
  authentication and production readiness are false.

## Non-goals and trust limits

This is a **source consistency** guard, NOT cryptographic authentication of a
reviewer's identity, issuer, independent evaluator or a genuine execution.
It cannot prove the imported source was executed honestly or prevent malicious
callers from forging labels, predictions, feature-use declarations or external
pins. Direct `inspect_router` remains synthetic-only and must never be
connected to deployment/promotion. No production trust is granted.

We deliberately retain the fixed finance baseline in this DRAFT review:
`6bace5fe82ef92393c81d44af714a087e37869d3`. A moving base changes the
meaning of the audited comparison, so subsequent main drift requires a newly
frozen candidate and re-review; production CI can later adopt an owner-approved
dynamic protected-path policy. Existing finance paths and workflow remain
untouched.

## Acceptance and rollback

- Run source-byte spoofing, malformed input and negative-flag regression tests,
  and the entire Factory offline suite on the exact new head.
- Check exact-head GitHub Actions and independent external critique before
  any merge decision. Finance PR #11 is separate and requires combined-tree CI.
- Rollback by closing this draft branch; no main or production state changed.
