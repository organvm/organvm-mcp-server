"""Testament tools — the system's generative self-portrait via MCP.

Exposes testament status, catalog, and rendering to any Claude Code session.
"""

from __future__ import annotations

from typing import Any


def testament_status() -> dict[str, Any]:
    """What the system can produce and has produced."""
    from organvm_engine.testament.catalog import catalog_summary, load_catalog
    from organvm_engine.testament.manifest import (
        MODULE_SOURCES,
        ORGAN_OUTPUT_MATRIX,
        all_artifact_types,
    )

    types = all_artifact_types()
    catalog = load_catalog()
    summary = catalog_summary(catalog)

    return {
        "registered_types": len(types),
        "organ_profiles": len(ORGAN_OUTPUT_MATRIX),
        "source_modules": len(MODULE_SOURCES),
        "catalog_total": summary.total,
        "by_modality": summary.by_modality,
        "by_organ": summary.by_organ,
        "latest_timestamp": summary.latest_timestamp,
        "modalities": [m.value for m in sorted(
            {t.modality for t in types}, key=lambda m: m.value,
        )],
    }


def testament_catalog(organ: str | None = None) -> dict[str, Any]:
    """List all produced testament artifacts."""
    import dataclasses

    from organvm_engine.testament.catalog import load_catalog

    catalog = load_catalog()
    if organ:
        catalog = [a for a in catalog if a.organ == organ]

    artifacts = []
    for a in catalog:
        d = dataclasses.asdict(a)
        d["modality"] = a.modality.value if hasattr(a.modality, "value") else str(a.modality)
        d["format"] = a.format.value if hasattr(a.format, "value") else str(a.format)
        artifacts.append(d)

    return {
        "total": len(artifacts),
        "artifacts": artifacts,
    }


def testament_render(organ: str | None = None, write: bool = False) -> dict[str, Any]:
    """Render testament artifacts from live system data.

    Dry-run by default — set write=True to produce files.
    """
    from pathlib import Path

    from organvm_engine.testament.pipeline import render_all, render_organ
    output_dir = Path.home() / ".organvm" / "testament" / "artifacts"

    if organ:
        results = render_organ(organ, output_dir, dry_run=not write)
    else:
        results = render_all(output_dir, dry_run=not write)

    succeeded = [r for r in results if r.success]
    failed = [r for r in results if not r.success]

    return {
        "dry_run": not write,
        "total": len(results),
        "succeeded": len(succeeded),
        "failed": len(failed),
        "artifacts": [
            {
                "title": r.artifact.title,
                "modality": r.artifact.modality.value,
                "organ": r.artifact.organ,
                "path": r.artifact.path if r.success else None,
                "error": r.error,
            }
            for r in results
        ],
    }
