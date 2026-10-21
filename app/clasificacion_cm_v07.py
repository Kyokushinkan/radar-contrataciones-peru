"""Clasificación complementaria de servicios profesionales v0.7."""

from app.clasificacion_cm_v2 import normalizar
from app.clasificacion_cm_v3 import clasificar_v3


REGLAS = [
    (
        "gestion_presupuestal",
        [
            "conciliacion marco legal del presupuesto",
            "conciliacion del marco legal del presupuesto",
            "planeamiento y presupuesto",
        ],
    ),
    (
        "gestion_administrativa",
        [
            "procesos administrativos",
            "expedientes administrativos",
            "atencion administrativa",
            "auxiliar administrativo",
        ],
    ),
    (
        "gestion_documental",
        [
            "gestion documental",
            "tramite documentario",
            "revision de expedientes",
        ],
    ),
    (
        "empadronamiento",
        [
            "empadronador",
            "empadronamiento",
        ],
    ),
    (
        "digitacion",
        [
            "digitacion",
            "digitador",
        ],
    ),
    (
        "servicios_farmaceuticos",
        [
            "productos farmaceuticos",
            "auxiliar en farmacia",
            "tecnico en farmacia",
        ],
    ),
    (
        "evaluacion_prestaciones_salud",
        [
            "evaluacion de prestaciones de servicios de salud",
        ],
    ),
    (
        "alquiler_vehiculos",
        [
            "alquiler de un (01) vehiculo",
            "alquiler de una camioneta",
            "alquiler de camioneta",
        ],
    ),
    (
        "impresion_servicios",
        [
            "impresion de triptico",
            "impresion de tripticos",
            "impresion de cartilla",
        ],
    ),
    (
        "alquiler_equipamiento_eventos",
        [
            "alquiler de toldos",
            "alquiler de sillas",
        ],
    ),
]


def clasificar_v07(tipo, descripcion):
    categoria_actual = clasificar_v3(tipo, descripcion)

    if normalizar(tipo) != "servicio":
        return categoria_actual

    # Conservamos las categorías específicas de v3.
    if categoria_actual != "otros_servicios":
        return categoria_actual

    texto = normalizar(descripcion)

    for categoria, expresiones in REGLAS:
        if any(expresion in texto for expresion in expresiones):
            return categoria

    return categoria_actual
