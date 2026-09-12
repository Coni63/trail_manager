"""
Script de test : calcule les métriques des sections 1 et 2 de
analysis/02-modelisation-mathematique.md sur une séance 10x30-30.

Séance modélisée en vitesse (km/h), échantillonnée toutes les secondes :
  - 10 min d'échauffement à 10 km/h
  - 10 x (30 s à 16 km/h / 30 s à 8 km/h)
  - 10 min de retour au calme à 10 km/h

Terrain plat (pente i = 0) : v_GAP = v_réelle (C_run(i)/C_run(0) = 1).
Seuil (vitesse_seuil) = 15 km/h.

Les formules elles-mêmes vivent dans metrics.py (testées dans test_metrics.py) ;
ce script ne fait que construire la séance d'exemple et appeler ces fonctions.
"""
import sys
import numpy as np

from metrics import (
    v_gap, ngp, intensity_factor, rtss, dss,
    ctl_suivant, atl_suivant, tsb,
)

sys.stdout.reconfigure(encoding="utf-8")
          # pas d'échantillonnage (secondes)
VITESSE_SEUIL_KMH = 15.0
V_REF_DESCENTE_KMH = 12.0   # vitesse de référence en descente (calibration DSS)
RESILIENCE_MUSC = 1.0       # trait `res_musc` du coureur, 0-1 (1 = référence)

# --- Construction de la séance (vitesse en km/h par bin de 5 s) ---

echauffement = [10] * 10 * 60
intervalle = []
for _ in range(10):
    intervalle += [16] * 30   # 30 s à 16 km/h
    intervalle += [8] * 30    # 30 s à 8 km/h
retour_calme = [10] * 10 * 60

vitesses_kmh = np.array(echauffement + intervalle + retour_calme, dtype=float)
n_bins = len(vitesses_kmh)

# --- Contruction de la pente
pentes = np.zeros(n_bins)      # séance plate
is_run = np.ones(n_bins, dtype=bool)  # only running

duree_totale_s = n_bins

print(f"Séance : {n_bins} bins de 1 s = {duree_totale_s} s = {duree_totale_s/60:.1f} min")

# --- §2.2 GAP, NGP, IF, rTSS ---

v_gap_kmh = v_gap(vitesses_kmh, pentes, is_run)
ngp_kmh = ngp(v_gap_kmh, fenetre_s=30)
IF = intensity_factor(ngp_kmh, VITESSE_SEUIL_KMH)
rTSS = rtss(duree_totale_s, IF)

print()
print(f"v_GAP moyen        : {v_gap_kmh.mean():.2f} km/h  (moyenne arithmétique brute)")
print(f"NGP                : {ngp_kmh:.2f} km/h  (lissée 30 s, pondérée ^4)")
print(f"vitesse_seuil       : {VITESSE_SEUIL_KMH:.2f} km/h")
print(f"IF                 : {IF:.3f}")
print(f"rTSS               : {rTSS:.1f}")

# --- §2.2 DSS (charge spécifique descente) ---
# Séance plate (pentes = 0 partout) : aucun bin en descente, donc DSS = 0 par
# construction. Formule quand même réutilisable avec un profil de pente non nul.

DSS = dss(vitesses_kmh, pentes, V_REF_DESCENTE_KMH, RESILIENCE_MUSC)

print(f"DSS                : {DSS:.1f}  (0 attendu : séance plate, aucune descente)")

# --- §1 CTL/ATL/TSB — départ à froid (CTL0 = ATL0 = 0), une seule séance ---

CTL_prec, ATL_prec = 0.0, 0.0
TSB = tsb(CTL_prec, ATL_prec)  # forme AVANT la séance du jour
CTL = ctl_suivant(CTL_prec, rTSS)
ATL = atl_suivant(ATL_prec, rTSS)

print()
print("CTL/ATL/TSB (départ à froid, CTL(t-1)=ATL(t-1)=0, une seule séance) :")
print(f"  CTL (après séance) : {CTL:.2f}")
print(f"  ATL (après séance) : {ATL:.2f}")
print(f"  TSB (avant séance) : {TSB:.2f}")
