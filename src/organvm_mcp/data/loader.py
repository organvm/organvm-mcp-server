"""Data loaders — wraps organvm-engine and reads raw data sources.

Loads and caches:
- registry-v2.json (via organvm_engine.registry.loader)
- seed.yaml files (via organvm_engine.seed.discover)
- event-catalog.yaml (direct YAML parse)
- governance-rules.json (direct JSON parse)

All loaders cache on first call. Call reload() to force refresh.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from organvm_mcp.data.paths import (
    event_catalog_path,
    governance_rules_path,
    registry_path,
    workspace_root,
)

# Module-level caches
_registry_cache: dict | None = None
_seeds_cache: list[dict] | None = None
_event_catalog_cache: list[dict] | None = None
_governance_rules_cache: dict | None = None


def load_registry() -> dict:
    """Load and cache registry-v2.json.

    Returns:
        Full registry dict with organ keys as top-level keys.
    """
    global _registry_cache
    if _registry_cache is None:
        _registry_cache = _read_json(registry_path())
    return _registry_cache


def load_all_seeds() -> list[dict]:
    """Discover and load all seed.yaml files in the workspace.

    Returns:
        List of parsed seed.yaml dicts, one per repo.
    """
    global _seeds_cache
    if _seeds_cache is None:
        _seeds_cache = _discover_seeds(workspace_root())
    return _seeds_cache


def load_event_catalog() -> list[dict]:
    """Load and cache event-catalog.yaml.

    Returns:
        List of event definitions.
    """
    global _event_catalog_cache
    if _event_catalog_cache is None:
        path = event_catalog_path()
        if path.exists():
            with path.open() as f:
                data = yaml.safe_load(f)
            _event_catalog_cache = data.get("events", []) if isinstance(data, dict) else []
        else:
            _event_catalog_cache = []
    return _event_catalog_cache


def load_governance_rules() -> dict:
    """Load and cache governance-rules.json.

    Returns:
        Governance rules dict with allowed_edges, forbidden_edges, etc.
    """
    global _governance_rules_cache
    if _governance_rules_cache is None:
        path = governance_rules_path()
        _governance_rules_cache = _read_json(path) if path.exists() else {}
    return _governance_rules_cache


def reload() -> None:
    """Clear all caches, forcing fresh reads on next access."""
    global _registry_cache, _seeds_cache, _event_catalog_cache, _governance_rules_cache
    _registry_cache = None
    _seeds_cache = None
    _event_catalog_cache = None
    _governance_rules_cache = None


def _read_json(path: Path) -> dict:
    """Read and parse a JSON file."""
    with path.open() as f:
        return json.load(f)


def _discover_seeds(workspace: Path) -> list[dict]:
    """Walk workspace directories to find and parse seed.yaml files.

    Looks for <workspace>/<organ-dir>/<repo>/seed.yaml pattern.
    """
    from organvm_engine.seed.discover import discover_seeds
    from organvm_engine.seed.reader import read_seed

    seed_paths = discover_seeds(workspace)
    results = []
    for path in seed_paths:
        try:
            results.append(read_seed(path))
        except Exception:
            # Skip invalid seeds for the MCP view
            continue
    return results
