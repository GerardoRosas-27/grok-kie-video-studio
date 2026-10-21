-- Se ejecuta sola en el primer arranque local. CREATE IF NOT EXISTS no borra datos.

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    machine TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    title TEXT NOT NULL,
    state TEXT NOT NULL,
    error TEXT NOT NULL DEFAULT '',
    files_json TEXT NOT NULL DEFAULT '[]',
    folder TEXT NOT NULL DEFAULT '',
    inputs_json TEXT NOT NULL DEFAULT '{}',
    result_json TEXT,
    credits REAL NOT NULL DEFAULT 0,
    usd REAL NOT NULL DEFAULT 0,
    provider TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE INDEX IF NOT EXISTS jobs_session_idx ON jobs(session_id, created_at);
