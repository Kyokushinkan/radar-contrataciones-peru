"""CLI de importación local PLADICOP."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.db import DB_PATH, ROOT
from app.pladicop import import_file


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archivo', type=Path)
    parser.add_argument('--db', type=Path, default=DB_PATH)
    parser.add_argument('--report-dir', type=Path, default=ROOT / 'data' / 'processed')
    parser.add_argument('--upcoming-hours', type=int, default=72)
    args = parser.parse_args()
    try:
        report = import_file(args.archivo, args.db, args.report_dir, upcoming_hours=args.upcoming_hours)
    except (OSError, ValueError) as exc:
        parser.exit(2, f'Error: {exc}\n')
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0 if report['resultado'] == 'ok' else 1


if __name__ == '__main__':
    sys.exit(main())
