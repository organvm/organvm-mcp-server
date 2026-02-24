# CLAUDE.md — organvm-mcp-server

**ORGAN Meta** (Meta) · `meta-organvm/organvm-mcp-server`
**Status:** ACTIVE · **Branch:** `main`

## What This Repo Is

MCP (Model Context Protocol) server that exposes the full ORGANVM system graph to any Claude Code session. When configured as a local MCP server, it lets an AI assistant in *any* repo — from ORGAN-I theory engines to personal portfolio sites — query the registry, dependency graph, seed contracts, event catalog, and system health in real time.

## Stack

**Language:** Python 3.11+
**Protocol:** MCP (stdio transport)
**Dependencies:** `mcp` SDK, `organvm-engine`, `pyyaml`

## Architecture

```
Claude Code session (any repo)
  ↓ stdio
organvm-mcp-server
  ↓ imports
organvm-engine (registry, seeds, governance, dispatch)
  ↓ reads
registry-v2.json, seed.yaml files, event-catalog.yaml, governance-rules.json
```

### Tool Groups

| Group | Tools | Data Source |
|-------|-------|-------------|
| `registry_*` | query_registry, get_repo, list_organs | registry-v2.json |
| `seed_*` | get_seed, find_edges, get_event_contract | seed.yaml files, event-catalog.yaml |
| `graph_*` | trace_dependencies, check_dependency, get_dependency_graph | governance-rules.json, registry |
| `health_*` | system_health, omega_status | registry + dashboard data |
| `context_*` | get_context | all sources, contextual to caller's repo |

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v
ruff check src/
```

## Running

```bash
# Direct stdio (for MCP client configuration)
organvm-mcp

# Test with MCP inspector
mcp dev src/organvm_mcp/server.py
```

## Claude Code Configuration

Add to `~/.claude/mcp.json`:
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

## ORGANVM Context

Part of **ORGAN Meta (Meta)** under the `meta-organvm` GitHub organization.
Sibling packages: organvm-engine, schema-definitions, system-dashboard, alchemia-ingestvm.

<!-- ORGANVM:AUTO:START -->
## System Context (auto-generated — do not edit)

**Organ:** META-ORGANVM (Meta) | **Tier:** infrastructure | **Status:** LOCAL
**Org:** `unknown` | **Repo:** `organvm-mcp-server`

### Edges
- **Consumes** ← `meta-organvm/organvm-corpvs-testamentvm`: registry-v2.json
- **Consumes** ← `meta-organvm/organvm-engine`: seed discovery, governance rules, dependency graph
- **Consumes** ← `organvm-iv-taxis/orchestration-start-here`: event-catalog.yaml

### Siblings in Meta
`.github`, `organvm-corpvs-testamentvm`, `alchemia-ingestvm`, `schema-definitions`, `organvm-engine`, `system-dashboard`

### Governance
- *Standard ORGANVM governance applies*

*Last synced: 2026-02-24T12:41:28Z*
<!-- ORGANVM:AUTO:END -->
