"""Coordination tools — punch-in/punch-out work claims across AI streams."""

from __future__ import annotations

from typing import Any


def coordination_punch_in(
    agent: str = "claude",
    session_id: str = "",
    organs: list[str] | None = None,
    repos: list[str] | None = None,
    files: list[str] | None = None,
    modules: list[str] | None = None,
    scope: str = "",
    resource_weight: str = "medium",
    test_obligations: list[str] | None = None,
) -> dict[str, Any]:
    """Punch in: declare areas of influence for this work session."""
    from organvm_engine.coordination.claims import punch_in

    return punch_in(
        agent=agent,
        session_id=session_id,
        organs=organs,
        repos=repos,
        files=files,
        modules=modules,
        scope=scope,
        resource_weight=resource_weight,
        test_obligations=test_obligations,
    )


def coordination_punch_out(claim_id: str) -> dict[str, Any]:
    """Punch out: release a claim on areas of influence."""
    from organvm_engine.coordination.claims import punch_out

    return punch_out(claim_id)


def coordination_work_board() -> dict[str, Any]:
    """Get the current work board — who's working on what."""
    from organvm_engine.coordination.claims import work_board

    return work_board()


def coordination_check_conflicts(
    organs: list[str] | None = None,
    repos: list[str] | None = None,
    files: list[str] | None = None,
    modules: list[str] | None = None,
) -> dict[str, Any]:
    """Check if proposed areas conflict with active claims."""
    from organvm_engine.coordination.claims import check_conflicts

    conflicts = check_conflicts(
        organs=organs, repos=repos, files=files, modules=modules,
    )
    return {
        "conflict_count": len(conflicts),
        "conflicts": [
            {
                "with_handle": c.existing_claim.handle,
                "with_agent": c.existing_claim.agent,
                "with_session": c.existing_claim.session_id,
                "overlap_type": c.overlap_type,
                "overlap_values": c.overlap_values,
                "claimed_scope": c.existing_claim.scope,
                "areas": c.existing_claim.areas,
            }
            for c in conflicts
        ],
    }


def coordination_capacity() -> dict[str, Any]:
    """Get current resource capacity status."""
    from organvm_engine.coordination.claims import capacity_status

    return capacity_status()


def coordination_prove_sweep() -> dict[str, Any]:
    """Collect all pending test obligations for a single prover session."""
    from organvm_engine.coordination.claims import prove_sweep

    return prove_sweep()


def coordination_tool_checkout(
    handle: str = "",
    tool: str = "bash",
    command_hint: str = "",
    weight: str | None = None,
) -> dict[str, Any]:
    """Check out a tool before running a command. Returns clear/wait."""
    from organvm_engine.coordination.tool_lock import tool_checkout

    return tool_checkout(
        handle=handle, tool=tool,
        command_hint=command_hint, weight=weight,
    )


def coordination_tool_checkin(checkout_id: str = "") -> dict[str, Any]:
    """Check in a tool after a command completes."""
    from organvm_engine.coordination.tool_lock import tool_checkin

    return tool_checkin(checkout_id)


def coordination_tool_queue() -> dict[str, Any]:
    """View the tool checkout queue — who's running what right now."""
    from organvm_engine.coordination.tool_lock import tool_queue

    return tool_queue()
