"""Read-only Learning Governance Core reference implementation."""
from .core import (
    SCHEMA, STATES, digest, validate_record, check_dependency_closure,
    invalidation_impact, check_scope, inspect_promotion,
    compare_parent_candidate, canary_truth_digest, score_critic_canary,
)

__all__ = [
    "SCHEMA", "STATES", "digest", "validate_record", "check_dependency_closure",
    "invalidation_impact", "check_scope", "inspect_promotion",
    "compare_parent_candidate", "canary_truth_digest", "score_critic_canary",
]
