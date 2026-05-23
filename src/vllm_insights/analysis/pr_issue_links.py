"""Extract PR → Issue links from PR bodies.

GitHub auto-closes issues when a PR body contains a "closing keyword" + an
issue reference. The full list of keywords lives in the GitHub docs and we
mirror it here. We deliberately ignore plain `#1234` mentions because they're
extremely noisy — issues get referenced for context all the time without
implying a fix.

Pattern: `(close|closes|closed|fix|fixes|fixed|resolve|resolves|resolved)
          \\s+(?:#|owner/repo#)?(\\d+)`

We also pick up the lower-strength "addresses #N" pattern because the vLLM
community uses it heavily for partial fixes. That ends up in the `kind`
column so the UI can downweight it.
"""
from __future__ import annotations

import re
from pathlib import Path

from rich.console import Console

from ..db import connect

console = Console()


# Keyword → normalized kind. Order doesn't matter; we match longest-first
# implicitly via the alternation.
_KW_MAP: dict[str, str] = {
    "close":    "closes",   "closes":  "closes",   "closed":   "closes",
    "fix":      "fixes",    "fixes":   "fixes",    "fixed":    "fixes",
    "resolve":  "resolves", "resolves":"resolves", "resolved": "resolves",
    "address":  "addresses","addresses":"addresses","addressed":"addresses",
}
_RE = re.compile(
    r"\b(" + "|".join(sorted(_KW_MAP.keys(), key=len, reverse=True)) + r")\b"
    r"[:\s]+"                      # the connector — `: ` or whitespace
    r"(?:vllm-project/vllm)?"      # optional owner/repo prefix
    r"#(\d{2,6})\b",
    re.IGNORECASE,
)


def extract_links(body: str) -> list[tuple[int, str]]:
    """Return `[(issue_number, kind), ...]` for every link found in `body`."""
    if not body:
        return []
    seen: set[tuple[int, str]] = set()
    out: list[tuple[int, str]] = []
    for m in _RE.finditer(body):
        kw = m.group(1).lower()
        kind = _KW_MAP.get(kw, "mentions")
        num = int(m.group(2))
        # Bound to reasonable issue numbers; vLLM is in the tens of thousands.
        if num < 1 or num > 99999:
            continue
        if (num, kind) in seen:
            continue
        seen.add((num, kind))
        out.append((num, kind))
    return out


def sync_pr_issue_links(db_path: Path) -> int:
    """Walk every PR with a non-empty body, parse it, upsert the links.

    Cheap: parsing is local. We deliberately rebuild from scratch each run
    rather than incrementally so changes to the regex propagate to old PRs.
    """
    n = 0
    with connect(db_path) as conn:
        # Drop the old snapshot; cheaper than diffing.
        conn.execute("DELETE FROM pr_issue_links")
        rows = conn.execute(
            "SELECT number, body FROM pull_requests WHERE body IS NOT NULL AND body != ''"
        ).fetchall()
        for r in rows:
            links = extract_links(r["body"])
            for issue_num, kind in links:
                conn.execute(
                    "INSERT OR IGNORE INTO pr_issue_links(pr_number, issue_number, kind) "
                    "VALUES (?, ?, ?)",
                    (r["number"], issue_num, kind),
                )
                n += 1
    console.print(f"[cyan]PR↔Issue links:[/] {n} link(s) across "
                  f"{len(rows)} PR bodies")
    return n


def top_issue_hotspots(db_path: Path, *, limit: int = 15,
                      only_open: bool = True) -> list[dict]:
    """Issues ranked by the number of distinct PRs that fixed/closed/resolved
    them. Excludes weak 'addresses' / 'mentions' kinds by default.

    Returns `[{number, title, state, url, labels, pr_count, kinds}, ...]`.
    """
    sql = """
        SELECT i.number, i.title, i.state, i.url, i.labels,
               COUNT(DISTINCT pil.pr_number) AS pr_count,
               GROUP_CONCAT(DISTINCT pil.kind) AS kinds
        FROM pr_issue_links pil
        JOIN issues i ON i.number = pil.issue_number
        WHERE pil.kind IN ('fixes', 'closes', 'resolves')
    """
    if only_open:
        sql += " AND i.state = 'OPEN'"
    sql += " GROUP BY i.number ORDER BY pr_count DESC LIMIT ?"
    with connect(db_path) as conn:
        rows = conn.execute(sql, (limit,)).fetchall()
    return [dict(r) for r in rows]
