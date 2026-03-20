"""Seed contract query tools.

Exposes produces/consumes edges and event contracts from seed.yaml
files and the event catalog.
"""

from __future__ import annotations

from typing import Any


def get_seed(org: str, name: str) -> dict[str, Any]:
    """Get the parsed seed.yaml for a specific repository.

    Args:
        org: GitHub organization.
        name: Repository name.

    Returns:
        Full seed.yaml dict, or {"error": "seed.yaml not found"}.
    """
    from organvm_mcp.data.loader import load_all_seeds

    seeds = load_all_seeds()
    for seed in seeds:
        if seed.get("org") == org and seed.get("repo") == name:
            return seed

    return {"error": f"seed.yaml not found for {org}/{name}"}


def find_edges(
    repo: str | None = None,
    organ: str | None = None,
    direction: str = "both",
) -> dict[str, Any]:
    """Find produces/consumes edges for a repo or organ.

    Args:
        repo: Repository name (optional — if omitted, uses organ filter).
        organ: Organ key like "ORGAN-I" (optional — if omitted, uses repo filter).
        direction: "produces", "consumes", or "both" (default).

    Returns:
        {"edges": [
            {"source": "org/repo", "target": "org/repo", "artifact": "...",
             "event_type": "...", "direction": "produces|consumes"},
            ...
        ]}
    """
    from organvm_mcp.data.loader import load_all_seeds

    seeds = load_all_seeds()
    edges = []

    for seed in seeds:
        current_repo = f"{seed.get('org')}/{seed.get('repo')}"
        current_organ = seed.get("organ")

        # Check if this seed matches the filter
        if repo and seed.get("repo") != repo:
            continue
        if organ and current_organ != organ:
            continue

        # Extract produces
        if direction in ["produces", "both"]:
            for prod_entry in seed.get("produces", []) or []:
                prod_dict = {"artifact": prod_entry} if isinstance(prod_entry, str) else prod_entry
                edges.append(
                    {
                        "source": current_repo,
                        "source_organ": current_organ,
                        "target": prod_dict.get("target") or "unknown",
                        "artifact": prod_dict.get("artifact") or "unknown",
                        "event_type": prod_dict.get("event") or "",
                        "direction": "produces",
                    },
                )

        # Extract consumes
        if direction in ["consumes", "both"]:
            for cons_entry in seed.get("consumes", []) or []:
                cons_dict = {"artifact": cons_entry} if isinstance(cons_entry, str) else cons_entry
                edges.append(
                    {
                        "source": cons_dict.get("source") or "unknown",
                        "target": current_repo,
                        "target_organ": current_organ,
                        "artifact": cons_dict.get("artifact") or "unknown",
                        "event_type": cons_dict.get("event") or "",
                        "direction": "consumes",
                    },
                )

    return {"edges": edges}


def get_event_contract(event_type: str) -> dict[str, Any]:
    """Get the event catalog entry for a specific event type.

    Args:
        event_type: Event type string (e.g., "essay.published",
            "community.milestone", "theory.candidate").

    Returns:
        Event catalog entry with producer, consumer, edge, payload fields,
        and workflow references. Returns {"error": "..."} if not found.
    """
    from organvm_mcp.data.loader import load_event_catalog

    events = load_event_catalog()
    for ev in events:
        if ev.get("event_type") == event_type:
            return ev

    return {"error": f"Event type '{event_type}' not found in catalog"}


def list_events() -> dict[str, Any]:
    """List all event types in the event catalog.

    Returns:
        {"events": [
            {"event_type": "essay.published", "edge": "V→VI,VII",
             "producer": "ORGAN-V", "consumer": "ORGAN-VI,VII"},
            ...
        ]}
    """
    from organvm_mcp.data.loader import load_event_catalog

    events = load_event_catalog()
    summary = []
    for ev in events:
        summary.append(
            {
                "event_type": ev.get("event_type"),
                "edge": ev.get("edge"),
                "producer": ev.get("producer"),
                "consumer": ev.get("consumer"),
                "description": ev.get("description", ""),
            },
        )

    return {"events": summary}
