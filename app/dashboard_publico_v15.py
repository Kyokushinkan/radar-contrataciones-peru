"""Radar Contrataciones Peru - Dashboard publico v1.5."""

import streamlit as st

from app.dashboard_datos_publicos_v15 import cargar_contratos_publicos


def main():
    st.set_page_config(
        page_title="Radar Contrataciones Peru",
        page_icon="📋",
        layout="wide",
    )

    st.title("Radar Contrataciones Perú")
    st.caption("Panel público v1.5 | Contratos menores")

    st.warning(
        "Información histórica de referencia. "
        "La disponibilidad actual de los contratos "
        "debe verificarse en las fuentes oficiales."
    )

    try:
        contratos = cargar_contratos_publicos()
    except (OSError, ValueError) as error:
        st.error(f"Error en datos públicos: {error}")
        st.stop()

    st.metric("Contratos publicados", len(contratos))

    if not contratos:
        st.info(
            "El dashboard está preparado. "
            "Los contratos públicos se incorporarán "
            "después de validar la información."
        )
        return

    tipos = {
        "suministro": "Bienes",
        "servicio": "Servicios",
    }

    for contrato in contratos:
        contrato["tipo"] = tipos.get(
            contrato["tipo_oportunidad"],
            contrato["tipo_oportunidad"],
        )

    opciones = ["Todos", "Bienes", "Servicios"]
    seleccion = st.selectbox("Tipo de oportunidad", opciones)

    if seleccion != "Todos":
        contratos = [
            contrato for contrato in contratos
            if contrato["tipo"] == seleccion
        ]

    busqueda = st.text_input("Buscar contrato, entidad o descripción")

    if busqueda.strip():
        texto = busqueda.casefold().strip()
        contratos = [
            contrato for contrato in contratos
            if any(
                texto in contrato[campo].casefold()
                for campo in (
                    "codigo",
                    "entidad",
                    "descripcion",
                )
            )
        ]

    st.subheader(f"Resultados: {len(contratos)}")

    st.dataframe(
        [
            {
                "Código": contrato["codigo"],
                "Entidad": contrato["entidad"],
                "Descripción": contrato["descripcion"],
                "Tipo": contrato["tipo"],
                "Categoría": contrato["categoria"],
                "Estado registrado": contrato["estado_administrativo"],
                "Inicio": contrato["inicio"],
                "Cierre": contrato["cierre"],
            }
            for contrato in contratos
        ],
        hide_index=True,
        width="stretch",
    )


if __name__ == "__main__":
    main()
