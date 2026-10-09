# AUTO-02 - Adversarial review of inherited Financial Intelligence & Media Factory

Observed main: `a55651dd1e2f8eef7625f904a7b55f20272c1b22` (2026-10-09 review). Findings are grounded in main-branch files, not a claim about actual runtime success or business results.

| Priority | Finding | Evidence path | Consequence | Treatment |
|---|---|---|---|---|
| P0 | Daily scheduled workflow grants `contents: write` and auto-commits output | `.github/workflows/daily_cycle.yml` | Without explicit migration gate, finance-specific writes persist | Candidate replaces with safe manual stub; existing main unaffected until merge |
| P0 | Model activation conflated with backtest strength | `engine/knowledge.py:promote`, `rank_active`; `engine/run_cycle.py` | Model may become ACTIVE without external acceptance or sealed final holdout | Exclude from Factory activation; gated comparator produces proposal only |
| P0 | Financial domain governs the supposed ML core | `engine/run_cycle.py`, `engine/config.py`, `config.yaml` | Cannot change problem by configuration alone | Introduce Universal Core and Task Template boundaries |
| P1 | Meta-learning reward is not long-term method survival | `engine/meta.py:REWARD`, `update` | Adaptive exploration can amplify backtest selection bias | Exclude from universal meta-learning until longitudinal, audited trial |
| P1 | Out-of-sample rolling tests can be reused in adaptive search | `engine/research.py:walk_forward`; `run_cycle.py` | Repeated exploration does not equal an untouched final holdout | Add frozen packet and independent challenger evaluation |
| P1 | Source and data quality still contain critical uncertainties | `state/PROJECT_STATE.yaml`, `data/derived/quality_flags.csv`, `config.yaml` | Yahoo price adjustment, survivorship and point-in-time limitations constrain claims | Data Adapter and task-specific provenance/data validation; no universal import |
| P1 | Loading model pickle assumes trusted execution provenance | `engine/knowledge.py:live_predict` calls `joblib.load` | Unsafe on untrusted artifacts | Defer to controlled Registry loader with provenance verification |
| P1 | Existing finance Owner mission and financial safety are not portable permissions | `governance/OWNER_MISSION.md`, `SAFETY_STATE.yaml` | Silent reuse of financial policies in unrelated domains | Keep immutable history, isolate finance adapter governance |
| P1 | PUBLIC repo can leak owner/private evidence if migration copies the Library | GitHub repository metadata | Irreversible public disclosure even if visibility later changes | Publish no private Library, identities, personal data, secrets or corpora |
| P2 | Validator is coupled to planned finance artifacts | `tools/validate.py` | A finance-specific check would block unrelated ML tasks | Keep legacy validator untouched; add Factory-specific read-only validator |

## What survives the criticism

Point-in-time feature/label availability checks, data-quality fail-closed decisions, deterministic scored predictions, backtests and baseline comparisons, experiment versioning and decay monitoring are useful patterns. Keep them task-local or in interface contracts after separating domain assumptions. Do not copy finance's specific thresholds, expected profits, paper execution or financial reward metrics into Universal Core.

## Adversarial self-check of this migration

- Current Factory tests are synthetic and built by the same implementing assistant; a true independent critic is not yet attached.
- Group and temporal split validation do not establish semantic target leakage, real-source provenance, entity deduplication, label policy or correct business metric.
- The first baseline predicts only the training majority class and is not a trained deployable ML model.
- A scheduled finance workflow on main remains active until merge or separate authorized disablement. No one should infer it is already stopped.
- The first branch still carries historical finance directories. Removing them without validated extract/owner approval would be premature.
- The Owner's reuse of an existing PUBLIC repository does not explicitly authorize moving private source material to it.

## Next tests required before claiming actual Factory operation

1. Independent exact-commit source/critic review with recorded findings and resolutions.
2. Trusted real tabular data contract, labelled holdout, group/temporal leakage inspection and baseline/challenger metrics.
3. Migration CI running on branch/PR without finance scheduler writes and without external secrets.
4. Reviewed finance adapter extraction and versioned dataset quarantine.
5. Independent acceptance, registry/deployment/monitoring/retraining gates and a rollback drill.
