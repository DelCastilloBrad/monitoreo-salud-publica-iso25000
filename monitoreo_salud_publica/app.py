# -*- coding: utf-8 -*-
"""
Módulo de Interfaz de Monitoreo y Vigilancia — Salud Pública (IRA/Neumonía, Perú)
Curso: Calidad de Software — Trabajo de Introducción
Equipo: Viuda Negra 2.0

Este módulo NO reimplementa la lógica del proyecto legado ISPySA-Pneumonia:
la reutiliza directamente, leyendo los CSV/PNG que sus scripts ya generan en
outputs/tables y outputs/figures (ver LEGACY_DIR más abajo). Esa es la
"integración con la lógica de negocio heredada" pedida en la actividad 3.
"""

import os
from pathlib import Path
import pandas as pd
from flask import Flask, render_template, abort, send_from_directory, request

BASE_DIR = Path(__file__).resolve().parent
# El proyecto legado debe estar como carpeta hermana de este módulo:
#   .../ISPySA-Pneumonia-main/
#   .../monitoreo_salud_publica/   <- este módulo
LEGACY_DIR = BASE_DIR.parent / "ISPySA-Pneumonia-main"
OUT_TABLES = LEGACY_DIR / "outputs" / "tables"
OUT_FIGURES = LEGACY_DIR / "outputs" / "figures"

app = Flask(__name__)

REGIONS = {
    "children": {
        "label": "Menores de 5 años",
        "regions": ["HUANUCO", "LORETO", "UCAYALI"],
        "top3_dir": LEGACY_DIR / "outputs" / "children_cases_top3_model_plots",
        "top3_prefix": "children_cases_top3_models",
    },
    "adults": {
        "label": "Adultos 60+",
        "regions": ["AREQUIPA", "CUSCO", "MOQUEGUA"],
        "top3_dir": LEGACY_DIR / "outputs" / "adults_cases_top3_models_final",
        "top3_prefix": "adults_cases_top3_models",
    },
}


def legacy_ready():
    return OUT_TABLES.exists() and OUT_FIGURES.exists()


@app.route("/legacy/<path:filename>")
def legacy_file(filename):
    """Sirve imágenes directamente desde outputs/ del proyecto legado."""
    full = (LEGACY_DIR / "outputs" / filename).resolve()
    if LEGACY_DIR.resolve() not in full.parents or not full.exists():
        abort(404)
    return send_from_directory(full.parent, full.name)


@app.route("/")
def home():
    if not legacy_ready():
        return render_template("legacy_missing.html", legacy_dir=str(LEGACY_DIR))

    kpis = {}
    for grupo, col_prefix in [("children", "men5"), ("adults", "60mas")]:
        f = OUT_TABLES / f"national_{grupo}_weekly_HR_CFR.csv"
        df = pd.read_csv(f, parse_dates=["date"]).sort_values("date")
        last = df.iloc[-1]
        kpis[grupo] = {
            "fecha": last["date"].strftime("%d/%m/%Y"),
            "casos": int(last[f"neumonias_{col_prefix}"]),
            "hr": round(float(last["HR_roll"]) * 100, 1),
            "cfr": round(float(last["CFR_roll"]) * 100, 2),
        }

    annual = pd.read_csv(OUT_TABLES / "national_annual_variation_rates.csv")
    ultimo_anio = int(annual["year"].max())

    return render_template(
        "index.html",
        kpis=kpis,
        ultimo_anio=ultimo_anio,
        regions=REGIONS,
    )


@app.route("/regional")
def regional():
    if not legacy_ready():
        return render_template("legacy_missing.html", legacy_dir=str(LEGACY_DIR))

    grupo = request.args.get("grupo", "children")
    if grupo not in REGIONS:
        grupo = "children"
    cfg = REGIONS[grupo]
    region = request.args.get("region", cfg["regions"][0]).upper()
    if region not in cfg["regions"]:
        region = cfg["regions"][0]

    label_fig = "Children_5" if grupo == "children" else "Adults_60plus"
    case_fig = f"figures/{region}_{label_fig}_Cases.png"

    top3_file = cfg["top3_dir"] / f"{region.lower()}_{cfg['top3_prefix']}.png"
    top3_fig = None
    if top3_file.exists():
        top3_fig = f"{cfg['top3_dir'].name}/{top3_file.name}"

    metrics_dir = {
        "children": LEGACY_DIR / "outputs" / "children_cases_ml_simulation_recursive",
        "adults": LEGACY_DIR / "outputs" / "adults_cases_ml_optimized",
    }[grupo]
    metrics_file = metrics_dir / f"{region.lower()}_ml_metrics.csv" if grupo == "children" \
        else LEGACY_DIR / "outputs" / "adults_cases_ml_optimized" / "all_regions_adults_cases_ml_metrics.csv"

    metrics_rows = []
    if grupo == "adults" and metrics_file.exists():
        df = pd.read_csv(metrics_file)
        metrics_rows = df[df["region"] == region].to_dict("records")
    elif grupo == "children" and metrics_file.exists():
        df = pd.read_csv(metrics_file)
        df["model"] = df.get("model", "ML")
        metrics_rows = df.to_dict("records")

    return render_template(
        "regional.html",
        regions=REGIONS,
        grupo=grupo,
        cfg=cfg,
        region=region,
        case_fig=case_fig,
        top3_fig=top3_fig,
        metrics_rows=metrics_rows,
    )


@app.route("/severidad")
def severidad():
    if not legacy_ready():
        return render_template("legacy_missing.html", legacy_dir=str(LEGACY_DIR))

    tablas = {}
    for grupo, col_prefix in [("children", "men5"), ("adults", "60mas")]:
        f = OUT_TABLES / f"national_{grupo}_annual_HR_CFR.csv"
        df = pd.read_csv(f).tail(5)
        tablas[grupo] = df.to_dict("records")

    return render_template("severidad.html", regions=REGIONS, tablas=tablas)


@app.route("/ranking")
def ranking():
    if not legacy_ready():
        return render_template("legacy_missing.html", legacy_dir=str(LEGACY_DIR))

    top3 = {}
    for grupo, key in [("children", "children"), ("adults", "older")]:
        f = OUT_TABLES / f"top3_frequency_{key}_cases_rate.csv"
        df = pd.read_csv(f).head(5)
        top3[grupo] = df.to_dict("records")

    return render_template("ranking.html", regions=REGIONS, top3=top3)


@app.route("/pronosticos")
def pronosticos():
    if not legacy_ready():
        return render_template("legacy_missing.html", legacy_dir=str(LEGACY_DIR))

    nat_children = pd.read_csv(
        LEGACY_DIR / "outputs" / "national_children_cases_ml" / "national_children_cases_ml_metrics.csv"
    ).to_dict("records")
    nat_adults = pd.read_csv(
        LEGACY_DIR / "outputs" / "national_adults_cases_ml" / "national_adults_cases_ml_metrics.csv"
    ).to_dict("records")

    return render_template(
        "pronosticos.html",
        regions=REGIONS,
        nat_children=nat_children,
        nat_adults=nat_adults,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Proyecto legado esperado en: {LEGACY_DIR}")
    print(f"  -> encontrado: {legacy_ready()}")
    app.run(host="127.0.0.1", port=port, debug=False)
