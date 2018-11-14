# -*- coding: utf-8 -*-
from openfisca_core.simulations import Simulation
import openfisca_france

import sys

periode = '2018-11'
periode_1 = '2018-10'
periodes = [periode]
calculs = {
    'acs_plafond': periodes,
    'acs': periodes,
    'cmu_base_ressources': periodes,
#    'cmu_c': periodes,
}

import csv

paths = [
    'cmu', 'coc', 'res'
]

class StripperReader(object):
    def __init__(self, reader):
        super(StripperReader, self).__init__()
        self.reader = reader

    def op(self, row):
        row = { fieldname.strip(): row[fieldname].strip() for fieldname in self.reader.fieldnames }
        return row

    def __iter__(self):
        self.reader.__iter__()
        return self

    def next(self):
        return self.op(self.reader.next())


def getPath(key):
    return sys.argv[-1].format(key)

situations = {
  'individus': {},
  'familles': {},
  'foyers_fiscaux': {},
  'menages': {},
}

ressourceMapping = {
#    'MNTSAL_RES': 'salaire traitement',
#    'MNTBOU_RES': '',
#    'MNTCHO_RES': 'chomage',
    'MNTPER_RES': 'pensions_alimentaires_percues',
    'MNTRET_RES': 'retraite_nette',
}

def main():
    ids = []
    n_limit = 100
    with open(getPath('cmu')) as csvfile:
        reader = StripperReader(csv.DictReader(csvfile, delimiter=';'))
        n = 0
        for row in reader:
            MATRICUL = row['ASSMAC_CMU'] + '_' + row['DATDEM_C']
            if len(ids) and MATRICUL not in ids:
                continue

            n = n + 1
            if n == n_limit:
                break
            situations['familles'][MATRICUL] = {
                'acs': {
                    periode_1: row['ACSM'] if row['C'] == 'B' else 0
                },
                'acs_plafond': {
                    periode_1: row['ACSPLA_CMU']
                },
                'cmu_c': {
                    periode_1: row['C'] == 'A'
                },
                'rsa': {
                    periode: 0
                },
                'parents': [],
                'enfants': []
            }
            situations['foyers_fiscaux'][MATRICUL] = {
                'declarants': [],
                'personnes_a_charge': []
            }
            situations['menages'][MATRICUL] = {
                'personne_de_reference': [],
                'conjoint': [],
                'enfants': []
            }

    with open(getPath('coc')) as csvfile:
        reader = StripperReader(csv.DictReader(csvfile, delimiter=';'))
        n = 0
        for row in reader:
            GROUP = '_'.join([row['ASSMAC_COC'], row['DATDEM_C']])
            MATRICUL = '_'.join([GROUP, row['NAIDSI_COC'], row['B']])
            NAIDSI = row['NAIDSI_COC']
            if GROUP not in situations['familles']:
                continue

            situations['individus'][MATRICUL] = {
                'date_naissance': {
                    periode: '{0}-{1}-{2}'.format(NAIDSI[0:4], NAIDSI[4:6], NAIDSI[6:])
                }
            }

            if len(situations['familles'][GROUP]['parents']) == 0:
                situations['familles'][GROUP]['parents'].append(MATRICUL)
                situations['foyers_fiscaux'][GROUP]['declarants'].append(MATRICUL)
                situations['menages'][GROUP]['personne_de_reference'].append(MATRICUL)
            elif len(situations['familles'][GROUP]['parents']) == 1:
                situations['familles'][GROUP]['parents'].append(MATRICUL)
                situations['foyers_fiscaux'][GROUP]['declarants'].append(MATRICUL)
                situations['menages'][GROUP]['conjoint'].append(MATRICUL)
            else:
                situations['familles'][GROUP]['enfants'].append(MATRICUL)
                situations['foyers_fiscaux'][GROUP]['personnes_a_charge'].append(MATRICUL)
                situations['menages'][GROUP]['enfants'].append(MATRICUL)

            n = n + 1
    print(n)

    with open(getPath('res')) as csvfile:
        reader = StripperReader(csv.DictReader(csvfile, delimiter=';'))
        n = 0
        for row in reader:
            GROUP = '_'.join([row['ASSMAC_RES'], row['DATDEM_R']])
            MATRICUL = '_'.join([GROUP, row['NAIDSI_RES'], row['B']])
            if MATRICUL not in situations['individus']:
                continue

            individu = situations['individus'][MATRICUL]
            for inputName, outputName in ressourceMapping.iteritems():
                individu[outputName] = {
                    periode_1: row[inputName].replace(',', '.')
                }
            n = n + 1
        print(n)

    from pprint import pprint
    pprint(situations)

    tax_benefit_system = openfisca_france.CountryTaxBenefitSystem()
    simulation_actuelle = Simulation(
        tax_benefit_system=tax_benefit_system,
        simulation_json=situations,
        trace=True)

    for calcul, periodes in calculs.iteritems():
        print(calcul)
        ids = simulation_actuelle.get_variable_entity(calcul).ids
        for periode in periodes:
            valeurs = simulation_actuelle.calculate(calcul, periode)
            sources = simulation_actuelle.calculate(calcul, periode_1)

            resultat = dict(zip(ids, zip(valeurs, sources)))
            for matricul, valeurs in resultat.iteritems():
                calculee, reelle = valeurs
                print (matricul, reelle, calculee)

    if len(ids) == 1:
        simulation_actuelle.tracer.print_computation_log()


if __name__ == '__main__':
    sys.exit(main())