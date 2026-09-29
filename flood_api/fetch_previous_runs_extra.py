"""Obsolète : fusionné dans fetch_previous_runs.py, qui lit les coordonnées des 18 zones
directement dans les fichiers de réanalyse (l'ancienne liste utilisait les coordonnées des
villes, légèrement différentes des cellules de réanalyse pour 6 zones, et une zone « dakar »
qui n'est pas modélisée)."""
import subprocess
import sys
from pathlib import Path

subprocess.run([sys.executable, str(Path(__file__).with_name("fetch_previous_runs.py")), *sys.argv[1:]],
               check=True)
