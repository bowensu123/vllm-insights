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
            conn.execute(
                """INSERT INTO pull_requests(number,title,state,author,created_at,merged_at,closed_at,
                                              additions,deletions,changed_files,labels,url)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(number) DO UPDATE SET
                     title=excluded.title, state=excluded.state, merged_at=excluded.merged_at,
                     closed_at=excluded.closed_at, labels=excluded.labels""",
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
                ),
            )
            count += 1
            if count % 200 == 0:
                console.log(f"  …{count} PRs synced")
        set_sync_state(conn, "prs", datetime.now(timezone.utc).isoformat())
    console.log(f"[green]PRs[/] synced: {count}")
    return count
