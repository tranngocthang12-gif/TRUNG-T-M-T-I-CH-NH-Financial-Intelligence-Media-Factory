# ADR-002: Bounded import of validated governance mechanisms

Date: 2026-10-09
Project: UNIVERSAL ML FACTORY
Decision status: OWNER-AUTHORIZED IMPLEMENTATION; REFERENCE CODE OFFLINE TESTED
Owner directive: Approves adapting established, tested MINH TRI mechanisms to Factory Learning Governance Core, excludes organizational duplication and unmerged Draft PR mechanisms; delegates routine implementation decisions to AUTO.
Authority: This ADR does not amend Supreme Architecture Laws 1-26 or ADR-001.

## Context and sources

The Factory's known durable records (Library `/UNIVERSAL_ML_FACTORY`) include `ARCHITECTURE_SUPREME_LAWS.md` and `PROJECT_STATE.json` (2026-09-28), and ADR-001. A separate Charter, architecture blueprint, handoff, or Factory GitHub runtime repository was not found at the start of this implementation. Thus the deliverable is an original offline reference implementation, not a production integration.

MINH TRI primary merged `main` references reviewed on 2026-10-09:

- `src/minhtri/knowledge_fast_lane.py`: bounded knowledge record validation and prohibition on self-VERIFIED promotion.
- `src/minhtri/semantic_guard.py`: pinned, stale, missing and ambiguous semantic dependencies.
- `src/minhtri/critic_canary.py`: offline critic scoring, canary controls, false-acceptance and subtle-error detection.
- `src/minhtri/evolution.py`: frozen parent/challenger metrics, no automatic promotion.
- `state/current.yaml` and `docs/vnext/FOUNDATION_LAW_CONSOLIDATED_V1_20261006.md`: active auto-learning/auto-critique/meta-learning runtimes disabled; autonomous acceptance forbidden.
- `docs/critic/LEARN_CRITIC_01_20261005.md`: existing concerns with provenance eligibility, weak canary N, and learning claims.

Source repository: https://github.com/tranngocthang12-gif/minh-tri-universal-intelligence-os

Excluded from import: unmerged MINH TRI PR #333 Learning Loop V1, PR #335 Meaning Fidelity Guard; autonomous/meta-learning behavior, GitHub authority/ledger/seat organization, domain Buddhist/economics records, and unaudited resolution statistics.

## Decision

Create the smallest provider-neutral, task-neutral Learning Governance Core, as read-only pure Python functions with no external dependencies:

1. Validate versioned knowledge records, evidence descriptors, and scoped applicability.
2. Evaluate exact pinned transitive dependencies; reject missing, stale, disputed/superseded or cyclic relationships.
3. Compute the minimal affected-knowledge set when a source/adapter changes; report changes rather than mutating state.
4. Inspect evidence-bound promotion proposals: source bytes must match recorded hashes; preregistered heldout/baseline evaluation and separate reviewer must reference the exact candidate. The function emits **review eligibility**, never an acceptance/promotion.
5. Compare parent vs challenger on identical frozen evaluation contracts and declared task metrics, disallow any regressed metric or critical integrity failure.
6. Assess a critic with a preregistered, frozen, single-use canary; enforce minimum sample counts plus one-sided Wilson uncertainty bounds; never interpret a synthetic test PASS as general critic reliability.

Design location: `learning_governance/core.py`, with `tests/test_governance.py`.
Domain-specific ML metrics and leakage definitions remain with task templates/adapters; the core only consumes frozen contracts/results.

## Explicit invariant and limits

- Read-only: no database or GitHub writes, no file writing, no provider calls, no scheduler or background execution.
- No automatic `CURRENT` or `VERIFIED` promotion, deployment, retraining, or model release.
- Source digest validates supplied bytes, not their independent authenticity.
- Distinct reviewer names do not prove provider identity or epistemic independence.
- Review/evaluation receipts remain unverified declarations until verified by a trusted external acceptance system.
- Unit-test PASS validates only the declared code contracts; not real-world learning, comprehension, critique, statistical effectiveness, or production safety.
- No migration of MINH TRI private material, proprietary corpus, or code; implementation is original and bounded to patterns already present on public merged main.

## Acceptance criteria for this bounded step

- All offline deterministic tests PASS.
- Tabular classification, forecasting and image-classification scoped records work without changing the core.
- No automatic mutation or promotion outputs exist.
- Source provenance, exact-version scope, stale-dependency, material-critic, canary-N, and regression negative cases are covered.

## Deferred integration gates

1. Resolve the Factory's actual production runtime repository and complete Charter/Architecture/Handoff canonical routing.
2. Define a Task Adapter contract for real held-out evaluation, leakage checks, and metric costs; connect the reference code to an authorized runtime only through a reviewed adapter.
3. Run adversarial review on exact code/package hash and separate real-data validation of reviewer/source provenance.
4. Define trusted approval authority, persistence, audit, rollback and CI enforcement outside this read-only reference code.
5. Owner approval is required for Supreme Law changes, autonomous durable mutation, automatic promotion, and external production deployment.

## Rejected alternatives

- Copy MINH TRI's complete organization, owner ledger, GitHub/seat authority stack: too much coupling and governance proliferation.
- Port PR #333/#335 as accepted functionality: they are Draft, unmerged and self-declare unproven semantic understanding.
- Auto-enable research, critic, meta-learning or model retraining: violates evidence and owner-gate principles.
- Promote based on synthetic unit tests or review votes: confuses structural validation with proven knowledge.
