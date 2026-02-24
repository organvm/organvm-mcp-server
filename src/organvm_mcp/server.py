"""ORGANVM MCP Server — entry point.

Registers all tools with the MCP SDK and runs the stdio transport.
Each tool group (registry, seeds, graph, health, context) is imported
and registered with descriptive schemas so Claude Code can discover
and invoke them.

Usage:
    organvm-mcp          # runs stdio server
    mcp dev server.py    # runs with MCP inspector
"""

from __future__ import annotations

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from organvm_mcp.tools import registry, seeds, graph, health, context

server = Server("organvm")

# ── Tool definitions ──────────────────────────────────────────────

TOOLS = [
    # Registry tools
    Tool(
        name="organvm_query_registry",
        description=(
            "Search and filter repos in the ORGANVM registry. "
            "Filter by organ, tier, promotion status, or name pattern. "
            "Returns matching repos with metadata."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "organ": {
                    "type": "string",
                    "description": "Filter by organ key (ORGAN-I through ORGAN-VII, META, PERSONAL)",
                },
                "tier": {
                    "type": "string",
                    "enum": ["flagship", "standard", "infrastructure", "archive"],
                    "description": "Filter by repo tier",
                },
                "promotion_status": {
                    "type": "string",
                    "enum": ["LOCAL", "CANDIDATE", "PUBLIC_PROCESS", "GRADUATED", "ARCHIVED"],
                    "description": "Filter by promotion pipeline status",
                },
                "name_pattern": {
                    "type": "string",
                    "description": "Substring match on repo name (case-insensitive)",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results (default 50)",
                    "default": 50,
                },
            },
        },
    ),
    Tool(
        name="organvm_get_repo",
        description=(
            "Get full details for a specific ORGANVM repository "
            "including metadata, dependencies, launch metrics, and current status."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "org": {"type": "string", "description": "GitHub organization"},
                "name": {"type": "string", "description": "Repository name"},
            },
            "required": ["org", "name"],
        },
    ),
    Tool(
        name="organvm_list_organs",
        description="List all 8 ORGANVM organs with summary statistics (repo count, tiers, edges).",
        inputSchema={"type": "object", "properties": {}},
    ),
    # Seed tools
    Tool(
        name="organvm_get_seed",
        description="Get the parsed seed.yaml automation contract for a specific repository.",
        inputSchema={
            "type": "object",
            "properties": {
                "org": {"type": "string", "description": "GitHub organization"},
                "name": {"type": "string", "description": "Repository name"},
            },
            "required": ["org", "name"],
        },
    ),
    Tool(
        name="organvm_find_edges",
        description=(
            "Find produces/consumes edges for a repo or organ. "
            "Shows what data flows in and out — events, artifacts, dependencies."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "repo": {"type": "string", "description": "Repository name (optional)"},
                "organ": {"type": "string", "description": "Organ key (optional)"},
                "direction": {
                    "type": "string",
                    "enum": ["produces", "consumes", "both"],
                    "default": "both",
                },
            },
        },
    ),
    Tool(
        name="organvm_get_event_contract",
        description=(
            "Get the event catalog entry for a dispatch event type "
            "(e.g., essay.published, community.milestone, theory.candidate)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "event_type": {"type": "string", "description": "Event type string"},
            },
            "required": ["event_type"],
        },
    ),
    Tool(
        name="organvm_list_events",
        description="List all event types in the ORGANVM event catalog with producers and consumers.",
        inputSchema={"type": "object", "properties": {}},
    ),
    # Graph tools
    Tool(
        name="organvm_trace_dependencies",
        description=(
            "Trace the dependency graph from a repo or organ. "
            "Shows upstream (what I depend on) and downstream (what depends on me)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "repo": {"type": "string", "description": "Repository name"},
                "organ": {"type": "string", "description": "Organ key"},
                "direction": {
                    "type": "string",
                    "enum": ["upstream", "downstream", "both"],
                    "default": "both",
                },
                "depth": {"type": "integer", "default": 2},
            },
        },
    ),
    Tool(
        name="organvm_check_dependency",
        description=(
            "Check if a dependency between two organs is allowed by governance rules. "
            "ORGANVM enforces unidirectional flow: I→II→III, no back-edges."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "source_organ": {"type": "string", "description": "Organ that would depend"},
                "target_organ": {"type": "string", "description": "Organ being depended on"},
            },
            "required": ["source_organ", "target_organ"],
        },
    ),
    Tool(
        name="organvm_get_dependency_graph",
        description=(
            "Get the full dependency graph or a subgraph for one organ. "
            "Returns nodes and edges suitable for visualization."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "organ": {"type": "string", "description": "Optional organ filter"},
            },
        },
    ),
    # Health tools
    Tool(
        name="organvm_system_health",
        description=(
            "Get system-wide health summary: repo counts, CI coverage, "
            "test coverage, seed coverage, promotion pipeline, revenue status."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="organvm_omega_status",
        description=(
            "Get omega criteria progress — 17 criteria across 5 horizons "
            "tracking the system's transition from construction to occupation. "
            "Returns real evaluated data from soak tests and registry."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="organvm_ci_health",
        description=(
            "Get CI health summary from latest soak test data. "
            "Shows pass/fail counts, failures categorized by organ, "
            "and identifies phantom failures from schedule-only workflows."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="organvm_upcoming_deadlines",
        description=(
            "Get upcoming deadlines from the rolling-todo — funding applications, "
            "submissions, and time-sensitive tasks sorted by date with urgency levels."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Number of days to look ahead (default 30)",
                    "default": 30,
                },
            },
        },
    ),
    Tool(
        name="organvm_pitch_status",
        description=(
            "Get pitch deck coverage across the system — how many repos "
            "have pitch decks (bespoke vs generated), broken down by organ."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    # Context tools
    Tool(
        name="organvm_get_context",
        description=(
            "Get full contextual awareness for a repo. Returns organ info, "
            "produces/consumes edges, siblings, governance constraints, and "
            "superproject status. THE primary tool for cross-repo awareness."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "repo": {"type": "string", "description": "Repository name"},
                "org": {"type": "string", "description": "GitHub organization"},
                "cwd": {
                    "type": "string",
                    "description": "Working directory (auto-resolves repo and org)",
                },
            },
        },
    ),
]


# ── Tool dispatch ─────────────────────────────────────────────────

_DISPATCH = {
    "organvm_query_registry": lambda args: registry.query_registry(**args),
    "organvm_get_repo": lambda args: registry.get_repo(**args),
    "organvm_list_organs": lambda args: registry.list_organs(),
    "organvm_get_seed": lambda args: seeds.get_seed(**args),
    "organvm_find_edges": lambda args: seeds.find_edges(**args),
    "organvm_get_event_contract": lambda args: seeds.get_event_contract(**args),
    "organvm_list_events": lambda args: seeds.list_events(),
    "organvm_trace_dependencies": lambda args: graph.trace_dependencies(**args),
    "organvm_check_dependency": lambda args: graph.check_dependency(**args),
    "organvm_get_dependency_graph": lambda args: graph.get_dependency_graph(**args),
    "organvm_system_health": lambda args: health.system_health(),
    "organvm_omega_status": lambda args: health.omega_status(),
    "organvm_ci_health": lambda args: health.ci_health(),
    "organvm_upcoming_deadlines": lambda args: health.deadlines(**args),
    "organvm_pitch_status": lambda args: health.pitch_status(),
    "organvm_get_context": lambda args: context.get_context(**args),
}


@server.list_tools()
async def list_tools() -> list[Tool]:
    """Return all registered tools."""
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Dispatch a tool call to the appropriate handler."""
    import json

    handler = _DISPATCH.get(name)
    if not handler:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    try:
        result = handler(arguments or {})
        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
    except NotImplementedError as e:
        return [TextContent(type="text", text=f"[STUB] {e}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {type(e).__name__}: {e}")]


# ── Entry point ───────────────────────────────────────────────────

def main() -> None:
    """Run the MCP server on stdio."""
    import asyncio
    asyncio.run(_run())


async def _run() -> None:
    """Async entry point."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    main()
