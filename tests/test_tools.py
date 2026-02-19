"""Tests for MCP server tools."""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from organvm_mcp.tools import registry, seeds, graph, health, context


@pytest.fixture
def mock_registry_data():
    return {
        "organs": {
            "ORGAN-I": {
                "name": "Theory",
                "organization": "organvm-i-theoria",
                "repositories": [
                    {"name": "repo-a", "tier": "flagship", "promotion_status": "GRADUATED", "dependencies": []},
                    {"name": "repo-b", "tier": "standard", "promotion_status": "LOCAL", "dependencies": ["repo-a"]}
                ]
            }
        }
    }


class TestRegistryTools:
    @patch("organvm_mcp.data.loader.load_registry")
    def test_query_registry(self, mock_load, mock_registry_data):
        mock_load.return_value = mock_registry_data
        res = registry.query_registry(organ="ORGAN-I")
        assert len(res["repos"]) == 2
        assert res["total"] == 2

    @patch("organvm_mcp.data.loader.load_registry")
    def test_get_repo(self, mock_load, mock_registry_data):
        mock_load.return_value = mock_registry_data
        res = registry.get_repo(org="organvm-i-theoria", name="repo-a")
        assert res["name"] == "repo-a"
        assert res["organ"] == "ORGAN-I"


class TestSeedTools:
    @patch("organvm_mcp.data.loader.load_all_seeds")
    def test_find_edges(self, mock_load):
        mock_load.return_value = [
            {"org": "org", "repo": "repo-a", "organ": "ORGAN-I", "produces": [{"target": "repo-b", "artifact": "data"}]}
        ]
        res = seeds.find_edges(repo="repo-a")
        assert len(res["edges"]) == 1
        assert res["edges"][0]["target"] == "repo-b"


class TestGraphTools:
    @patch("organvm_mcp.data.loader.load_registry")
    def test_trace_dependencies(self, mock_load, mock_registry_data):
        mock_load.return_value = mock_registry_data
        res = graph.trace_dependencies(repo="repo-b", direction="upstream")
        assert len(res["upstream"]) == 1
        assert res["upstream"][0]["repo"] == "repo-a"


class TestContextTools:
    @patch("organvm_mcp.data.loader.load_registry")
    @patch("organvm_mcp.data.loader.load_all_seeds")
    def test_get_context(self, mock_seeds, mock_reg, mock_registry_data):
        mock_reg.return_value = mock_registry_data
        mock_seeds.return_value = []
        res = context.get_context(repo="repo-a")
        assert res["repo"]["name"] == "repo-a"
        assert res["organ"]["key"] == "ORGAN-I"
