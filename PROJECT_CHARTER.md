# Universal ML Factory - Project Charter

Status: OWNER-DIRECTED REPOSITORY REPURPOSING; candidate until reviewed merge.
Owner directive date: 2026-10-09.
Mission: build one reusable machine-learning factory, not a separate custom model or codebase for each domain.

## Product contract

The ordinary user configuration describes `problem`, `data`, `target`, `metrics`, `constraints`, `deployment`, and `retraining`. New problems should usually require only a Task Template and Domain Configuration. The central factory must support problem definition, data contracts, leakage-safe validation and representation, baseline, training, evaluation, error analysis, selection, packaging, monitored deployment and governed retraining.

## Precedence

1. Human Owner mission, irreversible decisions, permissions and Supreme Architecture Laws 1-26 (kept in the Project's Library until repository migration is accepted).
2. Explicit Owner-approved ADRs and accepted project state.
3. This Charter, repository Architecture, Task Contracts and adapter contracts.
4. Execution plans, proposals and AI/LLM outputs.

Material architecture changes require an ADR and a validated checkpoint. No software may self-grant authority. An agent's account name, a passing test, or a CI green badge is not an authenticated human acceptance.

## Hard architecture

- Problem first; data contract before training; prevent leakage by construction.
- Baseline before complex model; holdout data frozen and isolated.
- Version datasets, experiment specs, code, metrics, models and deployed artifacts.
- Keep domain facts and provider knowledge in scoped, versioned adapters.
- No automatic knowledge promotion, model activation, release, or retraining solely because a metric passed.
- Use review eligibility, approval and deployment readiness as different states.
- Protect unrelated domains from automatic invalidation or finance-specific rules.
- The smallest coherent architecture wins; no independent agent council or duplicate governance stack.

## Financial system preservation boundary

The Owner assigned the preexisting Financial Intelligence & Media Factory repository to host this new Factory. Its financial-specific mission, investment guards, paper trading state, datasets and research history remain preserved as legacy material. They are NOT an authorization for a new universal system to spend money, perform live trades, publish, or run scheduled retraining. The original financial Owner mission and safety state are not modified by this migration.

A proposed cleanup must distinguish reusable patterns, finance adapters, historical data, and independently authorized deletion. History is not discarded merely because a file is not part of the universal core.

## Release truth

This branch is an offline reference integration with synthetic checks only. The existence of source code and passing unit tests does not establish production operation, semantic understanding, independent external critique, real-data performance or a safe live deployment.
