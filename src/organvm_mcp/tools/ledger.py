"""Ledger tools — Testament Protocol chain operations via MCP.

Exposes chain status, event log, verification, and digest to any
Claude Code session. The chain is the system's native blockchain —
every state mutation hash-linked to its predecessor.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

_CHAIN_PATH = Path.home() / ".organvm" / "testament" / "chain.jsonl"


def ledger_status() -> dict[str, Any]:
    """Chain status: event count, integrity, last sequence/hash."""
    from organvm_engine.ledger.chain import verify_chain

    if not _CHAIN_PATH.is_file():
        return {"exists": False, "event_count": 0, "message": "No chain found. Run `organvm ledger genesis`."}

    result = verify_chain(_CHAIN_PATH)
    return {
        "exists": True,
        "valid": result.valid,
        "event_count": result.event_count,
        "last_sequence": result.last_sequence,
        "last_hash": result.last_hash,
        "errors": result.errors[:5] if result.errors else [],
        "path": str(_CHAIN_PATH),
    }


def ledger_log(
    event_type: str | None = None,
    tier: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Query events from the chain with optional type/tier filter."""
    from dataclasses import asdict

    from organvm_engine.events.spine import EventSpine
    from organvm_engine.ledger.tiers import EventTier, classify_event_tier

    spine = EventSpine(_CHAIN_PATH)
    records = spine.query(event_type=event_type, limit=limit)

    if tier:
        target = EventTier(tier)
        records = [r for r in records if classify_event_tier(r.event_type) == target]

    events = []
    for r in records:
        d = asdict(r)
        d["tier"] = classify_event_tier(r.event_type).value
        events.append(d)

    return {"count": len(events), "events": events}


def ledger_verify() -> dict[str, Any]:
    """Full chain integrity verification from genesis."""
    from organvm_engine.ledger.chain import verify_chain

    if not _CHAIN_PATH.is_file():
        return {"verified": False, "error": "No chain found."}

    result = verify_chain(_CHAIN_PATH)
    return {
        "verified": result.valid,
        "event_count": result.event_count,
        "last_sequence": result.last_sequence,
        "errors": result.errors,
    }


def ledger_recent(limit: int = 10, tier: str | None = None) -> dict[str, Any]:
    """Most recent chain events, optionally filtered by tier."""
    return ledger_log(tier=tier, limit=limit)


def ledger_digest() -> dict[str, Any]:
    """Generate a digest summary of the current chain state."""
    from organvm_engine.events.spine import EventSpine
    from organvm_engine.ledger.digest import assemble_digest

    spine = EventSpine(_CHAIN_PATH)
    records = spine.query(limit=100_000)

    if not records:
        return {"event_count": 0, "text": "No events in chain."}

    digest = assemble_digest(records)
    return {
        "event_count": digest.event_count,
        "by_type": digest.by_type,
        "by_tier": digest.by_tier,
        "by_organ": digest.by_organ,
        "sequence_range": list(digest.sequence_range),
        "governance_highlights": digest.governance_highlights,
        "text": digest.render_text(),
    }
