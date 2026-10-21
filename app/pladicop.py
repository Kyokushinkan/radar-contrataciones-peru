"""Importación exclusivamente local; no realiza solicitudes de red."""
import hashlib
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

from app.db import DB_PATH, connect

LIMA = ZoneInfo('America/Lima')
FIELDS = '''secuencia idContrato nroContratacion desContratacion idObjetoContrato
nomObjetoContrato desObjetoContrato nomEtapaContratacion fecIniCotizacion
fecFinCotizacion cotizar idEstadoContrato nomEstadoContrato fecPublica
idTipoCotizacion idCotizacion idEstadoCotiza nomEstadoCotiza nomEntidad
numSubsanacionesTotal numSubsanacionesPendientes fecLimiteSubsanaMax'''.split()
DATES = ('fecIniCotizacion', 'fecFinCotizacion', 'fecPublica', 'fecLimiteSubsanaMax')
SCHEMA = '''
CREATE TABLE IF NOT EXISTS pladicop_imports (
 run_id TEXT PRIMARY KEY, file_path TEXT NOT NULL, file_sha256 TEXT NOT NULL,
 original_bytes BLOB NOT NULL, executed_at TEXT NOT NULL, report_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS pladicop_contracts (
 source TEXT NOT NULL CHECK(source='PLADICOP'), contract_id TEXT NOT NULL,
 payload_json TEXT NOT NULL, normalized_dates_json TEXT NOT NULL,
 payload_sha256 TEXT NOT NULL, first_run TEXT NOT NULL REFERENCES pladicop_imports(run_id),
 last_run TEXT NOT NULL REFERENCES pladicop_imports(run_id),
 PRIMARY KEY(source, contract_id)
);
CREATE TABLE IF NOT EXISTS pladicop_history (
 version_id INTEGER PRIMARY KEY, source TEXT NOT NULL, contract_id TEXT NOT NULL,
 run_id TEXT NOT NULL REFERENCES pladicop_imports(run_id),
 payload_json TEXT NOT NULL, normalized_dates_json TEXT NOT NULL, payload_sha256 TEXT NOT NULL,
 FOREIGN KEY(source, contract_id) REFERENCES pladicop_contracts(source, contract_id)
);
CREATE TABLE IF NOT EXISTS pladicop_rejections (
 rejection_id INTEGER PRIMARY KEY, run_id TEXT NOT NULL REFERENCES pladicop_imports(run_id),
 row_number INTEGER, reason TEXT NOT NULL, payload_json TEXT
);
'''


def dumps(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


def strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'Clave JSON repetida: {key}')
        result[key] = value
    return result


def invalid_constant(value):
    raise ValueError(f'Constante JSON inválida: {value}')


def normalize_date(value):
    if value is None:
        return None
    if not isinstance(value, str) or not re.fullmatch(r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}', value):
        raise ValueError('Fecha debe ser dd/mm/yyyy HH:MM:SS o null')
    parsed = datetime.strptime(value, '%d/%m/%Y %H:%M:%S')
    # Rechazar horas históricas ambiguas o inexistentes, en vez de adivinarlas.
    first = parsed.replace(tzinfo=LIMA, fold=0)
    if first.utcoffset() != parsed.replace(tzinfo=LIMA, fold=1).utcoffset():
        raise ValueError('Hora local ambigua o inexistente en America/Lima')
    return first.isoformat(timespec='seconds')


def validate(row):
    if not isinstance(row, dict):
        raise ValueError('La contratación debe ser un objeto')
    missing = set(FIELDS) - row.keys()
    if missing:
        raise ValueError('Campos ausentes: ' + ', '.join(sorted(missing)))
    identifier = row['idContrato']
    if type(identifier) not in (int, str) or not str(identifier).strip():
        raise ValueError('idContrato debe ser entero o cadena no vacía')
    if row['cotizar'] is not None and type(row['cotizar']) is not bool:
        raise ValueError('cotizar debe ser booleano o null')
    dates = {}
    for field in DATES:
        try:
            dates[field] = normalize_date(row[field])
        except ValueError as exc:
            raise ValueError(f'{field}: {exc}') from exc
    return str(identifier), dates


def import_file(file_path, db_path=DB_PATH, output_dir=None, *, now=None, upcoming_hours=72):
    path = Path(file_path).resolve(strict=True)
    raw = path.read_bytes()
    now = now or datetime.now(LIMA)
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError('now requiere zona horaria')
    if upcoming_hours <= 0:
        raise ValueError('upcoming_hours debe ser positivo')
    now = now.astimezone(LIMA)
    run_id = str(uuid4())
    report = dict(run_id=run_id, fuente='PLADICOP', archivo=str(path),
                  sha256=hashlib.sha256(raw).hexdigest(), ejecutado_en=now.isoformat(),
                  zona_horaria='America/Lima', total_leido=0, insertados=0,
                  actualizados=0, sin_cambios=0, rechazados=0, errores_archivo=[],
                  registros=[], proximos_vencimientos=[], ventana_horas=upcoming_hours,
                  alcance='Solo registros válidos de este archivo; no acredita vigencia ni elegibilidad')
    rows = []
    try:
        document = json.loads(raw.decode('utf-8-sig'), object_pairs_hook=strict_object,
                              parse_constant=invalid_constant)
        if not isinstance(document, dict) or not isinstance(document.get('data'), list):
            raise ValueError('Raíz debe contener data como lista')
        report['total_leido'] = len(document['data'])
        pageable = document.get('pageable')
        if not isinstance(pageable, dict) or any(
            type(pageable.get(k)) is not int or pageable[k] < 0
            for k in ('pageNumber', 'pageSize', 'totalElements')
        ):
            raise ValueError('pageable requiere pageNumber, pageSize y totalElements enteros no negativos')
        report['pageable'] = pageable
        rows = document['data']
    except (ValueError, UnicodeError) as exc:
        report['errores_archivo'].append(str(exc))
        report['rechazados'] = report['total_leido']

    conn = connect(db_path)
    try:
        conn.executescript(SCHEMA)
        with conn:
            conn.execute('INSERT INTO pladicop_imports VALUES(?,?,?,?,?,?)',
                         (run_id, str(path), report['sha256'], raw, now.isoformat(), '{}'))
            for error in report['errores_archivo']:
                conn.execute('INSERT INTO pladicop_rejections(run_id,reason) VALUES(?,?)', (run_id, error))
            seen = set()
            for index, row in enumerate(rows, 1):
                try:
                    identifier, dates = validate(row)
                    if identifier in seen:
                        raise ValueError('idContrato repetido en el archivo')
                    seen.add(identifier)
                except ValueError as exc:
                    report['rechazados'] += 1
                    conn.execute('INSERT INTO pladicop_rejections(run_id,row_number,reason,payload_json) VALUES(?,?,?,?)',
                                 (run_id, index, str(exc), dumps(row)))
                    continue
                payload = dumps(row)
                normalized = dumps(dates)
                digest = hashlib.sha256(payload.encode('utf-8')).hexdigest()
                previous = conn.execute("SELECT payload_sha256 FROM pladicop_contracts WHERE source='PLADICOP' AND contract_id=?", (identifier,)).fetchone()
                outcome = 'insertados' if previous is None else ('sin_cambios' if previous[0] == digest else 'actualizados')
                report[outcome] += 1
                conn.execute('''INSERT INTO pladicop_contracts VALUES('PLADICOP',?,?,?,?,?,?)
                    ON CONFLICT(source,contract_id) DO UPDATE SET payload_json=excluded.payload_json,
                    normalized_dates_json=excluded.normalized_dates_json,payload_sha256=excluded.payload_sha256,
                    last_run=excluded.last_run''', (identifier, payload, normalized, digest, run_id, run_id))
                if outcome != 'sin_cambios':
                    conn.execute('''INSERT INTO pladicop_history(source,contract_id,run_id,payload_json,normalized_dates_json,payload_sha256)
                                    VALUES('PLADICOP',?,?,?,?,?)''', (identifier, run_id, payload, normalized, digest))
                deadline = dates['fecFinCotizacion']
                hours = (datetime.fromisoformat(deadline).timestamp() - now.timestamp()) / 3600 if deadline else None
                item = dict(idContrato=identifier, cierre=deadline, horas_hasta_cierre=hours,
                            estado_temporal='sin_fecha' if hours is None else ('vencido' if hours <= 0 else 'futuro'),
                            cotizar=row['cotizar'], nomEstadoContrato=row['nomEstadoContrato'])
                report['registros'].append(item)
                if hours is not None and 0 < hours <= upcoming_hours:
                    report['proximos_vencimientos'].append(item)
            report['proximos_vencimientos'].sort(key=lambda item: item['horas_hasta_cierre'])
            report['resultado'] = 'archivo_invalido' if report['errores_archivo'] else ('parcial' if report['rechazados'] else 'ok')
            report['integridad_sqlite'] = [r[0] for r in conn.execute('PRAGMA integrity_check')]
            report['errores_claves_foraneas'] = conn.execute('PRAGMA foreign_key_check').fetchall()
            if report['integridad_sqlite'] != ['ok'] or report['errores_claves_foraneas']:
                raise sqlite3.IntegrityError('Falló la verificación de integridad')
            conn.execute('UPDATE pladicop_imports SET report_json=? WHERE run_id=?', (dumps(report), run_id))
    finally:
        conn.close()
    if output_dir is not None:
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        stem = output / f'pladicop_{run_id}'
        stem.with_suffix('.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        lines = ['# Importación local PLADICOP', '', f'Ejecución: {report["ejecutado_en"]}',
                 '', f'Archivo: `{path}`', '', report['alcance'], '', '| Métrica | Total |', '|---|---:|']
        lines += [f'| {key} | {report[key]} |' for key in ('total_leido', 'insertados', 'actualizados', 'sin_cambios', 'rechazados')]
        lines += ['', '## Próximos vencimientos', '', f'Ventana: {upcoming_hours} horas.']
        lines += [f'- {item["idContrato"]}: {item["cierre"]} ({item["horas_hasta_cierre"]:.2f} horas)' for item in report['proximos_vencimientos']]
        if not report['proximos_vencimientos']:
            lines.append('- Ninguno en el archivo.')
        lines += ['', 'Errores de archivo: ' + dumps(report['errores_archivo']), '', 'Integridad SQLite: ok', '']
        stem.with_suffix('.md').write_text('\n'.join(lines), encoding='utf-8')
    return report
