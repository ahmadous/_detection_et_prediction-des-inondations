# Saytu Mbeund 🌊🤖
## AI-Powered Early Flood Detection and Prediction System for Senegal

**Live platform:** https://sengaal-b4ab0.web.app/
**Demo video:** https://youtu.be/ml16aAvDvzs

## Results (AKTIION 2026 paper, corrected evaluation)

The results reported in the master's thesis (AUC-ROC = 1.000, zero false alerts) came from a
target-leakage issue and a validation set reused for model selection. They were superseded by the
leakage-free, temporally validated results below.

**Flood-risk forecasting (1–3 days ahead, 18 zones)**
- Test period 2023–2025 (7,632 zone-days): AUC-ROC 0.80–0.81 (Random Forest, gradient boosting,
  logistic regression), against 0.79 for a seasonal climatology baseline.
- With a genuine numerical weather forecast (Open-Meteo *Previous Runs*), forward-chaining over three
  rainy seasons (2024–2026): AUC-ROC **0.852** [0.833–0.871], +0.061 over the reanalysis-only model
  and +0.012 over the alert rule applied to the raw forecast.

**Visual flood detection (ground-level images)**
- 410 labeled images, 386 after deduplication; grouped 5-fold cross-validation.
- ConvNeXt-Tiny: accuracy 94.8%, F1 (flood) 94.7%, recall 95.7%, precision 93.7%, AUC-ROC 0.981,
  false-positive rate 6.0% — best of four architectures (ResNet-18, EfficientNet-B3, Swin-Tiny).

**Two-stage alert (scenario analysis):** confirming forecast alerts with validated images raises
alert precision from 0.30 to about 0.87.

## Reproducibility

All experiments are traced in executed notebooks in `flood_api/`:

| Notebook | Content |
|---|---|
| `audit_prevision_principale.ipynb` | Main forecasting results, year-blocked CV, climatology/persistence baselines |
| `validation_temporelle_prevision.ipynb` | Contribution of the numerical forecast, forward-chaining 2024–2026, bootstrap CIs |
| `verification_18_zones.ipynb` | Geolocation check of the 18 zones, reanalysis/forecast consistency |
| `flood-coparision.ipynb` | Four CNNs, deduplicated corpus, grouped 5-fold CV, Grad-CAM (executed on Kaggle GPU) |
| `cnn_comparaison_propre.ipynb` | Same CNN protocol, ready to run on Google Colab |

Meteorological data are not versioned; regenerate them from the open Open-Meteo API:

```bash
cd flood_api
python fetch_previous_runs.py          # archived forecasts 2024-01 → 2025-07 (18 zones)
python fetch_extension.py              # reanalysis + forecasts 2025-08 → 2026-09
```

Coordinates are read from the reanalysis files, so the forecast and the target always refer to the
same grid cell.

## Description
Saytu Mbeund aide les citoyens et les autorités à signaler, suivre et coordonner les alertes d’inondation en temps réel.

## Academic Validation
Master's thesis defended February 16, 2026
Université Iba Der Thiam de Thiès (UIDT) / 
Université de Technologie de Troyes (UTT)

## Author
Papa Ahmadou Seydou SOW
paseydou.sow@univ-thies.sn
Yaatal Digital — Senegal

## Awards
- WSIS Prizes 2026 — AL C7 E-environment
- AI for Good Impact Awards 2026 — AI for Planet
# Flood Monitoring Platform

This repository now follows a microservice layout:

- **Classification Service (5001)** – détection d’inondations par image (`flood_api/services/classification_service`).
- **API Gateway (5000)** – point d’entrée unique vers les services (`flood_api/gateway`).
- **Frontend (5173)** – Vue 3 client served with Vite (`frontend`).

## Project structure

```
.
├── docker-compose.yml
├── flood_api
│   ├── __init__.py
│   ├── app.py                 # keeps local compatibility by booting the gateway
│   ├── gateway/
│   ├── services/
│   │   └── classification_service/
│   ├── shared/
│   └── models/                # shared ML artefacts
└── frontend
    ├── Dockerfile
    └── src/
```

## Quick start with Docker

```bash
docker compose up --build
```

Services are exposed on:

- `http://localhost:5000` (gateway)
- `http://localhost:5001` (classification)
- `http://localhost:5173` (frontend)

Model files are mounted from `flood_api/models/`, so make sure the artefacts are present before launching the stack.  The classification service will automatically prefer `best_flood_model.pth` if it exists (this is the name produced by the training helper script); otherwise it falls back to the legacy `best_flood_classifier (1).pth`. You can also override any path with the `IMAGE_CLASSIFIER_PATH` environment variable.

## Alert workflow

- Les citoyens peuvent signaler une inondation depuis `/signaler`, avec ou sans photo, pour alimenter immédiatement le registre d’alertes.
- La barre supérieure expose un bandeau d’urgence et une cloche d’alertes pointant vers le centre d’alertes (`/alertes`).
- Le système met l’accent sur la gestion des alertes actives, le suivi local et le traitement par les équipes municipales.
- Les composants de détection image (`FloodClassify`, `DetectImage`) restent disponibles pour aider à prioriser les signalements visuels.
- Le mode manuel permet aux responsables de valider et clore les alertes sans dépendre d’un modèle prédictif externe.

## Gestion des rôles

- `guest` : visiteur sans compte. Peut consulter la carte, la liste publique et déposer un signalement simplifié.
- `citizen` : utilisateur connecté (créé automatiquement à la première connexion). Accède à l’historique de ses alertes (`/mes-alertes`).
- `local_admin` : comité local ou municipalité. Dispose du tableau de bord `/admin` et des outils de prédiction détaillés.
- `super_admin` : fédération. Peut gérer les comptes/permissions et superviser l’ensemble des données.

Les rôles sont stockés dans `userRoles/{uid}`. Une entrée est créée automatiquement (citizen) à la première connexion. Les responsables peuvent ensuite promouvoir un compte en ajustant la propriété `role` dans Firestore.

## Manual start (without Docker)

Create a virtual environment and install the shared dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r flood_api/requirements.txt
```

Run each backend service in its own terminal:

```bash
cd flood_api
python -m flood_api.services.classification_service.app
python -m flood_api.gateway.app
```

Launch the frontend in another terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend reads the service URLs from these environment variables:

- `VITE_API_GATEWAY_URL`
- `VITE_CLASSIFICATION_SERVICE_URL`

By default they fall back to `http://localhost:5000` and `http://localhost:5001` respectively.

## Configuration notes

- Gateway targets can be overridden with `CLASSIFICATION_SERVICE_URL` and optionally `GATEWAY_TIMEOUT`.
- Global constants (image size, probability threshold, supported zones) live in `flood_api/shared/config.py`.

## Next steps

- Add a dedicated satellite detection service to back the `DetectImage` component.
- Apply authentication at the gateway level.
- Wire a CI pipeline to build the Docker images and run automated tests.
