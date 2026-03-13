"""ORGANVM MCP Server — entry point.

Registers all tools with the MCP SDK and runs the stdio transport.
Each tool group is imported and registered with descriptive schemas
so Claude Code can discover and invoke them.

Usage:
    organvm-mcp          # runs stdio server
    mcp dev server.py    # runs with MCP inspector
"""

from __future__ import annotations

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from organvm_mcp.tools import (
    atoms,
    audit,
    context,
    coordination,
    distill,
    ecosystem,
    governance,
    graph,
    health,
    metrics,
    prompting,
    pulse,
    registry,
    revenue,
    seeds,
    sessions,
    sops,
    styx,
    verification,
)

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
                    "description": (
                        "Filter by organ key (ORGAN-I through ORGAN-VII, META, PERSONAL)"
                    ),
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
        description=(
            "List all 8 ORGANVM organs with summary statistics (repo count, tiers, edges)."
        ),
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
        description=(
            "List all event types in the ORGANVM event catalog with producers and consumers."
        ),
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
    # Organism tools
    Tool(
        name="organvm_organism",
        description=(
            "Get the unified system organism — hierarchical snapshot of all repos, "
            "organs, gates, and promotion status. Optionally zoom to a specific "
            "organ or repo. Returns gate pass rates, promo readiness, and blockers."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "organ": {
                    "type": "string",
                    "description": "Zoom to specific organ (e.g. ORGAN-I, META-ORGANVM)",
                },
                "repo": {
                    "type": "string",
                    "description": "Zoom to specific repo name",
                },
                "view": {
                    "type": "string",
                    "enum": ["full", "gates", "blockers"],
                    "description": "View projection (default: full)",
                    "default": "full",
                },
            },
        },
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
    # ── Revenue tools ────────────────────────────────────────────────
    Tool(
        name="organvm_revenue_pipeline",
        description=(
            "Full 6-layer revenue pipeline status: products, grants, consulting. "
            "Aggregates ORGAN-III products, funding deadlines, and consulting packages."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="organvm_revenue_products",
        description=("ORGAN-III products with revenue model, status, and deployment readiness."),
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="organvm_revenue_readiness",
        description=(
            "Per-product deployment readiness assessment with blockers, "
            "promotion eligibility, and downstream impact analysis."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "repo_name": {
                    "type": "string",
                    "description": "Repository name to assess",
                },
            },
            "required": ["repo_name"],
        },
    ),
    Tool(
        name="organvm_revenue_grants",
        description=(
            "Grant and funding deadline view — upcoming opportunities "
            "filtered from the rolling-todo with urgency levels."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Days to look ahead (default 90)",
                    "default": 90,
                },
            },
        },
    ),
    Tool(
        name="organvm_revenue_consulting",
        description=(
            "7 consulting service packages with SOP existence verification. "
            "Shows readiness based on whether backing SOPs exist."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    # ── Governance tools ─────────────────────────────────────────────
    Tool(
        name="organvm_governance_audit",
        description=(
            "Full system governance audit — checks promotion rules, "
            "dependency constraints, tier requirements, and organ policies."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="organvm_governance_check_transition",
        description=(
            "Validate whether a promotion state transition is allowed. "
            "E.g., can a repo move from CANDIDATE to PUBLIC_PROCESS?"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "current_state": {
                    "type": "string",
                    "enum": ["LOCAL", "CANDIDATE", "PUBLIC_PROCESS", "GRADUATED", "ARCHIVED"],
                    "description": "Current promotion state",
                },
                "target_state": {
                    "type": "string",
                    "enum": ["LOCAL", "CANDIDATE", "PUBLIC_PROCESS", "GRADUATED", "ARCHIVED"],
                    "description": "Target promotion state",
                },
            },
            "required": ["current_state", "target_state"],
        },
    ),
    Tool(
        name="organvm_governance_valid_transitions",
        description="List all valid promotion transitions from a given state.",
        inputSchema={
            "type": "object",
            "properties": {
                "current_state": {
                    "type": "string",
                    "enum": ["LOCAL", "CANDIDATE", "PUBLIC_PROCESS", "GRADUATED", "ARCHIVED"],
                    "description": "Current promotion state",
                },
            },
            "required": ["current_state"],
        },
    ),
    Tool(
        name="organvm_governance_validate_deps",
        description=(
            "Full dependency graph validation — checks for missing targets, "
            "self-dependencies, back-edges, and cycles."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="organvm_governance_impact",
        description=(
            "Blast radius calculation — what repos are affected "
            "if a given repo changes? Shows propagation path."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "repo_name": {
                    "type": "string",
                    "description": "Repository name to analyze impact for",
                },
            },
            "required": ["repo_name"],
        },
    ),
    Tool(
        name="organvm_governance_feedback_loops",
        description=(
            "Feedback loop inventory — positive and negative loops "
            "with active detection from registry and seed evidence."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="organvm_governance_dictums",
        description=(
            "List constitutional dictums — axioms, organ dictums, "
            "and repo rules from the Ontological Constitution. "
            "Filter by level (axiom/organ/repo)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "level": {
                    "type": "string",
                    "enum": ["axiom", "organ", "repo"],
                    "description": "Filter by dictum tier (optional)",
                },
            },
        },
    ),
    Tool(
        name="organvm_governance_check_dictums",
        description=(
            "Run dictum compliance checks — validates all enforceable "
            "dictums (AX-1 DAG, AX-3 TTL, OD-III factory gate, etc.) "
            "against the live registry. Returns violations by severity."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    # ── Session intelligence tools ───────────────────────────────────
    Tool(
        name="organvm_session_agents",
        description=(
            "Multi-agent session inventory — counts and sizes "
            "for Claude, Gemini, and Codex sessions."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="organvm_session_list",
        description=("List recent sessions with metadata (agent, project, date, duration)."),
        inputSchema={
            "type": "object",
            "properties": {
                "agent": {
                    "type": "string",
                    "enum": ["claude", "gemini", "codex"],
                    "description": "Filter by agent",
                },
                "project_filter": {
                    "type": "string",
                    "description": "Filter by project path substring",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max sessions to return (default 20)",
                    "default": 20,
                },
            },
        },
    ),
    Tool(
        name="organvm_session_plans",
        description=(
            "Plan file inventory by project, organ, and agent. "
            "Shows plan metadata including verification status."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_filter": {
                    "type": "string",
                    "description": "Filter by project path substring",
                },
                "organ": {
                    "type": "string",
                    "description": "Filter by organ key",
                },
                "agent": {
                    "type": "string",
                    "enum": ["claude", "gemini", "codex"],
                    "description": "Filter by agent",
                },
            },
        },
    ),
    Tool(
        name="organvm_session_analyze_prompts",
        description=(
            "Cross-session prompt pattern analysis — opening words, "
            "repeated phrases, agent breakdown, and aggregate stats."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "agent": {
                    "type": "string",
                    "enum": ["claude", "gemini", "codex"],
                    "description": "Filter by agent",
                },
                "sample_limit": {
                    "type": "integer",
                    "description": "Max sessions to analyze (default 100)",
                    "default": 100,
                },
            },
        },
    ),
    # ── SOP tools ────────────────────────────────────────────────────
    Tool(
        name="organvm_sop_discover",
        description=(
            "Discover all SOPs and METADOCs across the workspace. "
            "Returns file metadata, scope, phase, and type breakdown."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "organ": {
                    "type": "string",
                    "description": "Filter by organ (CLI key like I, META)",
                },
            },
        },
    ),
    Tool(
        name="organvm_sop_audit",
        description=(
            "Audit SOP coverage vs the METADOC inventory. "
            "Identifies tracked, untracked, reference copies, and missing SOPs."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="organvm_sop_resolve",
        description=(
            "Resolve applicable SOPs for a context using T4>T3>T2 cascade. "
            "System SOPs always included; filters by organ, repo, and phase."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "repo": {"type": "string", "description": "Repository name"},
                "organ": {"type": "string", "description": "Organ key"},
                "phase": {
                    "type": "string",
                    "description": "Lifecycle phase (genesis, foundation, hardening, etc.)",
                },
            },
        },
    ),
    # ── Distill / pattern tools ──────────────────────────────────────
    Tool(
        name="organvm_distill_patterns",
        description="List all 15 operational patterns from the distillation taxonomy.",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="organvm_distill_coverage",
        description=(
            "SOP-to-pattern coverage analysis — which patterns have "
            "backing SOPs, which are partial, which are uncovered."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="organvm_distill_scaffold",
        description=("Generate a SOP markdown scaffold for an uncovered operational pattern."),
        inputSchema={
            "type": "object",
            "properties": {
                "pattern_id": {
                    "type": "string",
                    "description": "Operational pattern ID (e.g., 'repo-onboarding')",
                },
            },
            "required": ["pattern_id"],
        },
    ),
    # ── Metrics tools ────────────────────────────────────────────────
    Tool(
        name="organvm_metrics_compute",
        description=(
            "System-wide metrics: total repos, per-organ counts, "
            "status distribution, code files, test files."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="organvm_metrics_consilience",
        description=(
            "Consilience index report — how well derived principles "
            "are supported by independent research evidence."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="organvm_metrics_ci_trend",
        description="CI pass rate trend over time from soak test snapshots.",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="organvm_metrics_engagement_trend",
        description="Engagement metrics trend (stars, forks) over time.",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="organvm_metrics_vars",
        description=(
            "System variable manifest — all computed metric variables "
            "available for injection into markdown files."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="organvm_metrics_lint",
        description=(
            "Lint workspace for unbound metric references — bare numbers "
            "that should be wrapped in variable markers."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    # ── Atoms / task tracking tools ──────────────────────────────────
    Tool(
        name="organvm_atoms_status",
        description="Atomization pipeline status from pipeline-manifest.json.",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="organvm_atoms_rollup",
        description=(
            "Per-organ task rollup — total/pending/completed tasks "
            "aggregated from the atomization pipeline."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "organ": {
                    "type": "string",
                    "description": "Filter to specific organ (CLI key like III, META)",
                },
            },
        },
    ),
    Tool(
        name="organvm_atoms_tasks",
        description="Pending tasks for a specific repo from the atomization pipeline.",
        inputSchema={
            "type": "object",
            "properties": {
                "repo_name": {
                    "type": "string",
                    "description": "Repository name",
                },
                "organ": {
                    "type": "string",
                    "description": "Organ key (optional, narrows search)",
                },
            },
            "required": ["repo_name"],
        },
    ),
    Tool(
        name="organvm_atoms_links",
        description=(
            "Cross-system task-prompt links — Jaccard-matched connections "
            "between atomized tasks and annotated prompts."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Max links to return (default 50)",
                    "default": 50,
                },
            },
        },
    ),
    # ── Prompting standards tools ────────────────────────────────────
    Tool(
        name="organvm_prompting_guidelines",
        description=(
            "Get agent-specific prompting guidelines — context limits, "
            "preferred format, thinking mode, key patterns."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "agent": {
                    "type": "string",
                    "description": "Agent name (claude, gemini, codex). Default: claude",
                    "default": "claude",
                },
            },
        },
    ),
    Tool(
        name="organvm_prompting_all",
        description="Get all provider prompting guidelines in one view.",
        inputSchema={"type": "object", "properties": {}},
    ),
    # Coordination tools (punch-in/punch-out)
    Tool(
        name="organvm_punch_in",
        description=(
            "Punch in: declare areas of influence for this AI work session. "
            "Other AI streams will see your claim and avoid those areas. "
            "Returns a claim_id (use to punch out) and any conflicts."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "agent": {
                    "type": "string",
                    "description": "Agent name: claude, gemini, codex, human",
                    "default": "claude",
                },
                "session_id": {
                    "type": "string",
                    "description": "Session identifier",
                },
                "organs": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Organ keys being worked on (e.g. ORGAN-I, META)",
                },
                "repos": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Repository names being worked on",
                },
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific file paths being modified",
                },
                "modules": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Module/package names being worked on",
                },
                "scope": {
                    "type": "string",
                    "description": "Free-text description of the work",
                },
                "resource_weight": {
                    "type": "string",
                    "enum": ["light", "medium", "heavy"],
                    "description": (
                        "Resource weight: light (1 unit, read-only/search), "
                        "medium (2 units, code gen/tests), "
                        "heavy (3 units, full builds/parallel subagents). "
                        "Default: medium"
                    ),
                    "default": "medium",
                },
                "test_obligations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Test commands to defer to the prover session "
                        "(e.g. ['pytest organvm-engine/tests/ -v']). "
                        "Don't run tests yourself — declare what needs testing."
                    ),
                },
            },
        },
    ),
    Tool(
        name="organvm_punch_out",
        description=("Punch out: release a work claim. Pass the claim_id from punch_in."),
        inputSchema={
            "type": "object",
            "properties": {
                "claim_id": {
                    "type": "string",
                    "description": "The claim_id returned from punch_in",
                },
            },
            "required": ["claim_id"],
        },
    ),
    Tool(
        name="organvm_work_board",
        description=(
            "View the work board: all active AI stream claims. "
            "Shows who is working on what, across all agents."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="organvm_check_conflicts",
        description=(
            "Check if proposed work areas conflict with active claims "
            "before starting. Does NOT create a claim."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "organs": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Organ keys to check",
                },
                "repos": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Repository names to check",
                },
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "File paths to check",
                },
                "modules": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Module names to check",
                },
            },
        },
    ),
    Tool(
        name="organvm_capacity",
        description=(
            "Check machine resource capacity. Shows current load from "
            "active AI streams (light=1, medium=2, heavy=3 units) "
            "against max capacity (6 units on 16GB M3). "
            "Call before starting heavy work."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="organvm_prove_sweep",
        description=(
            "Collect all pending test obligations from all agent sessions. "
            "Returns a deduplicated list of test commands to run in one "
            "sequential prover session. Agents BUILD and declare test_obligations; "
            "one prover session runs this to verify integrated correctness."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    # Tool checkout line
    Tool(
        name="organvm_tool_checkout",
        description=(
            "Check out a tool before running a command. If another agent "
            "is already running a heavy command, returns wait advisory. "
            "Call before Bash to avoid traffic jams on shared hardware."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "handle": {
                    "type": "string",
                    "description": "Agent handle from punch_in",
                },
                "tool": {
                    "type": "string",
                    "description": "Tool name (default: bash)",
                    "default": "bash",
                },
                "command_hint": {
                    "type": "string",
                    "description": "Command about to run (auto-classifies weight)",
                },
                "weight": {
                    "type": "string",
                    "enum": ["light", "medium", "heavy"],
                    "description": "Override auto weight classification",
                },
            },
            "required": ["handle", "command_hint"],
        },
    ),
    Tool(
        name="organvm_tool_checkin",
        description=(
            "Check in a tool after a command completes. Releases the lane for other agents."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "checkout_id": {
                    "type": "string",
                    "description": "The checkout_id from tool_checkout",
                },
            },
            "required": ["checkout_id"],
        },
    ),
    Tool(
        name="organvm_tool_queue",
        description=(
            "View the tool checkout queue — who's running what right now. "
            "Shows heavy and medium lane occupancy."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    # ── Ecosystem tools ────────────────────────────────────────────────
    Tool(
        name="organvm_ecosystem_profile",
        description=(
            "Get full business ecosystem profile for a product — "
            "delivery, revenue, marketing, community, content arms with status. "
            "Shows coverage stats and gap analysis."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "repo": {
                    "type": "string",
                    "description": "Repository name",
                },
            },
            "required": ["repo"],
        },
    ),
    Tool(
        name="organvm_ecosystem_matrix",
        description=(
            "Cross-product comparison of one pillar (e.g. 'revenue', 'delivery'). "
            "Shows all products' arms for that pillar side by side."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "pillar": {
                    "type": "string",
                    "description": "Pillar name (delivery, revenue, marketing, community, etc.)",
                },
                "organ": {
                    "type": "string",
                    "description": "Optional organ filter (CLI key like III, META)",
                },
            },
            "required": ["pillar"],
        },
    ),
    Tool(
        name="organvm_ecosystem_gaps",
        description=(
            "Find missing pillars/arms across product ecosystems. "
            "Compares against suggested defaults and flags suggestions."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "repo": {
                    "type": "string",
                    "description": "Optional: analyze one repo only",
                },
                "organ": {
                    "type": "string",
                    "description": "Optional organ filter",
                },
            },
        },
    ),
    Tool(
        name="organvm_ecosystem_actions",
        description=(
            "Prioritized next-action list from all ecosystem profiles. "
            "Aggregates next_action fields, sorted by priority."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "organ": {
                    "type": "string",
                    "description": "Optional organ filter",
                },
            },
        },
    ),
    Tool(
        name="organvm_pillar_dna",
        description=(
            "Get pillar DNA lifecycle contracts for a product — "
            "research scope, artifacts, gen/crit prompts, lifecycle gates. "
            "Shows one or all pillars for a repo."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "repo": {
                    "type": "string",
                    "description": "Repository name",
                },
                "pillar": {
                    "type": "string",
                    "description": "Optional: show only one pillar's DNA",
                },
            },
            "required": ["repo"],
        },
    ),
    Tool(
        name="organvm_ecosystem_staleness",
        description=(
            "Staleness report for pillar DNA artifacts. "
            "Checks all artifact freshness against staleness thresholds."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "repo": {
                    "type": "string",
                    "description": "Optional: check one repo only",
                },
                "organ": {
                    "type": "string",
                    "description": "Optional organ filter",
                },
            },
        },
    ),
    Tool(
        name="organvm_ecosystem_lifecycle",
        description=(
            "Lifecycle stages across repos — shows which stage each pillar "
            "is in (conception, research, planning, building, live, etc.)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "organ": {
                    "type": "string",
                    "description": "Optional organ filter",
                },
            },
        },
    ),
    # ── Pulse tools ──────────────────────────────────────────────────
    Tool(
        name="organvm_pulse_mood",
        description=(
            "System mood — qualitative health summary derived from "
            "organism health %, density, staleness, and velocity signals. "
            "Returns mood (fragile/stressed/stagnant/steady/growing/thriving) "
            "with reasoning."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="organvm_pulse_density",
        description=(
            "Interconnection density — edge saturation, cross-organ wiring, "
            "seed/CI/test/doc coverage, and composite density score (0-100). "
            "Low density = under-wired and fragile."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="organvm_pulse_events",
        description=(
            "Recent events from the append-only event bus. "
            "Filter by event type and limit. "
            "Shows registry updates, promotions, gate changes, mood shifts."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "event_type": {
                    "type": "string",
                    "description": "Filter by event type (e.g. 'repo.promoted', 'gate.changed')",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max events to return (default 20)",
                    "default": 20,
                },
            },
        },
    ),
    Tool(
        name="organvm_pulse_nerve",
        description=(
            "Subscription wiring from seed.yaml declarations — "
            "which repos listen for which events. "
            "Optionally filter to listeners for a specific event type."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "event_type": {
                    "type": "string",
                    "description": "Show only listeners for this event type",
                },
            },
        },
    ),
    Tool(
        name="organvm_pulse_emit",
        description=(
            "Emit an event to the event bus and show propagation results. "
            "Returns the emitted event and list of notified subscribers."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "event_type": {
                    "type": "string",
                    "description": "Event type string (e.g. 'repo.promoted')",
                },
                "source": {
                    "type": "string",
                    "description": "Event source identifier (default: 'mcp')",
                    "default": "mcp",
                },
                "payload": {
                    "type": "object",
                    "description": "Optional JSON payload for the event",
                },
            },
            "required": ["event_type"],
        },
    ),
    Tool(
        name="organvm_pulse_briefing",
        description=(
            "Session briefing for recent system activity — "
            "what changed in the last N hours. "
            "Useful for session openers."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "hours": {
                    "type": "integer",
                    "description": "Hours to look back (default 24)",
                    "default": 24,
                },
            },
        },
    ),
    Tool(
        name="organvm_pulse_memory",
        description=(
            "Query shared cross-agent memory — insights recorded by "
            "Claude, Gemini, Codex sessions for collective awareness."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Filter by category (e.g. 'bug', 'pattern', 'decision')",
                },
                "agent": {
                    "type": "string",
                    "description": "Filter by agent name (claude, gemini, codex)",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max insights to return (default 20)",
                    "default": 20,
                },
            },
        },
    ),
    Tool(
        name="organvm_pulse_record_insight",
        description=(
            "Record a new insight to shared cross-agent memory. "
            "Other agents will see this in pulse_memory queries."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "agent": {
                    "type": "string",
                    "description": "Agent recording the insight (claude, gemini, codex)",
                },
                "category": {
                    "type": "string",
                    "description": "Insight category (bug, pattern, decision, observation)",
                },
                "content": {
                    "type": "string",
                    "description": "The insight text",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional tags for the insight",
                },
                "organ": {
                    "type": "string",
                    "description": "Optional organ key this insight relates to",
                },
                "repo": {
                    "type": "string",
                    "description": "Optional repo name this insight relates to",
                },
            },
            "required": ["agent", "category", "content"],
        },
    ),
    Tool(
        name="organvm_pulse_flow",
        description=(
            "Dependency flow activity — measures data flow through "
            "the seed graph over recent time window."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    # Audit
    Tool(
        name="organvm_infrastructure_audit",
        description=(
            "Run infrastructure wiring audit — 6-layer verification of filesystem, "
            "registry/seed reconciliation, seed completeness, edge resolution, "
            "content artifacts, and deposit scanning. Returns findings by severity."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "organ": {
                    "type": "string",
                    "description": "Optional organ filter (e.g. ORGAN-I, META-ORGANVM)",
                },
                "layer": {
                    "type": "string",
                    "description": (
                        "Optional single layer: filesystem, reconcile, seeds, "
                        "edges, content, absorption"
                    ),
                },
                "scope": {
                    "type": "string",
                    "description": "Optional repo name to scope the audit to",
                },
            },
        },
    ),
    # Verification
    Tool(
        name="organvm_verify_system",
        description=(
            "Run formal verification of the dispatch pipeline — checks contract "
            "coverage (Hoare Logic), temporal ordering (DAG enforcement), and "
            "idempotency (duplicate dispatch detection). Returns a unified report."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "include_ledger": {
                    "type": "boolean",
                    "description": "Include dispatch ledger analysis (default: true)",
                },
            },
        },
    ),
    Tool(
        name="organvm_verify_contracts",
        description=(
            "Check registered dispatch contracts — shows required payload fields, "
            "validators, and consumption semantics for each event type."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "event": {
                    "type": "string",
                    "description": "Optional specific event type to check",
                },
            },
        },
    ),
    # Styx Orchestration
    Tool(
        name="organvm_styx_orchestrate_stake",
        description=(
            "Trigger a behavioral stake orchestration sequence. "
            "Validates the stake contract and triggers the Taxis receiver."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "commitment": {
                    "type": "string",
                    "description": "The theoretical commitment being staked against.",
                },
                "amount": {
                    "type": "integer",
                    "description": "Stake amount in fiat units.",
                },
                "source_organ": {
                    "type": "string",
                    "description": "The organ repo creating the stake (default: organvm-iii-ergon).",
                    "default": "organvm-iii-ergon",
                },
            },
            "required": ["commitment", "amount"],
        },
    ),
    Tool(
        name="organvm_styx_resolve_audit",
        description=("Resolve a behavioral stake based on peer audit results."),
        inputSchema={
            "type": "object",
            "properties": {
                "stake_id": {
                    "type": "string",
                    "description": "The unique ID of the stake to resolve.",
                },
                "outcome": {
                    "type": "string",
                    "enum": ["PASS", "FAIL"],
                    "description": "The outcome of the peer audit.",
                },
                "auditor": {
                    "type": "string",
                    "description": "The organ repo performing the audit (default: organvm-vi-koinonia).",
                    "default": "organvm-vi-koinonia",
                },
                "proof_hash": {
                    "type": "string",
                    "description": "The cryptographic proof hash from the audit.",
                },
            },
            "required": ["stake_id", "outcome", "proof_hash"],
        },
    ),
]


# ── Tool dispatch ─────────────────────────────────────────────────

_DISPATCH = {
    # Registry
    "organvm_query_registry": lambda args: registry.query_registry(**args),
    "organvm_get_repo": lambda args: registry.get_repo(**args),
    "organvm_list_organs": lambda args: registry.list_organs(),
    # Seeds
    "organvm_get_seed": lambda args: seeds.get_seed(**args),
    "organvm_find_edges": lambda args: seeds.find_edges(**args),
    "organvm_get_event_contract": lambda args: seeds.get_event_contract(**args),
    "organvm_list_events": lambda args: seeds.list_events(),
    # Graph
    "organvm_trace_dependencies": lambda args: graph.trace_dependencies(**args),
    "organvm_check_dependency": lambda args: graph.check_dependency(**args),
    "organvm_get_dependency_graph": lambda args: graph.get_dependency_graph(**args),
    # Health / Organism
    "organvm_organism": lambda args: health.organism(**args),
    "organvm_system_health": lambda args: health.system_health(),
    "organvm_omega_status": lambda args: health.omega_status(),
    "organvm_ci_health": lambda args: health.ci_health(),
    "organvm_upcoming_deadlines": lambda args: health.deadlines(**args),
    "organvm_pitch_status": lambda args: health.pitch_status(),
    # Context
    "organvm_get_context": lambda args: context.get_context(**args),
    # Revenue
    "organvm_revenue_pipeline": lambda args: revenue.revenue_pipeline(),
    "organvm_revenue_products": lambda args: revenue.revenue_products(),
    "organvm_revenue_readiness": lambda args: revenue.revenue_readiness(**args),
    "organvm_revenue_grants": lambda args: revenue.revenue_grants(**args),
    "organvm_revenue_consulting": lambda args: revenue.revenue_consulting(),
    # Governance
    "organvm_governance_audit": lambda args: governance.governance_audit(),
    "organvm_governance_check_transition": lambda args: governance.governance_check_transition(
        **args,
    ),
    "organvm_governance_valid_transitions": lambda args: governance.governance_valid_transitions(
        **args,
    ),
    "organvm_governance_validate_deps": lambda args: governance.governance_validate_deps(),
    "organvm_governance_impact": lambda args: governance.governance_impact(**args),
    "organvm_governance_feedback_loops": lambda args: governance.governance_feedback_loops(),
    "organvm_governance_dictums": lambda args: governance.governance_dictums(**args),
    "organvm_governance_check_dictums": lambda args: governance.governance_check_dictums(),
    # Sessions
    "organvm_session_agents": lambda args: sessions.session_agents(),
    "organvm_session_list": lambda args: sessions.session_list(**args),
    "organvm_session_plans": lambda args: sessions.session_plans(**args),
    "organvm_session_analyze_prompts": lambda args: sessions.session_analyze_prompts(**args),
    # SOPs
    "organvm_sop_discover": lambda args: sops.sop_discover(**args),
    "organvm_sop_audit": lambda args: sops.sop_audit(),
    "organvm_sop_resolve": lambda args: sops.sop_resolve(**args),
    # Distill
    "organvm_distill_patterns": lambda args: distill.distill_patterns(),
    "organvm_distill_coverage": lambda args: distill.distill_coverage(),
    "organvm_distill_scaffold": lambda args: distill.distill_scaffold(**args),
    # Metrics
    "organvm_metrics_compute": lambda args: metrics.metrics_compute(),
    "organvm_metrics_consilience": lambda args: metrics.metrics_consilience(),
    "organvm_metrics_ci_trend": lambda args: metrics.metrics_ci_trend(),
    "organvm_metrics_engagement_trend": lambda args: metrics.metrics_engagement_trend(),
    "organvm_metrics_vars": lambda args: metrics.metrics_vars(),
    "organvm_metrics_lint": lambda args: metrics.metrics_lint(),
    # Atoms
    "organvm_atoms_status": lambda args: atoms.atoms_status(),
    "organvm_atoms_rollup": lambda args: atoms.atoms_rollup(**args),
    "organvm_atoms_tasks": lambda args: atoms.atoms_tasks(**args),
    "organvm_atoms_links": lambda args: atoms.atoms_links(**args),
    # Prompting
    "organvm_prompting_guidelines": lambda args: prompting.prompting_guidelines(**args),
    "organvm_prompting_all": lambda args: prompting.prompting_all(),
    # Coordination
    "organvm_punch_in": lambda args: coordination.coordination_punch_in(**args),
    "organvm_punch_out": lambda args: coordination.coordination_punch_out(**args),
    "organvm_work_board": lambda args: coordination.coordination_work_board(),
    "organvm_check_conflicts": lambda args: coordination.coordination_check_conflicts(**args),
    "organvm_capacity": lambda args: coordination.coordination_capacity(),
    "organvm_prove_sweep": lambda args: coordination.coordination_prove_sweep(),
    "organvm_tool_checkout": lambda args: coordination.coordination_tool_checkout(**args),
    "organvm_tool_checkin": lambda args: coordination.coordination_tool_checkin(**args),
    "organvm_tool_queue": lambda args: coordination.coordination_tool_queue(),
    # Ecosystem
    "organvm_ecosystem_profile": lambda args: ecosystem.ecosystem_profile(**args),
    "organvm_ecosystem_matrix": lambda args: ecosystem.ecosystem_matrix(**args),
    "organvm_ecosystem_gaps": lambda args: ecosystem.ecosystem_gaps(**args),
    "organvm_ecosystem_actions": lambda args: ecosystem.ecosystem_actions(**args),
    "organvm_pillar_dna": lambda args: ecosystem.pillar_dna(**args),
    "organvm_ecosystem_staleness": lambda args: ecosystem.ecosystem_staleness(**args),
    "organvm_ecosystem_lifecycle": lambda args: ecosystem.ecosystem_lifecycle(**args),
    # Pulse
    "organvm_pulse_mood": lambda args: pulse.pulse_mood(),
    "organvm_pulse_density": lambda args: pulse.pulse_density(),
    "organvm_pulse_events": lambda args: pulse.pulse_events(**args),
    "organvm_pulse_nerve": lambda args: pulse.pulse_nerve(**args),
    "organvm_pulse_emit": lambda args: pulse.pulse_emit(**args),
    "organvm_pulse_briefing": lambda args: pulse.pulse_briefing(**args),
    "organvm_pulse_memory": lambda args: pulse.pulse_memory(**args),
    "organvm_pulse_record_insight": lambda args: pulse.pulse_record_insight(**args),
    "organvm_pulse_flow": lambda args: pulse.pulse_flow(),
    # Audit
    "organvm_infrastructure_audit": lambda args: audit.infrastructure_audit(**args),
    # Verification
    "organvm_verify_system": lambda args: verification.verify_system(**args),
    "organvm_verify_contracts": lambda args: verification.verify_contracts(**args),
    # Styx
    "organvm_styx_orchestrate_stake": lambda args: styx.styx_orchestrate_stake(**args),
    "organvm_styx_resolve_audit": lambda args: styx.styx_resolve_audit(**args),
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
    import sys
    # stdio_server() reads sys.stdout.buffer at entry, so we must call it
    # BEFORE redirecting stdout. Then redirect so stray print() calls go to
    # stderr instead of corrupting the JSON-RPC stream.
    async with stdio_server() as (read_stream, write_stream):
        sys.stdout = sys.stderr
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    main()
