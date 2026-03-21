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
from organvm_engine.paths import PathConfig, resolve_path_config

from organvm_mcp.data.paths import (
    atoms_data_dir,
    event_catalog_path,
    governance_rules_path,
    registry_path,
    system_metrics_path,
    workspace_root,
)

# Module-level caches keyed by workspace/corpus pair
_registry_cache: dict[tuple[str, str], dict] = {}
_seeds_cache: dict[tuple[str, str], list[dict]] = {}
_event_catalog_cache: dict[tuple[str, str], list[dict]] = {}
_governance_rules_cache: dict[tuple[str, str], dict] = {}
_system_metrics_cache: dict[tuple[str, str], dict] = {}
_pipeline_manifest_cache: dict[tuple[str, str], dict] = {}
_conversation_corpus_surfaces_cache: dict[tuple[str, str], dict] = {}


def _cache_key(config: PathConfig | None = None) -> tuple[str, str]:
    cfg = resolve_path_config(config)
    return (
        str(cfg.workspace_root().resolve()),
        str(cfg.corpus_dir().resolve()),
    )


def load_registry(config: PathConfig | None = None) -> dict:
    """Load and cache registry-v2.json.

    Returns:
        Full registry dict with organ keys as top-level keys.
    """
    key = _cache_key(config)
    if key not in _registry_cache:
        _registry_cache[key] = _read_json(registry_path(config))
    return _registry_cache[key]


def load_all_seeds(config: PathConfig | None = None) -> list[dict]:
    """Discover and load all seed.yaml files in the workspace.

    Returns:
        List of parsed seed.yaml dicts, one per repo.
    """
    key = _cache_key(config)
    if key not in _seeds_cache:
        _seeds_cache[key] = _discover_seeds(workspace_root(config))
    return _seeds_cache[key]


def load_event_catalog(config: PathConfig | None = None) -> list[dict]:
    """Load and cache event-catalog.yaml.

    Returns:
        List of event definitions.
    """
    key = _cache_key(config)
    if key not in _event_catalog_cache:
        path = event_catalog_path(config)
        if path.exists():
            with path.open() as f:
                data = yaml.safe_load(f)
            _event_catalog_cache[key] = data.get("events", []) if isinstance(data, dict) else []
        else:
            _event_catalog_cache[key] = []
    return _event_catalog_cache[key]


def load_governance_rules(config: PathConfig | None = None) -> dict:
    """Load and cache governance-rules.json.

    Returns:
        Governance rules dict with allowed_edges, forbidden_edges, etc.
    """
    key = _cache_key(config)
    if key not in _governance_rules_cache:
        path = governance_rules_path(config)
        _governance_rules_cache[key] = _read_json(path) if path.exists() else {}
    return _governance_rules_cache[key]


def load_system_metrics(config: PathConfig | None = None) -> dict:
    """Load and cache system-metrics.json.

    Returns:
        System metrics dict with computed and manual sections.
    """
    key = _cache_key(config)
    if key not in _system_metrics_cache:
        path = system_metrics_path(config)
        _system_metrics_cache[key] = _read_json(path) if path.exists() else {}
    return _system_metrics_cache[key]


def load_pipeline_manifest(config: PathConfig | None = None) -> dict:
    """Load and cache atoms pipeline manifest.

    Returns:
        Pipeline manifest dict with file hashes and counts.
    """
    key = _cache_key(config)
    if key not in _pipeline_manifest_cache:
        path = atoms_data_dir(config) / "pipeline-manifest.json"
        _pipeline_manifest_cache[key] = _read_json(path) if path.exists() else {}
    return _pipeline_manifest_cache[key]


def load_conversation_corpus_surfaces(config: PathConfig | None = None) -> dict:
    """Load and cache discovered conversation corpus surfaces."""
    key = _cache_key(config)
    if key not in _conversation_corpus_surfaces_cache:
        from organvm_engine.contextmd.surfaces import collect_conversation_corpus_surfaces

        _conversation_corpus_surfaces_cache[key] = collect_conversation_corpus_surfaces(
            config=resolve_path_config(config),
        )
    return _conversation_corpus_surfaces_cache[key]


def reload(config: PathConfig | None = None) -> None:
    """Clear caches for one config pair or for all cached data."""
    if config is None:
        _registry_cache.clear()
        _seeds_cache.clear()
        _event_catalog_cache.clear()
        _governance_rules_cache.clear()
        _system_metrics_cache.clear()
        _pipeline_manifest_cache.clear()
        _conversation_corpus_surfaces_cache.clear()
        return

    key = _cache_key(config)
    _registry_cache.pop(key, None)
    _seeds_cache.pop(key, None)
    _event_catalog_cache.pop(key, None)
    _governance_rules_cache.pop(key, None)
    _system_metrics_cache.pop(key, None)
    _pipeline_manifest_cache.pop(key, None)
    _conversation_corpus_surfaces_cache.pop(key, None)


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
