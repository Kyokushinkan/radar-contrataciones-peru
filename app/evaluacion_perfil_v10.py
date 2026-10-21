"""Evaluación temática y alertas de requisitos v1.0."""

from app.clasificacion_cm_v2 import normalizar


TEMAS_PRIORITARIOS = [
    ("contratacion_publica", [
        "contrataciones del estado",
        "contratacion publica",
        "abastecimiento",
        "logistica",
        "adquisiciones",
    ]),
    ("gestion_administrativa", [
        "procesos administrativos",
        "expedientes administrativos",
        "atencion administrativa",
        "gestion documental",
        "tramite y gestion documental",
        "auxiliar administrativo",
    ]),
    ("gestion_presupuestal", [
        "planeamiento y presupuesto",
        "marco legal del presupuesto",
        "gestion presupuestal",
    ]),
    ("gestion_publica", [
        "gestion publica",
        "programa vaso de leche",
        "ule-sisfoh",
        "empadronador",
    ]),
]


ALERTAS_ESPECIALIZACION = [
    ("ingenieria", [
        "ingenieria",
        "ingeniero",
        "infraestructura",
        "inspeccion de obra",
        "consultoria de la obra",
        "consultoria de obra",
        "proyecto de inversion",
        "proyectos de inversion",
    ]),
    ("legal", [
        "asesor legal",
        "notario publico",
        "peritaje forense",
    ]),
    ("salud", [
        "farmacia",
        "productos farmaceuticos",
        "prestaciones de servicios de salud",
    ]),
]


def evaluar_servicio(descripcion):
    texto = normalizar(descripcion)

    temas = [
        nombre
        for nombre, expresiones in TEMAS_PRIORITARIOS
        if any(expresion in texto for expresion in expresiones)
    ]

    alertas = [
        nombre
        for nombre, expresiones in ALERTAS_ESPECIALIZACION
        if any(expresion in texto for expresion in expresiones)
    ]

    if alertas:
        afinidad = "requiere_revision_especializada"
    elif temas:
        afinidad = "alta_afinidad_tematica"
    else:
        afinidad = "afinidad_no_determinada"

    return {
        "temas_detectados": "|".join(temas),
        "alertas_especializacion": "|".join(alertas),
        "afinidad_revisada": afinidad,
        "elegibilidad_confirmada": "no",
        "requisitos_verificados": "no",
    }
