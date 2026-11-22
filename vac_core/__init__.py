"""VAC authorization core: explicit, fail-closed data access decisions."""
from .engine import Grant, Decision, evaluate
__all__ = ["Grant", "Decision", "evaluate"]
