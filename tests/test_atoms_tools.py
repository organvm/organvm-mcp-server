"""Tests for atoms / task tracking tools."""

from __future__ import annotations

import json
from unittest.mock import patch

from organvm_mcp.tools import atoms


class TestAtomsStatus:
    @patch("organvm_mcp.data.paths.atoms_data_dir")
    def test_status_returns_manifest(self, mock_dir, tmp_path):
        manifest = {"version": 1, "files": {}, "counts": {"tasks": 80}}
        manifest_path = tmp_path / "pipeline-manifest.json"
        manifest_path.write_text(json.dumps(manifest))
        mock_dir.return_value = tmp_path
        res = atoms.atoms_status()
        assert res["version"] == 1
        assert res["counts"]["tasks"] == 80

    @patch("organvm_mcp.data.paths.atoms_data_dir")
    def test_status_missing_manifest(self, mock_dir, tmp_path):
        mock_dir.return_value = tmp_path
        res = atoms.atoms_status()
        assert "error" in res


class TestAtomsRollup:
    @patch("organvm_mcp.data.paths.atoms_data_dir")
    @patch("organvm_engine.atoms.rollup.build_rollups")
    def test_rollup_all(self, mock_build, mock_dir, tmp_path):
        from organvm_engine.atoms.rollup import OrganRollup

        mock_dir.return_value = tmp_path
        mock_build.return_value = {
            "III": OrganRollup(
                organ_key="III",
                organ_dir="organvm-iii-ergon",
                registry_key="ORGAN-III",
                total_tasks=10,
                pending_tasks=5,
                completed_tasks=5,
            ),
        }
        res = atoms.atoms_rollup()
        assert res["total_organs"] == 1
        assert res["total_tasks"] == 10

    @patch("organvm_mcp.data.paths.atoms_data_dir")
    @patch("organvm_engine.atoms.rollup.build_rollups")
    def test_rollup_organ_filter(self, mock_build, mock_dir, tmp_path):
        from organvm_engine.atoms.rollup import OrganRollup

        mock_dir.return_value = tmp_path
        mock_build.return_value = {
            "III": OrganRollup(
                organ_key="III",
                organ_dir="organvm-iii-ergon",
                registry_key="ORGAN-III",
                total_tasks=10,
                pending_tasks=5,
                completed_tasks=5,
            ),
        }
        res = atoms.atoms_rollup(organ="III")
        assert res["organ_key"] == "III"

    @patch("organvm_mcp.data.paths.atoms_data_dir")
    @patch("organvm_engine.atoms.rollup.build_rollups")
    def test_rollup_organ_not_found(self, mock_build, mock_dir, tmp_path):
        mock_dir.return_value = tmp_path
        mock_build.return_value = {}
        res = atoms.atoms_rollup(organ="UNKNOWN")
        assert "error" in res


class TestAtomsTasks:
    @patch("organvm_mcp.data.paths.atoms_data_dir")
    @patch("organvm_engine.atoms.rollup.build_rollups")
    def test_tasks_not_found(self, mock_build, mock_dir, tmp_path):
        mock_dir.return_value = tmp_path
        mock_build.return_value = {}
        res = atoms.atoms_tasks(repo_name="nonexistent")
        assert "error" in res


class TestAtomsLinks:
    @patch("organvm_mcp.data.paths.atoms_data_dir")
    def test_links_missing(self, mock_dir, tmp_path):
        mock_dir.return_value = tmp_path
        res = atoms.atoms_links()
        assert "error" in res

    @patch("organvm_mcp.data.paths.atoms_data_dir")
    def test_links_reads_jsonl(self, mock_dir, tmp_path):
        links_file = tmp_path / "atom-links.jsonl"
        links_file.write_text(
            '{"task_id": "abc", "prompt_id": "xyz", "score": 0.5}\n'
            '{"task_id": "def", "prompt_id": "uvw", "score": 0.3}\n',
        )
        mock_dir.return_value = tmp_path
        res = atoms.atoms_links(limit=10)
        assert res["shown"] == 2
        assert res["links"][0]["task_id"] == "abc"

    @patch("organvm_mcp.data.paths.atoms_data_dir")
    def test_links_respects_limit(self, mock_dir, tmp_path):
        links_file = tmp_path / "atom-links.jsonl"
        lines = [f'{{"id": {i}}}\n' for i in range(20)]
        links_file.write_text("".join(lines))
        mock_dir.return_value = tmp_path
        res = atoms.atoms_links(limit=5)
        assert res["shown"] == 5
        assert res["limit"] == 5
