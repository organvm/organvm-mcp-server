"""Dependency graph tools.

Exposes the ORGANVM dependency graph for inter-organ and intra-repo traversal.
"""

from __future__ import annotations

from collections import deque
from typing import Any


def _normalize_repo_name(value: str) -> str:
    """Normalize a repo identifier to a bare repository name."""
    cleaned = value.strip()
    if not cleaned:
        return ""
    if "/" in cleaned:
        return cleaned.rsplit("/", maxsplit=1)[-1]
    return cleaned


def _normalize_deps(raw_deps: list[Any] | None) -> list[str]:
    normalized: list[str] = []
    for dep in raw_deps or []:
        if not isinstance(dep, str):
            continue
        dep_name = _normalize_repo_name(dep)
        if dep_name:
            normalized.append(dep_name)
    return normalized


def trace_dependencies(
    repo: str | None = None,
    organ: str | None = None,
    direction: str = "both",
    depth: int = 2,
) -> dict[str, Any]:
    """Trace dependency edges from a repo or organ."""
    from organvm_engine.registry.query import all_repos

    from organvm_mcp.data.loader import load_registry

    registry = load_registry()

    adj_upstream: dict[str, list[str]] = {}
    adj_downstream: dict[str, list[str]] = {}
    repo_to_organ: dict[str, str] = {}

    for organ_key, repo_data in all_repos(registry):
        raw_name = repo_data.get("name")
        if not isinstance(raw_name, str):
            continue
        name = _normalize_repo_name(raw_name)
        if not name:
            continue

        deps = _normalize_deps(repo_data.get("dependencies"))
        adj_upstream[name] = deps
        repo_to_organ[name] = organ_key

        for dep_name in deps:
            adj_downstream.setdefault(dep_name, []).append(name)

    roots: list[str]
    if repo:
        repo_name = _normalize_repo_name(repo)
        if repo_name not in repo_to_organ:
            return {"error": f"Unknown repository: {repo}"}
        roots = [repo_name]
    elif organ:
        roots = [name for name, org_key in repo_to_organ.items() if org_key == organ]
        if not roots:
            return {"error": f"No repositories found for organ: {organ}"}
    else:
        return {"error": "Must provide either repo or organ"}

    max_depth = max(depth, 0)

    def traverse(start_nodes: list[str], adj: dict[str, list[str]]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        visited = set(start_nodes)
        queue = deque((node, 1) for node in start_nodes)

        while queue:
            current, level = queue.popleft()
            if level > max_depth:
                continue

            for neighbor in adj.get(current, []):
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                results.append(
                    {
                        "repo": neighbor,
                        "organ": repo_to_organ.get(neighbor, "unknown"),
                        "level": level,
                    },
                )
                queue.append((neighbor, level + 1))
        return results

    result: dict[str, Any] = {"root": repo or organ, "depth": max_depth}
    if direction in {"upstream", "both"}:
        result["upstream"] = traverse(roots, adj_upstream)
    if direction in {"downstream", "both"}:
        result["downstream"] = traverse(roots, adj_downstream)

    return result


def check_dependency(source_organ: str, target_organ: str) -> dict[str, Any]:
    """Check if a dependency between two organs is allowed."""
    from organvm_mcp.data.loader import load_governance_rules

    rules = load_governance_rules()
    if not rules:
        return {"allowed": True, "reason": "No governance rules found, defaulting to allowed"}

    allowed_edges = set(rules.get("allowed_edges", []))
    forbidden_edges = set(rules.get("forbidden_edges", []))
    edge = f"{source_organ}->{target_organ}"

    if edge in forbidden_edges:
        return {
            "allowed": False,
            "reason": f"Dependency {edge} is explicitly forbidden by governance rules",
            "rule": "forbidden_edges",
        }

    if edge in allowed_edges:
        return {
            "allowed": True,
            "reason": f"Dependency {edge} is explicitly allowed",
            "rule": "allowed_edges",
        }

    levels = {
        "ORGAN-I": 1,
        "ORGAN-II": 2,
        "ORGAN-III": 3,
        "ORGAN-IV": 0,  # Orchestration can see all
        "ORGAN-V": 4,
        "ORGAN-VI": 5,
        "ORGAN-VII": 6,
        "META": 0,
    }

    source_level = levels.get(source_organ)
    target_level = levels.get(target_organ)

    if source_level is not None and target_level is not None:
        if source_level >= target_level and source_level > 0 and target_level > 0:
            return {
                "allowed": True,
                "reason": (
                    f"Conforms to unidirectional flow ({source_organ} depends on {target_organ})"
                ),
            }
        if source_level < target_level and source_level > 0:
            return {
                "allowed": False,
                "reason": (
                    "Violates unidirectional flow: "
                    f"{source_organ} cannot depend on downstream {target_organ}"
                ),
            }

    return {"allowed": True, "reason": "No specific rule found, allowing by default"}


def get_dependency_graph(organ: str | None = None) -> dict[str, Any]:
    """Return the full dependency graph or a single-organ subgraph."""
    from organvm_engine.registry.query import all_repos

    from organvm_mcp.data.loader import load_all_seeds, load_registry

    registry = load_registry()
    seeds = load_all_seeds()

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    for organ_key, repo in all_repos(registry):
        if organ and organ_key != organ:
            continue

        repo_name = repo.get("name")
        if not isinstance(repo_name, str):
            continue
        repo_name = _normalize_repo_name(repo_name)
        if not repo_name:
            continue

        nodes.append(
            {
                "id": repo_name,
                "organ": organ_key,
                "tier": repo.get("tier"),
                "status": repo.get("promotion_status"),
            },
        )

        for dep in _normalize_deps(repo.get("dependencies")):
            edges.append({"source": repo_name, "target": dep, "type": "dependency"})

    for seed in seeds:
        current_repo = seed.get("repo")
        current_organ = seed.get("organ")
        if not isinstance(current_repo, str):
            continue

        current_repo = _normalize_repo_name(current_repo)
        if organ and current_organ != organ:
            continue

        for prod in seed.get("produces", []) or []:
            if not isinstance(prod, dict):
                continue
            target = prod.get("target")
            if isinstance(target, str):
                edges.append(
                    {
                        "source": current_repo,
                        "target": _normalize_repo_name(target),
                        "type": "produces",
                        "artifact": prod.get("artifact"),
                    },
                )

        for cons in seed.get("consumes", []) or []:
            if not isinstance(cons, dict):
                continue
            source = cons.get("source")
            if isinstance(source, str):
                edges.append(
                    {
                        "source": _normalize_repo_name(source),
                        "target": current_repo,
                        "type": "consumes",
                        "artifact": cons.get("artifact"),
                    },
                )

    return {"nodes": nodes, "edges": edges}
