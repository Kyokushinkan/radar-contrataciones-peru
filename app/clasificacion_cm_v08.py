"""Clasificación complementaria v0.8 de contratos menores."""

from app.clasificacion_cm_v2 import normalizar
from app.clasificacion_cm_v07 import clasificar_v07


REGLAS_V08 = [
    (
        "apoyo_supervision_obras",
        [
            "apoyo para la inspeccion de la obra",
            "apoyo para inspeccion de obra",
        ],
    ),
    (
        "mantenimiento_maquinaria_pesada",
        [
            "mantenimeinto de preventivo de cargador frontal",
            "mantenimiento preventivo de cargador frontal",
        ],
    ),
    (
        "infraestructura_telecomunicaciones",
        [
            "desmontaje de tres (03) torres",
            "desmontaje de torres",
        ],
    ),
    (
        "difusion_institucional",
        [
            "difusion de los instrumentos de gestion territorial",
        ],
    ),
]


def clasificar_v08(tipo, descripcion):
    anterior = clasificar_v07(tipo, descripcion)

    if normalizar(tipo) != "servicio":
        return anterior

    if anterior != "otros_servicios":
        return anterior

    texto = normalizar(descripcion)

    for categoria, expresiones in REGLAS_V08:
        if any(expresion in texto for expresion in expresiones):
            return categoria

    return anterior
