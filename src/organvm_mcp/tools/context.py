"""Contextual awareness tools.

The flagship tool: given the repo you're currently working in,
assembles everything an AI session needs to know — neighbors,
edges, governance constraints, organ context, and actionable notes.
"""

from __future__ import annotations

from typing import Any


def conversation_corpus_surfaces(
    repo: str | None = None,
    state: str | None = None,
) -> dict[str, Any]:
    """Return discovered conversation corpus surfaces with optional filters."""
    from organvm_mcp.data.loader import load_conversation_corpus_surfaces

    report = load_conversation_corpus_surfaces()
    surfaces = report.get("surfaces", [])

    if repo:
        repo_name = repo.split("/")[-1]
        surfaces = [item for item in surfaces if item.get("repo") == repo_name]

    if state:
        surfaces = [item for item in surfaces if item.get("state") == state]

    digests = [_surface_digest(item) for item in surfaces]
    return {
        "surface_count": len(digests),
        "valid_count": sum(1 for item in digests if item["state"] == "valid"),
        "partial_count": sum(1 for item in digests if item["state"] == "partial"),
        "invalid_count": sum(1 for item in digests if item["state"] == "invalid"),
        "surfaces": digests,
    }


def get_context(
    repo: str | None = None,
    org: str | None = None,
    cwd: str | None = None,
) -> dict[str, Any]:
    """Get contextual awareness for a specific repo or working directory.

    This is the primary tool for cross-repo awareness. Call it at the
    start of any session to understand the current repo's place in the
    ORGANVM system.
    """
    from pathlib import Path

    from organvm_engine.registry.query import find_repo

    from organvm_mcp.data.loader import (
        load_all_seeds,
        load_conversation_corpus_surfaces,
        load_registry,
    )

    registry = load_registry()
    seeds = load_all_seeds()
    surface_report = load_conversation_corpus_surfaces()

    # 1. Resolve repo name and organization
    resolved_repo = repo
    resolved_org = org

    if cwd:
        cwd_path = Path(cwd).resolve()
        # Expecting path like .../Workspace/<organ-dir>/<repo-name>
        if cwd_path.name != "Workspace":  # Not in root
            resolved_repo = cwd_path.name
            parent = cwd_path.parent
            if parent.name != "Workspace":
                resolved_org = parent.name

    if not resolved_repo:
        return {"error": "Could not resolve repository name from arguments or CWD"}

    # 2. Look up repo in registry
    reg_result = find_repo(registry, resolved_repo)
    if not reg_result:
        # Check if it's a personal repo
        if resolved_org == "4444J99":
            return {
                "repo": {"name": resolved_repo, "org": "4444J99", "tier": "personal"},
                "governance": {"notes": ["Personal workspace repo — no inter-organ obligations"]},
                "conversation_corpus": _conversation_corpus_overview(
                    surface_report,
                    resolved_repo,
                ),
            }
        return {"error": f"Repository '{resolved_repo}' not found in ORGANVM registry"}

    organ_key, repo_data = reg_result

    # 3. Assemble context
    organ_data = registry.get("organs", {}).get(organ_key, {})
    siblings = [
        r.get("name") for r in organ_data.get("repositories", []) if r.get("name") != resolved_repo
    ]

    produces = []
    consumes = []
    # Find matching seed edges
    for seed in seeds:
        if seed.get("repo") == resolved_repo:
            produces = seed.get("produces", []) or []
            consumes = seed.get("consumes", []) or []

    # Default governance notes based on organ position
    LEVELS = {"ORGAN-I": 1, "ORGAN-II": 2, "ORGAN-III": 3}
    lv = LEVELS.get(organ_key, 0)
    upstream = [k for k, v in LEVELS.items() if v < lv]
    downstream = [k for k, v in LEVELS.items() if v > lv]

    return {
        "repo": {**repo_data, "organ": organ_key},
        "organ": {
            "key": organ_key,
            "name": organ_data.get("name"),
            "org": organ_data.get("organization"),
        },
        "edges": {"produces": produces, "consumes": consumes},
        "siblings": siblings[:10],  # Limit sibling list
        "governance": {
            "upstream_organs": upstream,
            "downstream_organs": downstream,
            "notes": ["Unidirectional flow: I→II→III only."],
        },
        "conversation_corpus": _conversation_corpus_overview(surface_report, resolved_repo),
    }


def get_context_markdown(
    repo: str | None = None,
    org: str | None = None,
    cwd: str | None = None,
) -> str:
    """Same as get_context() but returns pre-formatted Markdown.

    Useful for injecting directly into a Claude Code session as
    context, or for the CLAUDE.md auto-generator.

    Returns:
        Markdown string with sections: System Context, Edges,
        Siblings, Governance Notes.
    """
    ctx = get_context(repo, org, cwd)
    if "error" in ctx:
        return f"**Error:** {ctx['error']}"

    repo_data = ctx["repo"]
    organ_data = ctx["organ"]
    edges = ctx.get("edges", {})
    governance = ctx.get("governance", {})
    conversation_corpus = ctx.get("conversation_corpus", {})

    lines = [
        f"## System Context: {repo_data.get('name')}",
        "",
        f"**Organ:** {organ_data.get('key')} ({organ_data.get('name')})",
        f"**Tier:** {repo_data.get('tier')} | **Status:** {repo_data.get('promotion_status')}",
        "",
    ]

    if edges.get("produces"):
        lines.append("### Produces")
        for p in edges["produces"]:
            lines.append(f"- → `{p.get('target')}`: {p.get('artifact')}")
        lines.append("")

    if edges.get("consumes"):
        lines.append("### Consumes")
        for c in edges["consumes"]:
            lines.append(f"- ← `{c.get('source')}`: {c.get('artifact')}")
        lines.append("")

    if ctx.get("siblings"):
        lines.append(f"### Siblings in {organ_data.get('name')}")
        lines.append(", ".join(f"`{s}`" for s in ctx["siblings"]))
        lines.append("")

    if governance.get("notes"):
        lines.append("### Governance Notes")
        for n in governance["notes"]:
            lines.append(f"- {n}")

    if conversation_corpus.get("available"):
        lines.append("")
        lines.append("### Conversation Corpus")
        lines.append(
            "- Surfaces: "
            f"{conversation_corpus.get('surface_count', 0)} total / "
            f"{conversation_corpus.get('valid_count', 0)} valid",
        )
        default_surface = conversation_corpus.get("default_surface")
        if default_surface:
            lines.append(
                "- Default surface: "
                f"`{default_surface.get('organization')}/{default_surface.get('repo')}` "
                f"[{default_surface.get('state')}]",
            )
        current_repo_surface = conversation_corpus.get("current_repo_surface")
        if current_repo_surface:
            lines.append(
                "- Current repo surface: "
                f"`{current_repo_surface.get('organization')}/{current_repo_surface.get('repo')}` "
                f"[{current_repo_surface.get('state')}]",
            )

    return "\n".join(lines)


def _conversation_corpus_overview(
    report: dict[str, Any],
    resolved_repo: str,
) -> dict[str, Any]:
    surfaces = report.get("surfaces", [])
    current_repo_surface = next(
        (item for item in surfaces if item.get("repo") == resolved_repo),
        None,
    )
    default_surface = next(
        (item for item in surfaces if item.get("state") == "valid"),
        surfaces[0] if surfaces else None,
    )
    return {
        "available": bool(surfaces),
        "surface_count": report.get("surface_count", 0),
        "valid_count": report.get("valid_count", 0),
        "partial_count": report.get("partial_count", 0),
        "invalid_count": report.get("invalid_count", 0),
        "repositories": [
            f"{item.get('organization')}/{item.get('repo')}"
            for item in surfaces[:10]
        ],
        "default_surface": _surface_digest(default_surface) if default_surface else None,
        "current_repo_surface": (
            _surface_digest(current_repo_surface) if current_repo_surface else None
        ),
    }


def _surface_digest(surface: dict[str, Any] | None) -> dict[str, Any] | None:
    if surface is None:
        return None
    return {
        "repo": surface.get("repo"),
        "organization": surface.get("organization"),
        "repo_root": surface.get("repo_root"),
        "surface_dir": surface.get("surface_dir"),
        "state": surface.get("state"),
        "files": surface.get("files"),
        "summary": surface.get("summary"),
        "validation": surface.get("validation"),
    }
