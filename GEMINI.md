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


## ⚡ Conductor OS Integration
This repository is a managed component of the ORGANVM meta-workspace.
- **Orchestration:** Use `conductor patch` for system status and work queue.
- **Lifecycle:** Follow the `FRAME -> SHAPE -> BUILD -> PROVE` workflow.
- **Governance:** Promotions are managed via `conductor wip promote`.
- **Intelligence:** Conductor MCP tools are available for routing and mission synthesis.
