"""Prolonge les données des 18 zones au-delà du 31/07/2025 (saison 2025 complète + 2026).

- réanalyse horaire (mêmes 14 variables que donnees_extra/) -> donnees_extension/{zone}_{start}_{end}.csv
  au format CSV Open-Meteo (même en-tête que les fichiers 2005-2025, lisible par rf_forecast) ;
- prévisions à échéance (Previous Runs) -> donnees_previous_runs_ext/{zone}_prevruns.csv.

Coordonnées = cellules de réanalyse existantes (fetch_previous_runs.zones_from_reanalysis).
Les fichiers 2005-2025 ne sont pas modifiés. Utilisé par validation_temporelle_prevision.ipynb.
"""
import argparse
import time
from pathlib import Path
import requests

import fetch_previous_runs as fpr

BASE = Path(__file__).resolve().parent
REANALYSIS_HOURLY = ["temperature_2m", "relative_humidity_2m", "dew_point_2m",
    "precipitation", "pressure_msl", "cloud_cover", "vapour_pressure_deficit",
    "et0_fao_evapotranspiration", "wind_speed_10m", "wind_gusts_10m",
    "soil_moisture_0_to_7cm", "soil_moisture_7_to_28cm",
    "soil_moisture_28_to_100cm", "soil_moisture_100_to_255cm"]


def fetch_reanalysis(out: Path, start: str, end: str, force: bool = False):
    out.mkdir(exist_ok=True)
    for zone, (lat, lon) in fpr.zones_from_reanalysis().items():
        dest = out / f"{zone}_{start[:4]}_{end[:4]}.csv"
        if dest.exists() and not force:
            print(f"• {zone} réanalyse déjà présente"); continue
        for attempt in range(6):
            try:
                r = requests.get("https://archive-api.open-meteo.com/v1/archive",
                                 params=dict(latitude=lat, longitude=lon, start_date=start, end_date=end,
                                             hourly=",".join(REANALYSIS_HOURLY), format="csv", timezone="GMT"),
                                 timeout=180)
                if r.status_code == 429:
                    raise RuntimeError("429 (limite de requêtes)")
                r.raise_for_status()
                if r.text.lstrip().startswith("{"):
                    raise RuntimeError(r.text[:120])
                dest.write_text(r.text)
                print(f"✓ réanalyse {zone:16s} ({lat:.3f}, {lon:.3f})")
                break
            except Exception as e:
                wait = min(15 * (attempt + 1), 70)
                print(f"  {zone} tentative {attempt+1}: {str(e)[:80]} — attente {wait}s"); time.sleep(wait)
        time.sleep(3)


def main(start: str, end: str, force: bool = False):
    fetch_reanalysis(BASE / "donnees_extension", start, end, force)
    fpr.main(BASE / "donnees_previous_runs_ext", force, start, end)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2025-08-01")
    ap.add_argument("--end", default="2026-09-18")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    main(a.start, a.end, a.force)
