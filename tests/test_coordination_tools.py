"""Tests for coordination tools (punch-in/punch-out)."""

from __future__ import annotations

import pytest

from organvm_mcp.tools import coordination


@pytest.fixture(autouse=True)
def isolated_claims(tmp_path, monkeypatch):
    """Route claims to temp file."""
    monkeypatch.setenv("ORGANVM_CLAIMS_FILE", str(tmp_path / "claims.jsonl"))


class TestPunchIn:
    def test_returns_claim_id(self):
        res = coordination.coordination_punch_in(
            agent="claude", session_id="test-1",
            organs=["ORGAN-I"], scope="theory work",
        )
        assert "claim_id" in res
        assert res["conflict_count"] == 0
        assert "organ:ORGAN-I" in res["areas"]

    def test_detects_conflicts(self):
        coordination.coordination_punch_in(
            agent="claude", session_id="s1",
            repos=["organvm-engine"],
        )
        res = coordination.coordination_punch_in(
            agent="gemini", session_id="s2",
            repos=["organvm-engine"],
        )
        assert res["conflict_count"] == 1


class TestPunchOut:
    def test_release(self):
        r = coordination.coordination_punch_in(
            agent="claude", session_id="s1", organs=["ORGAN-I"],
        )
        res = coordination.coordination_punch_out(r["claim_id"])
        assert res["released"] is True

    def test_invalid_id(self):
        res = coordination.coordination_punch_out("nonexistent")
        assert "error" in res


class TestWorkBoard:
    def test_empty_board(self):
        res = coordination.coordination_work_board()
        assert res["active_claims"] == 0

    def test_board_shows_claims(self):
        coordination.coordination_punch_in(
            agent="claude", session_id="s1",
            organs=["ORGAN-I"], scope="test",
        )
        res = coordination.coordination_work_board()
        assert res["active_claims"] == 1
        assert "claude" in res["by_agent"]


class TestCheckConflicts:
    def test_no_conflicts(self):
        res = coordination.coordination_check_conflicts(organs=["ORGAN-I"])
        assert res["conflict_count"] == 0

    def test_detects_conflict(self):
        coordination.coordination_punch_in(
            agent="claude", session_id="s1",
            modules=["governance"],
        )
        res = coordination.coordination_check_conflicts(modules=["governance"])
        assert res["conflict_count"] == 1
        assert res["conflicts"][0]["overlap_type"] == "module"


class TestCapacity:
    def test_empty_capacity(self):
        res = coordination.coordination_capacity()
        assert res["current_load"] == 0
        assert res["at_capacity"] is False

    def test_capacity_after_punch_in(self):
        coordination.coordination_punch_in(
            agent="claude", session_id="s1",
            resource_weight="heavy",
        )
        res = coordination.coordination_capacity()
        assert res["current_load"] == 3
        assert res["active_streams"] == 1

    def test_resource_weight_in_punch_in(self):
        res = coordination.coordination_punch_in(
            agent="claude", session_id="s1",
            resource_weight="light",
        )
        assert res["resource_weight"] == "light"
        assert res["cost"] == 1


class TestHandles:
    def test_punch_in_returns_handle(self):
        res = coordination.coordination_punch_in(
            agent="claude", session_id="s1",
            organs=["ORGAN-I"],
        )
        assert "handle" in res
        assert res["handle"].startswith("claude-")

    def test_handles_unique(self):
        r1 = coordination.coordination_punch_in(
            agent="claude", session_id="s1", organs=["ORGAN-I"],
        )
        r2 = coordination.coordination_punch_in(
            agent="claude", session_id="s2", organs=["ORGAN-II"],
        )
        assert r1["handle"] != r2["handle"]

    def test_handle_in_work_board(self):
        coordination.coordination_punch_in(
            agent="claude", session_id="s1",
            organs=["ORGAN-I"], scope="test",
        )
        res = coordination.coordination_work_board()
        claims = res["by_agent"]["claude"]
        assert claims[0]["handle"].startswith("claude-")


class TestTestObligationsMCP:
    def test_punch_in_with_obligations(self):
        res = coordination.coordination_punch_in(
            agent="claude", session_id="s1",
            repos=["engine"],
            test_obligations=["pytest engine/tests/ -v"],
        )
        assert "claim_id" in res

    def test_obligations_in_work_board(self):
        coordination.coordination_punch_in(
            agent="claude", session_id="s1",
            test_obligations=["pytest tests/ -v"],
        )
        res = coordination.coordination_work_board()
        assert res["test_obligation_count"] >= 1


class TestProveSweepMCP:
    def test_empty_sweep(self):
        res = coordination.coordination_prove_sweep()
        assert res["total"] == 0

    def test_sweep_with_obligations(self):
        coordination.coordination_punch_in(
            agent="claude", session_id="s1",
            test_obligations=["pytest engine/ -v", "ruff check src/"],
        )
        res = coordination.coordination_prove_sweep()
        assert res["total"] == 2
        assert "pytest engine/ -v" in res["obligations"]


class TestToolCheckoutMCP:
    def test_light_clears(self):
        res = coordination.coordination_tool_checkout(
            handle="claude-forge",
            command_hint="git status",
        )
        assert res["cleared"] is True

    def test_heavy_clears_when_empty(self):
        res = coordination.coordination_tool_checkout(
            handle="claude-forge",
            command_hint="pytest tests/ -v",
        )
        assert res["cleared"] is True
        assert res["checkout_id"] != ""

    def test_heavy_blocks_second(self):
        coordination.coordination_tool_checkout(
            handle="claude-forge",
            command_hint="pytest engine/ -v",
        )
        res = coordination.coordination_tool_checkout(
            handle="gemini-scout",
            command_hint="pytest mcp/ -v",
        )
        assert res["cleared"] is False
        assert res["wait"] is True


class TestToolCheckinMCP:
    def test_checkin_releases(self):
        co = coordination.coordination_tool_checkout(
            handle="claude-forge",
            command_hint="pytest tests/ -v",
        )
        res = coordination.coordination_tool_checkin(co["checkout_id"])
        assert res["released"] is True


class TestToolQueueMCP:
    def test_empty_queue(self):
        res = coordination.coordination_tool_queue()
        assert res["active_checkouts"] == 0

    def test_queue_shows_active(self):
        coordination.coordination_tool_checkout(
            handle="claude-forge",
            command_hint="pytest tests/ -v",
        )
        res = coordination.coordination_tool_queue()
        assert res["active_checkouts"] == 1
        assert res["heavy_lane"]["occupied"] == 1
