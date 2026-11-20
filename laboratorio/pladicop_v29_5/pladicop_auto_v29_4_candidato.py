# V29 LABORATORIO - CAPTURA REAL PROHIBIDA
if __name__ == "__main__":
    raise SystemExit("V29_CAPTURA_REAL_BLOQUEADA")
"""PLADICOP V23: captura supervisada de resultados filtrados como Vigente.
No modifica la base publica ni activa extraccion desatendida.
Requiere pladicop_navegador_v20.py y pladicop_json_v20.py.
"""
import csv
import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright
from pladicop_navegador_v20 import leer_pagina
from pladicop_json_v20 import extraer_json

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'data' / 'processed'
BASE = ROOT / 'data' / 'public' / 'pladicop_cotizaciones_v17.csv'
URL = 'https://prod6.seace.gob.pe/buscador-publico/contrataciones'
TZ = ZoneInfo('America/Lima')


def fecha(valor):
    for fmt in ('%d/%m/%Y %H:%M:%S', '%d/%m/%Y %H:%M'):
        try:
            return datetime.strptime(str(valor or '').strip(), fmt).replace(tzinfo=TZ)
        except ValueError:
            pass
    return None


def ids_publicados():
    if not BASE.is_file():
        raise RuntimeError('BASE_PUBLICA_AUSENTE')
    with BASE.open(encoding='utf-8-sig', newline='') as fh:
        lector = csv.DictReader(fh)
        campos = lector.fieldnames or []
        columna = next((c for c in campos if c.lower().replace('_', '') in ('idcontrato', 'id', 'codigocontrato')), None)
        if not columna:
            raise RuntimeError('COLUMNA_ID_NO_ENCONTRADA: ' + repr(campos))
        return {str(fila[columna]).strip() for fila in lector if str(fila.get(columna) or '').strip()}


def guardar(nombre, data):
    OUT.mkdir(parents=True, exist_ok=True)
    ruta = OUT / nombre
    tmp = ruta.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp.replace(ruta)
    return ruta


def main():
    # V29_BLOQUEO_MAIN_INDIRECTO
    raise RuntimeError("V29_CAPTURA_INDIRECTA_PROHIBIDA")
    # V29_LIMPIEZA_PRECAPTURA
    # Retirar artefactos importables anteriores antes de capturar.
    # Solo se permite dentro del laboratorio autorizado.
    if ROOT.resolve() != Path(
        r"C:\radar_pladicop_v29_laboratorio"
    ).resolve():
        raise RuntimeError("DIRECTORIO_CAPTURA_NO_AUTORIZADO")

    for nombre in (
        "pladicop_v23_nuevos.json",
        "pladicop_v23_abiertos.json",
    ):
        anterior = OUT / nombre
        if anterior.is_file():
            anterior.unlink()

    print("V29_ARCHIVOS_IMPORTABLES_ANTERIORES=RETIRADOS")

    publicados = ids_publicados()
    capturados = {}
    estado = 'INCOMPLETA'
    paginas = 0
    totales = []
    error = ''
    hora_inicio = datetime.now(TZ)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=False)
        page = browser.new_page()
        try:
            page.goto(URL, wait_until='domcontentloaded', timeout=60000)

            print('ESPERANDO_CARGA_PLADICOP=SI')

            page.locator(
                '.mat-mdc-paginator-range-label'
            ).wait_for(
                state='visible',
                timeout=60000
            )

            print('BUSCADOR_PLADICOP=CARGADO')

            # Selector V29 validado en pruebas sinteticas.
            from selector_estado_v29_2_candidato import seleccionar_vigente

            resultado_filtro = seleccionar_vigente(page)

            print("FILTRO_VIGENTE=OK")

            # Ejecutar la busqueda.
            page.get_by_role(
                "button", name="Buscar", exact=True
            ).click()

            # Configurar 100 contratos por pagina.
            paginador = page.locator("mat-paginator mat-select")
            paginador.wait_for(state="visible", timeout=60000)
            paginador.click()

            page.get_by_role(
                "option", name="100", exact=True
            ).click()

            # Confirmar rango 1-100 antes de comenzar.
            page.wait_for_function(
                """() => {
                    const texto = document.querySelector(
                        '.mat-mdc-paginator-range-label'
                    )?.textContent || '';

                    const numeros = texto.match(/[0-9]+/g) || [];

                    return numeros.length >= 3 &&
                           Number(numeros[0]) === 1 &&
                           Number(numeros[1]) === 100 &&
                           Number(numeros[2]) >= 100;
                }""",
                timeout=60000
            )

            print("PAGINACION_100=OK")

            # V29.3: esperar tarjetas, no solo el rango del paginador.
            page.wait_for_function(
                r"""() => {
                    const etiqueta = document.querySelector(
                        '.mat-mdc-paginator-range-label'
                    );
                    const texto = etiqueta?.textContent || '';
                    const numeros = texto.match(/[0-9]+/g) || [];
                    if (numeros.length < 3) return false;

                    const inicio = Number(numeros[0]);
                    const fin = Number(numeros[1]);
                    const esperado = fin - inicio + 1;

                    const tarjetas = document.querySelectorAll(
                        '.container-results .container-card'
                    );

                    return inicio === 1 &&
                           esperado === 100 &&
                           tarjetas.length === esperado;
                }""",
                timeout=60000
            )

            print("CAPTURA_AUTOMATICA=INICIADA")

            for n in range(1, 101):
                actual = leer_pagina(page)
                if n == 1 and actual['inicio'] != 1:
                    raise RuntimeError('INICIO_NO_ES_PAGINA_1')
                if n > 1:
                    esperado = (paginas * 100) + 1
                    if actual['inicio'] != esperado:
                        raise RuntimeError(f'SALTO_PAGINA: esperado {esperado}, obtenido {actual["inicio"]}')
                totales.append(actual['total'])
                temporal = OUT / 'pladicop_v23_pagina_temporal.json'
                extraidos = extraer_json(page, temporal)['data']
                for c in extraidos:
                    if str(c.get('nomEstadoContrato', '')).strip().lower() != 'vigente':
                        raise RuntimeError('TARJETA_NO_VIGENTE: ' + str(c.get('idContrato')))
                    identificador = str(c['idContrato']).strip()
                    if identificador in capturados:
                        raise RuntimeError('ID_REPETIDO_ENTRE_PAGINAS: ' + identificador)
                    capturados[identificador] = c
                paginas += 1
                print(f'PAGINA={paginas} RANGO={actual["rango"]} CAPTURADOS={len(capturados)}')
                if not actual['siguienteHabilitado']:
                    if len(capturados) != actual['total']:
                        raise RuntimeError('ULTIMA_PAGINA_CON_COBERTURA_INCOMPLETA')
                    if len(set(totales)) != 1:
                        raise RuntimeError('TOTAL_CAMBIO_DURANTE_RECORRIDO')
                    estado = 'COMPLETA_VALIDADA'
                    break
                anterior_inicio = actual['inicio']
                ids_anteriores = actual['ids']
                page.locator('button[aria-label="Siguiente página"]').click(timeout=10000)
                # Angular puede actualizar el paginador antes que las tarjetas.
                # Esperar al nuevo rango Y a un conjunto completo de IDs diferentes.
                # Esperar la nueva pagina usando el lector validado.
                import time

                limite = time.monotonic() + 60
                ultima_observacion = ""

                while time.monotonic() < limite:
                    try:
                        siguiente = leer_pagina(page)

                        rango_correcto = (
                            siguiente["inicio"] == anterior_inicio + 100
                        )

                        ids_correctos = (
                            len(siguiente["ids"]) ==
                            siguiente["fin"] - siguiente["inicio"] + 1
                            and len(siguiente["ids"]) ==
                            len(set(siguiente["ids"]))
                        )

                        total_estable = (
                            siguiente["total"] == totales[0]
                        )

                        ids_diferentes = (
                            not set(siguiente["ids"]).intersection(
                                ids_anteriores
                            )
                        )

                        if (
                            rango_correcto
                            and ids_correctos
                            and ids_diferentes
                            and total_estable
                        ):
                            print(
                                "PAGINA_SIGUIENTE_VALIDADA=",
                                siguiente["rango"]
                            )
                            break

                        ultima_observacion = (
                            f"rango={siguiente['rango']}, "
                            f"ids={len(siguiente['ids'])}, "
                            f"rango_correcto={rango_correcto}, "
                            f"ids_diferentes={ids_diferentes}"
                        )

                    except (ValueError, KeyError) as exc:
                        ultima_observacion = str(exc)

                    page.wait_for_timeout(1000)

                else:
                    raise RuntimeError(
                        "PAGINACION_NO_SINCRONIZADA: "
                        + ultima_observacion
                    )

            else:
                raise RuntimeError('LIMITE_SEGURIDAD_100_PAGINAS')
        except Exception as exc:
            error = str(exc)
            print('CAPTURA_DETENIDA=', error)
        finally:
            browser.close()

    ahora = datetime.now(TZ)
    abiertos, nuevos = [], []
    descartes = {'vencidos': 0, 'no_iniciados': 0, 'fecha_invalida': 0}
    for c in capturados.values():
        ini, fin = fecha(c.get('fecIniCotizacion')), fecha(c.get('fecFinCotizacion'))
        if ini is None or fin is None or ini > fin:
            descartes['fecha_invalida'] += 1
        elif ahora < ini:
            descartes['no_iniciados'] += 1
        elif ahora >= fin:
            descartes['vencidos'] += 1
        else:
            abiertos.append(c)
            if str(c['idContrato']).strip() not in publicados:
                nuevos.append(c)

    metadata = {
        'fuente': 'PLADICOP_DOM_PUBLICO',
        'capturadoEn': ahora.isoformat(),
        'inicioCaptura': hora_inicio.isoformat(),
        'paginasCapturadas': paginas,
        'totalExportado': len(capturados),
        'finalizacion': estado,
        'totalesObservados': totales,
        'error': error,
    }
    bruto = guardar('pladicop_v23_captura_revision.json', {**metadata, 'data': list(capturados.values())})
    # Los archivos de oportunidades solo se emiten si el recorrido fue completo y estable.
    if estado == 'COMPLETA_VALIDADA' and descartes['fecha_invalida'] == 0:
        abiertos_path = guardar('pladicop_v23_abiertos.json', {**metadata, 'totalExportado': len(abiertos), 'data': abiertos})
        nuevos_path = guardar('pladicop_v23_nuevos.json', {**metadata, 'totalExportado': len(nuevos), 'data': nuevos})
        print('JSON_ABIERTOS=', abiertos_path)
        print('JSON_NUEVOS=', nuevos_path)
    else:
        print('JSON_IMPORTABLE=NO')
    print('=== RESUMEN V23 ===')
    print('ESTADO=', estado)
    print('PAGINAS=', paginas)
    print('CAPTURADOS=', len(capturados))
    print('ABIERTOS=', len(abiertos))
    print('NUEVOS_CANDIDATOS=', len(nuevos))
    print('DESCARTES=', descartes)
    print('CAPTURA_REVISION=', bruto)
    print('BASE_PUBLICA_MODIFICADA=NO')



# V25_CONTROL_EJECUCION_SEGURA
if __name__ == "__main__":
    import sys
    import json
    from datetime import datetime, timezone

    inicio_ejecucion = datetime.now(timezone.utc)

    try:
        main()
    except Exception as exc:
        print("CAPTURA_V25=ERROR_EJECUCION", repr(exc))
        sys.exit(1)

    revision = Path(
        "data/processed/pladicop_v23_captura_revision.json"
    )

    if not revision.is_file():
        print("CAPTURA_V25=ERROR_SIN_REVISION")
        sys.exit(1)

    try:
        resultado = json.loads(
            revision.read_text(encoding="utf-8-sig")
        )

        fecha = datetime.fromisoformat(
            resultado["capturadoEn"]
        )

        if fecha.tzinfo is None:
            raise ValueError("FECHA_SIN_ZONA_HORARIA")

    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("CAPTURA_V25=ERROR_REVISION", repr(exc))
        sys.exit(1)

    if fecha.astimezone(timezone.utc) < inicio_ejecucion:
        print("CAPTURA_V25=ERROR_REVISION_ANTIGUA")
        sys.exit(1)

    if resultado.get("finalizacion") != "COMPLETA_VALIDADA":
        print("CAPTURA_V25=ERROR_INCOMPLETA")
        sys.exit(1)

    print("CAPTURA_V25=PASS")
