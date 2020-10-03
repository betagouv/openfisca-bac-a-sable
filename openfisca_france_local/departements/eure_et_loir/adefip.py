from openfisca_france.model.base import Variable, Individu, MONTH


class eure_et_loir_eligibilite_adefip(Variable):
    value_type = bool
    entity = Individu
    definition_period = MONTH
    label = u"Éligibilité à l'AdéFIP"

    def formula(individu, period):
        recoit_rsa = individu.famille("rsa", period) > 0
        reside_eure_et_loir = individu.menage(
            "eure_et_loir_eligibilite_residence", period
        )

        return recoit_rsa * reside_eure_et_loir
