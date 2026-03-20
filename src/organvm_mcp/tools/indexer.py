"""Indexer tools — deep structural census of atomic components.

Exposes the deep structural indexer to any Claude Code session,
enabling queries about repository structure at the component level.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def _workspace_root() -> Path:
    return Path(os.environ.get("ORGANVM_WORKSPACE_DIR", str(Path.home() / "Workspace")))


def index_scan(
    organ: str | None = None,
    repo: str | None = None,
) -> dict[str, Any]:
    """Run the deep structural index across the workspace.

    Returns system-wide component census with cohesion types,
    language breakdown, and per-organ statistics.
    """
    from organvm_engine.indexer import run_deep_index
    from organvm_engine.registry.loader import load_registry

    registry = load_registry()
    workspace = _workspace_root()
    index = run_deep_index(workspace, registry, repo, organ)
    return index.to_dict()


def index_show(repo_name: str) -> dict[str, Any]:
    """Show the component tree for a single repository.

    Returns atomic components with cohesion types, file/line counts,
    dominant language, and inter-component import edges.
    """
    from organvm_engine.indexer import index_repo
    from organvm_engine.organ_config import registry_key_to_dir
    from organvm_engine.paths import workspace_root
    from organvm_engine.registry.loader import load_registry
    from organvm_engine.registry.query import find_repo

    registry = load_registry()
    result = find_repo(registry, repo_name)
    if not result:
        return {"error": f"Repo '{repo_name}' not found in registry"}

    organ_key, repo = result
    r2d = registry_key_to_dir()
    organ_dir = r2d.get(organ_key, "")
    ws = workspace_root()
    repo_path = ws / organ_dir / repo["name"]

    idx = index_repo(repo_path, repo["name"], organ_key)
    return idx.to_dict()


def index_bridge(
    organ: str | None = None,
    repo: str | None = None,
) -> dict[str, Any]:
    """Register indexed components as ontologia entities.

    Creates MODULE entities with permanent UIDs for all atomic
    components discovered by the deep structural indexer.
    Idempotent — skips already-registered components.
    """
    from organvm_engine.indexer import run_deep_index
    from organvm_engine.indexer.bridge import register_components
    from organvm_engine.registry.loader import load_registry

    registry = load_registry()
    workspace = _workspace_root()
    index = run_deep_index(workspace, registry, repo, organ)
    result = register_components(index)
    return result.to_dict()


def query_relations(entity: str) -> dict[str, Any]:
    """Multi-scale relation query for any entity.

    Returns all relations at three scales:
    - Inter-repo: seed graph produces/consumes edges
    - Intra-repo: import edges between atomic components
    - Entity-level: ontologia hierarchy and relation edges
    """
    from organvm_engine.pulse.graph import query_relations as _query

    rmap = _query(entity)
    return rmap.to_dict()


def entity_memory(entity: str, limit: int = 50) -> dict[str, Any]:
    """Aggregate all signals about an entity from every data source.

    Collects pulse events, shared memory insights, ontologia events
    and name history, continuity signals, and metrics trends.
    """
    from organvm_engine.pulse.memory import aggregate_entity_memory

    mem = aggregate_entity_memory(entity, limit=limit)
    return mem.to_dict()
