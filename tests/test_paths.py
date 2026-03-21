"""Tests for data/paths.py — workspace path resolution."""

from pathlib import Path

from organvm_mcp.data.paths import (
    conversation_corpus_surface_bundle_path,
    conversation_corpus_surface_dir,
    corpus_dir,
    event_catalog_path,
    governance_rules_path,
    registry_path,
    repo_root_path,
    workspace_root,
)


def test_workspace_root_env(monkeypatch):
    monkeypatch.setenv("ORGANVM_WORKSPACE_DIR", "/custom/workspace")
    assert workspace_root() == Path("/custom/workspace")


def test_workspace_root_default(monkeypatch):
    monkeypatch.delenv("ORGANVM_WORKSPACE_DIR", raising=False)
    result = workspace_root()
    assert result == Path.home() / "Workspace"


def test_corpus_dir_env(monkeypatch):
    monkeypatch.setenv("ORGANVM_CORPUS_DIR", "/custom/corpus")
    assert corpus_dir() == Path("/custom/corpus")


def test_registry_path_suffix():
    result = registry_path()
    assert str(result).endswith("registry-v2.json")


def test_governance_rules_path_suffix():
    result = governance_rules_path()
    assert str(result).endswith("governance-rules.json")


def test_event_catalog_path_suffix():
    result = event_catalog_path()
    assert str(result).endswith("event-catalog.yaml")


def test_engine_dir_suffix():
    from organvm_mcp.data.paths import engine_dir

    result = engine_dir()
    assert str(result).endswith("meta-organvm/organvm-engine")


def test_repo_root_path():
    result = repo_root_path("organvm-i-theoria", "conversation-corpus-engine")
    assert str(result).endswith("organvm-i-theoria/conversation-corpus-engine")


def test_conversation_corpus_surface_dir():
    result = conversation_corpus_surface_dir("organvm-i-theoria", "conversation-corpus-engine")
    assert str(result).endswith("reports/surfaces")


def test_conversation_corpus_surface_bundle_path():
    result = conversation_corpus_surface_bundle_path(
        "organvm-i-theoria",
        "conversation-corpus-engine",
    )
    assert str(result).endswith("reports/surfaces/surface-bundle.json")
