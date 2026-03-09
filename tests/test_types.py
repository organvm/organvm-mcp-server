"""Tests for MCP server shared types."""

from __future__ import annotations

from organvm_mcp.types import (
    DependencyNode,
    EventContract,
    HealthReport,
    OrganSummary,
    PromotionStatus,
    RepoContext,
    RepoInfo,
    SeedEdge,
    Tier,
)


class TestEnums:
    def test_promotion_status_values(self):
        values = {s.value for s in PromotionStatus}
        assert values == {"LOCAL", "CANDIDATE", "PUBLIC_PROCESS", "GRADUATED", "ARCHIVED"}

    def test_promotion_status_count(self):
        assert len(PromotionStatus) == 5

    def test_tier_values(self):
        values = {t.value for t in Tier}
        assert values == {"flagship", "standard", "infrastructure", "archive", "personal"}

    def test_tier_count(self):
        assert len(Tier) == 5

    def test_enum_member_access(self):
        assert PromotionStatus.LOCAL.value == "LOCAL"
        assert Tier.FLAGSHIP.value == "flagship"


class TestRepoInfo:
    def test_required_fields(self):
        ri = RepoInfo(
            name="test-repo",
            org="meta-organvm",
            organ="META-ORGANVM",
            tier="flagship",
            promotion_status="CANDIDATE",
            documentation_status="COMPLETE",
        )
        assert ri.name == "test-repo"
        assert ri.org == "meta-organvm"
        assert ri.organ == "META-ORGANVM"
        assert ri.tier == "flagship"
        assert ri.promotion_status == "CANDIDATE"
        assert ri.documentation_status == "COMPLETE"

    def test_default_fields(self):
        ri = RepoInfo(
            name="x",
            org="o",
            organ="O",
            tier="t",
            promotion_status="LOCAL",
            documentation_status="NONE",
        )
        assert ri.description == ""
        assert ri.dependencies == []
        assert ri.url == ""

    def test_dependencies_default_not_shared(self):
        ri1 = RepoInfo(
            name="a",
            org="o",
            organ="O",
            tier="t",
            promotion_status="LOCAL",
            documentation_status="NONE",
        )
        ri2 = RepoInfo(
            name="b",
            org="o",
            organ="O",
            tier="t",
            promotion_status="LOCAL",
            documentation_status="NONE",
        )
        ri1.dependencies.append("dep")
        assert ri2.dependencies == []


class TestOrganSummary:
    def test_fields(self):
        os_ = OrganSummary(
            key="ORGAN-I",
            name="Theory",
            org="ivviiviivvi",
            repo_count=5,
            flagship_count=1,
            standard_count=3,
            infrastructure_count=1,
        )
        assert os_.key == "ORGAN-I"
        assert os_.repo_count == 5
        assert os_.produces == []
        assert os_.consumes == []

    def test_produces_consumes_default_not_shared(self):
        a = OrganSummary(
            key="A",
            name="A",
            org="a",
            repo_count=0,
            flagship_count=0,
            standard_count=0,
            infrastructure_count=0,
        )
        b = OrganSummary(
            key="B",
            name="B",
            org="b",
            repo_count=0,
            flagship_count=0,
            standard_count=0,
            infrastructure_count=0,
        )
        a.produces.append("x")
        assert b.produces == []


class TestSeedEdge:
    def test_fields(self):
        se = SeedEdge(
            source_repo="engine",
            source_organ="META-ORGANVM",
            target_repo="dashboard",
            target_organ="META-ORGANVM",
            artifact="registry-v2.json",
        )
        assert se.source_repo == "engine"
        assert se.artifact == "registry-v2.json"
        assert se.event_type == ""

    def test_with_event_type(self):
        se = SeedEdge(
            source_repo="a",
            source_organ="I",
            target_repo="b",
            target_organ="II",
            artifact="schemas",
            event_type="schema.updated",
        )
        assert se.event_type == "schema.updated"


class TestEventContract:
    def test_fields(self):
        ec = EventContract(
            event_type="repo.promoted",
            edge="ORGAN-I -> ORGAN-II",
            producer_organ="ORGAN-I",
            consumer_organ="ORGAN-II",
            producer_workflow="promote.yml",
            consumer_workflow="on-promote.yml",
        )
        assert ec.event_type == "repo.promoted"
        assert ec.description == ""
        assert ec.payload_fields == []


class TestDependencyNode:
    def test_fields(self):
        dn = DependencyNode(repo="engine", organ="META-ORGANVM")
        assert dn.depends_on == []
        assert dn.depended_by == []


class TestHealthReport:
    def test_fields(self):
        hr = HealthReport(
            total_repos=100,
            active_repos=90,
            archived_repos=10,
            repos_with_ci=50,
            repos_with_tests=40,
            seed_coverage=0.95,
            omega_criteria_met=4,
            omega_criteria_total=17,
            soak_test_running=True,
            soak_test_days_remaining=15,
        )
        assert hr.total_repos == 100
        assert hr.active_repos == 90
        assert hr.seed_coverage == 0.95
        assert hr.soak_test_running is True
        assert hr.soak_test_days_remaining == 15


class TestRepoContext:
    def test_fields(self):
        ri = RepoInfo(
            name="r",
            org="o",
            organ="O",
            tier="t",
            promotion_status="LOCAL",
            documentation_status="NONE",
        )
        os_ = OrganSummary(
            key="O",
            name="O",
            org="o",
            repo_count=1,
            flagship_count=0,
            standard_count=1,
            infrastructure_count=0,
        )
        rc = RepoContext(
            repo=ri,
            organ_summary=os_,
            produces=[],
            consumes=[],
            siblings=["sibling-repo"],
            upstream_organs=["ORGAN-I"],
            downstream_organs=["ORGAN-III"],
        )
        assert rc.siblings == ["sibling-repo"]
        assert rc.governance_notes == []
