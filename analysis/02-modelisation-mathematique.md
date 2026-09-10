# Trail Manager — Modélisation mathématique (v0.1)

> Objectif : un modèle **physiologiquement plausible, calibrable et jouable**.
> On ne cherche pas la vérité scientifique, on cherche des dynamiques qui
> *se comportent* comme la réalité : gains rapides puis plateau, surcharge qui
> casse, spécificité de l'entraînement, effondrement au km 70 quand on a mal mangé.
>
> Convention : toutes les constantes notées `k`, `τ`, `G`, `α`… sont des
> **paramètres de calibration**. Les valeurs données sont des points de départ
> raisonnables, pas des vérités.

---

<a name="glossaire"></a>
## Glossaire des abréviations

| Abréviation | Signification | Description rapide |
|---|---|---|
| **TSS** | Training Stress Score | Charge d'une séance pondérée par durée × intensité² (Coggan/TrainingPeaks). Base de CTL/ATL/TSB. |
| **rTSS** | running TSS | Variante course à pied du TSS : l'IF est calculé sur l'allure (NGP/allure seuil) plutôt que sur la puissance vélo. Formule identique une fois exprimée en IF. |
| **CTL** | Chronic Training Load | "Fitness" — EWMA de la charge quotidienne, τ ≈ 42 j. |
| **ATL** | Acute Training Load | "Fatigue" — EWMA de la charge quotidienne, τ ≈ 7 j. |
| **TSB** | Training Stress Balance | "Forme du jour" — CTL(t-1) − ATL(t-1). |
| **IF** | Intensity Factor | Intensité relative de la séance par rapport au seuil (NGP/vitesse_seuil, ou NP/FTP en vélo). |
| **NGP** | Normalized Graded Pace | Allure normalisée corrigée de la pente — moyenne roulante 30 s de la GAP à la puissance 4 (équivalent running du NP cycliste). |
| **GAP** | Grade Adjusted Pace | Allure équivalente plat : allure réelle corrigée par le coût métabolique de la pente. |
| **TRIMP** | Training Impulse | Charge d'entraînement basée sur la FC, pondération exponentielle du %FC de réserve (modèle de Banister). |
| **DSS** | Downhill Stress Score *(nom de travail)* | Charge spécifique à la descente, comptée à part car elle fatigue un système différent (dégâts musculaires excentriques). |
| **ACWR** | Acute:Chronic Workload Ratio | Ratio ATL/CTL — indicateur (controversé) de risque de surcharge. Zone confort ≈ 0.8–1.3. |
| **EWMA** | Exponentially Weighted Moving Average | Moyenne mobile à pondération exponentielle décroissante — mécanisme de lissage utilisé pour CTL/ATL et les stimulus de qualité. |
| **VO2max** | Volume d'O2 maximal | Consommation maximale d'oxygène (ml/kg/min) — proxy de la puissance aérobie. |
| **SV2** | 2ᵉ Seuil Ventilatoire | Seuil anaérobie — transition vers le domaine d'effort "sévère" ; sert de référence à `frac_seuil` et `CS`. |
| **T90** | Temps > 90 % VO2max | Proxy principal du stimulus VO2max pendant une séance (Billat, Buchheit & Laursen). |
| **W′** (Wprime) | Réserve anaérobie | Capacité de travail disponible au-delà de la vitesse critique (kJ) — modèle CS/W′ de Skiba/Jones. |
| **CS** | Critical Speed | Vitesse critique — équivalent course du CP cycliste, proche de la vitesse au SV2. |
| **CP** | Critical Power | Puissance critique — équivalent vélo de la CS. |
| **RPE** | Rate of Perceived Exertion | Échelle de perception subjective de l'effort. |
| **GI** | Gastro-Intestinal | Troubles digestifs en course (nausée, vomissement). |
| **DNF** | Did Not Finish | Abandon en course. |
| **Tc** | Température corporelle | "Core temperature" — pilote l'hyperthermie et l'arrêt forcé. |
| **Na** | Sodium | Natrémie — risque d'hyponatrémie si dilution excessive. |
| **SNC** | Système Nerveux Central | Origine de la fatigue "centrale" (`F_nerv`), distincte de la fatigue métabolique ou musculaire. |
| **RED-S** | Relative Energy Deficiency in Sport | Syndrome de déficit énergétique relatif — risque lié à un déficit calorique trop agressif. |
| **ITB** | IlioTibial Band | Bandelette ilio-tibiale — un des tissus modélisés dans le risque de blessure (§6.2). |
| **D+ / D−** | Dénivelé positif / négatif | Mètres montés / descendus sur un parcours ou un segment. |
| **UTMB** | Ultra-Trail du Mont-Blanc | Course de référence utilisée pour les ordres de grandeur de calibration (§10). |

---

## Sommaire

0. [Glossaire des abréviations](#glossaire)
1. [Pourquoi CTL/ATL seul ne suffit pas](#1)
2. [Quantifier une séance : charge, coût énergétique, dénivelé](#2)
3. [Le modèle multi-qualités (le cœur)](#3)
4. [Cas d'école : que fait vraiment un 30-30 ?](#4)
5. [Fatigue, récupération, forme du jour](#5)
6. [Blessures : modèle de hasard par tissu](#6)
7. [Des qualités à la performance : le moteur de course](#7)
8. [Simulation de course : glycogène, eau, dégâts, moral](#8)
9. [Matériel, environnement, nuit](#9)
10. [Calibration, tests de sanité, ordres de grandeur](#10)

---

<a name="1"></a>
## 1. Pourquoi CTL/ATL seul ne suffit pas

Le modèle de référence (Banister → Coggan → intervals.icu) est un **impulse-response
à deux composantes** :

```
CTL(t) = CTL(t-1) + (TSS(t) − CTL(t-1)) / 42      "fitness"   (EWMA τ=42 j)
ATL(t) = ATL(t-1) + (TSS(t) − ATL(t-1)) /  7      "fatigue"   (EWMA τ=7 j)
TSB(t) = CTL(t-1) − ATL(t-1)                      "forme"
```

Forme Banister équivalente :

```
Perf(t) = p₀ + k₁·Σ wᵢ·e^(−(t−tᵢ)/τ₁) − k₂·Σ wᵢ·e^(−(t−tᵢ)/τ₂)
          τ₁ ≈ 42 j, τ₂ ≈ 7 j, k₂ > k₁
```

C'est excellent pour **la forme du jour** et pour l'affûtage (le TSB monte quand on
réduit la charge, la perf pique ~10–20 j après le pic de CTL). Mais c'est
**scalaire** : 100 TSS de footing = 100 TSS de 30-30. Or :

- un bloc de sorties longues et un bloc de VMA ne produisent pas le même coureur ;
- l'économie de course ne s'améliore pas au même rythme que le VO2max ;
- la résistance à la descente n'a rien à voir avec la puissance aérobie ;
- le pic UTMB ne s'obtient pas comme le pic 10 km.

**Proposition : garder CTL/ATL comme couche "fatigue/forme" globale (elle est bonne
pour ça), et ajouter au-dessus un modèle multi-qualités avec un vecteur de
stimulus par séance.** C'est l'architecture du document.

```
        Séance ──► vecteur de stimulus S = (S_vo2, S_seuil, S_eco, S_endu, S_musc, …)
                     │                      │
                     │                      └─► Qualités qᵢ (impulse-response, τ propres)
                     └─► TSS ──► CTL/ATL/TSB ──► forme du jour, plafond de charge
                             └─► charges par tissu ──► risque de blessure
```

---

<a name="2"></a>
## 2. Quantifier une séance

### 2.1 Coût énergétique en fonction de la pente (Minetti)

Indispensable en trail. Coût métabolique en J·kg⁻¹·m⁻¹ (mètres **parcourus**, pas
horizontaux), `i` = pente en tangente (0.10 = 10 %), valide de −0.45 à +0.45 :

```
C_run(i)  = 155.4·i⁵ −  30.4·i⁴ −  43.3·i³ + 46.3·i² + 19.5·i + 3.6
C_walk(i) = 280.5·i⁵ −  58.7·i⁴ −  76.8·i³ + 51.9·i² + 19.6·i + 2.5
```

Quelques valeurs (J/kg/m) :

| pente | −20 % | −10 % | 0 % | +10 % | +20 % | +30 % | +40 % |
|---|---|---|---|---|---|---|---|
| courir | 2.9 | 2.4 | 3.6 | 5.97 | 8.91 | 12.3 | 16.2 |
| marcher | 2.0 | 1.6 | 2.5 | 4.90 | 7.88 | 11.2 | 15.0 |

> Note : marcher est **toujours** moins cher au mètre que courir. Le vrai arbitrage
> n'est donc pas le coût mais la **vitesse atteignable** (§7.3). C'est ce qui fait
> qu'on court sur le plat et qu'on marche à 25 %.

**Extension descente raide** : au-delà de −35 %, la vitesse est bornée par la
technicité, pas par le métabolisme. Et le coût *métabolique* baisse alors que
le coût *musculaire* (excentrique) explose → deux variables distinctes (§8.4).

### 2.2 Allure équivalente plat (GAP) et charge

```
v_GAP  =  v_réelle · C_run(i) / C_run(0)
```

Puis charge de type rTSS (intervals.icu / TrainingPeaks) :

```
IF   = NGP / vitesse_seuil
rTSS = (durée_s · IF²) / 3600 · 100
```

**NGP (Normalized Graded Pace)** — ce n'est pas la moyenne de `v_GAP`, c'est une
version lissée et pondérée qui pénalise l'irrégularité (équivalent du Normalized
Power cycliste, transposé à la vitesse) :

```
1. fenêtre glissante de 30 s sur v_GAP(t)   ← convolution, pas de découpage par blocs :
                                               la fenêtre avance point par point (1 s),
                                               chaque v_GAP_30s(t) est la moyenne des
                                               30 dernières secondes
2. v_GAP_30s(t) ⁴                            ← élever chaque valeur lissée à la puissance 4
3. moyenne sur toute la séance
4. racine 4ᵉ du résultat                     → NGP
```

La puissance 4 fait qu'un effort irrégulier (fractionné, relances) donne un NGP
**supérieur** à la simple moyenne arithmétique de `v_GAP`, même à distance/temps
égal — l'irrégularité coûte plus cher que la régularité, ce qui est le point de
la métrique. Sur un effort parfaitement constant, `NGP = v_GAP` (une constante à
la puissance 4 puis racine 4ᵉ redonne la même constante).

> ⚠️ Cohérence d'unités : `vitesse_seuil` doit être une **vitesse** (km/h ou m/s),
> pas une allure (min/km). Avec une vraie allure il faut inverser le ratio
> (`allure_seuil / allure_NGP`), sinon le sens du IF s'inverse (aller plus vite
> réduirait l'allure donc ferait *baisser* le IF, ce qui est faux).

Alternative FC (utile quand on n'a pas d'allure fiable), TRIMP de Banister :

```
x     = (FC − FC_repos) / (FC_max − FC_repos)
TRIMP = durée_min · x · 0.64·e^(1.92·x)        (♂ ; 0.86·e^(1.67x) pour ♀)
```

**Charge spécifique descente** — à compter séparément, car elle ne fatigue pas le
même système :

```
DSS = Σ_segments  (D−_m) · (v_descente / v_ref)^1.5 · (1 / résilience_musc)
```

### 2.3 Autres agrégats utiles (dashboard + risque)

```
Monotonie (Foster)  = moyenne(charge journalière sur 7 j) / écart-type(charge sur 7 j)
Strain              = charge hebdo × monotonie
Ramp rate           = CTL(t) − CTL(t−7)                          (danger si > 5–8 TSS/sem)
ACWR (EWMA)         = ATL / CTL                                  (zone confort 0.8–1.3)
```

> ⚠️ L'ACWR est méthodologiquement critiqué dans la littérature (Impellizzeri et al.).
> Pour un jeu c'est parfait : c'est intuitif, ça produit la bonne dynamique
> ("t'as augmenté trop vite"). Mais ne le vends pas comme une vérité.

---

<a name="3"></a>
## 3. Le modèle multi-qualités

### 3.1 Les qualités modélisées

| # | Qualité `q` | Unité | Plage humaine | τ_gain | τ_perte | Commentaire |
|---|---|---|---|---|---|---|
| 1 | `VO2max` | ml/kg/min | 35 → 85 | 10–20 j | 20–40 j | monte et descend vite |
| 2 | `frac_seuil` | % VO2max au SV2 | 0.72 → 0.90 | 25–40 j | 50 j | fraction utilisable |
| 3 | `eco` | J/kg/m à plat | 4.2 → 3.2 | 120–400 j | 500+ j | très lente, quasi acquise |
| 4 | `endu` | indice de durabilité | 0.03 → 0.09 | 90–200 j | 200 j | pilote la décroissance temporelle |
| 5 | `res_musc` | 0 → 1 | | 30–60 j | 60 j | tolérance excentrique |
| 6 | `gut` | g CHO/h absorbables | 40 → 110 | 20–40 j | 40 j | entraînable ! |
| 7 | `fatmax` | g lipides/min | 0.4 → 1.5 | 40–80 j | 80 j | flexibilité métabolique |
| 8 | `force_cote` | 0 → 1 | | 20–40 j | 40 j | marche rapide, relances |
| 9 | `Wprime` | kJ | 8 → 30 | 10–20 j | 15 j | réserve anaérobie |
| 10 | `tech_desc` | 0 → 1 | | 60 j | 300 j | compétence, se perd peu |
| 11 | `mental` | 0 → 1 | | lent | lent | monte avec les finishes durs |
| 12 | `acclim_chaleur` | 0 → 1 | | 10–14 j | 20–25 j | état court terme |
| 13 | `acclim_alt` | 0 → 1 | | 15–25 j | 20–30 j | état court terme |

### 3.2 Équation générique d'évolution

Pour chaque qualité `q` (pas journalier) :

```
Δq =  G_q · Ŝ_q(t) · (1 − q/q_max)^γ · R(t)          ← gain
    − D_q · (q − q_base)                              ← retour vers la base (détraining)
```

avec :
- `G_q` : gain unitaire (calibré pour donner des progressions réalistes, §10)
- `Ŝ_q(t)` : **stimulus effectif** de la qualité, lissé (voir 3.4)
- `q_max` : plafond génétique **caché**, tiré à la création → moteur du replay value
- `γ ≈ 1.5–2` : la saturation près du plafond doit être brutale
- `q_base` : niveau plancher sédentaire (on ne redescend pas à zéro)
- `D_q = 1/τ_perte`
- `R(t) ∈ [0,1]` : **facteur de récupération/disponibilité** — on n'assimile pas
  si on est cramé :

```
R(t) = clamp( 1 − λ·max(0, ATL/CTL − 1.15), 0.2, 1 ) · f_sommeil · f_nutrition · f_âge
```

C'est le point clé qui rend le surentraînement puni : **la charge continue de
fatiguer mais ne produit plus de gains**.

### 3.3 Matrice de stimulus séance → qualité

Chaque séance produit un vecteur brut `S`. Approche recommandée : ne **pas**
partir des zones, mais de **grandeurs physiologiques mesurables**, plus robustes :

| Stimulus primaire | Définition | Alimente principalement |
|---|---|---|
| `T90` | temps passé > 90 % VO2max | `VO2max` (§4) |
| `T_seuil` | temps entre 88 % et 100 % de vSV2 | `frac_seuil` |
| `V_facile` | volume (min) < 80 % vSV2 | `frac_seuil`, `eco`, `fatmax`, `endu` |
| `T_long` | temps au-delà de 90 min en continu | `endu`, `fatmax` |
| `T_glyco_bas` | temps couru avec glycogène < 40 % | `fatmax`, `endu` (et risque ↑) |
| `D+` | mètres de dénivelé positif | `force_cote`, `eco` |
| `D−_agressif` | descente rapide (via DSS §2.2) | `res_musc` (et dégâts) |
| `T_sprint` | temps > 105 % vVO2max | `Wprime`, `eco` (raideur) |
| `Renfo` | charge de musculation/plyo | `eco`, `res_musc`, `force_cote` |
| `CHO_ingérés/h` | en sortie longue | `gut` |
| `Chaleur`/`Altitude` | temps d'exposition | acclimatations |

Puis une **matrice de couplage** `W[stimulus][qualité]` (avec un peu de transfert
croisé, jamais 0 partout) :

```
                 VO2   seuil   eco   endu   fatmax  res_musc  force  W'
T90             1.00    0.35   0.10   0.05    0.00     0.00    0.10  0.15
T_seuil         0.30    1.00   0.15   0.20    0.10     0.00    0.05  0.05
V_facile        0.10    0.30   0.35   0.50    0.45     0.10    0.05  0.00
T_long          0.05    0.15   0.20   1.00    0.70     0.25    0.10  0.00
T_glyco_bas     0.00    0.05   0.05   0.35    1.00     0.00    0.00  0.00
D+              0.15    0.20   0.30   0.15    0.05     0.10    1.00  0.10
D−_agressif     0.00    0.00   0.15   0.10    0.00     1.00    0.00  0.00
T_sprint        0.20    0.05   0.40   0.00    0.00     0.05    0.20  1.00
Renfo           0.00    0.00   0.45   0.05    0.00     0.55    0.60  0.20
```

C'est **le fichier de game design le plus important du jeu**. Il encode la
spécificité de l'entraînement, donc tous les arbitrages du joueur. Il doit être
en data, éditable, et testé par simulation (§10.3).

### 3.4 Saturation et lissage du stimulus

Deux non-linéarités indispensables, sinon le joueur optimise en empilant :

**(a) Saturation intra-séance** (une séance 2× plus longue ne rapporte pas 2×) :

```
S_séance = S_max_séance · (1 − e^(−s_brut / s_ref))
```
Ex. pour le VO2max : `s_ref ≈ 8 min` de T90, `S_max_séance ≈ 1.4`.
→ 8 min de T90 = 0.88 ; 16 min = 1.24 ; 30 min = 1.38. Rendements décroissants nets.

**(b) Lissage inter-séances** (l'adaptation ne suit pas la séance d'hier) :

```
Ŝ_q(t) = Ŝ_q(t−1) + ( S_q(t) − Ŝ_q(t−1) ) / τ_stim_q      avec τ_stim_q ≈ 7–14 j
```

**(c) Saturation hebdomadaire** : plafond sur `Σ S_q` par semaine. Au-delà, le
surplus n'alimente que la fatigue et les blessures. C'est ce qui crée
la "dose optimale" (ex. 2 séances VO2max/semaine, la 3ᵉ ne sert quasi à rien).

### 3.5 Effet du poids et de la composition corporelle

```
VO2max_relatif = VO2max_absolu / masse
```
Perdre du poids améliore mécaniquement la puissance/poids **mais** :
- déficit énergétique → `R(t)` baisse, risque de blessure osseuse ↑, hormones ↓
- masse grasse trop basse → `res_musc` ↓, immunité ↓, risque RED-S
→ courbe en U avec un optimum individuel. **À manier avec précaution côté design :
prévoir un garde-fou et ne jamais présenter une spirale de restriction comme
une stratégie gagnante.**

---

<a name="4"></a>
## 4. Cas d'école : que fait vraiment un 30-30 ?

C'est ta question centrale. Voici comment je la traiterais.

### 4.1 Le bon proxy : le temps passé > 90 % VO2max (`T90`)

La littérature (Billat, Midgley, Buchheit & Laursen) converge : le déterminant
principal de l'amélioration du VO2max chez un sujet entraîné est le **temps
cumulé passé proche de VO2max**, pas la distance ni le TSS. Donc il faut
**simuler la cinétique de VO2 seconde par seconde** pendant la séance.

### 4.2 Cinétique de VO2 (modèle à 2 composantes)

```
Demande(t)   = VO2_repos + (VO2max − VO2_repos) · (v(t)/vVO2max)     [linéaire, extrapolable > 100 %]

Composante primaire :
  dVO2_p/dt = ( min(Demande, VO2max) − VO2_p ) / τ_p        τ_p ≈ 25–35 s (↓ avec l'entraînement)
  avec un délai cardio-dynamique de ~15–20 s au démarrage

Composante lente (domaine sévère uniquement, > seuil) :
  dVO2_sc/dt = ( A_sc − VO2_sc ) / τ_sc                     τ_sc ≈ 150–200 s
  A_sc ∝ (intensité − seuil), plafonnée

VO2(t) = min( VO2_p + VO2_sc , VO2max )
```

À la récupération, décroissance avec un τ similaire (~30–45 s). **C'est là que se
joue toute la magie du 30-30 : 30 s de récup ne suffisent pas à faire redescendre
VO2, donc les répétitions s'empilent.**

### 4.3 Simulation comparative (à 1 Hz)

Coureur type : VMA 18 km/h, VO2max 60, τ_p = 30 s.

| Séance | Structure | Temps total effort | **T90 estimé** | Fatigue (ATL) | Risque |
|---|---|---|---|---|---|
| A | 20 × (30 s @ 105 % / 30 s @ 50 %) | 10 min | **~8–10 min** | modérée | faible |
| B | 30 × (30/30) | 15 min | ~12–14 min | forte | moyen |
| C | 5 × 3 min @ 95 % / 2 min récup | 15 min | ~9–11 min | forte | moyen |
| D | 4 × 4 min @ 92 % / 3 min récup (Helgerud) | 16 min | ~10–12 min | forte | moyen |
| E | 6 × 1000 m @ 100 % / 2 min | ~20 min | ~11–13 min | très forte | élevé |
| F | continu 12 min @ 92 % | 12 min | ~6–7 min | forte | moyen |
| G | 15 × (15 s @ 115 % / 15 s repos) | 7.5 min | ~5–7 min | faible | faible |
| H | fartlek 10 × 1 min / 1 min @ 100 % | 10 min | ~7–9 min | modérée | faible |

**Lecture de game design** : le 30-30 est *le meilleur ratio T90 / fatigue*.
Il ne bat pas le 5×3′ en stimulus brut, mais il coûte beaucoup moins cher en
ATL et en risque tendineux. Le 15-15 est trop court (VO2 n'a pas le temps de
monter) → excellent en pré-saison ou en reprise, médiocre en bloc VO2max.
Le continu est le pire rapport douleur/T90.

**C'est exactement le genre d'arbitrage qui fait un bon jeu de gestion.**

### 4.4 Du T90 au gain de VO2max

```
S_vo2(séance)  = 1.4 · (1 − e^(−T90_min / 8))
Ŝ_vo2          = EWMA(S_vo2, τ = 10 j)
ΔVO2max/jour   = G_vo2 · Ŝ_vo2 · (1 − VO2/VO2_max_gen)^1.8 · R(t)  −  (VO2 − VO2_base)/τ_perte
```

Calibration cible (`G_vo2` ajusté pour) :
- débutant (VO2 = 40, plafond 58), 2 séances/sem : **+0.6 à +1.0 ml/kg/min par semaine**
  les premières semaines → +12 à +15 en 3–4 mois. Réaliste.
- entraîné (VO2 = 55, plafond 58), 2 séances/sem : **+0.05/sem**, plateau en 6 semaines.
- arrêt total : **−5 à −8 % en 3 semaines, −15 à −20 % en 3 mois**. Cohérent avec
  `τ_perte ≈ 30 j`.

> Astuce design : afficher au joueur une VO2max **estimée bruitée**
> (`VO2_affichée = VO2_vraie · N(1, 0.03)`), sauf après un test labo.

---

<a name="5"></a>
## 5. Fatigue, récupération, forme du jour

### 5.1 Compartiments de fatigue (hors course)

Trois échelles de temps, pas une :

```
F_méta (métabolique/glycogène)   τ ≈ 1–2 j    ← réserve énergétique, foie/muscle
F_musc (dégâts structurels)      τ ≈ 3–7 j    ← surtout excentrique/descente
F_nerv (fatigue centrale/SNC)    τ ≈ 2–10 j   ← intensité, longues distances, sommeil
```

Chacun suit :
```
F(t) = F(t−1)·e^(−1/τ) + contribution_séance
```
Contributions : `F_méta ∝ dépense glucidique`, `F_musc ∝ DSS + volume impact`,
`F_nerv ∝ T90 + T_sprint + durée > 3 h + dette de sommeil`.

`ATL` reste la synthèse affichée, mais **les trois compartiments pilotent
réellement** la forme et le risque. Ça permet des situations riches :
"CTL bon, TSB positif, mais quads encore explosés du 80 km il y a 10 jours".

### 5.2 Forme du jour (readiness)

```
Readiness = clamp( 1 − a·F̂_méta − b·F̂_musc − c·F̂_nerv
                     + d·max(0, TSB/50)
                     + e·(sommeil − 7.5)/2
                     − f·stress_vie
                     + ε ,  0.7 , 1.10 )        avec ε ~ N(0, 0.02)
```

Ce multiplicateur s'applique aux allures tenables du jour. Le `ε` est ce qui
produit les "jours sans" inexplicables — indispensable pour que le joueur ne
puisse pas jouer en tableur.

### 5.3 Affûtage

Le modèle CTL/ATL produit naturellement le bon comportement si on respecte :
réduire le **volume** (−40 à −60 %) en gardant l'**intensité** (T90 maintenu à
~60 %). Concrètement, ATL chute vite (τ=7) pendant que CTL et les qualités `q`
descendent lentement (τ=42+) → pic de perf 8 à 18 jours après le pic de charge.
Trop long → les qualités se dégradent. **Fenêtre optimale à trouver = mini-jeu.**

---

<a name="6"></a>
## 6. Blessures : modèle de hasard par tissu

### 6.1 Modèle global (rapide à implémenter)

Probabilité journalière via un modèle de hasard :

```
λ(t) = λ₀ · exp( β₁·pénalité_ACWR + β₂·(monotonie − 1.5)
                + β₃·(1 − résilience) + β₄·ramp_rate⁺
                + β₅·DSS_normalisée + β₆·(âge − 30)/10
                − β₇·années_de_pratique + β₈·déficit_sommeil )

P(blessure aujourd'hui) = 1 − e^(−λ(t))

avec pénalité_ACWR = max(0, ACWR − 1.3)² + max(0, 0.8 − ACWR)·0.5
```

Ordre de grandeur : viser **~2 à 4 blessures significatives par an** pour un
coureur qui pousse, **~0.5/an** pour un coureur prudent.

### 6.2 Modèle par tissu (recommandé pour la v1)

Bien plus riche en gameplay : le joueur reçoit des **signaux localisés**.

Tissus : `os_tibia`, `os_metatarse`, `tendon_achille`, `tendon_rotulien`,
`quadriceps`, `ischio`, `mollet`, `fascia_plantaire`, `ITB`, `cheville`.

Pour chaque tissu `j` :

```
Dommage_j(t) = Dommage_j(t−1) · (1 − r_j)  +  ( charge_j(t) / C_j )^p_j
```
- `charge_j` : projection de la séance sur ce tissu (matrice tissu × stimulus)
  - `os_*`  ← volume d'impact × vitesse² × surface dure
  - `achille` ← D+, vitesse, drop des chaussures, plyo
  - `rotulien`/`quadriceps` ← DSS (descente)
  - `fascia` ← volume, chaussures usées, minimalisme
- `C_j` : capacité du tissu = f(résilience génétique, historique d'entraînement,
  renfo effectué, âge, antécédents de blessure sur ce tissu)
- `r_j` : taux de réparation journalier (0.05–0.20), **augmenté par le repos,
  réduit par le déficit énergétique et le manque de sommeil**
- `p_j ≈ 1.5–2.5` : non-linéarité (une grosse charge est pire que deux moyennes)

**Adaptation positive** : sous un certain seuil, la charge *augmente* `C_j`
(les tendons et les os se renforcent) :

```
ΔC_j = +g_j · charge_j · 𝟙(Dommage_j < 0.5)  −  h_j · (C_j − C_j_base)
```
→ magnifique dynamique : la progressivité rend *plus* résistant, la précipitation casse.

**États** :

| Dommage_j | État | Effet |
|---|---|---|
| < 0.4 | OK | rien |
| 0.4–0.65 | Gêne (signal au joueur, flou) | −2 % perf, avertissement textuel |
| 0.65–0.85 | Douleur | −8 % perf, tirage P(blessure) chaque séance intense |
| > 0.85 | **Blessure** | arrêt 1–16 sem selon tissu, `C_j` réduit définitivement de 5–15 % |

Le joueur voit `"tension modérée au tendon d'Achille"` — jamais `0.72`.
Un kiné (payant) donne une estimation plus précise.

### 6.3 Maladie / surentraînement

```
λ_maladie ∝ monotonie · strain · déficit_énergétique · (1/sommeil) · stress_vie
```
Syndrome de surentraînement : déclenché si `ATL/CTL > 1.4` pendant > 21 j
avec `R(t) < 0.4` → chute des qualités, `R` bloqué bas pendant 4–12 semaines.
Le vrai game over de l'ambitieux.

---

<a name="7"></a>
## 7. Des qualités à la performance

### 7.1 Vitesse critique et réserve anaérobie (le socle)

Modèle **CS / W′** (équivalent course du CP/W′ cycliste) :

```
t_lim(v) = W′ / ( (v − CS) · C_run(0) )          pour v > CS
```
- `CS` (vitesse critique) ≈ vitesse au SV2 ≈ `frac_seuil · VO2max / eco`
- `W′` ≈ 10–25 kJ/kg-équivalent, c'est **la réserve pour relancer**

Reconstitution de W′ quand `v < CS` (Skiba) :

```
W′_bal(t) = W′ − Σ W′_dépensé · e^(−(t−u)/τ_W′)
τ_W′ = 546 · e^(−0.01·(CS − v)) + 316        [secondes]
```

C'est **exactement le système dont tu as besoin pour le "relancer / économiser"** :
- monter fort = puiser dans W′
- redescendre / plat facile = recharger W′ (lentement)
- W′ à zéro = impossible de relancer, plafond dur sur la vitesse en côte

### 7.2 Décroissance de la performance avec la durée (le cœur de l'ultra)

Le modèle CS/W′ diverge au-delà de ~30 min. Pour l'ultra, on utilise une
décroissance log-linéaire de la fraction de VO2max soutenable (esprit
Péronnet–Thibault), paramétrée par le **trait `endu`** :

```
frac(T) = frac_seuil − endu · ln( T / T_ref )        T_ref = 3600 s
```

Exemple, `frac_seuil = 0.86`, `endu = 0.055` :

| Durée | 30 min | 1 h | 3 h | 6 h | 12 h | 24 h | 40 h |
|---|---|---|---|---|---|---|---|
| % VO2max | 0.90 | 0.86 | 0.80 | 0.76 | 0.72 | 0.68 | 0.65 |

Un `endu` faible (0.08) → 0.60 à 24 h : le coureur "vite mais explose".
Un `endu` élevé (0.035) → 0.74 à 24 h : la diesel qui remonte tout le monde la nuit.
**C'est le trait qui distingue le spécialiste 20 km du finisher UTMB.**

> Riegel (`T₂ = T₁·(D₂/D₁)^1.06`) est un cas particulier de cette famille.
> Pour le trail il faut un exposant de 1.10–1.25 selon le profil — d'où l'intérêt
> de modéliser `endu` explicitement plutôt que de coder un exposant en dur.

### 7.3 Vitesse instantanée sur une pente donnée

```
P_dispo(t) = VO2max · frac_effective(t) · 60/1000 · 20.9 · Readiness · Π(pénalités)
             [W/kg]   ← 1 ml O2 ≈ 20.9 J

v_run  = P_dispo / ( C_run(i)  · eco_facteur )
v_walk = min( P_dispo / ( C_walk(i) · eco_facteur ) , v_walk_max(i, force_cote) )

v_choisie = max(v_run, v_walk)        ← bascule course/marche émergente, pas codée en dur
```

avec `v_walk_max(i)` ≈ `2.0 · (1 − 1.6·i)` m/s pour un coureur moyen, modulé par
`force_cote` et l'usage des bâtons. Ça donne naturellement : on court à plat, on
marche au-delà de ~18–22 % (et un bon marcheur bascule plus tard).

**Plafond en descente** (indépendant du métabolisme) :
```
v_desc_max = v_ref_desc · tech_desc · (1 − technicité_terrain) · f(nuit, pluie, fatigue_musc)
```

### 7.4 Chaîne de pénalités multiplicatives

```
frac_effective = frac(T) · Π pénalités
```

| Pénalité | Formule indicative |
|---|---|
| Glycogène | `1` si G > 40 % ; `0.55 + 0.45·(G/0.40)²` en dessous → **le mur** |
| Déshydratation | `1 − 0.02 · max(0, %perte_masse − 2)` |
| Dégâts musculaires | surtout en descente : `v_desc ×= (1 − 0.5·D_musc)` |
| Hyperthermie | `1 − 0.15·max(0, Tc − 38.5)²` ; > 40 °C = arrêt forcé |
| Altitude | `1 − 0.075 · max(0, (alt − 1200)/1000) · (1 − acclim_alt)` |
| Dette de sommeil | `1 − 0.10·(heures_éveillé − 20)/12` au-delà de 20 h |
| Moral | `0.90 + 0.15·moral` (moral ∈ [0,1]) |
| Charge portée | `1 − 0.012 · masse_sac_kg` (≈ 1.2 %/kg) |

---

<a name="8"></a>
## 8. Simulation de course

### 8.1 Architecture

Découpage du parcours en **segments homogènes de 50–200 m** (pente, technicité,
altitude, exposition). Pas de temps adaptatif : **1 s** en côte décisive et près
d'un rival, **10 s** en croisière. Un 100 miles ≈ 30 000 à 100 000 ticks : trivial
pour un CPU moderne, y compris ×40 concurrents.

État du coureur à chaque tick :
```
{ position, temps, v, G_musc, G_foie, hydratation, Na, D_musc, F_nerv,
  W′_bal, Tc, moral, dette_sommeil, ampoules, état_GI, W′, RPE }
```

### 8.2 Glycogène et énergétique

```
Puissance métabolique  P_met [W/kg] = v · C(i) · eco_facteur
Fraction glucidique    f_CHO = 1 / (1 + e^(−k·(I − I₀)))    I = P_met / P_VO2max
                       (sigmoïde ; I₀ ≈ 0.55 − 0.15·fatmax_normalisé)
Oxydation lipides      ox_lip = min( (1 − f_CHO)·P_met/38 , fatmax )   [g/min, 38 kJ/g]
Oxydation glucides     ox_cho = f_CHO · P_met / 17                     [g/min, 17 kJ/g]

dG/dt = ingestion_absorbée − ox_cho
ingestion_absorbée = min( ingestion_brute , gut/60 · pénalité_intensité · pénalité_chaleur )
```

Réserves de départ : `G_musc ≈ 400–550 g` (↑ avec l'entraînement et la charge en
glucides pré-course), `G_foie ≈ 90–110 g`. Total ≈ 2 000–2 600 kcal.

**Ordre de grandeur qui rend l'ultra intéressant** : un coureur de 65 kg à
600 kcal/h sur 20 h consomme 12 000 kcal. Il n'en stocke que 2 200 et n'en
absorbe que ~350/h. Le reste **doit** venir des lipides → `fatmax` et `endu`
deviennent les vraies stats reines de l'ultra, pas le VO2max. C'est un excellent
message de design.

**Troubles digestifs** :
```
P(GI) ∝ (ingestion_brute − gut/60)⁺ · intensité² · Tc · (1 − trait_estomac) · déshydratation
```
Un épisode GI → `gut` divisé par 2 pendant 30–90 min, nausée, arrêt possible.
Classique et très réaliste sur UTMB.

### 8.3 Hydratation, sodium, thermique

```
sudation [L/h] = 0.4 + 0.9·I + 0.06·(T_air − 15) + 0.4·humidité − 0.15·acclim_chaleur
%perte = (sudation·durée − boisson_absorbée) / masse

Bilan thermique :
dTc/dt = ( P_met·masse·(1 − 0.22)  −  Q_évap − Q_conv − Q_rad ) / (3470 · masse)
Q_évap plafonné par l'humidité et le débit sudoral effectif
```
- `Tc > 39.5` → réduction forcée de l'allure ; `> 40.5` → abandon médical
- `Na` : hyponatrémie si eau bue >> pertes sodées et apport en sel faible →
  confusion, vomissements. Rend le choix "1 L vs 2 L" non trivial dans les deux sens.

### 8.4 Dégâts musculaires (le facteur limitant de l'ultra montagne)

```
dD_musc = k · (D−_segment) · (v_desc / v_ref)^1.6 · (masse_totale/masse_ref)
              · (1 / res_musc) · (1 + 0.4·D_musc)          ← auto-aggravation
          + k₂ · D+_segment · 0.15                          ← concentrique, mineur
```
**Aucune récupération pendant la course.** Effets :
- `v_desc_max ×= (1 − 0.55·D_musc)`
- coût énergétique en montée `+= 0.15·D_musc` (perte d'efficacité)
- douleur → moral ↓, `P(DNF)` ↑
- risque de crampe : `P ∝ D_musc · déficit_Na · intensité_relative`

C'est ce qui explique qu'un routier rapide se fasse dévorer dans les descentes
du deuxième tiers de l'UTMB. Le trait `res_musc` et les blocs de descente
prennent tout leur sens.

### 8.5 Modèle psychologique

Variable `moral ∈ [0, 1]`, dérive lente + chocs :

```
d(moral)/dt = −ρ · (douleur + monotonie_effort + retard_sur_objectif)
              + reprise_vers_baseline

Chocs :
  + 0.06  doubler un concurrent (×2 si c'est un rival identifié)
  − 0.05  être doublé
  + 0.10  ravitaillement avec l'équipe / le public
  + 0.08  sommet atteint, lever du soleil
  + 0.12  passer devant l'objectif de classement
  − 0.12  tomber la nuit sous la pluie, se perdre
  − 0.15  vomir, avoir une grosse ampoule
  − 0.08  chaque heure de nuit (modulé par le trait nuit)
  + 0.05  arriver à un point de repère mentalement fort ("plus que 20 km")
```

Effets du moral :
- module `frac_effective` (§7.4) — le fameux "on va toujours moins vite qu'on croit
  quand on n'y croit plus"
- module le **plafond de RPE accepté** : un moral bas fait que le coureur
  n'exécute pas la consigne "pousse" du joueur
- pilote le **DNF** :
```
λ_DNF ∝ (1 − moral)³ · (1 − mental) · douleur · 𝟙(retard/barrière) · froid
```

**Boucle vertueuse/vicieuse** : relancer pour doubler coûte du W′ et du glycogène,
mais rapporte du moral, qui redonne de la vitesse. Si tu relances et que tu te
fais reprendre 5 min plus tard, tu perds sur les deux tableaux. **Voilà le
mini-jeu tactique.**

### 8.6 Obéissance à la consigne

Le joueur demande un effort `E_cible`. Le coureur produit :

```
E_réel = E_cible + (E_spontané − E_cible)·(1 − pilotage)  +  bruit
E_spontané = ce que le coureur ferait seul (fonction de moral, douleur, rivaux proches)
```
Un coureur avec un mauvais `pilotage de l'effort` part trop vite quand il est
excité (début de course, rival qui attaque) — source classique d'explosion.

---

<a name="9"></a>
## 9. Matériel & environnement

| Élément | Modélisation |
|---|---|
| **Eau 1 L vs 2 L** | +1 kg = −1.2 % de vitesse ; mais si `hydratation < −3 %` au ravito suivant, pénalité bien pire. Dépend de la température, de l'écart entre ravitos, du débit sudoral. |
| **Bâtons** | En pente > 15 % : `C(i) ×= (1 − 0.06·compétence_bâtons)`, transfert de ~10 % de la charge sur `F_bras` (nouvelle variable, τ propre). Sur le plat/descente : `−0` à `−3 %`. Coût : 200–350 g, mains occupées → prise alimentaire ralentie (+30 % de temps par prise). |
| **Chaussures** | `(amorti, grip, poids, drop, usure)`. Amorti ↓ `dD_musc`, ↑ poids. Grip ↑ `v_desc_max` sur boue/roche. Usure > 600–800 km → amorti dégradé, risque tissulaire ↑. Drop bas → charge Achille ↑, charge rotulienne ↓. |
| **Sac** | Volume ↔ matériel emporté ↔ poids. Contrôle du matériel obligatoire au départ et aléatoirement en course. |
| **Frontale** | Autonomie en heures ; batterie à plat la nuit = `v ×= 0.5` + moral ↓↓. |
| **Veste / couches** | Si `T_ressentie` basse et pas de veste : `Tc ↓`, hypothermie, `P(DNF)` ↑. Si trop couvert par temps chaud : `Q_évap ↓`. |
| **Nuit** | `v ×= (0.82 + 0.15·compétence_nuit)` sur terrain technique ; moral ↓ ; dette de sommeil ↑ ; `P(chute)` ×2.5. |
| **Altitude** | Voir §7.4. Sur UTMB (2 500 m max) l'effet est modeste ; sur un Hardrock-like il devient dominant. |
| **Météo** | Pluie → grip ↓, `Tc` ↓, moral ↓. Chaleur → sudation ↑, `f_CHO` ↑ (on brûle plus de sucre quand il fait chaud, effet réel et méchant). |

---

<a name="10"></a>
## 10. Calibration & tests de sanité

### 10.1 Ordres de grandeur cibles

| Grandeur | Valeur attendue | Vérifie |
|---|---|---|
| VO2max débutant, 3 mois d'entraînement structuré | +12 à +18 % | §4.4 |
| VO2max coureur entraîné, 1 an | +2 à +5 % | saturation `q_max` |
| Désentraînement 4 semaines | −7 à −10 % VO2max, −25 % CTL | `τ_perte` |
| Économie de course, 3 ans de pratique | −5 à −8 % de coût | `τ_gain` de `eco` |
| Marathon d'un coureur VMA 18, `frac_seuil` 0.85 | ~2 h 45–2 h 55 | §7.2 |
| UTMB (171 km / 10 000 m D+) top 10 | 21–23 h | §7–8 complet |
| UTMB finisher moyen | 38–44 h | idem |
| Taux d'abandon UTMB | 35–50 % | `λ_DNF` |
| Consommation glucidique en ultra | 250–350 g/h ingérés max chez les meilleurs | §8.2 |
| Blessures/an d'un coureur qui pousse | 2–4 significatives | §6 |

### 10.2 Tests de sanité automatisés (à écrire en premier !)

Un harnais de tests qui fait tourner des carrières simulées et vérifie :

1. **Monotonie de la spécificité** : un bloc VMA améliore plus `VO2max` qu'un bloc
   de sorties longues ; l'inverse pour `endu`.
2. **Plateau** : 5 ans du même plan → progression asymptotique, pas linéaire.
3. **Surcharge** : +30 % de volume par semaine pendant 6 semaines → blessure ou
   surentraînement dans > 70 % des runs.
4. **Affûtage** : perf maximale sur une fenêtre de 8–18 j après le pic de charge.
5. **Non-dominance des stratégies** : aucun plan d'entraînement unique ne doit être
   optimal pour toutes les distances **et** tous les profils génétiques.
   → tourner un optimiseur simple (recuit simulé) sur le plan d'entraînement ;
   s'il trouve une stratégie qui gagne partout, le modèle est cassé.
6. **Réalisme des chronos** : rejouer des courses réelles avec des profils calibrés.

### 10.3 Stratégie d'implémentation recommandée

```
Étape 1 : moteur de course "à froid"  (§7, §8) avec des qualités FIXES
          → valide qu'un coureur donné produit un chrono UTMB plausible
Étape 2 : simulateur de séance (§2, §4) avec cinétique de VO2
          → valide les T90 du tableau §4.3
Étape 3 : modèle d'évolution (§3) + fatigue (§5)
          → valide les progressions du §10.1
Étape 4 : blessures (§6)
Étape 5 : IA concurrents (même modèle, stratégies différentes)
Étape 6 : couches méta (sponsors, vie perso)
```

**Ne jamais coder l'étape N+1 avant que les tests de sanité de l'étape N passent.**
C'est le seul moyen d'éviter un modèle où les paramètres se compensent
mutuellement et deviennent impossibles à équilibrer.

### 10.4 Sources à creuser pour la calibration

- Coût énergétique de la locomotion en pente : Minetti et al. (2002)
- Modèle impulse-response : Banister ; implémentation moderne : intervals.icu, Runalyze
- Cinétique de VO2 et intermittent : Billat ; Buchheit & Laursen (2013)
- Vitesse critique / W′ : Jones & Vanhatalo ; W′ balance : Skiba
- Durabilité / décroissance : Péronnet & Thibault ; travaux récents sur la "durability"
- Charge et blessure : Gabbett (ACWR) **et** ses critiques (Impellizzeri)
- Ultra spécifiquement : Millet & Millet, travaux du labo de Saint-Étienne sur l'UTMB
  (fatigue neuromusculaire, dégâts musculaires, privation de sommeil)
- Nutrition : Jeukendrup (oxydation exogène glucose/fructose, entraînement de l'intestin)
