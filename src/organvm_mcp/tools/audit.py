"""Infrastructure wiring audit tool."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def _workspace_root() -> Path:
    return Path(os.environ.get("ORGANVM_WORKSPACE_DIR", str(Path.home() / "Workspace")))


def infrastructure_audit(
    organ: str | None = None,
    layer: str | None = None,
    scope: str | None = None,
) -> dict[str, Any]:
    """Run infrastructure wiring audit.

    Args:
        organ: Optional organ filter (e.g. "ORGAN-I", "META-ORGANVM").
        layer: Optional single layer (filesystem, reconcile, seeds, edges, content, absorption).
        scope: Optional repo name to scope to.

    Returns:
        Audit report as dict.
    """
    from organvm_engine.audit.coordinator import run_audit

    from organvm_mcp.data.loader import load_registry

    registry = load_registry()
    workspace = _workspace_root()
    layers = [layer] if layer else None

    report = run_audit(
        registry=registry,
        workspace=workspace,
        scope_organ=organ,
        scope_repo=scope,
        layers=layers,
    )
    return report.to_dict()
