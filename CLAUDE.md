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
| `irf_*` | organvm_irf_query | INST-INDEX-RERUM-FACIENDARUM.md |

- **irf**: `organvm_irf_query` — query the Index Rerum Faciendarum by item_id, priority, domain, status

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

**Organ:** META-ORGANVM (Meta) | **Tier:** infrastructure | **Status:** GRADUATED
**Org:** `meta-organvm` | **Repo:** `organvm-mcp-server`

### Edges
- **Consumes** ← `meta-organvm/organvm-corpvs-testamentvm`: registry-v2.json
- **Consumes** ← `meta-organvm/organvm-engine`: seed discovery, governance rules, dependency graph
- **Consumes** ← `organvm-iv-taxis/orchestration-start-here`: event-catalog.yaml

### Siblings in Meta
`.github`, `organvm-corpvs-testamentvm`, `alchemia-ingestvm`, `schema-definitions`, `organvm-engine`, `system-dashboard`, `praxis-perpetua`, `stakeholder-portal`, `materia-collider`, `organvm-ontologia`, `vigiles-aeternae--agon-cosmogonicum`, `cvrsvs-honorvm`, `custodia-securitatis`

### Governance
- *Standard ORGANVM governance applies*

*Last synced: 2026-05-23T00:26:31Z*

## Active Handoff Protocol

If `.conductor/active-handoff.md` exists, **READ IT FIRST** before doing any work.
It contains constraints, locked files, conventions, and completed work from the
originating agent. You MUST honor all constraints listed there.

If the handoff says "CROSS-VERIFICATION REQUIRED", your self-assessment will
NOT be trusted. A different agent will verify your output against these constraints.

## Session Review Protocol

At the end of each session that produces or modifies files:
1. Run `organvm session review --latest` to get a session summary
2. Check for unimplemented plans: `organvm session plans --project .`
3. Export significant sessions: `organvm session export <id> --slug <slug>`
4. Run `organvm prompts distill --dry-run` to detect uncovered operational patterns

Transcripts are on-demand (never committed):
- `organvm session transcript <id>` — conversation summary
- `organvm session transcript <id> --unabridged` — full audit trail
- `organvm session prompts <id>` — human prompts only


## System Library

Plans: 269 indexed | Chains: 5 available | SOPs: 8 active
Discover: `organvm plans search <query>` | `organvm chains list` | `organvm sop lifecycle`
Library: `/Users/4jp/Code/organvm/praxis-perpetua/library`


## Active Directives

| Scope | Phase | Name | Description |
|-------|-------|------|-------------|
| system | any | atomic-clock | The Atomic Clock |
| system | any | execution-sequence | Execution Sequence |
| system | any | multi-agent-dispatch | Multi-Agent Dispatch |
| system | any | session-handoff-avalanche | Session Handoff Avalanche |
| system | any | system-loops | System Loops |
| system | any | prompting-standards | Prompting Standards |
| system | any | background-task-resilience | background-task-resilience |
| system | any | context-window-conservation | context-window-conservation |
| system | any | session-self-critique | session-self-critique |
| system | any | the-descent-protocol | the-descent-protocol |
| system | any | the-membrane-protocol | the-membrane-protocol |
| system | any | theory-to-concrete-gate | theory-to-concrete-gate |
| system | any | triangulation-protocol | triangulation-protocol |

Linked skills: SOP-TRIADIC-REVIEW-PROTOCOL, cicd-resilience-and-recovery, continuous-learning-agent, evaluation-to-growth, genesis-dna, multi-agent-workforce-planner, promotion-and-state-transitions, quality-gate-baseline-calibration, repo-onboarding-and-habitat-creation, session-self-critique, structural-integrity-audit, the-membrane-protocol, triple-reference


**Prompting (Anthropic)**: context 200K tokens, format: XML tags, thinking: extended thinking (budget_tokens)


## System Density (auto-generated)

AMMOI: 25% | Edges: 0 | Tensions: 0 | Clusters: 0 | Adv: 27 | Events(24h): 37975
Structure: 8 organs / 148 repos / 1654 components (depth 17) | Inference: 0% | Organs: META-ORGANVM:63%, ORGAN-I:53%, ORGAN-II:48%, ORGAN-III:54% +5 more
Last pulse: 2026-05-23T00:26:28 | Δ24h: n/a | Δ7d: n/a


## Dialect Identity (Trivium)

**Dialect:** SELF_WITNESSING | **Classical Parallel:** The Eighth Art | **Translation Role:** The Witness — proves all translations compose without loss

Strongest translations: I (formal), IV (structural), V (analogical)

Scan: `organvm trivium scan META <OTHER>` | Matrix: `organvm trivium matrix` | Synthesize: `organvm trivium synthesize`


## Logos Documentation Layer

**Status:** ACTIVE | **Symmetry:** 0.5 (DREAM)

Nature demands a documentation counterpart. This formation maintains its narrative record in `docs/logos/`.

### The Tetradic Counterpart
- **[Telos (Idealized Form)](../docs/logos/telos.md)** — The dream and theoretical grounding.
- **[Pragma (Concrete State)](../docs/logos/pragma.md)** — The honest account of what exists.
- **[Praxis (Remediation Plan)](../docs/logos/praxis.md)** — The attack vectors for evolution.
- **[Receptio (Reception)](../docs/logos/receptio.md)** — The account of the constructed polis.

### Alchemical I/O
- **[Source & Transmutation](../docs/logos/alchemical-io.md)** — Narrative of inputs, process, and returns.



*Compliance: Record exists without implementation.*

<!-- ORGANVM:AUTO:END -->





## ⚡ Conductor OS Integration
This repository is a managed component of the ORGANVM meta-workspace.
- **Orchestration:** Use `conductor patch` for system status and work queue.
- **Lifecycle:** Follow the `FRAME -> SHAPE -> BUILD -> PROVE` workflow.
- **Governance:** Promotions are managed via `conductor wip promote`.
- **Intelligence:** Conductor MCP tools are available for routing and mission synthesis.