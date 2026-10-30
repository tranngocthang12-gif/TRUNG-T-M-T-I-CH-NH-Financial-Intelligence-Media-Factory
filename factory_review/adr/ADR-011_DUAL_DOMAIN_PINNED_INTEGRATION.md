# ADR-011 — P1 dual-domain reconciliation with pinned finance fixes

Date: 2026-10-30
Status: DRAFT REVIEW CANDIDATE; NO MAIN MERGE OR OWNER ACCEPTANCE.
Finance baseline: \`6bace5fe82ef92393c81d44af714a087e37869d3\`.
Factory source: PR #12 exact HEAD \`9140ee4e97c46dcc1c3523324997af20f3b4e070\`.
Finance fix source: PR #11 exact HEAD \`52972ff9e55dbe3e1c9c16f88a04fb52266cf8db\`.

## Decision

Build one **noncanonical, read-only integration review branch** from the exact
Factory PR #12 HEAD. Overlay only the six exact Git blobs changed in Finance
PR #11. No independent reimplementation or unreviewed financial-engine patch.

The branch's validator checks both source ancestries and two full Git diffs:
(1) against frozen finance main it permits only the explicit Factory additions
plus the six Finance P1 paths with exact A/M status; (2) against Factory PR #12
it permits only the six Finance P1 changes and named audit/CI/state changes.
For each finance path, it verifies the immutable PR #11 Git blob ID and regular
file mode. No broader \`engine/\`, \`tests/\`, dependency or workflow exception.

The Factory integration CI must require both the synthetic suite and the
**entire** finance + Factory pytest suite. The latter must **not** use
\`continue-on-error\`; existing finance law, Ledger, lookahead, and validation
checks stay separately required. The Finance P1 workflow is also carried
verbatim, read-only, from PR #11.

## Reason / review risks

The original Factory PR #12 fail-closed allowlist correctly denied even
legitimate Finance P1 changes. A blanket exception would hide malicious
changes; pinning the six source blobs preserves the review boundary. Source
pins do not prove an independent reviewer, true dataset labels, or production
performance. This branch does not change finance scheduling, spending, Owner
mission, root BOOT, canonical \`architecture/ARCHITECTURE.md\`, laws, model
registry, deployment, monitoring, or retraining.

The finance tests in PR #11 use subprocess isolation for legacy scripts to
avoid import-time shared state. This passes their own CI but is not a proof
of all runtime behavior or compatibility under every future dependency
version. Python 3.12 / current declared requirements is only one environment.

## Gates / rollback

1. Exact integrated HEAD must pass both **blocking** CI jobs; verify job
   conclusions and logs, not only the workflow badge.
2. A genuinely independent critic must inspect exact commit, the two source
   SHAs, code changes, test isolation, diff guard, and custody limitations;
   review outcome must be recorded as PASS/FAIL/INDETERMINATE.
3. Only Owner may separately authorize a future main merge and decide
   whether Factory remains isolated in the financial repository.
4. Production adapters, financial execution, paid APIs, model activation,
   retraining and release remain blocked.

Rollback: close this Draft PR / delete the temporary integration branch.
Source PRs #9, #11, #12 and financial main remain intact.
