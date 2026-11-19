# B1: raw-price evidence and real-engine bridge (research-only)

**Pinned base:** `432f45681ad8b661e98af4d7046abb9f100c0a1f` (after PR #32).
**Scope:** diagnostics and synthetic test only. No production behavior changes.

## Why this PR is intentionally small

- Two secondary PDFs in the local B1 package cite TCB ex-right **2024-06-20** (HOSE notice 1115/TB-SGDHCM) and VCB **2025-03-12** (notice 359/TB-SGDHCM). Local PDF SHA256:
  - TCB: `ed17a084b7cc7411a5db7bdf2d89407cc3ca672b73f19fbab77c73e009319232`
  - VCB: `2f12a95104e88b1f8ee5f63305687c402d64d78cf287d6131ab51064993be725`
- Neither is the direct authenticated source document from HOSE. The real `data/corporate_actions.csv` instead stores TCB **2024-06-11** and VCB **2025-03-03**, both `CAN_DOI_CHIEU`. Do not infer `DA_KIEM_CHUNG` from a price discontinuity.
- `engine/adjust.py` still allows an unverified event to become `APPLIED` if price-factor math fits. This is **OPEN P1** under Issue #33. A naive gate-only patch would change flags around the known Yahoo discontinuity without reconciling actual source data. Make the source-evidence/correction + gate change as a separate coordinated PR.
- The local B1 mock candidate passed 34/34 tests, but it has **not** been committed to this repository and is not a validated SSI/DNSE integration. This PR uses synthetic `mock_ssi` rows only to test the actual Finance data and adjust code path.

## What is checked

1. `tests/test_b1_engine_bridge.py` builds 285 synthetic trading days per ticker and an isolated temporary corporate-event CSV, then uses the **real** `engine/data.py::save_store`, `load_store`, `load_market`, `engine/adjust.py::build_events` and `factors`. It tests cutoff before/after synthetic split, stable raw bytes, first-observation behavior and no broker credentials.
2. `tools/b1_price_evidence.py` reads actual **first-observation** raw store without writing; prints previous and next observed raw close, `observed_at`, provider and percentage change around both disputed dates. Run in CI logs for audit, or locally as `python tools/b1_price_evidence.py`.
3. Existing `tests/test_adjustment.py` still contains status assertions for the two unverified real events; **this is an explicit known blocker** for the source-gate PR, not a reason to self-promote source status.

## Remaining gates (not satisfied by this PR)

- [ ] Obtain HOSE/VSDC primary notice URLs and original bytes; verify issuer, dates, ratios and SHA256.
- [ ] Compare actual raw discontinuity, provider adjustment history and exchange notice, with an explicit documented explanation for the conflict.
- [ ] Implement explicit allow-list and publication date in the real event contract; reject `CAN_DOI_CHIEU`, unknown announcement date and owner approval alone.
- [ ] Recompute immutable derived versions per ADR-0009, compare flags/labels/features/backtest/paper before vs after, support rollback without changing raw.
- [ ] B1 mock: atomic CSV+sidecar, approved root enforcement and true adapter integration, followed by an independent L-09 review on a pinned GitHub HEAD.
- [ ] Owner L-10 merge. `data.sources=[yahoo]`, `deployment_level=0`. No real credentials or trading.

This PR is **not** the corporate-action fix and must not be represented as completion of Issue #33.
