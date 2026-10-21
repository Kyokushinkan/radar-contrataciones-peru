import json
from pathlib import Path
from datetime import datetime, timezone
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.db import connect, initialize
ROOT = Path(__file__).resolve().parents[1]
sources = json.loads((ROOT / 'config' / 'sources.json').read_text(encoding='utf-8'))
initialize()
with connect() as conn:
    for source in sources:
        conn.execute('INSERT INTO sources(id,name,url,method,status,checked_at) VALUES(?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,url=excluded.url,method=excluded.method,status=excluded.status', (source['id'],source['name'],source['url'],source['method'],source['status'],None))
report = {'generated_at': datetime.now(timezone.utc).isoformat(), 'note':'Inventario de fuentes. No implica verificación de conectividad en tiempo real.', 'sources':sources}
out = ROOT / 'data' / 'processed' / 'source_audit.json'
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(f"SOURCE_COUNT={len(sources)}")
print(f"REPORT={out}")
for s in sources: print(f"{s['id'].upper()}={s['status']}")
