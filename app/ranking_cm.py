"""Ranking exploratorio de contratos menores; lectura local exclusivamente."""

import csv
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

LIMA = ZoneInfo("America/Lima")

CATEGORIAS = {
    "limpieza": ("limpieza", "detergente", "desinfectante", "escoba"),
    "impresion": ("toner", "tóner", "cartucho", "impresora"),
    "mobiliario": ("silla", "taburete", "escritorio", "mueble"),
    "ferreteria": ("escalera", "soporte de metal", "herramienta"),
    "equipos": ("electrobomba", "bomba", "equipo"),
    "combustibles": ("diesel", "diésel", "gasohol", "combustible"),
    "consultoria": ("consultoría", "consultoria", "asesoría", "asesoria"),
    "mantenimiento": ("mantenimiento", "reparación", "reparacion"),
    "transporte": ("transporte", "traslado", "alquiler de vehículo"),
}

PRIORIDADES = {
    "limpieza": 1,
    "impresion": 1,
    "mobiliario": 2,
    "ferreteria": 2,
    "equipos": 3,
    "combustibles": 3,
    "consultoria": 3,
    "mantenimiento": 3,
    "transporte": 3,
    "otros": 4,
}


def categoria(descripcion):
    texto = (descripcion or "").casefold()
    for nombre, palabras in CATEGORIAS.items():
        if any(palabra in texto for palabra in palabras):
            return nombre
    return "otros"


def estado_temporal(inicio, fin, ahora):
    if not inicio or not fin:
        return "sin_fecha"

    try:
        apertura = datetime.fromisoformat(inicio)
        cierre = datetime.fromisoformat(fin)
    except (TypeError, ValueError):
        return "sin_fecha"

    if apertura.tzinfo is None or cierre.tzinfo is None:
        return "sin_fecha"
    if cierre <= apertura:
        return "sin_fecha"

    if ahora < apertura:
        return "por_iniciar"
    if ahora >= cierre:
        return "vencido"
    return "ventana_abierta"


def generar_ranking(db_path, csv_path, ahora=None):
    db_path = Path(db_path).resolve(strict=True)
    csv_path = Path(csv_path).resolve()

    ahora = ahora or datetime.now(LIMA)
    if ahora.tzinfo is None or ahora.utcoffset() is None:
        raise ValueError("Se requiere fecha con zona horaria")
    ahora = ahora.astimezone(LIMA)

    if csv_path == db_path:
        raise ValueError("El CSV no puede sobrescribir la base SQLite")

    conn = sqlite3.connect(
        f"{db_path.as_uri()}?mode=ro", uri=True
    )

    try:
        registros = conn.execute(
            "SELECT contract_id, payload_json, normalized_dates_json "
            "FROM pladicop_contracts WHERE source='PLADICOP'"
        ).fetchall()
    finally:
        conn.close()

    salida = []

    for identificador, payload, fechas in registros:
        p = json.loads(payload)
        d = json.loads(fechas)
        descripcion = p.get("desObjetoContrato") or ""
        grupo = categoria(descripcion)

        temporal = estado_temporal(
            d.get("fecIniCotizacion"),
            d.get("fecFinCotizacion"),
            ahora,
        )

        administrativo = p.get("nomEstadoContrato") or ""

        # El estado administrativo prevalece sobre el plazo.
        if administrativo.casefold() != "vigente":
            situacion = "no_vigente"
        else:
            situacion = temporal

        salida.append({
            "idContrato": identificador,
            "entidad": p.get("nomEntidad") or "",
            "codigo": p.get("desContratacion") or "",
            "tipo": p.get("nomObjetoContrato") or "",
            "descripcion": descripcion,
            "categoria": grupo,
            "prioridad_preliminar": PRIORIDADES[grupo],
            "estado_administrativo": administrativo,
            "situacion_temporal": situacion,
            "inicio": d.get("fecIniCotizacion") or "",
            "cierre": d.get("fecFinCotizacion") or "",
            "cotizar_en_captura": p.get("cotizar"),
            "elegibilidad": "por_verificar",
            "rentabilidad": "sin_datos_suficientes",
            "evaluado_en": ahora.isoformat(),
        })

    salida.sort(
        key=lambda r: (
            r["situacion_temporal"] != "ventana_abierta",
            r["prioridad_preliminar"],
            r["cierre"] or "9999",
            r["idContrato"],
        )
    )

    csv_path.parent.mkdir(parents=True, exist_ok=True)

    campos = [
        "idContrato", "entidad", "codigo", "tipo",
        "descripcion", "categoria", "prioridad_preliminar",
        "estado_administrativo", "situacion_temporal",
        "inicio", "cierre", "cotizar_en_captura",
        "elegibilidad", "rentabilidad", "evaluado_en",
    ]

    with csv_path.open("w", newline="", encoding="utf-8-sig") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(salida)

    return salida
