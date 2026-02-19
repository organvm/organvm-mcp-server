"""Dependency graph tools.

Exposes the ORGANVM dependency graph — both inter-organ flow
(I→II→III, unidirectional) and intra-organ repo dependencies.
Governance rules enforce no back-edges.
"""

from __future__ import annotations

from typing import Any


def trace_dependencies(
    repo: str | None = None,
    organ: str | None = None,
    direction: str = "both",
    depth: int = 2,
) -> dict[str, Any]:
    """Trace the dependency graph from a repo or organ.

    Args:
        repo: Repository name (e.g., "organvm-engine"). Optional.
        organ: Organ key (e.g., "ORGAN-III"). Optional.
        direction: "upstream" (what I depend on), "downstream" (what depends
            on me), or "both".
        depth: Max traversal depth (default 2).

    Returns:
        {"root": "org/repo or organ",
         "upstream": [{"repo": "...", "organ": "...", "edge": "..."}],
         "downstream": [...],
         "depth": int}
    """
    from organvm_mcp.data.loader import load_registry
    from organvm_engine.registry.query import all_repos, find_repo
    
    registry = load_registry()
    
    # Build adjacency lists
    # repo -> list of dependencies (upstream)
    adj_upstream: dict[str, list[str]] = {}
    # repo -> list of dependents (downstream)
    adj_downstream: dict[str, list[str]] = {}
    
    repo_to_organ: dict[str, str] = {}
    
    for organ_key, r_data in all_repos(registry):
        name = r_data.get("name")
        deps = r_data.get("dependencies", []) or []
        adj_upstream[name] = deps
        repo_to_organ[name] = organ_key
        for d in deps:
            if d not in adj_downstream:
                adj_downstream[d] = []
            adj_downstream[d].append(name)

    # Determine roots
    roots = []
    if repo:
        roots.append(repo)
    elif organ:
        roots = [name for name, ok in repo_to_organ.items() if ok == organ]
    else:
        return {"error": "Must provide either repo or organ"}

    def traverse(start_nodes: list[str], adj: dict[str, list[str]], max_depth: int) -> list[dict]:
        results = []
        visited = set(start_nodes)
        queue = [(n, 1) for n in start_nodes]
        
        while queue:
            current, d = queue.pop(0)
            if d > max_depth:
                continue
                
            neighbors = adj.get(current, [])
            for neighbor in neighbors:
                if neighbor not in visited:
                    visited.add(neighbor)
                    results.append({
                        "repo": neighbor,
                        "organ": repo_to_organ.get(neighbor, "unknown"),
                        "level": d
                    })
                    queue.append((neighbor, d + 1))
        return results

    res: dict[str, Any] = {"root": repo or organ, "depth": depth}
    if direction in ["upstream", "both"]:
        res["upstream"] = traverse(roots, adj_upstream, depth)
    if direction in ["downstream", "both"]:
        res["downstream"] = traverse(roots, adj_downstream, depth)
        
    return res


def check_dependency(source_organ: str, target_organ: str) -> dict[str, Any]:
    """Check if a dependency between two organs is allowed.

    The ORGANVM governance model enforces unidirectional flow:
    I→II→III only. ORGAN-IV orchestrates all. No back-edges.

    Args:
        source_organ: The organ that would depend (e.g., "ORGAN-III").
        target_organ: The organ being depended on (e.g., "ORGAN-I").

    Returns:
        {"allowed": bool, "reason": "...",
         "rule": "governance-rules.json reference"}
    """
    from organvm_mcp.data.loader import load_governance_rules
    
    rules = load_governance_rules()
    if not rules:
        return {"allowed": True, "reason": "No governance rules found, defaulting to allowed"}
        
    allowed_edges = rules.get("allowed_edges", [])
    forbidden_edges = rules.get("forbidden_edges", [])
    
    edge = f"{source_organ}->{target_organ}"
    
    if edge in forbidden_edges:
        return {
            "allowed": False, 
            "reason": f"Dependency {edge} is explicitly forbidden by governance rules",
            "rule": "forbidden_edges"
        }
        
    if edge in allowed_edges:
        return {
            "allowed": True,
            "reason": f"Dependency {edge} is explicitly allowed",
            "rule": "allowed_edges"
        }
        
    # Default ORGANVM logic: I -> II -> III unidirectional
    # Map organ keys to numeric levels for comparison
    LEVELS = {
        "ORGAN-I": 1,
        "ORGAN-II": 2,
        "ORGAN-III": 3,
        "ORGAN-IV": 0, # Orchestration can see all
        "ORGAN-V": 4,  # Observation
        "ORGAN-VI": 5,
        "ORGAN-VII": 6,
        "META": 0
    }
    
    s_lv = LEVELS.get(source_organ)
    t_lv = LEVELS.get(target_organ)
    
    if s_lv is not None and t_lv is not None:
        if s_lv >= t_lv and s_lv > 0 and t_lv > 0:
            return {
                "allowed": True,
                "reason": f"Conforms to unidirectional flow ({source_organ} depends on {target_organ})"
            }
        elif s_lv < t_lv and s_lv > 0:
             return {
                "allowed": False,
                "reason": f"Violates unidirectional flow: {source_organ} cannot depend on downstream {target_organ}"
            }

    return {"allowed": True, "reason": "No specific rule found, allowing by default"}


def get_dependency_graph(organ: str | None = None) -> dict[str, Any]:
    """Get the full dependency graph or a subgraph for one organ.

    Args:
        organ: Optional organ filter. If None, returns the full system graph.

    Returns:
        {"nodes": [{"id": "org/repo", "organ": "...", "tier": "..."}],
         "edges": [{"source": "...", "target": "...", "type": "dependency|produces|consumes"}]}

    The output is structured for direct rendering as a graph visualization
    (compatible with D3, Mermaid, or the system-dashboard graph route).
    """
    from organvm_mcp.data.loader import load_registry, load_all_seeds
    from organvm_engine.registry.query import all_repos
    
    registry = load_registry()
    seeds = load_all_seeds()
    
    nodes = []
    edges = []
    
    # 1. Add nodes from registry
    for organ_key, repo in all_repos(registry):
        if organ and organ_key != organ:
            continue
            
        nodes.append({
            "id": repo.get("name"),
            "organ": organ_key,
            "tier": repo.get("tier"),
            "status": repo.get("promotion_status")
        })
        
        # Add dependency edges
        for dep in repo.get("dependencies", []) or []:
            edges.append({
                "source": repo.get("name"),
                "target": dep,
                "type": "dependency"
            })
            
    # 2. Add edges from seeds (produces/consumes)
    for seed in seeds:
        current_repo = seed.get("repo")
        current_organ = seed.get("organ")
        
        if organ and current_organ != organ:
            continue
            
        # produces
        for prod in seed.get("produces", []) or []:
            target = prod.get("target")
            if target:
                edges.append({
                    "source": current_repo,
                    "target": target,
                    "type": "produces",
                    "artifact": prod.get("artifact")
                })
                
        # consumes
        for cons in seed.get("consumes", []) or []:
            source = cons.get("source")
            if source:
                edges.append({
                    "source": source,
                    "target": current_repo,
                    "type": "consumes",
                    "artifact": cons.get("artifact")
                })
                
    return {"nodes": nodes, "edges": edges}
