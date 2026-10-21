# Plan MVP

## Etapa 0 — fuentes y datos (actual)
1. Inventario de cuatro fuentes oficiales y clasificación de acceso.
2. Prueba de esquema y registro de procedencia.
3. Validación manual de un archivo PAC y uno de procedimientos.

## Etapa 1 — históricos
- Importadores idempotentes para PAC y procedimientos, con detección de columnas por versión.
- Auditoría de totales, duplicados, años y cobertura por entidad.

## Etapa 2 — vigentes
- Revisar acceso autorizado al buscador público de contratos menores.
- Revisar mecanismos oficiales para procedimientos en curso.
- Alertas de vencimiento solo con fecha comprobada.

## Etapa 3 — planificación
- Inventario CMN por RUC de entidad, ejercicio, documento y versión.
- Extraer PDFs/Excel respetando formatos y procedencia.

## Etapa 4 — inteligencia comercial
- Integración de solo lectura con Radar SIE y Radar Perú Compras.
- Cruces por RUC, nomenclatura, ítem y equivalencias validadas.
- Panel privado con estados planificado/convocado/adjudicado.

## Condiciones de salida
Ningún dato pasa a producción sin evidencia de fuente, cobertura y controles de integridad.
