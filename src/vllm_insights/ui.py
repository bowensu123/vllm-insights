"""Shared UI primitives — design tokens, badges, section shells.

This module owns everything the rest of build_site.py is allowed to assume
about styling. The goal is a small, named set of building blocks instead of
ad-hoc inline classes scattered across renderers.

Design tokens (CSS variables):
  --accent             primary accent (links, highlights)
  --bg / --bg-2 / --bg-3  background layers
  --fg / --fg-2 / --fg-3  text layers (decreasing emphasis)
  --border / --border-soft
  --hot / --new / --watch / --derived   semantic signal colors
  --space-1..7         8/12/16/24/32/48/64 px spacing
  --r-sm / --r-md / --r-lg  border radii
  --shadow-1 / --shadow-2

Components (HTML helpers):
  badge(kind, label)               → small chip
  section_shell(...)               → <section> with sticky title, summary line,
                                     collapsible body, anchor link
  status_strip(rows)               → key:value strip used by the hero
"""
from __future__ import annotations

from dataclasses import dataclass
from html import escape


# Tokens — single source of truth. The dark variant flips with [data-theme=dark].
DESIGN_TOKENS_CSS = """
:root {
  /* Palette — light */
  --accent: #2f6feb;
  --accent-soft: rgba(47, 111, 235, 0.12);
  --bg: #fbfbfd;
  --bg-2: #ffffff;
  --bg-3: rgba(127, 127, 127, 0.045);
  --fg: #1d2230;
  --fg-2: #4a5060;
  --fg-3: #8a8f9c;
  --border: rgba(20, 24, 36, 0.10);
  --border-soft: rgba(20, 24, 36, 0.05);

  /* Semantic signals */
  --hot:     #d63a3a;     /* high-activity */
  --hot-bg:  rgba(214, 58, 58, 0.10);
  --new:     #2c8f48;     /* added recently */
  --new-bg:  rgba(44, 143, 72, 0.12);
  --watch:   #b8862b;     /* regression / release-blocker */
  --watch-bg:rgba(184, 134, 43, 0.12);
  --derived: #5468d6;     /* "this is derived" badge */
  --derived-bg: rgba(84, 104, 214, 0.10);

  /* Type scale */
  --t-xs: 0.72rem;
  --t-sm: 0.82rem;
  --t-md: 0.92rem;
  --t-lg: 1.05rem;
  --t-xl: 1.32rem;
  --t-2x: 1.78rem;

  /* Spacing */
  --s-1: 0.5rem;
  --s-2: 0.75rem;
  --s-3: 1rem;
  --s-4: 1.5rem;
  --s-5: 2rem;
  --s-6: 3rem;
  --s-7: 4rem;

  /* Radii */
  --r-sm: 4px;
  --r-md: 8px;
  --r-lg: 12px;

  /* Shadows */
  --shadow-1: 0 1px 2px rgba(0, 0, 0, 0.04), 0 1px 1px rgba(0, 0, 0, 0.03);
  --shadow-2: 0 6px 18px rgba(0, 0, 0, 0.08), 0 2px 4px rgba(0, 0, 0, 0.04);
}

[data-theme="dark"] {
  --bg: #0e1117;
  --bg-2: #161b22;
  --bg-3: rgba(255, 255, 255, 0.035);
  --fg: #e6e8ee;
  --fg-2: #aab1bd;
  --fg-3: #6c727e;
  --border: rgba(255, 255, 255, 0.10);
  --border-soft: rgba(255, 255, 255, 0.05);

  --accent: #58a6ff;
  --accent-soft: rgba(88, 166, 255, 0.15);

  --hot:     #f87171;
  --hot-bg:  rgba(248, 113, 113, 0.14);
  --new:     #4ade80;
  --new-bg:  rgba(74, 222, 128, 0.14);
  --watch:   #fbbf24;
  --watch-bg:rgba(251, 191, 36, 0.14);
  --derived: #93a8f8;
  --derived-bg: rgba(147, 168, 248, 0.14);

  --shadow-1: 0 1px 2px rgba(0, 0, 0, 0.30), 0 1px 1px rgba(0, 0, 0, 0.20);
  --shadow-2: 0 6px 22px rgba(0, 0, 0, 0.40);
}

/* Respect system preference if the user hasn't toggled. */
@media (prefers-color-scheme: dark) {
  :root:not([data-theme]) {
    color-scheme: dark;
  }
}
"""


# ---------------------------------------------------------------------------
# Badge component
# ---------------------------------------------------------------------------
_BADGE_KINDS = {"hot", "new", "watch", "derived", "neutral"}
_BADGE_ICONS = {"hot": "🔥", "new": "🆕", "watch": "⚠️", "derived": "📊", "neutral": ""}


def badge(kind: str, label: str, *, icon: bool = True) -> str:
    """Render a small signal chip. `kind` controls the color; `icon` adds emoji."""
    if kind not in _BADGE_KINDS:
        kind = "neutral"
    ic = _BADGE_ICONS.get(kind, "") if icon else ""
    ic_html = f'<span class="b-ic" aria-hidden="true">{ic}</span> ' if ic else ""
    return (
        f'<span class="b b-{kind}" data-kind="{kind}">'
        f'{ic_html}{escape(label)}'
        f'</span>'
    )


# ---------------------------------------------------------------------------
# Section shell
# ---------------------------------------------------------------------------
@dataclass
class Section:
    """Describes one homepage section."""
    slug: str                # anchor + ToC key, e.g. 'capability'
    title: str               # human title
    icon: str = ""           # emoji shown next to title
    badge_kind: str | None = None
    badge_label: str | None = None
    summary: str = ""        # one-line summary shown when collapsed
    default_open: bool = True
    empty_state: str | None = None  # rendered instead of body if body is empty


def section_shell(s: Section, body_html: str) -> str:
    """Wrap a section's body in our sticky-title + collapsible shell.

    If `body_html` is empty:
      - and `s.empty_state` is set → render the empty-state block
      - else → don't render the section at all (caller would have skipped anyway)
    """
    body = body_html.strip()
    if not body:
        if not s.empty_state:
            return ""
        body = (
            f'<div class="sec-empty">{s.empty_state}</div>'
        )

    badge_html = ""
    if s.badge_kind and s.badge_label:
        badge_html = " " + badge(s.badge_kind, s.badge_label)

    icon_html = f'<span class="sec-icon" aria-hidden="true">{s.icon}</span> ' if s.icon else ""
    summary_html = (
        f'<span class="sec-summary">{escape(s.summary)}</span>'
        if s.summary else ""
    )

    open_attr = " open" if s.default_open else ""
    return f'''
<section class="sec" id="{escape(s.slug)}" data-section="{escape(s.slug)}">
  <details class="sec-d"{open_attr}>
    <summary class="sec-head">
      <h2 class="sec-title">
        {icon_html}{escape(s.title)}{badge_html}
      </h2>
      {summary_html}
      <span class="sec-toggle" aria-hidden="true"></span>
    </summary>
    <div class="sec-body">{body}</div>
  </details>
</section>
'''.strip()


# ---------------------------------------------------------------------------
# Status strip (used by the hero)
# ---------------------------------------------------------------------------
def status_strip(rows: list[tuple[str, str, str | None]]) -> str:
    """Render `[(label, value, hint), ...]` as a single info row."""
    items = []
    for label, value, hint in rows:
        hint_html = (
            f'<span class="ss-hint">{escape(hint)}</span>' if hint else ""
        )
        items.append(
            f'<div class="ss-cell"><span class="ss-l">{escape(label)}</span>'
            f'<span class="ss-v">{escape(value)}</span>{hint_html}</div>'
        )
    return f'<div class="status-strip">{"".join(items)}</div>'


# ---------------------------------------------------------------------------
# Empty-state primitives
# ---------------------------------------------------------------------------
def empty_state(title: str, body: str, *, kind: str = "neutral") -> str:
    """A consistent empty/loading panel."""
    return (
        f'<div class="empty empty-{escape(kind)}">'
        f'<div class="empty-t">{escape(title)}</div>'
        f'<div class="empty-b">{body}</div>'
        f'</div>'
    )


def subscribe_form(username: str) -> str:
    """Buttondown email subscription form. Returns '' if *username* is not set.

    Set the BUTTONDOWN_USERNAME env var to enable. The form posts to Buttondown's
    embed endpoint and opens a confirmation popup so the visitor stays on the page.
    """
    if not username:
        return ""
    action = f"https://buttondown.com/api/emails/embed-subscribe/{escape(username)}"
    popup = f"https://buttondown.com/{escape(username)}"
    return (
        f'<form class="subscribe-form" action="{action}" method="post"'
        f' target="popupwindow" onsubmit="window.open(\'{popup}\',\'popupwindow\')">'
        '<div class="sub-row">'
        '<input class="sub-input" type="email" name="email"'
        ' placeholder="your@email.com" required autocomplete="email"'
        ' aria-label="Email address">'
        '<button class="sub-btn" type="submit">Subscribe</button>'
        '</div>'
        '<p class="sub-hint">Weekly digest &middot; no spam &middot; unsubscribe anytime</p>'
        '</form>'
    )


def progress_bar(label: str, current: int, total: int) -> str:
    """A labelled progress bar used for embedding backfill status etc."""
    pct = 0 if total <= 0 else min(100, int(current / total * 100))
    return (
        '<div class="progress">'
        f'<div class="progress-l">{escape(label)}'
        f'<span class="progress-n">{current:,} / {total:,} '
        f'({pct}%)</span></div>'
        '<div class="progress-bar">'
        f'<div class="progress-fill" style="width:{pct}%"></div>'
        '</div></div>'
    )


# ---------------------------------------------------------------------------
# Page-level CSS for components above
# ---------------------------------------------------------------------------
COMPONENTS_CSS = """
/* Body shell */
html, body { background: var(--bg); color: var(--fg); }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui,
       "Helvetica Neue", Arial, sans-serif; line-height: 1.65;
       margin: 0; padding: 0; font-size: 16px;
       text-rendering: optimizeLegibility; -webkit-font-smoothing: antialiased; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
code { font-family: ui-monospace, SFMono-Regular, "JetBrains Mono", Menlo, Consolas, monospace;
       background: var(--bg-3); padding: 0 0.25rem; border-radius: 4px;
       font-size: 0.85em; }

/* Container */
.page { max-width: 1180px; margin: 0 auto; padding: var(--s-4) var(--s-3) var(--s-7); }
@media (max-width: 760px) { .page { padding: var(--s-3) var(--s-2) var(--s-6); } }

/* Sticky top header */
.topbar { position: sticky; top: 0; z-index: 50;
    background: color-mix(in srgb, var(--bg) 92%, transparent);
    backdrop-filter: saturate(140%) blur(8px);
    -webkit-backdrop-filter: saturate(140%) blur(8px);
    border-bottom: 1px solid var(--border-soft);
}
.topbar-inner { max-width: 1180px; margin: 0 auto;
    display: flex; align-items: center; gap: var(--s-3);
    padding: 0.6rem var(--s-3); }
.brand { font-weight: 700; font-size: var(--t-md); letter-spacing: -0.01em;
    color: var(--fg); display: flex; align-items: center; gap: 0.4rem; }
.brand-mark { color: var(--accent); }
.topnav { display: flex; gap: var(--s-3); margin-left: var(--s-3);
    font-size: var(--t-sm); }
.topnav a { color: var(--fg-2); }
.topnav a:hover { color: var(--fg); text-decoration: none; }
.topbar-spacer { flex: 1; }

/* Hamburger + nav drawer (mobile) */
.topnav-toggle { display: none; background: none; border: 1px solid var(--border);
    color: var(--fg); padding: 0.3rem 0.55rem; border-radius: var(--r-sm);
    font-size: var(--t-sm); cursor: pointer; }
@media (max-width: 760px) {
    .topnav { display: none; }
    .topnav-toggle { display: inline-block; }
    .topnav.open { display: flex; position: absolute; top: 100%; left: 0; right: 0;
        flex-direction: column; align-items: stretch; gap: 0;
        background: var(--bg-2); border-bottom: 1px solid var(--border);
        margin: 0; padding: 0.5rem var(--s-3); box-shadow: var(--shadow-2); }
    .topnav.open a { padding: 0.55rem 0; border-bottom: 1px solid var(--border-soft); }
}

/* Header tools (theme toggle + search + subscribe) */
.tool-btn { background: var(--bg-2); border: 1px solid var(--border);
    color: var(--fg); border-radius: var(--r-sm); padding: 0.3rem 0.55rem;
    font-size: var(--t-sm); cursor: pointer; }
.tool-btn:hover { border-color: var(--accent); }
.search-wrap { position: relative; flex: 0 1 320px; min-width: 0; }
.search-input { width: 100%; box-sizing: border-box;
    background: var(--bg-2); border: 1px solid var(--border);
    color: var(--fg); border-radius: var(--r-sm); padding: 0.35rem 0.7rem;
    font-size: var(--t-sm); }
.search-input::placeholder { color: var(--fg-3); }
.search-input:focus { outline: none; border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--accent-soft); }
.search-results { position: absolute; top: 100%; left: 0; right: 0;
    background: var(--bg-2); border: 1px solid var(--border);
    border-radius: var(--r-md); margin-top: 0.3rem;
    max-height: 70vh; overflow: auto; box-shadow: var(--shadow-2);
    display: none; z-index: 60; }
.search-results.open { display: block; }
.search-results a { display: block; padding: 0.5rem 0.7rem;
    border-bottom: 1px solid var(--border-soft); color: var(--fg); }
.search-results a:hover { background: var(--bg-3); text-decoration: none; }
.search-results .sr-kind { font-size: var(--t-xs); color: var(--fg-3);
    text-transform: uppercase; letter-spacing: 0.04em; margin-right: 0.4rem; }
.search-results .sr-title { color: var(--fg); font-size: var(--t-sm); }
.search-results .sr-empty { padding: 0.7rem; color: var(--fg-3); font-size: var(--t-sm); }
@media (max-width: 760px) { .search-wrap { flex-basis: auto; flex: 1; } }

/* Hero */
.hero { background: linear-gradient(135deg, var(--accent-soft), transparent 60%);
    border: 1px solid var(--border-soft); border-radius: var(--r-lg);
    padding: var(--s-4) var(--s-4) var(--s-3); margin: 0 0 var(--s-5); }
.hero-eyebrow { font-size: var(--t-xs); color: var(--fg-3);
    text-transform: uppercase; letter-spacing: 0.07em; margin: 0 0 0.4rem; }
.hero-title { font-size: var(--t-2x); margin: 0 0 0.7rem; letter-spacing: -0.015em;
    line-height: 1.2; font-weight: 700; }
.hero-body { font-size: var(--t-lg); color: var(--fg-2); margin: 0 0 var(--s-3);
    max-width: 60ch; }
.hero-body p { margin: 0.4rem 0; }
.hero-body strong { color: var(--fg); }

/* Status strip */
.status-strip { display: flex; flex-wrap: wrap; gap: var(--s-3);
    padding: 0.7rem 0; border-top: 1px solid var(--border-soft); margin-top: var(--s-3); }
.ss-cell { display: flex; flex-direction: column; gap: 0.1rem; min-width: 110px; }
.ss-l { font-size: var(--t-xs); color: var(--fg-3);
    text-transform: uppercase; letter-spacing: 0.04em; }
.ss-v { font-size: var(--t-md); color: var(--fg); font-weight: 600; }
.ss-hint { font-size: var(--t-xs); color: var(--fg-3); }

/* Floating ToC */
.toc { position: sticky; top: 4.2rem; align-self: start;
    font-size: var(--t-sm); padding: 0.4rem 0; max-height: calc(100vh - 6rem); overflow: auto; }
.toc h3 { font-size: var(--t-xs); text-transform: uppercase;
    letter-spacing: 0.06em; color: var(--fg-3); margin: 0 0 0.5rem; }
.toc ul { list-style: none; padding: 0; margin: 0; }
.toc li a { display: block; padding: 0.25rem 0.4rem; border-radius: var(--r-sm);
    color: var(--fg-2); border-left: 2px solid transparent; }
.toc li a:hover { background: var(--bg-3); color: var(--fg); text-decoration: none; }
.toc li a.active { color: var(--fg); border-left-color: var(--accent);
    background: var(--accent-soft); }

/* Two-column layout */
.layout { display: grid; grid-template-columns: 210px 1fr; gap: var(--s-5); }
@media (max-width: 980px) { .layout { grid-template-columns: 1fr; }
    .toc { display: none; } }

/* Section shell */
.sec { margin: 0 0 var(--s-4); }
.sec-d {
    background: var(--bg-2); border: 1px solid var(--border-soft);
    border-radius: var(--r-lg); padding: var(--s-3) var(--s-4) var(--s-4);
    box-shadow: var(--shadow-1);
    transition: box-shadow 180ms ease, border-color 180ms ease;
}
.sec-d:hover { box-shadow: var(--shadow-2); border-color: var(--border); }

/* Section summary element: grid — title top-left, description bottom-left, chevron right */
.sec-head {
    cursor: pointer; list-style: none; padding: 0; user-select: none;
    display: grid;
    grid-template-columns: 1fr auto;
    grid-template-areas: "title toggle" "desc  toggle";
    align-items: center;
    gap: 0 var(--s-2);
}
.sec-head::-webkit-details-marker { display: none; }
.sec-title {
    grid-area: title;
    font-size: 1.08rem; margin: 0; font-weight: 700; letter-spacing: -0.01em;
    display: flex; align-items: center; gap: 0.4rem; flex-wrap: wrap;
}
.sec-icon { font-size: 1em; line-height: 1; }
.sec-summary {
    grid-area: desc;
    font-size: var(--t-sm); color: var(--fg-3);
    margin-top: 0.15rem; line-height: 1.4;
}
/* Hide the description when the section is already open — no need to repeat it */
details[open] > summary .sec-summary { display: none; }
.sec-toggle {
    grid-area: toggle;
    color: var(--fg-3); font-size: 1rem;
    transition: transform 200ms ease; align-self: start; margin-top: 0.15rem;
}
.sec-toggle::after { content: '▾'; }
details[open] > .sec-head .sec-toggle,
details[open] > summary.sec-head .sec-toggle { transform: rotate(180deg); }
.sec-body {
    margin-top: var(--s-2);
    padding-top: var(--s-3);
    border-top: 1px solid var(--border-soft);
}
.sec-empty { padding: var(--s-3); color: var(--fg-3); font-size: var(--t-sm);
    background: var(--bg-3); border-radius: var(--r-md); }

/* Empty / progress states */
.empty { padding: var(--s-3); border: 1px dashed var(--border);
    border-radius: var(--r-md); background: var(--bg-3); }
.empty-t { font-size: var(--t-md); color: var(--fg); font-weight: 600;
    margin-bottom: 0.2rem; }
.empty-b { font-size: var(--t-sm); color: var(--fg-2); }
.progress { margin: var(--s-2) 0; }
.progress-l { font-size: var(--t-sm); color: var(--fg-2); display: flex;
    justify-content: space-between; margin-bottom: 0.25rem; }
.progress-n { color: var(--fg-3); font-size: var(--t-xs);
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.progress-bar { height: 6px; background: var(--bg-3); border-radius: 999px;
    overflow: hidden; }
.progress-fill { height: 100%; background: var(--accent); transition: width 400ms; }

/* Badges */
.b { display: inline-flex; align-items: center; gap: 0.3rem;
    padding: 0.1rem 0.5rem; border-radius: 999px;
    font-size: var(--t-xs); font-weight: 600;
    line-height: 1.5; vertical-align: middle; }
.b-ic { font-size: 0.85em; }
.b-hot     { color: var(--hot);     background: var(--hot-bg); }
.b-new     { color: var(--new);     background: var(--new-bg); }
.b-watch   { color: var(--watch);   background: var(--watch-bg); }
.b-derived { color: var(--derived); background: var(--derived-bg); }
.b-neutral { color: var(--fg-2);    background: var(--bg-3); }

/* Utility */
.footnote { font-size: var(--t-xs); color: var(--fg-3); line-height: 1.5; }

/* Footer */
footer.foot { margin-top: var(--s-7); padding-top: var(--s-3);
    border-top: 1px solid var(--border-soft);
    color: var(--fg-3); font-size: var(--t-sm); display: flex;
    justify-content: space-between; flex-wrap: wrap; gap: 0.5rem; }

/* Accessibility */
*:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px;
    overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0; }

/* ── Verdict hero variant ────────────────────────────────────────────────── */
.hero-verdict {
  background: linear-gradient(135deg,
    color-mix(in srgb, var(--accent) 10%, transparent),
    color-mix(in srgb, var(--new) 6%, transparent) 60%,
    transparent);
}
.verdict-eyebrow {
  display: flex; align-items: baseline; gap: .55rem;
  margin: 0 0 .6rem; flex-wrap: wrap;
}
.ver-tag {
  font-size: var(--t-xl); font-weight: 700;
  color: var(--accent);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  letter-spacing: -.02em;
}
.ver-sep { color: var(--fg-3); font-size: var(--t-sm); }
.ver-age { font-size: var(--t-sm); color: var(--fg-3); }
.verdict-q {
  font-size: var(--t-xs); font-weight: 700; letter-spacing: .1em;
  text-transform: uppercase; color: var(--fg-3); margin: 0 0 .35rem;
}
.verdict-headline {
  font-size: clamp(1.35rem, 3.5vw, 2.3rem);
  font-weight: 700; line-height: 1.18; letter-spacing: -.02em;
  color: var(--fg); margin: 0 0 var(--s-3); max-width: 26ch;
}
.verdict-who {
  font-size: var(--t-sm); color: var(--fg-2);
  margin: 0 0 var(--s-3);
}
.verdict-who ul {
  list-style: none; padding: 0; margin: .35rem 0 0;
}
.verdict-who li {
  padding: .2rem 0; display: flex; gap: .4rem;
}
.verdict-who li::before {
  content: "→"; color: var(--accent); flex-shrink: 0;
}

/* Signal chips */
.signal-chips {
  display: flex; flex-wrap: wrap; gap: .45rem; margin: 0 0 var(--s-3);
}
.chip {
  display: inline-flex; align-items: center; gap: .3rem;
  padding: .28rem .75rem; border-radius: 999px;
  font-size: var(--t-xs); font-weight: 600;
  border: 1px solid var(--border); text-decoration: none;
  white-space: nowrap; transition: opacity 120ms;
}
.chip-perf   { color: var(--new);     background: var(--new-bg);     border-color: var(--new); }
.chip-model  { color: var(--derived); background: var(--derived-bg); border-color: var(--derived); }
.chip-watch  { color: var(--watch);   background: var(--watch-bg);   border-color: var(--watch); }
.chip-ok     { color: var(--new);     background: var(--new-bg);     border-color: var(--new); }
.chip-link   { color: var(--fg-2);   background: var(--bg-3);       border-color: var(--border); }
.chip-link:hover { color: var(--accent); border-color: var(--accent); text-decoration: none; opacity: .9; }

/* Email subscription form */
.subscribe-form { margin: var(--s-3) 0 0; }
.sub-row { display: flex; gap: var(--s-2); flex-wrap: wrap; }
.sub-input { flex: 1 1 180px; max-width: 260px; padding: 0.45rem 0.75rem;
    border: 1px solid var(--border); border-radius: var(--r-sm);
    background: var(--bg-2); color: var(--fg); font-size: var(--t-sm); }
.sub-input:focus { outline: none; border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--accent-soft); }
.sub-btn { padding: 0.45rem 1rem; background: var(--accent);
    color: #fff; border: none; border-radius: var(--r-sm);
    font-size: var(--t-sm); font-weight: 600; cursor: pointer; white-space: nowrap; }
.sub-btn:hover { opacity: 0.88; }
.sub-hint { font-size: var(--t-xs); color: var(--fg-3); margin: 0.3rem 0 0; }
"""
