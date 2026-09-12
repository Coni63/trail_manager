"""
Fonctions de calcul des métriques de charge d'entraînement, extraites de
analysis/02-modelisation-mathematique.md (§1 et §2). Séparées de
seance_metrics.py / charge_journaliere.py pour être testables unitairement
(voir test_metrics.py) et réutilisables ailleurs (moteur de simulation).

Convention : toutes les fonctions sont pures (pas d'état global, pas
d'impression), et vectorisées numpy quand l'entrée est une série temporelle.
"""
import numpy as np

# --- §2.1 Coût énergétique de la locomotion (Minetti) ---

COEFS_RUN = np.array([155.4, -30.4, -43.3, 46.3, 19.5, 3.6])
COEFS_WALK = np.array([280.5, -58.7, -76.8, 51.9, 19.6, 2.5])


def c_run(i: np.ndarray) -> np.ndarray:
    """Coût métabolique de la course en J/kg/m, i = pente en tangente (0.10 = 10 %)."""
    return np.polyval(COEFS_RUN, i)


def c_walk(i: np.ndarray) -> np.ndarray:
    """Coût métabolique de la marche en J/kg/m, i = pente en tangente (0.10 = 10 %)."""
    return np.polyval(COEFS_WALK, i)


# --- §2.2 GAP, NGP, IF, rTSS ---

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


def v_gap(vitesses_kmh: np.ndarray, pentes: np.ndarray, is_run: np.ndarray) -> np.ndarray:
    """Allure équivalente plat (Grade Adjusted Pace) : v_GAP = v_réelle · C(i)/C(0),
    avec C = C_run ou C_walk selon is_run (bool array)."""
    c0 = c_run(0.0)
    w0 = c_walk(0.0)
    return np.where(is_run,
                     vitesses_kmh * c_run(pentes) / c0,
                     vitesses_kmh * c_walk(pentes) / w0)


def ngp(v_gap_kmh: np.ndarray, fenetre_s: int = 30) -> float:
    """Normalized Graded Pace : moyenne roulante (fenetre_s) de v_GAP, élevée à
    la puissance 4, moyennée sur la séance, racine 4e. Pénalise l'irrégularité :
    sur un effort parfaitement constant, NGP = v_GAP."""
    v_gap_lisse = moyenne_roulante(v_gap_kmh, fenetre_s)
    return float(np.mean(v_gap_lisse ** 4) ** 0.25)


def intensity_factor(ngp_kmh: float, vitesse_seuil_kmh: float) -> float:
    """IF = NGP / vitesse_seuil. Attention : vitesse_seuil doit être une
    vitesse (km/h ou m/s), pas une allure (min/km), sinon le sens du ratio s'inverse."""
    return ngp_kmh / vitesse_seuil_kmh


def rtss(duree_totale_s: float, if_: float) -> float:
    """running TSS = (durée_s · IF²) / 3600 · 100."""
    return (duree_totale_s * if_ ** 2) / 3600 * 100


# --- §2.2 DSS (charge spécifique descente) ---

def dss(vitesses_kmh: np.ndarray, pentes: np.ndarray,
        v_ref_descente_kmh: float, resilience_musc: float,
        pas_s: float = 1.0) -> float:
    """DSS = Σ_bins (D−_m) · (v_descente / v_ref)^1.5 · (1 / résilience_musc).

    D−_bin = distance parcourue dans le bin (v · pas_s) · |pente|, uniquement
    pour les bins en descente (pente < 0). resilience_musc ∈ ]0, 1] (trait
    `res_musc` du coureur, 1 = référence)."""
    distance_m = vitesses_kmh / 3.6 * pas_s
    d_moins_m = np.where(pentes < 0, distance_m * (-pentes), 0.0)
    contrib = d_moins_m * (vitesses_kmh / v_ref_descente_kmh) ** 1.5 / resilience_musc
    return float(contrib.sum())


# --- §1 CTL/ATL/TSB ---

def ctl_suivant(ctl_prec: float, charge_jour: float, tau: int = 42) -> float:
    """CTL(t) = CTL(t-1) + (charge(t) − CTL(t-1)) / tau, tau ≈ 42 j ("fitness")."""
    return ctl_prec + (charge_jour - ctl_prec) / tau


def atl_suivant(atl_prec: float, charge_jour: float, tau: int = 7) -> float:
    """ATL(t) = ATL(t-1) + (charge(t) − ATL(t-1)) / tau, tau ≈ 7 j ("fatigue")."""
    return atl_prec + (charge_jour - atl_prec) / tau


def tsb(ctl_prec: float, atl_prec: float) -> float:
    """TSB = CTL(t-1) − ATL(t-1), la forme AVANT la charge du jour courant."""
    return ctl_prec - atl_prec


def ctl_atl_tsb_serie(charges: np.ndarray, tau_ctl: int = 42, tau_atl: int = 7,
                       ctl0: float = 0.0, atl0: float = 0.0):
    """Applique ctl_suivant/atl_suivant/tsb jour après jour sur une série de
    charges. Récursif par nature (chaque jour dépend du précédent), donc pas
    vectorisable : boucle explicite sur des scalaires.

    Retourne (CTL, ATL, TSB), trois arrays de même longueur que `charges`.
    ctl0/atl0 : état la veille du premier jour (0.0 = départ à froid)."""
    n = len(charges)
    CTL = np.zeros(n)
    ATL = np.zeros(n)
    TSB = np.zeros(n)
    ctl_prec, atl_prec = ctl0, atl0
    for j in range(n):
        TSB[j] = tsb(ctl_prec, atl_prec)
        CTL[j] = ctl_suivant(ctl_prec, charges[j], tau_ctl)
        ATL[j] = atl_suivant(atl_prec, charges[j], tau_atl)
        ctl_prec, atl_prec = CTL[j], ATL[j]
    return CTL, ATL, TSB


# --- §2.3 Monotonie, Strain, Ramp rate, ACWR ---

def monotonie(charges_fenetre: np.ndarray) -> float:
    """Monotonie (Foster) = moyenne / écart-type de la charge sur une fenêtre
    (typiquement 7 j). Écart-type nul (fenêtre constante, y compris tout à
    zéro) : retourne 0.0 plutôt qu'une division par zéro — pas de risque de
    monotonie à détecter s'il n'y a pas de variabilité à mesurer."""
    ecart_type = charges_fenetre.std()
    if ecart_type == 0:
        return 0.0
    return float(charges_fenetre.mean() / ecart_type)


def strain(charge_hebdo: float, monotonie_val: float) -> float:
    """Strain = charge hebdomadaire totale × monotonie."""
    return charge_hebdo * monotonie_val


def ramp_rate(ctl_actuel: float, ctl_il_y_a_7j: float) -> float:
    """Ramp rate = CTL(t) − CTL(t−7). Danger si > 5-8 CTL/semaine."""
    return ctl_actuel - ctl_il_y_a_7j


def acwr(atl_actuel: float, ctl_actuel: float) -> float:
    """Acute:Chronic Workload Ratio = ATL / CTL. CTL nul (tout début, aucun
    historique) : retourne 0.0 plutôt qu'une division par zéro. Zone de
    confort usuellement citée : 0.8-1.3 (indicateur controversé, cf. §2.3 du
    doc de modélisation)."""
    if ctl_actuel == 0:
        return 0.0
    return atl_actuel / ctl_actuel


def _sommes_glissantes(serie: np.ndarray, fenetre_j: int) -> np.ndarray:
    """Somme glissante tronquée en début de série (fenêtre_j jours), via
    sommes cumulées : O(n) et entièrement vectorisé, pas de boucle Python.
    fenetre[j] = somme(serie[max(0, j-fenetre_j+1) : j+1])."""
    n = len(serie)
    cumul = np.concatenate(([0.0], np.cumsum(serie)))  # cumul[k] = somme des k premiers éléments
    idx_fin = np.arange(1, n + 1)
    idx_debut = np.maximum(0, idx_fin - fenetre_j)
    return cumul[idx_fin] - cumul[idx_debut]


def charge_hebdo_serie(charges: np.ndarray, fenetre_j: int = 7) -> np.ndarray:
    """Charge cumulée sur une fenêtre glissante de fenetre_j jours (tronquée
    en début de série, comme moyenne_roulante)."""
    return _sommes_glissantes(charges, fenetre_j)


def monotonie_serie(charges: np.ndarray, fenetre_j: int = 7) -> np.ndarray:
    """Monotonie (Foster) jour par jour sur une fenêtre glissante de
    fenetre_j jours. Vectorisé via sommes cumulées : E[X] et E[X²] sur la
    fenêtre donnent moyenne et écart-type (Var = E[X²] − E[X]²) sans boucle
    Python. Même garde-fou que `monotonie()` : écart-type nul -> 0.0."""
    n = len(charges)
    compte = np.arange(1, n + 1) - np.maximum(0, np.arange(1, n + 1) - fenetre_j)
    somme = _sommes_glissantes(charges, fenetre_j)
    somme_carres = _sommes_glissantes(charges ** 2, fenetre_j)
    moyenne = somme / compte
    # max(..., 0) : garde-fou contre un résidu négatif dû aux arrondis flottants
    # quand la variance réelle est nulle.
    variance = np.maximum(somme_carres / compte - moyenne ** 2, 0.0)
    ecart_type = np.sqrt(variance)
    resultat = np.zeros_like(ecart_type)
    # np.where évaluerait la division sur tout le tableau avant de masquer,
    # d'où le `where=` de np.divide pour éviter le RuntimeWarning "divide by zero"
    # là où ecart_type == 0 (fenêtre constante, y compris tout à zéro).
    np.divide(moyenne, ecart_type, out=resultat, where=ecart_type > 0)
    return resultat


def strain_serie(charges: np.ndarray, fenetre_j: int = 7) -> np.ndarray:
    """Strain jour par jour = charge_hebdo × monotonie, sur la même fenêtre."""
    return charge_hebdo_serie(charges, fenetre_j) * monotonie_serie(charges, fenetre_j)


def ramp_rate_serie(CTL: np.ndarray, fenetre_j: int = 7) -> np.ndarray:
    """Ramp rate jour par jour = CTL(t) − CTL(t−fenetre_j), avec CTL(t<0) = 0
    (pas d'historique avant le début de la série)."""
    n = len(CTL)
    if n <= fenetre_j:
        ctl_decale = np.zeros(n)
    else:
        ctl_decale = np.concatenate((np.zeros(fenetre_j), CTL[:n - fenetre_j]))
    return CTL - ctl_decale


def acwr_serie(ATL: np.ndarray, CTL: np.ndarray) -> np.ndarray:
    """ACWR jour par jour = ATL/CTL, 0.0 là où CTL est nul (garde-fou division
    par zéro, cf. `acwr()`). `where=` évite le RuntimeWarning que déclencherait
    np.where en calculant la division sur tout le tableau avant de masquer."""
    resultat = np.zeros_like(CTL, dtype=float)
    np.divide(ATL, CTL, out=resultat, where=CTL > 0)
    return resultat


def charges_journalieres_vers_indicateurs(charges: np.ndarray, fenetre_j: int = 7):
    """Calcule CTL/ATL/TSB puis charge_hebdo/monotonie/strain/ramp_rate/acwr
    sur une fenêtre glissante de fenetre_j jours (tronquée en début de série).
    Entièrement vectorisé (une fonction *_serie par indicateur), à l'exception
    de CTL/ATL/TSB : cette récursion EWMA n'a pas d'équivalent numpy vectorisé
    (chaque jour dépend du résultat du jour précédent), cf. ctl_atl_tsb_serie.
    Retourne un dict de arrays, toutes de même longueur que `charges`."""
    CTL, ATL, TSB = ctl_atl_tsb_serie(charges)
    return {
        "charge": charges,
        "CTL": CTL,
        "ATL": ATL,
        "TSB": TSB,
        "charge_hebdo": charge_hebdo_serie(charges, fenetre_j),
        "monotonie": monotonie_serie(charges, fenetre_j),
        "strain": strain_serie(charges, fenetre_j),
        "ramp_rate": ramp_rate_serie(CTL, fenetre_j),
        "acwr": acwr_serie(ATL, CTL),
    }


# --- §6.1 Modèle de risque de blessure (hasard journalier) ---
#
# Version "globale" du doc (pas le modèle par tissu du §6.2, qui suppose un
# état persistant — dommage/capacité/réparation par tissu — qu'on ne simule
# pas encore). Constantes de calibration choisies pour retomber, très
# grossièrement, sur les ordres de grandeur visés au §10.1 (~0.5 blessure/an
# pour un profil prudent, ~2-4/an pour un profil qui pousse fort) : à revoir
# avec le harnais de tests de sanité du §10.2 dès qu'on aura de vraies données
# de blessures à caler dessus. Comme partout ailleurs dans le doc, ce sont des
# points de départ raisonnables, pas des vérités.

LAMBDA0_BLESSURE = 0.001
BETA_ACWR = 1.5
BETA_MONOTONIE = 0.4
BETA_RESILIENCE = 1.0
BETA_RAMP_RATE = 0.08
BETA_DSS = 0.6
BETA_AGE = 0.2
BETA_EXPERIENCE = 0.08
BETA_SOMMEIL = 0.3


def penalite_acwr(acwr_val):
    """pénalité_ACWR = max(0, ACWR − 1.3)² + max(0, 0.8 − ACWR)·0.5.
    Nulle dans la zone de confort 0.8-1.3, pénalise les deux extrêmes (charge
    relative trop haute OU trop basse). Fonctionne aussi bien sur un scalaire
    que sur un array numpy (np.maximum se comporte comme max élément par élément)."""
    return np.maximum(0.0, acwr_val - 1.3) ** 2 + np.maximum(0.0, 0.8 - acwr_val) * 0.5


def _exposant_risque_blessure(acwr_val, monotonie_val, ramp_rate_val,
                               dss_normalisee, resilience_musc, age,
                               annees_pratique, deficit_sommeil):
    """Partie commune scalaire/vectorisée de λ(t) : cf. proba_blessure_jour
    pour le détail des termes."""
    ramp_positif = np.maximum(0.0, ramp_rate_val)
    return (
        BETA_ACWR * penalite_acwr(acwr_val)
        + BETA_MONOTONIE * (monotonie_val - 1.5)
        + BETA_RESILIENCE * (1 - resilience_musc)
        + BETA_RAMP_RATE * ramp_positif
        + BETA_DSS * dss_normalisee
        + BETA_AGE * (age - 30) / 10
        - BETA_EXPERIENCE * annees_pratique
        + BETA_SOMMEIL * deficit_sommeil
    )


def proba_blessure_jour(acwr_val: float, monotonie_val: float, ramp_rate_val: float,
                         dss_normalisee: float = 0.0, resilience_musc: float = 1.0,
                         age: float = 30.0, annees_pratique: float = 0.0,
                         deficit_sommeil: float = 0.0) -> float:
    """Probabilité de blessure aujourd'hui (§6.1) :

        P(blessure) = 1 − e^(−λ(t))
        λ(t) = λ₀ · exp(β₁·pénalité_ACWR + β₂·(monotonie−1.5) + β₃·(1−résilience)
                         + β₄·ramp_rate⁺ + β₅·DSS_normalisée + β₆·(âge−30)/10
                         − β₇·années_pratique + β₈·déficit_sommeil)

    Les paramètres optionnels (resilience_musc, age, annees_pratique,
    deficit_sommeil) ont une valeur par défaut neutre (contribution nulle à
    l'exposant) tant que le simulateur ne produit pas ces variables d'état —
    à brancher dès qu'un coureur avec un historique/profil existera.
    dss_normalisee doit être ramenée à une échelle comparable aux autres
    termes (ex. DSS de la séance / DSS de référence d'un profil "normal")."""
    exposant = _exposant_risque_blessure(
        acwr_val, monotonie_val, ramp_rate_val, dss_normalisee,
        resilience_musc, age, annees_pratique, deficit_sommeil,
    )
    lam = LAMBDA0_BLESSURE * np.exp(exposant)
    return float(1 - np.exp(-lam))


def proba_blessure_serie(acwr_serie_val: np.ndarray, monotonie_serie_val: np.ndarray,
                          ramp_rate_serie_val: np.ndarray, dss_normalisee=0.0,
                          resilience_musc=1.0, age=30.0, annees_pratique=0.0,
                          deficit_sommeil=0.0) -> np.ndarray:
    """Version vectorisée de proba_blessure_jour, jour par jour sur des arrays
    (ex. les sorties de charges_journalieres_vers_indicateurs). Les paramètres
    optionnels acceptent un scalaire (même valeur tous les jours) ou un array
    de même longueur (ex. un déficit de sommeil qui varie jour après jour)."""
    exposant = _exposant_risque_blessure(
        acwr_serie_val, monotonie_serie_val, ramp_rate_serie_val, dss_normalisee,
        resilience_musc, age, annees_pratique, deficit_sommeil,
    )
    lam = LAMBDA0_BLESSURE * np.exp(exposant)
    return np.exp(-lam)
