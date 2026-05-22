"""Incremental sync for GitHub Issues (excluding PRs).

We only sync issues that carry at least one label we care about. The vLLM
issue tracker has tens of thousands of feature requests / questions — pulling
everything would burn rate budget without adding signal.

The label list below is intentionally narrow: it's the set that tells you
something about engine health (regressions, perf wins, unstable hardware
backends) or where the project is going (RFCs).
"""
from datetime import datetime, timezone
from rich.console import Console

from ..db import connect, get_sync_state, set_sync_state
from ..github import GitHubClient

console = Console()


# Labels that gate sync. Order matters only for the API request (GH OR-joins).
INTERESTING_LABELS: tuple[str, ...] = (
    "performance",
    "regression",
    "RFC",
    "rfc",
    "bug:hardware",
    "bug:cpu",
    "bug:rocm",
    "bug:tpu",
    "bug:correctness",
    "bug:perf-regression",
    "release-blocker",
    "good-first-issue",
)


def sync_issues(client: GitHubClient, db_path, full: bool = False) -> int:
    """Pull issues carrying at least one interesting label.

    Incremental by default: stops paginating once it hits an issue older than
    `last_synced_at`. Pass `full=True` to ignore the watermark.
    """
    with connect(db_path) as conn:
        since = None if full else get_sync_state(conn, "issues")

    count = 0
    # We loop per-label rather than `labels=l1,l2,...` because the latter is
    # AND semantics on GitHub — an issue must carry ALL listed labels — which
    # would filter out almost everything.
    seen: set[int] = set()
    with connect(db_path) as conn:
        for label in INTERESTING_LABELS:
            for it in client.list_issues(since_iso=since, labels=label, state="all"):
                num = it["number"]
                if num in seen:
                    continue
                seen.add(num)
                labels = ",".join(l["name"] for l in it.get("labels", []))
                conn.execute(
                    """INSERT INTO issues(number, title, state, author, created_at,
                                          updated_at, closed_at, labels, url, comments)
                       VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(number) DO UPDATE SET
                         title=excluded.title, state=excluded.state,
                         updated_at=excluded.updated_at, closed_at=excluded.closed_at,
                         labels=excluded.labels, comments=excluded.comments""",
                    (
                        num,
                        it.get("title"),
                        it.get("state", "").upper(),
                        (it.get("user") or {}).get("login"),
                        it.get("created_at"),
                        it.get("updated_at"),
                        it.get("closed_at"),
                        labels,
                        it.get("html_url"),
                        it.get("comments", 0),
                    ),
                )
                count += 1
        set_sync_state(conn, "issues", datetime.now(timezone.utc).isoformat())
    console.print(f"[cyan]Issues synced:[/] {count} new/updated across "
                  f"{len(INTERESTING_LABELS)} labels")
    return count
