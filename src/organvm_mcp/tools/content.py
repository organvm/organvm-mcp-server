"""Content pipeline tools — list posts, cadence health, signal detection.

Exposes the conversation-to-content pipeline to any Claude Code session.
"""

from __future__ import annotations

import os
from dataclasses import asdict
from pathlib import Path
from typing import Any


def _content_dir() -> Path:
    """Resolve the content pipeline directory."""
    workspace = Path(
        os.environ.get("ORGANVM_WORKSPACE_DIR", str(Path.home() / "Workspace")),
    )
    return workspace / "organvm-v-logos" / "content-pipeline" / "posts"


def content_list(
    status: str | None = None,
    tag: str | None = None,
) -> dict[str, Any]:
    """List all content posts with optional status/tag filters."""
    from organvm_engine.content.reader import discover_posts, filter_posts

    posts = discover_posts(_content_dir())
    filtered = filter_posts(posts, status=status, tag=tag)

    return {
        "total_posts": len(posts),
        "filtered_count": len(filtered),
        "filters": {"status": status, "tag": tag},
        "posts": [
            {
                "slug": p.slug,
                "title": p.title,
                "date": p.date,
                "status": p.status,
                "tags": p.tags,
                "distribution": p.distribution,
            }
            for p in filtered
        ],
    }


def content_status() -> dict[str, Any]:
    """Weekly cadence health check."""
    from organvm_engine.content.cadence import check_cadence
    from organvm_engine.content.reader import discover_posts

    posts = discover_posts(_content_dir())
    report = check_cadence(posts)

    return {
        "total_posts": report.total_posts,
        "published_count": report.published_count,
        "draft_count": report.draft_count,
        "archived_count": report.archived_count,
        "streak": report.streak,
        "weeks_since_last_post": report.weeks_since_last_post,
        "last_post_date": report.last_post_date,
        "posts_this_week": [
            {"slug": p.slug, "title": p.title, "status": p.status}
            for p in report.posts_this_week
        ],
    }


def content_signals(messages: list[str]) -> dict[str, Any]:
    """Run signal detection on session messages."""
    from organvm_engine.content.signals import detect_content_signals

    signals = detect_content_signals(messages)

    return {
        "message_count": len(messages),
        "signal_count": len(signals),
        "signals": [asdict(s) for s in signals],
    }
