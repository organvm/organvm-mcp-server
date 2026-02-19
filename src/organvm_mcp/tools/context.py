"""Contextual awareness tools.

The flagship tool: given the repo you're currently working in,
assembles everything an AI session needs to know — neighbors,
edges, governance constraints, organ context, and actionable notes.
"""

from __future__ import annotations

from typing import Any


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
    from organvm_mcp.data.loader import load_registry, load_all_seeds
    from organvm_engine.registry.query import find_repo, all_repos
    from pathlib import Path
    
    registry = load_registry()
    seeds = load_all_seeds()
    
    # 1. Resolve repo name and organization
    resolved_repo = repo
    resolved_org = org
    
    if cwd:
        cwd_path = Path(cwd).resolve()
        # Expecting path like .../Workspace/<organ-dir>/<repo-name>
        if cwd_path.name != "Workspace": # Not in root
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
                "governance": {"notes": ["Personal workspace repo — no inter-organ obligations"]}
            }
        return {"error": f"Repository '{resolved_repo}' not found in ORGANVM registry"}
        
    organ_key, repo_data = reg_result
    
    # 3. Assemble context
    organ_data = registry.get("organs", {}).get(organ_key, {})
    siblings = [r.get("name") for r in organ_data.get("repositories", []) if r.get("name") != resolved_repo]
    
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
            "org": organ_data.get("organization")
        },
        "edges": {
            "produces": produces,
            "consumes": consumes
        },
        "siblings": siblings[:10], # Limit sibling list
        "governance": {
            "upstream_organs": upstream,
            "downstream_organs": downstream,
            "notes": ["Unidirectional flow: I→II→III only."]
        }
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
    
    lines = [
        f"## System Context: {repo_data.get('name')}",
        "",
        f"**Organ:** {organ_data.get('key')} ({organ_data.get('name')})",
        f"**Tier:** {repo_data.get('tier')} | **Status:** {repo_data.get('promotion_status')}",
        ""
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
            
    return "\n".join(lines)
