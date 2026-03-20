"""Tests for MCP server dispatch and tool registration."""

import asyncio

from organvm_mcp.server import _DISPATCH, TOOLS, call_tool


class TestServerRegistration:
    def test_tools_count(self):
        assert len(TOOLS) == 126

    def test_dispatch_covers_all_tools(self):
        tool_names = {t.name for t in TOOLS}
        dispatch_names = set(_DISPATCH.keys())
        assert tool_names == dispatch_names

    def test_tool_names_prefixed(self):
        for tool in TOOLS:
            assert tool.name.startswith("organvm_"), f"{tool.name} missing prefix"

    def test_call_tool_unknown(self):
        result = asyncio.run(call_tool("nonexistent_tool", {}))
        assert len(result) == 1
        assert "Unknown tool" in result[0].text
