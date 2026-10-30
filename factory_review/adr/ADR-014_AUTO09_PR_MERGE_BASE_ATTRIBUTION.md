# ADR-014 — AUTO-09: attribute only PR-owned changes when main advances

Date: 2026-10-30
Status: DRAFT, REVIEW ONLY — HOLD MERGE. Neither an Owner acceptance nor an external critic signature.

## Context and frozen lineage

- Canonical finance anchor: `6bace5fe82ef92393c81d44af714a087e37869d3` (not permission to modify `main`).
- PR #16 / AUTO-08 frozen reviewed source: `e1e2e97ab851966c65072ad643f24273daf4826d`.
- The AUTO-09 branch starts at exactly that AUTO-08 commit. Its additions must stay separately reviewable.
- A fixed historical baseline is still needed for lineage and finance blob custody, but the change attributed to a review branch must reflect the current PR merge-base.

## Decision

The integration guard computes `git merge-base refs/remotes/origin/main HEAD` and audits
`git diff --name-status --no-renames <merge-base> HEAD` against the exact Finance/Factory
allowlist. It fails closed when `main` is inaccessible, when the frozen finance anchor is
no longer an ancestor of `main` or merge-base, or when the proposed review delta is
unapproved. Finance PR #11 file modes and exact blob pins, PR #12/#13/#14 lineage,
and the frozen AUTO-08 source SHA remain separate checks. AUTO-09 additionally has
its own exact path/status delta against the frozen AUTO-08 source.

The deterministic local Git regression makes a review branch, then advances `main`
with an unrelated data commit. A direct two-tip diff incorrectly shows main-only
data as a deletion; the merge-base diff shows only the PR-owned addition. A follow-on
unapproved source file on the review branch still appears in the diff and fails.
A missing frozen anchor is denied. The review workflow includes AUTO-09 push events.

## Security boundary and open issues

A merge-base comparison assigns *change responsibility*, not approval of new changes
already merged into `main`. Those commits require their own review. A git check executed
from the mutable candidate is not a trusted root; changes to this validator or workflow
require external audit and enforced repository rulesets. Neither this check nor the
evaluator-source byte digest attests to actual evaluator execution, label/holdout custody,
issuer identity, model usefulness, or provider authenticity. Synthetic metrics and mock
provider IDs MUST NOT be promoted to real deployment, financial operation, learning
authority or external review acceptance.

## Required acceptance

1. Validate the **exact new AUTO-09 SHA** with full Factory and finance regression CI.
2. Verify this patch's delta against `e1e2e97...`, and all six Finance PR #11 exact blobs.
3. Independent adversarial re-review of the complete new source and logs.
4. Owner-governed ruleset and separate merge decision. No auto-merge or deployment.

Until all gates are satisfied: `HOLD_MERGE`, `production_ready=false`,
`independent_critic_proven=false`; rollback by closing the draft AUTO-09 PR
without affecting frozen PR #16 or `main`.
