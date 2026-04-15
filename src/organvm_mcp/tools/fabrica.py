"""Fabrica tools — Cyclic Dispatch Protocol relay cycles (SPEC-024 Phase 6)."""

from __future__ import annotations

from typing import Any


def fabrica_status(
    packet_id: str | None = None,
    phase: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """List active relay cycles with dispatch records and current phase."""
    from organvm_engine.fabrica.mcp_tools import fabrica_status as _impl

    return _impl(packet_id=packet_id, phase=phase, limit=limit)


def fabrica_dispatch(
    text: str = "",
    source: str = "mcp",
    organ_hint: str | None = None,
    tags: list[str] | None = None,
    backend: str | None = None,
    repo: str | None = None,
    title: str | None = None,
    body: str | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Create a new dispatch — wraps RELEASE through HANDOFF."""
    from organvm_engine.fabrica.mcp_tools import fabrica_dispatch as _impl

    return _impl(
        text=text,
        source=source,
        organ_hint=organ_hint,
        tags=tags,
        backend=backend,
        repo=repo,
        title=title,
        body=body,
        dry_run=dry_run,
    )


def fabrica_log(
    packet_id: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """Show transition history for a relay cycle."""
    from organvm_engine.fabrica.mcp_tools import fabrica_log as _impl

    return _impl(packet_id=packet_id, limit=limit)


def fabrica_health() -> dict[str, Any]:
    """Return the health report — active/completed/failed counts."""
    from organvm_engine.fabrica.mcp_tools import fabrica_health as _impl

    return _impl()
