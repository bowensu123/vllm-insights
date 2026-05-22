"""Atom feed and per-feature deep pages.

`build_feed` emits a minimal Atom 1.0 feed listing the most recent vLLM
releases plus our own weekly digests, so readers can subscribe instead of
re-visiting the homepage. We keep it Atom rather than RSS because Atom is
better-defined for self-hosted content and most modern readers support both.

`build_feature_pages` writes one page per row in `source_inventory`. Each page
shows the source file with a permalink, the merged PRs from the last 180 days
that touched it (joined via `pr_files`), and a back-link to the homepage. This
is the SEO play: when someone Googles "vLLM fp8" or "vLLM awq_marlin" they
should land on a page about that exact file with real PR refs, not the
homepage. The pages are static; the GH Pages crawler will index them.
"""
from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from pathlib import Path
from xml.sax.saxutils import escape as xescape

from .db import connect
from .source_scan import load_inventory, kinds_in_order


def _site_base_url(repo_owner: str) -> str:
    """The site is published to <owner>.github.io/<project>. We hardcode the
    project slug here because the repo name and the published path may differ
    on a fork."""
    return f"https://{repo_owner}.github.io/vllm-insights"


def build_feed(db_path: Path, docs_dir: Path, site_owner: str = "bowensu123") -> Path:
    """Write `docs/feed.xml`. Returns the path written."""
    base = _site_base_url(site_owner)
    updated = datetime.now(timezone.utc).isoformat()

    entries: list[str] = []
    with connect(db_path) as conn:
        releases = conn.execute(
            "SELECT tag, name, published_at, url, body FROM releases "
            "WHERE is_prerelease = 0 ORDER BY published_at DESC LIMIT 15"
        ).fetchall()

    for r in releases:
        body_short = (r["body"] or "")[:600].strip()
        entry_id = f"{base}/release/{r['tag']}"
        entries.append(
            "<entry>"
            f"<id>{xescape(entry_id)}</id>"
            f"<title>vLLM release {xescape(r['tag'])}</title>"
            f"<link rel='alternate' href='{xescape(r['url'] or entry_id)}'/>"
            f"<updated>{xescape(r['published_at'])}</updated>"
            f"<summary type='text'>{xescape(body_short)}{'…' if r['body'] and len(r['body']) > 600 else ''}</summary>"
            "</entry>"
        )

    # Weekly digests written to docs/weekly/*.md
    weekly_dir = docs_dir / "weekly"
    if weekly_dir.exists():
        md_files = sorted(
            (p for p in weekly_dir.glob("*.md") if p.name not in ("latest.md", "index.md")),
            reverse=True,
        )[:10]
        for f in md_files:
            slug = f.stem  # e.g. "2026-W21"
            entry_id = f"{base}/weekly/{slug}.html"
            mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc).isoformat()
            head = ""
            try:
                head = f.read_text(encoding="utf-8")[:1500]
            except OSError:
                pass
            entries.append(
                "<entry>"
                f"<id>{xescape(entry_id)}</id>"
                f"<title>vLLM weekly digest {xescape(slug)}</title>"
                f"<link rel='alternate' href='{xescape(entry_id)}'/>"
                f"<updated>{xescape(mtime)}</updated>"
                f"<summary type='text'>{xescape(head)}</summary>"
                "</entry>"
            )

    body = (
        "<?xml version='1.0' encoding='utf-8'?>"
        "<feed xmlns='http://www.w3.org/2005/Atom'>"
        f"<id>{xescape(base)}/feed.xml</id>"
        "<title>vLLM Insights</title>"
        f"<updated>{xescape(updated)}</updated>"
        f"<link rel='self' href='{xescape(base)}/feed.xml'/>"
        f"<link rel='alternate' href='{xescape(base)}/'/>"
        "<author><name>vllm-insights</name></author>"
        f"{''.join(entries)}"
        "</feed>"
    )
    out = docs_dir / "feed.xml"
    out.write_text(body, encoding="utf-8")
    return out


def _feature_slug(kind: str, name: str) -> str:
    return f"{kind}-{name}".replace("_", "-").lower()


_FEATURE_PAGE_CSS = """
body { font-family: -apple-system, Segoe UI, Helvetica, Arial, sans-serif;
       max-width: 900px; margin: 2rem auto; padding: 0 1rem; line-height: 1.5; }
header { border-bottom: 1px solid #ddd3; padding-bottom: 1rem; margin-bottom: 1rem; }
h1 { margin: 0 0 .2rem; font-size: 1.5rem; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.lede { opacity: .8; margin: .3rem 0; }
.meta { font-size: .8rem; opacity: .6; }
.meta a { text-decoration: none; }
.meta a:hover { text-decoration: underline; }
ul.pr-list { padding-left: 0; list-style: none; }
ul.pr-list li { padding: .35rem 0; border-bottom: 1px solid #ddd3; font-size: .9rem; }
ul.pr-list a { text-decoration: none; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
"""


def build_feature_pages(db_path: Path, docs_dir: Path,
                        repo: str = "vllm-project/vllm") -> int:
    """One static page per source_inventory row, under docs/features/.

    Returns the number of pages written. If the inventory is empty (sync
    hasn't run) we write nothing.
    """
    inv = load_inventory(db_path)
    if not inv:
        return 0
    feat_dir = docs_dir / "features"
    feat_dir.mkdir(parents=True, exist_ok=True)

    kind_label = dict(kinds_in_order())
    pages = 0
    with connect(db_path) as conn:
        for row in inv:
            slug = _feature_slug(row["kind"], row["name"])
            path = row["source_path"]
            blob = f"https://github.com/{repo}/blob/main/{path}"

            pr_rows = conn.execute(
                """
                SELECT p.number, p.title, p.author, p.merged_at, p.url, p.release_tag
                FROM pr_files prf
                JOIN pull_requests p ON p.number = prf.pr_number
                WHERE prf.path = ?
                  AND p.merged_at IS NOT NULL
                  AND p.merged_at >= datetime('now', '-180 days')
                ORDER BY p.merged_at DESC
                LIMIT 50
                """,
                (path,),
            ).fetchall()

            pr_lis = "".join(
                f"<li>"
                f"<a href='{escape(r['url'])}' target='_blank' rel='noopener'>#{r['number']}</a> "
                f"{escape(r['title'])} &middot; "
                f"<span class='meta'>@{escape(r['author'] or '?')}"
                + (f" &rarr; {escape(r['release_tag'])}" if r['release_tag'] else "")
                + f" &middot; {escape((r['merged_at'] or '')[:10])}</span>"
                f"</li>"
                for r in pr_rows
            )
            empty_note = (
                "<p class='meta'>No merged PRs touched this file in the last 180 days. "
                "The file is still present in upstream but is dormant relative to the "
                "rest of the codebase.</p>"
            ) if not pr_rows else ""

            html = (
                "<!DOCTYPE html><html lang='en'><head>"
                "<meta charset='utf-8'>"
                "<meta name='viewport' content='width=device-width,initial-scale=1'>"
                f"<title>{escape(row['name'])} &mdash; vLLM Insights</title>"
                f"<meta name='description' content='Recent vLLM PRs touching "
                f"{escape(path)} (the {escape(row['name'])} implementation).'>"
                f"<style>{_FEATURE_PAGE_CSS}</style>"
                "</head><body>"
                "<header>"
                "<nav style='margin-bottom:.5rem'><a href='../'>&larr; Home</a></nav>"
                f"<h1>{escape(row['name'])}</h1>"
                f"<p class='lede'>{escape(kind_label.get(row['kind'], row['kind']))} "
                f"feature implemented at "
                f"<a href='{blob}' target='_blank' rel='noopener'>"
                f"<code>{escape(path)}</code></a> in upstream vLLM.</p>"
                f"<p class='meta'>Last verified in registry: "
                f"{escape((row['last_seen_at'] or '')[:10])}</p>"
                "</header>"
                f"<h2>Recent merged PRs touching this file</h2>"
                f"{empty_note}"
                f"<ul class='pr-list'>{pr_lis}</ul>"
                "</body></html>"
            )
            (feat_dir / f"{slug}.html").write_text(html, encoding="utf-8")
            pages += 1

    # Index page listing every feature.
    by_kind: dict[str, list[dict]] = {}
    for row in inv:
        by_kind.setdefault(row["kind"], []).append(row)
    sections = []
    for kind, label in kinds_in_order():
        if kind not in by_kind:
            continue
        lis = "".join(
            f"<li><a href='{_feature_slug(kind, r['name'])}.html'>"
            f"<code>{escape(r['name'])}</code></a> "
            f"<span class='meta'>{escape(r['source_path'])}</span></li>"
            for r in sorted(by_kind[kind], key=lambda r: r["name"])
        )
        sections.append(
            f"<h2>{escape(label)} <span class='meta'>({len(by_kind[kind])})</span></h2>"
            f"<ul class='pr-list'>{lis}</ul>"
        )
    index_html = (
        "<!DOCTYPE html><html lang='en'><head>"
        "<meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>Feature index &mdash; vLLM Insights</title>"
        f"<style>{_FEATURE_PAGE_CSS}</style>"
        "</head><body>"
        "<header><nav><a href='../'>&larr; Home</a></nav>"
        "<h1 style='font-family:inherit'>Feature index</h1>"
        "<p class='lede'>Every quantization method, attention backend, parallelism"
        " mode, hardware platform, LoRA implementation and spec-decode method"
        " in upstream vLLM. Sourced from <code>vllm/</code> via a recursive"
        " git-tree scan — no curation.</p></header>"
        f"{''.join(sections)}"
        "</body></html>"
    )
    (feat_dir / "index.html").write_text(index_html, encoding="utf-8")
    return pages
