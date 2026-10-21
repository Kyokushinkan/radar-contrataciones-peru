"""Paso 40: matriz local v1.2, sin inferir disponibilidad ni acreditación.

Ejecutar: python -m app.matriz_oportunidades_v12
Todas las columnas del radar se conservan literalmente. Las conclusiones nuevas
usan sufijo v12 cuando colisionan con campos históricos. doc_v11_* conserva la
evaluación aportada, no representa una nueva lectura del TDR.

Prioridad de revisión (menor primero): 1 pendientes seleccionados, 2 revisados
con limitaciones, 3 sin revisión. Desempate: afinidad v0.9 descendente, luego
idContrato lexicográfico. No se emplea el reloj ni se presume cotización abierta.
La afinidad es temática, no prueba de cumplimiento del perfil del proveedor.
"""

import csv
from collections import Counter
from pathlib import Path

PROCESSED = Path(__file__).resolve().parents[1] / "data" / "processed"
RADAR_REQUIRED = {
    "idContrato", "codigo", "entidad", "descripcion", "tipo", "categoria",
    "categoria_v08", "inicio", "cierre", "evaluado_en", "situacion_temporal",
    "estado_administrativo", "afinidad_profesional", "elegibilidad", "rentabilidad",
}
DOC_REQUIRED = {
    "idContrato", "codigo", "estado_evaluacion_documental", "documento_revisado",
    "fuente_documental", "requisitos_acreditados_por_usuario", "elegibilidad",
}
ESTADOS = {"pendiente_revision": 1, "revisado_con_limitaciones": 2,
           "sin_revision_documental": 3}
NEW_FIELDS = [
    "tipo_oportunidad", "situacion_temporal_en_captura",
    "seleccionado_revision_documental", "estado_revision_documental",
    "requisitos_verificados", "elegibilidad_v12", "disponibilidad_actual",
    "rentabilidad_v12", "prioridad_revision", "motivo_prioridad", "orden_revision",
]


def leer_csv(path, required):
    """Rechaza encabezados ambiguos, filas incompletas e IDs repetidos."""
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames or []
        if len(fields) != len(set(fields)) or not required <= set(fields):
            raise ValueError(f"Esquema CSV inválido: {path}")
        rows = list(reader)
    ids = set()
    for row in rows:
        identifier = row["idContrato"]
        if None in row or any(v is None for v in row.values()):
            raise ValueError(f"Fila incompleta o excedente: {path}")
        if not identifier.strip() or identifier in ids:
            raise ValueError(f"ID vacío o duplicado: {path}: {identifier}")
        ids.add(identifier)
    return fields, rows


def construir_matriz(suministros, servicios, documental):
    fields, goods = leer_csv(suministros, RADAR_REQUIRED)
    service_fields, services = leer_csv(servicios, RADAR_REQUIRED)
    doc_fields, documents = leer_csv(documental, DOC_REQUIRED)
    if fields != service_fields:
        raise ValueError("Los esquemas de los radares no coinciden")
    if len(goods) != 16 or len(services) != 84:
        raise ValueError("Se esperaban 16 suministros y 84 servicios")
    rows = goods + services
    if len({r['idContrato'] for r in rows}) != 100:
        raise ValueError("IDs duplicados entre radares")
    doc_by_id = {r["idContrato"]: r for r in documents}
    if not set(doc_by_id) <= {r["idContrato"] for r in rows}:
        raise ValueError("Expediente documental sin contrato en los radares")
    if Counter(d["estado_evaluacion_documental"] for d in documents) != {
        "pendiente_revision": 6, "revisado_con_limitaciones": 1
    } or doc_by_id.get("103654", {}).get("estado_evaluacion_documental") != "revisado_con_limitaciones":
        raise ValueError("Se esperaban seis pendientes y SENASA con limitaciones")
    extra = NEW_FIELDS + ["doc_v11_" + f for f in doc_fields]
    if set(extra) & set(fields):
        raise ValueError("Las columnas nuevas colisionan con el radar")
    result = []
    for group, expected_type, opportunity in (
        (goods, "Bien", "suministro"), (services, "Servicio", "servicio")
    ):
        for original in group:
            if original["tipo"] != expected_type:
                raise ValueError("Tipo incompatible con el radar de origen")
            if original["afinidad_profesional"] not in {str(n) for n in range(6)}:
                raise ValueError("Afinidad v0.9 fuera de la escala 0 a 5")
            doc = doc_by_id.get(original["idContrato"])
            state = doc["estado_evaluacion_documental"] if doc else "sin_revision_documental"
            if doc:
                if doc["codigo"] != original["codigo"]:
                    raise ValueError("Código documental incompatible con idContrato")
                reviewed = "si" if state == "revisado_con_limitaciones" else "no"
                if doc["documento_revisado"] != reviewed:
                    raise ValueError("Estado documental contradictorio")
            row = dict(original)
            row.update({
                "tipo_oportunidad": opportunity,
                "situacion_temporal_en_captura": original["situacion_temporal"],
                "seleccionado_revision_documental": "si" if doc else "no",
                "estado_revision_documental": state,
                # Leer requisitos de un TDR no acredita que el usuario los cumpla.
                "requisitos_verificados": "no_verificado",
                "elegibilidad_v12": "no_verificado",
                "disponibilidad_actual": "no_verificado",
                "rentabilidad_v12": "sin_datos",
                "prioridad_revision": str(ESTADOS[state]),
                "motivo_prioridad": (
                    f"grupo={state};afinidad_v09={original['afinidad_profesional']};"
                    "orden=grupo_asc,afinidad_desc,idContrato_lex_asc"
                ),
            })
            row.update({"doc_v11_" + f: doc[f] if doc else "sin_datos" for f in doc_fields})
            result.append(row)
    result.sort(key=lambda r: (int(r["prioridad_revision"]),
                              -int(r["afinidad_profesional"]), r["idContrato"]))
    for index, row in enumerate(result, 1):
        row["orden_revision"] = str(index)
    return fields + extra, result


def generar_matriz(
    suministros=PROCESSED / "radar_suministros_v09.csv",
    servicios=PROCESSED / "radar_servicios_v09.csv",
    documental=PROCESSED / "evaluacion_documental_v11.csv",
    salida=PROCESSED / "matriz_oportunidades_v12.csv",
):
    """Valida el lote completo antes de crear una salida; nunca sobrescribe."""
    salida = Path(salida)
    if salida.exists():
        raise FileExistsError(f"No se sobrescribirá: {salida}")
    fields, rows = construir_matriz(suministros, servicios, documental)
    with salida.open("x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return rows


if __name__ == "__main__":
    print(f"Matriz v1.2 creada: {len(generar_matriz())} contratos")
