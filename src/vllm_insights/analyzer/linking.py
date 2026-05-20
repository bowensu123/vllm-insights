"""Link each merged PR to the first release that included it."""
from pathlib import Path
from rich.console import Console

from ..db import connect

console = Console()


def link_prs_to_releases(db_path: Path) -> int:
    """For each merged PR, set release_tag = first non-prerelease whose published_at >= merged_at.

    Uses SQLite scalar subquery — simple and correct as long as the release count stays small.
    Returns the number of PRs updated.
    """
    with connect(db_path) as conn:
        # Only stable releases count as "first release including this PR"
        cur = conn.execute(
            """
            UPDATE pull_requests AS pr
            SET release_tag = (
                SELECT r.tag
                FROM releases AS r
                WHERE r.is_prerelease = 0
                  AND r.published_at >= pr.merged_at
                ORDER BY r.published_at ASC
                LIMIT 1
            )
            WHERE pr.merged_at IS NOT NULL
            """
        )
        n = cur.rowcount
    console.log(f"[green]link[/] PR→release: {n} rows updated")
    return n
