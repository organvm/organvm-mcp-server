"""Distill / pattern tools — operational patterns, coverage, scaffold generation."""

from __future__ import annotations

from typing import Any


def distill_patterns() -> dict[str, Any]:
    """List all operational patterns."""
    from organvm_engine.distill.taxonomy import OPERATIONAL_PATTERNS, all_pattern_ids

    patterns = []
    for pid in all_pattern_ids():
        p = OPERATIONAL_PATTERNS[pid]
        patterns.append(
            {
                "id": pid,
                "label": p.label,
                "description": p.description,
                "tier": p.tier,
                "scope": p.scope,
                "phase": p.phase,
                "sop_name_hint": p.sop_name_hint,
            },
        )

    return {
        "patterns": patterns,
        "total": len(patterns),
    }


def distill_coverage() -> dict[str, Any]:
    """SOP-to-pattern coverage analysis (simplified — without prompts)."""
    from organvm_engine.distill.taxonomy import OPERATIONAL_PATTERNS, all_pattern_ids
    from organvm_engine.sop.discover import discover_sops

    sops = discover_sops()
    sop_filenames = {e.filename for e in sops}

    entries = []
    covered = 0
    partial = 0
    uncovered = 0

    for pid in all_pattern_ids():
        p = OPERATIONAL_PATTERNS[pid]
        # Check sop_name_hint and aliases against discovered SOPs
        hints = [p.sop_name_hint] if p.sop_name_hint else []
        hints.extend(p.sop_name_aliases)
        matching = [h for h in hints if h in sop_filenames]
        if matching:
            status = "covered"
            covered += 1
        elif any(any(word in sf for word in p.label.lower().split()) for sf in sop_filenames):
            status = "partial"
            partial += 1
        else:
            status = "uncovered"
            uncovered += 1

        entries.append(
            {
                "pattern_id": pid,
                "pattern_label": p.label,
                "status": status,
                "matching_sops": matching,
            },
        )

    return {
        "entries": entries,
        "summary": {
            "total_patterns": len(entries),
            "covered": covered,
            "partial": partial,
            "uncovered": uncovered,
        },
    }


def distill_scaffold(pattern_id: str) -> dict[str, Any]:
    """Generate SOP scaffold for a pattern."""
    from organvm_engine.distill.scaffold import generate_sop_scaffold
    from organvm_engine.distill.taxonomy import get_pattern

    pattern = get_pattern(pattern_id)
    if pattern is None:
        return {"error": f"Pattern '{pattern_id}' not found"}

    scaffold = generate_sop_scaffold(pattern)
    return {
        "pattern_id": pattern_id,
        "pattern_label": pattern.label,
        "scaffold": scaffold,
    }
