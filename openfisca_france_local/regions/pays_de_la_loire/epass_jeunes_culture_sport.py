from openfisca_france.model.base import *
from numpy.core.defchararray import startswith


code_departements = [b'44', b'49', b'53', b'72', b'85']


class pays_de_la_loire_epass_jeunes_culture_sport(Variable):
    value_type = float
    entity = Individu
    definition_period = MONTH
    label = u"E.pass Culture Sport de la région Pays de la Loire"
    reference = [
        "https://www.epassjeunes-paysdelaloire.fr/cest-quoi/"
    ]

    def formula(individu, period):
        age = individu('age', period)
        activite = individu('activite', period)
        depcom = individu.menage('depcom', period)

        eligibilite_geographique = sum([startswith(depcom, code) for code in code_departements]) > 0

        etudiant_eligible = (activite == TypesActivite.etudiant)
        autre_eligible = (age >= 15) * (age <= 19) * (activite != TypesActivite.etudiant)

        eligible = eligibilite_geographique * (etudiant_eligible + autre_eligible)
        return 200 * eligible
