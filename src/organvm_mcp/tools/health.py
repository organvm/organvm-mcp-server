"""System health and omega status tools.

Provides aggregate health metrics and omega criteria tracking
for the full ORGANVM system.
"""

from __future__ import annotations

from typing import Any


def system_health() -> dict[str, Any]:
    """Get a system-wide health summary.

    Aggregates:
    - Repo counts (total, active, archived)
    - CI/CD coverage (repos with workflows)
    - Test coverage (repos with test directories)
    - Seed coverage (repos with valid seed.yaml)
    - Documentation coverage (repos with READMEs)
    - Promotion pipeline state (counts per status)
    - Revenue status (ORGAN-III pre-launch vs live)

    Returns:
        {"total_repos": int, "active_repos": int, "archived_repos": int,
         "ci_coverage": float, "test_coverage": float, "seed_coverage": float,
         "promotion_distribution": {"LOCAL": int, "CANDIDATE": int, ...},
         "revenue_status": {"pre_launch": int, "live": int},
         "timestamp": "ISO 8601"}
    """
    from organvm_mcp.data.loader import load_registry, load_all_seeds
    from organvm_engine.registry.query import all_repos
    from datetime import datetime, timezone
    
    registry = load_registry()
    seeds = load_all_seeds()
    
    all_r = list(all_repos(registry))
    total = len(all_r)
    active = len([r for _, r in all_r if not r.get("archived")])
    archived = total - active
    
    status_dist = {
        s: len([r for _, r in all_r if r.get("promotion_status") == s])
        for s in ["LOCAL", "CANDIDATE", "PUBLIC_PROCESS", "GRADUATED", "ARCHIVED"]
    }
    
    # Revenue status (rough estimate based on tier/status in ORGAN-III)
    pre_launch = 0
    live = 0
    for organ_key, repo in all_r:
        if organ_key == "ORGAN-III":
            if repo.get("promotion_status") in ["GRADUATED", "PUBLIC_PROCESS"]:
                live += 1
            else:
                pre_launch += 1
                
    return {
        "total_repos": total,
        "active_repos": active,
        "archived_repos": archived,
        "seed_coverage": len(seeds) / total if total > 0 else 0,
        "promotion_distribution": status_dist,
        "revenue_status": {"pre_launch": pre_launch, "live": live},
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def omega_status() -> dict[str, Any]:
    """Get omega criteria progress.

    The omega framework defines 17 criteria across 5 horizons for the
    system's transition from construction to occupation. Uses the real
    omega evaluator from organvm-engine.

    Returns:
        {"score": int, "total": 17, "in_progress": int,
         "criteria": [...], "soak": {...}, "generated": "ISO 8601"}
    """
    from organvm_mcp.data.loader import load_registry
    from organvm_engine.omega.scorecard import evaluate

    registry = load_registry()
    scorecard = evaluate(registry=registry)
    return scorecard.to_dict()


def ci_health() -> dict[str, Any]:
    """Get CI health summary from latest soak data.

    Categorizes CI failures by organ and identifies phantom failures
    (schedule-only workflows).

    Returns:
        {"date": str, "total_checked": int, "passing": int,
         "failing": int, "pass_rate": float,
         "by_organ": {...}, "phantom_candidates": [...]}
    """
    from organvm_engine.ci.triage import triage

    report = triage()
    return report.to_dict()


def deadlines(days: int = 30) -> dict[str, Any]:
    """Get upcoming deadlines from the rolling-todo.

    Parses deadline dates from the corpus rolling-todo.md and returns
    items within the specified window.

    Args:
        days: Number of days to look ahead (default 30).

    Returns:
        {"deadlines": [...], "total": int, "window_days": int}
    """
    from organvm_engine.deadlines.parser import parse_deadlines, filter_upcoming

    all_deadlines = parse_deadlines()
    filtered = filter_upcoming(all_deadlines, days=days)

    return {
        "deadlines": [
            {
                "item_id": d.item_id,
                "description": d.description,
                "date": d.deadline_date.isoformat(),
                "days_remaining": d.days_remaining,
                "urgency": d.urgency,
                "approximate": d.approximate,
            }
            for d in filtered
        ],
        "total_all": len(all_deadlines),
        "total_shown": len(filtered),
        "window_days": days,
    }
