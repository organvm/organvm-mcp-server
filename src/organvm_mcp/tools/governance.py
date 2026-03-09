"""Governance tools — audit, state machine, dependency graph, impact, feedback loops."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from organvm_engine.ci.mandate import CIMandateReport


def governance_audit() -> dict[str, Any]:
    """Run a full system governance audit."""
    from organvm_engine.governance.audit import run_audit

    from organvm_mcp.data.loader import load_governance_rules, load_registry

    registry = load_registry()
    rules = load_governance_rules() or None
    result = run_audit(registry, rules=rules, verify_ci=True)
    out: dict[str, Any] = {
        "passed": result.passed,
        "critical": result.critical,
        "warnings": result.warnings,
        "info": result.info,
        "critical_count": len(result.critical),
        "warning_count": len(result.warnings),
    }
    if result.ci_mandate is not None:
        mandate = cast("CIMandateReport", result.ci_mandate)
        out["ci_mandate"] = {
            "total": mandate.total,
            "has_ci": mandate.has_ci,
            "missing_ci": mandate.missing_ci,
            "adherence_rate": round(mandate.adherence_rate, 4),
            "drift": mandate.drift_from_registry(registry),
        }
    return out


def governance_check_transition(
    current_state: str,
    target_state: str,
) -> dict[str, Any]:
    """Validate a promotion state transition."""
    from organvm_engine.governance.state_machine import check_transition

    allowed, reason = check_transition(current_state, target_state)
    return {
        "current_state": current_state,
        "target_state": target_state,
        "allowed": allowed,
        "reason": reason,
    }


def governance_valid_transitions(current_state: str) -> dict[str, Any]:
    """List valid transitions from a given promotion state."""
    from organvm_engine.governance.state_machine import get_valid_transitions

    transitions = get_valid_transitions(current_state)
    return {
        "current_state": current_state,
        "valid_targets": transitions,
    }


def governance_validate_deps() -> dict[str, Any]:
    """Validate the full dependency graph against governance rules."""
    from organvm_engine.governance.dependency_graph import validate_dependencies

    from organvm_mcp.data.loader import load_registry

    registry = load_registry()
    result = validate_dependencies(registry)
    return {
        "passed": result.passed,
        "total_edges": result.total_edges,
        "violations": result.violations,
        "missing_targets": [{"from": f, "to": t} for f, t in result.missing_targets],
        "self_deps": result.self_deps,
        "back_edges": [
            {"from_repo": f, "to_repo": t, "from_org": fo, "to_org": to}
            for f, t, fo, to in result.back_edges
        ],
        "cycles": result.cycles,
        "cross_organ": result.cross_organ,
    }


def governance_impact(repo_name: str) -> dict[str, Any]:
    """Calculate blast radius for a repo change."""
    from organvm_engine.governance.impact import calculate_impact

    from organvm_mcp.data.loader import load_registry

    registry = load_registry()
    report = calculate_impact(repo_name, registry)
    return {
        "source_repo": report.source_repo,
        "affected_repos": report.affected_repos,
        "affected_count": len(report.affected_repos),
        "impact_graph": report.impact_graph,
    }


def governance_feedback_loops() -> dict[str, Any]:
    """Get feedback loop inventory with active detection."""
    from organvm_engine.governance.feedback_loops import detect_active_loops

    from organvm_mcp.data.loader import load_registry

    registry = load_registry()
    inventory = detect_active_loops(registry)
    return inventory.to_dict()
