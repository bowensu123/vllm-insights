from datetime import datetime, timezone
from rich.console import Console

from ..db import connect, set_sync_state
from ..github import GitHubClient
from ..release_notes import flatten, parse_sections

console = Console()


def sync_releases(client: GitHubClient, db_path) -> int:
    count = 0
    with connect(db_path) as conn:
        for rel in client.list_releases():
            tag = rel.get("tag_name")
            if not tag:
                continue
            conn.execute(
                """INSERT INTO releases(tag, name, published_at, is_prerelease, body, url)
                   VALUES(?,?,?,?,?,?)
                   ON CONFLICT(tag) DO UPDATE SET
                     name=excluded.name, published_at=excluded.published_at,
                     is_prerelease=excluded.is_prerelease, body=excluded.body, url=excluded.url""",
                (
                    tag,
                    rel.get("name"),
                    rel.get("published_at") or rel.get("created_at"),
                    1 if rel.get("prerelease") else 0,
                    rel.get("body"),
                    rel.get("html_url"),
                ),
            )
            # Parse sections
            conn.execute("DELETE FROM release_sections WHERE tag = ?", (tag,))
            for section, item in flatten(parse_sections(rel.get("body"))):
                conn.execute(
                    "INSERT OR IGNORE INTO release_sections(tag, section, item) VALUES(?,?,?)",
                    (tag, section[:200], item[:1000]),
                )
            count += 1
        set_sync_state(conn, "releases", datetime.now(timezone.utc).isoformat())
    console.log(f"[green]releases[/] synced: {count}")
    return count
