"""Ranking comercial v0.6 basado en clasificación v3."""

import csv
from pathlib import Path

from app.ranking_cm import generar_ranking
from app.clasificacion_cm_v3 import clasificar_v3


CATEGORIAS_PROFESIONALES = {
    "consultoria",
    "servicios_profesionales",
    "servicios_legales",
    "ingenieria_proyectos",
    "servicios_administrativos",
}


def modalidad_comercial(tipo, categoria):
    tipo = (tipo or "").strip().casefold()

    if tipo == "bien":
        return "suministro_bienes"

    if tipo == "servicio":
        if categoria in CATEGORIAS_PROFESIONALES:
            return "servicio_profesional_especializado"
        return "servicio_empresarial"

    return "por_verificar"


def prioridad_v06(modalidad, categoria):
    if categoria in {
        "insumos_limpieza",
        "impresion_consumibles",
        "mobiliario",
        "ferreteria",
    }:
        return 1

    if modalidad == "suministro_bienes":
        return 2

    if modalidad == "servicio_empresarial":
        return 3

    return 4


def generar_ranking_v06(db_path, csv_path, ahora=None):
    csv_path = Path(csv_path).resolve()

    if csv_path.exists():
        raise FileExistsError(
            f"El archivo ya existe y no se sobrescribirá: {csv_path}"
        )

    # La función original genera un CSV; usamos un archivo temporal
    # independiente y lo eliminamos después de leer sus registros.
    temporal = csv_path.with_name(
        csv_path.stem + "_temporal.csv"
    )

    if temporal.exists():
        raise FileExistsError(
            f"El archivo temporal ya existe: {temporal}"
        )

    try:
        registros = generar_ranking(
            db_path=db_path,
            csv_path=temporal,
            ahora=ahora,
        )

        nuevos = []

        for r in registros:
            nuevo = dict(r)

            categoria = clasificar_v3(
                r["tipo"],
                r["descripcion"],
            )

            modalidad = modalidad_comercial(
                r["tipo"],
                categoria,
            )

            nuevo["categoria_v3"] = categoria
            nuevo["modalidad_comercial"] = modalidad
            nuevo["prioridad_v06"] = prioridad_v06(
                modalidad,
                categoria,
            )

            nuevos.append(nuevo)

        nuevos.sort(
            key=lambda r: (
                r["situacion_temporal"] != "ventana_abierta",
                r["prioridad_v06"],
                r["cierre"] or "9999",
                r["idContrato"],
            )
        )

        campos = list(nuevos[0].keys()) if nuevos else [
            "idContrato", "categoria_v3",
            "modalidad_comercial", "prioridad_v06",
        ]

        csv_path.parent.mkdir(parents=True, exist_ok=True)

        with csv_path.open(
            "x", newline="", encoding="utf-8-sig"
        ) as archivo:
            escritor = csv.DictWriter(
                archivo, fieldnames=campos
            )
            escritor.writeheader()
            escritor.writerows(nuevos)

        return nuevos

    finally:
        if temporal.exists():
            temporal.unlink()
