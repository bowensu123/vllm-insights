"""CLI entry: vllm-insights sync / dash / stats"""
import subprocess
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from .config import load_settings
from .db import init_db
from .github import GitHubClient
from .fetcher.releases import sync_releases
from .fetcher.prs import sync_prs
from .fetcher.commits import sync_commits
from .fetcher.issues import sync_issues
from .fetcher.forks import sync_forks
from .fetcher.pr_reactions import sync_pr_reactions
from .analyzer.queries import releases_df, prs_df, commits_df
from .analyzer.linking import link_prs_to_releases
from .analysis.history import sync_history
from .analysis.perf_claims import sync_perf_claims
from .analysis.pr_issue_links import sync_pr_issue_links
from .analysis.release_diff import sync_release_diffs
from .analysis.embeddings import embed_entities
from .analysis.social import sync_hn_mentions
from .analysis.topics import run_clustering
from .analysis.benchmarks import sync_benchmarks
from .report import generate_weekly_digest
from .registry_sync import sync_registry
from .source_scan import sync_source_inventory
from .summarize import summarize_window, summarize_release
from .build_site import build_index, build_report_index
from .feed import build_feed, build_feature_pages, build_about_page, build_sitemap

app = typer.Typer(add_completion=False, help="vLLM GitHub insights CLI")
console = Console()


@app.command()
def sync(
    releases: bool = typer.Option(False, "--releases", help="Sync releases"),
    prs: bool = typer.Option(False, "--prs", help="Sync pull requests (incremental)"),
    commits: bool = typer.Option(False, "--commits", help="Sync commits (incremental)"),
    issues: bool = typer.Option(False, "--issues",
                                help="Sync labelled issues (performance / regression / RFC / …)"),
    forks: bool = typer.Option(False, "--forks",
                               help="Monitor active forks (ahead/behind + unique commits)"),
    reactions: bool = typer.Option(False, "--reactions",
                                   help="Refresh GitHub reaction counts on PRs (👍🚀❤️🎉)"),
    hn: bool = typer.Option(False, "--hn",
                            help="Pull HN mentions of vLLM via algolia.io (no auth)"),
    history: bool = typer.Option(False, "--history",
                                 help="Snapshot per-release inventory (arch, quant, platform, …) "
                                      "for time-series charts"),
    registry: bool = typer.Option(False, "--registry",
                                  help="Mirror upstream vllm/model_executor/models/registry.py"),
    source_scan: bool = typer.Option(False, "--source-scan",
                                     help="Enumerate quant / attention / platform / parallel "
                                          "/ spec-decode / lora files from upstream tree"),
    full: bool = typer.Option(False, "--full", help="Ignore last_synced_at and full-refresh"),
    all_: bool = typer.Option(False, "--all", help="Sync everything"),
):
    """Pull data from GitHub into local SQLite cache."""
    s = load_settings(require_token=True)
    init_db(s.db_path)
    if all_:
        releases = prs = commits = issues = forks = reactions = hn = history = registry = source_scan = True
    if not any((releases, prs, commits, issues, forks, reactions, hn,
                history, registry, source_scan)):
        console.print(
            "[yellow]Pick at least one of --releases / --prs / --commits / --issues "
            "/ --forks / --reactions / --hn / --history / --registry / --source-scan / --all[/]"
        )
        raise typer.Exit(1)

    client = GitHubClient(s.github_token, s.repo)
    try:
        if releases:
            sync_releases(client, s.db_path)
        if prs:
            sync_prs(client, s.db_path, full=full)
        if commits:
            sync_commits(client, s.db_path, full=full)
        if issues:
            sync_issues(client, s.db_path, full=full)
        if reactions:
            sync_pr_reactions(client, s.db_path, full=full)
        if forks:
            sync_forks(client, s.db_path)
        if history:
            sync_history(client, s.db_path)
        if source_scan:
            counts = sync_source_inventory(client, s.db_path)
            total = sum(counts.values())
            console.print(f"[cyan]Source inventory synced:[/] {total} files "
                          f"({', '.join(f'{k}={v}' for k, v in sorted(counts.items()))})")
    finally:
        client.close()
    if hn:
        sync_hn_mentions(s.db_path)
    if registry:
        counts = sync_registry(s.db_path)
        total = sum(counts.values())
        console.print(f"[cyan]Registry synced:[/] {total} arch entries "
                      f"({', '.join(f'{k}={v}' for k, v in sorted(counts.items()))})")
    # Always re-link PRs to releases (cheap)
    if releases or prs:
        link_prs_to_releases(s.db_path)
    console.print("[bold green]Done.[/]")


@app.command()
def analyze(
    pr_issue_links: bool = typer.Option(False, "--pr-issue-links",
                                        help="Mine Fixes/Closes/Resolves links from PR bodies"),
    perf_claims: bool = typer.Option(False, "--perf-claims",
                                     help="Extract author-claimed perf deltas from PR titles+bodies"),
    release_diff: bool = typer.Option(False, "--release-diff",
                                      help="Aggregate release-to-release file drift by directory"),
    embed: bool = typer.Option(False, "--embed",
                               help="OpenAI-embed PR + issue titles/bodies (needs OPENAI_API_KEY)"),
    cluster: bool = typer.Option(False, "--cluster",
                                 help="K-means topic clustering on embedded entities"),
    benchmarks: bool = typer.Option(False, "--benchmarks",
                                    help="Best-effort GH Actions perf artifact scrape (likely empty — see --perf-claims)"),
    all_: bool = typer.Option(False, "--all", help="Run every analysis"),
):
    """Run intelligent analyses over the cached data."""
    s = load_settings(require_token=True)
    init_db(s.db_path)
    if all_:
        pr_issue_links = perf_claims = release_diff = embed = cluster = benchmarks = True
    if not any((pr_issue_links, perf_claims, release_diff, embed, cluster, benchmarks)):
        console.print(
            "[yellow]Pick at least one of --pr-issue-links / --perf-claims / "
            "--release-diff / --embed / --cluster / --benchmarks / --all[/]"
        )
        raise typer.Exit(1)

    if pr_issue_links:
        sync_pr_issue_links(s.db_path)
    if perf_claims:
        sync_perf_claims(s.db_path)

    client: GitHubClient | None = None
    try:
        if release_diff or benchmarks:
            client = GitHubClient(s.github_token, s.repo)
        if release_diff:
            assert client is not None
            sync_release_diffs(client, s.db_path)
        if benchmarks:
            assert client is not None
            sync_benchmarks(client, s.db_path)
    finally:
        if client is not None:
            client.close()

    if embed:
        for kind in ("pr", "issue"):
            n = embed_entities(s.db_path, kind)
            console.print(f"[cyan]Embedded {kind}:[/] {n} new vector(s)")

    if cluster:
        for kind in ("pr", "issue"):
            rid = run_clustering(s.db_path, kind)
            if rid:
                console.print(f"[cyan]Clustered {kind}:[/] run={rid}")

    console.print("[bold green]Done.[/]")


@app.command()
def link():
    """Re-link merged PRs to the first release that included them."""
    s = load_settings()
    init_db(s.db_path)
    link_prs_to_releases(s.db_path)


@app.command()
def digest(
    out: Path = typer.Option(Path("docs/weekly/latest.md"), "--out",
                             help="Output markdown path"),
    days: int = typer.Option(7, "--days", help="Window in days"),
    llm: bool = typer.Option(True, "--llm/--no-llm", help="Include the LLM themed digest"),
    backend: str = typer.Option(None, "--backend", help="github | anthropic"),
    model: str = typer.Option(None, "--model"),
):
    """Generate a weekly themed digest under docs/weekly/.

    Replaces the old `report` command which produced a noisy daily file with
    duplicated stats tables. The new digest is theme-sliced (Kernels,
    Quantization, Parallelism, …) at the top, then a release list, then a
    collapsed raw PR list.
    """
    s = load_settings()
    init_db(s.db_path)
    text = generate_weekly_digest(
        s.db_path, days=days, repo=s.repo,
        include_llm=llm, llm_backend=backend, llm_model=model,
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    console.print(f"[green]Digest written:[/] {out}")


# Backwards-compat shim: the GH Actions workflow still invokes `report`. Keep
# the old name working so the cron doesn't break mid-rollout.
@app.command()
def report(
    out: Path = typer.Option(Path("docs/weekly/latest.md"), "--out", help="Output markdown path"),
    days: int = typer.Option(7, "--days", help="Window in days"),
    llm: bool = typer.Option(True, "--llm/--no-llm", help="Include LLM digest"),
    llm_days: int = typer.Option(7, "--llm-days", help="(deprecated, ignored)"),
    backend: str = typer.Option(None, "--backend", help="github | anthropic"),
    model: str = typer.Option(None, "--model"),
):
    """Deprecated alias for `digest`. Will be removed once workflow migrates."""
    del llm_days  # accepted for back-compat, ignored
    s = load_settings()
    init_db(s.db_path)
    text = generate_weekly_digest(
        s.db_path, days=days, repo=s.repo,
        include_llm=llm, llm_backend=backend, llm_model=model,
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    console.print(f"[green]Digest written:[/] {out}")


@app.command()
def summarize(
    out: Path = typer.Option(Path("docs/weekly/latest.md"), "--out", help="Output path"),
    days: int = typer.Option(7, "--days", help="Window in days (use 1 for daily digest)"),
    model: str = typer.Option(None, "--model", help="Override default model"),
    backend: str = typer.Option(None, "--backend",
                                help="github | anthropic (default: github if GITHUB_TOKEN set)"),
):
    """LLM-summarize the recent activity window."""
    s = load_settings()
    init_db(s.db_path)
    text = summarize_window(s.db_path, days=days, model=model, backend=backend)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    console.print(f"[green]Summary written:[/] {out}")


@app.command()
def stats():
    """Print quick stats from the cache."""
    s = load_settings()
    init_db(s.db_path)
    rel = releases_df(s.db_path)
    prs = prs_df(s.db_path)
    cm = commits_df(s.db_path)

    t = Table(title="vLLM insights — cache summary")
    t.add_column("Entity"); t.add_column("Count", justify="right"); t.add_column("Latest")
    t.add_row("Releases", str(len(rel)), str(rel["published_at"].max()) if not rel.empty else "—")
    t.add_row("PRs", str(len(prs)), str(prs["created_at"].max()) if not prs.empty else "—")
    t.add_row("Commits", str(len(cm)), str(cm["committed_at"].max()) if not cm.empty else "—")
    console.print(t)


@app.command(name="summarize-release")
def summarize_release_cmd(
    tag: str = typer.Option("latest", "--tag", help="Release tag, or 'latest' for newest stable"),
    backend: str = typer.Option(None, "--backend", help="github | anthropic"),
    model: str = typer.Option(None, "--model"),
    force: bool = typer.Option(False, "--force", help="Re-run LLM even if cached"),
):
    """LLM-summarize a release's notes (cached in SQLite)."""
    s = load_settings()
    init_db(s.db_path)
    real_tag, summary = summarize_release(
        s.db_path, tag=None if tag == "latest" else tag,
        backend=backend, model=model, repo=s.repo, force=force,
    )
    console.print(f"[green]Summary cached for[/] {real_tag}")
    console.print(summary)


@app.command()
def site(
    docs: Path = typer.Option(Path("docs"), "--docs", help="Output directory for static site"),
):
    """Build static HTML dashboard under docs/ for GitHub Pages."""
    s = load_settings()
    init_db(s.db_path)
    idx = build_index(s.db_path, docs, repo=s.repo)
    build_report_index(docs / "reports", "Daily reports (deprecated)")
    build_report_index(docs / "weekly", "Weekly themed digests")
    n_feat = build_feature_pages(s.db_path, docs, repo=s.repo)
    feed_path = build_feed(s.db_path, docs)
    about_path = build_about_page(docs)
    sitemap_path = build_sitemap(docs)
    console.print(f"[green]Site built:[/] {idx}")
    console.print(f"[green]Feature pages:[/] {n_feat} files under {docs}/features/")
    console.print(f"[green]About page:[/] {about_path}")
    console.print(f"[green]Atom feed:[/] {feed_path}")
    console.print(f"[green]Sitemap:[/] {sitemap_path}")


@app.command()
def dash():
    """Launch the Streamlit dashboard."""
    app_path = Path(__file__).with_name("app.py")
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path)], check=False)


if __name__ == "__main__":
    app()
