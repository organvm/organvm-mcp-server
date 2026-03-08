"""Tests for governance tools."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from organvm_mcp.tools import governance


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
                        "org": "organvm-i-theoria",
                        "tier": "flagship",
                        "promotion_status": "GRADUATED",
                        "implementation_status": "ACTIVE",
                        "dependencies": [],
                    },
                    {
                        "name": "repo-b",
                        "org": "organvm-i-theoria",
                        "tier": "standard",
                        "promotion_status": "CANDIDATE",
                        "implementation_status": "ACTIVE",
                        "dependencies": ["repo-a"],
                    },
                ],
            },
            "ORGAN-II": {
                "name": "Art",
                "organization": "organvm-ii-poiesis",
                "repositories": [
                    {
                        "name": "repo-c",
                        "org": "organvm-ii-poiesis",
                        "tier": "flagship",
                        "promotion_status": "PUBLIC_PROCESS",
                        "implementation_status": "ACTIVE",
                        "dependencies": ["organvm-i-theoria/repo-a"],
                    },
                ],
            },
        },
    }


class TestGovernanceAudit:
    @patch("organvm_mcp.data.loader.load_governance_rules")
    @patch("organvm_mcp.data.loader.load_registry")
    def test_audit_returns_structure(self, mock_reg, mock_rules, mock_registry_data):
        mock_reg.return_value = mock_registry_data
        mock_rules.return_value = {}
        res = governance.governance_audit()
        assert "passed" in res
        assert "critical" in res
        assert "warnings" in res
        assert "critical_count" in res
        assert isinstance(res["critical"], list)


class TestGovernanceTransitions:
    def test_check_valid_transition(self):
        res = governance.governance_check_transition("LOCAL", "CANDIDATE")
        assert res["allowed"] is True

    def test_check_invalid_transition(self):
        res = governance.governance_check_transition("LOCAL", "GRADUATED")
        assert res["allowed"] is False

    def test_check_transition_fields(self):
        res = governance.governance_check_transition("CANDIDATE", "PUBLIC_PROCESS")
        assert res["current_state"] == "CANDIDATE"
        assert res["target_state"] == "PUBLIC_PROCESS"
        assert "reason" in res

    def test_valid_transitions_from_local(self):
        res = governance.governance_valid_transitions("LOCAL")
        assert "CANDIDATE" in res["valid_targets"]

    def test_valid_transitions_from_graduated(self):
        res = governance.governance_valid_transitions("GRADUATED")
        assert "ARCHIVED" in res["valid_targets"]


class TestGovernanceDeps:
    @patch("organvm_mcp.data.loader.load_registry")
    def test_validate_deps(self, mock_reg, mock_registry_data):
        mock_reg.return_value = mock_registry_data
        res = governance.governance_validate_deps()
        assert "passed" in res
        assert "total_edges" in res
        assert "violations" in res

    @patch("organvm_mcp.data.loader.load_registry")
    def test_validate_deps_has_edges(self, mock_reg, mock_registry_data):
        mock_reg.return_value = mock_registry_data
        res = governance.governance_validate_deps()
        assert res["total_edges"] >= 1


class TestGovernanceImpact:
    @patch("organvm_mcp.data.loader.load_registry")
    def test_impact_report(self, mock_reg, mock_registry_data):
        mock_reg.return_value = mock_registry_data
        res = governance.governance_impact("repo-a")
        assert res["source_repo"] == "repo-a"
        assert "affected_repos" in res
        assert "affected_count" in res


class TestGovernanceFeedbackLoops:
    @patch("organvm_mcp.data.loader.load_registry")
    def test_feedback_loops(self, mock_reg, mock_registry_data):
        mock_reg.return_value = mock_registry_data
        res = governance.governance_feedback_loops()
        assert isinstance(res, dict)
