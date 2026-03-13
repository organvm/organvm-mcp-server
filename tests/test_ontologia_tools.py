"""Tests for ontologia MCP tools.

Tests entity resolution, listing, history, events, status, and
bridge resolution tools with isolated ontologia stores.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from ontologia.entity.identity import EntityType
from ontologia.events import bus as ontologia_bus
from ontologia.registry.store import RegistryStore

from organvm_mcp.tools import ontologia


@pytest.fixture(autouse=True)
def _isolate_ontologia(tmp_path, monkeypatch):
    """Redirect ontologia store and events to tmp_path."""
    store_dir = tmp_path / "ontologia"
    store_dir.mkdir()
    ontologia_bus.set_events_path(store_dir / "events.jsonl")
    ontologia_bus.clear_subscribers()
    monkeypatch.setattr(
        "ontologia.registry.store._default_store_dir",
        lambda: store_dir,
    )
    yield
    ontologia_bus.set_events_path(None)
    ontologia_bus.clear_subscribers()


@pytest.fixture
def populated_store(tmp_path) -> RegistryStore:
    """Create a store with test entities."""
    store_dir = tmp_path / "ontologia"
    store_dir.mkdir(exist_ok=True)
    ontologia_bus.set_events_path(store_dir / "events.jsonl")

    store = RegistryStore(store_dir=store_dir)
    store.load()
    store.create_entity(EntityType.ORGAN, "ORGAN-I", created_by="test")
    store.create_entity(EntityType.REPO, "organvm-engine", created_by="test")
    store.create_entity(EntityType.REPO, "test-repo", created_by="test")
    store.save()
    return store


class TestOntologiaResolve:
    def test_resolve_found(self, populated_store):
        with patch("ontologia.registry.store.open_store", return_value=populated_store):
            result = ontologia.ontologia_resolve(query="organvm-engine")

        assert "error" not in result
        assert result["uid"].startswith("ent_repo_")
        assert result["display_name"] == "organvm-engine"
        assert result["entity_type"] == "repo"

    def test_resolve_not_found(self):
        result = ontologia.ontologia_resolve(query="nonexistent")
        assert "error" in result
        assert "No entity found" in result["error"]

    def test_resolve_unavailable(self):
        with patch.dict("sys.modules", {"ontologia.registry.store": None}):
            result = ontologia._check_available()
        assert result is not None
        assert "not installed" in result["error"]


class TestOntologiaList:
    def test_list_all(self, populated_store):
        with patch("ontologia.registry.store.open_store", return_value=populated_store):
            result = ontologia.ontologia_list()

        assert "error" not in result
        assert result["total"] == 3
        assert len(result["entities"]) == 3

    def test_list_by_type(self, populated_store):
        with patch("ontologia.registry.store.open_store", return_value=populated_store):
            result = ontologia.ontologia_list(entity_type="repo")

        assert result["total"] == 2
        for e in result["entities"]:
            assert e["entity_type"] == "repo"

    def test_list_invalid_type(self, populated_store):
        with patch("ontologia.registry.store.open_store", return_value=populated_store):
            result = ontologia.ontologia_list(entity_type="invalid")
        assert "error" in result

    def test_list_with_limit(self, populated_store):
        with patch("ontologia.registry.store.open_store", return_value=populated_store):
            result = ontologia.ontologia_list(limit=1)
        assert len(result["entities"]) == 1
        assert result["total"] == 3


class TestOntologiaHistory:
    def test_history_found(self, populated_store):
        with patch("ontologia.registry.store.open_store", return_value=populated_store):
            result = ontologia.ontologia_history(entity="organvm-engine")

        assert "error" not in result
        assert result["uid"].startswith("ent_repo_")
        assert len(result["names"]) >= 1
        assert result["names"][0]["display_name"] == "organvm-engine"

    def test_history_not_found(self):
        result = ontologia.ontologia_history(entity="nonexistent")
        assert "error" in result


class TestOntologiaEvents:
    def test_events_returns_list(self, populated_store):
        with patch("ontologia.registry.store.open_store", return_value=populated_store):
            result = ontologia.ontologia_events()

        assert "error" not in result
        assert isinstance(result["events"], list)
        assert result["total"] >= 0


class TestOntologiaStatus:
    def test_status(self, populated_store):
        with patch("ontologia.registry.store.open_store", return_value=populated_store):
            result = ontologia.ontologia_status()

        assert "error" not in result
        assert result["entity_count"] == 3
        assert result["by_type"]["repo"] == 2
        assert result["by_type"]["organ"] == 1


class TestBridgeResolve:
    def test_bridge_via_ontologia(self, populated_store):
        mini_registry = {
            "organs": {
                "META-ORGANVM": {
                    "repositories": [
                        {"name": "organvm-engine", "tier": "flagship"},
                    ],
                },
            },
        }
        with (
            patch("ontologia.registry.store.open_store", return_value=populated_store),
            patch("organvm_mcp.data.loader.load_registry", return_value=mini_registry),
        ):
            result = ontologia.ontologia_bridge_resolve(query="organvm-engine")

        assert "error" not in result
        assert result["source"] == "ontologia"
        assert result["uid"] is not None

    def test_bridge_fallback_to_registry(self):
        mini_registry = {
            "organs": {
                "META-ORGANVM": {
                    "repositories": [
                        {"name": "organvm-engine", "tier": "flagship"},
                    ],
                },
            },
        }
        with (
            patch.dict("sys.modules", {"ontologia.registry.store": None}),
            patch("organvm_mcp.data.loader.load_registry", return_value=mini_registry),
        ):
            result = ontologia.ontologia_bridge_resolve(query="organvm-engine")

        assert "error" not in result
        assert result["source"] == "registry"

    def test_bridge_not_found(self):
        mini_registry = {"organs": {}}
        with (
            patch.dict("sys.modules", {"ontologia.registry.store": None}),
            patch("organvm_mcp.data.loader.load_registry", return_value=mini_registry),
        ):
            result = ontologia.ontologia_bridge_resolve(query="nonexistent")

        assert "error" in result
