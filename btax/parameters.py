import json
import os
import six
import re
import numpy as np
import pickle
import pkg_resources

# import btax
from btax.parametersbase import ParametersBase
from btax.get_taxcalc_rates import get_rates
from btax.calc_z import calc_tax_depr_rates, get_econ_depr
from btax.util import read_from_egg, DEFAULT_START_YEAR, RECORDS_START_YEAR


class Specifications(ParametersBase):
    """
    Inherits ParametersBase. Implements the PolicyBrain API for B-Tax
    """
    DEFAULTS_FILENAME = 'default_parameters.json'

    def __init__(self, test=False, time_path=True, baseline=False,
                 year=2018, call_tc=False, iit_reform={}, data='cps'):
        super(Specifications, self).__init__()

        # reads in default parameter values
        self._vals = self._params_dict_from_json_file()

        self.test = test
        self.baseline = baseline
        self.year = year
        self.iit_reform = iit_reform
        self.data = data

        # put B-Tax version in parameters to save for reference
        self.btax_version = pkg_resources.get_distribution("btax").version

        if call_tc:
            # Find individual income tax rates from Tax-Calculator
            indiv_rates = get_rates(self.baseline, self.year,
                                    self.iit_reform, self.data)
        else:
            # Set indiv rates to some values
            indiv_rates = {'tau_nc': np.array([0.1929392]),
                           'tau_div': np.array([0.1882453]),
                           'tau_int': np.array([0.31239301]),
                           'tau_scg': np.array([0.29068557]),
                           'tau_lcg': np.array([0.18837299]),
                           'tau_td': np.array([0.21860396]),
                           'tau_h': np.array([0.04376291])}
        self.tau_nc = indiv_rates['tau_nc']
        self.tau_div = indiv_rates['tau_div']
        self.tau_int = indiv_rates['tau_int']
        self.tau_scg = indiv_rates['tau_scg']
        self.tau_lcg = indiv_rates['tau_lcg']
        self.tau_xcg = 0.00  # tax rate on capital gains held to death
        self.tau_td = indiv_rates['tau_td']
        self.tau_h = indiv_rates['tau_h']

        # does cheap calculations to find parameter values
        self.initialize()

        self.parameter_warnings = ''
        self.parameter_errors = ''
        self._ignore_errors = False

    def initialize(self):
        """
        ParametersBase reads JSON file and sets attributes to self
        Next call self.compute_default_params for further initialization
        Parameters:
        -----------
        run_micro: boolean that indicates whether to estimate tax funtions
                   from microsim model
        """
        for name, data in self._vals.items():
            intg_val = data.get('integer_value', None)
            bool_val = data.get('boolean_value', None)
            string_val = data.get('string_value', None)
            values = data.get('value', None)
            # choose just value for one year
            data_startyear = data.get('start_year', None)
            try:
                if len(values) > 1:
                    value = values[self.year - data_startyear]
                else:
                    value = values
            except TypeError:
                value = values

            # this if statement is to avoid errors when trying to
            # expand list of all strings
            if string_val:
                # pass
                setattr(self, name, self._expand_array(
                    value, intg_val, bool_val, string_val))
            else:
                # setattr(self, name, self._expand_array(
                #     values, intg_val, bool_val, string_val))
                setattr(self, name, self._expand_array(
                    value, intg_val, bool_val, string_val))

        self.compute_default_params()

    def compute_default_params(self):
        """
        Does cheap calculations to return parameter values
        """
        u_c = self.CIT_rate
        print('corp rate = ', u_c)
        print('PT entity tax = ', self.PT_entity_tax_ind)
        if not self.PT_entity_tax_ind:
            u_nc = self.tau_nc
        else:
            u_nc = self.PT_entity_tax_rate
        self.u_array = np.array([u_c, u_nc])

        sprime_c_td = ((1 / self.Y_td) *
                       np.log(((1 - self.tau_td) *
                               np.exp(self.nominal_interest_rate *
                                      self.Y_td)) + self.tau_td) -
                       self.inflation_rate)
        s_c_d_td = (self.gamma * (self.nominal_interest_rate -
                                  self.inflation_rate) +
                    (1 - self.gamma) * sprime_c_td)
        s_c_d = (self.alpha_c_d_ft * (((1 - self.tau_int) *
                                       self.nominal_interest_rate) -
                                      self.inflation_rate) +
                 self.alpha_c_d_td * s_c_d_td + self.alpha_c_d_nt *
                 (self.nominal_interest_rate - self.inflation_rate))
        s_nc_d_td = s_c_d_td
        s_nc_d = (self.alpha_nc_d_ft * (((1 - self.tau_int) *
                                         self.nominal_interest_rate) -
                                        self.inflation_rate) +
                  self.alpha_nc_d_td * s_nc_d_td + self.alpha_nc_d_nt *
                  (self.nominal_interest_rate - self.inflation_rate))

        g_scg = ((1 / self.Y_scg) * np.log(((1 - self.tau_scg) *
                                            np.exp((self.inflation_rate
                                                    + self.m * self.E_c)
                                                   * self.Y_scg)) +
                                           self.tau_scg) -
                 self.inflation_rate)
        g_lcg = ((1 / self.Y_lcg) * np.log(((1 - self.tau_lcg) *
                                            np.exp((self.inflation_rate
                                                    + self.m * self.E_c)
                                                   * self.Y_lcg)) +
                                           self.tau_lcg) -
                 self.inflation_rate)
        g = (self.omega_scg * g_scg + self.omega_lcg * g_lcg +
             self.omega_xcg * self.m * self.E_c)
        s_c_e_ft = (1 - self.m) * self.E_c * (1 - self.tau_div) + g
        s_c_e_td = ((1 / self.Y_td) *
                    np.log(((1 - self.tau_td) *
                            np.exp((self.inflation_rate + self.E_c) *
                                   self.Y_td)) + self.tau_td) -
                    self.inflation_rate)
        s_c_e = (self.alpha_c_e_ft * s_c_e_ft + self.alpha_c_e_td *
                 s_c_e_td + self.alpha_c_e_nt * self.E_c)

        s_c = self.f_c * s_c_d + (1 - self.f_c) * s_c_e

        E_nc = s_c_e
        E_array = np.array([self.E_c, E_nc])
        s_nc_e = E_nc
        s_nc = self.f_nc * s_nc_d + (1 - self.f_nc) * s_nc_e
        self.s_array = np.squeeze(np.array([[s_c, s_nc], [s_c_d, s_nc_d], [s_c_e, s_nc_e]]))
        f_array = np.array([[self.f_c, self.f_nc], [1, 1], [0, 0]])
        ace_array = np.array([self.ace, self.ace_nc])
        r = np.empty_like(f_array)
        # r = (f_array * (self.nominal_interest_rate *
        #                 (1 - (1 - self.int_haircut) * self.u_array)) +
        #      (1 - f_array) * (E_array + self.inflation_rate - E_array *
        #                       self.r_ace * ace_array))
        r[:, 0] = (f_array[:, 0] * (
            self.nominal_interest_rate *
            (1 - (1 - self.interest_deduct_haircut_corp) *
             self.u_array[0])) + (1 - f_array[:, 0]) *
                   (E_array[0] + self.inflation_rate - E_array[0] *
                    self.ace_int_rate * ace_array[0]))
        r[:, 1] = (f_array[:, 1] * (
            self.nominal_interest_rate *
            (1 - (1 - self.interest_deduct_haircut_PT) *
             self.u_array[1])) + (1 - f_array[:, 1]) *
                   (E_array[1] + self.inflation_rate - E_array[1] *
                    self.ace_int_rate * ace_array[1]))
        r_prime = (f_array * self.nominal_interest_rate + (1 - f_array)
                   * (E_array + self.inflation_rate))

        # if no entity level taxes on pass-throughs, ensure mettr and metr
        # on non-corp entities the same
        if not self.PT_entity_tax_ind:
            r_prime[:, 1] = self.s_array[:, 1] + self.inflation_rate
        # If entity level tax, assume distribute earnings at same rate corps
        # distribute dividends and these are taxed at dividends tax rate
        # (which seems likely).  Also implicitly assumed that if entity
        # level tax, then only additional taxes on pass-through income are
        # capital gains and dividend taxes
        else:
            # keep debt and equity financing ratio the same even though now
            # entity level tax that might now favor debt
            self.s_array[0, 1] = self.f_nc * s_nc_d + (1 - self.f_nc) * s_c_e
            self.s_array[2, 1] = s_c_e
        self.delta = get_econ_depr()
        self.tax_methods = {'DB 200%': 2.0, 'DB 150%': 1.5, 'SL': 1.0,
                            'Economic': 1.0, 'Expensing': 1.0}
        self.financing_list = ['', '_d', '_e']
        self.entity_list = ['_c', '_nc']
        self.r = r
        self.r_prime = r_prime

        # Create dictionaries with depreciation system and rate of bonus
        # depreciation by asset class
        class_list = [3, 5, 7, 10, 15, 20, 25, 27.5, 39]
        class_list_str = [(str(i) if i != 27.5 else '27_5') for i in
                          class_list]
        self.deprec_system = {}
        self.bonus_deprec = {}
        for cl in class_list_str:
            self.deprec_system[cl] = getattr(self,
                                             'DeprecSystem_{}yr'.format(cl))
            self.bonus_deprec[cl] = getattr(self,
                                            'BonusDeprec_{}yr'.format(cl))
        self.bonus_deprec['100'] = 0.0  # to handle land and inventories - fixed later, but should work on this
        tax_methods = {'DB 200%': 2.0, 'DB 150%': 1.5, 'SL': 1.0,
                       'Economic': 1.0, 'Expensing': 1.0}
        self.financing_list = ['', '_d', '_e']
        self.entity_list = ['_c', '_nc']
        self.z = calc_tax_depr_rates(r, self.inflation_rate,
                                     self.delta, self.bonus_deprec,
                                     self.deprec_system,
                                     self.inventory_expensing,
                                     self.land_expensing, tax_methods,
                                     self.financing_list, self.entity_list)

        asset_dict = dict.fromkeys(['Mainframes', 'PCs', 'DASDs',
                                'Printers', 'Terminals', 'Tape drives',
                                'Storage devices', 'System integrators',
                                'Prepackaged software',
                                'Custom software'],
                               'Computers and Software')
        asset_dict.update(dict.fromkeys(['Communications',
                                         'Nonelectro medical instruments',
                                         'Electro medical instruments',
                                         'Nonmedical instruments',
                                         'Photocopy and related equipment',
                                         'Office and accounting equipment'],
                                        'Instruments and Communications Equipment'))
        asset_dict.update(dict.fromkeys(['Household furniture',
                                         'Other furniture',
                                         'Household appliances'],
                                        'Office and Residential Equipment'))
        asset_dict.update(dict.fromkeys(['Light trucks (including utility vehicles)',
                                         'Other trucks, buses and truck trailers',
                                         'Autos', 'Aircraft','Ships and boats',
                                         'Railroad equipment','Steam engines',
                                         'Internal combustion engines'],
                                        'Transportation Equipment'))
        asset_dict.update(dict.fromkeys(['Special industrial machinery',
                                         'General industrial equipment'],
                                        'Industrial Machinery'))
        asset_dict.update(dict.fromkeys(['Nuclear fuel',
                                         'Other fabricated metals',
                                         'Metalworking machinery',
                                         'Electric transmission and distribution',
                                         'Other agricultural machinery',
                                         'Farm tractors',
                                         'Other construction machinery',
                                         'Construction tractors',
                                         'Mining and oilfield machinery'],
                                        'Other Industrial Equipment'))
        asset_dict.update(dict.fromkeys(['Service industry machinery',
                                         'Other electrical', 'Other'],
                                        'Other Equipment'))
        asset_dict.update(dict.fromkeys(['Residential'],
                                        'Residential Buildings'))
        asset_dict.update(dict.fromkeys(['Manufacturing', 'Office',
                                         'Hospitals', 'Special care',
                                         'Medical buildings',
                                         'Multimerchandise shopping',
                                         'Food and beverage establishments',
                                         'Warehouses', 'Other commercial',
                                         'Air transportation',
                                         'Other transportation',
                                         'Religious',
                                         'Educational and vocational',
                                         'Lodging', 'Public safety'],
                                        'Nonresidential Buildings'))
        asset_dict.update(dict.fromkeys(['Gas', 'Petroleum pipelines',
                                         'Communication',
                                         'Petroleum and natural gas',
                                         'Mining'],
                                        'Mining and Drilling Structures'))
        asset_dict.update(dict.fromkeys(['Electric', 'Wind and solar',
                                         'Amusement and recreation',
                                         'Other railroad',
                                         'Track replacement',
                                         'Local transit structures',
                                         'Other land transportation',
                                         'Farm', 'Water supply',
                                         'Sewage and waste disposal',
                                         'Highway and conservation and development',
                                         'Mobile structures'],
                                        'Other Structures'))
        asset_dict.update(dict.fromkeys(['Pharmaceutical and medicine manufacturing',
                                         'Chemical manufacturing, ex. pharma and med',
                                         'Semiconductor and other component manufacturing',
                                         'Computers and peripheral equipment manufacturing',
                                         'Communications equipment manufacturing',
                                         'Navigational and other instruments manufacturing',
                                         'Other computer and electronic manufacturing, n.e.c.',
                                         'Motor vehicles and parts manufacturing',
                                         'Aerospace products and parts manufacturing',
                                         'Other manufacturing',
                                         'Scientific research and development services',
                                         'Software publishers',
                                         'Financial and real estate services',
                                         'Computer systems design and related services',
                                         'All other nonmanufacturing, n.e.c.',
                                         'Private universities and colleges',
                                         'Other nonprofit institutions',
                                         'Theatrical movies',
                                         'Long-lived television programs',
                                         'Books', 'Music',
                                         'Other entertainment originals',
                                         'Own account software'],
                                        'Intellectual Property'))

        # major asset groups
        major_asset_groups = dict.fromkeys(['Mainframes', 'PCs', 'DASDs',
                                            'Printers', 'Terminals',
                                            'Tape drives', 'Storage devices',
                                            'System integrators',
                                            'Prepackaged software',
                                            'Custom software',
                                            'Communications',
                                            'Nonelectro medical instruments',
                                            'Electro medical instruments',
                                            'Nonmedical instruments',
                                            'Photocopy and related equipment',
                                            'Office and accounting equipment',
                                            'Household furniture',
                                            'Other furniture',
                                            'Household appliances',
                                            'Light trucks (including utility vehicles)',
                                            'Other trucks, buses and truck trailers',
                                            'Autos', 'Aircraft',
                                            'Ships and boats',
                                            'Railroad equipment',
                                            'Steam engines',
                                            'Internal combustion engines',
                                            'Special industrial machinery',
                                            'General industrial equipment',
                                            'Nuclear fuel',
                                            'Other fabricated metals',
                                            'Metalworking machinery',
                                            'Electric transmission and distribution',
                                            'Other agricultural machinery',
                                            'Farm tractors',
                                            'Other construction machinery',
                                            'Construction tractors',
                                            'Mining and oilfield machinery',
                                            'Service industry machinery',
                                            'Other electrical', 'Other'],
                                           'Equipment')
        major_asset_groups.update(dict.fromkeys(['Residential',
                                                 'Manufacturing', 'Office',
                                                 'Hospitals', 'Special care',
                                                 'Medical buildings',
                                                 'Multimerchandise shopping',
                                                 'Food and beverage establishments',
                                                 'Warehouses',
                                                 'Other commercial',
                                                 'Air transportation',
                                                 'Other transportation',
                                                 'Religious',
                                                 'Educational and vocational',
                                                 'Lodging', 'Public safety',
                                                 'Gas',
                                                 'Petroleum pipelines',
                                                 'Communication',
                                                 'Petroleum and natural gas',
                                                 'Mining', 'Electric',
                                                 'Wind and solar',
                                                 'Amusement and recreation',
                                                 'Other railroad',
                                                 'Track replacement',
                                                 'Local transit structures',
                                                 'Other land transportation',
                                                 'Farm', 'Water supply',
                                                 'Sewage and waste disposal',
                                                 'Highway and conservation and development',
                                                 'Mobile structures'],
                                                'Structures'))
        major_asset_groups.update(dict.fromkeys(['Pharmaceutical and medicine manufacturing',
                                                 'Chemical manufacturing, ex. pharma and med',
                                                 'Semiconductor and other component manufacturing',
                                                 'Computers and peripheral equipment manufacturing',
                                                 'Communications equipment manufacturing',
                                                 'Navigational and other instruments manufacturing',
                                                 'Other computer and electronic manufacturing, n.e.c.',
                                                 'Motor vehicles and parts manufacturing',
                                                 'Aerospace products and parts manufacturing',
                                                 'Other manufacturing',
                                                 'Scientific research and development services',
                                                 'Software publishers',
                                                 'Financial and real estate services',
                                                 'Computer systems design and related services',
                                                 'All other nonmanufacturing, n.e.c.',
                                                 'Private universities and colleges',
                                                 'Other nonprofit institutions',
                                                 'Theatrical movies',
                                                 'Long-lived television programs',
                                                 'Books', 'Music',
                                                 'Other entertainment originals',
                                                 'Own account software'],
                                                'Intellectual Property'))
        major_asset_groups.update(dict.fromkeys(['Inventories'],
                                                'Inventories'))
        major_asset_groups.update(dict.fromkeys(['Land'], 'Land'))

        # define major industry groupings
        ind_dict = dict.fromkeys(['Farms',
                                  'Forestry, fishing, and related activities'],
                                 'Agriculture, forestry, fishing, and hunting')
        ind_dict.update(dict.fromkeys(['Oil and gas extraction',
                                       'Mining, except oil and gas',
                                       'Support activities for mining'],
                                      'Mining'))
        ind_dict.update(dict.fromkeys(['Utilities'], 'Utilities'))
        ind_dict.update(dict.fromkeys(['Construction'], 'Construction'))
        ind_dict.update(dict.fromkeys(['Wood products',
                                       'Nonmetallic mineral products',
                                       'Primary metals',
                                       'Fabricated metal products',
                                       'Machinery',
                                       'Computer and electronic products',
                                       'Electrical equipment, appliances, and components',
                                       'Motor vehicles, bodies and trailers, and parts',
                                       'Other transportation equipment',
                                       'Furniture and related products',
                                       'Miscellaneous manufacturing',
                                       'Food, beverage, and tobacco products',
                                       'Textile mills and textile products',
                                       'Apparel and leather and allied products',
                                       'Paper products', 'Printing and related support activities',
                                       'Petroleum and coal products',
                                       'Chemical products',
                                       'Plastics and rubber products'],
                                      'Manufacturing'))
        ind_dict.update(dict.fromkeys(['Wholesale trade'], 'Wholesale trade'))
        ind_dict.update(dict.fromkeys(['Retail trade'], 'Retail trade'))
        ind_dict.update(dict.fromkeys(['Air transportation',
                                       'Railroad transportation',
                                       'Water transportation',
                                       'Truck transportation',
                                       'Transit and ground passenger transportation',
                                       'Pipeline transportation',
                                       'Other transportation and support activitis',
                                       'Warehousing and storage'],
                                      'Transportation and warehousing'))
        ind_dict.update(dict.fromkeys(['Publishing industries (including software)',
                                       'Motion picture and sound recording industries',
                                       'Broadcasting and telecommunications',
                                       'Information and telecommunications'],
                                      'Information'))
        ind_dict.update(dict.fromkeys(['Federal Reserve banks',
                                       'Credit intermediation and related activities',
                                       'Securities, commodity contracts, and investments',
                                       'Insurance carriers and related activities',
                                       'Funds, trusts, and other financial vehicles'],
                                      'Finance and insurance'))
        ind_dict.update(dict.fromkeys(['Real estate',
                                       'Rental and leasing services and lessors of intangible assets'],
                                      'Real estate and rental and leasing'))
        ind_dict.update(dict.fromkeys(['Legal services',
                                       'Computer systems design and related services',
                                       'Miscellaneous professional, scientific, and technical services'],
                                      'Professional, scientific, and technical services'))
        ind_dict.update(dict.fromkeys(['Management of companies and enterprises'],
                                      'Management of companies and enterprises'))
        ind_dict.update(dict.fromkeys(['Administrative and support services',
                                       'Waster management and remediation services'],
                                      'Administrative and waste management services'))
        ind_dict.update(dict.fromkeys(['Educational services'],
                                      'Educational services'))
        ind_dict.update(dict.fromkeys(['Ambulatory health care services',
                                       'Hospitals',
                                       'Nursing and residential care facilities',
                                       'Social assistance'],
                                      'Health care and social assistance'))
        ind_dict.update(dict.fromkeys(['Performing arts, spectator sports, museums, and related activities',
                                       'Amusements, gambling, and recreation industries'],
                                      'Arts, entertainment, and recreation'))
        ind_dict.update(dict.fromkeys(['Accomodation',
                                       'Food services and drinking places'],
                                      'Accommodation and food services'))
        ind_dict.update(dict.fromkeys(['Other services, except government'],
                                      'Other services, except government'))

        bea_code_dict = dict.fromkeys(['110C', '113F'],
                                      'Agriculture, forestry, fishing, and hunting')
        bea_code_dict.update(dict.fromkeys(['2110', '2120', '2130'],
                                           'Mining'))
        bea_code_dict.update(dict.fromkeys(['2200'], 'Utilities'))
        bea_code_dict.update(dict.fromkeys(['2300'], 'Construction'))
        bea_code_dict.update(dict.fromkeys(['3210', '3270', '3310', '3320',
                                            '3330', '3340', '3350', '336M',
                                            '336O', '3370', '338A', '311A',
                                            '313T', '315A', '3220', '3230',
                                            '3240', '3250', '3260'],
                                           'Manufacturing'))
        bea_code_dict.update(dict.fromkeys(['4200'], 'Wholesale trade'))
        bea_code_dict.update(dict.fromkeys(['44RT'], 'Retail trade'))
        bea_code_dict.update(dict.fromkeys(['4810', '4820', '4830', '4840',
                                            '4850', '4860', '487S', '4930'],
                                           'Transportation and warehousing'))
        bea_code_dict.update(dict.fromkeys(['5110', '5120', '5130', '5140'],
                                           'Information'))
        bea_code_dict.update(dict.fromkeys(['5210', '5220', '5230', '5240',
                                            '5250'],
                                           'Finance and insurance'))
        bea_code_dict.update(dict.fromkeys(['5310', '5320'],
                                           'Real estate and rental and leasing'))
        bea_code_dict.update(dict.fromkeys(['5411', '5415', '5412'],
                                           'Professional, scientific, and technical services'))
        bea_code_dict.update(dict.fromkeys(['5500'],
                                           'Management of companies and enterprises'))
        bea_code_dict.update(dict.fromkeys(['5610', '5620'],
                                           'Administrative and waste management services'))
        bea_code_dict.update(dict.fromkeys(['6100'],
                                           'Educational services'))
        bea_code_dict.update(dict.fromkeys(['6210', '622H', '6230', '6240'],
                                           'Health care and social assistance'))
        bea_code_dict.update(dict.fromkeys(['711A', '7130'],
                                           'Arts, entertainment, and recreation'))
        bea_code_dict.update(dict.fromkeys(['7210', '7220'],
                                           'Accommodation and food services'))
        bea_code_dict.update(dict.fromkeys(['8100'],
                                           'Other services, except government'))
        asset_dict = dict.fromkeys(['Mainframes', 'PCs', 'DASDs',
                                    'Printers', 'Terminals', 'Tape drives',
                                    'Storage devices', 'System integrators',
                                    'Prepackaged software',
                                    'Custom software'],
                                   'Computers and Software')
        asset_dict.update(dict.fromkeys(['Communications',
                                         'Nonelectro medical instruments',
                                         'Electro medical instruments',
                                         'Nonmedical instruments',
                                         'Photocopy and related equipment',
                                         'Office and accounting equipment'],
                                        'Instruments and Communications Equipment'))
        asset_dict.update(dict.fromkeys(['Household furniture',
                                         'Other furniture',
                                         'Household appliances'],
                                        'Office and Residential Equipment'))
        asset_dict.update(dict.fromkeys(['Light trucks (including utility vehicles)',
                                         'Other trucks, buses and truck trailers',
                                         'Autos', 'Aircraft','Ships and boats',
                                         'Railroad equipment','Steam engines',
                                         'Internal combustion engines'],
                                        'Transportation Equipment'))
        asset_dict.update(dict.fromkeys(['Special industrial machinery',
                                         'General industrial equipment'],
                                        'Industrial Machinery'))
        asset_dict.update(dict.fromkeys(['Nuclear fuel',
                                         'Other fabricated metals',
                                         'Metalworking machinery',
                                         'Electric transmission and distribution',
                                         'Other agricultural machinery',
                                         'Farm tractors',
                                         'Other construction machinery',
                                         'Construction tractors',
                                         'Mining and oilfield machinery'],
                                        'Other Industrial Equipment'))
        asset_dict.update(dict.fromkeys(['Service industry machinery',
                                         'Other electrical', 'Other'],
                                        'Other Equipment'))
        asset_dict.update(dict.fromkeys(['Residential'],
                                        'Residential Buildings'))
        asset_dict.update(dict.fromkeys(['Manufacturing', 'Office',
                                         'Hospitals', 'Special care',
                                         'Medical buildings',
                                         'Multimerchandise shopping',
                                         'Food and beverage establishments',
                                         'Warehouses', 'Other commercial',
                                         'Air transportation',
                                         'Other transportation',
                                         'Religious',
                                         'Educational and vocational',
                                         'Lodging', 'Public safety'],
                                        'Nonresidential Buildings'))
        asset_dict.update(dict.fromkeys(['Gas', 'Petroleum pipelines',
                                         'Communication',
                                         'Petroleum and natural gas',
                                         'Mining'],
                                        'Mining and Drilling Structures'))
        asset_dict.update(dict.fromkeys(['Electric', 'Wind and solar',
                                         'Amusement and recreation',
                                         'Other railroad',
                                         'Track replacement',
                                         'Local transit structures',
                                         'Other land transportation',
                                         'Farm', 'Water supply',
                                         'Sewage and waste disposal',
                                         'Highway and conservation and development',
                                         'Mobile structures'],
                                        'Other Structures'))
        asset_dict.update(dict.fromkeys(['Pharmaceutical and medicine manufacturing',
                                         'Chemical manufacturing, ex. pharma and med',
                                         'Semiconductor and other component manufacturing',
                                         'Computers and peripheral equipment manufacturing',
                                         'Communications equipment manufacturing',
                                         'Navigational and other instruments manufacturing',
                                         'Other computer and electronic manufacturing, n.e.c.',
                                         'Motor vehicles and parts manufacturing',
                                         'Aerospace products and parts manufacturing',
                                         'Other manufacturing',
                                         'Scientific research and development services',
                                         'Software publishers',
                                         'Financial and real estate services',
                                         'Computer systems design and related services',
                                         'All other nonmanufacturing, n.e.c.',
                                         'Private universities and colleges',
                                         'Other nonprofit institutions',
                                         'Theatrical movies',
                                         'Long-lived television programs',
                                         'Books', 'Music',
                                         'Other entertainment originals',
                                         'Own account software'],
                                        'Intellectual Property'))

        # major asset groups
        major_asset_groups = dict.fromkeys(['Mainframes', 'PCs', 'DASDs',
                                            'Printers', 'Terminals',
                                            'Tape drives', 'Storage devices',
                                            'System integrators',
                                            'Prepackaged software',
                                            'Custom software',
                                            'Communications',
                                            'Nonelectro medical instruments',
                                            'Electro medical instruments',
                                            'Nonmedical instruments',
                                            'Photocopy and related equipment',
                                            'Office and accounting equipment',
                                            'Household furniture',
                                            'Other furniture',
                                            'Household appliances',
                                            'Light trucks (including utility vehicles)',
                                            'Other trucks, buses and truck trailers',
                                            'Autos', 'Aircraft',
                                            'Ships and boats',
                                            'Railroad equipment',
                                            'Steam engines',
                                            'Internal combustion engines',
                                            'Special industrial machinery',
                                            'General industrial equipment',
                                            'Nuclear fuel',
                                            'Other fabricated metals',
                                            'Metalworking machinery',
                                            'Electric transmission and distribution',
                                            'Other agricultural machinery',
                                            'Farm tractors',
                                            'Other construction machinery',
                                            'Construction tractors',
                                            'Mining and oilfield machinery',
                                            'Service industry machinery',
                                            'Other electrical', 'Other'],
                                           'Equipment')
        major_asset_groups.update(dict.fromkeys(['Residential',
                                                 'Manufacturing', 'Office',
                                                 'Hospitals', 'Special care',
                                                 'Medical buildings',
                                                 'Multimerchandise shopping',
                                                 'Food and beverage establishments',
                                                 'Warehouses',
                                                 'Other commercial',
                                                 'Air transportation',
                                                 'Other transportation',
                                                 'Religious',
                                                 'Educational and vocational',
                                                 'Lodging', 'Public safety',
                                                 'Gas',
                                                 'Petroleum pipelines',
                                                 'Communication',
                                                 'Petroleum and natural gas',
                                                 'Mining', 'Electric',
                                                 'Wind and solar',
                                                 'Amusement and recreation',
                                                 'Other railroad',
                                                 'Track replacement',
                                                 'Local transit structures',
                                                 'Other land transportation',
                                                 'Farm', 'Water supply',
                                                 'Sewage and waste disposal',
                                                 'Highway and conservation and development',
                                                 'Mobile structures'],
                                                'Structures'))
        major_asset_groups.update(dict.fromkeys(['Pharmaceutical and medicine manufacturing',
                                                 'Chemical manufacturing, ex. pharma and med',
                                                 'Semiconductor and other component manufacturing',
                                                 'Computers and peripheral equipment manufacturing',
                                                 'Communications equipment manufacturing',
                                                 'Navigational and other instruments manufacturing',
                                                 'Other computer and electronic manufacturing, n.e.c.',
                                                 'Motor vehicles and parts manufacturing',
                                                 'Aerospace products and parts manufacturing',
                                                 'Other manufacturing',
                                                 'Scientific research and development services',
                                                 'Software publishers',
                                                 'Financial and real estate services',
                                                 'Computer systems design and related services',
                                                 'All other nonmanufacturing, n.e.c.',
                                                 'Private universities and colleges',
                                                 'Other nonprofit institutions',
                                                 'Theatrical movies',
                                                 'Long-lived television programs',
                                                 'Books', 'Music',
                                                 'Other entertainment originals',
                                                 'Own account software'],
                                                'Intellectual Property'))
        major_asset_groups.update(dict.fromkeys(['Inventories'],
                                                'Inventories'))
        major_asset_groups.update(dict.fromkeys(['Land'], 'Land'))

        # define major industry groupings
        ind_dict = dict.fromkeys(['Farms',
                                  'Forestry, fishing, and related activities'],
                                 'Agriculture, forestry, fishing, and hunting')
        ind_dict.update(dict.fromkeys(['Oil and gas extraction',
                                       'Mining, except oil and gas',
                                       'Support activities for mining'],
                                      'Mining'))
        ind_dict.update(dict.fromkeys(['Utilities'], 'Utilities'))
        ind_dict.update(dict.fromkeys(['Construction'], 'Construction'))
        ind_dict.update(dict.fromkeys(['Wood products',
                                       'Nonmetallic mineral products',
                                       'Primary metals',
                                       'Fabricated metal products',
                                       'Machinery',
                                       'Computer and electronic products',
                                       'Electrical equipment, appliances, and components',
                                       'Motor vehicles, bodies and trailers, and parts',
                                       'Other transportation equipment',
                                       'Furniture and related products',
                                       'Miscellaneous manufacturing',
                                       'Food, beverage, and tobacco products',
                                       'Textile mills and textile products',
                                       'Apparel and leather and allied products',
                                       'Paper products', 'Printing and related support activities',
                                       'Petroleum and coal products',
                                       'Chemical products',
                                       'Plastics and rubber products'],
                                      'Manufacturing'))
        ind_dict.update(dict.fromkeys(['Wholesale trade'], 'Wholesale trade'))
        ind_dict.update(dict.fromkeys(['Retail trade'], 'Retail trade'))
        ind_dict.update(dict.fromkeys(['Air transportation',
                                       'Railroad transportation',
                                       'Water transportation',
                                       'Truck transportation',
                                       'Transit and ground passenger transportation',
                                       'Pipeline transportation',
                                       'Other transportation and support activitis',
                                       'Warehousing and storage'],
                                      'Transportation and warehousing'))
        ind_dict.update(dict.fromkeys(['Publishing industries (including software)',
                                       'Motion picture and sound recording industries',
                                       'Broadcasting and telecommunications',
                                       'Information and telecommunications'],
                                      'Information'))
        ind_dict.update(dict.fromkeys(['Federal Reserve banks',
                                       'Credit intermediation and related activities',
                                       'Securities, commodity contracts, and investments',
                                       'Insurance carriers and related activities',
                                       'Funds, trusts, and other financial vehicles'],
                                      'Finance and insurance'))
        ind_dict.update(dict.fromkeys(['Real estate',
                                       'Rental and leasing services and lessors of intangible assets'],
                                      'Real estate and rental and leasing'))
        ind_dict.update(dict.fromkeys(['Legal services',
                                       'Computer systems design and related services',
                                       'Miscellaneous professional, scientific, and technical services'],
                                      'Professional, scientific, and technical services'))
        ind_dict.update(dict.fromkeys(['Management of companies and enterprises'],
                                      'Management of companies and enterprises'))
        ind_dict.update(dict.fromkeys(['Administrative and support services',
                                       'Waster management and remediation services'],
                                      'Administrative and waste management services'))
        ind_dict.update(dict.fromkeys(['Educational services'],
                                      'Educational services'))
        ind_dict.update(dict.fromkeys(['Ambulatory health care services',
                                       'Hospitals',
                                       'Nursing and residential care facilities',
                                       'Social assistance'],
                                      'Health care and social assistance'))
        ind_dict.update(dict.fromkeys(['Performing arts, spectator sports, museums, and related activities',
                                       'Amusements, gambling, and recreation industries'],
                                      'Arts, entertainment, and recreation'))
        ind_dict.update(dict.fromkeys(['Accomodation',
                                       'Food services and drinking places'],
                                      'Accommodation and food services'))
        ind_dict.update(dict.fromkeys(['Other services, except government'],
                                      'Other services, except government'))

        bea_code_dict = dict.fromkeys(['110C', '113F'],
                                      'Agriculture, forestry, fishing, and hunting')
        bea_code_dict.update(dict.fromkeys(['2110', '2120', '2130'],
                                           'Mining'))
        bea_code_dict.update(dict.fromkeys(['2200'], 'Utilities'))
        bea_code_dict.update(dict.fromkeys(['2300'], 'Construction'))
        bea_code_dict.update(dict.fromkeys(['3210', '3270', '3310', '3320',
                                            '3330', '3340', '3350', '336M',
                                            '336O', '3370', '338A', '311A',
                                            '313T', '315A', '3220', '3230',
                                            '3240', '3250', '3260'],
                                           'Manufacturing'))
        bea_code_dict.update(dict.fromkeys(['4200'], 'Wholesale trade'))
        bea_code_dict.update(dict.fromkeys(['44RT'], 'Retail trade'))
        bea_code_dict.update(dict.fromkeys(['4810', '4820', '4830', '4840',
                                            '4850', '4860', '487S', '4930'],
                                           'Transportation and warehousing'))
        bea_code_dict.update(dict.fromkeys(['5110', '5120', '5130', '5140'],
                                           'Information'))
        bea_code_dict.update(dict.fromkeys(['5210', '5220', '5230', '5240',
                                            '5250'],
                                           'Finance and insurance'))
        bea_code_dict.update(dict.fromkeys(['5310', '5320'],
                                           'Real estate and rental and leasing'))
        bea_code_dict.update(dict.fromkeys(['5411', '5415', '5412'],
                                           'Professional, scientific, and technical services'))
        bea_code_dict.update(dict.fromkeys(['5500'],
                                           'Management of companies and enterprises'))
        bea_code_dict.update(dict.fromkeys(['5610', '5620'],
                                           'Administrative and waste management services'))
        bea_code_dict.update(dict.fromkeys(['6100'],
                                           'Educational services'))
        bea_code_dict.update(dict.fromkeys(['6210', '622H', '6230', '6240'],
                                           'Health care and social assistance'))
        bea_code_dict.update(dict.fromkeys(['711A', '7130'],
                                           'Arts, entertainment, and recreation'))
        bea_code_dict.update(dict.fromkeys(['7210', '7220'],
                                           'Accommodation and food services'))
        bea_code_dict.update(dict.fromkeys(['8100'],
                                           'Other services, except government'))

        self.bea_code_dict = bea_code_dict
        self.asset_dict = asset_dict
        self.major_asset_groups = major_asset_groups
        self.ind_dict = ind_dict

    def default_parameters(self):
        """
        Return Policy object same as self except with current-law policy.
        Returns
        -------
        Specifications: Specifications instance with the default configuration
        """
        dp = Specifications()
        return dp

    def update_specifications(self, revision, raise_errors=True):
        """
        Updates parameter specification with values in revision dictionary
        Parameters
        ----------
        reform: dictionary of one or more PARAM:VALUE pairs
        raise_errors: boolean
            if True (the default), raises ValueError when parameter_errors
                    exists;
            if False, does not raise ValueError when parameter_errors exists
                    and leaves error handling to caller of
                    update_specifications.
        Raises
        ------
        ValueError:
            if raise_errors is True AND
              _validate_parameter_names_types generates errors OR
              _validate_parameter_values generates errors.
        Returns
        -------
        nothing: void
        Notes
        -----
        Given a reform dictionary, typical usage of the Policy class
        is as follows::
            specs = Specifications()
            specs.update_specifications(reform)
        An example of a multi-parameter specification is as follows::
            spec = {
                frisch: [0.03]
            }
        This method was adapted from the Tax-Calculator
        behavior.py-update_behavior method.
        """
        # check that all revisions dictionary keys are integers
        if not isinstance(revision, dict):
            raise ValueError('ERROR: revision is not a dictionary')
        if not revision:
            return  # no revision to implement
        revision_years = sorted(list(revision.keys()))
        # check range of remaining revision_years
        # validate revision parameter names and types
        self.parameter_errors = ''
        self.parameter_warnings = ''
        self._validate_parameter_names_types(revision)
        if not self._ignore_errors and self.parameter_errors:
            raise ValueError(self.parameter_errors)
        # implement the revision
        revision_parameters = set()
        revision_parameters.update(revision.keys())
        self._update(revision)
        # validate revision parameter values
        self._validate_parameter_values(revision_parameters)
        if self.parameter_errors and raise_errors:
            raise ValueError('\n' + self.parameter_errors)
        self.compute_default_params()

    @staticmethod
    def read_json_param_objects(revision):
        """
        Read JSON file and convert to dictionary
        Returns
        -------
        rev_dict: formatted dictionary
        """
        # next process first reform parameter
        if revision is None:
            rev_dict = dict()
        elif isinstance(revision, six.string_types):
            if os.path.isfile(revision):
                txt = open(revision, 'r').read()
            else:
                txt = revision
            # strip out //-comments without changing line numbers
            json_str = re.sub('//.*', ' ', txt)
            # convert JSON text into a Python dictionary
            try:
                rev_dict = json.loads(json_str)
            except ValueError as valerr:
                msg = 'Policy reform text below contains invalid JSON:\n'
                msg += str(valerr) + '\n'
                msg += 'Above location of the first error may be approximate.\n'
                msg += 'The invalid JSON reform text is between the lines:\n'
                bline = 'XX----.----1----.----2----.----3----.----4'
                bline += '----.----5----.----6----.----7'
                msg += bline + '\n'
                linenum = 0
                for line in json_str.split('\n'):
                    linenum += 1
                    msg += '{:02d}{}'.format(linenum, line) + '\n'
                msg += bline + '\n'
                raise ValueError(msg)
        else:
            raise ValueError('reform is neither None nor string')

        return rev_dict

    def _validate_parameter_names_types(self, revision):
        """
        Check validity of parameter names and parameter types used
        in the specified revision dictionary.
        Parameters
        ----------
        revision: parameter dictionary of form {parameter_name: [value]}
        Returns:
        --------
        nothing: void
        Notes
        -----
        copied from taxcalc.Behavior._validate_parameter_names_types
        """
        param_names = set(self._vals.keys())
        # print('Parameter names = ', param_names)
        revision_param_names = list(revision.keys())
        for param_name in revision_param_names:
            if param_name not in param_names:
                msg = '{} unknown parameter name'
                self.parameter_errors += (
                    'ERROR: ' + msg.format(param_name) + '\n'
                )
            else:
                # check parameter value type avoiding use of isinstance
                # because isinstance(True, (int,float)) is True, which
                # makes it impossible to check float parameters
                bool_param_type = self._vals[param_name]['boolean_value']
                int_param_type = self._vals[param_name]['integer_value']
                string_param_type = self._vals[param_name]['string_value']
                if isinstance(revision[param_name], list):
                    param_value = revision[param_name]
                else:
                    param_value = [revision[param_name]]
                for idx in range(0, len(param_value)):
                    pval = param_value[idx]
                    pval_is_bool = type(pval) == bool
                    pval_is_int = type(pval) == int
                    pval_is_float = type(pval) == float
                    pval_is_string = type(pval) == str
                    if bool_param_type:
                        if not pval_is_bool:
                            msg = '{} value {} is not boolean'
                            self.parameter_errors += (
                                'ERROR: ' +
                                msg.format(param_name, pval) +
                                '\n'
                            )
                    elif int_param_type:
                        if not pval_is_int:  # pragma: no cover
                            msg = '{} value {} is not integer'
                            self.parameter_errors += (
                                'ERROR: ' +
                                msg.format(param_name, pval) +
                                '\n'
                            )
                    elif string_param_type:
                        if not pval_is_string:  # pragma: no cover
                            msg = '{} value {} is not string'
                            self.parameter_errors += (
                                'ERROR: ' +
                                msg.format(param_name, pval) +
                                '\n'
                            )
                    else:  # param is float type
                        if not (pval_is_int or pval_is_float):
                            msg = '{} value {} is not a number'
                            self.parameter_errors += (
                                'ERROR: ' +
                                msg.format(param_name, pval) +
                                '\n'
                            )
        del param_names

    def _validate_parameter_values(self, parameters_set):
        """
        Check values of parameters in specified parameter_set using
        range information from the current_law_policy.json file.
        Parameters:
        -----------
        parameters_set: set of parameters whose values need to be validated
        Returns:
        --------
        nothing: void
        Notes
        -----
        copied from taxcalc.Policy._validate_parameter_values
        """
        dp = self.default_parameters()
        parameters = sorted(parameters_set)
        for param_name in parameters:
            param_value = getattr(self, param_name)
            if not hasattr(param_value, 'shape'):  # value is not a numpy array
                param_value = np.array([param_value])
            for validation_op, validation_value in self._vals[param_name]['range'].items():
                if validation_op == 'possible_values':
                    if param_value not in validation_value:
                        out_of_range = True
                        msg = '{} value {} not in possible values {}'
                        if out_of_range:
                            self.parameter_errors += (
                                'ERROR: ' + msg.format(param_name,
                                                       param_value,
                                                       validation_value) + '\n'
                                )
                else:
                    # print(validation_op, param_value, validation_value)
                    if isinstance(validation_value, six.string_types):
                        validation_value = self.simple_eval(validation_value)
                    else:
                        validation_value = np.full(param_value.shape,
                                                   validation_value)
                    assert param_value.shape == validation_value.shape
                    for idx in np.ndindex(param_value.shape):
                        out_of_range = False
                        if validation_op == 'min' and (param_value[idx] <
                                                       validation_value[idx]):
                            out_of_range = True
                            msg = '{} value {} < min value {}'
                            extra = self._vals[param_name]['out_of_range_minmsg']
                            if extra:
                                msg += ' {}'.format(extra)
                        if validation_op == 'max' and (param_value[idx] >
                                                       validation_value[idx]):
                            out_of_range = True
                            msg = '{} value {} > max value {}'
                            extra = self._vals[param_name]['out_of_range_maxmsg']
                            if extra:
                                msg += ' {}'.format(extra)
                        if out_of_range:
                            self.parameter_errors += (
                                'ERROR: ' + msg.format(
                                    param_name, param_value[idx],
                                    validation_value[idx]) + '\n')
        del dp
        del parameters


# copied from taxcalc.tbi.tbi.reform_errors_warnings--probably needs further
# changes
def reform_warnings_errors(user_mods):
    """
    Generate warnings and errors for B-Tax parameter specifications
    Parameters:
    -----------
    user_mods : dict created by read_json_param_objects
    Return
    ------
    rtn_dict : dict with endpoint specific warning and error messages
    """
    rtn_dict = {'btax': {'warnings': '', 'errors': ''}}

    # create Specifications object and implement reform
    specs = Specifications()
    specs._ignore_errors = True
    try:
        specs.update_specifications(user_mods['btax'], raise_errors=False)
        rtn_dict['btax']['warnings'] = specs.parameter_warnings
        rtn_dict['btax']['errors'] = specs.parameter_errors
    except ValueError as valerr_msg:
        rtn_dict['btax']['errors'] = valerr_msg.__str__()
    return rtn_dict
