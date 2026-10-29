# ADR-005: Bounded provider-neutral Capability Contracts and offline mocks

Date: 2026-10-30
Status: **CANDIDATE / NOT MERGED / NOT PRODUCTION**
Scope: Universal ML Factory migration branch only, not the legacy finance `main` runtime.

## Context and decision

The Factory charter requires replacement of model/framework/cloud providers through
adapters, with stable Universal Core boundaries. Claude Skills, Gemini structured
outputs, Grok reasoning controls and GPT bounded decisions provide useful design ideas,
but copying four distinct orchestrators would violate the smallest-coherent-core rule.

Add one optional `capability_contracts` package with a versioned, provider-neutral
request/result JSON Schema (`contract_v1.schema.json`), a dependency-free fail-closed
Python validator and four deterministic mock adapter identities: `mock-claude`,
`mock-gemini`, `mock-grok`, `mock-gpt`. All run the same local evaluator and cannot
call real providers. The contract demonstrates the interface, **not** provider parity.

The only allowed capabilities in v1 are `validate_data`, `analyze_errors`, and
`inspect_experiment`. The last action inspects declared metadata; it is not
independent experimental review. All tasks are explicitly offline, must declare
`data_role` as `SYNTHETIC` or `TRAINING` (no holdout/production), and forbid network,
mutation and paid API usage. Inputs are bounded by bytes, record count and depth.
Results are labeled `SIMULATED_ONLY`, bound to canonical request/output SHA-256
and carry non-negotiable zero-call, zero-cost and false-authority receipts.

A SHA-256 comparison proves byte consistency, not the identity or reliability of a
provider or the correctness of a model's judgment. The self-declared input data
roles are NOT an independently enforced dataset-access boundary: a future runtime
must establish trusted data authorization separately.

## Placement and responsibilities

- `capability_contracts/core.py`: offline wire validation and deterministic mock run.
- `capability_contracts/contract_v1.schema.json`: language-neutral request/result spec.
- `tests/test_factory_capabilities.py`: synthetic positive/negative cases.
- **Not added:** provider SDKs, routing decisions, new orchestrator, knowledge store,
  self-approval, release authority, model registry, dataset ingestion or retraining.

This package is an optional interface prototype. The existing
`learning_governance` remains the only bounded review reference, and the
Task Template remains responsible for leakage controls and heldout evaluations.
The finance-specific `contracts/` directory is deliberately not modified.

## Acceptance tests and gates

1. Four provider-labelled mocks produce identical deterministic results for all
   declared capabilities; no claims are made about actual vendor performance.
2. Reject malformed version/JSON, unauthorized capabilities, holdout/production
   data roles, network/mutation/cost, duplicate/malformed cases, poisoned/nonfinite
   payloads, oversized input and fabricated model promotion/approval receipts.
3. Run `python -m unittest discover -s tests -p 'test_factory_*.py' -v` and
   `python tools/validate_factory.py` on the exact target branch when available.
4. Require independent exact-commit review, schema/runtime conformance and a
   later authorized real-data evaluation before any live provider adapter.

No synthetic test, CI PASS or PR merge alone grants authority to use real data,
call APIs, change existing model states, deploy, spend or enable retraining.

## Alternatives rejected

- Four vendor-specific core subsystems: coupling and redundant governance.
- Calling APIs in a contract proof: would introduce secrets, spend and network risk.
- Reusing finance `contracts/` as generic Factory authority: domain contamination.
- Reusing a model's memory or structured output as canonical verified knowledge.

## Reversal and relation to open migration

Close/revert this candidate PR, remove these optional files; no `main` or
production state is mutated. Factory migration PR #2 remains DRAFT and requires
its separate main reconciliation and Owner review; this ADR does not approve it.
A later implementation must compare the exact candidate head against evolving
finance `main` before the Owner decides whether to merge the migration.

## Candidate audit amendment - mock provider label confusion

An adversarial test found that the initial receipt validator accepted a
mock-claude result re-labelled as mock-gpt. The boundary now requires
`expected_provider_id` supplied separately from the trusted invocation context
and blocks a mismatch or absent context. This guards mock-context consistency,
not the authenticity of any real provider. No API or production authority added.
