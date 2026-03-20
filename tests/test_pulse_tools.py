"""Tests for pulse MCP tools."""

from __future__ import annotations

from dataclasses import dataclass, field
from unittest.mock import MagicMock, patch

import pytest

from organvm_mcp.tools.pulse import (
    _compute_velocity_factors,
    pulse_briefing,
    pulse_density,
    pulse_emit,
    pulse_events,
    pulse_flow,
    pulse_memory,
    pulse_mood,
    pulse_nerve,
    pulse_record_insight,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@dataclass
class _FakeGate:
    name: str = "SEED"
    passed: bool = True
    rate: float = 80.0


@dataclass
class _FakeRepo:
    name: str = "test-repo"
    promo: str = "CANDIDATE"
    gates: list = field(default_factory=lambda: [_FakeGate()])


@dataclass
class _FakeGateStat:
    name: str = "SEED"
    rate: float = 80.0


@dataclass
class _FakeOrganism:
    total_repos: int = 10
    sys_pct: int = 50
    total_stale: int = 2
    total_promo_ready: int = 3
    all_repos: list = field(default_factory=lambda: [_FakeRepo()])

    def gate_stats(self):
        return [_FakeGateStat()]


@dataclass
class _FakeDensity:
    interconnection_score: float = 55.0

    def to_dict(self):
        return {
            "declared_edges": 10,
            "possible_edges": 100,
            "edge_saturation": 0.1,
            "interconnection_score": self.interconnection_score,
        }


@dataclass
class _FakeSeedGraph:
    nodes: list = field(default_factory=lambda: ["org/a", "org/b"])
    edges: list = field(default_factory=lambda: [("org/a", "org/b", "produces")])


@dataclass
class _FakeMoodReading:
    def to_dict(self):
        return {
            "mood": "steady",
            "glyph": "o",
            "description": "Stable",
            "factors": {},
            "reasoning": ["No significant signals"],
        }


@dataclass
class _FakeEvent:
    event_type: str = "repo.promoted"
    source: str = "cli"
    payload: dict = field(default_factory=dict)
    timestamp: str = "2026-03-13T00:00:00+00:00"


@dataclass
class _FakeSubscription:
    subscriber: str = "org/repo"
    event_type: str = "repo.promoted"
    source: str = ""
    action: str = "notify"

    def to_dict(self):
        return {
            "subscriber": self.subscriber,
            "event_type": self.event_type,
            "source": self.source,
            "action": self.action,
        }


@dataclass
class _FakeNerveBundle:
    subscriptions: list = field(default_factory=list)
    by_event: dict = field(default_factory=dict)
    by_subscriber: dict = field(default_factory=dict)

    def listeners_for(self, event_type):
        return self.by_event.get(event_type, [])

    def to_dict(self):
        return {"total": len(self.subscriptions), "by_event": {}, "by_subscriber": {}}


@pytest.fixture(autouse=True)
def isolated_events(tmp_path, monkeypatch):
    """Route pulse events to a temp directory."""
    monkeypatch.setenv("HOME", str(tmp_path))


# ---------------------------------------------------------------------------
# Tests: pulse_mood
# ---------------------------------------------------------------------------

class TestPulseMood:
    def test_returns_dict(self):
        result = _call_mood_patched()
        assert isinstance(result, dict)
        assert "mood" in result

    def test_mood_has_reasoning(self):
        result = _call_mood_patched()
        assert "reasoning" in result


def _call_mood_patched() -> dict:
    """Helper to call pulse_mood with all engine imports mocked."""
    organism = _FakeOrganism()
    graph = _FakeSeedGraph()
    density = _FakeDensity()
    mood = _FakeMoodReading()

    with (
        patch(
            "organvm_engine.metrics.organism.get_organism",
            return_value=organism,
        ),
        patch(
            "organvm_engine.seed.graph.build_seed_graph",
            return_value=graph,
        ),
        patch(
            "organvm_engine.seed.graph.validate_edge_resolution",
            return_value=[],
        ),
        patch(
            "organvm_engine.pulse.density.compute_density",
            return_value=density,
        ),
        patch(
            "organvm_engine.pulse.affective.compute_mood",
            return_value=mood,
        ),
    ):
        return pulse_mood()


# ---------------------------------------------------------------------------
# Tests: pulse_density
# ---------------------------------------------------------------------------

class TestPulseDensity:
    def test_returns_dict(self):
        result = _call_density_patched()
        assert isinstance(result, dict)
        assert "interconnection_score" in result

    def test_has_edge_metrics(self):
        result = _call_density_patched()
        assert "declared_edges" in result


def _call_density_patched() -> dict:
    """Helper to call pulse_density with all engine imports mocked."""
    organism = _FakeOrganism()
    graph = _FakeSeedGraph()
    density = _FakeDensity()

    with (
        patch(
            "organvm_engine.metrics.organism.get_organism",
            return_value=organism,
        ),
        patch(
            "organvm_engine.seed.graph.build_seed_graph",
            return_value=graph,
        ),
        patch(
            "organvm_engine.seed.graph.validate_edge_resolution",
            return_value=[],
        ),
        patch(
            "organvm_engine.pulse.density.compute_density",
            return_value=density,
        ),
    ):
        return pulse_density()


# ---------------------------------------------------------------------------
# Tests: pulse_events
# ---------------------------------------------------------------------------

class TestPulseEvents:
    def test_returns_dict(self):
        fake_events = [_FakeEvent()]
        with (
            patch(
                "organvm_engine.pulse.events.replay",
                return_value=fake_events,
            ),
            patch(
                "organvm_engine.pulse.events.event_counts",
                return_value={"repo.promoted": 1},
            ),
        ):
            result = pulse_events()
            assert isinstance(result, dict)
            assert result["total_shown"] == 1

    def test_empty_events(self):
        with (
            patch("organvm_engine.pulse.events.replay", return_value=[]),
            patch("organvm_engine.pulse.events.event_counts", return_value={}),
        ):
            result = pulse_events()
            assert result["total_shown"] == 0
            assert result["events"] == []

    def test_filter_by_type(self):
        with (
            patch("organvm_engine.pulse.events.replay", return_value=[]) as mock_replay,
            patch("organvm_engine.pulse.events.event_counts", return_value={}),
        ):
            pulse_events(event_type="repo.promoted", limit=5)
            mock_replay.assert_called_once_with(event_type="repo.promoted", limit=5)


# ---------------------------------------------------------------------------
# Tests: pulse_nerve
# ---------------------------------------------------------------------------

class TestPulseNerve:
    def test_returns_bundle_dict(self):
        bundle = _FakeNerveBundle(subscriptions=[_FakeSubscription()])
        with patch(
            "organvm_engine.pulse.nerve.resolve_subscriptions",
            return_value=bundle,
        ):
            result = pulse_nerve()
            assert isinstance(result, dict)
            assert "total" in result

    def test_filter_by_event_type(self):
        sub = _FakeSubscription()
        bundle = _FakeNerveBundle(
            subscriptions=[sub],
            by_event={"repo.promoted": [sub]},
        )
        with patch(
            "organvm_engine.pulse.nerve.resolve_subscriptions",
            return_value=bundle,
        ):
            result = pulse_nerve(event_type="repo.promoted")
            assert result["event_type"] == "repo.promoted"
            assert result["listener_count"] == 1

    def test_filter_no_match(self):
        bundle = _FakeNerveBundle()
        with patch(
            "organvm_engine.pulse.nerve.resolve_subscriptions",
            return_value=bundle,
        ):
            result = pulse_nerve(event_type="nonexistent")
            assert result["listener_count"] == 0


# ---------------------------------------------------------------------------
# Tests: pulse_emit
# ---------------------------------------------------------------------------

class TestPulseEmit:
    def test_returns_emitted(self):
        event = _FakeEvent()
        bundle = _FakeNerveBundle()
        with (
            patch("organvm_engine.pulse.events.emit", return_value=event),
            patch(
                "organvm_engine.pulse.nerve.resolve_subscriptions",
                return_value=bundle,
            ),
            patch("organvm_engine.pulse.nerve.propagate", return_value=[]),
        ):
            result = pulse_emit(event_type="repo.promoted")
            assert isinstance(result, dict)
            assert "emitted" in result
            assert result["notified_count"] == 0

    def test_with_payload(self):
        event = _FakeEvent(payload={"repo": "test"})
        bundle = _FakeNerveBundle()
        with (
            patch("organvm_engine.pulse.events.emit", return_value=event),
            patch(
                "organvm_engine.pulse.nerve.resolve_subscriptions",
                return_value=bundle,
            ),
            patch("organvm_engine.pulse.nerve.propagate", return_value=[]),
        ):
            result = pulse_emit(
                event_type="repo.promoted",
                payload={"repo": "test"},
            )
            assert result["emitted"]["payload"] == {"repo": "test"}

    def test_propagation_results(self):
        event = _FakeEvent()
        notified = [{"subscriber": "org/repo", "action": "notify"}]
        bundle = _FakeNerveBundle()
        with (
            patch("organvm_engine.pulse.events.emit", return_value=event),
            patch(
                "organvm_engine.pulse.nerve.resolve_subscriptions",
                return_value=bundle,
            ),
            patch("organvm_engine.pulse.nerve.propagate", return_value=notified),
        ):
            result = pulse_emit(event_type="repo.promoted")
            assert result["notified_count"] == 1


# ---------------------------------------------------------------------------
# Tests: pulse_briefing
# ---------------------------------------------------------------------------

class TestPulseBriefing:
    def test_import_error_handled(self):
        with patch.dict(
            "sys.modules",
            {"organvm_engine.pulse.continuity": None},
        ):
            result = pulse_briefing()
            assert "error" in result

    def test_returns_dict(self):
        mock_briefing = MagicMock()
        mock_briefing.to_dict.return_value = {"summary": "all quiet", "hours": 24}
        mock_module = MagicMock()
        mock_module.build_briefing.return_value = mock_briefing

        with patch.dict(
            "sys.modules",
            {"organvm_engine.pulse.continuity": mock_module},
        ):
            result = pulse_briefing(hours=12)
            assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# Tests: pulse_memory
# ---------------------------------------------------------------------------

class TestPulseMemory:
    def test_import_error_handled(self):
        with patch.dict(
            "sys.modules",
            {"organvm_engine.pulse.shared_memory": None},
        ):
            result = pulse_memory()
            assert "error" in result

    def test_returns_insights(self):
        mock_insight = MagicMock()
        mock_insight.to_dict.return_value = {"content": "found a bug"}
        mock_module = MagicMock()
        mock_module.query_insights.return_value = [mock_insight]

        with patch.dict(
            "sys.modules",
            {"organvm_engine.pulse.shared_memory": mock_module},
        ):
            result = pulse_memory(category="bug")
            assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# Tests: pulse_record_insight
# ---------------------------------------------------------------------------

class TestPulseRecordInsight:
    def test_import_error_handled(self):
        with patch.dict(
            "sys.modules",
            {"organvm_engine.pulse.shared_memory": None},
        ):
            result = pulse_record_insight(
                agent="claude",
                category="bug",
                content="found issue",
            )
            assert "error" in result

    def test_records_insight(self):
        mock_insight = MagicMock()
        mock_insight.to_dict.return_value = {
            "agent": "claude",
            "category": "bug",
            "content": "found issue",
        }
        mock_module = MagicMock()
        mock_module.record_insight.return_value = mock_insight

        with patch.dict(
            "sys.modules",
            {"organvm_engine.pulse.shared_memory": mock_module},
        ):
            result = pulse_record_insight(
                agent="claude",
                category="bug",
                content="found issue",
                tags=["engine"],
            )
            assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# Tests: pulse_flow
# ---------------------------------------------------------------------------

class TestPulseFlow:
    def test_import_error_handled(self):
        with patch.dict(
            "sys.modules",
            {"organvm_engine.pulse.flow": None},
        ):
            result = pulse_flow()
            assert "error" in result

    def test_returns_profile(self):
        mock_profile = MagicMock()
        mock_profile.to_dict.return_value = {"total_flow": 42}
        mock_flow_module = MagicMock()
        mock_flow_module.compute_flow.return_value = mock_profile

        with (
            patch.dict(
                "sys.modules",
                {"organvm_engine.pulse.flow": mock_flow_module},
            ),
            patch(
                "organvm_engine.seed.graph.build_seed_graph",
                return_value=_FakeSeedGraph(),
            ),
        ):
            result = pulse_flow()
            assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# Fake AMMOI snapshots for velocity tests
# ---------------------------------------------------------------------------

@dataclass
class _FakeAMMOI:
    """Minimal AMMOI stand-in with fields needed by extract_timeseries."""

    system_density: float = 0.5
    active_edges: int = 10
    tension_count: int = 3
    event_frequency_24h: int = 100
    cluster_count: int = 2
    orphan_count: int = 1
    overcoupled_count: int = 0
    inference_score: float = 0.8
    flow_score: float = 0.6


# ---------------------------------------------------------------------------
# Tests: _compute_velocity_factors
# ---------------------------------------------------------------------------

class TestComputeVelocityFactors:
    """Verify that _compute_velocity_factors wires real temporal data."""

    def test_returns_zeros_when_no_history(self):
        """With no AMMOI history, all factors should be 0.0."""
        with (
            patch(
                "organvm_engine.pulse.ammoi._read_history",
                return_value=[],
            ),
            patch(
                "organvm_engine.pulse.events.event_counts",
                return_value={},
            ),
        ):
            hv, sv, sf = _compute_velocity_factors()
            assert hv == 0.0
            assert sv == 0.0
            assert sf == 0.0

    def test_returns_zeros_with_single_snapshot(self):
        """A single snapshot is insufficient for velocity computation."""
        with (
            patch(
                "organvm_engine.pulse.ammoi._read_history",
                return_value=[_FakeAMMOI()],
            ),
            patch(
                "organvm_engine.pulse.events.event_counts",
                return_value={},
            ),
        ):
            hv, sv, sf = _compute_velocity_factors()
            assert hv == 0.0
            assert sv == 0.0

    def test_positive_velocity_from_rising_density(self):
        """A rising density series should produce positive health_velocity."""
        snapshots = [
            _FakeAMMOI(system_density=0.40),
            _FakeAMMOI(system_density=0.45),
            _FakeAMMOI(system_density=0.50),
            _FakeAMMOI(system_density=0.55),
        ]
        with (
            patch(
                "organvm_engine.pulse.ammoi._read_history",
                return_value=snapshots,
            ),
            patch(
                "organvm_engine.pulse.events.event_counts",
                return_value={},
            ),
        ):
            hv, sv, sf = _compute_velocity_factors()
            assert hv > 0, f"Expected positive health_velocity, got {hv}"
            assert sv < 0, f"Expected negative stale_velocity, got {sv}"
            assert sv == -hv, "stale_velocity should be -health_velocity"

    def test_negative_velocity_from_falling_density(self):
        """A falling density series should produce negative health_velocity."""
        snapshots = [
            _FakeAMMOI(system_density=0.60),
            _FakeAMMOI(system_density=0.55),
            _FakeAMMOI(system_density=0.50),
            _FakeAMMOI(system_density=0.45),
        ]
        with (
            patch(
                "organvm_engine.pulse.ammoi._read_history",
                return_value=snapshots,
            ),
            patch(
                "organvm_engine.pulse.events.event_counts",
                return_value={},
            ),
        ):
            hv, sv, sf = _compute_velocity_factors()
            assert hv < 0, f"Expected negative health_velocity, got {hv}"
            assert sv > 0, f"Expected positive stale_velocity, got {sv}"

    def test_stable_density_produces_near_zero_velocity(self):
        """A flat density series should produce ~0 velocity."""
        snapshots = [
            _FakeAMMOI(system_density=0.50),
            _FakeAMMOI(system_density=0.50),
            _FakeAMMOI(system_density=0.50),
        ]
        with (
            patch(
                "organvm_engine.pulse.ammoi._read_history",
                return_value=snapshots,
            ),
            patch(
                "organvm_engine.pulse.events.event_counts",
                return_value={},
            ),
        ):
            hv, sv, sf = _compute_velocity_factors()
            assert hv == pytest.approx(0.0)
            assert sv == pytest.approx(0.0)

    def test_session_frequency_computed_from_events(self):
        """Session events should produce a non-zero session_frequency."""
        with (
            patch(
                "organvm_engine.pulse.ammoi._read_history",
                return_value=[],
            ),
            patch(
                "organvm_engine.pulse.events.event_counts",
                return_value={
                    "session.started": 5,
                    "session.ended": 5,
                    "registry.updated": 10,
                    "pulse.heartbeat": 80,
                },
            ),
        ):
            _, _, sf = _compute_velocity_factors()
            # 10 session events / 100 total = 0.1
            assert sf == pytest.approx(0.1)

    def test_session_frequency_zero_with_no_session_events(self):
        """No session events means session_frequency = 0."""
        with (
            patch(
                "organvm_engine.pulse.ammoi._read_history",
                return_value=[],
            ),
            patch(
                "organvm_engine.pulse.events.event_counts",
                return_value={"registry.updated": 10},
            ),
        ):
            _, _, sf = _compute_velocity_factors()
            assert sf == pytest.approx(0.0)

    def test_graceful_fallback_on_history_exception(self):
        """If AMMOI history raises, velocity falls back to 0.0."""
        with (
            patch(
                "organvm_engine.pulse.ammoi._read_history",
                side_effect=RuntimeError("disk error"),
            ),
            patch(
                "organvm_engine.pulse.events.event_counts",
                return_value={},
            ),
        ):
            hv, sv, sf = _compute_velocity_factors()
            assert hv == 0.0
            assert sv == 0.0

    def test_graceful_fallback_on_event_exception(self):
        """If event_counts raises, session_frequency falls back to 0.0."""
        with (
            patch(
                "organvm_engine.pulse.ammoi._read_history",
                return_value=[],
            ),
            patch(
                "organvm_engine.pulse.events.event_counts",
                side_effect=RuntimeError("event bus down"),
            ),
        ):
            _, _, sf = _compute_velocity_factors()
            assert sf == 0.0

    def test_velocity_scaling_matches_affective_thresholds(self):
        """Velocity should be scaled to health_pct range (0-100)."""
        # A density change of 0.05 per step -> 0.05 raw velocity
        # Scaled by 100x -> 5.0, which exceeds affective.py's 0.5 threshold
        snapshots = [
            _FakeAMMOI(system_density=0.40),
            _FakeAMMOI(system_density=0.45),
            _FakeAMMOI(system_density=0.50),
        ]
        with (
            patch(
                "organvm_engine.pulse.ammoi._read_history",
                return_value=snapshots,
            ),
            patch(
                "organvm_engine.pulse.events.event_counts",
                return_value={},
            ),
        ):
            hv, _, _ = _compute_velocity_factors()
            assert hv == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# Tests: pulse_mood with real velocity wiring
# ---------------------------------------------------------------------------

class TestPulseMoodVelocityWiring:
    """Verify pulse_mood passes real velocity data to MoodFactors."""

    def test_velocity_flows_to_compute_mood(self):
        """MoodFactors receives real velocity values, not hardcoded 0.0."""
        organism = _FakeOrganism()
        graph = _FakeSeedGraph()
        density = _FakeDensity()
        snapshots = [
            _FakeAMMOI(system_density=0.40),
            _FakeAMMOI(system_density=0.45),
            _FakeAMMOI(system_density=0.50),
        ]

        captured_factors = {}

        def _capture_compute_mood(factors):
            captured_factors["health_velocity"] = factors.health_velocity
            captured_factors["stale_velocity"] = factors.stale_velocity
            captured_factors["session_frequency"] = factors.session_frequency
            return _FakeMoodReading()

        with (
            patch(
                "organvm_engine.metrics.organism.get_organism",
                return_value=organism,
            ),
            patch(
                "organvm_engine.seed.graph.build_seed_graph",
                return_value=graph,
            ),
            patch(
                "organvm_engine.seed.graph.validate_edge_resolution",
                return_value=[],
            ),
            patch(
                "organvm_engine.pulse.density.compute_density",
                return_value=density,
            ),
            patch(
                "organvm_engine.pulse.affective.compute_mood",
                side_effect=_capture_compute_mood,
            ),
            patch(
                "organvm_engine.pulse.ammoi._read_history",
                return_value=snapshots,
            ),
            patch(
                "organvm_engine.pulse.events.event_counts",
                return_value={"session.started": 3, "pulse.heartbeat": 7},
            ),
        ):
            pulse_mood()

        assert captured_factors["health_velocity"] != 0.0, (
            "health_velocity should not be hardcoded to 0.0"
        )
        assert captured_factors["health_velocity"] > 0, (
            "Rising density should produce positive health_velocity"
        )
        assert captured_factors["stale_velocity"] < 0, (
            "Rising density should produce negative stale_velocity"
        )
        assert captured_factors["session_frequency"] > 0, (
            "Session events should produce non-zero session_frequency"
        )

    def test_mood_degrades_to_steady_without_history(self):
        """Without AMMOI history, velocity factors are 0 and mood is still returned."""
        organism = _FakeOrganism()
        graph = _FakeSeedGraph()
        density = _FakeDensity()

        captured_factors = {}

        def _capture_compute_mood(factors):
            captured_factors["health_velocity"] = factors.health_velocity
            captured_factors["stale_velocity"] = factors.stale_velocity
            captured_factors["session_frequency"] = factors.session_frequency
            return _FakeMoodReading()

        with (
            patch(
                "organvm_engine.metrics.organism.get_organism",
                return_value=organism,
            ),
            patch(
                "organvm_engine.seed.graph.build_seed_graph",
                return_value=graph,
            ),
            patch(
                "organvm_engine.seed.graph.validate_edge_resolution",
                return_value=[],
            ),
            patch(
                "organvm_engine.pulse.density.compute_density",
                return_value=density,
            ),
            patch(
                "organvm_engine.pulse.affective.compute_mood",
                side_effect=_capture_compute_mood,
            ),
            patch(
                "organvm_engine.pulse.ammoi._read_history",
                return_value=[],
            ),
            patch(
                "organvm_engine.pulse.events.event_counts",
                return_value={},
            ),
        ):
            result = pulse_mood()

        assert isinstance(result, dict)
        assert captured_factors["health_velocity"] == 0.0
        assert captured_factors["stale_velocity"] == 0.0
        assert captured_factors["session_frequency"] == 0.0


# ---------------------------------------------------------------------------
# Tests: pulse_emit logging
# ---------------------------------------------------------------------------

class TestPulseEmitLogging:
    """Verify pulse_emit logs errors instead of silently swallowing them."""

    def test_propagation_error_is_logged(self):
        """When propagation fails, the error should be logged, not silently swallowed."""
        event = _FakeEvent()
        with (
            patch("organvm_engine.pulse.events.emit", return_value=event),
            patch(
                "organvm_engine.pulse.nerve.resolve_subscriptions",
                side_effect=RuntimeError("subscription resolution failed"),
            ),
            patch("organvm_mcp.tools.pulse.logger") as mock_logger,
        ):
            result = pulse_emit(event_type="repo.promoted")
            # Event should still be emitted even if propagation fails
            assert "emitted" in result
            assert result["notified_count"] == 0
            # The error should have been logged
            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args
            assert "repo.promoted" in str(call_args)

    def test_propagation_success_no_warning(self):
        """When propagation succeeds, no warning should be logged."""
        event = _FakeEvent()
        bundle = _FakeNerveBundle()
        with (
            patch("organvm_engine.pulse.events.emit", return_value=event),
            patch(
                "organvm_engine.pulse.nerve.resolve_subscriptions",
                return_value=bundle,
            ),
            patch("organvm_engine.pulse.nerve.propagate", return_value=[]),
            patch("organvm_mcp.tools.pulse.logger") as mock_logger,
        ):
            result = pulse_emit(event_type="repo.promoted")
            assert result["notified_count"] == 0
            mock_logger.warning.assert_not_called()
