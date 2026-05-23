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

import json
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


def _shared_page_css() -> str:
    """Same tokens as the homepage so styling is consistent across pages."""
    from .ui import DESIGN_TOKENS_CSS, COMPONENTS_CSS
    return DESIGN_TOKENS_CSS + COMPONENTS_CSS + """
.feature-hero { padding: var(--s-3) 0 var(--s-4); border-bottom: 1px solid var(--border-soft); }
.breadcrumbs { font-size: var(--t-sm); color: var(--fg-3); margin: 0 0 var(--s-2); }
.breadcrumbs a { color: var(--fg-2); }
.breadcrumbs .sep { margin: 0 .4rem; opacity: .55; }
.feature-title { font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: var(--t-2x); margin: 0; letter-spacing: -.01em; }
.feature-sub { color: var(--fg-2); margin: .4rem 0 var(--s-3); font-size: var(--t-md); }
.feature-meta { display: flex; flex-wrap: wrap; gap: var(--s-3); font-size: var(--t-sm);
    color: var(--fg-3); }
.feature-meta strong { color: var(--fg-2); font-weight: 600; }
.feature-meta a { color: var(--accent); }
ul.pr-list { padding-left: 0; list-style: none; margin: 0; }
ul.pr-list li { padding: .45rem 0; border-bottom: 1px solid var(--border-soft); font-size: .9rem; }
ul.pr-list a { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
ul.pr-list .meta { font-size: .72rem; color: var(--fg-3); margin-left: .3rem; }
.siblings { margin: var(--s-4) 0; padding: var(--s-3); border: 1px solid var(--border-soft);
    border-radius: var(--r-md); background: var(--bg-2); }
.siblings h2 { font-size: var(--t-sm); text-transform: uppercase;
    letter-spacing: .05em; color: var(--fg-3); margin: 0 0 .5rem; }
.siblings .pill { display: inline-block; margin: .15rem .25rem .15rem 0;
    padding: .2rem .55rem; border-radius: 999px;
    border: 1px solid var(--border); background: var(--bg-3); color: var(--fg-2);
    text-decoration: none; font-size: var(--t-xs);
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.siblings .pill:hover { border-color: var(--accent); color: var(--accent); text-decoration: none; }
.siblings .pill.current { color: var(--accent); border-color: var(--accent);
    background: var(--accent-soft); }
"""


def _feature_topbar() -> str:
    return """
<div class="topbar"><div class="topbar-inner">
<a class="brand" href="../"><span class="brand-mark">▮</span> vLLM Insights</a>
<nav class="topnav">
  <a href="../#latest-release">Release</a>
  <a href="../#capability">Capability</a>
  <a href="../">Home</a>
  <a href="../about.html">About</a>
</nav>
<span class="topbar-spacer"></span>
<a class="tool-btn" href="../feed.xml">RSS</a>
<button class="tool-btn" id="theme-toggle" type="button" aria-label="Toggle theme">◐</button>
</div></div>
<script>
(() => {
  const root = document.documentElement;
  const stored = localStorage.getItem('vi-theme');
  if (stored === 'dark' || stored === 'light') root.setAttribute('data-theme', stored);
  const b = document.getElementById('theme-toggle');
  if (b) b.addEventListener('click', () => {
    const cur = root.getAttribute('data-theme') ||
      (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    const next = cur === 'dark' ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    localStorage.setItem('vi-theme', next);
  });
})();
</script>
"""


def build_feature_pages(db_path: Path, docs_dir: Path,
                        repo: str = "vllm-project/vllm",
                        site_owner: str = "bowensu123") -> int:
    """One static page per source_inventory row, under docs/features/.

    Each page is a proper landing page: breadcrumbs, sibling features, source
    link, recent PR list, OpenGraph card + JSON-LD Article schema.
    """
    inv = load_inventory(db_path)
    if not inv:
        return 0
    feat_dir = docs_dir / "features"
    feat_dir.mkdir(parents=True, exist_ok=True)
    base_site = _site_base_url(site_owner)

    # Bucket inventory by kind so the sibling-pill row is a single lookup.
    by_kind: dict[str, list[dict]] = {}
    for row in inv:
        by_kind.setdefault(row["kind"], []).append(row)

    kind_label = dict(kinds_in_order())
    page_css = _shared_page_css()
    topbar = _feature_topbar()
    pages = 0
    with connect(db_path) as conn:
        for row in inv:
            slug = _feature_slug(row["kind"], row["name"])
            path = row["source_path"]
            blob = f"https://github.com/{repo}/blob/main/{path}"
            kind = row["kind"]
            label = kind_label.get(kind, kind)
            page_url = f"{base_site}/features/{slug}.html"

            pr_rows = conn.execute(
                """SELECT p.number, p.title, p.author, p.merged_at, p.url, p.release_tag
                   FROM pr_files prf
                   JOIN pull_requests p ON p.number = prf.pr_number
                   WHERE prf.path = ?
                     AND p.merged_at IS NOT NULL
                     AND p.merged_at >= datetime('now', '-180 days')
                   ORDER BY p.merged_at DESC LIMIT 50""",
                (path,),
            ).fetchall()
            pr_30d = sum(1 for r in pr_rows
                         if (r["merged_at"] or "") >= _iso_days_ago(30))

            pr_lis = "".join(
                f"<li><a href='{escape(r['url'])}' target='_blank' rel='noopener'>"
                f"#{r['number']}</a> {escape(r['title'])}"
                f"<span class='meta'>@{escape(r['author'] or '?')}"
                + (f" &rarr; {escape(r['release_tag'])}" if r['release_tag'] else "")
                + f" &middot; {escape((r['merged_at'] or '')[:10])}</span></li>"
                for r in pr_rows
            )
            empty_note = (
                "<p style='color:var(--fg-3);font-size:.85rem'>"
                "No merged PRs touched this file in the last 180 days. "
                "It still exists upstream but is dormant.</p>"
            ) if not pr_rows else ""

            # Sibling features (other items of the same kind), excluding self.
            siblings = [r for r in by_kind.get(kind, []) if r["name"] != row["name"]]
            siblings_html = ""
            if siblings:
                pills = "".join(
                    f"<a class='pill' href='{_feature_slug(kind, r['name'])}.html'>"
                    f"{escape(r['name'])}</a>"
                    for r in sorted(siblings, key=lambda r: r["name"])
                )
                siblings_html = (
                    f"<section class='siblings'>"
                    f"<h2>Other {escape(label.lower())} implementations</h2>"
                    f"<span class='pill current'>{escape(row['name'])}</span>"
                    f"{pills}</section>"
                )

            desc = (f"Recent vLLM merged PRs touching {row['name']} "
                    f"({label.lower()}) at {path}.")

            # JSON-LD Article — gives Google a structured snippet
            jsonld = json.dumps({
                "@context": "https://schema.org",
                "@type": "TechArticle",
                "headline": f"{row['name']} — vLLM",
                "description": desc,
                "url": page_url,
                "about": label,
                "isPartOf": {"@type": "WebSite", "name": "vLLM Insights",
                             "url": base_site},
                "datePublished": (row['last_seen_at'] or '')[:10],
            }, ensure_ascii=False)

            html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(row['name'])} — vLLM Insights</title>
<meta name="description" content="{escape(desc)}">
<link rel="canonical" href="{escape(page_url)}">
<meta property="og:type" content="article">
<meta property="og:title" content="{escape(row['name'])} — vLLM Insights">
<meta property="og:description" content="{escape(desc)}">
<meta property="og:url" content="{escape(page_url)}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{escape(row['name'])} — vLLM Insights">
<meta name="twitter:description" content="{escape(desc)}">
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><rect width='64' height='64' rx='12' fill='%232f6feb'/><text x='32' y='44' text-anchor='middle' font-family='-apple-system,sans-serif' font-size='38' font-weight='700' fill='white'>v</text></svg>">
<style>{page_css}</style>
<script type="application/ld+json">{jsonld}</script>
</head>
<body>
{topbar}
<main class="page">
<header class="feature-hero">
<nav class="breadcrumbs" aria-label="Breadcrumb">
  <a href="../">Home</a><span class="sep">/</span>
  <a href="./">Features</a><span class="sep">/</span>
  <span>{escape(label)}</span><span class="sep">/</span>
  <span aria-current="page">{escape(row['name'])}</span>
</nav>
<h1 class="feature-title">{escape(row['name'])}</h1>
<p class="feature-sub">{escape(label)} implementation in upstream vLLM.</p>
<div class="feature-meta">
  <div><strong>Source:</strong> <a href="{blob}" target="_blank" rel="noopener">
    <code>{escape(path)}</code></a></div>
  <div><strong>Last verified:</strong> {escape((row['last_seen_at'] or '')[:10])}</div>
  <div><strong>PRs touching it (180d):</strong> {len(pr_rows)} ({pr_30d} in last 30d)</div>
</div>
</header>
{siblings_html}
<section style="margin-top:var(--s-4)">
<h2 style="font-size:var(--t-lg);margin:0 0 var(--s-2)">Recent merged PRs touching this file</h2>
{empty_note}
<ul class='pr-list'>{pr_lis}</ul>
</section>
<footer class="foot">
<div>vllm-insights &middot; <a href="../">home</a> &middot;
  <a href="../about.html">about</a> &middot; <a href="../feed.xml">Atom</a></div>
</footer>
</main>
</body></html>"""
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
    index_url = f"{base_site}/features/"
    index_html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Feature index — vLLM Insights</title>
<meta name="description" content="Every quantization method, attention backend, parallelism mode, hardware platform, LoRA + spec-decode file in upstream vLLM.">
<link rel="canonical" href="{escape(index_url)}">
<meta property="og:type" content="website">
<meta property="og:title" content="Feature index — vLLM Insights">
<meta property="og:url" content="{escape(index_url)}">
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><rect width='64' height='64' rx='12' fill='%232f6feb'/><text x='32' y='44' text-anchor='middle' font-family='-apple-system,sans-serif' font-size='38' font-weight='700' fill='white'>v</text></svg>">
<style>{page_css}</style>
</head><body>
{topbar}
<main class="page">
<header class="feature-hero">
<nav class="breadcrumbs"><a href="../">Home</a><span class="sep">/</span>
<span aria-current="page">Features</span></nav>
<h1 class="feature-title" style="font-family:inherit">Feature index</h1>
<p class="feature-sub">Every quantization method, attention backend, parallelism mode,
hardware platform, LoRA + spec-decode file in upstream vLLM. Discovered by recursive
git-tree scan — no curation.</p>
</header>
{''.join(sections)}
<footer class="foot">
<div>vllm-insights &middot; <a href="../">home</a> &middot;
  <a href="../about.html">about</a> &middot; <a href="../feed.xml">Atom</a></div>
</footer>
</main></body></html>"""
    (feat_dir / "index.html").write_text(index_html, encoding="utf-8")
    return pages


def _iso_days_ago(days: int) -> str:
    """Return an ISO-ish timestamp `days` days before now. Used for cheap
    string comparisons against merged_at without parsing dates."""
    from datetime import timedelta
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


# ----- About / methodology page ------------------------------------------------

_ABOUT_BODY = """
<h2 id="what">What this is</h2>
<p>vLLM Insights is a derived view of the
<a href="https://github.com/vllm-project/vllm" target="_blank" rel="noopener">vllm-project/vllm</a>
codebase and community. It exists because the canonical signals — what's
supported, what's heating up, what just broke, where to read source — live
across the GitHub repo, the registry file, issues, forks, weekly releases,
and the Hacker News front page. Stitching them together by hand each week
is a chore; this site does it on a cron.</p>

<h2 id="how">How each section is sourced</h2>
<ul>
<li><strong>Latest release verdict</strong> — synthesized from the raw GitHub
release notes following a fixed template (verdict / who-should-upgrade /
likely-to-break / perf and infra). Output is cached per release tag so the
same words don't get re-rolled every cron.</li>
<li><strong>Supported models</strong> — mirrored from upstream
<code>vllm/model_executor/models/registry.py</code> on every cron. Categories
(text, multimodal, embedding, …) come from the upstream dict names; we don't
re-bucket. Arch pills that disappear from the registry are kept with a
strike-through so version drift is visible.</li>
<li><strong>Capability matrix</strong> — every <code>.py</code> file in
<code>vllm/{platforms,distributed,lora,v1/attention/backends,
v1/spec_decode,model_executor/layers/quantization}</code>, discovered via the
GitHub git-tree API. 90-day PR activity per file is joined from the
cached PR data.</li>
<li><strong>Growth over time</strong> — a per-release snapshot of those same
trees, taken by replaying the tree API at each stable-release tag.</li>
<li><strong>Perf claims</strong> — regex over PR titles + bodies for
multipliers / percentages / tok/s, with hardware and model keyword tagging.
These are author-asserted, not measured.</li>
<li><strong>Discovered topics &amp; momentum</strong> — PR and issue text is
indexed into a vector space, then grouped with K-means clustering;
short topic labels are generated automatically from each cluster's
representative members.</li>
<li><strong>Release drift</strong> — GitHub's <code>/compare</code> endpoint
between adjacent stable releases, bucketed by two-segment directory prefix.</li>
<li><strong>Community temperature</strong> — PR reaction counts from the
<code>/issues</code> endpoint (since <code>/pulls</code> doesn't return them
in list responses) + Hacker News mentions via Algolia (no auth required).</li>
<li><strong>Issue hotspots</strong> — open issues with the most distinct
PRs containing a <code>Fixes #N</code> / <code>Closes #N</code> /
<code>Resolves #N</code> reference, weighted by label priority.</li>
<li><strong>Active forks</strong> — every fork above 5 stars, sorted by
<code>ahead_by</code>; top three also list a sample of their unique commits.</li>
</ul>

<h2 id="caveats">What's curated, what's not</h2>
<p>The only hand-curated inputs are:</p>
<ul>
<li>The seven-vendor focus list for the Supported models grid (Qwen, DeepSeek,
MiniMax, GLM, Meta, Google, Microsoft) — the regex rules that map an arch class
back to its vendor live in <code>src/vllm_insights/models.py</code>.</li>
<li>The label set we pull from the Issues feed (performance, regression, RFC,
release-blocker, bug:hardware, bug:rocm, bug:tpu, bug:correctness).</li>
<li>The keyword set for the perf-claim extractor + the hardware / model tag
regexes that decorate it.</li>
</ul>
<p>Everything else — arches, file paths, counts, PR text — is derived. If a
table on this site looks wrong, click through to the GitHub link in the row;
it's the source.</p>

<h2 id="freshness">How fresh is the data?</h2>
<p>The pipeline runs once per hour. End-to-end staleness from upstream event to
homepage is ≤1h 10min (cron + workflow + Pages deploy). Some sections cache
forever per-tag (release verdicts, release diffs) because the underlying data
literally cannot change retroactively.</p>

<h2 id="subscribe">Following</h2>
<p>Subscribe via the
<a href="feed.xml">Atom feed</a> or just watch
<a href="https://github.com/bowensu123/vllm-insights" target="_blank" rel="noopener">
this repo</a> on GitHub. The site has no analytics, no cookies, no login.</p>

<h2 id="bugs">If something looks wrong</h2>
<p>File an issue on
<a href="https://github.com/bowensu123/vllm-insights/issues" target="_blank" rel="noopener">
the source repo</a>. The data pipeline is open; the wrong number is one PR away
from being right.</p>
"""


def build_about_page(docs_dir: Path, *, site_owner: str = "bowensu123") -> Path:
    """Write `docs/about.html` — methodology + caveats + how-to-subscribe."""
    page_css = _shared_page_css()
    topbar_about = """
<div class="topbar"><div class="topbar-inner">
<a class="brand" href="./"><span class="brand-mark">▮</span> vLLM Insights</a>
<nav class="topnav">
  <a href="./#latest-release">Release</a>
  <a href="./#capability">Capability</a>
  <a href="./">Home</a>
  <a href="features/">Features</a>
</nav>
<span class="topbar-spacer"></span>
<a class="tool-btn" href="feed.xml">RSS</a>
<button class="tool-btn" id="theme-toggle" type="button">◐</button>
</div></div>
<script>
(() => {
  const root = document.documentElement;
  const stored = localStorage.getItem('vi-theme');
  if (stored === 'dark' || stored === 'light') root.setAttribute('data-theme', stored);
  const b = document.getElementById('theme-toggle');
  if (b) b.addEventListener('click', () => {
    const cur = root.getAttribute('data-theme') ||
      (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    const next = cur === 'dark' ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    localStorage.setItem('vi-theme', next);
  });
})();
</script>"""
    base_site = _site_base_url(site_owner)
    page_url = f"{base_site}/about.html"
    desc = ("How vLLM Insights derives every section — supported models from "
            "registry.py, capability matrix from the git tree, topics from "
            "embeddings, perf claims from PR text. No curation hidden under "
            "the hood.")
    html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>About &amp; methodology — vLLM Insights</title>
<meta name="description" content="{escape(desc)}">
<link rel="canonical" href="{escape(page_url)}">
<meta property="og:type" content="website">
<meta property="og:title" content="About — vLLM Insights">
<meta property="og:description" content="{escape(desc)}">
<meta property="og:url" content="{escape(page_url)}">
<meta name="twitter:card" content="summary">
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><rect width='64' height='64' rx='12' fill='%232f6feb'/><text x='32' y='44' text-anchor='middle' font-family='-apple-system,sans-serif' font-size='38' font-weight='700' fill='white'>v</text></svg>">
<style>{page_css}
article.about {{ max-width: 70ch; }}
article.about h2 {{ font-size: var(--t-lg); margin-top: var(--s-5); }}
article.about p, article.about li {{ font-size: var(--t-md); color: var(--fg); }}
article.about ul {{ padding-left: 1.4rem; }}
article.about code {{ font-size: 0.85em; }}
</style>
</head><body>
{topbar_about}
<main class="page">
<header class="feature-hero">
<nav class="breadcrumbs"><a href="./">Home</a>
<span class="sep">/</span><span aria-current="page">About</span></nav>
<h1 class="feature-title" style="font-family:inherit">About &amp; methodology</h1>
<p class="feature-sub">How the data on this site is sourced, what's curated, and
how to follow.</p>
</header>
<article class="about">
{_ABOUT_BODY}
</article>
<footer class="foot">
<div>vllm-insights &middot; <a href="./">home</a> &middot;
  <a href="features/">features</a> &middot; <a href="feed.xml">Atom</a></div>
</footer>
</main></body></html>"""
    out = docs_dir / "about.html"
    out.write_text(html, encoding="utf-8")
    return out


def build_sitemap(docs_dir: Path, *, site_owner: str = "bowensu123") -> Path:
    """Generate sitemap.xml listing the homepage, about, features index +
    every per-feature page + the weekly digest archive."""
    base_site = _site_base_url(site_owner)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    urls: list[tuple[str, str, str]] = [
        (f"{base_site}/", today, "hourly"),
        (f"{base_site}/about.html", today, "monthly"),
        (f"{base_site}/features/", today, "daily"),
        (f"{base_site}/weekly/", today, "weekly"),
    ]
    feat_dir = docs_dir / "features"
    if feat_dir.exists():
        for p in sorted(feat_dir.glob("*.html")):
            if p.name == "index.html":
                continue
            urls.append((f"{base_site}/features/{p.name}", today, "weekly"))
    weekly_dir = docs_dir / "weekly"
    if weekly_dir.exists():
        for p in sorted(weekly_dir.glob("*.html"), reverse=True)[:10]:
            urls.append((f"{base_site}/weekly/{p.name}", today, "weekly"))

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url, lastmod, freq in urls:
        lines.append(f"<url><loc>{url}</loc><lastmod>{lastmod}</lastmod>"
                     f"<changefreq>{freq}</changefreq></url>")
    lines.append("</urlset>")
    out = docs_dir / "sitemap.xml"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out
