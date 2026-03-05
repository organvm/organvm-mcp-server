"""System health, omega status, and pitch deck coverage tools."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TEST_DIRS = ("tests", "__tests__", "test", "spec")


def _workspace_root() -> Path:
    return Path(os.environ.get("ORGANVM_WORKSPACE_DIR", str(Path.home() / "Workspace")))


def _repo_path(organ_key: str, repo_name: str) -> Path | None:
    from organvm_engine.organ_config import registry_key_to_dir

    organ_dirs = registry_key_to_dir()
    organ_dir = organ_dirs.get(organ_key)
    if not organ_dir:
        return None

    path = _workspace_root() / organ_dir / repo_name
    return path if path.is_dir() else None


def _has_ci_workflow(repo: dict[str, Any], local_path: Path | None) -> bool:
    if repo.get("ci_workflow"):
        return True
    if not local_path:
        return False
    workflows_dir = local_path / ".github" / "workflows"
    return workflows_dir.is_dir() and any(workflows_dir.glob("*.yml"))


def _has_tests(local_path: Path | None) -> bool:
    if not local_path:
        return False
    return any((local_path / dirname).is_dir() for dirname in TEST_DIRS)


def _has_docs(repo: dict[str, Any], local_path: Path | None) -> bool:
    doc_status = str(repo.get("documentation_status", "")).strip().upper()
    if doc_status and doc_status != "NONE":
        return True
    if not local_path:
        return False
    return (local_path / "README.md").is_file()


def system_health() -> dict[str, Any]:
    """Get a system-wide health summary."""
    from organvm_engine.registry.query import all_repos

    from organvm_mcp.data.loader import load_all_seeds, load_registry

    registry = load_registry()
    seeds = load_all_seeds()
    all_registry_repos = list(all_repos(registry))
    total = len(all_registry_repos)

    seed_repo_names = {
        seed.get("repo")
        for seed in seeds
        if isinstance(seed, dict) and isinstance(seed.get("repo"), str)
    }

    archived = 0
    active = 0
    ci_count = 0
    test_count = 0
    docs_count = 0
    seed_count = 0

    promotion_distribution = {
        status: 0 for status in ["LOCAL", "CANDIDATE", "PUBLIC_PROCESS", "GRADUATED", "ARCHIVED"]
    }
    by_organ: dict[str, dict[str, int]] = {}

    pre_launch = 0
    live = 0

    for organ_key, repo in all_registry_repos:
        raw_name = repo.get("name")
        if not isinstance(raw_name, str):
            continue
        repo_name = raw_name

        impl_status = str(repo.get("implementation_status", "")).upper()
        is_archived = bool(repo.get("archived")) or impl_status == "ARCHIVED"
        if is_archived:
            archived += 1
        else:
            active += 1

        promo = str(repo.get("promotion_status", "LOCAL")).upper()
        if promo in promotion_distribution:
            promotion_distribution[promo] += 1

        local_path = _repo_path(organ_key, repo_name)
        if _has_ci_workflow(repo, local_path):
            ci_count += 1
        if _has_tests(local_path):
            test_count += 1
        if _has_docs(repo, local_path):
            docs_count += 1
        if repo_name in seed_repo_names:
            seed_count += 1

        organ_counts = by_organ.setdefault(
            organ_key,
            {
                "total": 0,
                "active": 0,
                "archived": 0,
            },
        )
        organ_counts["total"] += 1
        if is_archived:
            organ_counts["archived"] += 1
        else:
            organ_counts["active"] += 1

        if organ_key == "ORGAN-III":
            revenue_status = str(repo.get("revenue_status", "")).strip().lower()
            if revenue_status == "live":
                live += 1
            else:
                pre_launch += 1

    def ratio(count: int) -> float:
        if total == 0:
            return 0.0
        return round(count / total, 4)

    return {
        "total_repos": total,
        "active_repos": active,
        "archived_repos": archived,
        "ci_coverage": ratio(ci_count),
        "test_coverage": ratio(test_count),
        "docs_coverage": ratio(docs_count),
        "seed_coverage": ratio(seed_count),
        "promotion_distribution": promotion_distribution,
        "revenue_status": {"pre_launch": pre_launch, "live": live},
        "by_organ": by_organ,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


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
