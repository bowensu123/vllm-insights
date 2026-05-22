import sqlite3
from contextlib import contextmanager
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS releases (
    tag             TEXT PRIMARY KEY,
    name            TEXT,
    published_at    TEXT NOT NULL,
    is_prerelease   INTEGER NOT NULL DEFAULT 0,
    body            TEXT,
    url             TEXT
);

CREATE TABLE IF NOT EXISTS release_sections (
    tag             TEXT NOT NULL,
    section         TEXT NOT NULL,
    item            TEXT NOT NULL,
    PRIMARY KEY (tag, section, item),
    FOREIGN KEY (tag) REFERENCES releases(tag)
);

CREATE TABLE IF NOT EXISTS pull_requests (
    number          INTEGER PRIMARY KEY,
    title           TEXT NOT NULL,
    state           TEXT NOT NULL,           -- OPEN / CLOSED / MERGED
    author          TEXT,
    created_at      TEXT NOT NULL,
    merged_at       TEXT,
    closed_at       TEXT,
    additions       INTEGER,
    deletions       INTEGER,
    changed_files   INTEGER,
    labels          TEXT,                    -- comma-separated
    url             TEXT
);

CREATE INDEX IF NOT EXISTS idx_pr_created ON pull_requests(created_at);
CREATE INDEX IF NOT EXISTS idx_pr_merged  ON pull_requests(merged_at);

-- release_tag is the first release whose published_at >= pr.merged_at (set by link_prs_to_releases)

CREATE TABLE IF NOT EXISTS commits (
    sha             TEXT PRIMARY KEY,
    author          TEXT,
    author_email    TEXT,
    committed_at    TEXT NOT NULL,
    message         TEXT,
    url             TEXT
);

CREATE INDEX IF NOT EXISTS idx_commit_date ON commits(committed_at);

CREATE TABLE IF NOT EXISTS pr_files (
    pr_number       INTEGER NOT NULL,
    path            TEXT NOT NULL,
    additions       INTEGER,
    deletions       INTEGER,
    PRIMARY KEY (pr_number, path),
    FOREIGN KEY (pr_number) REFERENCES pull_requests(number)
);

CREATE TABLE IF NOT EXISTS release_summaries (
    tag             TEXT PRIMARY KEY,
    summary         TEXT NOT NULL,
    model           TEXT,
    backend         TEXT,
    generated_at    TEXT NOT NULL,
    FOREIGN KEY (tag) REFERENCES releases(tag)
);

CREATE TABLE IF NOT EXISTS sync_state (
    entity          TEXT PRIMARY KEY,        -- 'releases' | 'prs' | 'commits' | 'registry'
    last_synced_at  TEXT NOT NULL,
    cursor          TEXT
);

-- Snapshot of vllm/model_executor/models/registry.py parsed from upstream main.
-- One row per architecture-class entry across all internal dicts. We re-sync this
-- on every run; rows missing from a fresh fetch get `removed_at` set instead of
-- being deleted, so we can spot drops between vLLM versions.
CREATE TABLE IF NOT EXISTS model_registry (
    arch_class      TEXT PRIMARY KEY,        -- e.g. 'Qwen3MoeForCausalLM'
    category        TEXT NOT NULL,           -- 'text' | 'multimodal' | 'embedding' | 'classification' | 'reward' | 'speculative' | 'transcription'
    module_name     TEXT,                    -- e.g. 'qwen3_moe'
    impl_class      TEXT,                    -- e.g. 'Qwen3MoeForCausalLM' (often == arch_class)
    first_seen_at   TEXT NOT NULL,
    last_seen_at    TEXT NOT NULL,
    removed_at      TEXT                     -- non-NULL if no longer present upstream
);

CREATE INDEX IF NOT EXISTS idx_reg_cat ON model_registry(category);

-- Inventory of feature implementations discovered by scanning vLLM source.
-- Each row is a file or class that implements a feature (a quantization method,
-- attention backend, hardware platform, parallelism mode, spec-decode method).
-- We deliberately don't store a maturity label here — we only show that the
-- file exists in upstream + when it was last touched + recent PR activity.
CREATE TABLE IF NOT EXISTS source_inventory (
    kind            TEXT NOT NULL,       -- 'quantization' | 'platform' | 'attention' | 'parallel' | 'spec_decode' | 'lora' | 'kernel'
    name            TEXT NOT NULL,       -- e.g. 'fp8', 'awq_marlin', 'cuda', 'rocm', 'ngram'
    source_path     TEXT NOT NULL,       -- e.g. 'vllm/model_executor/layers/quantization/fp8.py'
    source_sha      TEXT,                -- the SHA the path was discovered at
    last_seen_at    TEXT NOT NULL,
    PRIMARY KEY (kind, name, source_path)
);

CREATE INDEX IF NOT EXISTS idx_src_kind ON source_inventory(kind);
CREATE INDEX IF NOT EXISTS idx_src_path ON source_inventory(source_path);

-- GitHub Issues — separate from PRs because the activity profile is different.
-- We only sync issues carrying a label we care about (performance, regression,
-- rfc, bug:*, etc.) to avoid pulling tens of thousands of feature-requests.
CREATE TABLE IF NOT EXISTS issues (
    number          INTEGER PRIMARY KEY,
    title           TEXT NOT NULL,
    state           TEXT NOT NULL,        -- OPEN / CLOSED
    author          TEXT,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    closed_at       TEXT,
    labels          TEXT,                 -- comma-separated
    url             TEXT,
    comments        INTEGER
);

CREATE INDEX IF NOT EXISTS idx_issue_updated ON issues(updated_at);
CREATE INDEX IF NOT EXISTS idx_issue_state ON issues(state);
"""


@contextmanager
def connect(db_path: Path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: Path) -> None:
    with connect(db_path) as conn:
        conn.executescript(SCHEMA)
        # Idempotent migrations
        cols = {r["name"] for r in conn.execute("PRAGMA table_info(pull_requests)").fetchall()}
        if "release_tag" not in cols:
            conn.execute("ALTER TABLE pull_requests ADD COLUMN release_tag TEXT")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_pr_release ON pull_requests(release_tag)")


def get_sync_state(conn: sqlite3.Connection, entity: str) -> str | None:
    row = conn.execute(
        "SELECT last_synced_at FROM sync_state WHERE entity = ?", (entity,)
    ).fetchone()
    return row["last_synced_at"] if row else None


def set_sync_state(conn: sqlite3.Connection, entity: str, ts: str) -> None:
    conn.execute(
        """INSERT INTO sync_state(entity, last_synced_at) VALUES(?, ?)
           ON CONFLICT(entity) DO UPDATE SET last_synced_at = excluded.last_synced_at""",
        (entity, ts),
    )
