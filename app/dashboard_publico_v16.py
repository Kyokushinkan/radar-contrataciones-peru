from pathlib import Path
import sys
from collections import Counter
from datetime import date, datetime

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
from dashboard_datos_publicos_v15 import cargar_contratos_publicos


URL_SEACE = "https://prod6.seace.gob.pe/buscador-publico/"


def tipo_legible(registro):
    return (
        "Bienes"
        if registro["tipo_oportunidad"] == "suministro"
        else "Servicios"
    )


def enlace_oficial(registro):
    identificador = str(registro["idContrato"]).strip()
    if identificador.isdecimal():
        return URL_SEACE + "contrataciones/" + identificador
    return None


def mostrar_contratos(registros, clave):
    if not registros:
        st.info("No se encontraron registros con estos filtros.")
        return

    por_pagina = st.selectbox(
        "Registros por página",
        [10, 25, 50],
        key=f"tam_{clave}",
    )

    paginas = max(
        1,
        (len(registros) + por_pagina - 1) // por_pagina,
    )

    pagina = st.number_input(
        "Página",
        min_value=1,
        max_value=paginas,
        value=1,
        key=f"pag_{clave}",
    )

    inicio = (pagina - 1) * por_pagina

    st.caption(
        f"{len(registros)} registros | Página {pagina} de {paginas}"
    )

    for registro in registros[inicio:inicio + por_pagina]:
        titulo = f'{registro["codigo"]} | {registro["entidad"]}'

        with st.expander(titulo):
            st.write("**Descripción:**", registro["descripcion"])
            st.write("**Tipo:**", tipo_legible(registro))
            st.write("**Categoría:**", registro["categoria"])
            st.write(
                "**Estado histórico:**",
                registro["estado_administrativo"],
            )
            st.write("**Inicio:**", registro["inicio"])
            st.write("**Cierre:**", registro["cierre"])
            st.write("**ID:**", registro["idContrato"])

            url = enlace_oficial(registro)

            if url:
                st.link_button("Ver detalle en SEACE", url)

            st.link_button(
                "Buscar código en SEACE",
                URL_SEACE,
            )

            st.caption(
                "Si el enlace directo no muestra información, "
                "utiliza el buscador oficial con el código indicado."
            )


# PLAZOS_V21: fechas de cotizacion, siempre hora local de Lima.
def _fecha_plazo_v21(valor):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    texto = str(valor or "").strip()
    for formato in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(texto, formato).replace(tzinfo=ZoneInfo("America/Lima"))
        except ValueError:
            continue
    return None


def _plazo_v21(registro, ahora):
    inicio = _fecha_plazo_v21(registro.get("Inicio"))
    cierre = _fecha_plazo_v21(registro.get("Cierre"))
    if cierre is None or inicio is None or cierre < inicio:
        return "Sin fecha verificable", "—", None
    if ahora > cierre:
        return "Plazo vencido", "Vencido", cierre
    if ahora < inicio:
        return "Proximo a iniciar", "Aun no inicia", cierre
    segundos = max(0, int((cierre - ahora).total_seconds()))
    dias, resto = divmod(segundos, 86400)
    horas, minutos = divmod(resto, 3600)
    return "Plazo abierto", f"{dias} d {horas} h {minutos // 60} min", cierre


def main():
    st.set_page_config(
        page_title="Radar Contrataciones Peru v2.1",
        page_icon="📋",
        layout="wide",
    )

    st.title("Radar Contrataciones Perú")
    st.caption("Version 2.1 | Radar de oportunidades y plazos de cotizacion")

    contratos = cargar_contratos_publicos()

    st.warning(
        "Los registros disponibles son históricos. "
        "No se ha confirmado que estén abiertos para cotizar."
    )

    bienes = sum(
        c["tipo_oportunidad"] == "suministro"
        for c in contratos
    )

    servicios = sum(
        c["tipo_oportunidad"] == "servicio"
        for c in contratos
    )

    # PORTADA_V20: separar PLADICOP de los antecedentes historicos.
    from pathlib import Path as _PathV20
    import csv as _csv_v20
    _csv_publico_v20 = (
        _PathV20(__file__).resolve().parents[1]
        / "data" / "public" / "pladicop_cotizaciones_v17.csv"
    )
    _total_pladicop_v20 = 0
    if _csv_publico_v20.is_file():
        with _csv_publico_v20.open(encoding="utf-8-sig", newline="") as _f_v20:
            _total_pladicop_v20 = sum(1 for _ in _csv_v20.DictReader(_f_v20))

    a, b, c, d = st.columns(4)
    a.metric("Contratos PLADICOP", _total_pladicop_v20)
    b.metric("Base historica independiente", len(contratos))
    c.metric("Bienes / servicios historicos", f"{bienes} / {servicios}")
    d.metric("Verificados en tiempo real", 0)
    st.caption("PLADICOP: capturas consolidadas. La base historica es independiente; no se suman ambos universos.")

    tabs = st.tabs([
        "Contrataciones PLADICOP",
        "Explorador historico (99)",
        "Antecedentes por rubro",
        "Entidades y categorías",
        "Archivo historico",
    ])

    with tabs[0]:
        # PLADICOP_ACTIVOS_V16
        from oportunidades_pladicop_v16 import cargar_oportunidades

        st.subheader("Contrataciones menores - PLADICOP")

        # METADATOS_PORTADA_V17
        import csv
        from datetime import datetime
        from zoneinfo import ZoneInfo

        ruta_csv_v17 = (
            Path(__file__).resolve().parents[1]
            / "data/public/pladicop_cotizaciones_v17.csv"
        )

        if ruta_csv_v17.exists():
            with ruta_csv_v17.open(
                "r", encoding="utf-8-sig", newline=""
            ) as archivo_csv:
                filas_v17 = list(csv.DictReader(archivo_csv))

            fechas_publicacion = []

            for fila_v17 in filas_v17:
                valor = (fila_v17.get("fecPublica") or "").strip()
                if valor:
                    try:
                        fechas_publicacion.append(
                            datetime.strptime(
                                valor, "%d/%m/%Y %H:%M:%S"
                            )
                        )
                    except ValueError:
                        pass

            fecha_mas_reciente = (
                max(fechas_publicacion).strftime("%d/%m/%Y %H:%M")
                if fechas_publicacion
                else "No disponible en CSV"
            )

            fecha_archivo = datetime.fromtimestamp(
                ruta_csv_v17.stat().st_mtime,
                ZoneInfo("America/Lima")
            ).strftime("%d/%m/%Y %H:%M")

            st.info(
                "\n".join([
                    "**Estado de la base PLADICOP**",
                    "",
                    f"Registros consolidados: **{len(filas_v17)}**",
                    f"Publicacion mas reciente: **{fecha_mas_reciente}**",
                    f"Fecha tecnica del archivo: **{fecha_archivo} (Lima)**",
                    "Descarga automatica: **no habilitada**",
                    "",
                    "Datos de capturas consolidadas, no en tiempo real."
                ])
            )
        else:
            st.info(
                "CSV incremental v1.7 no disponible. "
                "Se utilizar? la fuente de respaldo."
            )


        st.caption(
            "Oportunidades obtenidas de una captura local. "
            "No verificadas en tiempo real."
        )

        try:
            oportunidades = cargar_oportunidades()
        except (OSError, ValueError) as exc:
            st.error(f"Error al cargar datos: {exc}")
            oportunidades = []

        # PLAZOS_V21: evaluar las fechas reales, no el estado de captura.
        from zoneinfo import ZoneInfo
        ahora_lima = datetime.now(ZoneInfo("America/Lima"))
        todos_plazos = []
        for original in oportunidades:
            fila = dict(original)
            estado, restante, cierre_dt = _plazo_v21(fila, ahora_lima)
            fila["Estado del plazo"] = estado
            fila["Tiempo restante"] = restante
            fila["Estado en captura"] = fila.pop("Estado PLADICOP", "")
            fila["_cierre_v21"] = cierre_dt
            todos_plazos.append(fila)

        abiertos = [r for r in todos_plazos if r["Estado del plazo"] == "Plazo abierto"]
        proximos = [r for r in todos_plazos if r["Estado del plazo"] == "Proximo a iniciar"]
        vencidos = [r for r in todos_plazos if r["Estado del plazo"] == "Plazo vencido"]
        desconocidos = [r for r in todos_plazos if r["Estado del plazo"] == "Sin fecha verificable"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Contratos PLADICOP", len(todos_plazos))
        c2.metric("Con plazo abierto (segun captura)", len(abiertos))
        c3.metric("Proximos a iniciar", len(proximos))
        c4.metric("Plazo vencido", len(vencidos))
        st.caption(
            f"{len(desconocidos)} sin fecha verificable. "
            "Las fechas son de capturas historicas, no una confirmacion en tiempo real. "
            "Antes de cotizar, verifica el expediente oficial."
        )

        busqueda = st.text_input(
            "Buscar entidad, codigo o descripcion",
            key="busqueda_pladicop_activos"
        ).strip().casefold()
        vista = st.radio(
            "Registros que deseas consultar",
            ["Plazo abierto", "Proximos a iniciar", "Todos los contratos", "Plazo vencido", "Sin fecha verificable"],
            horizontal=True,
            key="vista_pladicop_v21",
        )
        grupos_v21 = {
            "Plazo abierto": abiertos,
            "Proximos a iniciar": proximos,
            "Todos los contratos": todos_plazos,
            "Plazo vencido": vencidos,
            "Sin fecha verificable": desconocidos,
        }
        registros = list(grupos_v21[vista])
        if busqueda:
            registros = [
                r for r in registros
                if busqueda in " ".join(str(v) for k, v in r.items() if not k.startswith("_")).casefold()
            ]
        # Priorizar cierres proximos; los que no tienen fecha van al final.
        registros.sort(key=lambda r: (
            r["_cierre_v21"] is None,
            r["_cierre_v21"] or datetime.max.replace(tzinfo=ZoneInfo("America/Lima"))
        ))
        st.write(f"**{len(registros)} registros encontrados**")
        if registros:
            tamano = st.selectbox(
                "Contratos por pagina", [10, 25, 50], index=1,
                key="tamano_pladicop_v21"
            )
            total_paginas = (len(registros) + tamano - 1) // tamano
            pagina = st.number_input(
                "Pagina", min_value=1, max_value=total_paginas,
                value=1, step=1, key="pagina_pladicop_v21"
            )
            desde = (pagina - 1) * tamano
            pagina_registros = registros[desde:desde + tamano]
            st.caption(f"Mostrando {desde + 1}-{desde + len(pagina_registros)} de {len(registros)} contratos")
            filas_tabla = []
            for fila in pagina_registros:
                item = {k: v for k, v in fila.items() if not k.startswith("_")}
                identificador = str(item.get("ID", "")).strip()
                item["Abrir proceso"] = (
                    "https://prod6.seace.gob.pe/buscador-publico/contrataciones/" + identificador
                    if identificador.isdigit() else None
                )
                filas_tabla.append(item)
            st.dataframe(
                filas_tabla,
                use_container_width=True,
                hide_index=True,
                column_order=[
                    "Abrir proceso", "ID", "Codigo", "Entidad", "Objeto",
                    "Descripcion", "Inicio", "Cierre", "Estado del plazo",
                    "Tiempo restante", "Estado en captura", "Verificacion"
                ],
                column_config={
                    "Abrir proceso": st.column_config.LinkColumn(
                        "Abrir proceso", display_text="Ver expediente",
                        help="Verificar directamente en PLADICOP antes de cotizar"
                    )
                },
            )
        else:
            st.info("No existen registros para el filtro seleccionado.")

        st.link_button(
            "Verificar en SEACE",
            URL_SEACE
        )

    with tabs[1]:
        st.subheader("Explorador de la base historica independiente")

        buscar = st.text_input(
            "Buscar",
            placeholder="Código, entidad, descripción o categoría",
            key="explorar_buscar",
        )

        tipos = st.multiselect(
            "Tipo de contratación",
            ["Bienes", "Servicios"],
            default=["Bienes", "Servicios"],
            key="explorar_tipo",
        )

        categorias = sorted({
            c["categoria"]
            for c in contratos
            if c["categoria"].strip()
        })

        seleccion = st.multiselect(
            "Categoría",
            categorias,
            key="explorar_categoria",
        )

        filtrados = []

        for contrato in contratos:
            texto = " ".join(
                str(contrato.get(campo, ""))
                for campo in (
                    "codigo",
                    "entidad",
                    "descripcion",
                    "categoria",
                )
            ).casefold()

            if buscar.strip().casefold() not in texto:
                continue

            if tipo_legible(contrato) not in tipos:
                continue

            if seleccion and contrato["categoria"] not in seleccion:
                continue

            filtrados.append(contrato)

        mostrar_contratos(filtrados, "explorador")

    with tabs[2]:
        st.subheader("Antecedentes comerciales por rubro (base historica)")

        st.caption(
            "Búsqueda de antecedentes por rubro. "
            "No representa oportunidades actualmente abiertas."
        )

        grupos = {
            "Limpieza e higiene": [
                "limpieza", "papel", "higien",
                "escoba", "detergente", "desinfect",
            ],
            "Oficina y útiles": [
                "oficina", "escritorio", "toner",
                "tóner", "lapicero", "archivador",
            ],
            "Tecnología": [
                "computadora", "laptop", "impresora",
                "software", "informática",
            ],
            "Mantenimiento": [
                "mantenimiento", "reparación",
                "reparacion", "instalación",
                "instalacion",
            ],
            "Aire acondicionado": [
                "aire acondicionado",
                "climatización", "climatizacion",
            ],
        }

        rubro = st.selectbox(
            "Seleccionar rubro comercial",
            list(grupos),
        )

        terminos = grupos[rubro]

        encontrados = [
            contrato
            for contrato in contratos
            if any(
                termino in (
                    contrato["descripcion"] + " "
                    + contrato["categoria"]
                ).casefold()
                for termino in terminos
            )
        ]

        st.metric("Registros historicos relacionados (no abiertos)", len(encontrados))

        mostrar_contratos(encontrados, "potenciales")

    with tabs[3]:
        st.subheader("Entidades compradoras")

        entidades = Counter(
            c["entidad"] for c in contratos
        )

        st.dataframe(
            [
                {
                    "Entidad": entidad,
                    "Registros históricos": cantidad,
                }
                for entidad, cantidad in entidades.most_common()
            ],
            use_container_width=True,
            hide_index=True,
        )

        st.subheader("Categorías registradas")

        categorias_contador = Counter(
            c["categoria"] for c in contratos
        )

        st.dataframe(
            [
                {
                    "Categoría": categoria,
                    "Registros históricos": cantidad,
                }
                for categoria, cantidad
                in categorias_contador.most_common()
            ],
            use_container_width=True,
            hide_index=True,
        )

    with tabs[4]:
        st.subheader("Archivo historico independiente (99 registros)")

        st.caption(
            "Base histórica conservada para consulta y análisis."
        )

        mostrar_contratos(contratos, "historico")

    st.divider()
    st.caption(
        "Fuente: registros históricos PLADICOP. "
        "Actualización automática de nuevas contrataciones: pendiente."
    )


if __name__ == "__main__":
    main()
