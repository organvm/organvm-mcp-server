"""Revenue intelligence tools — pipeline, products, readiness, grants, consulting.

All statistics are dynamically derived from evolving data sources:
- Products: registry-v2.json (ORGAN-III repos with revenue fields)
- Grants: rolling-todo.md (F-prefixed deadlines)
- Consulting: consulting-services-manifest.md (parsed from Layer 2 table)
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

# Regex to parse the Layer 2 consulting table rows
# Format: | **Package Name** | SOP Asset | Essay Asset | Target Client | Deliverable | Temporal |
_TABLE_ROW_RE = re.compile(
    r"\|\s*\*\*(.+?)\*\*\s*\|"  # column 1: package name in bold
    r"\s*(.+?)\s*\|"  # column 2: SOP asset
    r"\s*(.+?)\s*\|"  # column 3: essay asset
    r"\s*(.+?)\s*\|"  # column 4: target client
    r"\s*(.+?)\s*\|"  # column 5: deliverable
    r"\s*(.+?)\s*\|",  # column 6: temporal lens
)

# Extract SOP filenames from the SOP Asset column
_SOP_REF_RE = re.compile(r"((?:SOP|METADOC)--[\w-]+)")


def _parse_consulting_manifest(
    manifest_path: Path | None = None,
) -> list[dict[str, Any]]:
    """Parse consulting packages from the consulting-services-manifest.md.

    Reads the Layer 2 table and extracts package names, SOP references,
    essay references, target clients, and deliverables.
    """
    if manifest_path is None:
        from organvm_mcp.data.paths import corpus_dir

        manifest_path = corpus_dir() / "docs" / "strategy" / "consulting-services-manifest.md"

    if not manifest_path.is_file():
        return []

    text = manifest_path.read_text(encoding="utf-8")

    packages = []
    for match in _TABLE_ROW_RE.finditer(text):
        name = match.group(1).strip()
        sop_asset = match.group(2).strip()
        essay_asset = match.group(3).strip()
        target_client = match.group(4).strip()
        deliverable = match.group(5).strip()
        temporal = match.group(6).strip()

        # Extract SOP--* references from the SOP Asset column
        sop_refs = _SOP_REF_RE.findall(sop_asset)

        packages.append(
            {
                "name": name,
                "sop_asset": sop_asset,
                "sop_refs": [f"{ref}.md" for ref in sop_refs],
                "essay_asset": essay_asset,
                "target_client": target_client,
                "deliverable": deliverable,
                "temporal_lens": temporal,
            },
        )

    return packages


def revenue_pipeline() -> dict[str, Any]:
    """Full 6-layer revenue pipeline status."""
    from organvm_engine.deadlines.parser import filter_upcoming, parse_deadlines
    from organvm_engine.registry.query import all_repos

    from organvm_mcp.data.loader import load_registry

    registry = load_registry()

    # Layer 1: Products (ORGAN-III)
    products = []
    for organ_key, repo in all_repos(registry):
        if organ_key == "ORGAN-III":
            products.append(
                {
                    "name": repo.get("name"),
                    "revenue_model": repo.get("revenue_model", "none"),
                    "revenue_status": repo.get("revenue_status", "pre-launch"),
                    "promotion_status": repo.get("promotion_status", "LOCAL"),
                    "tier": repo.get("tier", "standard"),
                },
            )

    live = sum(1 for p in products if p["revenue_status"] == "live")

    # Layer 2: Grants / Funding
    try:
        all_deadlines = parse_deadlines()
        grants = [
            {
                "item_id": d.item_id,
                "description": d.description,
                "date": d.deadline_date.isoformat(),
                "urgency": d.urgency,
            }
            for d in filter_upcoming(all_deadlines, days=90)
            if d.item_id.startswith("F")
        ]
    except Exception:
        grants = []

    # Layer 3: Consulting (parsed from manifest)
    consulting_packages = _parse_consulting_manifest()

    return {
        "layers": {
            "products": {
                "total": len(products),
                "live": live,
                "pre_launch": len(products) - live,
            },
            "grants": {"upcoming": len(grants)},
            "consulting": {"packages": len(consulting_packages)},
        },
        "products": products,
        "grants": grants,
    }


def revenue_products() -> dict[str, Any]:
    """ORGAN-III products with revenue model/status/readiness."""
    from organvm_engine.registry.query import all_repos

    from organvm_mcp.data.loader import load_registry

    registry = load_registry()
    products = []
    for organ_key, repo in all_repos(registry):
        if organ_key != "ORGAN-III":
            continue
        products.append(
            {
                "name": repo.get("name"),
                "description": repo.get("description", ""),
                "revenue_model": repo.get("revenue_model", "none"),
                "revenue_status": repo.get("revenue_status", "pre-launch"),
                "promotion_status": repo.get("promotion_status", "LOCAL"),
                "tier": repo.get("tier", "standard"),
                "implementation_status": repo.get("implementation_status", ""),
                "ci_workflow": repo.get("ci_workflow", False),
            },
        )

    return {
        "products": products,
        "total": len(products),
        "by_revenue_model": _count_by_field(products, "revenue_model"),
        "by_revenue_status": _count_by_field(products, "revenue_status"),
    }


def revenue_readiness(repo_name: str) -> dict[str, Any]:
    """Per-product deployment readiness with blockers."""
    from organvm_engine.governance.impact import calculate_impact
    from organvm_engine.governance.state_machine import check_transition
    from organvm_engine.registry.query import find_repo

    from organvm_mcp.data.loader import load_registry

    registry = load_registry()
    found = find_repo(registry, repo_name)
    if found is None:
        return {"error": f"Repository '{repo_name}' not found"}

    organ_key, repo = found
    current_status = repo.get("promotion_status", "LOCAL")

    blockers = []
    if not repo.get("ci_workflow"):
        blockers.append("No CI workflow configured")
    if repo.get("implementation_status") != "ACTIVE":
        impl = repo.get("implementation_status", "unknown")
        blockers.append(
            f"Implementation status is '{impl}', not ACTIVE",
        )

    # Check if promotable
    next_states = {
        "LOCAL": "CANDIDATE",
        "CANDIDATE": "PUBLIC_PROCESS",
        "PUBLIC_PROCESS": "GRADUATED",
    }
    next_state = next_states.get(current_status)
    promo_ready = False
    promo_reason = "Already at terminal state"
    if next_state:
        promo_ready, promo_reason = check_transition(
            current_status,
            next_state,
        )

    # Impact
    impact = calculate_impact(repo_name, registry)

    return {
        "repo": repo_name,
        "organ": organ_key,
        "current_status": current_status,
        "revenue_model": repo.get("revenue_model", "none"),
        "revenue_status": repo.get("revenue_status", "pre-launch"),
        "blockers": blockers,
        "blocker_count": len(blockers),
        "promotion_ready": promo_ready,
        "promotion_reason": promo_reason,
        "downstream_impact": len(impact.affected_repos),
    }


def revenue_grants(days: int = 90) -> dict[str, Any]:
    """Grant/funding deadline view."""
    from organvm_engine.deadlines.parser import filter_upcoming, parse_deadlines

    all_deadlines = parse_deadlines()
    filtered = filter_upcoming(all_deadlines, days=days)
    grants = [d for d in filtered if d.item_id.startswith("F")]

    return {
        "grants": [
            {
                "item_id": d.item_id,
                "description": d.description,
                "date": d.deadline_date.isoformat(),
                "days_remaining": d.days_remaining,
                "urgency": d.urgency,
            }
            for d in grants
        ],
        "total": len(grants),
        "window_days": days,
    }


def revenue_consulting() -> dict[str, Any]:
    """Consulting packages parsed from manifest, with SOP verification."""
    from organvm_engine.sop.discover import discover_sops

    parsed = _parse_consulting_manifest()
    if not parsed:
        return {
            "error": "consulting-services-manifest.md not found or empty",
            "packages": [],
            "total": 0,
        }

    sops = discover_sops()
    sop_filenames = {e.filename for e in sops}

    packages = []
    for pkg in parsed:
        refs = pkg["sop_refs"]
        verified = [ref for ref in refs if ref in sop_filenames]
        missing = [ref for ref in refs if ref not in sop_filenames]
        packages.append(
            {
                **pkg,
                "sop_verified": verified,
                "sop_missing": missing,
                "ready": len(refs) > 0 and len(missing) == 0,
            },
        )

    ready_count = sum(1 for p in packages if p["ready"])
    return {
        "packages": packages,
        "total": len(packages),
        "ready": ready_count,
        "not_ready": len(packages) - ready_count,
    }


def _count_by_field(items: list[dict], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        val = str(item.get(field, "unknown"))
        counts[val] = counts.get(val, 0) + 1
    return counts
