"""Pulse tools — system mood, density, events, nerve wiring, memory.

Exposes the pulse nervous-system layer to any Claude Code session.
"""

from __future__ import annotations

import os
from dataclasses import asdict
from pathlib import Path
from typing import Any


def _workspace_root() -> Path:
    return Path(os.environ.get("ORGANVM_WORKSPACE_DIR", str(Path.home() / "Workspace")))


def pulse_mood() -> dict[str, Any]:
    """Compute and return the system mood."""
    from organvm_engine.metrics.organism import get_organism
    from organvm_engine.pulse.affective import MoodFactors, compute_mood
    from organvm_engine.pulse.density import compute_density
    from organvm_engine.seed.graph import build_seed_graph, validate_edge_resolution

    organism = get_organism(include_omega=False)
    workspace = _workspace_root()
    graph = build_seed_graph(workspace)
    unresolved = validate_edge_resolution(graph)
    dp = compute_density(graph, organism, len(unresolved))

    total = organism.total_repos or 1
    total_stale = organism.total_stale
    gate_stats = organism.gate_stats()
    avg_gate_rate = (
        sum(g.rate for g in gate_stats) / len(gate_stats) if gate_stats else 0.0
    )

    factors = MoodFactors(
        health_pct=organism.sys_pct,
        health_velocity=0.0,
        stale_ratio=total_stale / total,
        stale_velocity=0.0,
        density_score=dp.interconnection_score,
        gate_pass_rate=avg_gate_rate,
        promo_ready_ratio=organism.total_promo_ready / total,
        session_frequency=0.0,
    )

    mood_result = compute_mood(factors)
    return mood_result.to_dict()


def pulse_density() -> dict[str, Any]:
    """Compute and return interconnection density."""
    from organvm_engine.metrics.organism import get_organism
    from organvm_engine.pulse.density import compute_density
    from organvm_engine.seed.graph import build_seed_graph, validate_edge_resolution

    organism = get_organism(include_omega=False)
    workspace = _workspace_root()
    graph = build_seed_graph(workspace)
    unresolved = validate_edge_resolution(graph)
    dp = compute_density(graph, organism, len(unresolved))
    return dp.to_dict()


def pulse_events(
    event_type: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Return recent events from the event bus."""
    from organvm_engine.pulse.events import event_counts, replay

    events = replay(event_type=event_type, limit=limit)
    counts = event_counts()

    return {
        "events": [asdict(e) for e in events],
        "total_shown": len(events),
        "counts": counts,
    }


def pulse_nerve(event_type: str | None = None) -> dict[str, Any]:
    """Return subscription wiring from seed.yaml declarations."""
    from organvm_engine.pulse.nerve import resolve_subscriptions

    workspace = _workspace_root()
    bundle = resolve_subscriptions(workspace)

    if event_type:
        listeners = bundle.listeners_for(event_type)
        return {
            "event_type": event_type,
            "listener_count": len(listeners),
            "listeners": [s.to_dict() for s in listeners],
        }

    return bundle.to_dict()


def pulse_emit(
    event_type: str,
    source: str = "mcp",
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Emit an event and return propagation results."""
    from organvm_engine.pulse.events import emit
    from organvm_engine.pulse.nerve import propagate, resolve_subscriptions

    event = emit(event_type, source, payload or {})

    notified: list[dict] = []
    try:
        workspace = _workspace_root()
        bundle = resolve_subscriptions(workspace)
        notified = propagate(event, bundle)
    except Exception:
        pass

    return {
        "emitted": asdict(event),
        "notified": notified,
        "notified_count": len(notified),
    }


def pulse_briefing(hours: int = 24) -> dict[str, Any]:
    """Get session briefing for recent system activity."""
    try:
        from organvm_engine.pulse.continuity import build_briefing

        briefing = build_briefing(hours=hours)
        return briefing.to_dict()
    except ImportError:
        return {"error": "continuity module not yet available", "hours": hours}
    except Exception as exc:
        return {"error": str(exc), "hours": hours}


def pulse_memory(
    category: str | None = None,
    agent: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Query shared cross-agent memory."""
    try:
        from organvm_engine.pulse.shared_memory import query_insights

        insights = query_insights(category=category, agent=agent, limit=limit)
        return {
            "insights": [i.to_dict() for i in insights],
            "total": len(insights),
        }
    except ImportError:
        return {"error": "shared_memory module not yet available"}
    except Exception as exc:
        return {"error": str(exc)}


def pulse_record_insight(
    agent: str,
    category: str,
    content: str,
    tags: list[str] | None = None,
    organ: str | None = None,
    repo: str | None = None,
) -> dict[str, Any]:
    """Record a new insight to shared memory."""
    try:
        from organvm_engine.pulse.shared_memory import record_insight

        insight = record_insight(
            agent=agent,
            category=category,
            content=content,
            tags=tags,
            organ=organ,
            repo=repo,
        )
        return insight.to_dict()
    except ImportError:
        return {"error": "shared_memory module not yet available"}
    except Exception as exc:
        return {"error": str(exc)}


def pulse_flow() -> dict[str, Any]:
    """Compute dependency flow activity."""
    try:
        from organvm_engine.pulse.flow import compute_flow
        from organvm_engine.seed.graph import build_seed_graph

        workspace = _workspace_root()
        graph = build_seed_graph(workspace)
        profile = compute_flow(graph)
        return profile.to_dict()
    except ImportError:
        return {"error": "flow module not yet available"}
    except Exception as exc:
        return {"error": str(exc)}


def pulse_scan() -> dict[str, Any]:
    """Run a full pulse cycle: sensors + AMMOI computation."""
    try:
        from organvm_engine.pulse.rhythm import pulse_once

        workspace = _workspace_root()
        ammoi = pulse_once(workspace=workspace)
        return ammoi.to_dict()
    except ImportError:
        return {"error": "rhythm module not yet available"}
    except Exception as exc:
        return {"error": str(exc)}


def pulse_ammoi(
    organ: str | None = None,
    repo: str | None = None,
) -> dict[str, Any]:
    """Get AMMOI density at system, organ, or repo scale."""
    try:
        from organvm_engine.pulse.ammoi import compute_ammoi

        workspace = _workspace_root()
        ammoi = compute_ammoi(workspace=workspace)

        if organ and organ in ammoi.organs:
            return {
                "scale": "organ",
                "organ": organ,
                **ammoi.organs[organ].to_dict(),
                "system_density": ammoi.system_density,
                "compressed_text": ammoi.compressed_text,
            }

        return ammoi.to_dict()
    except ImportError:
        return {"error": "ammoi module not yet available"}
    except Exception as exc:
        return {"error": str(exc)}
