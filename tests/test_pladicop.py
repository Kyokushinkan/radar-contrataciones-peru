import json
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pytest

from app.pladicop import LIMA, import_file, normalize_date

FIXTURE = Path(__file__).parent / 'fixtures' / 'pladicop_five.json'
NOW = datetime(2026, 10, 20, 12, tzinfo=LIMA)


def test_import_idempotence_update_and_provenance(tmp_path):
    db = tmp_path / 'test.db'
    report = import_file(FIXTURE, db, tmp_path / 'reports', now=NOW)
    assert [report[k] for k in ('total_leido', 'insertados', 'actualizados', 'sin_cambios', 'rechazados')] == [5, 5, 0, 0, 0]
    assert [r['horas_hasta_cierre'] for r in report['registros']] == [1, -24, None, 72, 240]
    assert [r['idContrato'] for r in report['proximos_vencimientos']] == ['SYNTH-1', 'SYNTH-4']
    assert report['registros'][0]['cotizar'] is False
    second = import_file(FIXTURE, db, now=NOW)
    assert second['sin_cambios'] == 5
    assert second['insertados'] == second['actualizados'] == 0
    doc = json.loads(FIXTURE.read_text(encoding='utf-8'))
    doc['data'][0]['fecFinCotizacion'] = '21/10/2026 12:00:00'
    changed = tmp_path / 'changed.json'
    changed.write_text(json.dumps(doc), encoding='utf-8')
    third = import_file(changed, db, now=NOW)
    assert third['actualizados'] == 1 and third['sin_cambios'] == 4
    assert third['registros'][0]['horas_hasta_cierre'] == 24
    # Reversión es una nueva versión aunque su hash ya haya existido.
    assert import_file(FIXTURE, db, now=NOW)['actualizados'] == 1
    with sqlite3.connect(db) as conn:
        assert conn.execute('SELECT count(*) FROM pladicop_contracts').fetchone()[0] == 5
        assert conn.execute('SELECT count(*) FROM pladicop_history').fetchone()[0] == 7
        assert conn.execute('SELECT original_bytes FROM pladicop_imports WHERE run_id=?', (report['run_id'],)).fetchone()[0] == FIXTURE.read_bytes()
        assert conn.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        assert conn.execute('PRAGMA foreign_key_check').fetchall() == []
    saved = next((tmp_path / 'reports').glob('*.json'))
    assert json.loads(saved.read_text(encoding='utf-8')) == report
    assert saved.with_suffix('.md').exists()


@pytest.mark.parametrize('raw', ['{', '{"data":[]}', '{"data":[],"data":[]}', '{"data":[NaN]}', '[]'])
def test_invalid_json_or_envelope(tmp_path, raw):
    path = tmp_path / 'invalid.json'
    path.write_text(raw, encoding='utf-8')
    report = import_file(path, tmp_path / 'db', tmp_path / 'reports', now=NOW)
    assert report['resultado'] == 'archivo_invalido'
    assert report['errores_archivo']
    assert report['insertados'] == 0
    with sqlite3.connect(tmp_path / 'db') as conn:
        assert conn.execute('SELECT count(*) FROM pladicop_rejections').fetchone()[0] == 1


def test_invalid_records_and_duplicate(tmp_path):
    doc = json.loads(FIXTURE.read_text(encoding='utf-8'))
    doc['data'][1]['fecFinCotizacion'] = '31/02/2026 10:00:00'
    doc['data'][2]['idContrato'] = None
    doc['data'][3]['idContrato'] = 'SYNTH-1'
    del doc['data'][4]['cotizar']
    path = tmp_path / 'rows.json'
    path.write_text(json.dumps(doc), encoding='utf-8')
    report = import_file(path, tmp_path / 'db', now=NOW)
    assert report['insertados'] == 1 and report['rechazados'] == 4
    assert report['resultado'] == 'parcial'
    with sqlite3.connect(tmp_path / 'db') as conn:
        assert conn.execute('SELECT count(*) FROM pladicop_rejections').fetchone()[0] == 4


def test_dates_and_current_time(tmp_path):
    assert normalize_date(None) is None
    assert normalize_date('20/10/2026 09:30:15') == '2026-10-20T09:30:15-05:00'
    assert normalize_date('29/02/2024 00:00:00') == '2024-02-29T00:00:00-05:00'
    for invalid in ('29/02/2025 00:00:00', '', '2026-10-20', '20/10/2026 24:00:00', 123):
        with pytest.raises(ValueError):
            normalize_date(invalid)
    later = datetime(2026, 10, 31, 12, tzinfo=LIMA)
    report = import_file(FIXTURE, tmp_path / 'db', now=later)
    assert report['proximos_vencimientos'] == []
    assert report['registros'][0]['estado_temporal'] == 'vencido'


def test_cli(tmp_path):
    command = [sys.executable, 'scripts/import_pladicop.py', str(FIXTURE), '--db', str(tmp_path / 'db'), '--report-dir', str(tmp_path / 'reports')]
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['insertados'] == 5
    invalid = tmp_path / 'bad.json'
    invalid.write_text('{', encoding='utf-8')
    command[2] = str(invalid)
    assert subprocess.run(command, capture_output=True).returncode == 1
