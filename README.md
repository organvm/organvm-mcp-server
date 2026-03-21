# ORGANVM MCP Server

Exposes the full ORGANVM system context to any Claude Code session.

## Overview

The `organvm-mcp-server` is a local infrastructure component that allows AI assistants working in *any* repository (within or outside the 8-organ system) to query live metadata about the entire ecosystem.

It provides a unified view of:
- **Registry**: Repository metadata, status, and tiers.
- **Seeds**: Automation contracts, produces/consumes edges.
- **Graph**: Dependency relationships and inter-organ flow.
- **Health**: System-wide health metrics and Omega status.
- **Context**: Tailored awareness for the current working directory.
- **Conversation Corpus Surfaces**: Governed CCE exports with validation state and provider readiness.

## Tools Provided

- `organvm_query_registry`: Search and filter repos in the system.
- `organvm_get_repo`: Get full details for a specific repository.
- `organvm_list_organs`: Get summary stats for all 8 organs.
- `organvm_get_seed`: Read the automation contract for a repo.
- `organvm_find_edges`: Discover produces/consumes relationships.
- `organvm_get_event_contract`: Look up event schemas from the catalog.
- `organvm_trace_dependencies`: Traverse the dependency graph.
- `organvm_check_dependency`: Validate if a relationship is allowed by governance.
- `organvm_system_health`: Get a high-level health report.
- `organvm_omega_status`: Track transition criteria progress.
- `organvm_get_context`: **Primary Tool** — Get everything relevant to your current repo.
- `organvm_conversation_corpus_surfaces`: Inspect exported conversation-memory surfaces and their validation state.

## Installation

```bash
cd /Users/4jp/Workspace/meta-organvm/organvm-mcp-server
pip install -e .
```

## Configuration

Add to your `~/.claude/mcp.json` (or equivalent AI editor config):

```json
{
  "mcpServers": {
    "organvm": {
      "command": "organvm-mcp",
      "args": []
    }
  }
}
```

## Development

- **Run tests (stubs)**: `pytest tests/`
- **MCP Inspector**: `mcp dev src/organvm_mcp/server.py`
