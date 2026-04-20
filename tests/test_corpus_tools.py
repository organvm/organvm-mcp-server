"""Tests for corpus knowledge graph MCP tools."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from organvm_engine.corpus.graph import CorpusGraph, GraphEdge, GraphNode


def _make_test_graph() -> CorpusGraph:
    """Build a minimal corpus graph for testing."""
    g = CorpusGraph()

    # Concepts
    g.add_node(GraphNode(
        uid="concept:ammoi",
        node_type="concept",
        title="AMMOI",
        metadata={"description": "Adaptive Macro-Micro Ontological Index", "discovery": "cross_trunk"},
    ))
    g.add_node(GraphNode(
        uid="concept:era_model",
        node_type="concept",
        title="era_model",
        metadata={"description": "Temporal era governance", "discovery": "spec_directory"},
    ))
    g.add_node(GraphNode(
        uid="concept:orphan",
        node_type="concept",
        title="orphan",
        metadata={"description": "No implementation", "discovery": "spec_directory"},
    ))

    # Transcripts
    g.add_node(GraphNode(uid="TRX-HIS", node_type="transcript", title="Hierarchical Index"))

    # Repos
    g.add_node(GraphNode(
        uid="repo:meta/engine",
        node_type="repo",
        title="organvm-engine",
        metadata={"organ": "META"},
    ))
    g.add_node(GraphNode(
        uid="repo:i/kb",
        node_type="repo",
        title="my-knowledge-base",
        metadata={"organ": "I"},
    ))

    # Edges
    g.add_edge(GraphEdge(source="TRX-HIS", target="concept:ammoi", edge_type="DEFINES"))
    g.add_edge(GraphEdge(
        source="repo:meta/engine",
        target="concept:ammoi",
        edge_type="IMPLEMENTS",
        metadata={"aspect": "metrics/organism.py"},
    ))
    g.add_edge(GraphEdge(
        source="repo:i/kb",
        target="concept:ammoi",
        edge_type="IMPLEMENTS",
        metadata={"aspect": "knowledge pipeline"},
    ))
    g.add_edge(GraphEdge(
        source="spec_dir:era-model",
        target="concept:era_model",
        edge_type="DEFINES",
    ))

    return g


@pytest.fixture()
def mock_graph():
    """Patch the loader to return a test graph."""
    g = _make_test_graph()
    with patch("organvm_mcp.data.loader.load_corpus_graph", return_value=g):
        yield g


class TestCorpusConcepts:
    def test_returns_all_concepts(self, mock_graph: CorpusGraph) -> None:
        from organvm_mcp.tools.corpus import corpus_concepts

        result = corpus_concepts()
        assert result["total"] == 3
        assert result["implemented"] == 1  # Only ammoi has implementations
        assert result["unimplemented"] == 2

    def test_pattern_filter(self, mock_graph: CorpusGraph) -> None:
        from organvm_mcp.tools.corpus import corpus_concepts

        result = corpus_concepts(pattern="ammoi")
        assert result["total"] == 1
        assert result["concepts"][0]["title"] == "AMMOI"

    def test_implementation_details(self, mock_graph: CorpusGraph) -> None:
        from organvm_mcp.tools.corpus import corpus_concepts

        result = corpus_concepts(pattern="ammoi")
        concept = result["concepts"][0]
        assert concept["implementation_count"] == 2
        assert len(concept["implementations"]) == 2


class TestCorpusTrace:
    def test_traces_concept(self, mock_graph: CorpusGraph) -> None:
        from organvm_mcp.tools.corpus import corpus_trace

        result = corpus_trace(concept="AMMOI")
        assert result["concept"] == "AMMOI"
        assert len(result["defining_sources"]) == 1
        assert result["defining_sources"][0]["source"] == "TRX-HIS"
        assert result["implementation_count"] == 2

    def test_concept_not_found(self, mock_graph: CorpusGraph) -> None:
        from organvm_mcp.tools.corpus import corpus_trace

        result = corpus_trace(concept="nonexistent")
        assert "error" in result

    def test_organ_filter(self, mock_graph: CorpusGraph) -> None:
        from organvm_mcp.tools.corpus import corpus_trace

        result = corpus_trace(concept="AMMOI", organ="META")
        assert result["implementation_count"] == 1
        assert result["implementing_repos"][0]["repo"] == "organvm-engine"


class TestCorpusGaps:
    def test_default_threshold(self, mock_graph: CorpusGraph) -> None:
        from organvm_mcp.tools.corpus import corpus_gaps

        result = corpus_gaps()
        assert result["threshold"] == 2
        assert result["robust"] == 1  # ammoi (2 impls >= threshold)
        assert result["fragile"] == 0
        assert result["unimplemented"] == 2  # era_model + orphan

    def test_custom_threshold(self, mock_graph: CorpusGraph) -> None:
        from organvm_mcp.tools.corpus import corpus_gaps

        result = corpus_gaps(threshold=3)
        # ammoi has 2, below threshold of 3 → fragile
        assert result["fragile"] == 1
        assert result["unimplemented"] == 2


class TestCorpusStats:
    def test_returns_stats(self, mock_graph: CorpusGraph) -> None:
        from organvm_mcp.tools.corpus import corpus_stats

        result = corpus_stats()
        assert result["total_nodes"] == 6  # 3 concepts + 1 transcript + 2 repos
        assert "coverage" in result
        assert result["coverage"]["total_concepts"] == 3
        assert result["coverage"]["implemented"] == 1
        assert result["coverage"]["coverage_ratio"] == round(1 / 3, 3)
