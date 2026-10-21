"""Preparación de rankings especializados v0.9."""

from app.clasificacion_cm_v08 import clasificar_v08


AFINIDAD_PROFESIONAL = {
    "gestion_presupuestal": 5,
    "gestion_administrativa": 5,
    "gestion_documental": 5,
    "servicios_administrativos": 5,
    "consultoria": 4,
    "empadronamiento": 4,
    "digitacion": 3,
    "impresion_servicios": 3,
    "comunicaciones_publicidad": 2,
    "evaluacion_prestaciones_salud": 2,
    "servicios_profesionales": 2,
    "ingenieria_proyectos": 2,
    "servicios_legales": 1,
    "servicios_farmaceuticos": 1,
}


def clasificar_oportunidad(tipo, descripcion):
    categoria = clasificar_v08(tipo, descripcion)

    tipo_normalizado = str(tipo or "").strip().casefold()

    if tipo_normalizado == "bien":
        return {
            "categoria_v08": categoria,
            "radar": "suministros",
            "afinidad_profesional": 0,
        }

    if tipo_normalizado == "servicio":
        return {
            "categoria_v08": categoria,
            "radar": "servicios",
            "afinidad_profesional": AFINIDAD_PROFESIONAL.get(
                categoria, 1
            ),
        }

    return {
        "categoria_v08": categoria,
        "radar": "por_verificar",
        "afinidad_profesional": 0,
    }
