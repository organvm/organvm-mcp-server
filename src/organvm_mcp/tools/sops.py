"""SOP discovery, audit, and resolution tools."""

from __future__ import annotations

from typing import Any


def sop_discover(organ: str | None = None) -> dict[str, Any]:
    """Discover all SOPs/METADOCs across the workspace."""
    from organvm_engine.sop.discover import discover_sops

    entries = discover_sops(organ=organ)
    return {
        "sops": [
            {
                "filename": e.filename,
                "title": e.title,
                "doc_type": e.doc_type,
                "scope": e.scope,
                "phase": e.phase,
                "canonical": e.canonical,
                "org": e.org,
                "repo": e.repo,
                "path": str(e.path),
            }
            for e in entries
        ],
        "total": len(entries),
        "by_type": _count_by(entries, "doc_type"),
        "by_scope": _count_by(entries, "scope"),
    }


def sop_audit() -> dict[str, Any]:
    """Audit SOP coverage vs METADOC inventory."""
    from organvm_engine.sop.discover import discover_sops
    from organvm_engine.sop.inventory import audit_sops

    discovered = discover_sops()
    result = audit_sops(discovered)
    return {
        "tracked": len(result.tracked),
        "untracked": len(result.untracked),
        "reference_copy": len(result.reference_copy),
        "missing": result.missing,
        "missing_count": len(result.missing),
        "untracked_files": [e.filename for e in result.untracked],
    }


def sop_resolve(
    repo: str | None = None,
    organ: str | None = None,
    phase: str | None = None,
) -> dict[str, Any]:
    """Resolve applicable SOPs for a context (T4>T3>T2 cascade)."""
    from organvm_engine.sop.discover import discover_sops
    from organvm_engine.sop.resolver import resolve_all

    discovered = discover_sops()
    resolved = resolve_all(discovered, repo=repo, organ=organ, phase=phase)
    return {
        "resolved": [
            {
                "filename": e.filename,
                "title": e.title,
                "doc_type": e.doc_type,
                "scope": e.scope,
                "phase": e.phase,
            }
            for e in resolved
        ],
        "total": len(resolved),
        "context": {"repo": repo, "organ": organ, "phase": phase},
    }


def _count_by(entries: list, attr: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for e in entries:
        val = getattr(e, attr, "unknown")
        counts[val] = counts.get(val, 0) + 1
    return counts
