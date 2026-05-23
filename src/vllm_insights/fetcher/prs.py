from datetime import datetime, timezone
from rich.console import Console

from ..db import connect, get_sync_state, set_sync_state
from ..github import GitHubClient

console = Console()


def sync_prs(client: GitHubClient, db_path, full: bool = False) -> int:
    with connect(db_path) as conn:
        since = None if full else get_sync_state(conn, "prs")
    count = 0
    with connect(db_path) as conn:
        for pr in client.list_pulls(state="all", since_iso=since):
            labels = ",".join(l["name"] for l in pr.get("labels", []))
            state = "MERGED" if pr.get("merged_at") else pr.get("state", "").upper()
            # GitHub returns a `reactions` object on issues + PRs with per-emoji
            # counts. The /pulls list endpoint doesn't always include it; when
            # missing we just default to zero — it'll get backfilled next sync.
            reacts = pr.get("reactions") or {}
            conn.execute(
                """INSERT INTO pull_requests(
                       number, title, state, author, created_at, merged_at, closed_at,
                       additions, deletions, changed_files, labels, url, body,
                       updated_at, reactions_total, reactions_plus_one, reactions_minus_one,
                       reactions_rocket, reactions_heart, reactions_hooray,
                       reactions_eyes, reactions_laugh, reactions_confused)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(number) DO UPDATE SET
                     title=excluded.title, state=excluded.state, merged_at=excluded.merged_at,
                     closed_at=excluded.closed_at, labels=excluded.labels,
                     body=excluded.body, updated_at=excluded.updated_at,
                     reactions_total=excluded.reactions_total,
                     reactions_plus_one=excluded.reactions_plus_one,
                     reactions_minus_one=excluded.reactions_minus_one,
                     reactions_rocket=excluded.reactions_rocket,
                     reactions_heart=excluded.reactions_heart,
                     reactions_hooray=excluded.reactions_hooray,
                     reactions_eyes=excluded.reactions_eyes,
                     reactions_laugh=excluded.reactions_laugh,
                     reactions_confused=excluded.reactions_confused""",
                (
                    pr["number"],
                    pr.get("title"),
                    state,
                    (pr.get("user") or {}).get("login"),
                    pr.get("created_at"),
                    pr.get("merged_at"),
                    pr.get("closed_at"),
                    pr.get("additions"),
                    pr.get("deletions"),
                    pr.get("changed_files"),
                    labels,
                    pr.get("html_url"),
                    pr.get("body") or "",
                    pr.get("updated_at"),
                    reacts.get("total_count", 0),
                    reacts.get("+1", 0),
                    reacts.get("-1", 0),
                    reacts.get("rocket", 0),
                    reacts.get("heart", 0),
                    reacts.get("hooray", 0),
                    reacts.get("eyes", 0),
                    reacts.get("laugh", 0),
                    reacts.get("confused", 0),
                ),
            )
            count += 1
            if count % 200 == 0:
                console.log(f"  …{count} PRs synced")
        set_sync_state(conn, "prs", datetime.now(timezone.utc).isoformat())
    console.log(f"[green]PRs[/] synced: {count}")
    return count
