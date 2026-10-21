import argparse
import csv
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

COLUMNAS = [
    "idContrato",
    "nroContratacion",
    "desContratacion",
    "nomEntidad",
    "nomObjetoContrato",
    "desObjetoContrato",
    "nomEstadoContrato",
    "cotizar",
    "fecIniCotizacion",
    "fecFinCotizacion",
]


def exportar(db_path, csv_base, salida):
    registros = {}

    if csv_base.exists():
        with csv_base.open(
            "r", encoding="utf-8-sig", newline=""
        ) as archivo:
            for fila in csv.DictReader(archivo):
                identificador = str(
                    fila.get("idContrato") or ""
                ).strip()

                if identificador:
                    registros[identificador] = fila

    if db_path.exists():
        with sqlite3.connect(db_path) as conexion:
            filas = conexion.execute(
                """
                SELECT contract_id, payload_json
                FROM pladicop_contracts
                WHERE source = 'PLADICOP'
                """
            ).fetchall()

        for identificador, contenido in filas:
            registro = json.loads(contenido)

            clave = str(identificador).strip()

            if not clave:
                continue

            anterior = registros.get(clave, {})

            nuevo = {}

            for columna in COLUMNAS:
                valor = registro.get(columna)

                if valor is None:
                    valor = anterior.get(columna, "")

                nuevo[columna] = valor

            nuevo["idContrato"] = clave

            registros[clave] = nuevo

    salida.parent.mkdir(
        parents=True, exist_ok=True
    )

    temporal = salida.with_suffix(".tmp")

    with temporal.open(
        "w", encoding="utf-8", newline=""
    ) as archivo:
        escritor = csv.DictWriter(
            archivo,
            fieldnames=COLUMNAS,
        )
        escritor.writeheader()

        for clave in sorted(registros):
            escritor.writerow(registros[clave])

    temporal.replace(salida)

    return len(registros)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--db", required=True
    )
    parser.add_argument(
        "--base",
        default=str(
            ROOT / "data/public/pladicop_cotizaciones_v16.csv"
        ),
    )
    parser.add_argument(
        "--output", required=True
    )

    args = parser.parse_args()

    db_path = Path(args.db).resolve()
    salida = Path(args.output).resolve()

    # La base de ensayo nunca debe publicarse.
    if "pladicop_v17_prueba" in str(db_path).lower():
        destino_publico = (
            ROOT / "data/public"
        ).resolve()

        if salida == destino_publico or destino_publico in salida.parents:
            raise SystemExit(
                "ERROR: no se permite publicar datos de ensayo"
            )

    cantidad = exportar(
        db_path,
        Path(args.base),
        salida,
    )

    print("EXPORTACION_V17=OK")
    print("CONTRATOS_UNICOS=", cantidad)
    print("ARCHIVO=", salida)


if __name__ == "__main__":
    main()
