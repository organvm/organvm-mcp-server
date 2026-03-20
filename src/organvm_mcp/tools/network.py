"""Network testament tools — mirror mapping, status, suggestions.

Exposes the network map, engagement ledger, and convergence analysis
to any Claude Code session via MCP.
"""

from __future__ import annotations

from typing import Any


def _load_maps() -> list:
    """Load all network maps from workspace."""
    from organvm_engine.network.mapper import discover_network_maps
    from organvm_engine.paths import workspace_root

    pairs = discover_network_maps(workspace_root())
    return [nmap for _, nmap in pairs]


def network_map(repo: str | None = None, organ: str | None = None) -> dict[str, Any]:
    """Show network mirrors for a repo or all repos."""
    maps = _load_maps()

    if repo:
        for nmap in maps:
            if nmap.repo == repo:
                return nmap.to_dict()
        return {"error": f"No network-map.yaml found for '{repo}'"}

    if organ:
        maps = [m for m in maps if m.organ == organ]

    return {
        "maps_count": len(maps),
        "total_mirrors": sum(m.mirror_count for m in maps),
        "repos": [
            {
                "repo": m.repo,
                "organ": m.organ,
                "technical": len(m.technical),
                "parallel": len(m.parallel),
                "kinship": len(m.kinship),
                "total": m.mirror_count,
            }
            for m in maps
        ],
    }


def network_status() -> dict[str, Any]:
    """Network health summary: density, coverage, velocity, convergences."""
    from organvm_engine.network.ledger import ledger_summary
    from organvm_engine.network.metrics import (
        convergence_points,
        mirror_coverage,
        network_density,
    )

    maps = _load_maps()
    summary = ledger_summary()
    density = network_density(maps, 76)  # approximate active repos
    coverage = mirror_coverage(maps)
    convergences = convergence_points(maps)

    return {
        "density": round(density, 3),
        "coverage": {k: round(v, 3) for k, v in coverage.items()},
        "maps_count": len(maps),
        "total_mirrors": sum(m.mirror_count for m in maps),
        "convergence_points": len(convergences),
        "top_convergences": [
            {"project": p, "repos": r, "count": len(r)}
            for p, r in sorted(convergences.items(), key=lambda x: -len(x[1]))[:10]
        ],
        "ledger": summary,
    }


def network_suggest(repo: str | None = None) -> dict[str, Any]:
    """Actionable engagement suggestions based on network state."""
    from organvm_engine.network.ledger import read_ledger
    from organvm_engine.network.metrics import (
        convergence_points,
        form_balance,
        lens_balance,
        mirror_coverage,
    )
    from organvm_engine.network.query import blind_spots

    maps = _load_maps()
    entries = read_ledger()

    suggestions: list[dict] = []

    # Convergence points
    convergences = convergence_points(maps)
    if convergences:
        top = sorted(convergences.items(), key=lambda x: -len(x[1]))[:5]
        suggestions.append({
            "type": "convergence",
            "message": "Deepen engagement with high-value targets",
            "targets": [{"project": p, "repos": r} for p, r in top],
        })

    # Lens imbalance
    coverage = mirror_coverage(maps)
    if maps:
        weak = [k for k, v in coverage.items() if v < 0.1]
        if weak:
            suggestions.append({
                "type": "lens_gap",
                "message": f"Lenses with <10% coverage: {', '.join(weak)}",
                "action": "Seek parallel and kinship mirrors for mapped repos",
            })

    # Engagement form gaps
    if entries:
        forms = form_balance(entries)
        absent = [f for f, v in forms.items() if v == 0.0]
        if absent:
            suggestions.append({
                "type": "form_gap",
                "message": f"Unused engagement forms: {', '.join(absent)}",
                "action": "Diversify: all four forms are equal",
            })

    # Repo-specific suggestion
    if repo:
        repo_maps = [m for m in maps if m.repo == repo]
        if repo_maps:
            nmap = repo_maps[0]
            if not nmap.parallel:
                suggestions.append({
                    "type": "repo_gap",
                    "repo": repo,
                    "message": f"{repo} has no parallel mirrors",
                    "action": "Find projects solving similar problems",
                })
            if not nmap.kinship:
                suggestions.append({
                    "type": "repo_gap",
                    "repo": repo,
                    "message": f"{repo} has no kinship mirrors",
                    "action": "Identify communities with philosophical alignment",
                })

    return {"suggestions": suggestions, "count": len(suggestions)}


def network_log(
    organvm_repo: str,
    external_project: str,
    lens: str,
    action_type: str,
    detail: str,
    url: str | None = None,
    outcome: str | None = None,
) -> dict[str, Any]:
    """Log an engagement action to the ledger."""
    from organvm_engine.network.ledger import create_engagement, log_engagement

    entry = create_engagement(
        organvm_repo=organvm_repo,
        external_project=external_project,
        lens=lens,
        action_type=action_type,
        action_detail=detail,
        url=url,
        outcome=outcome,
    )
    log_engagement(entry)
    return {
        "status": "logged",
        "timestamp": entry.timestamp,
        "repo": organvm_repo,
        "project": external_project,
        "lens": lens,
        "action": action_type,
    }


def network_convergences() -> dict[str, Any]:
    """External projects mirrored by multiple ORGANVM repos."""
    from organvm_engine.network.metrics import convergence_points

    maps = _load_maps()
    convergences = convergence_points(maps)

    return {
        "total": len(convergences),
        "convergences": [
            {"project": p, "repos": r, "count": len(r)}
            for p, r in sorted(convergences.items(), key=lambda x: -len(x[1]))
        ],
    }
