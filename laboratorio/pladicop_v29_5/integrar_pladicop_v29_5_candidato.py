import csv
import json
import re
from pathlib import Path

base = Path("data/public/pladicop_cotizaciones_v17.csv")
fuente = Path("data/processed/pladicop_v23_nuevos.json")
salida = Path("data/processed/pladicop_v25_incremental_candidato.csv")

with base.open(encoding="utf-8-sig", newline="") as f:
    lector = csv.DictReader(f)
    campos = lector.fieldnames
    anteriores = list(lector)

obj = json.loads(fuente.read_text(encoding="utf-8-sig"))
nuevos = obj["data"]

# V29: comprobacion de frescura y ventana de ejecucion.
import os
from datetime import datetime, timezone

inicio_texto = os.environ.get("PLADICOP_V29_INICIO_UTC")
fin_texto = os.environ.get("PLADICOP_V29_FIN_UTC")

if not inicio_texto or not fin_texto:
    raise SystemExit("V29_ERROR: VENTANA_EJECUCION_AUSENTE")

def fecha_utc(valor):
    try:
        fecha = datetime.fromisoformat(valor)
        if fecha.tzinfo is None:
            raise ValueError("FECHA_SIN_ZONA")
        return fecha.astimezone(timezone.utc)
    except (TypeError, ValueError, AttributeError):
        raise SystemExit("V29_ERROR: FECHA_INVALIDA")

inicio = fecha_utc(inicio_texto)
fin = fecha_utc(fin_texto)

if inicio > fin:
    raise SystemExit("V29_ERROR: VENTANA_INVALIDA")

if obj.get("finalizacion") != "COMPLETA_VALIDADA":
    raise SystemExit("V29_ERROR: CAPTURA_INCOMPLETA")

capturado = fecha_utc(obj.get("capturadoEn"))

if capturado < inicio or capturado > fin:
    raise SystemExit("V29_ERROR: CAPTURA_FUERA_DE_VENTANA")

print("V29_FRESCURA=PASS")


if obj.get("finalizacion") != "COMPLETA_VALIDADA":
    raise SystemExit("ERROR: captura no validada")


if not isinstance(nuevos, list):
    raise SystemExit("ERROR: datos JSON no son una lista")

ids_fuente = [str(x.get("idContrato", "")).strip() for x in nuevos]

if any(not ident for ident in ids_fuente):
    raise SystemExit("ERROR: identificador vacio en fuente")

if len(ids_fuente) != len(set(ids_fuente)):
    raise SystemExit("ERROR: identificadores duplicados en fuente")

ids_anteriores = [str(x["idContrato"]).strip() for x in anteriores]

if any(not ident for ident in ids_anteriores):
    raise SystemExit("ERROR: identificador vacio en base")

if len(ids_anteriores) != len(set(ids_anteriores)):
    raise SystemExit("ERROR: duplicados en base")

ids = set(ids_anteriores)
registros = list(anteriores)
incorporados = 0

for x in nuevos:
    ident = str(x["idContrato"]).strip()
    if ident in ids:
        continue

    texto = re.sub(r"\s+", " ", x.get("textoVisible", "")).strip()

    numero = re.match(r"^(.*?)\s+Vigente\s+", texto, re.I)
    tipo = re.search(
        r"\b(Consultor.a de Obra|Bien|Servicio|Obra)\s*:\s*",
        texto, re.I
    )

    if not numero or not tipo or tipo.start() <= numero.end():
        raise SystemExit("ERROR: contrato sin estructura " + ident)

    entidad = texto[numero.end():tipo.start()].strip()
    descripcion = texto[tipo.end():].split(" Cotizaciones:", 1)[0].strip()

    if not entidad or not descripcion:
        raise SystemExit("ERROR: datos incompletos " + ident)

    fila = {c: "" for c in campos}
    fila.update({
        "idContrato": ident,
        "desContratacion": numero.group(1).strip(),
        "nomEntidad": entidad,
        "nomObjetoContrato": tipo.group(1).capitalize(),
        "desObjetoContrato": descripcion,
        "nomEstadoContrato": x.get("nomEstadoContrato", ""),
        "cotizar": "False",
        "fecIniCotizacion": x.get("fecIniCotizacion", ""),
        "fecFinCotizacion": x.get("fecFinCotizacion", ""),
        "fecPublica": x.get("fecPublica", "")
    })

    registros.append(fila)
    ids.add(ident)
    incorporados += 1

if len(registros) != len(anteriores) + incorporados:
    raise SystemExit("ERROR: inconsistencia en total integrado")

if incorporados > len(nuevos):
    raise SystemExit("ERROR: incorporados exceden candidatos")

print("CANDIDATOS_RECIBIDOS=", len(nuevos))
print("CANDIDATOS_YA_EXISTENTES=", len(nuevos) - incorporados)

if len({str(r["idContrato"]).strip() for r in registros}) != len(registros):
    raise SystemExit("ERROR: identificadores duplicados")

for i, anterior in enumerate(anteriores):
    if registros[i] != anterior:
        raise SystemExit(
            f"ERROR: registro historico modificado en posicion {i}"
        )

print("INTEGRIDAD_HISTORICA=PASS")
print("DUPLICADOS=0")

# V29.5: escritura temporal y reemplazo atomico.
# Solo debe ejecutarse dentro del laboratorio autorizado.
import os
import tempfile

if Path.cwd().resolve() != Path(__file__).resolve().parent:
    raise SystemExit("V29_5_DIRECTORIO_NO_AUTORIZADO")

if not Path.cwd().name.lower().endswith("_laboratorio"):
    raise SystemExit("V29_5_LABORATORIO_REQUERIDO")

salida.parent.mkdir(parents=True, exist_ok=True)

temporal = None

try:
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8-sig",
        newline="",
        dir=salida.parent,
        prefix="pladicop_v29_5_",
        suffix=".csv.tmp",
        delete=False
    ) as f:
        temporal = Path(f.name)
        escritor = csv.DictWriter(f, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(registros)
        f.flush()
        os.fsync(f.fileno())

    with temporal.open(
        "r", encoding="utf-8-sig", newline=""
    ) as f:
        verificador = csv.DictReader(f)
        campos_verificados = verificador.fieldnames
        filas_verificadas = list(verificador)

    if campos_verificados != campos:
        raise RuntimeError("V29_5_ESQUEMA_INVALIDO")

    if filas_verificadas != registros:
        raise RuntimeError("V29_5_CONTENIDO_INVALIDO")

    temporal.replace(salida)

finally:
    if temporal is not None and temporal.exists():
        temporal.unlink()

print("=== INTEGRACION INCREMENTAL V25 ===")
print("BASE_ANTERIOR=", len(anteriores))
print("NUEVOS_INCORPORADOS=", incorporados)
print("TOTAL_INTEGRADO=", len(registros))
print("CSV_GENERADO=", salida)
print("INTEGRACION_FINAL=PASS")
print("BASE_PUBLICA_MODIFICADA=NO")
print("PUBLICACION_GITHUB=NO")
