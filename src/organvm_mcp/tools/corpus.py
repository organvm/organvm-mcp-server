"""Corpus knowledge graph MCP tools (IRF-SYS-104).

Exposes the constitutional source corpus as a queryable graph:
concepts, implementations, gaps, and statistics.
"""

from __future__ import annotations

import re
from typing import Any


def corpus_concepts(
    pattern: str | None = None,
    live: bool = False,
) -> dict[str, Any]:
    """List all concepts with implementation status."""
    from organvm_mcp.data.loader import load_corpus_graph

    graph = load_corpus_graph(live=live)
    concepts = graph.nodes_by_type("concept")

    if pattern:
        regex = re.compile(pattern, re.IGNORECASE)
        concepts = [c for c in concepts if regex.search(c.title) or regex.search(c.uid)]

    results = []
    for c in sorted(concepts, key=lambda x: x.uid):
        impls = [e for e in graph.edges_to(c.uid) if e.edge_type == "IMPLEMENTS"]
        impl_repos = []
        for e in impls:
            repo_node = graph.get_node(e.source)
            impl_repos.append({
                "repo": repo_node.title if repo_node else e.source,
                "aspect": e.metadata.get("aspect", ""),
            })

        results.append({
            "uid": c.uid,
            "title": c.title,
            "description": c.metadata.get("description", ""),
            "source": c.metadata.get("discovery", "cross_trunk"),
            "implementation_count": len(impls),
            "implementations": impl_repos,
        })

    return {
        "total": len(results),
        "implemented": sum(1 for r in results if r["implementation_count"] > 0),
        "unimplemented": sum(1 for r in results if r["implementation_count"] == 0),
        "concepts": results,
    }


def corpus_trace(
    concept: str,
    depth: int = 3,
    organ: str | None = None,
    live: bool = False,
) -> dict[str, Any]:
    """Trace a concept through the graph: transcripts → specs → repos."""
    from organvm_mcp.data.loader import load_corpus_graph

    graph = load_corpus_graph(live=live)

    # Resolve concept UID
    uid = concept if concept.startswith("concept:") else f"concept:{concept}"
    node = graph.get_node(uid)
    if node is None:
        # Try case-insensitive search
        for n in graph.nodes_by_type("concept"):
            if n.title.lower() == concept.lower():
                node = n
                uid = n.uid
                break
        if node is None:
            return {"error": f"Concept '{concept}' not found", "concept": concept}

    # Find defining sources (edges TO this concept with DEFINES type)
    defining = []
    for e in graph.edges_to(uid):
        if e.edge_type == "DEFINES":
            src_node = graph.get_node(e.source)
            defining.append({
                "source": e.source,
                "title": src_node.title if src_node else e.source,
                "type": src_node.node_type if src_node else "unknown",
            })

    # Find referencing transcripts
    referencing = []
    for e in graph.edges_to(uid):
        if e.edge_type == "REFERENCES":
            src_node = graph.get_node(e.source)
            referencing.append({
                "source": e.source,
                "title": src_node.title if src_node else e.source,
            })

    # Find compiled specs from defining transcripts
    compiled_specs = []
    for d in defining:
        for e in graph.edges_from(d["source"]):
            if e.edge_type == "COMPILES":
                spec_node = graph.get_node(e.target)
                if spec_node and spec_node not in compiled_specs:
                    compiled_specs.append({
                        "uid": spec_node.uid,
                        "title": spec_node.title,
                    })

    # Find implementing repos
    implementing = []
    for e in graph.edges_to(uid):
        if e.edge_type == "IMPLEMENTS":
            repo_node = graph.get_node(e.source)
            if repo_node:
                repo_organ = repo_node.metadata.get("organ", "")
                if organ and repo_organ.upper() != organ.upper():
                    continue
                implementing.append({
                    "repo": repo_node.title,
                    "organ": repo_organ,
                    "aspect": e.metadata.get("aspect", ""),
                })

    return {
        "concept": node.title,
        "uid": uid,
        "description": node.metadata.get("description", ""),
        "discovery": node.metadata.get("discovery", "cross_trunk"),
        "defining_sources": defining,
        "referencing_transcripts": referencing,
        "compiled_specs": compiled_specs,
        "implementing_repos": implementing,
        "implementation_count": len(implementing),
    }


def corpus_gaps(
    threshold: int = 2,
    live: bool = False,
) -> dict[str, Any]:
    """Find implementation gaps or fragile concepts."""
    from organvm_mcp.data.loader import load_corpus_graph

    graph = load_corpus_graph(live=live)
    concepts = graph.nodes_by_type("concept")

    robust = []
    fragile = []
    unimplemented = []

    for c in sorted(concepts, key=lambda x: x.uid):
        impls = [e for e in graph.edges_to(c.uid) if e.edge_type == "IMPLEMENTS"]
        count = len(impls)
        entry = {
            "concept": c.title,
            "uid": c.uid,
            "description": c.metadata.get("description", ""),
            "implementation_count": count,
            "sources": [
                graph.get_node(e.source).title if graph.get_node(e.source) else e.source
                for e in impls
            ],
        }
        if count == 0:
            unimplemented.append(entry)
        elif count < threshold:
            fragile.append(entry)
        else:
            robust.append(entry)

    return {
        "threshold": threshold,
        "total_concepts": len(concepts),
        "robust": len(robust),
        "fragile": len(fragile),
        "unimplemented": len(unimplemented),
        "fragile_concepts": fragile,
        "unimplemented_concepts": unimplemented,
    }


def corpus_stats(live: bool = False) -> dict[str, Any]:
    """Graph-level statistics and coverage metrics."""
    from organvm_mcp.data.loader import load_corpus_graph

    graph = load_corpus_graph(live=live)
    stats = graph.stats()

    concepts = graph.nodes_by_type("concept")
    implemented = sum(
        1 for c in concepts
        if any(e.edge_type == "IMPLEMENTS" for e in graph.edges_to(c.uid))
    )
    impl_counts = [
        sum(1 for e in graph.edges_to(c.uid) if e.edge_type == "IMPLEMENTS")
        for c in concepts
    ]
    avg_impl = sum(impl_counts) / len(impl_counts) if impl_counts else 0

    stats["coverage"] = {
        "total_concepts": len(concepts),
        "implemented": implemented,
        "unimplemented": len(concepts) - implemented,
        "coverage_ratio": round(implemented / len(concepts), 3) if concepts else 0,
        "avg_implementations_per_concept": round(avg_impl, 2),
    }

    return stats
