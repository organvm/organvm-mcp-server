"""Workspace path resolution.

Resolves canonical paths to ORGANVM data sources. Uses environment
variables when available, falls back to conventional defaults.

Environment variables:
    ORGANVM_WORKSPACE_DIR — workspace root (default: ~/Workspace)
    ORGANVM_CORPUS_DIR — corpus repo (default: <workspace>/meta-organvm/organvm-corpvs-testamentvm)
"""

from __future__ import annotations

import os
from pathlib import Path

# Conventional defaults
_DEFAULT_WORKSPACE = Path.home() / "Workspace"
_DEFAULT_CORPUS_SUBPATH = "meta-organvm/organvm-corpvs-testamentvm"
_DEFAULT_ENGINE_SUBPATH = "meta-organvm/organvm-engine"
_DEFAULT_ORCHESTRATOR_SUBPATH = "organvm-iv-taxis/orchestration-start-here"


def workspace_root() -> Path:
    """Return the workspace root directory."""
    return Path(os.environ.get("ORGANVM_WORKSPACE_DIR", str(_DEFAULT_WORKSPACE)))


def corpus_dir() -> Path:
    """Return the path to organvm-corpvs-testamentvm."""
    env = os.environ.get("ORGANVM_CORPUS_DIR")
    if env:
        return Path(env)
    return workspace_root() / _DEFAULT_CORPUS_SUBPATH


def registry_path() -> Path:
    """Return the path to registry-v2.json."""
    return corpus_dir() / "registry-v2.json"


def event_catalog_path() -> Path:
    """Return the path to event-catalog.yaml."""
    return workspace_root() / _DEFAULT_ORCHESTRATOR_SUBPATH / "docs" / "event-catalog.yaml"


def governance_rules_path() -> Path:
    """Return the path to governance-rules.json."""
    return corpus_dir() / "governance-rules.json"


def engine_dir() -> Path:
    """Return the path to organvm-engine."""
    return workspace_root() / _DEFAULT_ENGINE_SUBPATH


def organ_directories() -> dict[str, Path]:
    """Return mapping of organ keys to their workspace directories.

    Returns:
        Dict like {"ORGAN-I": Path("~/Workspace/organvm-i-theoria"), ...}
    """
    from organvm_engine.git.superproject import ORGAN_DIR_MAP
    
    ws = workspace_root()
    return {
        key: ws / subpath 
        for key, subpath in ORGAN_DIR_MAP.items()
    }
