# ADR-013 — AUTO-08: Port evaluator source consistency to the frozen dual-domain review tree

Date: 2026-10-30
Status: DRAFT REVIEW ONLY — NOT MERGED, OWNER APPROVED OR PRODUCTION READY.

## Frozen references
- Finance canonical main: `6bace5fe82ef92393c81d44af714a087e37869d3`.
- Integrated Finance + Factory PR #14 source: `ad4d145e0cfadb7ad185c9f977956f42d563dd46`.
- Separate Factory PR #15 source: `2b194a9997af3a2a9abbfba88cb79df9ccd5558c`.
- Owner has authorized preparing this review-only integration, **not merge**.

## Decision

Cherry-pick *semantics* of PR #15's evaluator-source binding into PR #14's more hardened synthetic bridge rather than replacing the entire file. Preserve PR #14's 12..64-case bound, malformed-input normalization, negative authority flags, exact finance patch blob pins and blocking dual CI.

The bridge now hashes the actual imported bytes of `task_templates/tabular_classification/evidence_pilot.py` and `learning_governance/core.py` with stable relative file paths, and checks that imported modules resolve to the expected repository files. It compares this source-set digest with both an explicit expected evaluator pin and `router_packet.evaluator_sha256`; the derived receipt carries the observed digest rather than merely echoing the packet. Both blocked and successful results state `evaluator_source_authenticity_proven=False` and no production authority.

The review validator additionally compares the exact proposed delta against frozen PR #14 and still enforces all six Finance PR #11 blob pins and the earlier PR #12/PR #13/PR #14 ancestries. It is self-modifiable, and therefore never a trusted external attestation or a substitute for an Owner-enforced GitHub ruleset.

## Trust and release limitations

This is local **code/bytes consistency**, not proof that code genuinely executed under a trusted evaluator, not a signature from an external issuer, and not proof of legitimate holdout/label provenance. A malicious caller with control over case labels, predictions, `features_used`, integrity counters and caller-side pins can still fabricate an internally consistent packet. Provider latency/cost remain mock values. The synthetic router's proposal must not be used for production, model promotion or deployment.

The Finance `main` branch, ledger, market data, scheduled finance workflows and permissions remain unchanged. Finance full-suite and Factory tests must pass together on the exact new commit; independent reviewer must fetch the **new HEAD**, inspect the complete actual diff and evidence, and reproduce adversarial tests. No CI result can sign off on itself.

## Acceptance / rollback

Require:
1. Exact-head Factory contract/adversarial suite PASS.
2. Exact-head blocking finance + Factory full pytest suite PASS and proof tests did not modify finance worktree.
3. Baseline/finance blob/PR14 delta guard PASS.
4. Independent adversarial report (P0/P1/P2, source refs and reproductions); address material findings.
5. Separate Owner decision about repository branch protection, migration and merge.

Until gates 4/5: `REVISE_AND_REVIEW`, `HOLD_MERGE`, `production_ready=false`.
Rollback: close this review-only branch and draft PR; frozen PR #14 and finance main are unaffected.
