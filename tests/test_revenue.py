"""Tests for revenue tools."""

from __future__ import annotations

from datetime import date
from unittest.mock import patch

import pytest

from organvm_mcp.tools import revenue


@pytest.fixture
def mock_registry_data():
    return {
        "organs": {
            "ORGAN-III": {
                "name": "Ergon",
                "organization": "labores-profani-crux",
                "repositories": [
                    {
                        "name": "product-a",
                        "tier": "flagship",
                        "promotion_status": "GRADUATED",
                        "implementation_status": "ACTIVE",
                        "revenue_model": "SaaS",
                        "revenue_status": "live",
                        "ci_workflow": True,
                        "dependencies": [],
                    },
                    {
                        "name": "product-b",
                        "tier": "standard",
                        "promotion_status": "CANDIDATE",
                        "implementation_status": "ACTIVE",
                        "revenue_model": "freemium",
                        "revenue_status": "pre-launch",
                        "ci_workflow": False,
                        "dependencies": [],
                    },
                ],
            },
            "ORGAN-I": {
                "name": "Theory",
                "organization": "ivviiviivvi",
                "repositories": [],
            },
        },
    }


class TestRevenuePipeline:
    @patch("organvm_engine.deadlines.parser.filter_upcoming")
    @patch("organvm_engine.deadlines.parser.parse_deadlines")
    @patch("organvm_mcp.data.loader.load_registry")
    def test_pipeline_structure(self, mock_reg, mock_parse, mock_filter, mock_registry_data):
        mock_reg.return_value = mock_registry_data
        mock_parse.return_value = []
        mock_filter.return_value = []
        res = revenue.revenue_pipeline()
        assert "layers" in res
        assert res["layers"]["products"]["total"] == 2
        assert res["layers"]["products"]["live"] == 1

    @patch("organvm_engine.deadlines.parser.filter_upcoming")
    @patch("organvm_engine.deadlines.parser.parse_deadlines")
    @patch("organvm_mcp.data.loader.load_registry")
    def test_pipeline_products(self, mock_reg, mock_parse, mock_filter, mock_registry_data):
        mock_reg.return_value = mock_registry_data
        mock_parse.return_value = []
        mock_filter.return_value = []
        res = revenue.revenue_pipeline()
        assert len(res["products"]) == 2
        assert res["products"][0]["name"] == "product-a"


class TestRevenueProducts:
    @patch("organvm_mcp.data.loader.load_registry")
    def test_products_list(self, mock_reg, mock_registry_data):
        mock_reg.return_value = mock_registry_data
        res = revenue.revenue_products()
        assert res["total"] == 2
        assert "by_revenue_model" in res
        assert res["by_revenue_model"]["SaaS"] == 1


class TestRevenueReadiness:
    @patch("organvm_mcp.data.loader.load_registry")
    def test_readiness_live_product(self, mock_reg, mock_registry_data):
        mock_reg.return_value = mock_registry_data
        res = revenue.revenue_readiness("product-a")
        assert res["repo"] == "product-a"
        assert res["blocker_count"] == 0

    @patch("organvm_mcp.data.loader.load_registry")
    def test_readiness_not_found(self, mock_reg, mock_registry_data):
        mock_reg.return_value = mock_registry_data
        res = revenue.revenue_readiness("nonexistent")
        assert "error" in res

    @patch("organvm_mcp.data.loader.load_registry")
    def test_readiness_with_blockers(self, mock_reg, mock_registry_data):
        mock_reg.return_value = mock_registry_data
        res = revenue.revenue_readiness("product-b")
        assert res["blocker_count"] >= 1
        assert "No CI workflow" in res["blockers"][0]


class TestRevenueGrants:
    @patch("organvm_engine.deadlines.parser.filter_upcoming")
    @patch("organvm_engine.deadlines.parser.parse_deadlines")
    def test_grants_filter(self, mock_parse, mock_filter):
        from organvm_engine.deadlines.parser import Deadline

        funding = Deadline(
            item_id="F4", description="NEH Grant", deadline_date=date(2026, 5, 1),
        )
        non_funding = Deadline(
            item_id="E3", description="Google Creative", deadline_date=date(2026, 5, 15),
        )
        mock_parse.return_value = [funding, non_funding]
        mock_filter.return_value = [funding, non_funding]
        res = revenue.revenue_grants(days=90)
        assert res["total"] == 1
        assert res["grants"][0]["item_id"] == "F4"


class TestParseConsultingManifest:
    def test_parses_table_from_fixture(self, tmp_path):
        manifest = tmp_path / "consulting-services-manifest.md"
        manifest.write_text(
            "## Layer 2: Consulting Packages\n\n"
            "| Package | SOP Asset | Essay Asset | Target Client "
            "| Deliverable | Temporal Lens |\n"
            "|---------|-----------|-------------|---------------"
            "|-------------|---------------|\n"
            "| **Alpha Service** | SOP--alpha-check | 09 (Essay) "
            "| Startups | Report | NOW: ready |\n"
            "| **Beta Framework** | SOP--beta-framework + METADOC--beta-guide "
            "| 31 (Org) | Enterprise | Blueprint | FUTURE: needs work |\n",
        )
        packages = revenue._parse_consulting_manifest(manifest)
        assert len(packages) == 2
        assert packages[0]["name"] == "Alpha Service"
        assert packages[0]["sop_refs"] == ["SOP--alpha-check.md"]
        assert packages[1]["name"] == "Beta Framework"
        assert "SOP--beta-framework.md" in packages[1]["sop_refs"]
        assert "METADOC--beta-guide.md" in packages[1]["sop_refs"]
        assert packages[0]["temporal_lens"] == "NOW: ready"

    def test_missing_manifest(self, tmp_path):
        packages = revenue._parse_consulting_manifest(
            tmp_path / "nonexistent.md",
        )
        assert packages == []


class TestRevenueConsulting:
    @patch("organvm_engine.sop.discover.discover_sops")
    @patch("organvm_mcp.tools.revenue._parse_consulting_manifest")
    def test_consulting_with_sop_verification(self, mock_parse, mock_discover):
        from pathlib import Path

        from organvm_engine.sop.discover import SOPEntry

        mock_parse.return_value = [
            {
                "name": "Stranger Test Protocol",
                "sop_asset": "SOP--stranger-test-protocol",
                "sop_refs": ["SOP--stranger-test-protocol.md"],
                "essay_asset": "35 (Stranger Test)",
                "target_client": "OSS projects",
                "deliverable": "Legibility score",
                "temporal_lens": "NOW",
            },
            {
                "name": "Orchestration Architecture",
                "sop_asset": "Conductor framework",
                "sop_refs": [],
                "essay_asset": "09",
                "target_client": "Companies",
                "deliverable": "Fleet management",
                "temporal_lens": "FUTURE",
            },
        ]
        mock_discover.return_value = [
            SOPEntry(
                path=Path("/tmp/SOP--stranger-test-protocol.md"),
                org="meta",
                repo="praxis",
                filename="SOP--stranger-test-protocol.md",
                title="Stranger Test",
                doc_type="SOP",
                canonical=True,
                has_canonical_header=False,
            ),
        ]
        res = revenue.revenue_consulting()
        assert res["total"] == 2
        # Stranger Test has its SOP → ready
        stranger = next(
            p for p in res["packages"]
            if p["name"] == "Stranger Test Protocol"
        )
        assert stranger["ready"] is True
        # Orchestration has no SOP refs → not ready
        orch = next(
            p for p in res["packages"]
            if p["name"] == "Orchestration Architecture"
        )
        assert orch["ready"] is False

    @patch("organvm_mcp.tools.revenue._parse_consulting_manifest")
    def test_consulting_empty_manifest(self, mock_parse):
        mock_parse.return_value = []
        res = revenue.revenue_consulting()
        assert "error" in res
        assert res["total"] == 0
