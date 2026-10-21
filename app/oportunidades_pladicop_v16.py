import csv
"""Lectura local de oportunidades PLADICOP para Streamlit."""

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

LIMA = ZoneInfo("America/Lima")

ROOT = Path(__file__).resolve().parents[1]

CAPTURA = (
    ROOT
    / "data"
    / "raw"
    / "pladicop_paso43_prueba"
    / "captura_original_100.json"
)


def fecha_pladicop(valor):
    if not valor:
        return None

    try:
        return datetime.strptime(
            valor, "%d/%m/%Y %H:%M:%S"
        ).replace(tzinfo=LIMA)
    except (TypeError, ValueError):
        return None


def clasificar(registro, ahora=None):
    ahora = ahora or datetime.now(LIMA)

    if ahora.tzinfo is None:
        raise ValueError("Se requiere fecha con zona horaria")

    ahora = ahora.astimezone(LIMA)

    estado = str(
        registro.get("nomEstadoContrato") or ""
    ).strip().lower()

    if estado != "vigente":
        return "Culminado u otro estado"

    if registro.get("cotizar") is not True:
        return "No cotizable"

    inicio = fecha_pladicop(
        registro.get("fecIniCotizacion")
    )

    cierre = fecha_pladicop(
        registro.get("fecFinCotizacion")
    )

    if inicio is None or cierre is None:
        return "Fechas no verificables"

    if ahora < inicio:
        return "Cotizacion aun no iniciada"

    if ahora >= cierre:
        return "Vencido"

    return "Candidato a cotizacion"


# CSV_PUBLICO_V16
CSV_PUBLICO = ROOT / "data/public/pladicop_cotizaciones_v16.csv"

# CSV incremental v1.7: tiene prioridad cuando existe.
CSV_INCREMENTAL_V17 = (
    ROOT / "data/public/pladicop_cotizaciones_v17.csv"
)


def cargar_oportunidades(ruta=CAPTURA, ahora=None):
    ruta = Path(ruta)

    if CSV_INCREMENTAL_V17.is_file() and ruta == CAPTURA:
        fuente = CSV_INCREMENTAL_V17
    elif ruta.is_file():
        fuente = ruta
    elif CSV_PUBLICO.is_file():
        fuente = CSV_PUBLICO
    else:
        return []

    if fuente.suffix.lower() == ".csv":
        with fuente.open(
            "r", encoding="utf-8-sig", newline=""
        ) as archivo:
            registros = list(csv.DictReader(archivo))

        for registro in registros:
            registro["cotizar"] = (
                str(registro.get("cotizar", "")).lower() == "true"
            )
    else:
        documento = json.loads(
            fuente.read_text(encoding="utf-8-sig")
        )
        registros = documento.get("data", [])

    if not isinstance(registros, list):
        raise ValueError("El campo data debe ser una lista")

    resultado = []

    for r in registros:
        if not isinstance(r, dict):
            continue

        clasificacion = clasificar(r, ahora)

        resultado.append({
            "ID": str(r.get("idContrato", "")),
            "Codigo": str(r.get("desContratacion") or
                          r.get("nroContratacion") or ""),
            "Entidad": str(r.get("nomEntidad") or ""),
            "Objeto": str(r.get("nomObjetoContrato") or ""),
            "Descripcion": str(
                r.get("desObjetoContrato") or ""
            ),
            "Estado PLADICOP": str(
                r.get("nomEstadoContrato") or ""
            ),
            "Cotizar": r.get("cotizar") is True,
            "Inicio": str(
                r.get("fecIniCotizacion") or ""
            ),
            "Cierre": str(
                r.get("fecFinCotizacion") or ""
            ),
            "Clasificacion": clasificacion,
            "Verificacion": "Captura local; no tiempo real",
        })

    return resultado
