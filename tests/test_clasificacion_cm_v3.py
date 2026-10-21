import pytest

from app.clasificacion_cm_v3 import clasificar_v3


@pytest.mark.parametrize(
    "tipo,descripcion,esperado",
    [
        (
            "Bien",
            "ADQUISICION DE UTILES DE LIMPIEZA",
            "insumos_limpieza",
        ),
        (
            "Bien",
            "ADQUISICION DE TONER",
            "impresion_consumibles",
        ),
        (
            "Bien",
            "ADQUISICION DE SILLAS ERGONOMICAS",
            "mobiliario",
        ),
        (
            "Bien",
            "Adquisicion de mochilas extintoras forestales",
            "equipos_forestales",
        ),
        (
            "Bien",
            "Piezas de instalaciones electricas",
            "material_electrico",
        ),
        (
            "Bien",
            "Adquisicion de carpa para atencion frente a emergencias",
            "equipamiento_emergencias",
        ),
        (
            "Servicio",
            "SERVICIO DE LIMPIEZA Y DESINFECCION",
            "limpieza_servicios",
        ),
        (
            "Servicio",
            "MANTENIMIENTO CORRECTIVO DE IMPRESORA",
            "mantenimiento",
        ),
        (
            "Servicio",
            "SERVICIO DE ALQUILER DE UN VEHICULO",
            "alquiler_vehiculos",
        ),
        (
            "Servicio",
            "SERVICIO DE AUXILIAR ADMINISTRATIVO",
            "servicios_administrativos",
        ),
        (
            "Servicio",
            "SERVICIO DE NOTARIO PUBLICO",
            "servicios_legales",
        ),
        (
            "Servicio",
            "SERVICIO DE ACTUALIZACION TECNOLOGICA",
            "tecnologia_sistemas",
        ),
        (
            "Servicio",
            "SERVICIO DE PUBLICIDAD EN MEDIOS DE COMUNICACION",
            "comunicaciones_publicidad",
        ),
        (
            "Servicio",
            "SERVICIO DE IMPRESIONES EN GENERAL",
            "impresion_servicios",
        ),
    ],
)
def test_clasificacion_v3(tipo, descripcion, esperado):
    assert clasificar_v3(tipo, descripcion) == esperado


def test_bien_desconocido():
    assert clasificar_v3(
        "Bien", "ADQUISICION DE PRODUCTO NO IDENTIFICADO"
    ) == "otros_bienes"


def test_servicio_desconocido():
    assert clasificar_v3(
        "Servicio", "SERVICIO NO IDENTIFICADO"
    ) == "otros_servicios"


def test_tipo_desconocido():
    assert clasificar_v3(
        "Desconocido", "OBJETO SIN TIPO"
    ) == "tipo_no_identificado"
