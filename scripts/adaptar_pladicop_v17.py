import argparse
import json
from pathlib import Path

from app.pladicop import FIELDS


def adaptar(documento):
    if isinstance(documento, list):
        registros = documento
        metadatos = {}
    elif isinstance(documento, dict) and isinstance(documento.get("data"), list):
        registros = documento["data"]
        metadatos = {
            clave: valor
            for clave, valor in documento.items()
            if clave != "data"
        }
    else:
        raise ValueError("Se esperaba una lista o un objeto con data[]")

    adaptados = []
    completados = set()

    for registro in registros:
        if not isinstance(registro, dict):
            raise ValueError("Registro no es un objeto JSON")

        nuevo = dict(registro)

        for campo in FIELDS:
            if campo not in nuevo:
                nuevo[campo] = None
                completados.add(campo)

        adaptados.append(nuevo)

    return {
        **metadatos,
        "data": adaptados,
    }, sorted(completados)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("entrada")
    parser.add_argument("salida")
    args = parser.parse_args()

    entrada = Path(args.entrada)
    salida = Path(args.salida)

    documento = json.loads(entrada.read_text(encoding="utf-8-sig"))
    resultado, completados = adaptar(documento)

    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("ADAPTACION=OK")
    print("REGISTROS=", len(resultado["data"]))
    print("CAMPOS_COMPLETADOS_CON_NULL=", completados)
    print("ARCHIVO_SALIDA=", salida)


if __name__ == "__main__":
    main()
