"""Panel privado v1.4. Ejecutar con Streamlit desde la raíz del proyecto."""
from pathlib import Path
import sys

# Streamlit ejecuta este archivo por ruta; resolver imports sin depender del cwd.
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import streamlit as st

from app.dashboard_datos_v14 import (
    ADVERTENCIA, FILTROS, cargar_datos, exportar_csv, ficha, filtrar_datos, resumen,
)


def main():
    st.set_page_config(page_title='Radar Contrataciones Perú', page_icon='📋', layout='wide')
    if st.get_option('server.address') != '127.0.0.1' or st.get_option('browser.gatherUsageStats'):
        st.error('Configuración no permitida: use 127.0.0.1 y desactive gatherUsageStats.')
        st.stop()
    st.title('Radar Contrataciones Perú')
    st.caption('Panel privado · v1.4 · Evaluación v1.3 · Consulta local de solo lectura')
    st.warning(ADVERTENCIA)
    try:
        datos = cargar_datos()
    except (OSError, ValueError) as exc:
        st.error(f'No se pudo leer la evaluación local: {exc}')
        st.stop()

    st.subheader('Resumen ejecutivo')
    for column, (label, value) in zip(st.columns(6), resumen(datos).items()):
        column.metric(label, value)
    st.caption('Resumen del lote completo. Documentación revisada incluye revisiones con limitaciones; no implica elegibilidad.')
    counts = datos['decision_v13'].value_counts().rename_axis('Decisión v1.3').reset_index(name='Contratos')
    st.dataframe(counts, hide_index=True, width='stretch')

    st.sidebar.title('Explorar contratos')
    query = st.sidebar.text_input('Buscar por código, descripción, entidad o ID', key='busqueda')
    filters = {key: st.sidebar.multiselect(label, sorted(datos[key].unique()), key=key)
               for key, label in FILTROS.items()}
    st.sidebar.caption('Filtros combinados con Y. Sin selección: todas las opciones. Búsqueda literal sin distinguir tildes ni mayúsculas.')
    filtered = filtrar_datos(datos, filters, query)
    st.subheader(f'Resultados filtrados · {len(filtered)} de {len(datos)}')
    st.caption('Orden de prioridad de verificación del motor v1.3. “Vigente” es un estado administrativo registrado, no una cotización abierta.')
    columns = {'orden_verificacion_v13': 'Orden', 'idContrato': 'ID', 'codigo': 'Código',
               'entidad': 'Entidad', 'tipo_oportunidad': 'Tipo', 'categoria_v08': 'Categoría',
               'afinidad_profesional_v13': 'Afinidad', 'decision_v13': 'Decisión',
               'estado_revision_documental': 'Estado documental',
               'situacion_temporal_en_captura': 'Situación en captura'}
    st.dataframe(filtered[list(columns)].rename(columns=columns), hide_index=True, width='stretch')
    st.download_button('Descargar resultados filtrados (CSV)', data=exportar_csv(filtered),
                       file_name='radar_resultados_filtrados_v14.csv', mime='text/csv',
                       disabled=filtered.empty)
    if filtered.empty:
        st.info('No hay contratos que coincidan. Ajuste los filtros o la búsqueda.')
        return

    st.subheader('Ficha individual')
    labels = filtered.set_index('idContrato')['codigo'].to_dict()
    selected = st.selectbox('Seleccionar contrato', list(labels),
                            format_func=lambda key: f'{key} · {labels[key]}', key='contrato')
    detail = ficha(filtered, selected)
    for message in detail['limitaciones'][:2]:
        st.warning(message)
    general, documents, commercial = st.tabs(['Contrato y decisión', 'Requisitos documentales', 'Evaluación comercial'])
    with general:
        for label, value in detail['detalle'].items():
            st.caption(label)
            st.text(value)  # Texto de fuente local, sin interpretar HTML ni enlaces.
    with documents:
        st.dataframe(pd.DataFrame(detail['requisitos']), hide_index=True, width='stretch')
        for message in detail['limitaciones'][2:]:
            st.text(message)
    with commercial:
        st.dataframe(pd.DataFrame(detail['comercial'].items(), columns=['Campo', 'Valor registrado']),
                     hide_index=True, width='stretch')


if __name__ == '__main__':
    main()
