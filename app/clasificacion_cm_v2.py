"""Clasificación comercial v2, sin conexiones externas."""

import unicodedata


def normalizar(texto):
    texto = unicodedata.normalize("NFKD", str(texto or ""))
    return "".join(
        c for c in texto
        if not unicodedata.combining(c)
    ).casefold()


def clasificar(tipo, descripcion):
    texto = normalizar(descripcion)
    tipo = normalizar(tipo)

    if tipo == "bien":
        reglas = [
            ("insumos_limpieza", ["utiles de limpieza", "detergente", "desinfectante"]),
            ("impresion_consumibles", ["toner", "cartucho", "tinta"]),
            ("mobiliario", ["silla", "taburete", "escritorio"]),
            ("ferreteria", ["escalera", "soporte de metal", "herramienta"]),
            ("equipos_bombas", ["electrobomba", "bomba de agua"]),
            ("combustibles", ["diesel", "gasohol", "combustible"]),
            ("insumos_quimicos", ["hipoclorito", "reactivo dpd"]),
            ("equipos_forestales", ["mochila extintora", "sopladora forestal"]),
            ("materiales_construccion", ["arena chancada", "confitillo"]),
        ]
        defecto = "otros_bienes"

    elif tipo == "servicio":
        reglas = [
            ("seguridad_vigilancia", ["vigilancia", "resguardo", "guardian nocturno"]),
            ("limpieza_servicios", ["servicio de limpieza", "limpieza de drenajes"]),
            ("mantenimiento", ["mantenimiento", "reparacion"]),
            ("transporte_servicios", ["traslado aereo", "servicio de transporte", "alquiler de vehiculo"]),
            ("consultoria", ["consultoria", "asesoria", "asistencia tecnica"]),
            ("servicios_profesionales", ["peritaje", "notificador"]),
            ("eventos", ["refrigerios", "decoracion", "ambientacion", "alquiler de equipo de sonido"]),
            ("instalaciones", ["instalacion", "suministro e instalacion"]),
        ]
        defecto = "otros_servicios"

    else:
        return "tipo_no_identificado"

    for categoria, palabras in reglas:
        if any(palabra in texto for palabra in palabras):
            return categoria

    return defecto
