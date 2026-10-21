from pathlib import Path
from app.db import initialize, connect

def test_schema(tmp_path: Path):
    db = tmp_path / 'test.sqlite3'
    initialize(db)
    with connect(db) as conn:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {'sources', 'entities', 'records', 'ingestion_runs'} <= tables
