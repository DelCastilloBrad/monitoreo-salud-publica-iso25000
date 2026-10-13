"""Comprobaciones de la interfaz con CSV/PNG reales, precalculados por el legado."""

import pandas as pd
import pytest

from monitoreo_salud_publica import app as module


@pytest.fixture(scope="module")
def client():
    assert module.legacy_ready(), "Faltan outputs/tables u outputs/figures del legado"
    module.app.config.update(TESTING=True)
    return module.app.test_client()


@pytest.mark.parametrize("route", ["/", "/regional", "/severidad", "/ranking", "/pronosticos"])
def test_cinco_vistas_con_archivos_legados(client, route):
    response = client.get(route)
    assert response.status_code == 200
    assert b"No se encontr" not in response.data


def test_kpis_coinciden_con_ultima_fila_de_csv(client):
    page = client.get("/").get_data(as_text=True)
    for group, suffix in (("children", "men5"), ("adults", "60mas")):
        csv = module.OUT_TABLES / f"national_{group}_weekly_HR_CFR.csv"
        last = pd.read_csv(csv, parse_dates=["date"]).sort_values("date").iloc[-1]
        cases = int(last[f"neumonias_{suffix}"])
        date = last["date"].strftime("%d/%m/%Y")
        assert f"Semana del {date}" in page
        assert f'<p class="kpi-value">{cases} <span' in page


def test_severidad_y_ranking_coinciden_con_csv(client):
    severity = client.get("/severidad").get_data(as_text=True)
    ranking = client.get("/ranking").get_data(as_text=True)
    for group, key in (("children", "children"), ("adults", "older")):
        last = pd.read_csv(module.OUT_TABLES / f"national_{group}_annual_HR_CFR.csv").tail(1).iloc[0]
        assert f"<td>{int(last['year'])}</td><td>{last['HR'] * 100:.2f}%</td><td>{last['CFR'] * 100:.2f}%</td>" in severity
        first = pd.read_csv(module.OUT_TABLES / f"top3_frequency_{key}_cases_rate.csv").iloc[0]
        assert f"<td>{first['region']}</td><td>{int(first['top3_appearances'])}</td>" in ranking


@pytest.mark.parametrize(
    "query,expected",
    [
        ("grupo=children&region=LORETO", "LORETO — Menores de 5 años"),
        ("grupo=adults&region=CUSCO", "CUSCO — Adultos 60+"),
        ("grupo=invalido&region=invalida", "HUANUCO — Menores de 5 años"),
    ],
)
def test_filtros_regionales(client, query, expected):
    response = client.get(f"/regional?{query}")
    assert response.status_code == 200
    assert expected in response.get_data(as_text=True)


def test_pronosticos_coinciden_con_csv(client):
    page = client.get("/pronosticos").get_data(as_text=True)
    for group in ("children", "adults"):
        filename = f"national_{group}_cases_ml_metrics.csv"
        first = pd.read_csv(module.LEGACY_DIR / "outputs" / f"national_{group}_cases_ml" / filename).iloc[0]
        assert f"<td>{first['model']}</td><td>{first['mae']}</td>" in page


def test_png_legado_es_servido_sin_modificar(client):
    path = module.OUT_FIGURES / "HUANUCO_Children_5_Cases.png"
    response = client.get("/legacy/figures/HUANUCO_Children_5_Cases.png")
    assert response.status_code == 200
    assert response.data == path.read_bytes()
