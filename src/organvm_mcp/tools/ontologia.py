"""Ontologia structural registry tools.

Exposes entity resolution, listing, history, events, and store status
from the ontologia package. All functions return plain dicts for JSON
serialization. Degrades gracefully when ontologia is not installed.
"""

from __future__ import annotations

from typing import Any


def _check_available() -> dict[str, Any] | None:
    """Return error dict if ontologia is not installed, else None."""
    try:
        from ontologia.registry.store import open_store  # noqa: F401

        return None
    except ImportError:
        return {
            "error": "organvm-ontologia is not installed",
            "hint": "pip install -e ../organvm-ontologia/",
        }


def ontologia_resolve(query: str) -> dict[str, Any]:
    """Resolve an entity by name, UID, slug, or alias.

    Args:
        query: Entity UID, display name, slug, or alias.

    Returns:
        Entity details with uid, type, status, name, and match method.
    """
    err = _check_available()
    if err:
        return err

    from ontologia.registry.store import open_store

    store = open_store()
    resolver = store.resolver()
    resolved = resolver.resolve(query)

    if resolved is None:
        return {"error": f"No entity found for: {query}"}

    name = store.current_name(resolved.identity.uid)
    return {
        "uid": resolved.identity.uid,
        "entity_type": resolved.identity.entity_type.value,
        "lifecycle_status": resolved.identity.lifecycle_status.value,
        "display_name": name.display_name if name else None,
        "matched_by": resolved.matched_by,
        "created_at": resolved.identity.created_at,
    }


def ontologia_list(
    entity_type: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """List entities with optional type filter.

    Args:
        entity_type: Filter by entity type (organ, repo, module, document).
        limit: Max results (default 50).

    Returns:
        {"entities": [...], "total": int}
    """
    err = _check_available()
    if err:
        return err

    from ontologia.entity.identity import EntityType
    from ontologia.registry.store import open_store

    store = open_store()
    et = None
    if entity_type:
        try:
            et = EntityType(entity_type)
        except ValueError:
            return {"error": f"Unknown entity type: {entity_type}"}

    entities = store.list_entities(entity_type=et)
    rows = []
    for e in entities[:limit]:
        name = store.current_name(e.uid)
        rows.append({
            "uid": e.uid,
            "entity_type": e.entity_type.value,
            "lifecycle_status": e.lifecycle_status.value,
            "display_name": name.display_name if name else None,
        })

    return {"entities": rows, "total": len(entities)}


def ontologia_history(entity: str) -> dict[str, Any]:
    """Show name history for an entity.

    Args:
        entity: Entity UID or name to look up.

    Returns:
        {"uid": str, "names": [...]} with temporal name records.
    """
    err = _check_available()
    if err:
        return err

    from ontologia.registry.store import open_store

    store = open_store()
    resolver = store.resolver()
    resolved = resolver.resolve(entity)

    if resolved is None:
        return {"error": f"Entity not found: {entity}"}

    names = store.name_history(resolved.identity.uid)
    return {
        "uid": resolved.identity.uid,
        "names": [
            {
                "display_name": n.display_name,
                "slug": n.slug,
                "is_primary": n.is_primary,
                "valid_from": n.valid_from,
                "valid_to": n.valid_to,
            }
            for n in names
        ],
    }


def ontologia_events(limit: int = 20) -> dict[str, Any]:
    """Show recent ontologia events.

    Args:
        limit: Max events to return (default 20).

    Returns:
        {"events": [...], "total": int}
    """
    err = _check_available()
    if err:
        return err

    from ontologia.registry.store import open_store

    store = open_store()
    events = store.events(limit=limit)

    return {
        "events": [
            {
                "timestamp": e.timestamp,
                "event_type": e.event_type,
                "subject_entity": e.subject_entity,
            }
            for e in events
        ],
        "total": len(events),
    }


def ontologia_status() -> dict[str, Any]:
    """Show ontologia store status summary.

    Returns:
        Store path, entity counts by type and status, last event.
    """
    err = _check_available()
    if err:
        return err

    from ontologia.registry.store import open_store

    store = open_store()
    entities = store.list_entities()
    events = store.events(limit=1)

    by_type: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for e in entities:
        by_type[e.entity_type.value] = by_type.get(e.entity_type.value, 0) + 1
        by_status[e.lifecycle_status.value] = by_status.get(e.lifecycle_status.value, 0) + 1

    result: dict[str, Any] = {
        "store_dir": str(store.store_dir),
        "entity_count": len(entities),
        "by_type": by_type,
        "by_status": by_status,
    }
    if events:
        result["last_event"] = {
            "timestamp": events[-1].timestamp,
            "event_type": events[-1].event_type,
        }
    return result


def ontologia_sense(
    sensor: str | None = None,
) -> dict[str, Any]:
    """Run sensors and return detected changes.

    Args:
        sensor: Optional sensor name to run (registry_sensor, soak_sensor,
                ci_sensor, promotion_sensor). Runs all if not specified.

    Returns:
        {sensor_name: [signals...]} grouped by sensor.
    """
    from organvm_engine.ontologia.sensors import scan_all

    results = scan_all(sensor_filter=sensor)
    # Convert signals to plain dicts
    out: dict[str, list] = {}
    for name, signals in results.items():
        out[name] = [
            {
                "sensor": s.sensor_name if hasattr(s, "sensor_name") else s.get("sensor", ""),
                "type": s.signal_type if hasattr(s, "signal_type") else s.get("type", ""),
                "entity": s.entity_id if hasattr(s, "entity_id") else s.get("entity", ""),
                "details": s.details if hasattr(s, "details") else s.get("details", {}),
            }
            for s in signals
        ]
    total = sum(len(v) for v in out.values())
    return {"sensors": out, "total_signals": total}


def ontologia_tensions() -> dict[str, Any]:
    """Run tension detection across all entities.

    Returns:
        Orphans, naming conflicts, overcoupled entities with severity scores.
    """
    from organvm_engine.ontologia.inference_bridge import detect_tensions

    return detect_tensions()


def ontologia_policies(evaluate: bool = False) -> dict[str, Any]:
    """List or evaluate governance policies.

    Args:
        evaluate: If True, evaluate policies against all entities.
                  If False, just list the defined policies.

    Returns:
        Policy list or evaluation results with triggered policies.
    """
    from organvm_engine.ontologia.policies import evaluate_all_policies, load_policies

    if evaluate:
        return evaluate_all_policies()
    return {"policies": load_policies()}


def ontologia_health(entity: str | None = None) -> dict[str, Any]:
    """Composite entity health — tensions, clusters, and blast radius.

    Args:
        entity: Optional entity UID or name for per-entity detail.

    Returns:
        Combined health view with tensions, clusters, and optional entity detail.
    """
    from organvm_engine.ontologia.inference_bridge import infer_health

    return infer_health(entity_query=entity)


def ontologia_snapshot(compare: bool = False) -> dict[str, Any]:
    """Create or compare state snapshots.

    Args:
        compare: If True, compare two most recent snapshots for drift.
                 If False, create a new snapshot.

    Returns:
        Snapshot creation result or drift detection result.
    """
    from organvm_engine.ontologia.snapshots import create_system_snapshot, detect_drift

    if compare:
        return detect_drift()
    return create_system_snapshot()


def ontologia_revisions(status: str | None = None, limit: int = 50) -> dict[str, Any]:
    """Query the revision log.

    Args:
        status: Filter by revision status (detected, proposed, applied, etc.).
        limit: Max revisions to return (default 50).

    Returns:
        {"revisions": [...], "total": int}
    """
    from organvm_engine.ontologia.policies import load_revisions

    revisions = load_revisions(status=status, limit=limit)
    return {"revisions": revisions, "total": len(revisions)}


def ontologia_bridge_resolve(
    query: str,
    include_registry: bool = True,
) -> dict[str, Any]:
    """Resolve an entity using the engine's bridge function.

    Checks ontologia first, falls back to registry name lookup.
    This is the unified resolution path that combines both data sources.

    Args:
        query: Entity UID, name, slug, or alias.
        include_registry: Whether to include registry fallback (default True).

    Returns:
        Unified result with source indicator (ontologia vs registry).
    """
    from organvm_engine.registry.query import resolve_entity

    registry = None
    if include_registry:
        from organvm_mcp.data.loader import load_registry

        registry = load_registry()

    result = resolve_entity(query, registry=registry)
    if result is None:
        return {"error": f"Entity not found anywhere: {query}"}
    return result
