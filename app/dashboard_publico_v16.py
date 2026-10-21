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


def main():
    st.set_page_config(
        page_title="Radar Contrataciones Peru v1.7",
        page_icon="📋",
        layout="wide",
    )

    st.title("Radar Contrataciones Perú")
    st.caption("Version 1.7 | Explorador de contrataciones menores")

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

    a, b, c, d = st.columns(4)
    a.metric("Registros históricos", len(contratos))
    b.metric("Bienes historicos", bienes)
    c.metric("Servicios historicos", servicios)
    d.metric("Activos verificados en tiempo real", 0)

    tabs = st.tabs([
        "Contrataciones PLADICOP",
        "Explorador",
        "Oportunidades potenciales",
        "Entidades y categorías",
        "Histórico",
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

        candidatos = [
            r for r in oportunidades
            if r["Clasificacion"] == "Candidato a cotizacion"
        ]

        c1, c2, c3 = st.columns(3)

        c1.metric("Contratos PLADICOP", len(oportunidades))
        c2.metric("Candidatos a cotizacion", len(candidatos))
        c3.metric(
            "No clasificados como candidatos",
            len(oportunidades) - len(candidatos)
        )

        st.warning(
            "La vigencia se calcula a partir de la ultima "
            "captura disponible. Verifica cada oportunidad "
            "en SEACE antes de cotizar."
        )

        busqueda = st.text_input(
            "Buscar entidad, codigo o descripcion",
            key="busqueda_pladicop_activos"
        ).strip().casefold()

        vista = st.radio(
            "Registros que deseas consultar",
            ["Todos los contratos", "Solo candidatos"],
            horizontal=True,
            key="vista_pladicop_v17",
        )

        registros = (
            list(oportunidades)
            if vista == "Todos los contratos"
            else list(candidatos)
        )

        if busqueda:
            registros = [
                r for r in registros
                if busqueda in " ".join(
                    str(valor) for valor in r.values()
                ).lower()
            ]

        registros.sort(
            key=lambda r: str(r.get("Cierre", "")),
            reverse=True,
        )

        st.write(f"**{len(registros)} registros encontrados**")

        if registros:
            tamano = st.selectbox(
                "Contratos por pagina",
                [10, 25, 50],
                index=1,
                key="tamano_pladicop_v17",
            )

            total_paginas = (
                len(registros) + tamano - 1
            ) // tamano

            pagina = st.number_input(
                "Pagina",
                min_value=1,
                max_value=total_paginas,
                value=1,
                step=1,
                key="pagina_pladicop_v17",
            )

            desde = (pagina - 1) * tamano
            pagina_registros = registros[
                desde:desde + tamano
            ]

            st.caption(
                f"Mostrando {desde + 1}-"
                f"{desde + len(pagina_registros)} "
                f"de {len(registros)} contratos"
            )

            st.dataframe(
                pagina_registros,
                use_container_width=True,
                hide_index=True,
                column_order=[
                    "ID",
                    "Codigo",
                    "Entidad",
                    "Objeto",
                    "Descripcion",
                    "Inicio",
                    "Cierre",
                    "Estado PLADICOP",
                    "Verificacion"
                ]
            )
        else:
            st.info(
                "No existen registros para los filtros "
                "seleccionados."
            )

        st.link_button(
            "Verificar en SEACE",
            URL_SEACE
        )

    with tabs[1]:
        st.subheader("Explorador de contratos")

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
        st.subheader("Oportunidades comerciales potenciales")

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

        st.metric("Antecedentes relacionados", len(encontrados))

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
        st.subheader("Histórico completo")

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
