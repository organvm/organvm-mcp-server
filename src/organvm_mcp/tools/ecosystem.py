"""Ecosystem discovery tools — profile, matrix, gaps, actions.

Exposes per-product business ecosystem intelligence to any Claude Code session.
"""

from __future__ import annotations

import contextlib
from typing import Any


def _load_ecosystems(organ: str | None = None) -> list[dict]:
    """Load all ecosystem profiles from workspace."""
    from organvm_engine.ecosystem.discover import discover_ecosystems
    from organvm_engine.ecosystem.reader import read_ecosystem

    paths = discover_ecosystems(organ=organ)
    data: list[dict] = []
    for p in paths:
        with contextlib.suppress(Exception):
            data.append(read_ecosystem(p))
    return data


def ecosystem_profile(repo: str) -> dict[str, Any]:
    """Full ecosystem data + coverage stats for a single product."""
    from organvm_engine.ecosystem.query import coverage_matrix, gaps
    from organvm_engine.ecosystem.reader import get_pillars

    ecosystems = _load_ecosystems()

    for eco in ecosystems:
        if eco.get("repo") == repo:
            pillars = get_pillars(eco)
            gap_list = gaps(eco)
            matrix = coverage_matrix([eco])
            return {
                "repo": repo,
                "organ": eco.get("organ"),
                "display_name": eco.get("display_name"),
                "pillars": {
                    name: {
                        "arms": arms,
                        "count": len(arms),
                    }
                    for name, arms in pillars.items()
                },
                "coverage": matrix.get(repo, {}),
                "gaps": gap_list,
            }

    return {"error": f"No ecosystem.yaml found for '{repo}'"}


def ecosystem_matrix(pillar: str, organ: str | None = None) -> dict[str, Any]:
    """Cross-product pillar comparison."""
    from organvm_engine.ecosystem.query import pillar_view, status_summary

    ecosystems = _load_ecosystems(organ=organ)
    view = pillar_view(ecosystems, pillar)
    summary = status_summary(ecosystems)

    return {
        "pillar": pillar,
        "products_with_pillar": len(view),
        "total_products": summary["total_products"],
        "view": view,
    }


def ecosystem_gaps(
    repo: str | None = None,
    organ: str | None = None,
) -> dict[str, Any]:
    """Missing pillars/arms with suggestions."""
    from organvm_engine.ecosystem.query import gaps

    ecosystems = _load_ecosystems(organ=organ)
    all_gaps: dict[str, list[str]] = {}

    for eco in ecosystems:
        r = eco.get("repo", "unknown")
        if repo and r != repo:
            continue
        gap_list = gaps(eco)
        if gap_list:
            all_gaps[r] = gap_list

    return {
        "products_analyzed": len(ecosystems),
        "products_with_gaps": len(all_gaps),
        "gaps": all_gaps,
    }


def ecosystem_actions(organ: str | None = None) -> dict[str, Any]:
    """Prioritized next-action list."""
    from organvm_engine.ecosystem.query import next_actions

    ecosystems = _load_ecosystems(organ=organ)
    actions = next_actions(ecosystems)

    return {
        "total_actions": len(actions),
        "actions": actions,
    }


def pillar_dna(repo: str, pillar: str | None = None) -> dict[str, Any]:
    """Pillar DNA lifecycle contracts for a repo."""
    from organvm_engine.ecosystem.discover import discover_ecosystems
    from organvm_engine.ecosystem.pillar_dna import list_pillar_dnas, read_pillar_dna

    # Find repo path
    eco_paths = discover_ecosystems()
    repo_path = None
    for ep in eco_paths:
        if ep.parent.name == repo:
            repo_path = ep.parent
            break

    if not repo_path:
        return {"error": f"Repository '{repo}' not found"}

    if pillar:
        dna = read_pillar_dna(repo_path, pillar)
        if not dna:
            return {"error": f"No pillar DNA for '{pillar}' in {repo}"}
        return {"repo": repo, "pillar": pillar, "dna": dna}

    pillars = list_pillar_dnas(repo_path)
    all_dna: dict[str, dict] = {}
    for p in pillars:
        dna = read_pillar_dna(repo_path, p)
        if dna:
            all_dna[p] = dna

    return {"repo": repo, "pillars": all_dna}


def ecosystem_staleness(
    repo: str | None = None,
    organ: str | None = None,
) -> dict[str, Any]:
    """Staleness report for pillar DNA artifacts."""
    from organvm_engine.ecosystem.discover import discover_ecosystems
    from organvm_engine.ecosystem.intelligence import staleness_report

    eco_paths = discover_ecosystems(organ=organ)
    all_stale: dict[str, list[dict]] = {}

    for eco_path in eco_paths:
        repo_path = eco_path.parent
        repo_name = repo_path.name
        if repo and repo_name != repo:
            continue
        with contextlib.suppress(Exception):
            report = staleness_report(repo_path)
            if report:
                all_stale[repo_name] = report

    return {
        "repos_checked": len(eco_paths),
        "repos_with_stale": len(all_stale),
        "stale_artifacts": all_stale,
    }


def ecosystem_lifecycle(organ: str | None = None) -> dict[str, Any]:
    """Lifecycle stages across repos."""
    from organvm_engine.ecosystem.discover import discover_ecosystems
    from organvm_engine.ecosystem.pillar_dna import list_pillar_dnas, read_pillar_dna

    eco_paths = discover_ecosystems(organ=organ)
    result: dict[str, dict[str, str]] = {}

    for eco_path in eco_paths:
        repo_path = eco_path.parent
        repo_name = repo_path.name
        pillars = list_pillar_dnas(repo_path)
        if not pillars:
            continue
        stages: dict[str, str] = {}
        for p in pillars:
            dna = read_pillar_dna(repo_path, p)
            if dna:
                stages[p] = dna.get("lifecycle_stage", "conception")
        if stages:
            result[repo_name] = stages

    return {
        "repos_with_dna": len(result),
        "lifecycle": result,
    }
