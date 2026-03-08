"""Tests for prompting standards tools."""

from __future__ import annotations

from unittest.mock import patch

from organvm_mcp.tools import prompting


class TestPromptingGuidelines:
    @patch("organvm_engine.prompting.loader.load_guidelines")
    def test_returns_guidelines(self, mock_load):
        from organvm_engine.prompting.standards import ProviderGuidelines

        mock_load.return_value = ProviderGuidelines(
            provider="anthropic",
            system_prompt_support=True,
            max_context="200K tokens",
            thinking_mode="extended thinking",
            preferred_format="XML tags",
        )
        res = prompting.prompting_guidelines(agent="claude")
        assert res["provider"] == "anthropic"
        assert res["system_prompt_support"] is True

    @patch("organvm_engine.prompting.loader.load_guidelines")
    def test_unknown_agent(self, mock_load):
        mock_load.return_value = None
        res = prompting.prompting_guidelines(agent="unknown")
        assert "error" in res

    @patch("organvm_engine.prompting.loader.load_guidelines")
    def test_default_agent(self, mock_load):
        from organvm_engine.prompting.standards import ProviderGuidelines

        mock_load.return_value = ProviderGuidelines(
            provider="anthropic",
            system_prompt_support=True,
            max_context="200K tokens",
            thinking_mode=None,
            preferred_format="XML",
        )
        res = prompting.prompting_guidelines()
        assert res["provider"] == "anthropic"
        mock_load.assert_called_once_with("claude")


class TestPromptingAll:
    def test_returns_all_providers(self):
        res = prompting.prompting_all()
        assert "providers" in res
        assert "total" in res
        assert res["total"] >= 1
        assert "anthropic" in res["providers"]
