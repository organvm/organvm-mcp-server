"""Prompting standards tools — provider guidelines for multi-agent work."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any


def prompting_guidelines(agent: str = "claude") -> dict[str, Any]:
    """Get agent-specific prompting guidelines."""
    from organvm_engine.prompting.loader import load_guidelines

    guidelines = load_guidelines(agent)
    if guidelines is None:
        return {"error": f"No guidelines found for agent '{agent}'"}
    return asdict(guidelines)


def prompting_all() -> dict[str, Any]:
    """Get all provider guidelines."""
    from organvm_engine.prompting.standards import PROVIDER_GUIDELINES

    return {
        "providers": {key: asdict(g) for key, g in PROVIDER_GUIDELINES.items()},
        "total": len(PROVIDER_GUIDELINES),
    }
