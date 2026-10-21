from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "radar_contrataciones.sqlite3"
SCHEMA = """
CREATE TABLE IF NOT EXISTS sources (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, url TEXT NOT NULL,
    method TEXT NOT NULL, status TEXT NOT NULL, checked_at TEXT
);
CREATE TABLE IF NOT EXISTS entities (
    entity_id TEXT PRIMARY KEY, ruc TEXT, name TEXT NOT NULL,
    region TEXT, source_id TEXT, UNIQUE(ruc)
);
CREATE TABLE IF NOT EXISTS records (
    record_id TEXT PRIMARY KEY, source_id TEXT NOT NULL,
    source_record_id TEXT NOT NULL, entity_id TEXT,
    record_type TEXT NOT NULL, title TEXT, amount_pen REAL,
    publication_date TEXT, deadline TEXT, status TEXT,
    official_url TEXT, raw_sha256 TEXT, observed_at TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    UNIQUE(source_id, source_record_id, raw_sha256),
    FOREIGN KEY(source_id) REFERENCES sources(id),
    FOREIGN KEY(entity_id) REFERENCES entities(entity_id)
);
CREATE TABLE IF NOT EXISTS ingestion_runs (
    run_id TEXT PRIMARY KEY, source_id TEXT NOT NULL,
    started_at TEXT NOT NULL, finished_at TEXT, result TEXT,
    row_count INTEGER DEFAULT 0, notes TEXT
);
CREATE INDEX IF NOT EXISTS idx_records_entity ON records(entity_id);
CREATE INDEX IF NOT EXISTS idx_records_deadline ON records(deadline);
CREATE INDEX IF NOT EXISTS idx_records_source_type ON records(source_id, record_type);
"""

def connect(path=DB_PATH):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def initialize(path=DB_PATH):
    with connect(path) as conn:
        conn.executescript(SCHEMA)
