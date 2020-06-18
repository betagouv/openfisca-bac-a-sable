 # -*- coding: utf-8 -*-
from numpy import logical_not as not_

from openfisca_france.model.base import Variable, Individu, MONTH

class eure_et_loir_a_recu_adefip(Variable):
    value_type = bool
    entity = Individu
    definition_period = MONTH
    label = u"A perçu l'AdéFIP dans les 12 derniers mois"


class eure_et_loir_eligibilite_adefip(Variable):
    value_type = bool
    entity = Individu
    definition_period = MONTH
    label = u"Éligibilité à l'AdéFIP"

    def formula(individu, period):
        recoit_rsa = individu.famille('rsa', period) > 0
        reside_eure_et_loir = individu.menage('eure_et_loir_eligibilite_residence', period)
        eure_et_loir_a_recu_adefip = individu('eure_et_loir_a_recu_adefip', period)

        return not_(eure_et_loir_a_recu_adefip) * recoit_rsa * reside_eure_et_loir
