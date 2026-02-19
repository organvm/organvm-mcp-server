"""Shared types for the ORGANVM MCP server."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class PromotionStatus(Enum):
    LOCAL = "LOCAL"
    CANDIDATE = "CANDIDATE"
    PUBLIC_PROCESS = "PUBLIC_PROCESS"
    GRADUATED = "GRADUATED"
    ARCHIVED = "ARCHIVED"


class Tier(Enum):
    FLAGSHIP = "flagship"
    STANDARD = "standard"
    INFRASTRUCTURE = "infrastructure"
    ARCHIVE = "archive"
    PERSONAL = "personal"


@dataclass
class RepoInfo:
    """Summary of a single repository from the registry."""

    name: str
    org: str
    organ: str
    tier: str
    promotion_status: str
    documentation_status: str
    description: str = ""
    dependencies: list[str] = field(default_factory=list)
    url: str = ""


@dataclass
class OrganSummary:
    """Summary statistics for an organ."""

    key: str
    name: str
    org: str
    repo_count: int
    flagship_count: int
    standard_count: int
    infrastructure_count: int
    produces: list[str] = field(default_factory=list)
    consumes: list[str] = field(default_factory=list)


@dataclass
class SeedEdge:
    """A produces/consumes edge from a seed.yaml contract."""

    source_repo: str
    source_organ: str
    target_repo: str
    target_organ: str
    artifact: str
    event_type: str = ""


@dataclass
class EventContract:
    """An event type from the event catalog."""

    event_type: str
    edge: str
    producer_organ: str
    consumer_organ: str
    producer_workflow: str
    consumer_workflow: str
    description: str = ""
    payload_fields: list[str] = field(default_factory=list)


@dataclass
class DependencyNode:
    """A node in the dependency graph."""

    repo: str
    organ: str
    depends_on: list[str] = field(default_factory=list)
    depended_by: list[str] = field(default_factory=list)


@dataclass
class HealthReport:
    """System-wide health summary."""

    total_repos: int
    active_repos: int
    archived_repos: int
    repos_with_ci: int
    repos_with_tests: int
    seed_coverage: float
    omega_criteria_met: int
    omega_criteria_total: int
    soak_test_running: bool
    soak_test_days_remaining: int


@dataclass
class RepoContext:
    """Contextual awareness payload for a specific repo.

    Returned by get_context() — assembles everything an AI session
    needs to know when working in a particular repo.
    """

    repo: RepoInfo
    organ_summary: OrganSummary
    produces: list[SeedEdge]
    consumes: list[SeedEdge]
    siblings: list[str]
    upstream_organs: list[str]
    downstream_organs: list[str]
    governance_notes: list[str] = field(default_factory=list)
