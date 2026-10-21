# Radar Contrataciones Perú — MVP v0.1

Radar privado de oportunidades del Estado peruano. **No modifica** Radar SIE ni Radar Perú Compras.

## Alcance
- Contratos menores: fuente PLADICOP, pendiente de auditoría de acceso.
- Procedimientos tradicionales: descargas oficiales OCDS/SEACE, pendiente de validación de archivos.
- PAC: datos abiertos oficiales, pendiente de validación de archivos.
- CMN: inventario de publicaciones oficiales por entidad, pendiente de cobertura nacional.

## Puesta en marcha (Windows PowerShell)
```powershell
cd C:\radar-contrataciones-peru
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts\init_db.py
.\.venv\Scripts\python.exe scripts\audit_sources.py
.\.venv\Scripts\python.exe -m pytest -q
```

Por defecto usa SQLite para validar el esquema sin credenciales. PostgreSQL será el destino de producción después de aprobar los primeros lotes.

## Principios
- No automatizar autenticación, CAPTCHA, envío de ofertas o consultas masivas no autorizadas.
- Registrar fuente, fecha de observación, identificador y hash de cada archivo.
- No presentar registros planificados como convocatorias abiertas.
- Conservar historial de versiones y evitar duplicados.

## Primer entregable
Ejecutar `scripts/audit_sources.py` para generar `data/processed/source_audit.json`; luego descargar manualmente **un archivo oficial de PAC y uno de procedimientos** para examinar sus columnas y diseñar importadores.
