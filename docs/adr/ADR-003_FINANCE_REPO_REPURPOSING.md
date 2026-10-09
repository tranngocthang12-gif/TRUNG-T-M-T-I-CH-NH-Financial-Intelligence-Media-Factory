# ADR-003 - Repurpose financial repository as Universal ML Factory host

Date: 2026-10-09
Status: OWNER-DIRECTED; IMPLEMENTED AS REVIEW CANDIDATE, NOT MERGED/PRODUCTION
Repository: tranngocthang12-gif/TRUNG-T-M-T-I-CH-NH-Financial-Intelligence-Media-Factory
Observed pre-migration main commit: a55651dd1e2f8eef7625f904a7b55f20272c1b22

## Owner directive

The Owner expressly assigns this financial repository to the Universal ML Factory, asks that useful components be kept, unsuitable concepts be excluded, and the existing architecture be subjected to criticism. This overrides the previous provisional plan to create a separate Factory repository. It does not authorize an investment trade, finance data deletion, public release of private Library knowledge, or silent alteration of Factory Laws 1-26.

## Decision

1. Introduce Factory first-class Charter, Architecture, State, Handoff and core/task contracts in a REVIEW BRANCH; promote them on main only after an accepted PR.
2. Carry over only the previously tested read-only governance reference with exact source digest and 63 inherited offline tests.
3. Implement a synthetic tabular-classification split contract and baseline as the first non-financial task; no new model deployment authority.
4. Disable the old `schedule` trigger and change `contents: write` to `contents: read` in the candidate revision of the former daily workflow. Main remains unchanged prior to merge.
5. Keep preexisting financial files and immutable Owner finance mission/safety policy untouched, classify them as legacy; extract a scoped finance adapter only with later evidence.
6. Create a new read-only CI for Factory tests, no production training, data downloads or financial API calls.

## Critique basis

- The existing `engine/run_cycle.py` mixes finance ingestion, features, backtest, model activation, paper execution and report writing under a global finance config: domain contamination and insufficient adapter separation.
- `engine/knowledge.py` `promote()` and `rank_active()` can mark a model ACTIVE from a SUPPORTED/STRONG/REGIME_SPECIFIC backtest status without independent external approval/heldout deployment acceptance.
- `engine/meta.py` Thompson-sampling bandit rewards an immediately classified backtest status, not independently audited real-world survival; therefore it should not be claimed to learn method effectiveness causally.
- `.github/workflows/daily_cycle.yml` runs scheduled finance operations with repository write permission and performs git push: inappropriate as a generic Factory default.
- `state/PROJECT_STATE.yaml` records unresolved source rights/source quality and a not-yet-signed original finance mission. Existing backtest/Synthetic checks cannot cure that by renaming the project.
- The repo is PUBLIC: migration must not copy private Library/Owner data into the GitHub repository.

## Rejected alternatives

- Graft universal code into old financial `engine/run_cycle.py`: would make cross-domain reuse depend on finance configuration.
- Delete finance engine, datasets or history now: destructive, defeats provenance and rollback.
- Automatically enable local or cloud training or Model Registry promotions because old workflows existed: violates Factory gates.
- Treat review by the same assistant or green CI as independent behavioural proof.

## Migration acceptance / rollback

Candidate can pass only with local deterministic tests, inspection of proposed workflow privileges, independent review and an explicit merge decision. Branch changes are reversible by closing the PR. Default-branch original finance history is preserved by Git; public publication cannot be undone. After merge, CI must report exact commit; migration may still be non-production.

Scope of this ADR excludes repository rename/visibility changes, financial legal or capital policy edits, private source material, and live ML deployment.
