"""Tests for ecosystem MCP tools."""

from unittest.mock import patch

import pytest

from organvm_mcp.tools.ecosystem import (
    ecosystem_actions,
    ecosystem_gaps,
    ecosystem_matrix,
    ecosystem_profile,
)


@pytest.fixture
def sample_ecosystem_data():
    return [
        {
            "schema_version": "1.0",
            "repo": "test-product",
            "organ": "III",
            "display_name": "Test Product",
            "delivery": [
                {"platform": "web_app", "status": "live", "url": "https://test.com"},
                {"platform": "mobile_app_ios", "status": "planned"},
            ],
            "revenue": [
                {
                    "platform": "subscription",
                    "status": "planned",
                    "priority": "critical",
                    "next_action": "Stripe setup",
                },
            ],
        },
        {
            "schema_version": "1.0",
            "repo": "other-product",
            "organ": "III",
            "delivery": [
                {"platform": "cli", "status": "in_progress"},
            ],
        },
    ]


class TestEcosystemProfile:
    def test_found(self, sample_ecosystem_data):
        with patch(
            "organvm_mcp.tools.ecosystem._load_ecosystems",
            return_value=sample_ecosystem_data,
        ):
            result = ecosystem_profile("test-product")
            assert result["repo"] == "test-product"
            assert "delivery" in result["pillars"]
            assert result["pillars"]["delivery"]["count"] == 2

    def test_not_found(self, sample_ecosystem_data):
        with patch(
            "organvm_mcp.tools.ecosystem._load_ecosystems",
            return_value=sample_ecosystem_data,
        ):
            result = ecosystem_profile("nonexistent")
            assert "error" in result


class TestEcosystemMatrix:
    def test_matrix(self, sample_ecosystem_data):
        with patch(
            "organvm_mcp.tools.ecosystem._load_ecosystems",
            return_value=sample_ecosystem_data,
        ):
            result = ecosystem_matrix("delivery")
            assert result["pillar"] == "delivery"
            assert result["products_with_pillar"] == 2
            assert "test-product" in result["view"]

    def test_matrix_empty_pillar(self, sample_ecosystem_data):
        with patch(
            "organvm_mcp.tools.ecosystem._load_ecosystems",
            return_value=sample_ecosystem_data,
        ):
            result = ecosystem_matrix("listings")
            assert result["products_with_pillar"] == 0


class TestEcosystemGaps:
    def test_gaps(self, sample_ecosystem_data):
        with patch(
            "organvm_mcp.tools.ecosystem._load_ecosystems",
            return_value=sample_ecosystem_data,
        ):
            result = ecosystem_gaps()
            assert result["products_analyzed"] == 2
            # Both products should have gaps (missing pillars)
            assert result["products_with_gaps"] > 0

    def test_gaps_filtered_by_repo(self, sample_ecosystem_data):
        with patch(
            "organvm_mcp.tools.ecosystem._load_ecosystems",
            return_value=sample_ecosystem_data,
        ):
            result = ecosystem_gaps(repo="test-product")
            # Should only have test-product in gaps
            assert all(r == "test-product" for r in result["gaps"])


class TestEcosystemActions:
    def test_actions(self, sample_ecosystem_data):
        with patch(
            "organvm_mcp.tools.ecosystem._load_ecosystems",
            return_value=sample_ecosystem_data,
        ):
            result = ecosystem_actions()
            assert result["total_actions"] == 1
            assert result["actions"][0]["next_action"] == "Stripe setup"
