"""Tests for content pipeline MCP tools."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from organvm_mcp.tools.content import content_list, content_signals, content_status


@dataclass
class FakePost:
    slug: str
    title: str
    date: str
    hook: str = ""
    status: str = "draft"
    source_session: str = ""
    context: str = ""
    tags: list[str] = field(default_factory=list)
    distribution: dict[str, Any] = field(default_factory=dict)
    engagement: dict[str, Any] = field(default_factory=dict)
    redacted_items: list[str] = field(default_factory=list)
    directory: Path = field(default_factory=lambda: Path("/tmp/fake"))


@pytest.fixture
def sample_posts():
    return [
        FakePost(
            slug="automation-essay",
            title="Why Automation Matters",
            date="2026-03-18",
            status="published",
            tags=["automation", "ethics"],
            distribution={"linkedin": {"posted": True}},
        ),
        FakePost(
            slug="organ-deep-dive",
            title="The Eight Organs",
            date="2026-03-15",
            status="draft",
            tags=["architecture"],
        ),
        FakePost(
            slug="old-post",
            title="An Old Post",
            date="2026-02-01",
            status="archived",
            tags=["ethics"],
        ),
    ]


class TestContentList:
    def test_list_all(self, sample_posts):
        with (
            patch(
                "organvm_mcp.tools.content.discover_posts",
                return_value=sample_posts,
            ),
            patch(
                "organvm_mcp.tools.content.filter_posts",
                return_value=sample_posts,
            ),
        ):
            result = content_list()
            assert result["total_posts"] == 3
            assert result["filtered_count"] == 3
            assert len(result["posts"]) == 3
            assert result["posts"][0]["slug"] == "automation-essay"

    def test_list_with_status_filter(self, sample_posts):
        published = [p for p in sample_posts if p.status == "published"]
        with (
            patch(
                "organvm_mcp.tools.content.discover_posts",
                return_value=sample_posts,
            ),
            patch(
                "organvm_mcp.tools.content.filter_posts",
                return_value=published,
            ),
        ):
            result = content_list(status="published")
            assert result["total_posts"] == 3
            assert result["filtered_count"] == 1
            assert result["filters"]["status"] == "published"

    def test_list_with_tag_filter(self, sample_posts):
        ethics = [p for p in sample_posts if "ethics" in p.tags]
        with (
            patch(
                "organvm_mcp.tools.content.discover_posts",
                return_value=sample_posts,
            ),
            patch(
                "organvm_mcp.tools.content.filter_posts",
                return_value=ethics,
            ),
        ):
            result = content_list(tag="ethics")
            assert result["filtered_count"] == 2
            assert result["filters"]["tag"] == "ethics"

    def test_list_empty(self):
        with (
            patch(
                "organvm_mcp.tools.content.discover_posts",
                return_value=[],
            ),
            patch(
                "organvm_mcp.tools.content.filter_posts",
                return_value=[],
            ),
        ):
            result = content_list()
            assert result["total_posts"] == 0
            assert result["posts"] == []

    def test_list_includes_distribution(self, sample_posts):
        with (
            patch(
                "organvm_mcp.tools.content.discover_posts",
                return_value=sample_posts,
            ),
            patch(
                "organvm_mcp.tools.content.filter_posts",
                return_value=sample_posts,
            ),
        ):
            result = content_list()
            first = result["posts"][0]
            assert "distribution" in first
            assert first["distribution"]["linkedin"]["posted"] is True


class TestContentStatus:
    def test_status_report(self, sample_posts):
        from organvm_engine.content.cadence import CadenceReport

        report = CadenceReport(
            posts_this_week=[sample_posts[0]],
            weeks_since_last_post=0,
            streak=2,
            total_posts=3,
            published_count=1,
            draft_count=1,
            archived_count=1,
            last_post_date="2026-03-18",
        )
        with (
            patch(
                "organvm_mcp.tools.content.discover_posts",
                return_value=sample_posts,
            ),
            patch(
                "organvm_mcp.tools.content.check_cadence",
                return_value=report,
            ),
        ):
            result = content_status()
            assert result["total_posts"] == 3
            assert result["published_count"] == 1
            assert result["streak"] == 2
            assert result["last_post_date"] == "2026-03-18"
            assert len(result["posts_this_week"]) == 1
            assert result["posts_this_week"][0]["slug"] == "automation-essay"

    def test_status_empty(self):
        from organvm_engine.content.cadence import CadenceReport

        with (
            patch(
                "organvm_mcp.tools.content.discover_posts",
                return_value=[],
            ),
            patch(
                "organvm_mcp.tools.content.check_cadence",
                return_value=CadenceReport(),
            ),
        ):
            result = content_status()
            assert result["total_posts"] == 0
            assert result["streak"] == 0
            assert result["posts_this_week"] == []


class TestContentSignals:
    def test_detect_signals(self):
        messages = [
            "I feel like this is what matters most to me.",
            "Fix the CI pipeline.",
            "ORGAN-I and ORGAN-III are the foundation of everything.",
        ]
        result = content_signals(messages)
        assert result["message_count"] == 3
        assert result["signal_count"] > 0
        # Should detect emotional_resonance and architectural_connection
        types = {s["signal_type"] for s in result["signals"]}
        assert "emotional_resonance" in types
        assert "architectural_connection" in types

    def test_detect_no_signals(self):
        messages = ["Fix bug.", "Run tests."]
        result = content_signals(messages)
        assert result["message_count"] == 2
        assert result["signal_count"] == 0
        assert result["signals"] == []

    def test_empty_messages(self):
        result = content_signals([])
        assert result["message_count"] == 0
        assert result["signal_count"] == 0

    def test_signal_fields(self):
        messages = [
            "I realized that this is what I've been thinking about. I feel strongly.",
        ]
        result = content_signals(messages)
        assert result["signal_count"] > 0
        signal = result["signals"][0]
        assert "prompt_index" in signal
        assert "signal_type" in signal
        assert "description" in signal
        assert "excerpt" in signal
        assert "strength" in signal
