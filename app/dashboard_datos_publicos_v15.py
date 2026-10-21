from pathlib import Path
import csv

FUENTE_PUBLICA = (
    Path(__file__).resolve().parents[1]
    / "data/public/contratos_publicos_v15.csv"
)

COLUMNAS = (
    "idContrato",
    "codigo",
    "entidad",
    "descripcion",
    "tipo_oportunidad",
    "categoria",
    "estado_administrativo",
    "inicio",
    "cierre",
)


def cargar_contratos_publicos():
    if not FUENTE_PUBLICA.is_file():
        return []

    with FUENTE_PUBLICA.open(
        encoding="utf-8-sig", newline=""
    ) as archivo:
        lector = csv.DictReader(archivo)
        encabezados = lector.fieldnames or []

        if (
            len(encabezados) != len(set(encabezados))
            or set(encabezados) != set(COLUMNAS)
        ):
            raise ValueError("Columnas publicas invalidas")

        contratos = list(lector)

    if any(
        None in contrato
        or any(valor is None for valor in contrato.values())
        for contrato in contratos
    ):
        raise ValueError("Filas publicas incompletas")

    identificadores = [
        contrato["idContrato"].strip()
        for contrato in contratos
    ]

    if (
        any(not identificador for identificador in identificadores)
        or len(identificadores) != len(set(identificadores))
    ):
        raise ValueError("Identificadores publicos invalidos")

    return contratos
