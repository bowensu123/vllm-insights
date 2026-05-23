"""Backfill PR reaction counts via the /issues endpoint.

GitHub's `/repos/{owner}/{repo}/pulls` list endpoint doesn't return reactions
on PRs, but `/repos/{owner}/{repo}/issues` does (because PRs are a sub-type of
issues there). So we walk the issues feed sorted by updated-desc, filter to
items that carry a `pull_request` key, and update `pull_requests.reactions_*`
for each one.

We only need PRs the community has actually reacted to — and reactions on
inactive PRs don't change. So this fetcher is incremental on `updated_at`:
on subsequent runs it stops paging as soon as it sees a PR older than the
last sync watermark.
"""
from datetime import datetime, timezone
from rich.console import Console

from ..db import connect, get_sync_state, set_sync_state
from ..github import GitHubClient

console = Console()


def sync_pr_reactions(client: GitHubClient, db_path, full: bool = False) -> int:
    """Update reaction counts on pull_requests rows. Returns rows updated."""
    with connect(db_path) as conn:
        since = None if full else get_sync_state(conn, "pr_reactions")
    n = 0
    with connect(db_path) as conn:
        # `/issues` returns mixed issues+PRs sorted by updated-desc; the
        # `pull_request` key on the response payload distinguishes them.
        for it in client.list_issues(since_iso=since, state="all"):
            if "pull_request" not in it:
                continue
            num = it["number"]
            r = it.get("reactions") or {}
            res = conn.execute(
                """UPDATE pull_requests SET
                       reactions_total = ?, reactions_plus_one = ?, reactions_minus_one = ?,
                       reactions_rocket = ?, reactions_heart = ?, reactions_hooray = ?,
                       reactions_eyes = ?, reactions_laugh = ?, reactions_confused = ?,
                       updated_at = COALESCE(?, updated_at)
                   WHERE number = ?""",
                (
                    r.get("total_count", 0),
                    r.get("+1", 0), r.get("-1", 0),
                    r.get("rocket", 0), r.get("heart", 0), r.get("hooray", 0),
                    r.get("eyes", 0), r.get("laugh", 0), r.get("confused", 0),
                    it.get("updated_at"), num,
                ),
            )
            if res.rowcount:
                n += 1
        set_sync_state(conn, "pr_reactions",
                       datetime.now(timezone.utc).isoformat())
    console.print(f"[cyan]PR reactions:[/] {n} PR(s) updated")
    return n
