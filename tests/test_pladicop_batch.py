import json
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from app.db import DB_PATH
from app.pladicop_batch import consolidate

FIXTURES = Path(__file__).parent / 'fixtures' / 'pladicop_pages'


def run(tmp_path, scenario):
    return consolidate(FIXTURES / scenario, tmp_path / 'batch.db', tmp_path / 'reports')


def test_missing_duplicates_and_idempotence(tmp_path):
    first = run(tmp_path, 'missing_duplicates')
    assert first['registros_recibidos'] == 6
    assert first['ids_unicos'] == first['insertados'] == 4
    assert first['duplicados_omitidos'] == 2
    assert first['paginas_observadas'] == [0, 2]
    assert first['huecos_entre_paginas_observadas'] == [[1, 1]]
    assert first['base_paginacion'] == 0
    assert first['hipotesis_paginas_faltantes']['0']['intervalos'] == [[1, 1]]
    assert first['cobertura_estimada_porcentaje'] == pytest.approx(100 * 4 / 6)
    assert len(first['paginas_repetidas']['0']) == 2
    second = run(tmp_path, 'missing_duplicates')
    assert second['insertados'] == second['actualizados'] == 0
    assert second['sin_cambios'] == 4
    with sqlite3.connect(tmp_path / 'batch.db') as conn:
        assert conn.execute('SELECT count(*) FROM pladicop_history').fetchone()[0] == 4
        assert conn.execute('SELECT count(*) FROM pladicop_batch_files').fetchone()[0] == 6
        for entry in first['archivos']:
            assert conn.execute('SELECT original_bytes FROM pladicop_imports WHERE run_id=?', (entry['run_id'],)).fetchone()[0] == Path(entry['archivo']).read_bytes()
        assert conn.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        assert conn.execute('PRAGMA foreign_key_check').fetchall() == []
    saved = tmp_path / 'reports' / ('cobertura_' + first['batch_id'] + '.json')
    assert json.loads(saved.read_text(encoding='utf-8')) == first
    assert saved.with_suffix('.md').exists()


def test_inconsistent_and_uncertain(tmp_path):
    result = run(tmp_path, 'inconsistent')
    assert result['totales_declarados'] == [5, 8]
    assert result['tamanos_de_pagina'] == [2, 3]
    assert result['cobertura_estimada_porcentaje'] is None
    assert result['hipotesis_paginas_faltantes'] == {}
    ambiguous = run(tmp_path, 'ambiguous')
    assert ambiguous['base_paginacion'] is None
    assert ambiguous['hipotesis_paginas_faltantes']['0']['intervalos'] == [[0, 0]]
    assert ambiguous['hipotesis_paginas_faltantes']['1']['intervalos'] == [[3, 3]]


def test_conflicts_do_not_flip_versions(tmp_path):
    for _ in range(2):
        report = run(tmp_path, 'conflict')
        assert report['ids_en_conflicto'] == ['SYNTH-1']
        assert report['rechazados'] == 2
        assert report['actualizados'] == 0
    with sqlite3.connect(tmp_path / 'batch.db') as conn:
        assert conn.execute('SELECT count(*) FROM pladicop_contracts').fetchone()[0] == 2
        assert conn.execute('SELECT count(*) FROM pladicop_history').fetchone()[0] == 2


def test_order_independence_and_update(tmp_path):
    folder = tmp_path / 'pages'
    shutil.copytree(FIXTURES / 'complete', folder)
    first = consolidate(folder, tmp_path / 'batch.db', tmp_path / 'reports')
    assert first['cobertura_estimada_porcentaje'] == 100
    assert first['hipotesis_paginas_faltantes']['0']['intervalos'] == []
    for index, path in enumerate(sorted(folder.glob('*.json'))):
        path.rename(folder / f'reversed_{9-index}.json')
    second = consolidate(folder, tmp_path / 'batch.db', tmp_path / 'reports')
    assert second['sin_cambios'] == 5 and second['actualizados'] == 0
    path = next(folder.glob('*.json'))
    doc = json.loads(path.read_text(encoding='utf-8'))
    doc['data'][0]['fecFinCotizacion'] = '24/10/2026 12:00:00'
    path.write_text(json.dumps(doc), encoding='utf-8')
    changed = consolidate(folder, tmp_path / 'batch.db', tmp_path / 'reports')
    assert changed['actualizados'] == 1 and changed['sin_cambios'] == 4


def test_invalid_input_zero_total_and_excess_ids(tmp_path):
    folder = tmp_path / 'pages'
    folder.mkdir()
    path = folder / 'bad.json'
    path.write_text('{', encoding='utf-8')
    report = consolidate(folder, tmp_path / 'batch.db', tmp_path / 'reports')
    assert report['archivos'][0]['errores']
    assert report['cobertura_estimada_porcentaje'] is None
    path.write_text(json.dumps(dict(data=[], pageable=dict(pageNumber=0, pageSize=2, totalElements=0))), encoding='utf-8')
    empty = consolidate(folder, tmp_path / 'batch.db', tmp_path / 'reports')
    assert empty['ids_unicos'] == 0
    assert empty['cobertura_estimada_porcentaje'] is None
    doc = json.loads((FIXTURES / 'complete' / 'z_page.json').read_text(encoding='utf-8'))
    doc['pageable']['totalElements'] = 1
    path.write_text(json.dumps(doc), encoding='utf-8')
    excess = consolidate(folder, tmp_path / 'batch.db', tmp_path / 'reports')
    assert excess['ids_unicos'] == 2
    assert excess['cobertura_estimada_porcentaje'] is None


def test_production_guard_and_cli(tmp_path):
    before = DB_PATH.read_bytes()
    with pytest.raises(ValueError, match='protegida'):
        consolidate(FIXTURES / 'complete', DB_PATH, tmp_path / 'reports')
    assert DB_PATH.read_bytes() == before
    command = [sys.executable, 'scripts/import_pladicop_folder.py', str(FIXTURES / 'complete'), '--db', str(tmp_path / 'batch.db'), '--report-dir', str(tmp_path / 'reports')]
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['insertados'] == 5


def test_batch_rolls_back_on_database_error(tmp_path):
    from app.pladicop import SCHEMA
    db = tmp_path / 'batch.db'
    with sqlite3.connect(db) as conn:
        conn.executescript(SCHEMA)
        conn.execute("""CREATE TRIGGER fail_insert BEFORE INSERT ON pladicop_contracts
                        WHEN NEW.contract_id='SYNTH-1'
                        BEGIN SELECT RAISE(ABORT, 'test rollback'); END""")
    with pytest.raises(sqlite3.IntegrityError, match='test rollback'):
        consolidate(FIXTURES / 'complete', db, tmp_path / 'reports')
    with sqlite3.connect(db) as conn:
        for table in ('pladicop_contracts', 'pladicop_imports', 'pladicop_history', 'pladicop_batches', 'pladicop_batch_files'):
            assert conn.execute('SELECT count(*) FROM ' + table).fetchone()[0] == 0


def test_metadata_errors_and_independent_gaps(tmp_path):
    folder = tmp_path / 'pages'
    shutil.copytree(FIXTURES / 'missing_duplicates', folder)
    path = folder / 'a_last.json'
    doc = json.loads(path.read_text(encoding='utf-8'))
    doc['pageable']['totalElements'] = 8
    path.write_text(json.dumps(doc), encoding='utf-8')
    report = consolidate(folder, tmp_path / 'batch.db', tmp_path / 'reports')
    assert report['cobertura_estimada_porcentaje'] is None
    assert report['huecos_entre_paginas_observadas'] == [[1, 1]]
    doc['pageable']['pageSize'] = 0
    path.write_text(json.dumps(doc), encoding='utf-8')
    report = consolidate(folder, tmp_path / 'batch.db', tmp_path / 'reports')
    assert report['rechazados'] == 2
    assert report['cobertura_estimada_porcentaje'] is None
