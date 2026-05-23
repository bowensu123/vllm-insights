"""Fork monitoring.

vLLM has tens of thousands of forks; ~99% are abandoned. We pull the list
sorted by star count, keep only forks above `min_stars`, and for each one
ask /compare {upstream}:main...{fork_owner}:{default_branch} to find out
how far it has diverged.

A fork is "interesting" if it has commits NOT yet in upstream — those are
where independent feature work lives (downstream patches, perf experiments,
custom backends). For each interesting fork we also persist up to N of those
unique commits, with the commit message, so the homepage can show "what is
fork X carrying that upstream doesn't have".

Cost: O(forks_above_threshold) compare calls per sync. For vLLM today
that's roughly 30-50, well within rate budget.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from rich.console import Console

from ..db import connect, set_sync_state
from ..github import GitHubClient

console = Console()


def sync_forks(
    client: GitHubClient,
    db_path: Path,
    *,
    min_stars: int = 5,
    max_forks: int = 60,
    upstream_branch: str = "main",
    capture_commits: int = 10,
) -> int:
    """Pull the top forks of `client.repo`, fetch their ahead/behind status,
    and capture up to `capture_commits` unique commits per interesting fork.

    `min_stars` filters out the abandoned long tail. `max_forks` bounds the
    number of /compare calls we make so a runaway sync can't burn the rate
    budget. Tune both based on what the homepage actually surfaces.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    n_seen = 0
    n_interesting = 0

    with connect(db_path) as conn:
        for fork in client.list_forks(sort="stargazers"):
            stars = fork.get("stargazers_count", 0)
            if stars < min_stars:
                # Forks endpoint is sorted by star count desc; once we drop
                # below the threshold the rest will too.
                break
            if n_seen >= max_forks:
                break
            full = fork.get("full_name")
            owner = (fork.get("owner") or {}).get("login")
            head_branch = fork.get("default_branch") or "main"
            url = fork.get("html_url")
            pushed = fork.get("pushed_at")

            ahead = behind = None
            try:
                cmp = client.compare(upstream_branch, f"{owner}:{head_branch}")
                ahead = cmp.get("ahead_by")
                behind = cmp.get("behind_by")
            except Exception as e:  # noqa: BLE001 - one fork failing shouldn't kill the sync
                console.print(f"[yellow]compare failed for {full}:[/] "
                              f"{type(e).__name__}: {e}")
                cmp = None

            conn.execute(
                """INSERT INTO forks(full_name, owner, stars, default_branch,
                                     pushed_at, ahead_by, behind_by, url,
                                     last_checked_at)
                   VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(full_name) DO UPDATE SET
                     stars=excluded.stars, default_branch=excluded.default_branch,
                     pushed_at=excluded.pushed_at,
                     ahead_by=excluded.ahead_by, behind_by=excluded.behind_by,
                     url=excluded.url, last_checked_at=excluded.last_checked_at""",
                (full, owner, stars, head_branch, pushed, ahead, behind, url, now_iso),
            )
            n_seen += 1

            # Capture sample commits if the fork is ahead. The /compare response
            # already includes a `commits` list (up to ~250), so no extra call.
            if cmp and ahead and ahead > 0:
                n_interesting += 1
                conn.execute(
                    "DELETE FROM fork_commits WHERE fork_full_name = ?", (full,)
                )
                for c in (cmp.get("commits") or [])[:capture_commits]:
                    commit_obj = c.get("commit") or {}
                    author = ((commit_obj.get("author") or {}).get("name")
                              or (c.get("author") or {}).get("login"))
                    conn.execute(
                        """INSERT INTO fork_commits(fork_full_name, sha, message,
                                                    author, committed_at, url)
                           VALUES(?, ?, ?, ?, ?, ?)
                           ON CONFLICT(fork_full_name, sha) DO NOTHING""",
                        (
                            full,
                            c.get("sha"),
                            (commit_obj.get("message") or "").split("\n", 1)[0][:240],
                            author,
                            (commit_obj.get("author") or {}).get("date"),
                            c.get("html_url"),
                        ),
                    )
        set_sync_state(conn, "forks", now_iso)

    console.print(f"[cyan]Forks synced:[/] {n_seen} fork(s) above {min_stars}★, "
                  f"{n_interesting} carrying unique commits")
    return n_seen
