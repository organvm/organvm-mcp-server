"""Tests for session intelligence tools."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from organvm_mcp.tools import sessions


def _make_session(agent="claude", sid="abc123", project="/test"):
    from organvm_engine.session.agents import AgentSession

    return AgentSession(
        agent=agent,
        session_id=sid,
        file_path=Path(f"/tmp/{sid}.jsonl"),
        project_dir=project,
        started=datetime(2026, 3, 1, 10, 0),
        ended=datetime(2026, 3, 1, 11, 0),
        size_bytes=1024,
    )


class TestSessionAgents:
    @patch("organvm_engine.session.agents.agent_summary")
    def test_returns_summary(self, mock_summary):
        mock_summary.return_value = {
            "claude": {"count": 10, "size_bytes": 1000},
            "gemini": {"count": 5, "size_bytes": 500},
        }
        res = sessions.session_agents()
        assert "claude" in res
        assert res["claude"]["count"] == 10


class TestSessionList:
    @patch("organvm_engine.session.agents.discover_all_sessions")
    def test_returns_sessions(self, mock_discover):
        mock_discover.return_value = [_make_session()]
        res = sessions.session_list()
        assert res["total"] == 1
        assert res["shown"] == 1
        assert res["sessions"][0]["agent"] == "claude"

    @patch("organvm_engine.session.agents.discover_all_sessions")
    def test_respects_limit(self, mock_discover):
        mock_discover.return_value = [_make_session(sid=f"s{i}") for i in range(30)]
        res = sessions.session_list(limit=5)
        assert res["total"] == 30
        assert res["shown"] == 5
        assert res["limit"] == 5

    @patch("organvm_engine.session.agents.discover_all_sessions")
    def test_passes_filters(self, mock_discover):
        mock_discover.return_value = []
        sessions.session_list(agent="gemini", project_filter="meta")
        mock_discover.assert_called_once_with(agent="gemini", project_filter="meta")


class TestSessionPlans:
    @patch("organvm_engine.session.plans.discover_plans")
    def test_returns_plans(self, mock_discover):
        from organvm_engine.session.plans import PlanFile

        mock_discover.return_value = [
            PlanFile(
                path=Path("/tmp/2026-03-01-test.md"),
                project="meta-organvm/organvm-engine",
                slug="test",
                date="2026-03-01",
                title="Test Plan",
                size_bytes=2048,
                has_verification=True,
            ),
        ]
        res = sessions.session_plans()
        assert res["total"] == 1
        assert res["plans"][0]["title"] == "Test Plan"
        assert res["by_project"]["meta-organvm/organvm-engine"] == 1


class TestSessionAnalyzePrompts:
    @patch("organvm_engine.session.analysis.analyze_prompts")
    def test_returns_stats(self, mock_analyze):
        from organvm_engine.session.analysis import PromptStats

        mock_analyze.return_value = PromptStats(
            total_sessions=50,
            total_prompts=200,
            total_chars=10000,
            avg_prompt_length=50,
        )
        res = sessions.session_analyze_prompts()
        assert res["total_sessions"] == 50
        assert res["total_prompts"] == 200
