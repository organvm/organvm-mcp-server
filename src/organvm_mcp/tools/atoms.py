"""Atoms / task tracking tools — pipeline status, rollups, task queues, links."""

from __future__ import annotations

import json
from typing import Any


def atoms_status() -> dict[str, Any]:
    """Atomization pipeline status from pipeline-manifest.json."""
    from organvm_mcp.data.paths import atoms_data_dir

    manifest_path = atoms_data_dir() / "pipeline-manifest.json"
    if not manifest_path.exists():
        return {"error": "Pipeline manifest not found", "path": str(manifest_path)}

    with manifest_path.open() as f:
        return json.load(f)


def atoms_rollup(organ: str | None = None) -> dict[str, Any]:
    """Per-organ task rollup."""
    from organvm_engine.atoms.rollup import build_rollups

    from organvm_mcp.data.paths import atoms_data_dir

    rollups = build_rollups(atoms_data_dir())
    if organ:
        rollup = rollups.get(organ)
        if rollup is None:
            return {"error": f"No rollup data for organ '{organ}'"}
        return rollup.to_dict()

    return {
        "organs": {key: r.to_dict() for key, r in rollups.items()},
        "total_organs": len(rollups),
        "total_tasks": sum(r.total_tasks for r in rollups.values()),
        "total_pending": sum(r.pending_tasks for r in rollups.values()),
    }


def atoms_tasks(repo_name: str, organ: str | None = None) -> dict[str, Any]:
    """Pending tasks for a repo."""
    from organvm_engine.atoms.rollup import build_rollups, load_repo_task_queue

    from organvm_mcp.data.paths import atoms_data_dir

    rollups = build_rollups(atoms_data_dir())

    # Search through rollups for matching repo
    for key, rollup in rollups.items():
        if organ and key != organ:
            continue
        result = load_repo_task_queue(rollup.to_dict(), repo_name)
        if result is not None:
            return {
                "organ": key,
                "repo": repo_name,
                **result,
            }

    return {"error": f"No tasks found for repo '{repo_name}'"}


def atoms_links(limit: int = 50) -> dict[str, Any]:
    """Cross-system task-prompt links."""
    from organvm_mcp.data.paths import atoms_data_dir

    links_path = atoms_data_dir() / "atom-links.jsonl"
    if not links_path.exists():
        return {"error": "atom-links.jsonl not found", "path": str(links_path)}

    links = []
    with links_path.open() as f:
        for i, raw_line in enumerate(f):
            if i >= limit:
                break
            stripped = raw_line.strip()
            if stripped:
                links.append(json.loads(stripped))

    return {
        "links": links,
        "shown": len(links),
        "limit": limit,
    }
