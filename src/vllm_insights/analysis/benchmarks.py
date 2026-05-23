"""Best-effort scraper for vLLM's perf-benchmark CI artifacts.

vLLM publishes benchmark results from CI in a few different shapes (JSON
files dropped as GitHub Actions artifacts, files committed to the repo,
buildkite output). We can only reach GitHub Actions artifacts from this
side; buildkite would need a separate API key and is out of scope.

What this module does, in order:

  1. Discover candidate perf workflows by listing `.github/workflows/` and
     keeping files whose name contains a keyword like `perf`, `bench`, or
     `benchmark`.
  2. For each discovered workflow, fetch the most recent N successful runs
     on `main`.
  3. For each run, list artifacts and download those whose name looks like
     it carries metric data (json / csv / .md ending).
  4. Try to parse the artifact as JSON, then as CSV. If we recognise the
     shape — a list/dict with `throughput`-like or `latency`-like keys — we
     emit rows into the `benchmarks` table. If we don't, we still log the
     artifact's existence so the UI can show "we saw N artifacts but couldn't
     parse them" rather than silently failing.

This is intentionally tolerant: upstream changes their CI structure several
times a year, and the right behaviour is "ingest what we recognise, surface
the rest as known-unknown" rather than crashing.
"""
from __future__ import annotations

import csv
import io
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from rich.console import Console

from ..db import connect, set_sync_state
from ..github import GitHubClient

console = Console()


_PERF_WORKFLOW_KW = re.compile(r"perf|bench", re.IGNORECASE)

# Metric keys we recognise. The key is what shows up in the benchmarks table;
# values are regex patterns that match upstream's various naming conventions
# (throughput_tps, tokens_per_second, output_throughput, …). Order matters
# only for tie-breaking.
_METRIC_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("throughput_tps",
        re.compile(r"^(?:output_)?throughput(?:_tps|_tok|_tokens)?(?:_per_sec)?$", re.I)),
    ("requests_per_sec",
        re.compile(r"^(?:request|requests|qps).*per.*sec", re.I)),
    ("latency_p50_ms",
        re.compile(r"^(?:median_)?(?:itl|tpot|latency)_(?:median|p50)(?:_ms|_s)?$", re.I)),
    ("latency_p99_ms",
        re.compile(r"^(?:itl|tpot|latency)_p99(?:_ms|_s)?$", re.I)),
    ("ttft_p50_ms",
        re.compile(r"^ttft_(?:median|p50)(?:_ms|_s)?$", re.I)),
    ("ttft_p99_ms",
        re.compile(r"^ttft_p99(?:_ms|_s)?$", re.I)),
]


def _classify_metric(key: str) -> str | None:
    for name, pat in _METRIC_PATTERNS:
        if pat.match(key):
            return name
    return None


def _guess_hardware(blob: dict | None, filename: str) -> str:
    """Best-effort hardware tag. Looks at the artifact name, then any
    likely fields in the JSON envelope."""
    candidates: list[str] = [filename]
    if isinstance(blob, dict):
        for k in ("hardware", "gpu", "device", "instance_type", "platform"):
            v = blob.get(k)
            if isinstance(v, str):
                candidates.append(v)
    text = " ".join(candidates).lower()
    for tag in ("h200", "h100", "b200", "mi300x", "mi300", "mi250",
                "tpu", "trainium", "xpu", "cpu"):
        if tag in text:
            return tag.upper().replace("X", "x") if tag.endswith("x") else tag.upper()
    return "unknown"


def _guess_workload(blob: dict | None, filename: str) -> str:
    """Best-effort workload tag (e.g. 'llama3-70b-fp8')."""
    candidates: list[str] = [filename]
    if isinstance(blob, dict):
        for k in ("workload", "model", "test_name", "scenario"):
            v = blob.get(k)
            if isinstance(v, str):
                candidates.append(v)
    text = " ".join(candidates).lower()
    # Best-effort: strip extension, drop obvious dates
    base = filename.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    base = re.sub(r"-?\d{8}", "", base)
    return base or "unknown"


def _parse_artifact_zip(zip_bytes: bytes) -> Iterable[dict]:
    """Yield candidate metric rows from a benchmark artifact zip."""
    try:
        zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    except zipfile.BadZipFile:
        return
    for name in zf.namelist():
        if name.endswith("/"):
            continue
        lname = name.lower()
        if not (lname.endswith(".json") or lname.endswith(".csv")):
            continue
        try:
            raw = zf.read(name)
        except KeyError:
            continue

        # Try JSON
        if lname.endswith(".json"):
            try:
                data = json.loads(raw.decode("utf-8", errors="replace"))
            except json.JSONDecodeError:
                continue
            yield from _rows_from_json(name, data)
            continue

        # Try CSV — each row is one observation.
        try:
            reader = csv.DictReader(io.StringIO(raw.decode("utf-8", errors="replace")))
        except Exception:  # noqa: BLE001
            continue
        for row in reader:
            yield from _rows_from_csv(name, row)


def _rows_from_json(filename: str, data) -> Iterable[dict]:
    """Walk a JSON blob looking for recognisable metric keys."""
    # Flat dict of metrics
    if isinstance(data, dict):
        for k, v in data.items():
            metric = _classify_metric(k)
            if metric is None or not isinstance(v, (int, float)):
                continue
            yield {
                "workload": _guess_workload(data, filename),
                "hardware": _guess_hardware(data, filename),
                "metric": metric,
                "value": float(v),
                "unit": "",
            }
        # Some workflows emit {"results": [...]} — recurse.
        for k in ("results", "data", "benchmarks", "rows"):
            inner = data.get(k)
            if isinstance(inner, list):
                yield from _rows_from_json(filename, inner)
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                yield from _rows_from_json(filename, item)


def _rows_from_csv(filename: str, row: dict) -> Iterable[dict]:
    workload = row.get("workload") or row.get("model") or _guess_workload(None, filename)
    hardware = row.get("hardware") or row.get("gpu") or _guess_hardware(None, filename)
    for k, v in row.items():
        if not isinstance(v, str) or v == "":
            continue
        metric = _classify_metric(k)
        if metric is None:
            continue
        try:
            val = float(v)
        except ValueError:
            continue
        yield {
            "workload": workload, "hardware": hardware,
            "metric": metric, "value": val, "unit": "",
        }


def discover_perf_workflows(client: GitHubClient) -> list[str]:
    """Return the list of workflow filenames matching perf/bench keywords."""
    files = client.list_workflow_files()
    return [f for f in files if _PERF_WORKFLOW_KW.search(f)]


def sync_benchmarks(
    client: GitHubClient,
    db_path: Path,
    *,
    max_runs_per_workflow: int = 5,
    max_artifacts_per_run: int = 6,
    artifact_size_cap_bytes: int = 8 * 1024 * 1024,   # 8 MB
) -> tuple[int, int]:
    """Best-effort ingest. Returns `(rows_written, artifacts_seen)`.

    Bounded by `max_runs_per_workflow` and `max_artifacts_per_run` so a
    runaway sync can't burn through the daily 5GB artifact-download budget.
    """
    workflows = discover_perf_workflows(client)
    if not workflows:
        console.print("[yellow]No perf-like workflow files found in upstream[/]")
        return 0, 0

    console.print(f"[cyan]Perf workflows discovered:[/] "
                  f"{', '.join(workflows)}")
    now_iso = datetime.now(timezone.utc).isoformat()
    n_rows = 0
    n_arts = 0

    with connect(db_path) as conn:
        for wf in workflows:
            try:
                runs = list(client.list_workflow_runs(wf, status="success", branch="main"))
            except Exception as e:  # noqa: BLE001
                console.print(f"[yellow]list_workflow_runs failed for {wf}:[/] "
                              f"{type(e).__name__}: {e}")
                continue
            for run in runs[:max_runs_per_workflow]:
                run_id = str(run.get("id"))
                head_sha = run.get("head_sha")
                head_branch = run.get("head_branch")
                run_url = run.get("html_url")
                try:
                    artifacts = list(client.list_artifacts(int(run["id"])))
                except Exception as e:  # noqa: BLE001
                    console.print(f"[yellow]list_artifacts failed for run {run_id}:[/] "
                                  f"{type(e).__name__}: {e}")
                    continue

                for art in artifacts[:max_artifacts_per_run]:
                    n_arts += 1
                    if (art.get("size_in_bytes") or 0) > artifact_size_cap_bytes:
                        continue
                    if art.get("expired"):
                        continue
                    try:
                        blob = client.download_artifact(int(art["id"]))
                    except Exception as e:  # noqa: BLE001
                        console.print(f"[yellow]download failed for art {art.get('id')}:[/] "
                                      f"{type(e).__name__}: {e}")
                        continue
                    for row in _parse_artifact_zip(blob):
                        conn.execute(
                            """INSERT OR REPLACE INTO benchmarks(
                                 source, run_id, release_tag, commit_sha,
                                 workload, hardware, metric, value, unit, observed_at)
                               VALUES('github-actions', ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (
                                run_id, None, head_sha,
                                row["workload"], row["hardware"], row["metric"],
                                row["value"], row.get("unit") or "",
                                run.get("created_at") or now_iso,
                            ),
                        )
                        n_rows += 1
        set_sync_state(conn, "benchmarks", now_iso)

    console.print(f"[cyan]Benchmarks:[/] {n_rows} metric row(s) "
                  f"from {n_arts} artifact(s)")
    return n_rows, n_arts


def load_recent_benchmarks(db_path: Path, *, limit: int = 200) -> list[dict]:
    """Most recent benchmark observations across all metrics."""
    with connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM benchmarks ORDER BY observed_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]
