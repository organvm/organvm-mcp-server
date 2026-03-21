"""Tests for MCP server tools."""

from __future__ import annotations

from datetime import date
from unittest.mock import patch

import pytest

from organvm_mcp.tools import context, graph, health, registry, seeds


@pytest.fixture
def mock_registry_data():
    return {
        "organs": {
            "ORGAN-I": {
                "name": "Theory",
                "organization": "organvm-i-theoria",
                "repositories": [
                    {
                        "name": "repo-a",
                        "tier": "flagship",
                        "promotion_status": "GRADUATED",
                        "implementation_status": "ACTIVE",
                        "dependencies": [],
                    },
                    {
                        "name": "repo-b",
                        "tier": "standard",
                        "promotion_status": "LOCAL",
                        "implementation_status": "ACTIVE",
                        "dependencies": ["repo-a"],
                    },
                ],
            },
            "ORGAN-II": {
                "name": "Art",
                "organization": "organvm-ii-poiesis",
                "repositories": [
                    {
                        "name": "repo-c",
                        "tier": "flagship",
                        "promotion_status": "PUBLIC_PROCESS",
                        "implementation_status": "ACTIVE",
                        "dependencies": ["organvm-i-theoria/repo-a"],
                    },
                ],
            },
        },
    }


class TestRegistryTools:
    @patch("organvm_mcp.data.loader.load_registry")
    def test_query_registry(self, mock_load, mock_registry_data):
        mock_load.return_value = mock_registry_data
        res = registry.query_registry(organ="ORGAN-I")
        assert len(res["repos"]) == 2
        assert res["total"] == 2

    @patch("organvm_mcp.data.loader.load_registry")
    def test_query_registry_by_promotion_status(self, mock_load, mock_registry_data):
        mock_load.return_value = mock_registry_data
        res = registry.query_registry(promotion_status="GRADUATED")
        assert res["total"] == 1
        assert res["repos"][0]["name"] == "repo-a"

    @patch("organvm_mcp.data.loader.load_registry")
    def test_query_registry_by_tier(self, mock_load, mock_registry_data):
        mock_load.return_value = mock_registry_data
        res = registry.query_registry(tier="flagship")
        assert res["total"] == 2

    @patch("organvm_mcp.data.loader.load_registry")
    def test_query_registry_by_name_pattern(self, mock_load, mock_registry_data):
        mock_load.return_value = mock_registry_data
        res = registry.query_registry(name_pattern="repo-a")
        assert res["total"] == 1
        assert res["repos"][0]["name"] == "repo-a"

    @patch("organvm_mcp.data.loader.load_registry")
    def test_query_registry_limit(self, mock_load, mock_registry_data):
        mock_load.return_value = mock_registry_data
        res = registry.query_registry(limit=1)
        assert len(res["repos"]) == 1
        assert res["total"] == 3  # total matches, but only 1 returned

    @patch("organvm_mcp.data.loader.load_registry")
    def test_get_repo(self, mock_load, mock_registry_data):
        mock_load.return_value = mock_registry_data
        res = registry.get_repo(org="organvm-i-theoria", name="repo-a")
        assert res["name"] == "repo-a"
        assert res["organ"] == "ORGAN-I"

    @patch("organvm_mcp.data.loader.load_registry")
    def test_get_repo_not_found(self, mock_load, mock_registry_data):
        mock_load.return_value = mock_registry_data
        res = registry.get_repo(org="organvm-i-theoria", name="nonexistent")
        assert "error" in res

    @patch("organvm_mcp.data.loader.load_registry")
    def test_list_organs(self, mock_load, mock_registry_data):
        mock_load.return_value = mock_registry_data
        res = registry.list_organs()
        assert len(res["organs"]) == 2
        organ_keys = {o["key"] for o in res["organs"]}
        assert "ORGAN-I" in organ_keys
        assert "ORGAN-II" in organ_keys

    @patch("organvm_mcp.data.loader.load_registry")
    def test_list_organs_counts(self, mock_load, mock_registry_data):
        mock_load.return_value = mock_registry_data
        res = registry.list_organs()
        organ_i = next(o for o in res["organs"] if o["key"] == "ORGAN-I")
        assert organ_i["repo_count"] == 2
        assert organ_i["flagship_count"] == 1


class TestSeedTools:
    @patch("organvm_mcp.data.loader.load_all_seeds")
    def test_find_edges(self, mock_load):
        mock_load.return_value = [
            {
                "org": "org",
                "repo": "repo-a",
                "organ": "ORGAN-I",
                "produces": [{"target": "repo-b", "artifact": "data"}],
            },
        ]
        res = seeds.find_edges(repo="repo-a")
        assert len(res["edges"]) == 1
        assert res["edges"][0]["target"] == "repo-b"

    @patch("organvm_mcp.data.loader.load_all_seeds")
    def test_find_edges_no_match(self, mock_load):
        mock_load.return_value = [
            {"org": "org", "repo": "repo-a", "organ": "ORGAN-I", "produces": []},
        ]
        res = seeds.find_edges(repo="nonexistent")
        assert len(res["edges"]) == 0

    @patch("organvm_mcp.data.loader.load_all_seeds")
    def test_get_seed_found(self, mock_load):
        mock_load.return_value = [
            {"org": "org-a", "repo": "repo-a", "organ": "ORGAN-I", "tier": "flagship"},
        ]
        res = seeds.get_seed(org="org-a", name="repo-a")
        assert res["tier"] == "flagship"

    @patch("organvm_mcp.data.loader.load_all_seeds")
    def test_get_seed_not_found(self, mock_load):
        mock_load.return_value = [
            {"org": "org-a", "repo": "repo-a", "organ": "ORGAN-I"},
        ]
        res = seeds.get_seed(org="org-a", name="nonexistent")
        assert "error" in res

    @patch("organvm_mcp.data.loader.load_event_catalog")
    def test_get_event_contract_found(self, mock_load):
        mock_load.return_value = [
            {"event_type": "essay.published", "edge": "V->VI", "producer": "ORGAN-V"},
        ]
        res = seeds.get_event_contract("essay.published")
        assert res["event_type"] == "essay.published"

    @patch("organvm_mcp.data.loader.load_event_catalog")
    def test_get_event_contract_not_found(self, mock_load):
        mock_load.return_value = [
            {"event_type": "essay.published"},
        ]
        res = seeds.get_event_contract("nonexistent.event")
        assert "error" in res

    @patch("organvm_mcp.data.loader.load_event_catalog")
    def test_list_events(self, mock_load):
        mock_load.return_value = [
            {
                "event_type": "essay.published",
                "edge": "V->VI",
                "producer": "ORGAN-V",
                "consumer": "ORGAN-VI",
            },
            {
                "event_type": "theory.candidate",
                "edge": "I->IV",
                "producer": "ORGAN-I",
                "consumer": "ORGAN-IV",
            },
        ]
        res = seeds.list_events()
        assert len(res["events"]) == 2

    @patch("organvm_mcp.data.loader.load_all_seeds")
    def test_find_edges_produces_only(self, mock_load):
        mock_load.return_value = [
            {
                "org": "org",
                "repo": "repo-a",
                "organ": "ORGAN-I",
                "produces": [{"target": "repo-b", "artifact": "data"}],
                "consumes": [{"source": "repo-c", "artifact": "schemas"}],
            },
        ]
        res = seeds.find_edges(repo="repo-a", direction="produces")
        assert len(res["edges"]) == 1
        assert res["edges"][0]["direction"] == "produces"


class TestGraphTools:
    @patch("organvm_mcp.data.loader.load_registry")
    def test_trace_dependencies(self, mock_load, mock_registry_data):
        mock_load.return_value = mock_registry_data
        res = graph.trace_dependencies(repo="repo-b", direction="upstream")
        assert len(res["upstream"]) == 1
        assert res["upstream"][0]["repo"] == "repo-a"
        assert res["upstream"][0]["organ"] == "ORGAN-I"

    @patch("organvm_mcp.data.loader.load_registry")
    def test_trace_dependencies_normalizes_canonical_dependency_names(
        self,
        mock_load,
        mock_registry_data,
    ):
        mock_load.return_value = mock_registry_data
        res = graph.trace_dependencies(repo="repo-c", direction="upstream")
        assert len(res["upstream"]) == 1
        assert res["upstream"][0]["repo"] == "repo-a"
        assert res["upstream"][0]["organ"] == "ORGAN-I"

    @patch("organvm_mcp.data.loader.load_registry")
    def test_trace_dependencies_downstream_with_canonical_repo_arg(
        self,
        mock_load,
        mock_registry_data,
    ):
        mock_load.return_value = mock_registry_data
        res = graph.trace_dependencies(
            repo="organvm-i-theoria/repo-a",
            direction="downstream",
            depth=2,
        )
        downstream = {entry["repo"] for entry in res["downstream"]}
        assert "repo-b" in downstream
        assert "repo-c" in downstream

    @patch("organvm_mcp.data.loader.load_registry")
    def test_trace_dependencies_unknown_repo(self, mock_load, mock_registry_data):
        mock_load.return_value = mock_registry_data
        res = graph.trace_dependencies(repo="does-not-exist")
        assert "error" in res

    @patch("organvm_mcp.data.loader.load_governance_rules")
    def test_check_dependency_allowed(self, mock_load):
        mock_load.return_value = {"allowed_edges": [], "forbidden_edges": []}
        res = graph.check_dependency(source_organ="ORGAN-III", target_organ="ORGAN-I")
        assert res["allowed"] is True

    @patch("organvm_mcp.data.loader.load_governance_rules")
    def test_check_dependency_back_edge(self, mock_load):
        mock_load.return_value = {"allowed_edges": [], "forbidden_edges": []}
        res = graph.check_dependency(source_organ="ORGAN-I", target_organ="ORGAN-III")
        assert res["allowed"] is False

    @patch("organvm_mcp.data.loader.load_all_seeds")
    @patch("organvm_mcp.data.loader.load_registry")
    def test_get_dependency_graph_full(self, mock_reg, mock_seeds, mock_registry_data):
        mock_reg.return_value = mock_registry_data
        mock_seeds.return_value = []
        res = graph.get_dependency_graph()
        assert "nodes" in res
        assert "edges" in res
        assert len(res["nodes"]) == 3

    @patch("organvm_mcp.data.loader.load_all_seeds")
    @patch("organvm_mcp.data.loader.load_registry")
    def test_get_dependency_graph_filtered(self, mock_reg, mock_seeds, mock_registry_data):
        mock_reg.return_value = mock_registry_data
        mock_seeds.return_value = []
        res = graph.get_dependency_graph(organ="ORGAN-I")
        assert all(n["organ"] == "ORGAN-I" for n in res["nodes"])
        assert len(res["nodes"]) == 2

    @patch("organvm_mcp.data.loader.load_governance_rules")
    def test_check_dependency_no_rules(self, mock_load):
        mock_load.return_value = {}
        res = graph.check_dependency(source_organ="ORGAN-I", target_organ="ORGAN-II")
        assert res["allowed"] is True

    @patch("organvm_mcp.data.loader.load_governance_rules")
    def test_check_dependency_forbidden_edge(self, mock_load):
        mock_load.return_value = {
            "allowed_edges": [],
            "forbidden_edges": ["ORGAN-I->ORGAN-VII"],
        }
        res = graph.check_dependency(source_organ="ORGAN-I", target_organ="ORGAN-VII")
        assert res["allowed"] is False
        assert "forbidden" in res["reason"]

    def test_normalize_repo_name_with_slash(self):
        assert graph._normalize_repo_name("org/repo") == "repo"

    def test_normalize_repo_name_empty(self):
        assert graph._normalize_repo_name("") == ""


class TestHealthTools:
    @patch("organvm_mcp.data.loader.load_all_seeds")
    @patch("organvm_mcp.data.loader.load_registry")
    def test_system_health(self, mock_reg, mock_seeds, mock_registry_data):
        mock_reg.return_value = mock_registry_data
        mock_seeds.return_value = [{"repo": "repo-a"}, {"repo": "repo-b"}]
        res = health.system_health()
        assert res["total_repos"] == 3
        assert res["active_repos"] == 3
        assert "ci_coverage" in res
        assert "test_coverage" in res
        assert "docs_coverage" in res
        assert "seed_coverage" in res
        assert "by_organ" in res
        assert "promotion_distribution" in res
        assert "timestamp" in res

    @patch("organvm_engine.omega.scorecard.evaluate")
    @patch("organvm_mcp.data.loader.load_registry")
    def test_omega_status_returns_structure(self, mock_reg, mock_eval, mock_registry_data):
        from organvm_engine.omega.scorecard import OmegaCriterion, OmegaScorecard, SoakStreak

        mock_reg.return_value = mock_registry_data
        mock_eval.return_value = OmegaScorecard(
            criteria=[
                OmegaCriterion(
                    id=i,
                    name=f"C{i}",
                    horizon="H1",
                    measurement="test",
                    auto=False,
                    status="MET" if i == 6 else "NOT_MET",
                    value="x",
                )
                for i in range(1, 18)
            ],
            soak=SoakStreak(total_snapshots=8, streak_days=8),
            generated="2026-02-24T00:00:00",
        )
        res = health.omega_status()
        assert "score" in res
        assert "total" in res
        assert res["total"] == 17
        assert "criteria" in res
        assert len(res["criteria"]) == 17
        assert "soak" in res
        assert "generated" in res

    @patch("organvm_engine.ci.triage.triage")
    def test_ci_health(self, mock_triage):
        from organvm_engine.ci.triage import CITriageReport

        mock_triage.return_value = CITriageReport(
            date="2026-02-23",
            total_checked=77,
            passing=52,
            failing=25,
            pass_rate=0.675,
            by_organ={"ORGAN-I": [{"name": "repo-a"}]},
            phantom_candidates=[".github"],
        )
        res = health.ci_health()
        assert res["failing"] == 25
        assert "ORGAN-I" in res["by_organ"]

    @patch("organvm_engine.deadlines.parser.filter_upcoming")
    @patch("organvm_engine.deadlines.parser.parse_deadlines")
    def test_deadlines(self, mock_parse, mock_filter):
        from organvm_engine.deadlines.parser import Deadline

        mock_deadlines = [
            Deadline(item_id="F4", description="Submit NEH", deadline_date=date(2026, 3, 6)),
        ]
        mock_parse.return_value = mock_deadlines
        mock_filter.return_value = mock_deadlines
        res = health.deadlines(days=30)
        assert res["total_shown"] == 1
        assert res["deadlines"][0]["item_id"] == "F4"

    @patch("organvm_mcp.data.loader.load_all_seeds")
    @patch("organvm_mcp.data.loader.load_registry")
    def test_organism_full_view(self, mock_reg, mock_seeds, mock_registry_data):
        mock_reg.return_value = mock_registry_data
        mock_seeds.return_value = []
        res = health.organism()
        assert "total_repos" in res
        assert "organs" in res
        assert "sys_pct" in res
        assert res["total_repos"] == 3

    @patch("organvm_mcp.data.loader.load_registry")
    def test_organism_gates_view(self, mock_reg, mock_registry_data):
        mock_reg.return_value = mock_registry_data
        res = health.organism(view="gates")
        assert "gates" in res
        assert isinstance(res["gates"], list)
        assert len(res["gates"]) > 0
        # Each gate entry should have standard fields
        gate = res["gates"][0]
        assert "name" in gate
        assert "applicable" in gate
        assert "passed" in gate

    @patch("organvm_mcp.data.loader.load_registry")
    def test_organism_blockers_view(self, mock_reg, mock_registry_data):
        mock_reg.return_value = mock_registry_data
        res = health.organism(view="blockers")
        assert "ready" in res
        assert "blocked" in res
        assert isinstance(res["ready"], list)
        assert isinstance(res["blocked"], list)

    @patch("organvm_mcp.data.loader.load_registry")
    def test_organism_organ_zoom(self, mock_reg, mock_registry_data):
        mock_reg.return_value = mock_registry_data
        res = health.organism(organ="ORGAN-I")
        assert res["organ_id"] == "ORGAN-I"
        assert res["count"] == 2
        assert "repos" in res

    @patch("organvm_mcp.data.loader.load_registry")
    def test_organism_repo_zoom(self, mock_reg, mock_registry_data):
        mock_reg.return_value = mock_registry_data
        res = health.organism(repo="repo-a")
        assert res["repo"] == "repo-a"
        assert res["organ"] == "ORGAN-I"
        assert "gates" in res
        assert "pct" in res

    @patch("organvm_mcp.data.loader.load_all_seeds")
    @patch("organvm_mcp.data.loader.load_registry")
    def test_system_health_has_organism_fields(self, mock_reg, mock_seeds, mock_registry_data):
        mock_reg.return_value = mock_registry_data
        mock_seeds.return_value = [{"repo": "repo-a"}, {"repo": "repo-b"}]
        res = health.system_health()
        # Organism-derived fields
        assert "ci_coverage" in res
        assert "promotion_distribution" in res
        assert "by_organ" in res
        assert isinstance(res["ci_coverage"], float)
        assert isinstance(res["promotion_distribution"], dict)
        assert isinstance(res["by_organ"], dict)
        # Supplemental fields not from organism
        assert "seed_coverage" in res
        assert "revenue_status" in res
        assert "timestamp" in res
        # Verify 'generated' was renamed to 'timestamp'
        assert "generated" not in res


class TestContextTools:
    @patch("organvm_mcp.data.loader.load_conversation_corpus_surfaces")
    @patch("organvm_mcp.data.loader.load_registry")
    @patch("organvm_mcp.data.loader.load_all_seeds")
    def test_get_context(self, mock_seeds, mock_reg, mock_surfaces, mock_registry_data):
        mock_reg.return_value = mock_registry_data
        mock_seeds.return_value = []
        mock_surfaces.return_value = {
            "surface_count": 1,
            "valid_count": 1,
            "partial_count": 0,
            "invalid_count": 0,
            "surfaces": [
                {
                    "repo": "conversation-corpus-engine",
                    "organization": "organvm-i-theoria",
                    "repo_root": "/tmp/cce",
                    "surface_dir": "/tmp/cce/reports/surfaces",
                    "state": "valid",
                    "files": {"bundle": "/tmp/cce/reports/surfaces/surface-bundle.json"},
                    "summary": {"provider_count": 1},
                    "validation": {},
                },
            ],
        }
        res = context.get_context(repo="repo-a")
        assert res["repo"]["name"] == "repo-a"
        assert res["organ"]["key"] == "ORGAN-I"
        assert res["conversation_corpus"]["surface_count"] == 1

    @patch("organvm_mcp.data.loader.load_conversation_corpus_surfaces")
    @patch("organvm_mcp.data.loader.load_registry")
    @patch("organvm_mcp.data.loader.load_all_seeds")
    def test_get_context_not_found(self, mock_seeds, mock_reg, mock_surfaces, mock_registry_data):
        mock_reg.return_value = mock_registry_data
        mock_seeds.return_value = []
        mock_surfaces.return_value = {"surface_count": 0, "surfaces": []}
        res = context.get_context(repo="nonexistent")
        assert "error" in res

    @patch("organvm_mcp.data.loader.load_conversation_corpus_surfaces")
    @patch("organvm_mcp.data.loader.load_registry")
    @patch("organvm_mcp.data.loader.load_all_seeds")
    def test_get_context_with_seeds(self, mock_seeds, mock_reg, mock_surfaces, mock_registry_data):
        mock_reg.return_value = mock_registry_data
        mock_seeds.return_value = [
            {
                "repo": "repo-a",
                "produces": [{"target": "repo-b", "artifact": "schemas"}],
                "consumes": [],
            },
        ]
        mock_surfaces.return_value = {"surface_count": 0, "surfaces": []}
        res = context.get_context(repo="repo-a")
        assert len(res["edges"]["produces"]) == 1

    @patch("organvm_mcp.data.loader.load_conversation_corpus_surfaces")
    @patch("organvm_mcp.data.loader.load_registry")
    @patch("organvm_mcp.data.loader.load_all_seeds")
    def test_get_context_includes_siblings(
        self,
        mock_seeds,
        mock_reg,
        mock_surfaces,
        mock_registry_data,
    ):
        mock_reg.return_value = mock_registry_data
        mock_seeds.return_value = []
        mock_surfaces.return_value = {"surface_count": 0, "surfaces": []}
        res = context.get_context(repo="repo-a")
        assert "repo-b" in res["siblings"]

    @patch("organvm_mcp.data.loader.load_conversation_corpus_surfaces")
    @patch("organvm_mcp.data.loader.load_registry")
    @patch("organvm_mcp.data.loader.load_all_seeds")
    def test_get_context_personal_repo(
        self,
        mock_seeds,
        mock_reg,
        mock_surfaces,
        mock_registry_data,
    ):
        mock_reg.return_value = mock_registry_data
        mock_seeds.return_value = []
        mock_surfaces.return_value = {"surface_count": 0, "surfaces": []}
        res = context.get_context(repo="my-site", org="4444J99")
        assert res["repo"]["tier"] == "personal"

    @patch("organvm_mcp.data.loader.load_conversation_corpus_surfaces")
    @patch("organvm_mcp.data.loader.load_registry")
    @patch("organvm_mcp.data.loader.load_all_seeds")
    def test_get_context_markdown(self, mock_seeds, mock_reg, mock_surfaces, mock_registry_data):
        mock_reg.return_value = mock_registry_data
        mock_seeds.return_value = []
        mock_surfaces.return_value = {
            "surface_count": 1,
            "valid_count": 1,
            "partial_count": 0,
            "invalid_count": 0,
            "surfaces": [
                {
                    "repo": "conversation-corpus-engine",
                    "organization": "organvm-i-theoria",
                    "repo_root": "/tmp/cce",
                    "surface_dir": "/tmp/cce/reports/surfaces",
                    "state": "valid",
                    "files": {"bundle": "/tmp/cce/reports/surfaces/surface-bundle.json"},
                    "summary": {"provider_count": 1},
                    "validation": {},
                },
            ],
        }
        res = context.get_context_markdown(repo="repo-a")
        assert "## System Context" in res
        assert "ORGAN-I" in res
        assert "Conversation Corpus" in res

    @patch("organvm_mcp.data.loader.load_conversation_corpus_surfaces")
    def test_conversation_corpus_surfaces(self, mock_surfaces):
        mock_surfaces.return_value = {
            "surface_count": 2,
            "valid_count": 1,
            "partial_count": 1,
            "invalid_count": 0,
            "surfaces": [
                {
                    "repo": "conversation-corpus-engine",
                    "organization": "organvm-i-theoria",
                    "repo_root": "/tmp/cce",
                    "surface_dir": "/tmp/cce/reports/surfaces",
                    "state": "valid",
                    "files": {"bundle": "/tmp/cce/reports/surfaces/surface-bundle.json"},
                    "summary": {"provider_count": 2},
                    "validation": {},
                },
                {
                    "repo": "other-repo",
                    "organization": "meta-organvm",
                    "repo_root": "/tmp/other",
                    "surface_dir": "/tmp/other/reports/surfaces",
                    "state": "partial",
                    "files": {"bundle": None},
                    "summary": {"provider_count": 0},
                    "validation": {},
                },
            ],
        }
        res = context.conversation_corpus_surfaces(state="valid")
        assert res["surface_count"] == 1
        assert res["surfaces"][0]["repo"] == "conversation-corpus-engine"


# ── Network tool tests ────────────────────────────────────────────────

class TestNetworkTools:
    """Tests for network testament MCP tool handlers."""

    @patch("organvm_mcp.tools.network._load_maps")
    def test_network_map_all(self, mock_maps):
        from organvm_engine.network.schema import MirrorEntry, NetworkMap

        from organvm_mcp.tools.network import network_map

        mock_maps.return_value = [
            NetworkMap(
                schema_version="1.0", repo="test-repo", organ="META",
                technical=[MirrorEntry(
                    project="astral-sh/ruff", platform="github", relevance="linter",
                )],
            ),
        ]
        result = network_map()
        assert result["maps_count"] == 1
        assert result["total_mirrors"] == 1
        assert result["repos"][0]["repo"] == "test-repo"

    @patch("organvm_mcp.tools.network._load_maps")
    def test_network_map_single_repo(self, mock_maps):
        from organvm_engine.network.schema import MirrorEntry, NetworkMap

        from organvm_mcp.tools.network import network_map

        nmap = NetworkMap(
            schema_version="1.0", repo="target", organ="META",
            technical=[MirrorEntry(
                project="x/y", platform="github", relevance="dep",
            )],
        )
        mock_maps.return_value = [nmap]
        result = network_map(repo="target")
        assert result["repo"] == "target"
        assert "mirrors" in result

    @patch("organvm_mcp.tools.network._load_maps")
    def test_network_map_not_found(self, mock_maps):
        from organvm_mcp.tools.network import network_map

        mock_maps.return_value = []
        result = network_map(repo="nonexistent")
        assert "error" in result

    @patch("organvm_mcp.tools.network._load_maps")
    @patch("organvm_mcp.tools.network._count_active")
    def test_network_status(self, mock_active, mock_maps):
        from organvm_engine.network.schema import MirrorEntry, NetworkMap

        from organvm_mcp.tools.network import network_status

        mock_active.return_value = 10
        mock_maps.return_value = [
            NetworkMap(
                schema_version="1.0", repo="a", organ="X",
                technical=[MirrorEntry(
                    project="x/y", platform="github", relevance="dep",
                )],
            ),
        ]
        result = network_status()
        assert "density" in result
        assert "coverage" in result
        assert result["maps_count"] == 1

    @patch("organvm_mcp.tools.network._load_maps")
    def test_network_suggest_empty(self, mock_maps):
        from organvm_mcp.tools.network import network_suggest

        mock_maps.return_value = []
        result = network_suggest()
        assert "suggestions" in result

    def test_network_log(self, tmp_path):
        from organvm_mcp.tools.network import network_log

        with patch(
            "organvm_engine.network.ledger.DEFAULT_LEDGER_PATH",
            tmp_path / "test-ledger.jsonl",
        ):
            result = network_log(
                organvm_repo="test-repo",
                external_project="x/y",
                lens="technical",
                action_type="contribution",
                detail="Filed issue #1",
            )
            assert result["status"] == "logged"
            assert result["repo"] == "test-repo"

    @patch("organvm_mcp.tools.network._load_maps")
    def test_network_convergences(self, mock_maps):
        from organvm_engine.network.schema import MirrorEntry, NetworkMap

        from organvm_mcp.tools.network import network_convergences

        mock_maps.return_value = [
            NetworkMap(
                schema_version="1.0", repo="a", organ="X",
                technical=[MirrorEntry(
                    project="shared/p", platform="github", relevance="dep",
                )],
            ),
            NetworkMap(
                schema_version="1.0", repo="b", organ="X",
                technical=[MirrorEntry(
                    project="shared/p", platform="github", relevance="dep",
                )],
            ),
        ]
        result = network_convergences()
        assert result["total"] == 1
        assert result["convergences"][0]["project"] == "shared/p"
