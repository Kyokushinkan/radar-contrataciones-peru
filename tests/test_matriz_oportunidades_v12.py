import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import pytest

from app.matriz_oportunidades_v12 import PROCESSED, construir_matriz, generar_matriz

ROOT = PROCESSED.parents[1]
INPUTS = [PROCESSED / name for name in (
    "radar_suministros_v09.csv", "radar_servicios_v09.csv", "evaluacion_documental_v11.csv"
)]


def read(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


@pytest.fixture
def matrix():
    return construir_matriz(*INPUTS)[1]


def test_totales_y_estados(matrix):
    assert len(matrix) == len({r['idContrato'] for r in matrix}) == 100
    assert Counter(r['tipo_oportunidad'] for r in matrix) == {'suministro': 16, 'servicio': 84}
    assert Counter(r['estado_revision_documental'] for r in matrix) == {
        'pendiente_revision': 6, 'revisado_con_limitaciones': 1, 'sin_revision_documental': 93}
    assert sum(r['seleccionado_revision_documental'] == 'si' for r in matrix) == 7


def test_preserva_todos_los_campos_y_cruce_por_id(matrix):
    originals = {r['idContrato']: r for p in INPUTS[:2] for r in read(p)}
    documents = {r['idContrato']: r for r in read(INPUTS[2])}
    for row in matrix:
        assert all(row[k] == v for k, v in originals[row['idContrato']].items())
        if row['idContrato'] in documents:
            assert all(row['doc_v11_' + k] == v for k, v in documents[row['idContrato']].items())
        else:
            assert all(v == 'sin_datos' for k, v in row.items() if k.startswith('doc_v11_'))
    senasa = next(r for r in matrix if r['idContrato'] == '103654')
    assert senasa['estado_revision_documental'] == 'revisado_con_limitaciones'
    assert senasa['doc_v11_formacion_academica_detalle'] == 'no_legible_completamente'


def test_no_infiere_elegibilidad_disponibilidad_o_ganancias(matrix):
    assert any(r['estado_administrativo'] == 'Vigente' for r in matrix)
    assert any(r['situacion_temporal'] == 'ventana_abierta' for r in matrix)
    for row in matrix:
        assert row['situacion_temporal_en_captura'] == row['situacion_temporal']
        assert row['elegibilidad_v12'] == row['requisitos_verificados'] == 'no_verificado'
        assert row['disponibilidad_actual'] == 'no_verificado'
        assert row['rentabilidad_v12'] == 'sin_datos'
        assert row['elegibilidad'] == 'por_verificar'
        assert row['rentabilidad'] == 'sin_datos_suficientes'


def test_orden_explicable_y_reproducible(matrix, tmp_path):
    paths = []
    for index, path in enumerate(INPUTS):
        rows = read(path)
        dest = tmp_path / f'{index}.csv'
        with dest.open('x', encoding='utf-8-sig', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(reversed(rows))
        paths.append(dest)
    assert construir_matriz(*paths)[1] == matrix
    assert [r['idContrato'] for r in matrix[:7]] == [
        '103645', '103685', '103725', '103727', '103662', '103721', '103654']
    assert [r['orden_revision'] for r in matrix] == list(map(str, range(1, 101)))
    assert all(r['estado_revision_documental'] in r['motivo_prioridad'] for r in matrix)


def test_salida_y_no_sobrescritura(tmp_path, matrix):
    output = tmp_path / 'matriz.csv'
    assert generar_matriz(salida=output) == matrix
    assert read(output) == matrix
    before = output.read_bytes()
    with pytest.raises(FileExistsError):
        generar_matriz(salida=output)
    assert output.read_bytes() == before
    with pytest.raises(FileExistsError):
        generar_matriz(salida=INPUTS[0])


@pytest.mark.parametrize('defect', ['duplicate', 'orphan', 'schema', 'contradiction'])
def test_rechaza_documental_invalido_sin_crear_salida(tmp_path, defect):
    rows = read(INPUTS[2])
    fields = list(rows[0])
    if defect == 'duplicate':
        rows[1]['idContrato'] = rows[0]['idContrato']
    elif defect == 'orphan':
        rows[0]['idContrato'] = 'INEXISTENTE'
    elif defect == 'contradiction':
        rows[0]['documento_revisado'] = 'si'
    else:
        fields.remove('codigo')
        for row in rows:
            del row['codigo']
    source = tmp_path / 'documental.csv'
    with source.open('x', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    output = tmp_path / 'salida.csv'
    with pytest.raises(ValueError):
        generar_matriz(documental=source, salida=output)
    assert not output.exists()


def test_integridad_originales(tmp_path):
    manifest = json.loads((PROCESSED / 'integridad_paso40_antes.json').read_text(encoding='utf-8'))
    for relative, expected in manifest.items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected
    generar_matriz(salida=tmp_path / 'matriz.csv')
    for relative, expected in manifest.items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected
