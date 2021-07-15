# -*- coding: utf-8 -*-
from openfisca_france.model.base import *

from numpy.core.defchararray import startswith


class eure_loire_eligibilite_residence(Variable):
    value_type = bool
    entity = Menage
    definition_period = MONTH
    label = u"Éligibilité résidentielle d'un ménage aux dipositifs de l'Eure et Loire"

    def formula(menage, period):
        return startswith(menage('depcom', period), b'28')


class adefip_eligibilite_activite(Variable):
    value_type = bool
    entity = Individu
    definition_period = MONTH
    label = u"Éligibilité en lien avec l'activité de l'individu"

    def formula(individu, period, parameters):
        params_adefip = parameters(period).departements.eure_et_loir.adefip
        duree_activite = individu('duree_contrat_ou_formation', period)

        contrat_de_travail_duree = individu('contrat_de_travail_duree', period)
        TypesContratDeTravailDuree = contrat_de_travail_duree.possible_values

        # cas formation
        formation = individu('formation', period)
        condition_formation = formation * (duree_activite >= params_adefip.durees.duree_minimum_formation)

        # cas CDD
        condition_duree_cdd = duree_activite >= params_adefip.durees.duree_minimum_cdd_palier1
        condition_cdd = not_(condition_formation) * (
                    contrat_de_travail_duree == TypesContratDeTravailDuree.cdd) * condition_duree_cdd

        # cas CDI
        condition_cdi = not_(condition_formation) * (contrat_de_travail_duree == TypesContratDeTravailDuree.cdi)

        return condition_formation + condition_cdd + condition_cdi


class adefip_eligibilite(Variable):
    value_type = bool
    entity = Individu
    definition_period = MONTH

    def formula(individu, period):
        annee_glissante = period.start.period('year').offset(-1)

        # conditions de domiciliation
        residence_eure_loire = individu.menage('eure_loire_eligibilite_residence', period)

        # conditions de RSA
        percoit_rsa = individu.famille('rsa', period)

        # conditions de AdéFIP
        adefip_12_derniers_mois = individu('adefip', annee_glissante, options=[ADD])
        ne_percoit_pas_adefip_12_derniers_mois = (adefip_12_derniers_mois == 0)

        # conditions de CER et PPAE
        avoir_cer_ppae = individu('cer_ou_ppae', period)

        # conditions d'emplois/entreprise
        condition_activite = individu('adefip_eligibilite_activite', period);
        condition_entreprise = not_(condition_activite) * individu('creation_ou_reprise_entreprise', period)

        return residence_eure_loire * percoit_rsa * ne_percoit_pas_adefip_12_derniers_mois * avoir_cer_ppae * (
                    condition_activite + condition_entreprise)


class adefip_montant(Variable):
    value_type = float
    entity = Individu
    definition_period = MONTH

    def formula(individu, period, parameters):
        params_adefip = parameters(period).departements.eure_et_loir.adefip

        duree_activite = individu('duree_contrat_ou_formation', period)

        contrat_de_travail = individu('contrat_de_travail', period)
        TypesContratDeTravail = contrat_de_travail.possible_values

        contrat_de_travail_duree = individu('contrat_de_travail_duree', period)
        TypesContratDeTravailDuree = contrat_de_travail_duree.possible_values

        # cas formation
        formation = individu('formation', period)
        condition_formation = formation * (
                duree_activite >= params_adefip.durees.duree_minimum_formation)
        montant_formation = condition_formation * params_adefip.montants.montant_formation_3_mois_ou_plus

        # cas creation ou reprise entreprise
        condition_entreprise = not_(condition_formation) * individu('creation_ou_reprise_entreprise', period)
        montant_creation_reprise_entreprise = condition_entreprise * params_adefip.montants.montant_creation_reprise_entreprise

        # cas CDD palier 1 (entre 3 et 6 mois)
        est_en_cdd = contrat_de_travail_duree == TypesContratDeTravailDuree.cdd
        condition_duree_cdd_palier_1_min = (duree_activite >= params_adefip.durees.duree_minimum_cdd_palier1)
        condition_duree_cdd_palier_1_max = (duree_activite <= params_adefip.durees.duree_minimum_cdd_palier2)
        condition_cdd_palier_1 = est_en_cdd * condition_duree_cdd_palier_1_min * condition_duree_cdd_palier_1_max
        montant_cdd_palier_1 = condition_cdd_palier_1 * params_adefip.montants.montant_cdd_3_a_6_mois

        # cas CDD palier 2 (plus de 6 mois)
        condition_duree_cdd_palier_2_min = (duree_activite > params_adefip.durees.duree_minimum_cdd_palier2)
        condition_cdd_palier_2 = est_en_cdd * condition_duree_cdd_palier_2_min
        montant_cdd_palier_2 = condition_cdd_palier_2 * params_adefip.montants.montant_cdd_6_mois_ou_plus

        montant_cdd = (montant_cdd_palier_1 + montant_cdd_palier_2) * not_(condition_formation) * not_(
            condition_entreprise)

        # cas CDI temps plein
        est_en_cdi = contrat_de_travail_duree == TypesContratDeTravailDuree.cdi
        est_a_temps_plein = contrat_de_travail == TypesContratDeTravail.temps_plein
        condition_cdi_temps_plein = est_en_cdi * est_a_temps_plein
        montant_cdi_temps_plein = condition_cdi_temps_plein * params_adefip.montants.montant_cdi_temps_plein

        # cas CDI temps partiel
        est_a_temps_partiel = contrat_de_travail == TypesContratDeTravail.temps_partiel
        condition_cdi_temps_partiel = est_en_cdi * est_a_temps_partiel
        montant_cdi_temps_partiel = condition_cdi_temps_partiel * params_adefip.montants.montant_cdi_temps_partiel

        montant_cdi = (montant_cdi_temps_plein + montant_cdi_temps_partiel) * not_(condition_formation) * not_(
            condition_entreprise)

        montant_adefip = montant_formation + montant_cdd + montant_cdi + montant_creation_reprise_entreprise

        return montant_adefip


class adefip(Variable):
    value_type = int
    entity = Individu
    definition_period = MONTH
    set_input = set_input_divide_by_period

    def formula(individu, period):
        # eligibilite
        eligibilite = individu('adefip_eligibilite', period)

        # montant
        montant = individu('adefip_montant', period)

        return montant * eligibilite