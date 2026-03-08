"""Tests for SOP tools."""

from __future__ import annotations

from unittest.mock import patch

from organvm_mcp.tools import sops


class TestSopDiscover:
    @patch("organvm_engine.sop.discover.discover_sops")
    def test_returns_structure(self, mock_discover):
        from pathlib import Path

        from organvm_engine.sop.discover import SOPEntry

        mock_discover.return_value = [
            SOPEntry(
                path=Path("/tmp/SOP--test.md"),
                org="meta-organvm",
                repo="praxis-perpetua",
                filename="SOP--test.md",
                title="Test SOP",
                doc_type="SOP",
                canonical=True,
                has_canonical_header=False,
                scope="system",
                phase="any",
            ),
        ]
        res = sops.sop_discover()
        assert res["total"] == 1
        assert res["sops"][0]["filename"] == "SOP--test.md"
        assert "by_type" in res
        assert "by_scope" in res

    @patch("organvm_engine.sop.discover.discover_sops")
    def test_empty(self, mock_discover):
        mock_discover.return_value = []
        res = sops.sop_discover()
        assert res["total"] == 0

    @patch("organvm_engine.sop.discover.discover_sops")
    def test_organ_filter_passed(self, mock_discover):
        mock_discover.return_value = []
        sops.sop_discover(organ="META")
        mock_discover.assert_called_once_with(organ="META")


class TestSopAudit:
    @patch("organvm_engine.sop.inventory.audit_sops")
    @patch("organvm_engine.sop.discover.discover_sops")
    def test_returns_structure(self, mock_discover, mock_audit):
        from organvm_engine.sop.inventory import AuditResult

        mock_discover.return_value = []
        mock_audit.return_value = AuditResult(
            tracked=[],
            untracked=[],
            reference_copy=[],
            missing=["SOP--missing.md"],
        )
        res = sops.sop_audit()
        assert res["missing_count"] == 1
        assert "SOP--missing.md" in res["missing"]


class TestSopResolve:
    @patch("organvm_engine.sop.resolver.resolve_all")
    @patch("organvm_engine.sop.discover.discover_sops")
    def test_returns_structure(self, mock_discover, mock_resolve):
        mock_discover.return_value = []
        mock_resolve.return_value = []
        res = sops.sop_resolve(repo="my-repo", organ="III")
        assert res["total"] == 0
        assert res["context"]["repo"] == "my-repo"
        assert res["context"]["organ"] == "III"
