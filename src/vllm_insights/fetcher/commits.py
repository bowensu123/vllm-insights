from datetime import datetime, timezone
from rich.console import Console

from ..db import connect, get_sync_state, set_sync_state
from ..github import GitHubClient

console = Console()


def sync_commits(client: GitHubClient, db_path, full: bool = False) -> int:
    with connect(db_path) as conn:
        since = None if full else get_sync_state(conn, "commits")
    count = 0
    with connect(db_path) as conn:
        for c in client.list_commits(since_iso=since):
            commit = c.get("commit") or {}
            author_info = commit.get("author") or {}
            author_login = (c.get("author") or {}).get("login") or author_info.get("name")
            conn.execute(
                """INSERT INTO commits(sha, author, author_email, committed_at, message, url)
                   VALUES(?,?,?,?,?,?)
                   ON CONFLICT(sha) DO UPDATE SET
                     message=excluded.message""",
                (
                    c["sha"],
                    author_login,
                    author_info.get("email"),
                    author_info.get("date"),
                    commit.get("message"),
                    c.get("html_url"),
                ),
            )
            count += 1
            if count % 500 == 0:
                console.log(f"  …{count} commits synced")
        set_sync_state(conn, "commits", datetime.now(timezone.utc).isoformat())
    console.log(f"[green]commits[/] synced: {count}")
    return count
