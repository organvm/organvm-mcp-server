"""Tests for MCP data loader caching and error handling."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import yaml

import organvm_mcp.data.loader as loader_mod


class TestLoaderCaching:
    def setup_method(self):
        loader_mod.reload()

    def teardown_method(self):
        loader_mod.reload()

    @patch("organvm_mcp.data.loader._read_json")
    @patch("organvm_mcp.data.loader.registry_path")
    def test_load_registry_caches(self, mock_path, mock_read):
        mock_read.return_value = {"organs": {}}
        first = loader_mod.load_registry()
        second = loader_mod.load_registry()
        assert first is second
        mock_read.assert_called_once()

    @patch("organvm_mcp.data.loader._read_json")
    @patch("organvm_mcp.data.loader.registry_path")
    def test_reload_clears_registry_cache(self, mock_path, mock_read):
        mock_read.return_value = {"organs": {}}
        first = loader_mod.load_registry()
        loader_mod.reload()
        mock_read.return_value = {"organs": {"NEW": {}}}
        second = loader_mod.load_registry()
        assert first is not second

    @patch("organvm_mcp.data.loader.governance_rules_path")
    def test_load_governance_rules_missing_file(self, mock_path):
        mock_path.return_value = Path("/nonexistent/governance-rules.json")
        result = loader_mod.load_governance_rules()
        assert result == {}

    @patch("organvm_mcp.data.loader.governance_rules_path")
    def test_load_governance_rules_caches(self, mock_path):
        mock_path.return_value = Path("/nonexistent/governance-rules.json")
        first = loader_mod.load_governance_rules()
        second = loader_mod.load_governance_rules()
        assert first is second

    @patch("organvm_mcp.data.loader.event_catalog_path")
    def test_load_event_catalog_missing_file(self, mock_path):
        mock_path.return_value = Path("/nonexistent/event-catalog.yaml")
        result = loader_mod.load_event_catalog()
        assert result == []

    @patch("organvm_mcp.data.loader.event_catalog_path")
    def test_load_event_catalog_with_data(self, mock_path, tmp_path):
        catalog_file = tmp_path / "event-catalog.yaml"
        catalog_file.write_text(yaml.dump({"events": [{"type": "test.event"}]}))
        mock_path.return_value = catalog_file
        result = loader_mod.load_event_catalog()
        assert len(result) == 1
        assert result[0]["type"] == "test.event"

    @patch("organvm_mcp.data.loader.event_catalog_path")
    def test_load_event_catalog_caches(self, mock_path, tmp_path):
        catalog_file = tmp_path / "event-catalog.yaml"
        catalog_file.write_text(yaml.dump({"events": [{"type": "a"}]}))
        mock_path.return_value = catalog_file
        first = loader_mod.load_event_catalog()
        second = loader_mod.load_event_catalog()
        assert first is second

    @patch("organvm_mcp.data.loader.event_catalog_path")
    def test_load_event_catalog_non_dict_returns_empty(self, mock_path, tmp_path):
        catalog_file = tmp_path / "event-catalog.yaml"
        catalog_file.write_text("- just a list\n- not a dict\n")
        mock_path.return_value = catalog_file
        result = loader_mod.load_event_catalog()
        assert result == []

    @patch("organvm_engine.contextmd.surfaces.collect_conversation_corpus_surfaces")
    def test_load_conversation_corpus_surfaces_caches(self, mock_collect):
        mock_collect.return_value = {"surface_count": 1, "surfaces": []}
        first = loader_mod.load_conversation_corpus_surfaces()
        second = loader_mod.load_conversation_corpus_surfaces()
        assert first is second
        mock_collect.assert_called_once()

    def test_reload_clears_all_caches(self):
        # Set caches to non-empty values directly
        loader_mod._registry_cache[("test", "test")] = {"data": True}
        loader_mod._seeds_cache[("test", "test")] = [{"data": True}]
        loader_mod._event_catalog_cache[("test", "test")] = [{"data": True}]
        loader_mod._governance_rules_cache[("test", "test")] = {"data": True}
        loader_mod._conversation_corpus_surfaces_cache[("test", "test")] = {"data": True}

        loader_mod.reload()

        assert loader_mod._registry_cache == {}
        assert loader_mod._seeds_cache == {}
        assert loader_mod._event_catalog_cache == {}
        assert loader_mod._governance_rules_cache == {}
        assert loader_mod._conversation_corpus_surfaces_cache == {}
