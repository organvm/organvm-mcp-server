"""Metrics tools — compute, consilience, timeseries, vars, lint."""

from __future__ import annotations

from typing import Any

from organvm_mcp.data.paths import workspace_root


def metrics_compute() -> dict[str, Any]:
    """System-wide metrics (repos, words, code, tests)."""
    from organvm_engine.metrics.calculator import compute_metrics

    from organvm_mcp.data.loader import load_registry

    registry = load_registry()
    return compute_metrics(registry, workspace=workspace_root())


def metrics_consilience() -> dict[str, Any]:
    """Consilience index report."""
    from organvm_engine.metrics.consilience import compute_consilience

    report = compute_consilience()
    return report.to_dict()


def metrics_ci_trend() -> dict[str, Any]:
    """CI pass rate trend over time."""
    from organvm_engine.metrics.timeseries import ci_trend, load_snapshots

    snapshots = load_snapshots()
    trend = ci_trend(snapshots)
    return {
        "trend": trend,
        "data_points": len(trend),
    }


def metrics_engagement_trend() -> dict[str, Any]:
    """Engagement metrics trend."""
    from organvm_engine.metrics.timeseries import engagement_trend, load_snapshots

    snapshots = load_snapshots()
    trend = engagement_trend(snapshots)
    return {
        "trend": trend,
        "data_points": len(trend),
    }


def metrics_vars() -> dict[str, Any]:
    """System variable manifest."""
    from organvm_engine.metrics.calculator import compute_metrics
    from organvm_engine.metrics.vars import build_vars

    from organvm_mcp.data.loader import load_registry

    registry = load_registry()
    raw_metrics = compute_metrics(registry, workspace=workspace_root())
    variables = build_vars(raw_metrics, registry)
    return {
        "variables": variables,
        "total": len(variables),
    }


def metrics_lint() -> dict[str, Any]:
    """Unbound metric reference lint across workspace."""
    from organvm_engine.metrics.calculator import compute_metrics
    from organvm_engine.metrics.lint_vars import lint_workspace
    from organvm_engine.metrics.vars import build_vars

    from organvm_mcp.data.loader import load_registry

    ws = workspace_root()
    registry = load_registry()
    raw_metrics = compute_metrics(registry, workspace=ws)
    variables = build_vars(raw_metrics, registry)
    report = lint_workspace(ws, variables)
    return {
        "files_scanned": report.files_scanned,
        "files_clean": report.files_clean,
        "total_violations": report.total_violations,
        "violations": [
            {
                "file": str(v.file),
                "line": v.line,
                "key": v.key,
                "value": v.value,
                "context": v.context,
            }
            for v in report.violations[:50]  # cap output
        ],
    }
