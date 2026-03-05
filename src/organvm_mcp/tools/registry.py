"""Registry query tools.

Exposes the ORGANVM registry (100 repos, 8 organs) to MCP clients.
All functions return plain dicts for JSON serialization.
"""

from __future__ import annotations

from typing import Any


def query_registry(
    organ: str | None = None,
    tier: str | None = None,
    promotion_status: str | None = None,
    name_pattern: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Search and filter repos in the registry.

    Args:
        organ: Filter by organ key (e.g., "ORGAN-I", "ORGAN-III", "META").
        tier: Filter by tier ("flagship", "standard", "infrastructure", "archive").
        promotion_status: Filter by promotion status ("LOCAL", "CANDIDATE", etc.).
        name_pattern: Substring match on repo name (case-insensitive).
        limit: Max results to return (default 50).

    Returns:
        {"repos": [...], "total": int, "filters_applied": {...}}
    """
    from organvm_engine.registry.query import list_repos

    from organvm_mcp.data.loader import load_registry

    registry = load_registry()
    matches = list_repos(
        registry,
        organ=organ,
        promotion_status=promotion_status,
        tier=tier,
    )

    # Apply name pattern if provided
    if name_pattern:
        pat = name_pattern.lower()
        matches = [(o, r) for o, r in matches if pat in r.get("name", "").lower()]

    total = len(matches)
    results = [repo for _, repo in matches[:limit]]

    return {
        "repos": results,
        "total": total,
        "filters_applied": {
            "organ": organ,
            "tier": tier,
            "promotion_status": promotion_status,
            "name_pattern": name_pattern,
            "limit": limit,
        },
    }


def get_repo(org: str, name: str) -> dict[str, Any]:
    """Get full details for a specific repository.

    Args:
        org: GitHub organization (e.g., "organvm-i-theoria").
        name: Repository name (e.g., "recursive-engine--generative-entity").

    Returns:
        Full repo dict from registry including all metadata, launch_metrics,
        dependencies, and current status. Returns {"error": "..."} if not found.
    """
    from organvm_engine.registry.query import find_repo

    from organvm_mcp.data.loader import load_registry

    registry = load_registry()
    result = find_repo(registry, name)

    if not result:
        return {"error": f"Repository '{name}' not found in registry"}

    organ_key, repo = result
    # Ensure org matches if provided (registry doesn't always have org per repo,
    # but we can check the organ's organization)
    organ_data = registry.get("organs", {}).get(organ_key, {})
    if organ_data.get("organization") != org and repo.get("org") != org:
        return {
            "error": (
                f"Repository '{name}' found in {organ_key} but "
                f"organization mismatch (expected {org})"
            ),
        }

    return {**repo, "organ": organ_key}


def list_organs() -> dict[str, Any]:
    """List all organs with summary statistics.

    Returns:
        {"organs": [
            {"key": "ORGAN-I", "name": "Theory", "org": "organvm-i-theoria",
             "repo_count": 20, "flagship_count": 3, "local_count": 18, ...},
            ...
        ]}
    """
    from organvm_mcp.data.loader import load_registry

    registry = load_registry()
    organs = []

    for key, data in registry.get("organs", {}).items():
        repos = data.get("repositories", [])
        organs.append(
            {
                "key": key,
                "name": data.get("name"),
                "org": data.get("organization"),
                "repo_count": len(repos),
                "flagship_count": len([r for r in repos if r.get("tier") == "flagship"]),
                "standard_count": len([r for r in repos if r.get("tier") == "standard"]),
                "infrastructure_count": len(
                    [r for r in repos if r.get("tier") == "infrastructure"],
                ),
                "status_distribution": {
                    status: len([r for r in repos if r.get("promotion_status") == status])
                    for status in ["LOCAL", "CANDIDATE", "PUBLIC_PROCESS", "GRADUATED", "ARCHIVED"]
                },
            },
        )

    return {"organs": organs}
