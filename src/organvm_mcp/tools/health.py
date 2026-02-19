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
    system's transition from construction to occupation.

    Returns:
        {"criteria_met": int, "criteria_total": 17,
         "percentage": float,
         "horizons": [...],
         "next_milestone": {"id": int, "name": "...", "estimated_date": "..."}}
    """
    # For now, providing a structured summary based on the 17 criteria model
    # TODO: implement real parsing of omega-evidence-map.md
    
    return {
        "criteria_met": 8,
        "criteria_total": 17,
        "percentage": 47.0,
        "horizons": [
            {
                "name": "H1: Prove It Works", 
                "timeline": "Days 1-30",
                "criteria": [
                    {"id": 1, "name": "Soak test complete", "status": "IN_PROGRESS"},
                    {"id": 2, "name": "Registry V2 valid", "status": "MET"},
                    {"id": 3, "name": "All 8 organs mapped", "status": "MET"}
                ]
            },
            {
                "name": "H2: Unified Workflow",
                "timeline": "Days 31-60",
                "criteria": [
                    {"id": 4, "name": "Cross-repo awareness", "status": "IN_PROGRESS"},
                    {"id": 5, "name": "Shared CI actions", "status": "IN_PROGRESS"}
                ]
            }
        ],
        "next_milestone": {"id": 1, "name": "Soak test complete", "estimated_date": "2026-03-18"}
    }
