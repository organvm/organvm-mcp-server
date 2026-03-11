"""Verification tools — formal verification of the dispatch pipeline."""

from __future__ import annotations

from typing import Any


def verify_system(
    include_ledger: bool = True,
) -> dict[str, Any]:
    """Run full system verification across all formal logic layers.

    Returns contract coverage, temporal ordering, and idempotency status.
    """
    from organvm_engine.seed.reader import read_seed
    from organvm_engine.verification.idempotency import DispatchLedger
    from organvm_engine.verification.model_check import verify_system as _verify

    from organvm_mcp.data.loader import load_all_seeds, load_registry

    registry = load_registry()

    # Build seed graph from loaded seeds
    raw_seeds = load_all_seeds()
    seed_graph: dict[str, dict] = {}
    for seed in raw_seeds:
        if isinstance(seed, dict):
            identity = f"{seed.get('org', 'unknown')}/{seed.get('repo', 'unknown')}"
            seed_graph[identity] = seed

    ledger = DispatchLedger() if include_ledger else None

    report = _verify(registry, seed_graph, ledger)
    return report.to_dict()


def verify_contracts(
    event: str | None = None,
) -> dict[str, Any]:
    """Check registered dispatch contracts.

    Args:
        event: Optional specific event type to check.

    Returns dict with contract details and validation status.
    """
    from organvm_engine.verification.contracts import CONTRACTS

    if event and event not in CONTRACTS:
        return {
            "error": f"No contract registered for event: {event}",
            "registered_events": sorted(CONTRACTS.keys()),
        }

    contracts = {event: CONTRACTS[event]} if event else CONTRACTS

    results = []
    for event_type, contract in sorted(contracts.items()):
        results.append({
            "event_type": event_type,
            "required_fields": {
                k: v.__name__ for k, v in contract.required_payload_fields.items()
            },
            "validator_count": len(contract.required_payload_validators),
            "consumes_trigger": contract.consumes_trigger,
            "post_condition": contract.post_condition,
            "is_vacuous": len(contract.required_payload_fields) == 0,
        })

    return {
        "total_contracts": len(results),
        "contracts": results,
    }
