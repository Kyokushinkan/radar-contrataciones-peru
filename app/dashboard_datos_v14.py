"""Lectura y consulta local, sin dependencias de interfaz ni acceso a red."""

from pathlib import Path
import csv
import io
import unicodedata

import pandas as pd

FUENTE = Path(__file__).resolve().parents[1] / 'data/processed/evaluacion_oportunidades_v13.csv'
ADVERTENCIA = ('Los registros proceden de capturas históricas de PLADICOP. '
              'La disponibilidad actual, la elegibilidad y la rentabilidad requieren verificación independiente.')
FILTROS = {
    'entidad': 'Entidad pública', 'tipo_oportunidad': 'Tipo de oportunidad',
    'categoria_v08': 'Categoría v0.8', 'afinidad_profesional_v13': 'Afinidad profesional',
    'decision_v13': 'Decisión orientativa', 'estado_revision_documental': 'Estado documental',
    'situacion_temporal_en_captura': 'Situación temporal registrada',
}
REQUISITOS = {
    'formacion_academica': 'Formación académica', 'experiencia_general': 'Experiencia general',
    'experiencia_especifica': 'Experiencia específica', 'capacitaciones': 'Capacitaciones',
    'inscripcion_habilitacion': 'Inscripción o habilitación',
    'documentacion_administrativa': 'Documentación administrativa',
    'lugar_prestacion': 'Lugar de prestación', 'otros_requisitos': 'Otros requisitos específicos',
}
COMERCIAL = {
    'monto_contractual': 'Monto contractual', 'moneda_monto': 'Moneda del monto',
    'fuente_monto': 'Fuente del monto', 'costos_estimados': 'Costos estimados',
    'moneda_costos': 'Moneda de costos', 'fuente_costos': 'Fuente de costos',
    'gastos_ejecucion': 'Gastos de ejecución', 'margen_bruto_estimado': 'Margen bruto estimado',
    'plazo_ejecucion': 'Plazo de ejecución', 'condiciones_pago': 'Condiciones de pago',
    'rentabilidad_evaluada': 'Rentabilidad evaluada', 'riesgos_comerciales': 'Riesgos comerciales',
    'fuente_comercial': 'Fuente comercial',
}
DETALLE = {
    'idContrato': 'Identificador', 'codigo': 'Código', 'entidad': 'Entidad',
    'descripcion': 'Descripción', 'categoria_v08': 'Categoría v0.8',
    'afinidad_profesional_v13': 'Afinidad profesional orientativa',
    'motivo_afinidad_v13': 'Motivo de afinidad', 'estado_administrativo': 'Estado administrativo registrado',
    'inicio': 'Inicio registrado', 'cierre': 'Cierre registrado', 'evaluado_en': 'Fecha de evaluación histórica',
    'situacion_temporal_en_captura': 'Situación temporal en la captura',
    'disponibilidad_actual': 'Disponibilidad actual', 'elegibilidad_global': 'Elegibilidad documental',
    'estado_revision_documental': 'Estado documental', 'decision_v13': 'Decisión orientativa',
    'motivo_decision_v13': 'Motivo de decisión', 'motivo_elegibilidad': 'Motivo de elegibilidad',
}
SENASA_CAMPOS = ['doc_v11_formacion_academica_detalle', 'doc_v11_capacitacion_detalle',
                 'doc_v11_experiencia_general_exigida', 'doc_v11_experiencia_especifica_exigida',
                 'doc_v11_observaciones_documentales', 'doc_v11_fuente_documental']
REQUERIDAS = (set(FILTROS) | set(COMERCIAL) | set(DETALLE) | set(SENASA_CAMPOS)
              | {'orden_verificacion_v13', 'seleccionado_revision_documental', 'doc_v11_documento_revisado'}
              | {'estado_' + k for k in REQUISITOS} | {'motivo_' + k for k in REQUISITOS})


def cargar_datos(ruta=FUENTE):
    # Path.open impide interpretar una URL como fuente de pandas.
    with Path(ruta).open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames or []
        if len(fields) != len(set(fields)) or not REQUERIDAS <= set(fields):
            raise ValueError('CSV v1.3 con columnas faltantes o duplicadas')
        rows = list(reader)
    if any(None in r or any(v is None for v in r.values()) for r in rows):
        raise ValueError('CSV con filas incompletas o excedentes')
    frame = pd.DataFrame(rows, columns=fields, dtype=str)
    if len(frame) != 100 or frame['idContrato'].nunique() != 100 or frame['idContrato'].str.strip().eq('').any():
        raise ValueError('Se requieren 100 contratos con identificadores únicos')
    if frame['tipo_oportunidad'].value_counts().to_dict() != {'servicio': 84, 'suministro': 16}:
        raise ValueError('Se requieren 16 suministros y 84 servicios')
    order = pd.to_numeric(frame['orden_verificacion_v13'], errors='raise')
    if sorted(order.tolist()) != list(range(1, 101)):
        raise ValueError('Orden de verificación inválido')
    return frame.loc[order.sort_values(kind='stable').index].reset_index(drop=True)


def normalizar(texto):
    return ''.join(c for c in unicodedata.normalize('NFKD', str(texto)).casefold()
                   if not unicodedata.combining(c))


def filtrar_datos(datos, filtros=None, busqueda=''):
    mask = pd.Series(True, index=datos.index)
    for column, values in (filtros or {}).items():
        if column not in FILTROS:
            raise ValueError('Filtro no permitido')
        if values:
            mask &= datos[column].isin(values)
    query = normalizar(busqueda).strip()
    if query:
        matches = pd.Series(False, index=datos.index)
        for column in ['codigo', 'descripcion', 'entidad', 'idContrato']:
            matches |= datos[column].map(normalizar).str.contains(query, regex=False)
        mask &= matches
    return datos.loc[mask].copy()


def presentar(valor):
    # No convierte desconocidos en cero, no, elegible o disponible.
    return str(valor) if valor is not None and str(valor).strip() else 'sin_datos'


def resumen(datos):
    return {
        'Total de contratos': len(datos),
        'Bienes': int(datos['tipo_oportunidad'].eq('suministro').sum()),
        'Servicios': int(datos['tipo_oportunidad'].eq('servicio').sum()),
        'Documentación revisada': int(datos['doc_v11_documento_revisado'].eq('si').sum()),
        'Elegibilidad pendiente': int(datos['elegibilidad_global'].eq('pendiente_verificacion').sum()),
        'Requieren especialista': int(datos['decision_v13'].eq('requiere_especialista').sum()),
    }


def ficha(datos, identificador):
    selected = datos.loc[datos['idContrato'].eq(identificador)]
    if len(selected) != 1:
        raise ValueError('Seleccione un contrato de los resultados filtrados')
    row = selected.iloc[0]
    limitaciones = []
    if identificador == '103654':
        limitaciones = [
            'SENASA: formación académica no legible completamente; capacitaciones no verificadas por recorte documental.',
            'La experiencia exigida no acredita cumplimiento del usuario. Elegibilidad pendiente de verificación.',
        ] + [f'{key}: {presentar(row[key])}' for key in SENASA_CAMPOS]
    return {
        'detalle': {label: presentar(row[key]) for key, label in DETALLE.items()},
        'requisitos': [{'Requisito': label, 'Estado': presentar(row['estado_' + key]),
                       'Motivo registrado': presentar(row['motivo_' + key])} for key, label in REQUISITOS.items()],
        'comercial': {label: presentar(row[key]) for key, label in COMERCIAL.items()},
        'limitaciones': limitaciones,
    }


def exportar_csv(filtrados):
    """CSV UTF-8 con BOM en memoria; conserva campos, valores y orden originales."""
    buffer = io.StringIO(newline='')
    filtrados.to_csv(buffer, index=False, lineterminator='\r\n')
    return buffer.getvalue().encode('utf-8-sig')
