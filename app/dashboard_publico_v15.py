from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
from dashboard_datos_publicos_v15 import cargar_contratos_publicos


def main():
    st.set_page_config(
        page_title="Radar Contrataciones Perú",
        page_icon="📋",
        layout="wide",
    )

    st.title("Radar Contrataciones Perú")
    st.caption("Panel público v1.6 | Contratos menores")

    st.warning(
        "Información histórica de referencia. "
        "La disponibilidad actual debe verificarse "
        "en las fuentes oficiales."
    )

    contratos = cargar_contratos_publicos()

    bienes = sum(
        c["tipo_oportunidad"] == "suministro"
        for c in contratos
    )
    servicios = sum(
        c["tipo_oportunidad"] == "servicio"
        for c in contratos
    )

    a, b, c = st.columns(3)
    a.metric("Contratos", len(contratos))
    b.metric("Bienes", bienes)
    c.metric("Servicios", servicios)

    st.divider()

    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        buscar = st.text_input(
            "Buscar",
            placeholder="Código, entidad o descripción",
        )

    with col2:
        tipo = st.selectbox(
            "Tipo",
            ["Todos", "Bienes", "Servicios"],
        )

    with col3:
        por_pagina = st.selectbox(
            "Registros por página",
            [10, 25, 50],
        )

    filtrados = []

    for contrato in contratos:
        tipo_registro = (
            "Bienes"
            if contrato["tipo_oportunidad"] == "suministro"
            else "Servicios"
        )

        if tipo != "Todos" and tipo_registro != tipo:
            continue

        texto = " ".join(
            str(contrato.get(campo, ""))
            for campo in ("codigo", "entidad", "descripcion")
        ).casefold()

        if buscar.strip().casefold() not in texto:
            continue

        filtrados.append(contrato)

    total = len(filtrados)
    paginas = max(1, (total + por_pagina - 1) // por_pagina)

    pagina = st.number_input(
        "Página",
        min_value=1,
        max_value=paginas,
        value=1,
        step=1,
    )

    inicio = (pagina - 1) * por_pagina
    visibles = filtrados[inicio:inicio + por_pagina]

    st.subheader(f"Resultados: {total}")
    st.caption(f"Página {pagina} de {paginas}")

    for contrato in visibles:
        codigo = contrato["codigo"]
        entidad = contrato["entidad"]

        with st.expander(f"{codigo} | {entidad}"):
            st.write("**Descripción:**", contrato["descripcion"])
            st.write("**Entidad:**", entidad)
            st.write("**Categoría:**", contrato["categoria"])
            st.write(
                "**Tipo:**",
                "Bienes"
                if contrato["tipo_oportunidad"] == "suministro"
                else "Servicios",
            )
            st.write(
                "**Estado registrado:**",
                contrato["estado_administrativo"],
            )
            st.write("**Inicio:**", contrato["inicio"])
            st.write("**Cierre:**", contrato["cierre"])
            st.write("**ID del contrato:**", contrato["idContrato"])

            st.caption(
                "Enlace oficial directo pendiente de verificación. "
                "No se ha confirmado una URL individual para este proceso."
            )

    st.divider()
    st.caption(
        "Fuente: registros históricos capturados de PLADICOP. "
        "Sin actualización automática activa."
    )


if __name__ == "__main__":
    main()
