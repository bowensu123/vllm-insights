"""pandas-based aggregations from the SQLite cache."""
from pathlib import Path
import pandas as pd
import sqlite3


def _read(db_path: Path, sql: str, params: tuple = ()) -> pd.DataFrame:
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql_query(sql, conn, params=params)


def releases_df(db_path: Path) -> pd.DataFrame:
    df = _read(db_path, "SELECT tag, name, published_at, is_prerelease, url FROM releases")
    if df.empty:
        return df
    df["published_at"] = pd.to_datetime(df["published_at"], utc=True)
    df = df.sort_values("published_at").reset_index(drop=True)
    df["interval_days"] = df["published_at"].diff().dt.total_seconds() / 86400
    return df


def release_sections_df(db_path: Path) -> pd.DataFrame:
    return _read(db_path, "SELECT tag, section, item FROM release_sections")


def prs_df(db_path: Path) -> pd.DataFrame:
    df = _read(
        db_path,
        "SELECT number,title,state,author,created_at,merged_at,closed_at,"
        "additions,deletions,changed_files,labels,url,release_tag FROM pull_requests",
    )
    if df.empty:
        return df
    for col in ("created_at", "merged_at", "closed_at"):
        df[col] = pd.to_datetime(df[col], utc=True)
    df["merge_hours"] = (df["merged_at"] - df["created_at"]).dt.total_seconds() / 3600
    return df


def commits_df(db_path: Path) -> pd.DataFrame:
    df = _read(db_path, "SELECT sha, author, committed_at, message FROM commits")
    if df.empty:
        return df
    df["committed_at"] = pd.to_datetime(df["committed_at"], utc=True)
    return df


# ---- Tech classification ----

# Order matters: first match wins.
TECH_RULES: list[tuple[str, str]] = [
    ("Attention/Kernel", r"(^|/)(csrc|vllm/attention|vllm/_custom_ops)"),
    ("Model Support",    r"vllm/model_executor/models/"),
    ("Quantization",     r"(quantization|gptq|awq|fp8|int8|int4)"),
    ("Scheduling/Engine",r"vllm/(core|engine|scheduler)"),
    ("Sampling/Logits",  r"vllm/(sampling|logits)"),
    ("Distributed",      r"vllm/(distributed|worker|executor)"),
    ("Hardware-ROCm",    r"(rocm|hip)"),
    ("Hardware-TPU",     r"(tpu|xla)"),
    ("Hardware-CPU",     r"(cpu_executor|cpu_worker)"),
    ("API/Serving",      r"vllm/(entrypoints|api_server|openai)"),
    ("Tests",            r"^tests/"),
    ("CI/Build",         r"(^\.github/|^Dockerfile|^setup\.py|^pyproject\.toml|^requirements)"),
    ("Docs",             r"(^docs/|\.md$)"),
]


def classify_pr_by_title(title: str) -> str:
    import re
    t = (title or "").lower()
    # vLLM convention: [Model], [Kernel], [Bugfix], [Core], [Hardware][AMD]...
    tag_match = re.findall(r"\[([^\]]+)\]", title or "")
    tag_lower = " ".join(x.lower() for x in tag_match)
    if "model" in tag_lower: return "Model Support"
    if "kernel" in tag_lower or "attention" in tag_lower: return "Attention/Kernel"
    if "quant" in tag_lower: return "Quantization"
    if "core" in tag_lower or "engine" in tag_lower or "scheduler" in tag_lower: return "Scheduling/Engine"
    if "hardware" in tag_lower or "rocm" in tag_lower or "amd" in tag_lower: return "Hardware-ROCm"
    if "tpu" in tag_lower: return "Hardware-TPU"
    if "cpu" in tag_lower: return "Hardware-CPU"
    if "frontend" in tag_lower or "api" in tag_lower or "openai" in tag_lower: return "API/Serving"
    if "doc" in tag_lower: return "Docs"
    if "ci" in tag_lower or "build" in tag_lower: return "CI/Build"
    if "bugfix" in tag_lower or "fix" in tag_lower: return "Bugfix"
    if "test" in tag_lower: return "Tests"
    if "perf" in tag_lower or "speedup" in tag_lower: return "Performance"
    # fallback: simple keywords in title
    if "model" in t: return "Model Support"
    if "quant" in t: return "Quantization"
    return "Other"


def pr_tech_distribution(db_path: Path, since: str | None = None) -> pd.DataFrame:
    df = prs_df(db_path)
    if df.empty:
        return df
    if since:
        df = df[df["created_at"] >= pd.Timestamp(since, tz="UTC")]
    df["tech"] = df["title"].apply(classify_pr_by_title)
    return df


def merge_time_stats(df: pd.DataFrame) -> pd.DataFrame:
    merged = df.dropna(subset=["merged_at"]).copy()
    if merged.empty:
        return pd.DataFrame()
    merged["month"] = merged["merged_at"].dt.to_period("M").astype(str)
    g = merged.groupby("month")["merge_hours"].agg(["median", "mean", "count"]).reset_index()
    return g
