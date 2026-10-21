import csv
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from oportunidades_pladicop_v16 import clasificar

LIMA = ZoneInfo("America/Lima")

ORIGEN = ROOT / "data/public/pladicop_cotizaciones_v16.csv"
DESTINO = ROOT / "data/processed/reporte_automatico_v16.json"


def main():
    ahora = datetime.now(LIMA)

    if not ORIGEN.is_file():
        raise FileNotFoundError(
            f"No existe la captura publica: {ORIGEN}"
        )

    contenido = ORIGEN.read_bytes()
    sha256 = hashlib.sha256(contenido).hexdigest()

    with ORIGEN.open(
        encoding="utf-8-sig",
        newline=""
    ) as archivo:
        registros = list(csv.DictReader(archivo))

    if not registros:
        raise ValueError("La captura publica esta vacia")

    ids = [
        str(r.get("idContrato") or "").strip()
        for r in registros
    ]

    if any(not identificador for identificador in ids):
        raise ValueError("Existen contratos sin idContrato")

    if len(ids) != len(set(ids)):
        raise ValueError("Existen idContrato duplicados")

    conteo = Counter()

    for registro in registros:
        registro["cotizar"] = (
            str(registro.get("cotizar") or "")
            .strip()
            .lower() == "true"
        )

        categoria = clasificar(registro, ahora=ahora)
        conteo[categoria] += 1

    reporte = {
        "version": "1.6",
        "fecha_verificacion_peru": ahora.isoformat(),
        "fuente": "PLADICOP",
        "archivo": "pladicop_cotizaciones_v16.csv",
        "sha256_captura": sha256,
        "total_contratos": len(registros),
        "clasificacion": dict(sorted(conteo.items())),
        "candidatos_cotizacion": conteo[
            "Candidato a cotizacion"
        ],
        "vencidos": conteo["Vencido"],
        "estado_extraccion": "NO_EJECUTADA",
        "datos_nuevos_descargados": False,
        "fecha_captura_original": None,
        "observacion": (
            "Verificacion automatica de captura existente. "
            "No implica descarga nueva ni vigencia "
            "confirmada en PLADICOP."
        ),
    }

    DESTINO.parent.mkdir(parents=True, exist_ok=True)

    DESTINO.write_text(
        json.dumps(
            reporte,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print(json.dumps(
        reporte,
        ensure_ascii=False,
        indent=2
    ))

    print("REPORTE_AUTOMATICO=OK")


if __name__ == "__main__":
    main()
