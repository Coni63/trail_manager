"""
Script de test : suivi de charge jour par jour sur plusieurs semaines
(analysis/02-modelisation-mathematique.md, §1 et §2.3).

Entrée : une charge quotidienne (rTSS, ou tout équivalent TSS/TRIMP) par jour,
0 pour les jours de repos. Sortie : CTL, ATL, TSB, Monotonie, Strain,
Ramp rate et ACWR, jour par jour.

Départ à froid : CTL(-1) = ATL(-1) = 0 (pas d'historique avant J0).

Les formules elles-mêmes vivent dans metrics.py (testées dans test_metrics.py) ;
ce script ne fait que construire la série d'exemple et appeler ces fonctions.
"""
import sys
import numpy as np
import matplotlib.pyplot as plt

from metrics import charges_journalieres_vers_indicateurs, proba_blessure_serie

sys.stdout.reconfigure(encoding="utf-8")


FENETRE_J = 7  # fenêtre Monotonie/Strain/ACWR-hebdo (jours)

# --- Charge quotidienne d'exemple (4 semaines) : 0 = repos ---
# Semaine 1 : mise en route douce. Semaine 2 : charge. Semaine 3 : surcharge
# volontaire (pour voir Monotonie/Strain/ACWR décoller). Semaine 4 : coupure.
charges = np.array([
    # L     Ma    Me    J     V     S     D
    30,     0,   35,    0,   40,   55,    0,   # semaine 1
    35,    40,   35,    0,   45,   65,   20,   # semaine 2
    50,    45,   50,   45,   55,   90,   40,   # semaine 3 (surcharge)
     0,     0,   20,    0,    0,   25,    0,   # semaine 4 (coupure)
], dtype=float)

n_jours = len(charges)
resultats = charges_journalieres_vers_indicateurs(charges, fenetre_j=FENETRE_J)


print(resultats)
# --- Affichage ---

print(f"{'jour':>4} {'charge':>7} {'CTL':>6} {'ATL':>6} {'TSB':>6} "
      f"{'monoto':>7} {'strain':>7} {'ramp7j':>7} {'ACWR':>6}")
for j in range(n_jours):
    print(f"{j:>4} {resultats['charge'][j]:>7.0f} {resultats['CTL'][j]:>6.2f} "
          f"{resultats['ATL'][j]:>6.2f} {resultats['TSB'][j]:>6.2f} "
          f"{resultats['monotonie'][j]:>7.2f} {resultats['strain'][j]:>7.1f} "
          f"{resultats['ramp_rate'][j]:>7.2f} {resultats['acwr'][j]:>6.2f}")

print()
print("Repères : Monotonie > 2 = risqué, Strain élevé + Monotonie haute = signal")
print("d'alerte (Foster), Ramp rate > 5-8 CTL/sem = danger, ACWR hors 0.8-1.3 = zone")
print("de risque accru (indicateur controversé, cf. §2.3 du doc de modélisation).")

blessure_percent = proba_blessure_serie(resultats['acwr'], resultats['monotonie'], resultats['ramp_rate'])

X = list(range(len(charges)))
fig, (ax, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(20, 16))
ax.bar(X, charges)
ax2.plot(X, resultats['ATL'], label="ATL")
ax2.plot(X, resultats['CTL'], label="CTL")
ax2.plot(X, resultats['TSB'], label="TSB")
ax2.plot(X, resultats['monotonie'], label="monotonie")
ax2.plot(X, resultats['ramp_rate'], label="ramp_rate")
ax2.plot(X, resultats['acwr'], label="acwr")
ax3.plot(X, resultats['strain'], label="strain")
ax4.plot(X, blessure_percent, label="blessure_percent")
ax2.legend()
plt.show()