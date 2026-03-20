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
    rules = load_governance_rules()
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


def governance_dictums(level: str | None = None) -> dict[str, Any]:
    """List all constitutional dictums, optionally filtered by level."""
    from organvm_engine.governance.dictums import list_all_dictums

    from organvm_mcp.data.loader import load_governance_rules

    rules = load_governance_rules()
    all_dicts = list_all_dictums(rules)
    if level:
        all_dicts = [d for d in all_dicts if d["level"] == level]
    return {
        "count": len(all_dicts),
        "dictums": all_dicts,
    }


def governance_check_dictums() -> dict[str, Any]:
    """Run dictum compliance checks against the live registry."""
    from organvm_engine.governance.dictums import check_all_dictums

    from organvm_mcp.data.loader import load_governance_rules, load_registry

    registry = load_registry()
    rules = load_governance_rules()
    report = check_all_dictums(registry, rules)
    return report.to_dict()


def governance_placement(
    repo: str | None = None,
    audit_only: bool = False,
) -> dict[str, Any]:
    """Audit repo-to-organ placement affinity."""
    from organvm_engine.governance.placement import (
        audit_all_placements,
        load_organ_definitions,
        recommend_placement,
    )
    from organvm_engine.registry.query import find_repo

    from organvm_mcp.data.loader import load_registry

    registry = load_registry()
    definitions = load_organ_definitions()
    if not definitions:
        return {"error": "organ-definitions.json not found"}

    if repo:
        result = find_repo(registry, repo)
        if not result:
            return {"error": f"Repo '{repo}' not found"}
        _, repo_data = result
        rec = recommend_placement(repo_data, definitions)
        return rec.to_dict()

    audit = audit_all_placements(registry, definitions)
    out = audit.to_dict()
    if audit_only:
        out["questionable"] = out.get("questionable", [])
        out["misplaced"] = out.get("misplaced", [])
    return out


def governance_excavate(
    entity_type: str | None = None,
    severity: str | None = None,
    families_only: bool = False,
) -> dict[str, Any]:
    """Run buried entity excavation across the workspace."""

    from organvm_engine.governance.excavation import run_full_excavation
    from organvm_engine.paths import workspace_root

    from organvm_mcp.data.loader import load_registry

    registry = load_registry()
    workspace = workspace_root()

    report = run_full_excavation(workspace, registry)

    if families_only:
        return {
            "cross_organ_families": report.cross_organ_families,
            "family_count": len(report.cross_organ_families),
        }

    findings = report.findings
    if entity_type:
        findings = [f for f in findings if f.entity_type == entity_type]
    if severity:
        sev_order = {"info": 0, "warning": 1, "critical": 2}
        min_sev = sev_order.get(severity, 0)
        findings = [
            f for f in findings
            if sev_order.get(f.severity, 0) >= min_sev
        ]

    out = report.to_dict()
    out["findings"] = [f.to_dict() for f in findings]
    return out
