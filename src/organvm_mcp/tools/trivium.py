"""Trivium tools — Dialectica Universalis via MCP.

Exposes dialect identity, translation matrix, structural correspondence
scanning, and trivium health to any Claude Code session.
"""

from __future__ import annotations

from typing import Any


def trivium_dialects() -> dict[str, Any]:
    """List all eight dialects with profiles and classical parallels."""
    from organvm_engine.trivium.dialects import all_dialects, dialect_profile

    dialects = []
    for d in all_dialects():
        p = dialect_profile(d)
        dialects.append({
            "dialect": d.value,
            "organ_key": p.organ_key,
            "organ_name": p.organ_name,
            "translation_role": p.translation_role,
            "formal_basis": p.formal_basis,
            "classical_parallel": p.classical_parallel,
            "description": p.description,
        })

    return {"dialects": dialects, "count": len(dialects)}


def trivium_matrix(organ: str | None = None) -> dict[str, Any]:
    """Show the 28-pair translation evidence matrix.

    Args:
        organ: Optional CLI organ key to filter pairs involving that organ.
    """
    from organvm_engine.trivium.dialects import dialect_for_organ, organ_for_dialect
    from organvm_engine.trivium.translator import translation_matrix

    matrix = translation_matrix()

    pairs = []
    for (a, b), ev in sorted(
        matrix.items(), key=lambda x: -x[1].aggregate_strength,
    ):
        a_key = organ_for_dialect(a)
        b_key = organ_for_dialect(b)
        if organ and organ not in (a_key, b_key):
            continue
        pairs.append({
            "source": a_key,
            "target": b_key,
            "correspondences": len(ev.correspondences),
            "strength": ev.aggregate_strength,
            "preservation": ev.preservation_assessment,
            "summary": ev.summary,
        })

    total_corr = sum(p["correspondences"] for p in pairs)
    avg = sum(p["strength"] for p in pairs) / len(pairs) if pairs else 0.0

    return {
        "pairs": pairs,
        "count": len(pairs),
        "total_correspondences": total_corr,
        "avg_strength": round(avg, 3),
        "filter": organ,
    }


def trivium_scan(organ_a: str, organ_b: str) -> dict[str, Any]:
    """Scan structural correspondences between two organs.

    Args:
        organ_a: First organ CLI key (e.g., "I", "III", "META").
        organ_b: Second organ CLI key.
    """
    from organvm_engine.trivium.detector import scan_organ_pair

    return scan_organ_pair(organ_a, organ_b)


def trivium_status() -> dict[str, Any]:
    """Trivium subsystem health summary."""
    from organvm_engine.trivium.sources import dialect_data, isomorphism_data
    from organvm_engine.trivium.taxonomy import TranslationTier, pairs_by_tier

    d_data = dialect_data()
    tier_counts = {
        tier.value: len(pairs_by_tier(tier))
        for tier in TranslationTier
    }

    return {
        "dialects": d_data["count"],
        "translation_pairs": 28,
        "tier_counts": tier_counts,
        "thesis": (
            "Language, mathematics, and algorithms are not different "
            "disciplines; they are merely different dialects of the "
            "same underlying universal logic."
        ),
        "spec": "SPEC-018",
    }
