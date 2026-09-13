"""AdCopilot Sprint 3 baseline: synthetic data + deterministic CPA diagnosis."""

from adcopilot.engine import baseline_cpc_cvr, diagnose
from adcopilot.generate import SCENARIOS, generate_campaign

__all__ = ["baseline_cpc_cvr", "diagnose", "generate_campaign", "SCENARIOS"]
__version__ = "0.1.0"
