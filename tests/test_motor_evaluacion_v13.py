import csv
import hashlib
import json
from collections import Counter

import pytest

from app.motor_evaluacion_v13 import (
    PROCESSED, REQUISITOS, SIN_DATOS, calcular_margen, construir_evaluacion,
    decidir, evaluar_afinidad, evaluar_elegibilidad, generar_evaluacion,
)


def read(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


@pytest.fixture
def rows():
    return construir_evaluacion()[1]


def test_conservacion_contratos_y_documental(rows):
    assert len(rows) == len({r['idContrato'] for r in rows}) == 100
    assert Counter(r['tipo_oportunidad'] for r in rows) == {'suministro': 16, 'servicio': 84}
    originals = {r['idContrato']: r for r in read(PROCESSED / 'matriz_oportunidades_v12.csv')}
    for row in rows:
        assert all(row[k] == v for k, v in originals[row['idContrato']].items())
    docs = read(PROCESSED / 'evaluacion_documental_v11.csv')
    selected = {r['idContrato']: r for r in rows if r['seleccionado_revision_documental'] == 'si'}
    assert len(selected) == len(docs) == 7
    for doc in docs:
        assert all(selected[doc['idContrato']]['doc_v11_' + k] == v for k, v in doc.items())


def test_senasa_y_ausencia_de_evidencia(rows):
    senasa = next(r for r in rows if r['idContrato'] == '103654')
    assert senasa['codigo'] == 'CM-180-2026-SENASA'
    assert senasa['elegibilidad_global'] == 'pendiente_verificacion'
    assert senasa['estado_formacion_academica'] == 'no_legible'
    assert senasa['estado_capacitaciones'] == 'pendiente_verificacion'
    assert senasa['estado_experiencia_especifica'] == 'pendiente_verificacion'
    assert senasa['plazo_ejecucion'] == '60 dias calendario'
    assert senasa['condiciones_pago'] == '2 pagos de 50 por ciento'
    assert senasa['decision_v13'] == 'solicitar_documentacion'
    for row in rows:
        assert row['elegibilidad_global'] == 'pendiente_verificacion'
        assert row['disponibilidad_actual'] == 'no_verificado'
        assert all(row['estado_' + k] in {'pendiente_verificacion', 'no_legible'} for k in REQUISITOS)
        for key in ['monto_contractual', 'costos_estimados', 'gastos_ejecucion',
                    'margen_bruto_estimado', 'rentabilidad_evaluada']:
            assert row[key] == SIN_DATOS


def test_reproducibilidad_y_prioridad(rows):
    assert construir_evaluacion()[1] == rows
    assert {r['idContrato'] for r in rows[:7]} == {
        '103645', '103654', '103662', '103685', '103721', '103725', '103727'}
    assert [r['orden_verificacion_v13'] for r in rows] == list(map(str, range(1, 101)))
    for row in reversed(rows):
        assert decidir(row['afinidad_profesional_v13'], row['elegibilidad_global'],
                       row['seleccionado_revision_documental'] == 'si',
                       row['estado_revision_documental'] == 'revisado_con_limitaciones') == (
                           row['decision_v13'], row['motivo_decision_v13'])


@pytest.mark.parametrize('description', [
    'Administración de empresas', 'Gestión pública', 'Contrataciones del Estado',
    'Logística y abastecimiento', 'Gestión administrativa', 'Gestión presupuestal',
    'Gestión documental', 'Control patrimonial',
])
def test_areas_prioritarias(description):
    assert evaluar_afinidad(dict(tipo_oportunidad='servicio', descripcion=description,
                                categoria_v08='otros_servicios'))[0] == 'alta_afinidad_tematica'


@pytest.mark.parametrize('category,expected', [
    ('ingenieria_proyectos', 'requiere_revision_especializada'),
    ('digitacion', 'afinidad_media'), ('comunicaciones_publicidad', 'afinidad_baja'),
    ('otros_servicios', 'afinidad_no_determinada'),
])
def test_afinidad_categorias(category, expected):
    assert evaluar_afinidad(dict(tipo_oportunidad='servicio', descripcion='Servicio',
                                categoria_v08=category))[0] == expected


def acreditaciones():
    return {k: dict(estado='acreditado', fuente='expediente/prueba',
                   evidencia='verificación humana folio 1') for k in REQUISITOS}


def test_elegibilidad_exige_evidencia_e_inventario_completo():
    assert evaluar_elegibilidad({}) == 'pendiente_verificacion'
    requirements = acreditaciones()
    assert evaluar_elegibilidad(requirements) == 'pendiente_verificacion'
    assert evaluar_elegibilidad(requirements, inventario_completo=True,
                               fuente_inventario='TDR íntegro') == 'elegible_documentalmente'
    requirements['formacion_academica']['estado'] = 'no_acreditado'
    assert evaluar_elegibilidad(requirements) == 'no_elegible_documentalmente'
    requirements['formacion_academica']['evidencia'] = ''
    with pytest.raises(ValueError, match='evidencia'):
        evaluar_elegibilidad(requirements)


@pytest.mark.parametrize('state', ['acreditado', 'no_acreditado', 'no_exigido'])
def test_estados_concluyentes_requieren_fuente(state):
    with pytest.raises(ValueError):
        evaluar_elegibilidad({'formacion_academica': {'estado': state}})


def money(value, currency='PEN', source='documento/folio-1'):
    return dict(valor=value, moneda=currency, fuente=source)


@pytest.mark.parametrize('revenue,cost,margin,percent', [
    ('1000', '600', '400.00', '40.00'),
    ('1000', '1200', '-200.00', '-20.00'),
    ('100', '100', '0.00', '0.00'),
    ('0', '10', '-10.00', 'no_aplicable'),
    ('3', '2', '1.00', '33.33'),
])
def test_margen_determinista(revenue, cost, margin, percent):
    result = calcular_margen(money(revenue), money(cost))
    assert result['estado'] == 'calculado'
    assert result['margen_bruto_estimado'] == margin
    assert result['margen_porcentaje'] == percent
    assert result['moneda'] == 'PEN'
    assert result['fuente_monto'] == result['fuente_costos'] == 'documento/folio-1'
    assert result['monto_documentado'] == revenue


@pytest.mark.parametrize('amount,cost', [
    (None, None), (money('100'), None), (None, money('10')),
    (money('100', source=''), money('10')), (money(''), money('10')),
    (money('100'), money('10', currency='')),
])
def test_margen_incompleto(amount, cost):
    result = calcular_margen(amount, cost)
    assert result['estado'] == result['margen_bruto_estimado'] == SIN_DATOS


@pytest.mark.parametrize('invalid', ['-1', 'NaN', 'Infinity', 'texto'])
def test_margen_invalido(invalid):
    with pytest.raises(ValueError):
        calcular_margen(money(invalid), money('1'))


def test_no_mezcla_monedas():
    with pytest.raises(ValueError, match='Monedas distintas'):
        calcular_margen(money('100', 'PEN'), money('10', 'USD'))
    assert calcular_margen(money('100', 'USD'), money('10', 'USD'))['moneda'] == 'USD'


def test_decision_sin_descarte_por_ausencia():
    assert decidir('afinidad_baja', 'pendiente_verificacion', False, False)[0] == 'sin_informacion_suficiente'
    assert decidir('alta_afinidad_tematica', 'no_elegible_documentalmente', True, False)[0] == 'descartar_por_incompatibilidad_acreditada'
    assert decidir('alta_afinidad_tematica', 'elegible_documentalmente', True, False)[0] == 'evaluar_costos'


def test_salida_integridad_y_sobrescritura(tmp_path, rows):
    manifest = json.loads((PROCESSED / 'integridad_paso41_antes.json').read_text(encoding='utf-8'))
    root = PROCESSED.parents[1]
    def verify():
        assert all(hashlib.sha256((root / p).read_bytes()).hexdigest() == h for p, h in manifest.items())
    verify()
    output = tmp_path / 'v13.csv'
    generar_evaluacion(salida=output)
    assert read(output) == rows
    before = output.read_bytes()
    with pytest.raises(FileExistsError):
        generar_evaluacion(salida=output)
    assert output.read_bytes() == before
    with pytest.raises(FileExistsError):
        generar_evaluacion(salida=PROCESSED / 'matriz_oportunidades_v12.csv')
    verify()


@pytest.mark.parametrize('defect', ['duplicate', 'schema', 'documental'])
def test_rechaza_entrada_invalida(tmp_path, defect):
    data = read(PROCESSED / 'matriz_oportunidades_v12.csv')
    if defect == 'duplicate':
        data[1]['idContrato'] = data[0]['idContrato']
    elif defect == 'schema':
        for row in data:
            del row['tipo_oportunidad']
    else:
        data[0]['doc_v11_codigo'] = 'incorrecto'
    source = tmp_path / 'entrada.csv'
    with source.open('x', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(data[0]))
        writer.writeheader()
        writer.writerows(data)
    output = tmp_path / 'salida.csv'
    with pytest.raises(ValueError):
        generar_evaluacion(entrada=source, salida=output)
    assert not output.exists()
