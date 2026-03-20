"""System health, omega status, and pitch deck coverage tools."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def _workspace_root() -> Path:
    return Path(os.environ.get("ORGANVM_WORKSPACE_DIR", str(Path.home() / "Workspace")))


def system_health() -> dict[str, Any]:
    """Get a system-wide health summary via organism + view projection."""
    from organvm_engine.metrics.organism import compute_organism
    from organvm_engine.metrics.views import project_mcp_health
    from organvm_engine.registry.query import all_repos

    from organvm_mcp.data.loader import load_all_seeds, load_registry

    registry = load_registry()
    organism = compute_organism(registry)
    result = project_mcp_health(organism)

    # Supplement with seed coverage and revenue status (not in organism)
    seeds = load_all_seeds()
    seed_repo_names = {
        seed.get("repo")
        for seed in seeds
        if isinstance(seed, dict) and isinstance(seed.get("repo"), str)
    }
    total = result["total_repos"]
    all_registry_repos = list(all_repos(registry))
    seed_count = sum(
        1
        for _, repo in all_registry_repos
        if isinstance(repo.get("name"), str) and repo["name"] in seed_repo_names
    )
    result["seed_coverage"] = round(seed_count / total, 4) if total else 0.0

    pre_launch = 0
    live = 0
    for organ_key, repo in all_registry_repos:
        if organ_key == "ORGAN-III":
            revenue_status = str(repo.get("revenue_status", "")).strip().lower()
            if revenue_status == "live":
                live += 1
            else:
                pre_launch += 1
    result["revenue_status"] = {"pre_launch": pre_launch, "live": live}

    # Rename generated -> timestamp for backward compatibility
    result["timestamp"] = result.pop("generated")

    return result


def organism(
    organ: str | None = None,
    repo: str | None = None,
    view: str = "full",
) -> dict[str, Any]:
    """Get unified system organism with optional zoom and view."""
    from organvm_engine.metrics.organism import compute_organism
    from organvm_engine.metrics.views import (
        project_blockers,
        project_gate_stats,
        project_organism_cli,
    )

    from organvm_mcp.data.loader import load_registry

    registry = load_registry()
    org = compute_organism(registry)

    if view == "gates":
        return project_gate_stats(org)
    if view == "blockers":
        return project_blockers(org)

    return project_organism_cli(org, organ=organ, repo=repo)


def omega_status() -> dict[str, Any]:
    """Get omega criteria progress."""
    from organvm_engine.omega.scorecard import evaluate

    from organvm_mcp.data.loader import load_registry

    registry = load_registry()
    scorecard = evaluate(registry=registry)
    return scorecard.to_dict()


def ci_health() -> dict[str, Any]:
    """Get CI health summary from latest soak data."""
    from organvm_engine.ci.triage import triage

    report = triage()
    return report.to_dict()


def ci_audit(organ: str = "", repo: str = "") -> dict[str, Any]:
    """Run Descent Protocol infrastructure audit.

    Checks all 15 GitHub infrastructure mechanisms against
    promotion-tier requirements for each repo.
    """
    from organvm_engine.ci.audit import run_infra_audit

    from organvm_mcp.data.loader import load_registry

    registry = load_registry()
    report = run_infra_audit(
        registry=registry,
        organ_filter=organ or None,
        repo_filter=repo or None,
    )
    result = report.to_dict()
    result["summary"] = report.summary()
    return result


def deadlines(days: int = 30) -> dict[str, Any]:
    """Get upcoming deadlines from the rolling-todo."""
    from organvm_engine.deadlines.parser import filter_upcoming, parse_deadlines

    all_deadlines = parse_deadlines()
    filtered = filter_upcoming(all_deadlines, days=days)

    return {
        "deadlines": [
            {
                "item_id": deadline.item_id,
                "description": deadline.description,
                "date": deadline.deadline_date.isoformat(),
                "days_remaining": deadline.days_remaining,
                "urgency": deadline.urgency,
                "approximate": deadline.approximate,
            }
            for deadline in filtered
        ],
        "total_all": len(all_deadlines),
        "total_shown": len(filtered),
        "window_days": days,
    }


def pitch_status() -> dict[str, Any]:
    """Get pitch deck coverage across the system."""
    from organvm_engine.git.superproject import REGISTRY_KEY_MAP
    from organvm_engine.pitchdeck import PITCH_MARKER
    from organvm_engine.registry.query import all_repos

    from organvm_mcp.data.loader import load_registry

    registry = load_registry()
    workspace = _workspace_root()

    excluded_tiers = {"infrastructure", "archive"}
    total_eligible = 0
    with_decks = 0
    bespoke_count = 0
    generated_count = 0
    by_organ: dict[str, dict[str, int]] = {}

    for organ_key, repo in all_repos(registry):
        tier = repo.get("tier", "standard")
        if tier in excluded_tiers:
            continue

        repo_name = repo.get("name", "")
        if not isinstance(repo_name, str) or not repo_name:
            continue
        organ_dir = REGISTRY_KEY_MAP.get(organ_key, "")

        total_eligible += 1
        if organ_key not in by_organ:
            by_organ[organ_key] = {"eligible": 0, "with_deck": 0, "bespoke": 0, "generated": 0}
        by_organ[organ_key]["eligible"] += 1

        for subdir in ("docs/pitch", "docs/pitch-deck"):
            pitch_file = workspace / organ_dir / repo_name / subdir / "index.html"
            if not pitch_file.exists():
                continue

            with_decks += 1
            by_organ[organ_key]["with_deck"] += 1
            try:
                content = pitch_file.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                break

            if PITCH_MARKER in content:
                generated_count += 1
                by_organ[organ_key]["generated"] += 1
            else:
                bespoke_count += 1
                by_organ[organ_key]["bespoke"] += 1
            break

    coverage_pct = round(with_decks / total_eligible * 100, 1) if total_eligible > 0 else 0.0
    return {
        "total_eligible": total_eligible,
        "with_decks": with_decks,
        "bespoke": bespoke_count,
        "generated": generated_count,
        "missing": total_eligible - with_decks,
        "coverage_pct": coverage_pct,
        "by_organ": by_organ,
    }
