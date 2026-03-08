"""Tests for distill / pattern tools."""

from __future__ import annotations

from unittest.mock import patch

from organvm_mcp.tools import distill


class TestDistillPatterns:
    def test_returns_patterns(self):
        res = distill.distill_patterns()
        assert "patterns" in res
        assert res["total"] >= 1
        assert "id" in res["patterns"][0]
        assert "label" in res["patterns"][0]
        assert "description" in res["patterns"][0]

    def test_all_patterns_have_tier(self):
        res = distill.distill_patterns()
        for p in res["patterns"]:
            assert "tier" in p


class TestDistillCoverage:
    @patch("organvm_engine.sop.discover.discover_sops")
    def test_coverage_structure(self, mock_discover):
        mock_discover.return_value = []
        res = distill.distill_coverage()
        assert "entries" in res
        assert "summary" in res
        assert res["summary"]["total_patterns"] >= 1

    @patch("organvm_engine.sop.discover.discover_sops")
    def test_coverage_entries(self, mock_discover):
        mock_discover.return_value = []
        res = distill.distill_coverage()
        for entry in res["entries"]:
            assert "pattern_id" in entry
            assert "status" in entry
            assert entry["status"] in ("covered", "partial", "uncovered")


class TestDistillScaffold:
    def test_scaffold_valid_pattern(self):
        from organvm_engine.distill.taxonomy import all_pattern_ids

        pid = all_pattern_ids()[0]
        res = distill.distill_scaffold(pid)
        assert "scaffold" in res
        assert res["pattern_id"] == pid
        assert "pattern_label" in res
        assert isinstance(res["scaffold"], str)
        assert len(res["scaffold"]) > 0

    def test_scaffold_invalid_pattern(self):
        res = distill.distill_scaffold("nonexistent-pattern")
        assert "error" in res
