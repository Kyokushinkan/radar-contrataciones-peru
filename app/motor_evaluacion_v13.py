"""Paso 41. Motor local auditable; ejecutar python -m app.motor_evaluacion_v13.

No cambia categorías ni columnas anteriores. Reutiliza afinidad v0.9 y temas y
alertas v1.0. No tiene reloj, red ni acceso a SQLite. Reglas explícitas v1.3:
especialidad > tema prioritario/categoría alta > afinidad media/baja conocida.
Una categoría sin regla específica no constituye afinidad baja por defecto.
"""

import csv
import hashlib
from collections import Counter
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from pathlib import Path

from app.clasificacion_cm_v2 import normalizar
from app.evaluacion_perfil_v10 import evaluar_servicio
from app.matriz_oportunidades_v12 import PROCESSED, leer_csv
from app.rankings_especializados_v09 import AFINIDAD_PROFESIONAL

SIN_DATOS = "sin_datos_suficientes"
REQUISITOS = (
    "formacion_academica", "experiencia_general", "experiencia_especifica",
    "capacitaciones", "inscripcion_habilitacion", "documentacion_administrativa",
    "lugar_prestacion", "otros_requisitos",
)
ESTADOS = {"acreditado", "no_acreditado", "pendiente_verificacion", "no_exigido", "no_legible"}
TEMAS_ADICIONALES = {
    "administracion_empresas": ("administracion de empresas",),
    "gestion_publica": ("gestion publica",),
    "contrataciones_estado": ("contrataciones del estado", "contratacion publica"),
    "logistica_abastecimiento": ("logistica", "abastecimiento"),
    "gestion_administrativa": ("gestion administrativa",),
    "gestion_presupuestal": ("gestion presupuestal",),
    "gestion_documental": ("gestion documental",),
    "control_patrimonial": ("control patrimonial", "gestion patrimonial"),
}
ESPECIALIZADAS = {
    "ingenieria_proyectos", "servicios_legales", "servicios_farmaceuticos",
    "evaluacion_prestaciones_salud", "apoyo_supervision_obras",
}
DOC_MAP = {
    "formacion_academica": "formacion_academica_detalle",
    "experiencia_general": "experiencia_general_exigida",
    "experiencia_especifica": "experiencia_especifica_exigida",
    "capacitaciones": "capacitacion_detalle",
    "lugar_prestacion": "lugar_prestacion",
    "otros_requisitos": "subcontratacion",
}


def calcular_margen(monto=None, costos=None):
    """Cada entrada: {valor: decimal textual, moneda: PEN/USD, fuente: referencia}.

    Margen bruto = monto - costos directos; porcentaje sobre ingresos.
    No incluye gastos de ejecución ni determina rentabilidad neta. No convierte
    monedas. Retiene fuentes e importes; redondea resultados a 2 decimales.
    Ausencia de datos/fuentes/moneda devuelve sin datos; valores inválidos fallan.
    """
    result = dict(estado=SIN_DATOS, margen_bruto_estimado=SIN_DATOS,
                  margen_porcentaje=SIN_DATOS, moneda=SIN_DATOS,
                  fuente_monto=(monto or {}).get("fuente", ""),
                  fuente_costos=(costos or {}).get("fuente", ""),
                  monto_documentado=(monto or {}).get("valor"),
                  costos_documentados=(costos or {}).get("valor"))
    values = []
    for item in (monto, costos):
        if not item or any(item.get(k) is None or not str(item[k]).strip()
                           for k in ("valor", "moneda", "fuente")):
            return result
        if item['moneda'] not in {'PEN', 'USD'}:
            raise ValueError("Moneda no soportada; requiere unidad documentada PEN o USD")
        try:
            value = Decimal(str(item['valor']))
        except InvalidOperation as exc:
            raise ValueError("Importe inválido") from exc
        if not value.is_finite() or value < 0:
            raise ValueError("Importe debe ser finito y no negativo")
        values.append(value)
    if monto['moneda'] != costos['moneda']:
        raise ValueError("Monedas distintas: conversión documentada requerida")
    with localcontext() as context:
        context.prec = 50
        revenue, cost = values
        margin = revenue - cost
        result.update(estado="calculado", moneda=monto['moneda'],
                      margen_bruto_estimado=str(margin.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)),
                      margen_porcentaje=(str((margin / revenue * 100).quantize(
                          Decimal('.01'), rounding=ROUND_HALF_UP)) if revenue else "no_aplicable"))
    return result


def evaluar_elegibilidad(requisitos, *, inventario_completo=False, fuente_inventario=""):
    """Evidencia por requisito: estado, fuente, evidencia (referencia verificable).

    no_acreditado significa incumplimiento probado, nunca documento ausente.
    La función consume evidencia validada por revisión humana; no autentica PDFs.
    Confirmar elegibilidad exige inventario completo documentado y todos los
    requisitos acreditados o explícitamente no exigidos con fuente y evidencia.
    """
    validated = []
    for key in REQUISITOS:
        item = requisitos.get(key, {})
        state = item.get('estado', 'pendiente_verificacion')
        if state not in ESTADOS:
            raise ValueError(f"Estado de requisito inválido: {key}")
        if state in {'acreditado', 'no_acreditado', 'no_exigido'}:
            if not str(item.get('fuente') or '').strip() or not str(item.get('evidencia') or '').strip():
                raise ValueError(f"Falta evidencia explícita: {key}")
        validated.append(state)
    if 'no_acreditado' in validated:
        return 'no_elegible_documentalmente'
    if inventario_completo and fuente_inventario.strip() and all(
        s in {'acreditado', 'no_exigido'} for s in validated
    ):
        return 'elegible_documentalmente'
    return 'pendiente_verificacion'


def evaluar_afinidad(row):
    if row['tipo_oportunidad'] == 'suministro':
        return 'afinidad_no_determinada', 'A0:bien;afinidad profesional no inferida de suministro'
    old = evaluar_servicio(row['descripcion'])
    text = normalizar(row['descripcion'])
    themes = sorted(k for k, words in TEMAS_ADICIONALES.items() if any(w in text for w in words))
    category = row['categoria_v08']
    score = AFINIDAD_PROFESIONAL.get(category)
    evidence = f"categoria_v08={category};temas_v10={old['temas_detectados']};temas_v13={'|'.join(themes)}"
    if old['alertas_especializacion'] or category in ESPECIALIZADAS:
        return 'requiere_revision_especializada', f"A1:{evidence};alertas={old['alertas_especializacion']}"
    if old['temas_detectados'] or themes or score == 5:
        return 'alta_afinidad_tematica', 'A2:' + evidence
    if score is not None and score >= 3:
        return 'afinidad_media', 'A3:' + evidence
    if score is not None:
        return 'afinidad_baja', 'A4:' + evidence
    return 'afinidad_no_determinada', 'A5:' + evidence


def decidir(afinidad, elegibilidad, seleccionado, revisado):
    """Reglas en orden de precedencia; no usa disponibilidad ni fecha histórica."""
    if elegibilidad == 'no_elegible_documentalmente':
        return 'descartar_por_incompatibilidad_acreditada', 'D1:incumplimiento con evidencia explícita'
    if afinidad == 'requiere_revision_especializada':
        return 'requiere_especialista', 'D2:alerta temática especializada; no implica incumplimiento'
    if elegibilidad == 'elegible_documentalmente':
        return 'evaluar_costos', 'D3:elegibilidad acreditada; evaluar costos y disponibilidad'
    if revisado:
        return 'solicitar_documentacion', 'D4:revisión con limitaciones; completar evidencia legible'
    if seleccionado or afinidad == 'alta_afinidad_tematica':
        return 'priorizar_verificacion', 'D5:selección documental o afinidad alta; requisitos pendientes'
    if afinidad == 'afinidad_media':
        return 'solicitar_documentacion', 'D6:afinidad media; obtener requisitos y evidencia'
    return 'sin_informacion_suficiente', 'D7:sin base suficiente para priorizar; no implica descarte'


def construir_evaluacion(entrada=PROCESSED / 'matriz_oportunidades_v12.csv',
                        documental=PROCESSED / 'evaluacion_documental_v11.csv'):
    required = {'idContrato', 'codigo', 'descripcion', 'categoria_v08', 'tipo_oportunidad',
                'seleccionado_revision_documental', 'estado_revision_documental',
                'situacion_temporal_en_captura', 'disponibilidad_actual', 'prioridad_revision'}
    fields, rows = leer_csv(entrada, required)
    doc_fields, docs = leer_csv(documental, {'idContrato', 'codigo', 'estado_evaluacion_documental',
        'fuente_documental', 'duracion_servicio', 'modalidad_pago', *DOC_MAP.values()})
    if len(rows) != 100 or Counter(r['tipo_oportunidad'] for r in rows) != {'suministro': 16, 'servicio': 84}:
        raise ValueError('Se requieren 100 contratos: 16 suministros y 84 servicios')
    by_id = {d['idContrato']: d for d in docs}
    selected = {r['idContrato'] for r in rows if r['seleccionado_revision_documental'] == 'si'}
    if len(docs) != 7 or selected != set(by_id):
        raise ValueError('Los siete expedientes documentales no coinciden')
    hashes = {name: hashlib.sha256(Path(path).read_bytes()).hexdigest()
              for name, path in [('matriz', entrada), ('documental', documental)]}
    result = []
    for original in rows:
        doc = by_id.get(original['idContrato'])
        if doc and any(original.get('doc_v11_' + k) != doc[k] for k in doc_fields):
            raise ValueError('La matriz no conserva la evaluación v1.1 por idContrato')
        if doc and (doc['codigo'] != original['codigo'] or
                    doc['estado_evaluacion_documental'] != original['estado_revision_documental']):
            raise ValueError('Identidad o estado documental contradictorio')
        affinity, affinity_reason = evaluar_afinidad(original)
        evaluation = {}
        new = {'version_motor': '1.3', 'sha256_matriz_v12': hashes['matriz'],
               'sha256_documental_v11': hashes['documental'],
               'afinidad_profesional_v13': affinity, 'motivo_afinidad_v13': affinity_reason}
        for requirement in REQUISITOS:
            field = DOC_MAP.get(requirement)
            detail = doc.get(field, '') if doc and field else ''
            state = 'no_legible' if detail == 'no_legible_completamente' else 'pendiente_verificacion'
            evaluation[requirement] = {'estado': state}
            new['estado_' + requirement] = state
            new['motivo_' + requirement] = (
                f"doc_v11_{field}={detail};sin acreditación del usuario" if detail
                else 'sin evidencia registrada; ausencia no equivale a incumplimiento')
        eligibility = evaluar_elegibilidad(evaluation)
        decision, reason = decidir(affinity, eligibility, doc is not None,
                                  original['estado_revision_documental'] == 'revisado_con_limitaciones')
        new.update(elegibilidad_global=eligibility,
                   motivo_elegibilidad='E1:sin inventario completo ni acreditaciones individuales verificadas',
                   monto_contractual=SIN_DATOS, moneda_monto=SIN_DATOS, fuente_monto=SIN_DATOS,
                   costos_estimados=SIN_DATOS, moneda_costos=SIN_DATOS, fuente_costos=SIN_DATOS,
                   gastos_ejecucion=SIN_DATOS, margen_bruto_estimado=SIN_DATOS,
                   rentabilidad_evaluada=SIN_DATOS,
                   plazo_ejecucion=(doc.get('duracion_servicio') or SIN_DATOS) if doc else SIN_DATOS,
                   condiciones_pago=(doc.get('modalidad_pago') or SIN_DATOS) if doc else SIN_DATOS,
                   fuente_comercial=(doc['fuente_documental'] if doc and doc.get('duracion_servicio') else SIN_DATOS),
                   riesgos_comerciales='monto_costos_gastos_desconocidos|disponibilidad_no_verificada',
                   decision_v13=decision, motivo_decision_v13=reason)
        if doc and doc.get('subcontratacion') == 'prohibida':
            new['riesgos_comerciales'] += '|subcontratacion_prohibida_registrada_v11'
        # Prioridad de trabajo: conservar los 7 seleccionados primero; luego
        # alta, media, especialista, baja/no determinada. Desempate por ID.
        group = 1 if doc else {'alta_afinidad_tematica': 2, 'afinidad_media': 3,
                               'requiere_revision_especializada': 4}.get(affinity, 5)
        new['prioridad_verificacion_v13'] = str(group)
        new['motivo_prioridad_v13'] = 'P1:seleccionados,alta,media,especialista,resto;desempate=idContrato_lex_asc'
        if set(new) & set(fields):
            raise ValueError('Colisión con columnas anteriores')
        result.append({**original, **new})
    result.sort(key=lambda r: (int(r['prioridad_verificacion_v13']), r['idContrato']))
    if 'orden_verificacion_v13' in fields:
        raise ValueError('Colisión con orden anterior')
    for i, row in enumerate(result, 1):
        row['orden_verificacion_v13'] = str(i)
    return list(result[0]), result


def generar_evaluacion(entrada=PROCESSED / 'matriz_oportunidades_v12.csv',
                       documental=PROCESSED / 'evaluacion_documental_v11.csv',
                       salida=PROCESSED / 'evaluacion_oportunidades_v13.csv'):
    salida = Path(salida)
    if salida.exists():
        raise FileExistsError(f'No se sobrescribirá: {salida}')
    fields, rows = construir_evaluacion(entrada, documental)
    with salida.open('x', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return rows


if __name__ == '__main__':
    print(f'Evaluación v1.3 creada: {len(generar_evaluacion())} contratos')
