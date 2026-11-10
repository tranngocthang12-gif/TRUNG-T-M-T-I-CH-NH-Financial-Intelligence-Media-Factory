# ADR-012 — AUTO-07B: bounded R3 contract hardening without trust-root escalation

Date: 2026-10-30
Status: DRAFT REVIEW CANDIDATE; not merged or Owner-approved.
Frozen integration parent: PR #13 `b1a9012ff55c916d53183c44b52cf503f3222fbb`.
Financial canonical main: `6bace5fe82ef92393c81d44af714a087e37869d3`.

## Decision

1. Restrict the combined synthetic A -> B -> C mock bridge to 12..64 cases (the A adapter limit). The standalone B pilot and C router may accept up to 128, but that does **not** imply the combined chain can. Reject malformed policy objects, request contexts and non-text case IDs with `BridgeContractError`.
2. Return explicit negative authority/provenance fields on **both** blocked and successful synthetic branches. A declared evaluator digest or matching caller-provided hash never authenticates real execution. Deliberately do **not** reject 100% synthetic accuracy merely because it is 100%; such a heuristic is not a leakage proof.
3. On the **review-only** Factory CI, pin the OS runner to `ubuntu-24.04`, record Python and installed dependency versions (not a lock), and fail if tests alter tracked **or untracked** finance-related files. Keep full-suite `pytest tests` blocking. Preserve the six Finance PR #11 blob IDs unchanged.
4. Extend the scope validator to compare against frozen PR #13 and require the eight named AUTO-07B modifications. This prevents accidental unrelated changes and supports exact-source review; it does **not** turn a self-modifiable PR script/workflow into an authenticated independent trust root.
5. Record the **verified PR #13 parent** CI (173 Factory tests; 185 pytest + 38 subtests) separately from the **new AUTO-07B head**, whose exact-head CI and independent review start PENDING until actually observed.

## Explicit unresolved gates

- **Owner-controlled repository ruleset:** GitHub API showed `main.protected=false`, no ruleset and no enforceable required checks. Owner must select an enforceable trusted workflow, required checks and independent approval; a branch-authored validator alone is insufficient. Do not globally require the existing frozen-base validator for unrelated PRs: it is scoped to this integration snapshot and would block unrelated work.
- **External provenance:** The synthetic receipts, `evaluator_sha256`, features-used and claimed integrity are caller-controlled. No authenticated label custody/holdout, evaluator attestation, real provider identity or production promotion is implemented. All results remain `SIMULATED_ONLY` or synthetic proposals.
- **Finance compatibility:** Legacy `requirements.txt` remains unpinned, and the old `tests.yml` full-suite remains informational. Both require a separately Owner-scoped finance runtime/release decision. The version-log CI step is not a replacement for a dependency lock.
- **Evidence custody:** Reviewer must read actual new SHA, changed files and CI job logs or independently reproduce, not trust this ADR or Builder's summary. There is no GitHub PR review or Owner merge approval in this ADR.
- The existing scheduled `daily_cycle.yml` remains unchanged; new Factory work conveys no trading, publishing, paid API, model deployment or retraining permission.

## Minimum Owner action (separate from this draft)

1. GitHub Settings -> Rules -> Rulesets: establish an active `main` ruleset requiring PR review and status checks from trusted workflows that run for every relevant PR, block force-push/deletion, define bypass policy and review signed commits. Verify the rule is active from GitHub API/settings.
2. Obtain independent exact-new-SHA review of AUTO-07B and review each changed blob, including the guard and workflow. Reopen/fix any material P1 findings.
3. Only after these gates may Owner separately decide if and how the Factory is migrated. No automatic merge is authorized.

Rollback: close the AUTO-07B Draft PR/branch. Frozen PR #13, Finance PR #11 and canonical finance `main` stay unchanged.
