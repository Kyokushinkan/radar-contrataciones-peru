"""Auditoría de capturas locales: no contiene transporte HTTP."""
import hashlib
import json
import math
import sqlite3
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from app.db import DB_PATH, ROOT, connect
from app.pladicop import SCHEMA, LIMA, dumps, strict_object, invalid_constant, validate

BATCH_SCHEMA = '''
CREATE TABLE IF NOT EXISTS pladicop_batches (
 batch_id TEXT PRIMARY KEY, executed_at TEXT NOT NULL, report_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS pladicop_batch_files (
 batch_id TEXT NOT NULL REFERENCES pladicop_batches(batch_id),
 run_id TEXT NOT NULL REFERENCES pladicop_imports(run_id),
 pageable_json TEXT, PRIMARY KEY(batch_id, run_id)
);
'''


def consolidate(folder, db_path, output_dir, *, now=None):
    folder, database, output = (Path(p).resolve() for p in (folder, db_path, output_dir))
    for path in (folder, database, output):
        if not path.is_relative_to(ROOT):
            raise ValueError('Todas las rutas deben permanecer dentro del proyecto')
    if database == DB_PATH.resolve() or (database.exists() and DB_PATH.exists() and database.samefile(DB_PATH)):
        raise ValueError('La base principal está protegida; use una base de pruebas separada')
    if output == folder:
        raise ValueError('Los reportes deben guardarse fuera de la carpeta de entrada')
    paths = sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() == '.json')
    if not paths:
        raise ValueError('No hay archivos JSON en la carpeta')
    now = now or datetime.now(LIMA)
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError('now requiere zona horaria')
    stamp = now.astimezone(LIMA).isoformat()
    report = dict(batch_id=str(uuid4()), ejecutado_en=stamp, archivos=[], registros_recibidos=0,
                  insertados=0, actualizados=0, sin_cambios=0, rechazados=0,
                  duplicados_omitidos=0, advertencias=[])
    files, occurrences, pages = [], defaultdict(list), defaultdict(list)
    totals, sizes = set(), set()
    metadata_complete = True
    for path in paths:
        if not path.resolve().is_relative_to(ROOT):
            raise ValueError('Archivo fuera del proyecto')
        raw = path.read_bytes()
        entry = dict(archivo=str(path), sha256=hashlib.sha256(raw).hexdigest(), run_id=str(uuid4()),
                     pageable=None, registros_recibidos=0, errores=[])
        item = dict(entry=entry, raw=raw, rows=[], valid=[])
        report['archivos'].append(entry)
        files.append(item)
        try:
            doc = json.loads(raw.decode('utf-8-sig'), object_pairs_hook=strict_object, parse_constant=invalid_constant)
            if not isinstance(doc, dict) or not isinstance(doc.get('data'), list):
                raise ValueError('data debe ser una lista')
            item['rows'] = doc['data']
            entry['registros_recibidos'] = len(doc['data'])
            report['registros_recibidos'] += len(doc['data'])
            meta = entry['pageable'] = doc.get('pageable')
            if not isinstance(meta, dict) or any(type(meta.get(k)) is not int or meta[k] < 0 for k in ('pageNumber', 'pageSize', 'totalElements')) or meta['pageSize'] == 0:
                raise ValueError('pageable inválido; pageSize debe ser positivo')
            totals.add(meta['totalElements'])
            sizes.add(meta['pageSize'])
            pages[meta['pageNumber']].append(str(path))
            if len(doc['data']) > meta['pageSize']:
                report['advertencias'].append(f'Más filas que pageSize: {path.name}')
        except (ValueError, UnicodeError) as exc:
            metadata_complete = False
            entry['errores'].append(dict(fila=None, motivo=str(exc)))
        for index, row in enumerate(item['rows'], 1):
            identifier = row.get('idContrato') if isinstance(row, dict) else None
            if type(identifier) in (int, str) and str(identifier).strip():
                occurrences[str(identifier)].append(dict(archivo=str(path), fila=index, payload=dumps(row)))
            try:
                identifier, dates = validate(row)
                if any(e['fila'] is None for e in entry['errores']):
                    raise ValueError('Archivo con metadatos inválidos')
                item['valid'].append((index, identifier, row, dates))
            except ValueError as exc:
                entry['errores'].append(dict(fila=index, motivo=str(exc)))
                report['rechazados'] += 1
    conflicts = {key for key, values in occurrences.items() if len({v['payload'] for v in values}) > 1}
    report['ids_unicos'] = len(occurrences)
    report['ids_repetidos'] = {key: [{k: v for k, v in loc.items() if k != 'payload'} for loc in values] for key, values in occurrences.items() if len(values) > 1}
    report['ids_en_conflicto'] = sorted(conflicts)
    report['paginas_observadas'] = sorted(pages)
    report['huecos_entre_paginas_observadas'] = [
        [left + 1, right - 1]
        for left, right in zip(sorted(pages), sorted(pages)[1:]) if right > left + 1
    ]
    report['paginas_repetidas'] = {str(key): values for key, values in pages.items() if len(values) > 1}
    report['totales_declarados'] = sorted(totals)
    report['tamanos_de_pagina'] = sorted(sizes)
    total = next(iter(totals)) if len(totals) == 1 and metadata_complete else None
    size = next(iter(sizes)) if len(sizes) == 1 and metadata_complete else None
    report['total_consistente'] = total
    report['cobertura_estimada_porcentaje'] = (100 * len(occurrences) / total if total and len(occurrences) <= total else None)
    # Solo se infiere cero con una página cero observada. La ausencia de cero no prueba uno.
    report['base_paginacion'] = 0 if 0 in pages else None
    report['hipotesis_paginas_faltantes'] = {}
    if total is not None and size is not None:
        count = math.ceil(total / size)
        # Intervalos compactos: evita materializar millones de páginas declaradas.
        for base in ([0] if 0 in pages else [0, 1]):
            end = base + count - 1
            observed = sorted(p for p in pages if base <= p <= end)
            cursor, gaps = base, []
            for page in observed:
                if page > cursor:
                    gaps.append([cursor, page - 1])
                cursor = page + 1
            if cursor <= end:
                gaps.append([cursor, end])
            report['hipotesis_paginas_faltantes'][str(base)] = dict(intervalos=gaps, fuera_de_rango=sorted(p for p in pages if not base <= p <= end), paginas_esperadas=count)
    warn = report['advertencias']
    if not metadata_complete: warn.append('Hay archivos ilegibles o metadatos inválidos; cobertura no estimable.')
    if len(totals) > 1: warn.append('totalElements contradictorio; cobertura no estimable.')
    if len(sizes) > 1: warn.append('pageSize contradictorio; no se estiman páginas faltantes.')
    if report['base_paginacion'] is None: warn.append('Base de paginación incierta: no se observó página cero; las hipótesis no acreditan el inicio.')
    if report['paginas_repetidas']: warn.append('Hay números de página repetidos; pueden corresponder a capturas diferentes.')
    if report['ids_repetidos']: warn.append('Hay IDs repetidos; los idénticos se consolidan una sola vez.')
    if conflicts: warn.append('IDs con contenido contradictorio excluidos; no se infiere cuál versión es más reciente por nombre u orden de archivo.')
    if report['huecos_entre_paginas_observadas']: warn.append('Hay huecos entre páginas observadas, independientemente de la base de numeración.')
    if report['rechazados']: warn.append('Hay filas inválidas; IDs recibidos no equivale a contratos válidos consolidados.')
    if total is not None and len(occurrences) > total: warn.append('IDs únicos exceden totalElements; cobertura no estimable.')
    if any(h['intervalos'] for h in report['hipotesis_paginas_faltantes'].values()): warn.append('Hay páginas faltantes bajo al menos una hipótesis de numeración.')
    if any(h['fuera_de_rango'] for h in report['hipotesis_paginas_faltantes'].values()): warn.append('Hay páginas fuera del rango esperado bajo al menos una hipótesis.')
    warn.append('Estimación sobre archivos locales: no acredita mismo filtro, instante, exhaustividad del portal ni vigencia. Un 100% de IDs no prueba cobertura completa.')
    conn = connect(database)
    try:
        conn.executescript(SCHEMA + BATCH_SCHEMA)
        with conn:
            conn.execute('INSERT INTO pladicop_batches VALUES(?,?,?)', (report['batch_id'], stamp, '{}'))
            for item in files:
                entry = item['entry']
                conn.execute('INSERT INTO pladicop_imports VALUES(?,?,?,?,?,?)', (entry['run_id'], entry['archivo'], entry['sha256'], item['raw'], stamp, dumps(entry)))
                conn.execute('INSERT INTO pladicop_batch_files VALUES(?,?,?)', (report['batch_id'], entry['run_id'], dumps(entry['pageable'])))
                for error in entry['errores']:
                    row = item['rows'][error['fila'] - 1] if error['fila'] else None
                    conn.execute('INSERT INTO pladicop_rejections(run_id,row_number,reason,payload_json) VALUES(?,?,?,?)', (entry['run_id'], error['fila'], error['motivo'], dumps(row)))
            selected = set()
            for item in files:
                run = item['entry']['run_id']
                for index, identifier, row, dates in item['valid']:
                    payload = dumps(row)
                    if identifier in conflicts:
                        report['rechazados'] += 1
                        conn.execute('INSERT INTO pladicop_rejections(run_id,row_number,reason,payload_json) VALUES(?,?,?,?)', (run, index, 'ID con versiones contradictorias en el lote', payload))
                        continue
                    if identifier in selected:
                        report['duplicados_omitidos'] += 1
                        continue
                    selected.add(identifier)
                    normalized = dumps(dates)
                    digest = hashlib.sha256(payload.encode('utf-8')).hexdigest()
                    previous = conn.execute("SELECT payload_sha256 FROM pladicop_contracts WHERE source='PLADICOP' AND contract_id=?", (identifier,)).fetchone()
                    outcome = 'insertados' if previous is None else ('sin_cambios' if previous[0] == digest else 'actualizados')
                    report[outcome] += 1
                    conn.execute('''INSERT INTO pladicop_contracts VALUES('PLADICOP',?,?,?,?,?,?)
                        ON CONFLICT(source,contract_id) DO UPDATE SET payload_json=excluded.payload_json,
                        normalized_dates_json=excluded.normalized_dates_json,payload_sha256=excluded.payload_sha256,
                        last_run=excluded.last_run''', (identifier, payload, normalized, digest, run, run))
                    if outcome != 'sin_cambios':
                        conn.execute('''INSERT INTO pladicop_history(source,contract_id,run_id,payload_json,normalized_dates_json,payload_sha256)
                            VALUES('PLADICOP',?,?,?,?,?)''', (identifier, run, payload, normalized, digest))
            report['ids_consolidados'] = len(selected)
            report['integridad_sqlite'] = [r[0] for r in conn.execute('PRAGMA integrity_check')]
            report['errores_claves_foraneas'] = conn.execute('PRAGMA foreign_key_check').fetchall()
            if report['integridad_sqlite'] != ['ok'] or report['errores_claves_foraneas']:
                raise sqlite3.IntegrityError('Falló integridad SQLite')
            conn.execute('UPDATE pladicop_batches SET report_json=? WHERE batch_id=?', (dumps(report), report['batch_id']))
    finally:
        conn.close()
    output.mkdir(parents=True, exist_ok=True)
    stem = output / ('cobertura_' + report['batch_id'])
    stem.with_suffix('.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    lines = ['# Cobertura local PLADICOP', '', f'Ejecución: {stamp}', '', '| Métrica | Valor |', '|---|---|']
    for key in ('registros_recibidos', 'ids_unicos', 'ids_consolidados', 'paginas_observadas', 'total_consistente', 'cobertura_estimada_porcentaje', 'insertados', 'actualizados', 'sin_cambios', 'rechazados', 'duplicados_omitidos'):
        lines.append(f'| {key} | {report[key]} |')
    lines += ['', '## Advertencias', ''] + ['- ' + warning for warning in warn]
    lines += ['', '## Huecos entre páginas observadas (intervalos inclusivos)', '', dumps(report['huecos_entre_paginas_observadas']), '', '## Páginas faltantes por hipótesis (intervalos inclusivos)', '', dumps(report['hipotesis_paginas_faltantes']), '', '## Procedencia', '']
    lines += [f'- `{e["archivo"]}`; SHA-256 `{e["sha256"]}`; pageable: `{dumps(e["pageable"])}`' for e in report['archivos']]
    stem.with_suffix('.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return report
