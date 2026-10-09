"""Task-local tabular classification baseline; intentionally no ML provider dependence."""
from .contract import ContractError, freeze_rows, validate_split, majority_baseline
__all__ = ["ContractError", "freeze_rows", "validate_split", "majority_baseline"]
