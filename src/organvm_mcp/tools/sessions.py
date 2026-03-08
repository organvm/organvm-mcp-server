"""Session intelligence tools — multi-agent session discovery and analysis."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any


def session_agents() -> dict[str, Any]:
    """Get multi-agent session inventory."""
    from organvm_engine.session.agents import agent_summary

    return agent_summary()


def session_list(
    agent: str | None = None,
    project_filter: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """List recent sessions with metadata."""
    from organvm_engine.session.agents import discover_all_sessions

    sessions = discover_all_sessions(agent=agent, project_filter=project_filter)
    total = len(sessions)
    capped = sessions[:limit]
    return {
        "sessions": [
            {
                "agent": s.agent,
                "session_id": s.session_id,
                "project": s.project_dir,
                "date": s.date_str,
                "duration_minutes": s.duration_minutes,
                "size": s.size_human,
            }
            for s in capped
        ],
        "total": total,
        "shown": len(capped),
        "limit": limit,
    }


def session_plans(
    project_filter: str | None = None,
    organ: str | None = None,
    agent: str | None = None,
) -> dict[str, Any]:
    """Plan file inventory by project/organ."""
    from organvm_engine.session.plans import discover_plans

    plans = discover_plans(
        project_filter=project_filter,
        organ=organ,
        agent=agent,
        include_global=False,
    )
    by_project: dict[str, int] = {}
    for p in plans:
        by_project[p.project] = by_project.get(p.project, 0) + 1

    return {
        "plans": [
            {
                "date": p.date,
                "slug": p.slug,
                "title": p.title,
                "project": p.project,
                "agent": p.agent,
                "organ": p.organ,
                "repo": p.repo,
                "has_verification": p.has_verification,
                "status": p.status,
                "version": p.version,
            }
            for p in plans
        ],
        "total": len(plans),
        "by_project": by_project,
    }


def session_analyze_prompts(
    agent: str | None = None,
    sample_limit: int = 100,
) -> dict[str, Any]:
    """Cross-session prompt pattern analysis."""
    from organvm_engine.session.analysis import analyze_prompts

    stats = analyze_prompts(agent=agent, sample_limit=sample_limit)
    return asdict(stats)
