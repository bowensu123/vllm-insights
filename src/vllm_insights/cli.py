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
from .analyzer.queries import releases_df, prs_df, commits_df
from .analyzer.linking import link_prs_to_releases
from .report import generate_daily_report
from .summarize import summarize_week
from .build_site import build_index, build_report_index

app = typer.Typer(add_completion=False, help="vLLM GitHub insights CLI")
console = Console()


@app.command()
def sync(
    releases: bool = typer.Option(False, "--releases", help="Sync releases"),
    prs: bool = typer.Option(False, "--prs", help="Sync pull requests (incremental)"),
    commits: bool = typer.Option(False, "--commits", help="Sync commits (incremental)"),
    full: bool = typer.Option(False, "--full", help="Ignore last_synced_at and full-refresh"),
    all_: bool = typer.Option(False, "--all", help="Sync everything"),
):
    """Pull data from GitHub into local SQLite cache."""
    s = load_settings(require_token=True)
    init_db(s.db_path)
    if all_:
        releases = prs = commits = True
    if not (releases or prs or commits):
        console.print("[yellow]Pick at least one of --releases / --prs / --commits / --all[/]")
        raise typer.Exit(1)

    client = GitHubClient(s.github_token, s.repo)
    try:
        if releases:
            sync_releases(client, s.db_path)
        if prs:
            sync_prs(client, s.db_path, full=full)
        if commits:
            sync_commits(client, s.db_path, full=full)
    finally:
        client.close()
    # Always re-link PRs to releases (cheap)
    if releases or prs:
        link_prs_to_releases(s.db_path)
    console.print("[bold green]Done.[/]")


@app.command()
def link():
    """Re-link merged PRs to the first release that included them."""
    s = load_settings()
    init_db(s.db_path)
    link_prs_to_releases(s.db_path)


@app.command()
def report(
    out: Path = typer.Option(Path("reports/daily.md"), "--out", help="Output markdown path"),
    days: int = typer.Option(7, "--days", help="Activity window in days"),
):
    """Generate a markdown activity report."""
    s = load_settings()
    init_db(s.db_path)
    text = generate_daily_report(s.db_path, days=days)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    console.print(f"[green]Report written:[/] {out}")


@app.command()
def summarize(
    out: Path = typer.Option(Path("reports/weekly-summary.md"), "--out", help="Output path"),
    days: int = typer.Option(7, "--days"),
    model: str = typer.Option(None, "--model", help="Override ANTHROPIC_MODEL"),
):
    """LLM-summarize the past week of releases + merged PRs."""
    s = load_settings()
    init_db(s.db_path)
    text = summarize_week(s.db_path, days=days, model=model)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    console.print(f"[green]Weekly summary written:[/] {out}")


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


@app.command()
def site(
    docs: Path = typer.Option(Path("docs"), "--docs", help="Output directory for static site"),
):
    """Build static HTML dashboard under docs/ for GitHub Pages."""
    s = load_settings()
    init_db(s.db_path)
    idx = build_index(s.db_path, docs, repo=s.repo)
    build_report_index(docs / "reports", "Daily activity reports")
    build_report_index(docs / "weekly", "Weekly LLM summaries")
    console.print(f"[green]Site built:[/] {idx}")


@app.command()
def dash():
    """Launch the Streamlit dashboard."""
    app_path = Path(__file__).with_name("app.py")
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path)], check=False)


if __name__ == "__main__":
    app()
