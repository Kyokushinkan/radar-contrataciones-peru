import csv
import hashlib
import io
import json
import socket
import tomllib
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from app.dashboard_datos_v14 import (
    ADVERTENCIA, FUENTE, cargar_datos, exportar_csv, ficha, filtrar_datos, presentar, resumen,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def datos():
    return cargar_datos()


def test_lectura_preserva_datos(datos):
    assert len(datos) == datos.idContrato.nunique() == 100
    assert datos.tipo_oportunidad.value_counts().to_dict() == {'servicio': 84, 'suministro': 16}
    with FUENTE.open(encoding='utf-8-sig', newline='') as stream:
        assert datos.to_dict('records') == list(csv.DictReader(stream))
    assert resumen(datos) == {'Total de contratos': 100, 'Bienes': 16, 'Servicios': 84,
                              'Documentación revisada': 1, 'Elegibilidad pendiente': 100,
                              'Requieren especialista': 19}


def test_filtros_combinables(datos):
    result = filtrar_datos(datos, {'tipo_oportunidad': ['servicio'],
                                  'entidad': ['SERVICIO NACIONAL DE SANIDAD AGRARIA'],
                                  'estado_revision_documental': ['revisado_con_limitaciones']})
    assert result.idContrato.tolist() == ['103654']
    assert filtrar_datos(datos, {'tipo_oportunidad': ['suministro'],
                                'estado_revision_documental': ['revisado_con_limitaciones']}).empty
    pd.testing.assert_frame_equal(filtrar_datos(datos, {'entidad': []}), datos)


@pytest.mark.parametrize('query', ['103654', 'cm-180-2026-senasa',
                                   'SERVICIO NACIONAL DE SANIDAD AGRARIA',
                                   'analisis en planeamiento y presupuesto'])
def test_busqueda_por_cada_campo(datos, query):
    assert '103654' in filtrar_datos(datos, busqueda=query).idContrato.values


def test_busqueda_literal_y_combinada(datos):
    assert filtrar_datos(datos, busqueda='.*').empty
    assert filtrar_datos(datos, {'tipo_oportunidad': ['suministro']}, '103654').empty
    assert filtrar_datos(datos, busqueda='no-existe-xyz').empty


@pytest.mark.parametrize('value', ['no_verificado', 'no_legible', 'sin_datos_suficientes', 'pendiente_verificacion'])
def test_estados_desconocidos(value):
    assert presentar(value) == value
    assert presentar('') == 'sin_datos'


def test_senasa(datos):
    record = ficha(datos, '103654')
    assert record['detalle']['Elegibilidad documental'] == 'pendiente_verificacion'
    assert record['detalle']['Disponibilidad actual'] == 'no_verificado'
    assert record['comercial']['Monto contractual'] == 'sin_datos_suficientes'
    assert record['comercial']['Condiciones de pago'] == '2 pagos de 50 por ciento'
    assert 'no legible' in record['limitaciones'][0]
    assert 'recorte documental' in record['limitaciones'][0]
    requirements = {r['Requisito']: r['Estado'] for r in record['requisitos']}
    assert requirements['Formación académica'] == 'no_legible'
    assert requirements['Experiencia específica'] == 'pendiente_verificacion'
    with pytest.raises(ValueError):
        ficha(filtrar_datos(datos, {'tipo_oportunidad': ['suministro']}), '103654')


def test_exportacion_solo_filtrados_e_integridad(datos):
    before = FUENTE.read_bytes()
    original = datos.copy(deep=True)
    filtered = filtrar_datos(datos, {'tipo_oportunidad': ['suministro']})
    payload = exportar_csv(filtered)
    downloaded = list(csv.DictReader(io.StringIO(payload.decode('utf-8-sig'))))
    assert len(downloaded) == 16
    assert downloaded == filtered.to_dict('records')
    assert list(csv.DictReader(io.StringIO(exportar_csv(filtered.iloc[:0]).decode('utf-8-sig')))) == []
    assert FUENTE.read_bytes() == before
    pd.testing.assert_frame_equal(original, datos)
    manifest = json.loads((ROOT / 'data/processed/integridad_paso42_antes.json').read_text(encoding='utf-8'))
    assert all(hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h for p, h in manifest.items())


def test_configuracion_privada():
    config = tomllib.loads((ROOT / '.streamlit/config.toml').read_text(encoding='utf-8'))
    assert config['server']['address'] == '127.0.0.1'
    assert config['server']['headless'] is True
    assert config['server']['enableStaticServing'] is False
    assert config['browser']['gatherUsageStats'] is False
    assert config['server']['showEmailPrompt'] is False


def test_interfaz_senasa_filtros_sin_red(monkeypatch):
    calls = []
    def guard(original, method=False):
        def checked(*args, **kwargs):
            address = args[1] if method else args[0]
            # asyncio en Windows usa socketpair sobre loopback internamente.
            if address[0] not in {'127.0.0.1', '::1', 'localhost'}:
                calls.append(str(address))
                raise AssertionError('Conexión externa no permitida en el panel')
            return original(*args, **kwargs)
        return checked
    monkeypatch.setattr(socket.socket, 'connect', guard(socket.socket.connect, True))
    monkeypatch.setattr(socket.socket, 'connect_ex', guard(socket.socket.connect_ex, True))
    monkeypatch.setattr(socket, 'create_connection', guard(socket.create_connection))
    app = AppTest.from_file(str(ROOT / 'app/dashboard_v14.py'), default_timeout=30).run()
    assert not app.exception
    assert ADVERTENCIA in [w.value for w in app.warning]
    assert [m.value for m in app.metric] == ['100', '16', '84', '1', '100', '19']
    app.sidebar.text_input(key='busqueda').set_value('103654').run()
    assert not app.exception
    assert app.selectbox(key='contrato').value == '103654'
    assert any('recorte documental' in w.value for w in app.warning)
    assert any(t.value == 'pendiente_verificacion' for t in app.text)
    app.sidebar.multiselect(key='tipo_oportunidad').set_value(['suministro']).run()
    assert not app.exception
    assert not app.selectbox
    assert any('No hay contratos' in i.value for i in app.info)
    assert calls == []


@pytest.mark.parametrize('defect', ['duplicate', 'schema'])
def test_entrada_invalida(datos, tmp_path, defect):
    altered = datos.copy()
    if defect == 'duplicate':
        altered.loc[1, 'idContrato'] = altered.loc[0, 'idContrato']
    else:
        altered = altered.drop(columns=['decision_v13'])
    path = tmp_path / 'invalid.csv'
    altered.to_csv(path, index=False)
    with pytest.raises(ValueError):
        cargar_datos(path)
