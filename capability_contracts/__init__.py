"""Bounded, offline-only Universal Capability Contracts for Factory review."""
from .core import (
    CAPABILITIES, PROVIDERS, REQUEST_SCHEMA, RESULT_SCHEMA,
    CapabilityContractError, MockCapabilityAdapter,
    make_mock_adapters, validate_mock_result, validate_request,
)

__all__ = [
    "CAPABILITIES", "PROVIDERS", "REQUEST_SCHEMA", "RESULT_SCHEMA",
    "CapabilityContractError", "MockCapabilityAdapter",
    "make_mock_adapters", "validate_mock_result", "validate_request",
]
