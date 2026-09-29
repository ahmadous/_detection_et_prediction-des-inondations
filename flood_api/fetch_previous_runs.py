"""Télécharge les VRAIES prévisions à échéance (Open-Meteo Previous Runs API).

Pour chaque jour valide D, `precipitation_previous_dayK` = pluie prévue pour D
par le run émis K jours plus tôt (à D-K). Donc pour un jour d'émission t, la
prévision de la fenêtre future t+1…t+3 s'obtient par :
    fc(t+1) = lead1 valide en t+1 ; fc(t+2) = lead2 valide en t+2 ; fc(t+3) = lead3 valide en t+3
=> émise à t, disponible à t : pas de fuite.

Archive disponible ~2024-03 -> 2025-07 (démonstration de principe).

Coordonnées : lues dans l'en-tête des fichiers de réanalyse (donnees/ et donnees_extra/),
c'est-à-dire la cellule exacte de la zone modélisée. Il n'y a plus de liste codée en dur :
l'ancienne liste contenait les points erronés de Keur Massar (homonyme de la région de Louga)
et de Kaolack, et nommait « keur_massar » le fichier de la banlieue de Dakar.
Vérification : verification_18_zones.ipynb.
Remplace aussi fetch_previous_runs_extra.py.
"""
import argparse
import time
from pathlib import Path
import requests
import pandas as pd

BASE = Path(__file__).resolve().parent
REA_DIRS = [BASE / "donnees", BASE / "donnees_extra"]
HOURLY = ["precipitation", "precipitation_previous_day1",
          "precipitation_previous_day2", "precipitation_previous_day3"]
URL = "https://previous-runs-api.open-meteo.com/v1/forecast"


def zones_from_reanalysis():
    """zone -> (lat, lon) de la cellule de réanalyse (2e ligne du CSV Open-Meteo)."""
    zones = {}
    for d in REA_DIRS:
        for csv in sorted(d.glob("*_2005_2025.csv")):
            lat, lon = map(float, csv.read_text().splitlines()[1].split(",")[:2])
            zones[csv.stem.replace("_2005_2025", "")] = (lat, lon)
    return zones


def main(out: Path, force: bool, start: str = "2024-01-01", end: str = "2025-07-31", suffix: str = "prevruns"):
    out.mkdir(exist_ok=True)
    zones = zones_from_reanalysis()
    print(f"{len(zones)} zones lues dans la réanalyse -> {out}")
    for zone, (lat, lon) in zones.items():
        dest = out / f"{zone}_{suffix}.csv"
        if dest.exists() and not force:
            print(f"• {zone} déjà présent (--force pour re-télécharger)")
            continue
        params = dict(latitude=lat, longitude=lon, start_date=start,
                      end_date=end, hourly=",".join(HOURLY), timezone="GMT")
        for attempt in range(4):
            try:
                r = requests.get(URL, params=params, timeout=90)
                r.raise_for_status()
                h = r.json()["hourly"]
                df = pd.DataFrame(h)
                df["date"] = pd.to_datetime(df["time"]).dt.floor("D")
                # somme journalière de la pluie réelle et des prévisions par échéance
                daily = df.groupby("date").agg(
                    actual=("precipitation", "sum"),
                    fc_lead1=("precipitation_previous_day1", "sum"),
                    fc_lead2=("precipitation_previous_day2", "sum"),
                    fc_lead3=("precipitation_previous_day3", "sum"),
                ).reset_index()
                daily["location"] = zone
                daily.to_csv(dest, index=False)
                nn = daily["fc_lead3"].notna().sum()
                print(f"✓ {zone:16s} ({lat:.3f}, {lon:.3f}) {len(daily)} jours ({nn} avec prév J-3)")
                break
            except Exception as e:
                print(f"  {zone} tentative {attempt+1}: {str(e)[:100]}")
                time.sleep(4)
        time.sleep(1)
    print("Terminé.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=BASE / "donnees_previous_runs")
    ap.add_argument("--force", action="store_true", help="re-télécharger les fichiers existants")
    ap.add_argument("--start", default="2024-01-01")
    ap.add_argument("--end", default="2025-07-31")
    a = ap.parse_args()
    main(a.out, a.force, a.start, a.end)
