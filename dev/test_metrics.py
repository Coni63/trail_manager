"""
Tests unitaires des formules de metrics.py, une par formule de
analysis/02-modelisation-mathematique.md (§1 et §2).

Lancer : python -m unittest test_metrics.py -v
"""
import unittest

import numpy as np

import metrics as m


class TestCoutEnergetique(unittest.TestCase):
    """§2.1 Minetti : valeurs de la table du doc (pente 0 %)."""

    def test_c_run_plat(self):
        self.assertAlmostEqual(m.c_run(0.0), 3.6, places=6)

    def test_c_walk_plat(self):
        self.assertAlmostEqual(m.c_walk(0.0), 2.5, places=6)

    def test_c_run_vectorise(self):
        # np.polyval doit s'appliquer élément par élément sur un array de pentes.
        pentes = np.array([-0.10, 0.0, 0.10])
        couts = m.c_run(pentes)
        self.assertEqual(couts.shape, pentes.shape)
        self.assertAlmostEqual(couts[1], 3.6, places=6)


class TestMoyenneRoulante(unittest.TestCase):
    def test_serie_constante(self):
        # Moyenne roulante d'une constante = la constante, sur toute la série,
        # y compris pendant la période de "montée en charge" de la fenêtre.
        serie = np.full(50, 7.0)
        roulante = m.moyenne_roulante(serie, fenetre_s=10)
        np.testing.assert_allclose(roulante, 7.0)

    def test_debut_de_serie_tronque(self):
        # Les premiers points sont moyennés sur moins de fenetre_s valeurs :
        # roulante[0] = serie[0], roulante[1] = moyenne(serie[0:2]), etc.
        serie = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        roulante = m.moyenne_roulante(serie, fenetre_s=3)
        attendu = np.array([1.0, 1.5, 2.0, 3.0, 4.0])
        np.testing.assert_allclose(roulante, attendu)

    def test_fenetre_pleine(self):
        serie = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
        roulante = m.moyenne_roulante(serie, fenetre_s=3)
        # roulante[3] = moyenne(2,3,4) = 3 ; roulante[5] = moyenne(4,5,6) = 5
        self.assertAlmostEqual(roulante[3], 3.0)
        self.assertAlmostEqual(roulante[5], 5.0)


class TestGapNgp(unittest.TestCase):
    def test_v_gap_plat_egale_vitesse_reelle(self):
        # Terrain plat : C(i)/C(0) = 1, donc v_GAP = v_réelle, course ou marche.
        vitesses = np.array([10.0, 12.0, 8.0])
        pentes = np.zeros(3)
        is_run = np.array([True, True, False])
        v_gap = m.v_gap(vitesses, pentes, is_run)
        np.testing.assert_allclose(v_gap, vitesses)

    def test_v_gap_montee_plus_couteuse_que_plat(self):
        # En côte, C_run(i) > C_run(0) donc v_GAP > v_réelle à vitesse égale
        # (courir en côte "coûte" l'équivalent d'aller plus vite sur le plat).
        vitesses = np.array([10.0])
        pentes = np.array([0.10])
        is_run = np.array([True])
        v_gap = m.v_gap(vitesses, pentes, is_run)
        self.assertGreater(v_gap[0], vitesses[0])

    def test_ngp_effort_constant_egale_v_gap(self):
        # Sur un effort parfaitement constant, NGP = v_GAP (une constante à la
        # puissance 4 puis racine 4e redonne la même constante).
        v_gap_kmh = np.full(120, 11.5)
        self.assertAlmostEqual(m.ngp(v_gap_kmh, fenetre_s=30), 11.5, places=6)

    def test_ngp_irregulier_superieur_a_la_moyenne(self):
        # L'irrégularité (fractionné) doit donner un NGP strictement supérieur
        # à la moyenne arithmétique brute, à moyenne égale. Blocs de 60 s (plus
        # longs que la fenêtre de lissage de 30 s) pour que le lissage ne gomme
        # pas complètement l'irrégularité (avec une alternance à la période de
        # la fenêtre, la moyenne roulante serait constante et le test trivial).
        v_gap_kmh = np.tile(np.array([16.0] * 60 + [8.0] * 60), 4)
        moyenne_brute = v_gap_kmh.mean()
        self.assertGreater(m.ngp(v_gap_kmh, fenetre_s=30), moyenne_brute)

    def test_intensity_factor(self):
        self.assertAlmostEqual(m.intensity_factor(12.0, 15.0), 0.8)

    def test_rtss_if_1_sur_une_heure(self):
        # IF = 1 (allure = seuil) pendant 1 h -> rTSS = 100 par définition.
        self.assertAlmostEqual(m.rtss(3600, 1.0), 100.0)

    def test_rtss_proportionnel_a_if_carre(self):
        # À durée égale, doubler IF quadruple le rTSS.
        base = m.rtss(3600, 1.0)
        double_if = m.rtss(3600, 2.0)
        self.assertAlmostEqual(double_if, base * 4)


class TestDss(unittest.TestCase):
    def test_dss_nulle_sur_terrain_plat(self):
        vitesses = np.full(100, 12.0)
        pentes = np.zeros(100)
        self.assertEqual(m.dss(vitesses, pentes, v_ref_descente_kmh=12.0, resilience_musc=1.0), 0.0)

    def test_dss_nulle_en_montee(self):
        # Seuls les bins en descente (pente < 0) contribuent au DSS.
        vitesses = np.full(10, 10.0)
        pentes = np.full(10, 0.10)  # montée
        self.assertEqual(m.dss(vitesses, pentes, v_ref_descente_kmh=12.0, resilience_musc=1.0), 0.0)

    def test_dss_calcul_manuel_un_bin(self):
        # 1 bin de 1 s à 12 km/h, pente -20 % :
        # distance = 12/3.6 = 3.3333 m, D- = 3.3333 * 0.20 = 0.66667 m
        # ratio vitesse = (12/12)^1.5 = 1 -> DSS = 0.66667 / 1.0
        vitesses = np.array([12.0])
        pentes = np.array([-0.20])
        attendu = (12.0 / 3.6) * 0.20 * (12.0 / 12.0) ** 1.5 / 1.0
        self.assertAlmostEqual(
            m.dss(vitesses, pentes, v_ref_descente_kmh=12.0, resilience_musc=1.0),
            attendu,
        )

    def test_dss_augmente_si_resilience_baisse(self):
        vitesses = np.array([14.0])
        pentes = np.array([-0.25])
        dss_resilient = m.dss(vitesses, pentes, v_ref_descente_kmh=12.0, resilience_musc=1.0)
        dss_fragile = m.dss(vitesses, pentes, v_ref_descente_kmh=12.0, resilience_musc=0.5)
        self.assertGreater(dss_fragile, dss_resilient)


class TestCtlAtlTsb(unittest.TestCase):
    def test_ctl_suivant_depart_a_froid(self):
        # CTL(0) après une charge X en partant de 0 = X / tau.
        self.assertAlmostEqual(m.ctl_suivant(0.0, 42.0, tau=42), 1.0)

    def test_atl_suivant_depart_a_froid(self):
        self.assertAlmostEqual(m.atl_suivant(0.0, 7.0, tau=7), 1.0)

    def test_ctl_stable_si_charge_egale_ctl(self):
        # Si la charge du jour égale exactement le CTL courant, CTL ne bouge pas.
        self.assertAlmostEqual(m.ctl_suivant(50.0, 50.0), 50.0)

    def test_tsb_forme_avant_la_seance(self):
        self.assertAlmostEqual(m.tsb(ctl_prec=40.0, atl_prec=55.0), -15.0)

    def test_ctl_atl_tsb_serie_une_seule_charge(self):
        CTL, ATL, TSB = m.ctl_atl_tsb_serie(np.array([70.0]))
        self.assertAlmostEqual(CTL[0], 70.0 / 42)
        self.assertAlmostEqual(ATL[0], 70.0 / 7)
        self.assertAlmostEqual(TSB[0], 0.0)  # rien avant J0

    def test_ctl_atl_tsb_serie_repos_fait_decroitre(self):
        # Après une charge suivie de repos, CTL et ATL redescendent vers 0,
        # ATL plus vite (tau plus court) que CTL.
        CTL, ATL, _ = m.ctl_atl_tsb_serie(np.array([100.0, 0.0, 0.0, 0.0]))
        self.assertLess(CTL[3], CTL[0])
        self.assertLess(ATL[3], ATL[0])
        # ATL a un tau plus court : sa décroissance relative doit être plus rapide.
        self.assertLess(ATL[3] / ATL[0], CTL[3] / CTL[0])


class TestMonotonieStrainRampAcwr(unittest.TestCase):
    def test_monotonie_ecart_type_nul(self):
        # Fenêtre constante (y compris tout à zéro) : pas de division par zéro,
        # monotonie forcée à 0.
        self.assertEqual(m.monotonie(np.zeros(7)), 0.0)
        self.assertEqual(m.monotonie(np.full(7, 20.0)), 0.0)

    def test_monotonie_calcul_manuel(self):
        charges = np.array([10.0, 20.0, 30.0])
        attendu = charges.mean() / charges.std()
        self.assertAlmostEqual(m.monotonie(charges), attendu)

    def test_strain_produit_simple(self):
        self.assertAlmostEqual(m.strain(charge_hebdo=300.0, monotonie_val=2.0), 600.0)

    def test_ramp_rate_difference_ctl(self):
        self.assertAlmostEqual(m.ramp_rate(ctl_actuel=15.0, ctl_il_y_a_7j=10.0), 5.0)

    def test_ramp_rate_negatif_en_decharge(self):
        self.assertLess(m.ramp_rate(ctl_actuel=10.0, ctl_il_y_a_7j=15.0), 0.0)

    def test_acwr_ctl_nul(self):
        self.assertEqual(m.acwr(atl_actuel=10.0, ctl_actuel=0.0), 0.0)

    def test_acwr_calcul_simple(self):
        self.assertAlmostEqual(m.acwr(atl_actuel=10.0, ctl_actuel=5.0), 2.0)

    def test_charge_hebdo_serie_tronquee_en_debut(self):
        charges = np.array([10.0, 20.0, 30.0, 40.0])
        # fenêtre 7 j > série entière : chaque jour cumule tout l'historique disponible.
        attendu = np.array([10.0, 30.0, 60.0, 100.0])
        np.testing.assert_allclose(m.charge_hebdo_serie(charges, fenetre_j=7), attendu)

    def test_charge_hebdo_serie_fenetre_pleine(self):
        charges = np.array([10.0, 10.0, 10.0, 10.0, 10.0])
        # fenêtre de 3 : charge_hebdo[4] = charges[2]+charges[3]+charges[4] = 30
        self.assertAlmostEqual(m.charge_hebdo_serie(charges, fenetre_j=3)[4], 30.0)

    def test_monotonie_serie_coherente_avec_version_scalaire(self):
        # La version vectorisée doit reproduire exactement, jour par jour, ce
        # que donne monotonie() appliquée à la même fenêtre glissante.
        rng = np.random.default_rng(0)
        charges = rng.integers(0, 60, size=20).astype(float)
        fenetre_j = 7
        resultat_vectorise = m.monotonie_serie(charges, fenetre_j)
        for j in range(len(charges)):
            debut = max(0, j - fenetre_j + 1)
            attendu = m.monotonie(charges[debut:j + 1])
            self.assertAlmostEqual(resultat_vectorise[j], attendu, places=9)

    def test_strain_serie_coherente_avec_version_scalaire(self):
        charges = np.array([30.0, 0.0, 35.0, 0.0, 40.0, 55.0, 0.0, 35.0])
        fenetre_j = 7
        resultat_vectorise = m.strain_serie(charges, fenetre_j)
        for j in range(len(charges)):
            debut = max(0, j - fenetre_j + 1)
            fenetre = charges[debut:j + 1]
            attendu = m.strain(fenetre.sum(), m.monotonie(fenetre))
            self.assertAlmostEqual(resultat_vectorise[j], attendu, places=9)

    def test_ramp_rate_serie_avant_la_fenetre(self):
        # j < fenetre_j : comparé à CTL(t<0) = 0, comme dans ramp_rate() appelé
        # avec ctl_il_y_a_7j=0.0.
        CTL = np.array([1.0, 2.0, 3.0])
        resultat = m.ramp_rate_serie(CTL, fenetre_j=7)
        np.testing.assert_allclose(resultat, CTL)

    def test_ramp_rate_serie_coherente_avec_version_scalaire(self):
        CTL = np.array([1.0, 2.0, 4.0, 7.0, 11.0, 16.0, 22.0, 29.0, 37.0])
        fenetre_j = 7
        resultat_vectorise = m.ramp_rate_serie(CTL, fenetre_j)
        for j in range(len(CTL)):
            attendu = m.ramp_rate(CTL[j], CTL[j - fenetre_j] if j >= fenetre_j else 0.0)
            self.assertAlmostEqual(resultat_vectorise[j], attendu, places=9)

    def test_acwr_serie_coherente_avec_version_scalaire(self):
        ATL = np.array([0.0, 5.0, 10.0, 15.0])
        CTL = np.array([0.0, 1.0, 2.0, 3.0])
        resultat_vectorise = m.acwr_serie(ATL, CTL)
        for j in range(len(ATL)):
            self.assertAlmostEqual(resultat_vectorise[j], m.acwr(ATL[j], CTL[j]), places=9)

    def test_charges_journalieres_vers_indicateurs_longueurs(self):
        charges = np.array([30, 0, 35, 0, 40, 55, 0, 35], dtype=float)
        resultats = m.charges_journalieres_vers_indicateurs(charges, fenetre_j=7)
        for cle in ("CTL", "ATL", "TSB", "charge_hebdo", "monotonie", "strain", "ramp_rate", "acwr"):
            self.assertEqual(len(resultats[cle]), len(charges))

    def test_charges_journalieres_vers_indicateurs_semaine_reguliere_monotone(self):
        # Charge identique tous les jours -> écart-type nul -> monotonie/strain à 0
        # par convention (cf. test_monotonie_ecart_type_nul), pas une valeur infinie.
        charges = np.full(7, 40.0)
        resultats = m.charges_journalieres_vers_indicateurs(charges, fenetre_j=7)
        self.assertEqual(resultats["monotonie"][-1], 0.0)
        self.assertEqual(resultats["strain"][-1], 0.0)


class TestProbaBlessure(unittest.TestCase):
    def test_penalite_acwr_nulle_en_zone_de_confort(self):
        for acwr_val in (0.8, 1.0, 1.3):
            self.assertEqual(m.penalite_acwr(acwr_val), 0.0)

    def test_penalite_acwr_positive_hors_zone(self):
        self.assertGreater(m.penalite_acwr(1.6), 0.0)
        self.assertGreater(m.penalite_acwr(0.5), 0.0)

    def test_penalite_acwr_vectorisee(self):
        acwr_vals = np.array([0.5, 1.0, 1.6])
        attendu = np.array([m.penalite_acwr(v) for v in acwr_vals])
        np.testing.assert_allclose(m.penalite_acwr(acwr_vals), attendu)

    def test_proba_blessure_dans_lintervalle_0_1(self):
        p = m.proba_blessure_jour(acwr_val=1.6, monotonie_val=3.0, ramp_rate_val=8.0)
        self.assertGreaterEqual(p, 0.0)
        self.assertLessEqual(p, 1.0)

    def test_proba_blessure_augmente_avec_acwr_hors_zone(self):
        base = m.proba_blessure_jour(acwr_val=1.0, monotonie_val=1.5, ramp_rate_val=0.0)
        surcharge = m.proba_blessure_jour(acwr_val=1.8, monotonie_val=1.5, ramp_rate_val=0.0)
        self.assertGreater(surcharge, base)

    def test_proba_blessure_augmente_avec_monotonie(self):
        basse = m.proba_blessure_jour(acwr_val=1.0, monotonie_val=1.0, ramp_rate_val=0.0)
        haute = m.proba_blessure_jour(acwr_val=1.0, monotonie_val=3.5, ramp_rate_val=0.0)
        self.assertGreater(haute, basse)

    def test_proba_blessure_ramp_rate_negatif_pas_protecteur(self):
        # ramp_rate⁺ = max(0, ramp_rate) : une décharge (ramp négatif) ne doit
        # pas faire baisser le risque sous le cas ramp_rate = 0.
        neutre = m.proba_blessure_jour(acwr_val=1.0, monotonie_val=1.5, ramp_rate_val=0.0)
        decharge = m.proba_blessure_jour(acwr_val=1.0, monotonie_val=1.5, ramp_rate_val=-5.0)
        self.assertAlmostEqual(decharge, neutre, places=9)

    def test_proba_blessure_diminue_avec_experience(self):
        novice = m.proba_blessure_jour(acwr_val=1.0, monotonie_val=1.5, ramp_rate_val=0.0,
                                        annees_pratique=0.0)
        experimente = m.proba_blessure_jour(acwr_val=1.0, monotonie_val=1.5, ramp_rate_val=0.0,
                                             annees_pratique=10.0)
        self.assertLess(experimente, novice)

    def test_proba_blessure_augmente_avec_deficit_sommeil(self):
        repose = m.proba_blessure_jour(acwr_val=1.0, monotonie_val=1.5, ramp_rate_val=0.0,
                                        deficit_sommeil=0.0)
        fatigue = m.proba_blessure_jour(acwr_val=1.0, monotonie_val=1.5, ramp_rate_val=0.0,
                                         deficit_sommeil=2.0)
        self.assertGreater(fatigue, repose)

    def test_proba_blessure_serie_coherente_avec_version_scalaire(self):
        acwr_vals = np.array([0.9, 1.2, 1.6, 2.0])
        monotonie_vals = np.array([1.0, 1.5, 2.5, 3.8])
        ramp_vals = np.array([-2.0, 0.0, 4.0, 9.0])
        resultat_vectorise = m.proba_blessure_serie(acwr_vals, monotonie_vals, ramp_vals)
        for j in range(len(acwr_vals)):
            attendu = m.proba_blessure_jour(acwr_vals[j], monotonie_vals[j], ramp_vals[j])
            self.assertAlmostEqual(resultat_vectorise[j], attendu, places=9)


if __name__ == "__main__":
    unittest.main()
