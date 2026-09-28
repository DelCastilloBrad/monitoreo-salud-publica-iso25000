"""Pruebas iniciales del módulo web, sin ejecutar los modelos legados."""

import pandas as pd
import pytest

from monitoreo_salud_publica import app as module


@pytest.fixture
def client():
    module.app.config.update(TESTING=True)
    return module.app.test_client()


@pytest.mark.parametrize("route", ["/", "/regional", "/severidad", "/ranking", "/pronosticos"])
def test_vistas_informan_cuando_faltan_salidas_legadas(client, monkeypatch, tmp_path, route):
    monkeypatch.setattr(module, "OUT_TABLES", tmp_path / "sin_tablas")
    monkeypatch.setattr(module, "OUT_FIGURES", tmp_path / "sin_figuras")
    response = client.get(route)
    assert response.status_code == 200
    assert str(module.LEGACY_DIR).encode() in response.data


def test_archivo_legado_rechaza_traversal_y_archivo_inexistente(client):
    assert client.get("/legacy/figures/ausente.png").status_code == 404
    assert client.get("/legacy/..%2F..%2FREADME.md").status_code == 404


def test_home_muestra_datos_de_csv_controlados(client, monkeypatch, tmp_path):
    tables = tmp_path / "tables"
    figures = tmp_path / "figures"
    tables.mkdir()
    figures.mkdir()
    monkeypatch.setattr(module, "OUT_TABLES", tables)
    monkeypatch.setattr(module, "OUT_FIGURES", figures)

    for group, suffix in (("children", "men5"), ("adults", "60mas")):
        pd.DataFrame([
            {"date": "2023-01-01", f"neumonias_{suffix}": 1, "HR_roll": .1, "CFR_roll": .01},
            {"date": "2023-01-08", f"neumonias_{suffix}": 42, "HR_roll": .2, "CFR_roll": .02},
        ]).to_csv(tables / f"national_{group}_weekly_HR_CFR.csv", index=False)
    pd.DataFrame({"year": [2022, 2023]}).to_csv(
        tables / "national_annual_variation_rates.csv", index=False
    )

    response = client.get("/")
    assert response.status_code == 200
    assert b"42" in response.data
    assert b"2023" in response.data
