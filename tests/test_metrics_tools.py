"""Tests for metrics tools."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from organvm_mcp.tools import metrics


@pytest.fixture
def mock_registry_data():
    return {
        "organs": {
            "ORGAN-I": {
                "name": "Theory",
                "organization": "organvm-i-theoria",
                "repositories": [
                    {
                        "name": "repo-a",
                        "tier": "flagship",
                        "promotion_status": "GRADUATED",
                        "implementation_status": "ACTIVE",
                        "dependencies": [],
                    },
                ],
            },
        },
    }


class TestMetricsCompute:
    @patch("organvm_mcp.data.loader.load_registry")
    def test_compute_returns_dict(self, mock_reg, mock_registry_data):
        mock_reg.return_value = mock_registry_data
        res = metrics.metrics_compute()
        assert isinstance(res, dict)
        assert "total_repos" in res


class TestMetricsConsilience:
    @patch("organvm_engine.metrics.consilience.compute_consilience")
    def test_consilience_structure(self, mock_compute):
        from organvm_engine.metrics.consilience import ConsilienceReport

        mock_compute.return_value = ConsilienceReport(
            principles=[],
            research_docs=[],
        )
        res = metrics.metrics_consilience()
        assert isinstance(res, dict)


class TestMetricsCiTrend:
    @patch("organvm_engine.metrics.timeseries.load_snapshots")
    def test_ci_trend(self, mock_load):
        mock_load.return_value = [
            {
                "date": "2026-03-01",
                "ci": {"total_checked": 10, "passing": 8, "failing": 2},
            },
            {
                "date": "2026-03-02",
                "ci": {"total_checked": 10, "passing": 9, "failing": 1},
            },
        ]
        res = metrics.metrics_ci_trend()
        assert res["data_points"] == 2
        assert len(res["trend"]) == 2

    @patch("organvm_engine.metrics.timeseries.load_snapshots")
    def test_ci_trend_empty(self, mock_load):
        mock_load.return_value = []
        res = metrics.metrics_ci_trend()
        assert res["data_points"] == 0


class TestMetricsEngagementTrend:
    @patch("organvm_engine.metrics.timeseries.load_snapshots")
    def test_engagement_trend(self, mock_load):
        mock_load.return_value = [
            {
                "date": "2026-03-01",
                "engagement": {"stars": 5, "forks": 2},
            },
        ]
        res = metrics.metrics_engagement_trend()
        assert res["data_points"] == 1


class TestMetricsVars:
    @patch("organvm_mcp.data.loader.load_registry")
    def test_vars_structure(self, mock_reg, mock_registry_data):
        mock_reg.return_value = mock_registry_data
        res = metrics.metrics_vars()
        assert "variables" in res
        assert "total" in res
        assert isinstance(res["variables"], dict)


class TestMetricsLint:
    @patch("organvm_engine.metrics.lint_vars.lint_workspace")
    @patch("organvm_mcp.data.loader.load_registry")
    def test_lint_structure(self, mock_reg, mock_lint, mock_registry_data):
        from organvm_engine.metrics.lint_vars import LintReport

        mock_reg.return_value = mock_registry_data
        mock_lint.return_value = LintReport(files_scanned=10, files_clean=8)
        res = metrics.metrics_lint()
        assert res["files_scanned"] == 10
        assert res["total_violations"] == 0
