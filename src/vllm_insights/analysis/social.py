"""External social signals — currently HN via Algolia (no auth).

What we capture:

  * Hacker News mentions of "vllm" — title, points, comment count, posted
    time, HN thread URL and the destination URL. Pulled from Algolia's HN
    search API (`http://hn.algolia.com/api/v1/search_by_date?query=vllm`).
    No auth, generous rate limit.

  * (Existing) PR reaction counts — captured by the pr_reactions fetcher;
    we expose a "most-reacted PRs this week" view here so all social-signal
    code lives in one place.

Reddit and Twitter were considered and skipped: Reddit's API requires OAuth
since 2023 and the unauth'd JSON endpoints are rate-limited aggressively;
Twitter/X has no free tier for search. Both could be added later behind
their own credentials.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import httpx
from rich.console import Console

from ..db import connect, set_sync_state

console = Console()

# Algolia HN search. `query` does relevance ranking; `search_by_date` returns
# newest first which is what we want for an incremental feed.
_HN_URL = "http://hn.algolia.com/api/v1/search_by_date"


def fetch_hn_mentions(query: str = "vllm", *, days: int = 365,
                     per_page: int = 100, max_pages: int = 5) -> Iterable[dict]:
    """Yield HN hits matching `query` from the last `days` days."""
    since_unix = int(datetime.now(timezone.utc).timestamp()) - days * 86400
    params = {
        "query": query,
        "numericFilters": f"created_at_i>{since_unix}",
        "hitsPerPage": per_page,
        "tags": "story",
    }
    with httpx.Client(timeout=30.0) as client:
        for page in range(max_pages):
            params["page"] = page
            r = client.get(_HN_URL, params=params)
            if r.status_code != 200:
                break
            data = r.json()
            hits = data.get("hits") or []
            if not hits:
                break
            yield from hits
            if len(hits) < per_page:
                break


def sync_hn_mentions(db_path: Path, *, query: str = "vllm",
                    days: int = 365) -> int:
    """Pull HN mentions of vLLM and upsert into `hn_mentions`."""
    now_iso = datetime.now(timezone.utc).isoformat()
    n = 0
    with connect(db_path) as conn:
        for hit in fetch_hn_mentions(query=query, days=days):
            object_id = hit.get("objectID")
            if not object_id:
                continue
            created_iso = hit.get("created_at") or ""
            conn.execute(
                """INSERT INTO hn_mentions(object_id, title, url, hn_url, author,
                                           points, num_comments, created_at, fetched_at)
                   VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(object_id) DO UPDATE SET
                     title=excluded.title, url=excluded.url,
                     points=excluded.points, num_comments=excluded.num_comments,
                     fetched_at=excluded.fetched_at""",
                (
                    object_id,
                    hit.get("title") or "",
                    hit.get("url"),
                    f"https://news.ycombinator.com/item?id={object_id}",
                    hit.get("author"),
                    hit.get("points") or 0,
                    hit.get("num_comments") or 0,
                    created_iso,
                    now_iso,
                ),
            )
            n += 1
        set_sync_state(conn, "hn_mentions", now_iso)
    console.print(f"[cyan]HN mentions:[/] {n} item(s) for query={query!r}")
    return n


def hottest_recent_prs(db_path: Path, *, days: int = 30, limit: int = 10) -> list[dict]:
    """PRs with the highest total reaction count merged in last `days`."""
    with connect(db_path) as conn:
        rows = conn.execute(
            """SELECT number, title, url, author, merged_at,
                      reactions_total, reactions_plus_one, reactions_rocket,
                      reactions_heart, reactions_hooray
               FROM pull_requests
               WHERE merged_at IS NOT NULL
                 AND merged_at >= datetime('now', ?)
                 AND COALESCE(reactions_total, 0) > 0
               ORDER BY reactions_total DESC LIMIT ?""",
            (f"-{int(days)} days", limit),
        ).fetchall()
    return [dict(r) for r in rows]


def top_hn_mentions(db_path: Path, *, limit: int = 10) -> list[dict]:
    """Top HN stories by points (lifetime, not just recent)."""
    with connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM hn_mentions ORDER BY points DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def recent_hn_mentions(db_path: Path, *, limit: int = 10) -> list[dict]:
    """Most recent HN stories — what's being posted right now."""
    with connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM hn_mentions ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]
