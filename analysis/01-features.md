# Trail Manager — Document de features (v0.1, base de discussion)

> Pitch : **F1 Manager × Ultra Destin**. Tu prends un traileur lambda avec des stats
> semi-aléatoires et tu essaies, saison après saison, de l'amener le plus loin possible :
> premier 50 km, qualification UTMB, top 100, top 10, podium… avant que l'âge, les
> blessures ou la vie ne te rattrapent.

Statut de chaque feature : `[CORE]` = indispensable au prototype, `[V1]` = version
jouable complète, `[LATER]` = post-lancement / nice-to-have.

---

## 1. Boucle de jeu

```
Création du coureur
      ↓
┌─→ Planification (calendrier annuel : objectifs, courses, blocs d'entraînement)
│         ↓
│   Simulation d'entraînement (jour / semaine / jusqu'au prochain évènement)
│         ↓         ↖ blessures, vie perso, sponsors, tests physio
│   Préparation de course (affûtage, matériel, stratégie, nutrition)
│         ↓
│   COURSE EN LIVE (le moment "spectacle")
│         ↓
└─── Bilan : résultat, points ITRA, argent, réputation, progression, usure
      ↓
Fin de saison → vieillissement, renouvellement sponsors, nouveaux objectifs
```

Deux temporalités très différentes, et c'est voulu :
- **Entraînement = gestion asynchrone**, on avale des semaines, on regarde des courbes.
- **Course = temps réel accéléré**, on prend des décisions, on transpire.

---

## 2. Création & progression du coureur

### 2.1 Création `[CORE]`
- **Origine** (donne un profil de départ + traits) : ex-footballeur, marathonien
  routier, randonneur/alpiniste, cycliste reconverti, ancien nageur, débutant total
  à 35 ans, jeune espoir cross-country.
- **Morphologie** : taille, poids, %MG → impacte puissance/poids, économie,
  tolérance chaleur, dissipation thermique, résistance musculaire en descente.
- **Âge de départ** (18–45) : jeune = potentiel long mais faible base d'endurance ;
  vieux = base solide, fenêtre courte.
- **Plafonds génétiques cachés** : VO2max max, économie max, endurance max,
  résilience musculaire max, capacité digestive max. Le joueur ne les connaît **pas**,
  il les devine en voyant les gains ralentir. C'est le cœur du replay value.
- **Traits / perks** (2–3 au départ, positifs et négatifs) :
  - `Descendeur né`, `Grimpeur`, `Estomac en béton`, `Petit dormeur`,
    `Résistant au froid`, `Mental d'acier`, `Récupère vite`
  - `Genoux fragiles`, `Sujet aux ampoules`, `Estomac capricieux`,
    `Craint la chaleur`, `Anxieux (mauvais départs)`, `Nyctalope inversé (peur du noir)`
- **Contexte de vie** : job (heures/semaine dispo), famille, ville (accès montagne
  ou pas → contrainte sur le D+ disponible à l'entraînement), argent de départ.

### 2.2 Attributs du coureur `[CORE]`
Séparés en **physio** (moteur du modèle math) et **compétences** (modificateurs).

**Physiologiques** (voir doc 2 pour la modélisation)
| Attribut | Description | Vitesse d'évolution |
|---|---|---|
| VO2max / VMA | Cylindrée aérobie | Rapide (semaines) |
| Seuil (% VO2max au SV2) | Fraction utilisable | Moyenne (mois) |
| Économie de course | Coût énergétique J/kg/m | Lente (années) |
| Endurance / durabilité | Décroissance de la perf avec la durée | Lente |
| Résilience musculaire | Tolérance à l'excentrique (descente) | Moyenne |
| Capacité digestive | g de glucides/h absorbables | Moyenne, entraînable |
| Flexibilité métabolique | Oxydation lipidique max | Moyenne |
| Force / puissance en côte | Marche rapide, relances | Moyenne |
| Capacité anaérobie (W′) | Réserve pour les relances | Rapide |

**Compétences / mental**
| Attribut | Effet |
|---|---|
| Technicité descente | Vitesse max sur terrain cassant, risque de chute |
| Pilotage de l'effort | Écart entre l'allure demandée et l'allure tenue |
| Mental / résistance à la douleur | Plafond de RPE acceptable, résistance au DNF |
| Gestion du sommeil | Pénalité sur courses > 24 h |
| Navigation | Risque de hors-piste la nuit / brouillard |
| Acclimatation chaleur / altitude | Variables d'état à part (voir doc 2) |
| Réputation | Débloque sponsors, dossards élite, invitations |

### 2.3 Carrière long terme `[V1]`
- Courbe d'âge : pic ultra ~30–38 ans ; VO2max décline après ~35 mais économie et
  durabilité peuvent encore monter → arc narratif "je perds de la vitesse mais je
  cours mieux le 100 miles".
- Usure permanente (`mileage` cumulé) : plafonds qui s'érodent, blessures
  chroniques, arthrose.
- Fin de carrière : retraite choisie, ou blessure career-ending (option désactivable).
- **Score de carrière** final + Hall of Fame + comparaison entre parties.

---

## 3. Entraînement

### 3.1 Planification `[CORE]`
- Calendrier annuel (vue année / mois / semaine / jour).
- Bibliothèque de séances : SL, footing, fartlek, 30-30, VMA courte/longue,
  seuil continu, seuil fractionné, côtes courtes/longues, descentes, rando-course,
  sortie longue avec D+, back-to-back week-end, PPG/renfo, plyométrie, vélo, natation,
  home trainer, repos, sortie "sur les chaussures" (recon de parcours).
- **Paramétrage fin d'une séance** : durée, allure cible (% VMA / % seuil), D+/D−,
  terrain, nombre de reps, récup, chargement du sac (entraînement lesté), à jeun ou non.
- **Blocs & templates** `[CORE]` : créer un microcycle type et le répéter N semaines
  avec une progression (+5 % de volume/semaine, etc.). Indispensable pour ne pas
  transformer le jeu en tableur.
- **Assistant coach** `[V1]` : propose un plan auto (plus ou moins bon selon le coach
  payé). Le joueur peut tout accepter, ou micromanager. Curseur d'automatisation.
- **Périodisation** : blocs base / spécifique / affûtage. Le jeu ne l'impose pas mais
  le modèle math récompense ceux qui le respectent.

### 3.2 Simulation `[CORE]`
- Boutons : `Simuler la journée` / `la semaine` / `jusqu'au prochain évènement`.
- Chaque séance produit un **compte-rendu type Strava** : allure, FC, D+,
  charge (TSS), RPE ressenti, sensations textuelles ("jambes lourdes en fin de sortie").
- **Écart entre plan et réalisé** : jour sans, météo pourrie, imprévu boulot →
  la séance peut être ratée, écourtée, ou au contraire "jour de grâce".
- Signaux faibles de blessure : "légère gêne au tendon d'Achille" avant la vraie
  blessure → le joueur doit choisir : lever le pied ou pousser.

### 3.3 Feedback & mesure `[V1]`
Principe fort : **le joueur ne voit jamais les vraies valeurs internes.** Il voit
des *proxys bruités*, comme un vrai coureur.
- Dashboard type intervals.icu : CTL / ATL / TSB, courbe de charge, monotonie,
  répartition par zones, D+ cumulé, VO2max estimée (bruitée), courbe de puissance/allure.
- **Tests** pour réduire l'incertitude, contre argent/temps/fatigue :
  - test de terrain (VMA, demi-Cooper) → gratuit, imprécis
  - test labo VO2max + seuils → cher, précis
  - test de lactate, DEXA, analyse de foulée, test de sudation
- Journal du coureur : humeur, sommeil, motivation, douleurs.

---

## 4. Courses

### 4.1 Calendrier & structure de la saison `[CORE]`
- Catégories : route (10 km, semi, marathon), trail court (< 42 km),
  trail long (50–80 km), ultra (100 km), 100 miles, multi-jours `[LATER]`,
  km vertical, backyard ultra `[LATER]`.
- **Systèmes de qualification réels-inspirés** :
  - Points ITRA / indice de performance → seuils d'inscription
  - Running Stones / loterie UTMB → tension narrative énorme
    ("2 ans que je tente le tirage")
  - Séries : Golden Trail (trail court), UTMB World Series, championnats nationaux,
    sélection en équipe nationale `[V1]`
- Contraintes : coût d'inscription, voyage, jours de congés, décalage horaire,
  altitude d'arrivée → arbitrages économiques et physiologiques.

### 4.2 Préparation d'une course `[CORE]`
- Reconnaissance du parcours (coûte du temps, donne un bonus de pacing/navigation).
- **Affûtage** : le joueur choisit la durée/profondeur ; le modèle récompense.
- **Plan de course** : allure cible par section, temps aux ravitos, objectifs
  intermédiaires, plan nutrition (g de glucides/h, sel, eau).
- **Matériel** :
  - Chaussures : drop, amorti, grip, poids, usure → chaque paire a un kilométrage
  - Bâtons : oui/non, poids, gain en côte vs fatigue haut du corps, encombrement
    (ralentit la prise alimentaire)
  - Poche à eau 1 L vs 2 L vs flasques : poids porté vs risque de déshydratation
    entre deux ravitos
  - Sac, veste imper, frontale (autonomie batterie !), guêtres, crampons
  - **Matériel obligatoire** contrôlé au départ / en course → pénalité ou DSQ
- Drop bags : contenu à préparer par ravito.
- Assistance : équipe (coût), pacer sur la 2e moitié `[V1]`.

### 4.3 La course en live `[CORE — pièce maîtresse]`
Interface :
- Profil altimétrique déroulant + curseur de position, carte optionnelle
- Barres d'état : énergie (glycogène), hydratation, dégâts musculaires,
  fatigue nerveuse, moral, température corporelle, W′
- Classement live, écarts avec les rivaux, position vs objectif
- Météo dynamique, jour/nuit, altitude
- Chrono vs barrières horaires (le stress ultime en ultra)

Actions du joueur :
- **Curseur d'effort** (5–7 crans : "je me traîne" → "je me tue") réglable
  globalement ou par type de section (montée / plat / descente / technique)
- **Relancer** ponctuellement (consomme W′ + moral) pour doubler, décrocher,
  passer un ravito avant la meute
- **Économiser** : marcher les côtes, laisser filer
- Ravitos : durée d'arrêt, quoi manger/boire, changer de chaussures, prendre la
  frontale, s'asseoir 5 min, dormir 20 min `[V1]`
- Nutrition en course : gel / barre / soupe / coca, sel, eau — chaque prise a un
  coût de temps, un apport glucidique et un risque digestif
- Décisions ponctuelles : prendre les bâtons, enlever la veste, suivre un groupe,
  aider un concurrent en détresse (moral +, temps −)
- Évènements : chute, crampe, nausée, coup de moins bien, orage, erreur de balisage,
  seconde jeunesse au lever du soleil

Rythme : vitesse ×1 / ×20 / ×200, avec **pauses automatiques** aux ravitos, aux
changements de section, et quand un évènement survient. Une 100 miles doit se
jouer en 20–40 min.

### 4.4 Concurrents IA `[V1]`
- Chaque rival a **le même modèle physiologique** que le joueur (pas de triche),
  ses propres stats, sa propre stratégie (partant vite, diesel, spécialiste descente).
- Ils progressent aussi entre les saisons, se blessent, prennent leur retraite.
- Rivalités persistantes : un adversaire qui te bat trois fois devient "ta bête noire",
  le doubler donne un gros bonus de moral.
- Générateur de coureurs par nationalité + quelques "légendes" fictives.

---

## 5. Méta-gestion

### 5.1 Sponsors & argent `[V1]`
- Types : marque de chaussures, nutrition, textile, sac, montre, sponsor local,
  employeur arrangeant.
- Chaque contrat = revenu (fixe + primes) + **contraintes** :
  obligation de porter la marque, de courir telle course, d'utiliser telle nutrition
  (donc telle capacité digestive !), quota de posts réseaux, objectif de résultat.
- Négociation en fin de saison selon réputation et résultats.
- Dépenses : inscriptions, voyages, coach, kiné, ostéo, préparateur mental,
  diététicien, tente hypoxique, stage en altitude, matériel, garde d'enfants.
- Arc de carrière : amateur (job à temps plein, 8 h/semaine dispo) → semi-pro →
  pro (temps illimité mais pression de résultats).

### 5.2 Vie personnelle `[V1]`
- Budget temps hebdomadaire = ressource rare. Boulot + famille + entraînement.
- Jauge "conjoint / famille" : trop d'entraînement → conflits, malus moral, voire
  game over social.
- Évènements de vie : déménagement (accès montagne différent), naissance,
  changement de job, blessure d'un proche.
- Sommeil et stress alimentent directement le modèle de récupération.

### 5.3 Blessures & santé `[CORE]`
- Modèle par tissu : os (fracture de fatigue), tendon (Achille, rotulien),
  muscle (quadriceps, ischio), fascia plantaire, ITB, cheville.
- États : `OK → gêne → blessure légère (1–3 sem) → sévère (6–16 sem) → chronique`.
- Décisions : consulter (coût), s'arrêter, cross-training, infiltration
  ("je cours l'UTMB quand même" → risque).
- Maladies : surentraînement, anémie, RED-S/déficit énergétique, infections
  (favorisées par la monotonie et le stress).

---

## 6. Contenu & systèmes transverses

- **Parcours** `[CORE]` : définis en JSON/GPX (profil, technicité, exposition,
  ravitos, barrières). Une dizaine au proto, puis import GPX communautaire `[LATER]`.
- **Météo & saisons** : température, humidité, vent, pluie, neige, orage.
  Impacte la course et l'entraînement.
- **Nuit** : vitesse réduite, moral, dette de sommeil, hallucinations `[V1]`.
- **Altitude** : perte de VO2max en course, acclimatation entraînable.
- **Modes de jeu** `[V1]` : Carrière, Défi (une course, un coureur donné, un objectif),
  Scénario ("recréer une course légendaire"), Bac à sable.
- **Difficulté** : réalisme des blessures, permadeath carrière, brouillard
  d'information (voir/ne pas voir les vraies stats), agressivité de l'IA.
- **Moddabilité** `[LATER]` : courses, coureurs, séances, équipement en fichiers data.
- **Mode Manager d'équipe** `[LATER]` : gérer 3–5 athlètes → la vraie couche "F1 Manager".

---

## 7. Ce qui fera (ou non) la qualité du jeu

1. **La lisibilité du modèle.** Le joueur doit pouvoir se dire "j'ai fait trop de
   séances dures et pas assez de volume, c'est pour ça que j'ai explosé au km 70".
   Si c'est une boîte noire, c'est frustrant ; si c'est trop transparent, c'est un
   tableur à optimiser. → **incertitude bruitée + retours narratifs**.
2. **La course doit être tendue.** Barrières horaires, rivaux, coups de moins bien,
   décisions irréversibles (j'ai laissé la veste au drop bag).
3. **L'arbitrage temps/argent/risque** doit être permanent. Il ne doit jamais exister
   de plan optimal universel.
4. **La progression doit ralentir.** Le plaisir vient du plateau qu'on essaie de casser.
5. **Éviter le micro-management infini** : templates de blocs, coach auto, simulation
   rapide.

---

## 8. Périmètre proposé pour un prototype jouable

- 1 coureur, 3 parcours (trail 30 km, 80 km, 100 miles type UTMB)
- Modèle d'entraînement multi-qualités (doc 2, §2–4) + fatigue + blessures simplifiées
- Calendrier sur 2 saisons, 12 types de séances, templates de blocs
- Simulation de course complète avec glycogène / hydratation / dégâts musculaires /
  W′ / moral, curseur d'effort, ravitos, bâtons, choix d'eau
- 40 concurrents IA
- Pas de sponsors, pas de vie perso, pas d'équipement détaillé au début

---

## 9. Décisions tranchées

- **Joueur = le coureur, contrôlé depuis l'extérieur.** Pas un coach séparé avec
  jauge de confiance : le joueur incarne l'athlète, mais les actions passent par des
  directives ponctuelles données de l'extérieur ("là j'accélère", "je prends mes
  bâtons", "j'économise dans la descente"). Pas de micro-pilotage bio-mécanique,
  juste des décisions à la F1 Manager.
- **Unité de simulation : segments de 100 m** (fatigue, glycogène, etc.), mais
  **pas de réglage par segment**. Le joueur choisit un mode d'effort (ou une action
  du type relance/économie) qui reste actif et se ré-applique automatiquement
  segment après segment jusqu'à ce qu'il le change explicitement — comme le bouton
  "mode dépassement" de F1 Manager. Voir doc 2, §5.1 pour le détail du modèle par
  segment.
- **Concurrents IA reportés.** Pour le prototype, seul le coureur du joueur est
  simulé finement. Le classement final des autres coureurs est généré "random"
  (distribution plausible, pas de simulation physio). La simulation complète des
  rivaux (modèle physio partagé, stratégies, rivalités) viendra dans une itération
  ultérieure — cf. §4.4, à revoir comme `[LATER]` plutôt que `[V1]` pour le proto.
- **Carte 2D stylisée avec effet altimétrique**, si simple à faire : idéalement une
  vraie "carte/GPX" générée par génération procédurale de géographie aléatoire
  plutôt qu'un simple profil de courbe. À prototyper rapidement ; si la génération
  procédurale s'avère complexe, on retombe sur le profil altimétrique animé en
  fallback.
- **Stack technique** : moteur de simulation en **Python**, UI en **Angular ou
  React** (à trancher plus tard selon préférences front). Si la performance de la
  simulation (notamment à vitesse ×200 ou avec beaucoup de concurrents simulés plus
  tard) devient un problème, on envisagera de réécrire le moteur en **Rust**
  (exposé via binding ou service), mais l'API elle-même resterait en Python.
