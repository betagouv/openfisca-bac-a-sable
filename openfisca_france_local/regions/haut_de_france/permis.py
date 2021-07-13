from numpy import select
from numpy.core.defchararray import startswith
from openfisca_core.periods import MONTH
from openfisca_core.variables import Variable

from openfisca_france.entities import Individu
from openfisca_france.model.base import TypesActivite, TypesStatutMarital
from openfisca_france.model.prestations.aide_permis_demandeur_emploi import \
    aide_permis_demandeur_emploi_eligibilite_individu
from openfisca_france.model.base import max_
from openfisca_france.model.revenus.activite.salarie import TypesContratDeTravailDuree

class haut_de_france_aide_permis_eligibilite(Variable):
    value_type = bool
    entity = Individu
    label = "Éligibilité financière à l'aide à l’obtention du permis de conduire"
    reference = [
        "https://www.hautsdefrance.fr/aide-au-permis-de-conduire/"
    ]
    definition_period = MONTH

    def formula(individu, period, parameters):
        age = individu('age', period)
        criteres_age = parameters(period).regions.haut_de_france.aide_permis.age
        eligibilite_age = (criteres_age.minimum <= age) * (age <= criteres_age.maximum)

        depcom = individu.menage('depcom', period)
        eligibilite_geographique = sum([depcom == departementCode for departementCode in [b'60', b'59', b'02', b'62', b'80']])

        plafond_ressources = parameters(period).regions.haut_de_france.aide_permis.plafond_ressources
        rfr = individu.foyer_fiscal('rfr', period.this_year)
        nbptr = individu.foyer_fiscal('nbptr', period.last_year)

        statut_marital = individu('statut_marital', period)
        eligibilite_couple = (
            ((statut_marital == TypesStatutMarital.marie) + (statut_marital == TypesStatutMarital.pacse)) *
            plafond_ressources.base_personne_couple >= rfr
        )
        eligibilite_autonome = (
            (statut_marital == TypesStatutMarital.celibataire) *
            plafond_ressources.base_personne_autonome >= max_(0, rfr / nbptr)
        )
        return eligibilite_age * eligibilite_geographique * (eligibilite_autonome + eligibilite_couple)


class haut_de_france_aide_permis(Variable):
    value_type = float
    entity = Individu
    label = "Éligibilité financière à l'aide à l’obtention du permis de conduire"
    reference = [
        "https://www.hautsdefrance.fr/aide-au-permis-de-conduire/"
    ]
    definition_period = MONTH

    def formula(individu, period, parameters):
        eligibilite = individu("haut_de_france_aide_permis_eligibilite", period)
        montant = parameters(period).regions.haut_de_france.aide_permis.montant
        breakpoint()
        return eligibilite * montant