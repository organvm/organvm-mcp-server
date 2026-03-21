"""IRF query tool for MCP."""
from __future__ import annotations

import dataclasses
from typing import Any


def irf_query(
    item_id: str | None = None,
    priority: str | None = None,
    domain: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Query IRF items. Returns matching items + stats."""
    from organvm_engine.irf import irf_stats, parse_irf, query_irf
    from organvm_engine.paths import irf_path

    items = parse_irf(irf_path())
    filters = {}
    if item_id:
        filters["item_id"] = item_id
    if priority:
        filters["priority"] = priority
    if domain:
        filters["domain"] = domain
    if status:
        filters["status"] = status

    result = query_irf(items, **filters) if filters else [i for i in items if i.status == "open"]

    return {
        "items": [dataclasses.asdict(i) for i in result[:limit]],
        "total_matching": len(result),
        "stats": irf_stats(items),
    }
