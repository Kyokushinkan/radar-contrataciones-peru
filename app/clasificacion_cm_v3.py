"""Clasificación comercial experimental v3."""

from app.clasificacion_cm_v2 import clasificar, normalizar


def clasificar_v3(tipo, descripcion):
    texto = normalizar(descripcion)
    tipo_normalizado = normalizar(tipo)

    if tipo_normalizado == "bien":
        reglas = [
            ("equipos_forestales", [
                "mochilas extintoras",
                "mochila extintora",
                "sopladoras forestales",
                "sopladora forestal",
            ]),
            ("material_electrico", [
                "instalaciones electricas",
                "elementos electricos",
                "material electrico",
            ]),
            ("equipamiento_emergencias", [
                "carpa para atencion",
                "carpa de emergencia",
            ]),
        ]

    elif tipo_normalizado == "servicio":
        reglas = [
            ("alquiler_vehiculos", [
                "alquiler de un vehiculo",
                "alquiler de una camioneta",
                "alquiler de camioneta",
                "alquiler de vehiculo",
            ]),
            ("tecnologia_sistemas", [
                "actualizacion tecnologica",
                "sistema de registro civil",
                "desarrollo de software",
            ]),
            ("servicios_administrativos", [
                "auxiliar administrativo",
                "gestion documental",
                "tramite y gestion",
                "revision de expedientes",
                "planeamiento y presupuesto",
            ]),
            ("servicios_legales", [
                "asesor legal",
                "notario publico",
                "asesoria legal",
            ]),
            ("ingenieria_proyectos", [
                "ingeniero ambiental",
                "proyectos de inversion publica",
                "invierte.pe",
                "control de calidad de infraestructuras",
            ]),
            ("impresion_servicios", [
                "servicio de impresiones",
            ]),
            ("comunicaciones_publicidad", [
                "servicio de publicidad",
                "medios de comunicacion",
            ]),
            ("infraestructura_metalica", [
                "cobertura metalica",
            ]),
            ("cuidado_animales", [
                "cuidador de animales",
            ]),
        ]

    else:
        return clasificar(tipo, descripcion)

    for nombre, expresiones in reglas:
        if any(expresion in texto for expresion in expresiones):
            return nombre

    return clasificar(tipo, descripcion)
