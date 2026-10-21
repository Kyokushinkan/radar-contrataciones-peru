from datetime import datetime
from zoneinfo import ZoneInfo

from app.ranking_cm import categoria, estado_temporal

LIMA = ZoneInfo("America/Lima")


def test_categoria_limpieza():
    assert categoria("ADQUISICION DE UTILES DE LIMPIEZA") == "limpieza"


def test_categoria_toner():
    assert categoria("Adquisición de tóner para impresoras") == "impresion"


def test_categoria_mobiliario():
    assert categoria("ADQUISICION DE SILLAS ERGONOMICAS") == "mobiliario"


def test_ventana_por_iniciar():
    ahora = datetime(2026, 10, 21, 7, 0, tzinfo=LIMA)
    assert estado_temporal(
        "2026-10-21T08:00:00-05:00",
        "2026-10-21T13:00:00-05:00",
        ahora,
    ) == "por_iniciar"


def test_ventana_abierta():
    ahora = datetime(2026, 10, 21, 10, 0, tzinfo=LIMA)
    assert estado_temporal(
        "2026-10-21T08:00:00-05:00",
        "2026-10-21T13:00:00-05:00",
        ahora,
    ) == "ventana_abierta"


def test_ventana_vencida():
    ahora = datetime(2026, 10, 21, 14, 0, tzinfo=LIMA)
    assert estado_temporal(
        "2026-10-21T08:00:00-05:00",
        "2026-10-21T13:00:00-05:00",
        ahora,
    ) == "vencido"


def test_fecha_invalida():
    ahora = datetime(2026, 10, 21, 10, 0, tzinfo=LIMA)
    assert estado_temporal("", "", ahora) == "sin_fecha"


def test_intervalo_invalido():
    ahora = datetime(2026, 10, 21, 10, 0, tzinfo=LIMA)
    assert estado_temporal(
        "2026-10-22T08:00:00-05:00",
        "2026-10-21T13:00:00-05:00",
        ahora,
    ) == "sin_fecha"
