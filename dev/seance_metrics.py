"""
Script de test : calcule les métriques des sections 1 et 2 de
analysis/02-modelisation-mathematique.md sur une séance 10x30-30.

Séance modélisée en vitesse (km/h), échantillonnée toutes les secondes :
  - 10 min d'échauffement à 10 km/h
  - 10 x (30 s à 16 km/h / 30 s à 8 km/h)
  - 10 min de retour au calme à 10 km/h

Terrain plat (pente i = 0) : v_GAP = v_réelle (C_run(i)/C_run(0) = 1).
Seuil (vitesse_seuil) = 15 km/h.
"""
import sys
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
          # pas d'échantillonnage (secondes)
VITESSE_SEUIL_KMH = 15.0

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

# --- §2.1 Coût énergétique (Minetti) ---
# Terrain plat -> i = 0 sur toute la séance, donc C_run(i)/C_run(0) = 1.
# Formule quand même implémentée pour être réutilisable avec un profil de pente.
# Polynômes vectorisés (np.polyval s'applique en une passe à un array de pentes,
# donc pas besoin de cache/grille de précalcul : c'est déjà du O(n) sans bin par bin).

COEFS_RUN = np.array([155.4, -30.4, -43.3, 46.3, 19.5, 3.6])
COEFS_WALK = np.array([280.5, -58.7, -76.8, 51.9, 19.6, 2.5])

def c_run(i: np.ndarray) -> np.ndarray:
    """Coût métabolique de la course en J/kg/m, i = pente en tangente (0.10 = 10 %)."""
    return np.polyval(COEFS_RUN, i)

def c_walk(i: np.ndarray) -> np.ndarray:
    """Coût métabolique de la marche en J/kg/m, i = pente en tangente (0.10 = 10 %)."""
    return np.polyval(COEFS_WALK, i)


# --- §2.2 GAP, NGP, IF, rTSS ---
c0 = c_run(0.0)
w0 = c_walk(0.0)
v_gap_kmh = np.where(is_run,
                      vitesses_kmh * c_run(pentes) / c0,
                      vitesses_kmh * c_walk(pentes) / w0)


def moyenne_roulante(serie: np.ndarray, fenetre_s: int) -> np.ndarray:
    """Moyenne glissante, pas un découpage par blocs : la fenêtre avance bin
    par bin (chevauchement de fenetre_s - 1 bins), tronquée en début de série
    (les fenetre_s-1 premiers points sont moyennés sur moins de fenetre_s valeurs).

    Implémentée par convolution directe (np.convolve, pas de FFT) : c'est du
    O(n * fenetre_s), mais pour fenetre_s fixe (30 s) et n grand (séances
    longues), le facteur constant C de convolve bat le cumsum vectorisé
    (~25-30 % plus rapide en pratique, mesuré jusqu'à n=10M). Si fenetre_s
    devait un jour croître avec n, repasser à une version cumsum en O(n)."""
    n = len(serie)
    taille = max(1, fenetre_s)
    kernel = np.ones(taille)
    # mode='full'[:n] : convolve('full')[k] = sum(serie[max(0,k-taille+1):k+1]),
    # exactement la fenêtre calée sur le passé qu'on veut. On tronque après les
    # n premières valeurs (celles calées à droite de 'full' ne servent à rien ici).
    somme = np.convolve(serie, kernel, mode='full')[:n]
    # Nombre d'éléments réels dans chaque fenêtre en début de série : [1, 2, ..., taille, taille, ...]
    compte = np.minimum(np.arange(1, n + 1), taille)
    return somme / compte

v_gap_30s = moyenne_roulante(v_gap_kmh, 30)
ngp_kmh = np.mean(v_gap_30s ** 4) ** 0.25

IF = ngp_kmh / VITESSE_SEUIL_KMH
rTSS = (duree_totale_s * IF**2) / 3600 * 100

print()
print(f"v_GAP moyen        : {v_gap_kmh.mean():.2f} km/h  (moyenne arithmétique brute)")
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
