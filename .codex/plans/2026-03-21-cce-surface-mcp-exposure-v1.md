# CCE Surface MCP Exposure V1

Date: 2026-03-21
Project: meta-organvm/organvm-mcp-server

## Goal

Expose Conversation Corpus Engine surfaces through MCP so sessions can query governed conversation-memory state through Meta rather than reading repo-local files directly.

## Scope

1. Extend the loader layer with CCE surface accessors.
2. Add path helpers for resolving exported surface files in the workspace.
3. Fold the new surface data into `get_context`.
4. Add a dedicated tool for querying conversation corpus surfaces.
5. Register the new tool and add regression coverage for dispatch and responses.

## Constraints

- Keep tool payloads read-only and schema-backed.
- Follow the existing loader-cache pattern so MCP remains fast.
- Avoid duplicating engine discovery logic inside the tool layer.

## Verification

- Run targeted MCP tests for loader, tool output, and server registration.
- Confirm dispatch coverage and tool count stay correct after registration.
