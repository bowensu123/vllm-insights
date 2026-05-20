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
    entity          TEXT PRIMARY KEY,        -- 'releases' | 'prs' | 'commits'
    last_synced_at  TEXT NOT NULL,
    cursor          TEXT
);
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
