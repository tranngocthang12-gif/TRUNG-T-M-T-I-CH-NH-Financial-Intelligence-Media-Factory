# ADR-008 — AUTO-05A: reconcile finance main and Universal ML Factory review candidate

Date: 2026-10-30
Status: OWNER AUTHORIZED RECONCILIATION WORK; **REVIEW CANDIDATE ONLY**
Base main (observed): `6bace5fe82ef92393c81d44af714a087e37869d3`
Prior Factory stack: #2 -> #5 -> #6 -> #7; head `a67d0e03fff4aedcbdd71a2d59fec24ebc13fbe2`.

## Decision: coexistence on a review branch, no competing canonical authority

The Owner authorized AUTO-05A, AUTO-05B and AUTO-05C **in order**. That
approves preparing and validating a reconciled *review candidate*, not merging
code to `main`, changing the established finance mission, or operating
the finance engine or live provider APIs.

The financial repository's checked-out `main` continues to use
`BOOT.md`, `architecture/ARCHITECTURE.md` (v3.0), `governance/LAWS.md`
(L-07), `governance/OWNER_MISSION.md`, `governance/SAFETY_STATE.yaml`,
`governance/GOVERNOR_POLICY.yaml`, and its scheduled financial workflows.
The finance v3.0 document itself says DRAFT; presence on main is a repository
observation, **not** proof of authenticated Owner approval.

The earlier Factory migration #2 would replace the root `BOOT.md` and
disable `.github/workflows/daily_cycle.yml`; do NOT merge that old branch
onto the changed finance `main`. It also adds a second root
`ARCHITECTURE.md` in tension with finance law L-07.

On this new branch, carry only domain-neutral, read-only Factory code and
tests in new, non-colliding packages; place all Factory design/state/handoff
and ADRs under **`factory_review/`**, expressly subordinate to the
existing repository architecture for purposes of review. No new root
`ARCHITECTURE.md`, `PROJECT_STATE.json`, `BOOT.md` or governance authority.
No changes to finance `engine/`, `contracts/`, `state/`, `ledger/`,
`governance/`, `architecture/`, `reports/`, `data/`, scheduled workflows
or historical Owner files.

## Reconciliation matrix

| Element | On finance main | On Factory review branch | Gate |
| --- | --- | --- | --- |
| Bootstrap | root `BOOT.md` | **unchanged** | protected diff + finance validation |
| Canonical architecture | `architecture/ARCHITECTURE.md` and L-07 | **unchanged**, Factory design only under `factory_review/` | no dual canonical |
| Finance scheduled execution | `.github/workflows/daily_cycle.yml` schedule + write | **unchanged in review branch** | never execute from Factory CI |
| Ledger intake | `.github/workflows/ledger_intake.yml` | **unchanged** | finance regression |
| Finance Owner/financial risk | `governance/` and `engine/` | **unchanged** | protect authority/rights |
| Universal reference code | not yet deployed | `learning_governance/`, `task_templates/`, `capability_contracts/` | synthetic, no promotion |
| Factory evidence handoff | not implemented | optional `factory_review/evidence_bridge.py` | source and packet pins, fake receipt controls |
| Tests | finance suite | finance suite + Factory suite + cross-stage tests | exact-head dual CI |
| Future merge | Owner decision | **blocked** until independent review, source rights and explicit migration decision | never self-approve |

## Boundaries and alternatives

- Protect the original finance mission, data, ledger and schedules; merely
  sharing a Git repository does not give the Factory permission to run them.
- Existing scheduled finance jobs still run on finance `main` unless the
  Owner separately changes them; this project does not quietly disable them.
- The finance and Factory topologies remain logically distinct. A possible
  future Owner decision may keep them in separate repositories or use an
  explicitly isolated Factory package in this repository; neither is
  irrevocably selected here.
- Reject cherry-picking the entire old migration PR #2 and treating a clean
  Git merge as architecture reconciliation.
- Reject a second universal orchestrator or governance authority.
- Keep published Project Library files, personal data, capital profiles and
  secrets out of this **public** repository.

## Evidence, rollback and review gate

At the start of AUTO-05A, `main` and the old Factory full candidate diverged:
20 finance commits vs 18 candidate commits since the observed old base.
The same-file overlap was root `BOOT.md`; semantic conflicts extend to
architecture paths, tests and scheduled workflows.

This ADR is a proposed reconciliation implementation, not accepted finance
law, Factory canonical state, or authenticated independent critic review.
Closing this review PR or deleting this review branch leaves `main` intact.
Prior Factory draft PRs #2, #4, #5, #6, #7 remain untouched.

**Stop gate:** no merge into `main` without explicit Owner approval after
cross-system tests and a genuinely independent exact-commit review.
