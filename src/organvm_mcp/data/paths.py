"""Workspace path resolution for MCP loaders and tools."""

from __future__ import annotations

from pathlib import Path

from organvm_engine.paths import PathConfig, resolve_path_config

# Conventional defaults
_DEFAULT_ENGINE_SUBPATH = "meta-organvm/organvm-engine"
_DEFAULT_ORCHESTRATOR_SUBPATH = "organvm-iv-taxis/orchestration-start-here"


def workspace_root(config: PathConfig | None = None) -> Path:
    """Return the workspace root directory."""
    return resolve_path_config(config).workspace_root()


def corpus_dir(config: PathConfig | None = None) -> Path:
    """Return the path to organvm-corpvs-testamentvm."""
    return resolve_path_config(config).corpus_dir()


def registry_path(config: PathConfig | None = None) -> Path:
    """Return the path to registry-v2.json."""
    return resolve_path_config(config).registry_path()


def event_catalog_path(config: PathConfig | None = None) -> Path:
    """Return the path to event-catalog.yaml."""
    return workspace_root(config) / _DEFAULT_ORCHESTRATOR_SUBPATH / "docs" / "event-catalog.yaml"


def governance_rules_path(config: PathConfig | None = None) -> Path:
    """Return the path to governance-rules.json."""
    return resolve_path_config(config).governance_rules_path()


def engine_dir(config: PathConfig | None = None) -> Path:
    """Return the path to organvm-engine."""
    return workspace_root(config) / _DEFAULT_ENGINE_SUBPATH


def system_metrics_path(config: PathConfig | None = None) -> Path:
    """Return the path to system-metrics.json."""
    return corpus_dir(config) / "system-metrics.json"


def atoms_data_dir(config: PathConfig | None = None) -> Path:
    """Return the path to the atoms pipeline data directory."""
    return corpus_dir(config) / "data" / "atoms"


def organ_directories(config: PathConfig | None = None) -> dict[str, Path]:
    """Return mapping of organ keys to their workspace directories.

    Returns:
        Dict like {"ORGAN-I": Path("~/Workspace/organvm-i-theoria"), ...}
    """
    from organvm_engine.git.superproject import ORGAN_DIR_MAP

    ws = workspace_root(config)
    return {key: ws / subpath for key, subpath in ORGAN_DIR_MAP.items()}


def repo_root_path(org: str, repo: str, config: PathConfig | None = None) -> Path:
    """Return the path to a repository under the workspace."""
    return workspace_root(config) / org / repo


def conversation_corpus_surface_dir(
    org: str,
    repo: str,
    config: PathConfig | None = None,
) -> Path:
    """Return the conventional reports/surfaces directory for a repository."""
    return repo_root_path(org, repo, config) / "reports" / "surfaces"


def conversation_corpus_surface_bundle_path(
    org: str,
    repo: str,
    config: PathConfig | None = None,
) -> Path:
    """Return the conventional surface bundle path for a repository."""
    return conversation_corpus_surface_dir(org, repo, config) / "surface-bundle.json"
