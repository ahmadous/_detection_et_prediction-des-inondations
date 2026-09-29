"""Figures de la version finale (AKTIION 2026), en anglais et en français.

Sources (notebooks exécutés) :
  - validation_temporelle_prevision.ipynb -> rf_forecast_results/validation_temporelle/synthese.csv
  - flood-coparision.ipynb (figures CNN intégrées au notebook)
Sortie : docs/ieee_submission/
"""
import base64
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
OUT = BASE.parent / "docs" / "ieee_submission"
SYN = BASE / "rf_forecast_results" / "validation_temporelle" / "synthese.csv"
CNN_NB = BASE / "flood-coparision.ipynb"

# --------------------------------------------------------------------------- #
# 1. Apport de la prévision : CV mélangée vs forward-chaining (remplace fig5)
# --------------------------------------------------------------------------- #
syn = pd.read_csv(SYN)
A = syn[syn.Protocole.str.startswith("A.")].set_index("Modèle")
Cf = syn[syn.Protocole.str.startswith("C.")].set_index("Modèle")
MODELS = ["Réanalyse seule", "Prévision seule", "Réanalyse + Prévision",
          "Historique 2005–2023 + Prévision", "Règle d'alerte sur la prévision", "Climatologie", "Persistance"]
LAB = {
    "en": ["Reanalysis\nonly", "Forecast\nonly", "Reanalysis\n+ forecast", "2005–2023 model\n+ forecast",
           "Alert rule on\nraw forecast", "Climatology", "Persistence"],
    "fr": ["Réanalyse\nseule", "Prévision\nseule", "Réanalyse\n+ prévision", "Modèle 2005–2023\n+ prévision",
           "Règle d'alerte\nsur la prévision", "Climatologie", "Persistance"],
}
TXT = {
    "en": dict(a="Shuffled CV (2024–2025, original protocol)", c="Forward-chaining (2024–2026, temporal)",
               learned="learned models", base="no-training baselines"),
    "fr": dict(a="CV mélangée (2024–2025, protocole initial)", c="Forward-chaining (2024–2026, temporel)",
               learned="modèles appris", base="références sans apprentissage"),
}
for lang in ("en", "fr"):
    fig, ax = plt.subplots(figsize=(7.4, 4.3))
    x = np.arange(len(MODELS)); w = 0.38
    va = [A.AUC.get(m, np.nan) for m in MODELS]
    vc = Cf.loc[MODELS, "AUC"].values
    err = np.vstack([vc - Cf.loc[MODELS, "IC95_bas"].values, Cf.loc[MODELS, "IC95_haut"].values - vc])
    ax.bar(x - w / 2, va, w, color="#BDBDBD", label=TXT[lang]["a"])
    ax.bar(x + w / 2, vc, w, yerr=err, capsize=3, color="#2C7FB8", label=TXT[lang]["c"])
    for xi, v, hi in zip(x, vc, err[1]):
        ax.text(xi + w / 2, v + hi + 0.008, f"{v:.2f}", ha="center", fontsize=7)
    ax.axvline(3.5, color="k", lw=0.8, ls="--")
    ax.text(1.5, 0.975, TXT[lang]["learned"], ha="center", fontsize=8, style="italic")
    ax.text(5.0, 0.975, TXT[lang]["base"], ha="center", fontsize=8, style="italic")
    ax.set_xticks(x); ax.set_xticklabels(LAB[lang], fontsize=7.5)
    ax.set_ylim(0.5, 1.0); ax.set_ylabel("AUC-ROC"); ax.grid(axis="y", alpha=0.3)
    ax.legend(fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=2, frameon=False)
    plt.tight_layout()
    fig.savefig(OUT / f"fig5_temporal_validation_{lang}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

# --------------------------------------------------------------------------- #
# 2. Fusion à deux étages (analyse de scénario) avec les taux mesurés
# --------------------------------------------------------------------------- #
PI = 0.194                        # fréquence de la cible sur le test 2023-2025
R_F, F_F, P_F = 0.930, 0.527, 0.298   # RF au point opérationnel (Tableau II)
R_C, F_C = 0.957, 0.060            # ConvNeXt, validation croisée 5 plis (386 images)


def system(f_c, s=1.0):
    tp = PI * R_F * s * R_C
    fp = (1 - PI) * F_F * s * f_c
    return tp / (tp + fp), R_F * s * R_C


p_meas, r_meas = system(F_C)
print(f"Fusion au taux mesuré ({F_C:.3f}) : précision = {p_meas:.3f}, rappel = {r_meas:.3f}")
FT = {
    "en": dict(x="Visual-stage false-positive rate (%)", y="Alert precision", fc="Two-stage system (scenario)",
               ff=f"Forecasting stage alone ({P_F:.2f})", m=f"measured ConvNeXt-Tiny\n(FPR = {100*F_C:.1f}%)"),
    "fr": dict(x="Taux de faux positifs de l'étage visuel (%)", y="Précision de l'alerte",
               fc="Système à deux étages (scénario)", ff=f"Étage de prévision seul ({P_F:.2f})",
               m=f"ConvNeXt-Tiny mesuré\n(taux FP = {100*F_C:.1f} %)"),
}
xx = np.linspace(0, 0.20, 100)
for lang, L in FT.items():
    fig, ax = plt.subplots(figsize=(6.4, 3.9))
    ax.plot(xx * 100, [system(f)[0] for f in xx], lw=2.4, color="#2CA25F", label=L["fc"])
    ax.axhline(P_F, ls="--", color="#C44E52", lw=1.8, label=L["ff"])
    ax.scatter([F_C * 100], [p_meas], color="#2CA25F", zorder=5)
    ax.annotate(L["m"], (F_C * 100, p_meas), xytext=(F_C * 100 + 2.5, p_meas + 0.04), fontsize=8,
                arrowprops=dict(arrowstyle="->", lw=0.8))
    ax.set(xlabel=L["x"], ylabel=L["y"], ylim=(0, 1.05)); ax.grid(alpha=0.3)
    ax.legend(loc="lower left", fontsize=8)
    plt.tight_layout()
    fig.savefig(OUT / f"fig_fusion_{lang}_v2.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

# --------------------------------------------------------------------------- #
# 3. Figures CNN extraites du notebook exécuté (Kaggle)
# --------------------------------------------------------------------------- #
nb = json.load(open(CNN_NB))
imgs = {}
for i, c in enumerate(nb["cells"]):
    k = 0
    for o in c.get("outputs", []):
        if "image/png" in o.get("data", {}):
            imgs[(i, k)] = base64.b64decode(o["data"]["image/png"]); k += 1
src = "".join
cell_of = {tag: next(i for i, c in enumerate(nb["cells"]) if tag in src(c["source"]))
           for tag in ("exemples_corpus", "cnn_roc_cv", "cnn_gradcam_cv")}
MAP = {
    (cell_of["exemples_corpus"], 0): "fig_corpus_examples_en.png",
    (cell_of["exemples_corpus"], 1): "fig_corpus_examples_fr.png",
    (cell_of["cnn_roc_cv"], 0): "cnn_roc_cv_en.png",
    (cell_of["cnn_roc_cv"], 1): "cnn_confusion_cv_en.png",
    (cell_of["cnn_roc_cv"], 2): "cnn_roc_cv_fr.png",
    (cell_of["cnn_roc_cv"], 3): "cnn_confusion_cv_fr.png",
    (cell_of["cnn_gradcam_cv"], 0): "cnn_gradcam_cv_en.png",
    (cell_of["cnn_gradcam_cv"], 1): "cnn_gradcam_cv_fr.png",
}
for key, name in MAP.items():
    (OUT / name).write_bytes(imgs[key])
    print("✓", name)
print("✓ figures dans", OUT)
