# UNIVERSAL ML FACTORY - Controlled Migration Candidate

**Mission:** one reusable machine-learning factory: Universal Core -> Task Template -> Domain Configuration. The Owner assigned this existing Financial Intelligence & Media Factory repository as the intended new home on 2026-10-09. This proposal remains on a separate branch until review; it does not assert that the main branch is already migrated.

Start with `PROJECT_CHARTER.md`, then `PROJECT_STATE.json`, `ARCHITECTURE.md`, `PROJECT_HANDOFF.json` and `docs/adr/ADR-003_FINANCE_REPO_REPURPOSING.md`.

## First runnable slice

- `learning_governance/`: pure Python read-only knowledge evidence/dependency/promotion-inspection/model-comparison/critic-canary code, carried with the exact original Factory v0.1 source digest.
- `task_templates/tabular_classification/`: isolated holdout and leakage contract, plus a majority-class training-only baseline. This task template does not implement a trainable ML model or real-data evaluation.
- `.github/workflows/factory_ci.yml`: checks the new Factory contracts without credentials, external calls or write permissions.

Run locally:

```sh
python tools/validate_factory.py
python -m unittest discover -s tests -p 'test_factory_*.py' -v
```

The tests are synthetic, and CI is not an acceptance or production gate. No automatic retraining, knowledge promotion or deployment is enabled.

## Historical financial project

The former repository name, legacy financial engine, datasets, reports and finance governance files remain here for audit and controlled adapter extraction. They do not define the new Universal Core. The legacy daily job is proposed to become a manual, non-writing stub after this PR merges; existing default-branch scheduling continues until then. See `legacy/README.md`.

**Caution:** this repository is public. Do not commit confidential finance data, Library artifacts, credentials or personal Owner profile materials. A future private-repository decision requires the Owner and cannot undo prior public exposure.
