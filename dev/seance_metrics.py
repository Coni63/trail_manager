"""
Script de test : calcule les métriques des sections 1 et 2 de
analysis/02-modelisation-mathematique.md sur une séance 10x30-30.

Séance modélisée en vitesse (km/h), échantillonnée toutes les 5 s :
  - 10 min d'échauffement à 10 km/h
  - 10 x (30 s à 16 km/h / 30 s à 8 km/h)
  - 10 min de retour au calme à 10 km/h

Terrain plat (pente i = 0) : v_GAP = v_réelle (C_run(i)/C_run(0) = 1).
Seuil (vitesse_seuil) = 15 km/h.
"""

import sys
sys.stdout.reconfigure(encoding="utf-8")
          # pas d'échantillonnage (secondes)
VITESSE_SEUIL_KMH = 15.0

# --- Construction de la séance (vitesse en km/h par bin de 5 s) ---

def repeter(vitesse_kmh: float, duree_s: float) -> list[float]:
    return [vitesse_kmh] * duree_s

echauffement = [10] * 10 * 60
intervalle = []
for _ in range(10):
    intervalle += [16] * 30   # 30 s à 16 km/h
    intervalle += [8] * 30    # 30 s à 8 km/h
retour_calme = [10] * 10 * 60

vitesses_kmh = echauffement + intervalle + retour_calme
n_bins = len(vitesses_kmh)
duree_totale_s = n_bins

print(f"Séance : {n_bins} bins de 1 s = {duree_totale_s} s = {duree_totale_s/60:.1f} min")

# --- §2.1 Coût énergétique (Minetti) ---
# Terrain plat -> i = 0 sur toute la séance, donc C_run(i)/C_run(0) = 1.
# Formule quand même implémentée pour être réutilisable avec un profil de pente.

def c_run(i: float) -> float:
    """Coût métabolique de la course en J/kg/m, i = pente en tangente (0.10 = 10 %)."""
    return (155.4 * i**5 - 30.4 * i**4 - 43.3 * i**3
            + 46.3 * i**2 + 19.5 * i + 3.6)

pentes = [0.0] * n_bins  # séance plate
c0 = c_run(0.0)

# --- §2.2 GAP, NGP, IF, rTSS ---

v_gap_kmh = [v * c_run(p) / c0 for v, p in zip(vitesses_kmh, pentes)]

def moyenne_roulante(serie: list[float], fenetre_s: int) -> list[float]:
    """Moyenne glissante (convolution), pas un découpage par blocs :
    la fenêtre avance bin par bin, chevauchement de fenetre_s/DT_S - 1 bins."""
    taille = max(1, fenetre_s)
    out = []
    for k in range(len(serie)):
        debut = max(0, k - taille + 1)
        fenetre = serie[debut:k + 1]
        out.append(sum(fenetre) / len(fenetre))
    return out

v_gap_30s = moyenne_roulante(v_gap_kmh, 30)
ngp_kmh = (sum(v**4 for v in v_gap_30s) / len(v_gap_30s)) ** 0.25

IF = ngp_kmh / VITESSE_SEUIL_KMH
rTSS = (duree_totale_s * IF**2) / 3600 * 100

print()
print(f"v_GAP moyen        : {sum(v_gap_kmh)/n_bins:.2f} km/h  (moyenne arithmétique brute)")
print(f"NGP                : {ngp_kmh:.2f} km/h  (lissée 30 s, pondérée ^4)")
print(f"vitesse_seuil       : {VITESSE_SEUIL_KMH:.2f} km/h")
print(f"IF                 : {IF:.3f}")
print(f"rTSS               : {rTSS:.1f}")

# --- §1 CTL/ATL/TSB — départ à froid (CTL0 = ATL0 = 0), une seule séance ---

CTL_prec, ATL_prec = 0.0, 0.0
CTL = CTL_prec + (rTSS - CTL_prec) / 42
ATL = ATL_prec + (rTSS - ATL_prec) / 7
TSB = CTL_prec - ATL_prec  # forme AVANT la séance du jour

print()
print("CTL/ATL/TSB (départ à froid, CTL(t-1)=ATL(t-1)=0, une seule séance) :")
print(f"  CTL (après séance) : {CTL:.2f}")
print(f"  ATL (après séance) : {ATL:.2f}")
print(f"  TSB (avant séance) : {TSB:.2f}")
