"""Tests for trivium MCP tools."""

from organvm_mcp.tools.trivium import (
    trivium_dialects,
    trivium_matrix,
    trivium_scan,
    trivium_status,
)


def test_trivium_dialects():
    result = trivium_dialects()
    assert result["count"] == 8
    assert len(result["dialects"]) == 8
    for d in result["dialects"]:
        assert "dialect" in d
        assert "organ_key" in d
        assert "classical_parallel" in d


def test_trivium_matrix():
    result = trivium_matrix()
    assert result["count"] == 28
    assert len(result["pairs"]) == 28


def test_trivium_matrix_filter():
    result = trivium_matrix(organ="I")
    assert result["filter"] == "I"
    assert result["count"] == 7  # I connects to 7 others


def test_trivium_scan():
    result = trivium_scan("I", "III")
    assert result["organ_a"] == "I"
    assert result["organ_b"] == "III"
    assert "correspondences" in result


def test_trivium_status():
    result = trivium_status()
    assert result["dialects"] == 8
    assert result["translation_pairs"] == 28
    assert "tier_counts" in result
    assert result["spec"] == "SPEC-018"
