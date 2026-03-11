"""Tests for the infrastructure audit MCP tool."""

from unittest.mock import patch


def test_infrastructure_audit_returns_dict():
    """Smoke test: infrastructure_audit returns a dict with expected keys."""
    from organvm_mcp.tools.audit import infrastructure_audit

    minimal_registry = {
        "organs": {
            "ORGAN-I": {
                "name": "Test",
                "repositories": [],
            }
        }
    }

    with (
        patch("organvm_mcp.tools.audit._workspace_root") as mock_ws,
        patch("organvm_mcp.data.loader.load_registry", return_value=minimal_registry),
    ):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            mock_ws.return_value = Path(tmpdir)
            result = infrastructure_audit()

    assert isinstance(result, dict)
    assert "summary" in result
    assert "layers" in result


def test_infrastructure_audit_with_layer_filter():
    """Test that layer filter restricts to one layer."""
    from organvm_mcp.tools.audit import infrastructure_audit

    minimal_registry = {
        "organs": {
            "ORGAN-I": {
                "name": "Test",
                "repositories": [],
            }
        }
    }

    with (
        patch("organvm_mcp.tools.audit._workspace_root") as mock_ws,
        patch("organvm_mcp.data.loader.load_registry", return_value=minimal_registry),
    ):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            mock_ws.return_value = Path(tmpdir)
            result = infrastructure_audit(layer="filesystem")

    assert "filesystem" in result["layers"]
    # Should not have other layers
    assert len(result["layers"]) == 1
