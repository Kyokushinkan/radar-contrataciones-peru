"""Consolida una carpeta de respuestas locales en una base separada."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.db import ROOT
from app.pladicop_batch import consolidate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('carpeta', type=Path)
    parser.add_argument('--db', type=Path, required=True, help='Base de pruebas; nunca producción')
    parser.add_argument('--report-dir', type=Path, default=ROOT / 'data' / 'processed' / 'cobertura')
    args = parser.parse_args()
    try:
        report = consolidate(args.carpeta, args.db, args.report_dir)
    except (OSError, ValueError) as exc:
        parser.exit(2, f'Error: {exc}\n')
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 1 if report['rechazados'] or any(f['errores'] for f in report['archivos']) else 0


if __name__ == '__main__':
    sys.exit(main())
