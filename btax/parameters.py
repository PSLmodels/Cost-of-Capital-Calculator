"""
Parameters (parameters.py):
------------------------------------------------------------------------
This module contains all the parameters used for the
calc_final_outputs.py script. It also contains intermediate calculations
that produce more relevant parameters. The parameters are placed in a
dictionary.
"""

# from argparse import Namespace
# import copy
import json
import os

import numpy as np
import pandas as pd

from btax.util import read_from_egg, DEFAULT_START_YEAR, RECORDS_START_YEAR

# first year of tax parameters in btax_defaults.json
PARAMETER_START_YEAR = 2015
DEFAULTS = json.loads(read_from_egg(os.path.join('param_defaults',
                                                 'btax_defaults.json')))
DEFAULT_ASSET_COLS = json.loads(read_from_egg
                                (os.path.join('param_defaults',
                                              'btax_results_by_asset.json')))
DEFAULT_INDUSTRY_COLS = json.loads(read_from_egg
                                   (os.path.join('param_defaults',
                                                 'btax_results_by_industry.json')))


def translate_param_names(start_year=DEFAULT_START_YEAR, **user_mods):
    """
    Takes parameters names from UI and turns them into names used in btax

    Args:
        start_year: integer, tax year calculate METRs for
        user_mods: dictionary, user modifiable parameter values

    Returns:
        user_params: dictionary, user modified parameters formatted and
                      named for use in B-Tax

    """
    year = start_year - PARAMETER_START_YEAR
    defaults = dict(DEFAULTS)

    # Handle depreciation system first since can only have one True for
    # each asset class, so don't want to have this after the replace
    # missing user defined params with defauls that is next.
    class_list = [3, 5, 7, 10, 15, 20, 25, 27.5, 39]
    class_list_str = [(str(i) if i != 27.5 else '27_5') for i in
                      class_list]
    user_deprec_system = {}
    for cl in class_list_str:
        state = 'GDS'
        if user_mods.get('btax_depr_{}yr_gds_Switch'.format(cl)):
            state = 'GDS'
        if user_mods.get('btax_depr_{}yr_ads_Switch'.format(cl)):
            state = 'ADS'
        if user_mods.get('btax_depr_{}yr_tax_Switch'.format(cl)):
            state = 'Economic'
        user_deprec_system[cl] = state

    user_mods.update({k: v['value'][year] for k, v in defaults.items()
                      if k not in user_mods})

    user_bonus_deprec = {cl: user_mods['btax_depr_{}yr_exp'.format(cl)]
                         / 100. for cl in class_list_str}

    # Determine method for accounting for inventories
    if user_mods['inventory_method'] == 0:
        phi = 0.5  # Fraction of inventories using LIFO
        expense_inventory = False  # Flag for expensing of inventories
    elif user_mods['inventory_method'] == 1:
        phi = 1.0  # Use only LIFO
        expense_inventory = False
    elif user_mods['inventory_method'] == 2:
        phi = 0.0  # Use only FIFO
        expense_inventory = False
    elif user_mods['inventory_method'] == 3:
        phi = 0.5
        expense_inventory = True

    # Rate of expensing for land
    expense_land = user_mods['btax_depr_land_exp'] / 100.

    u_nc = user_mods['btax_betr_pass']

    user_params = {
        'u_c': user_mods['btax_betr_corp'],
        'u_nc': u_nc,
        'pi': user_mods['btax_econ_inflat'],
        'i': user_mods['btax_econ_nomint'],
        'ace_c': user_mods['btax_other_corpeq'],
        'int_haircut': user_mods['btax_other_hair'],
        'inv_credit': user_mods['btax_other_invest'],
        'w': user_mods['btax_other_proptx'],
        'bonus_deprec': user_bonus_deprec,
        'deprec_system': user_deprec_system,
        'phi': phi,
        'expense_inventory': expense_inventory,
        'expense_land': expense_land
    }

    return user_params


def get_params(test_run, baseline, start_year, iit_reform, **user_mods):
    """
    Sets values to all the model parameters.

    Args:
        test_run: Boolean, if True then run test version of model (no
                    need for puf.csv file)
        baseline: Boolean, True if current law policy run
        start_year: Integer, tax year in which METRs computed
        iit_reform: dictionary, Tax-Calculator reform dictionary
        user_mods: dicionary, user defined parameter values

    Returns:
        parameters: dictionary, values of all model parameters

    """
    from btax.calc_z import calc_tax_depr_rates, get_econ_depr
    # macro variables
    E_c = 0.058  # CBO (2014) 0.07
    f_c = 0.32  # CBO (2014)0.41
    f_nc = 0.29  # CBO (2014) 0.32
    f_array = np.array([[f_c, f_nc], [1, 1], [0, 0]])

    # househld portfolio share parameters - right now using CBO (2014)
    # fraction of capital gains at short term, long term, untaxed
    omega_scg = 0.034
    omega_lcg = 0.496
    omega_xcg = 0.469

    # fraction of corp equity facing full tax, tax deferred, and untaxed
    alpha_c_e_ft = 0.572
    alpha_c_e_td = 0.039
    alpha_c_e_nt = 0.389

    # fraction of corp debt facing full tax, tax deferred, and untaxed
    alpha_c_d_ft = 0.523
    alpha_c_d_td = 0.149
    alpha_c_d_nt = 0.328

    # fraction of non-corp equity in full tax, tax deferred, and untaxed
    alpha_nc_d_ft = 0.763
    alpha_nc_d_td = 0.101
    alpha_nc_d_nt = 0.136

    # fraction of homeowner equity in full tax, tax deferred, and untaxed
    # these aren't currently used
    alpha_h_d_ft = 0.779
    alpha_h_d_td = 0.037
    alpha_h_d_nt = 0.183

    # user defined variables
    user_params = translate_param_names(start_year, **user_mods)
    pi = user_params['pi']
    i = user_params['i']
    w = user_params['w']
    inv_credit = user_params['inv_credit']
    ace_c = user_params['ace_c']
    ace_nc = 0.
    ace_array = np.array([ace_c, ace_nc])
    r_ace = i
    int_haircut = user_params['int_haircut']
    bonus_deprec = user_params['bonus_deprec']
    deprec_system = user_params['deprec_system']
    phi = user_params['phi']
    expense_inventory = user_params['expense_inventory']
    expense_land = user_params['expense_land']

    # for land and inventories which don't have tax deprec
    bonus_deprec['100'] = 0.0
    deprec_system['100'] = 'GDS'

    # call tax calc to get individual rates
    if test_run:
        tau_nc = 0.33  # 0.331 # tax rate on non-corporate business income
        tau_div = 0.1757  # 0.184 # tax rate on dividend income
        tau_int = 0.2379  # 0.274 # tax rate on interest income
        tau_scg = 0.3131  # 0.323 # tax rate on short term capital gains
        tau_lcg = 0.222  # 0.212 # tax rate on long term capital gains
        tau_xcg = 0.00  # tax rate on capital gains held to death
        tau_td = 0.215  # tax rate on equity return held in tax deferred
        tau_h = 0.181  # tax rate owner occupied housing deductions
        # test below is that calculator can be created
        CUR_PATH = os.path.abspath(os.path.dirname(__file__))
        TAXDATA_PATH = os.path.join(CUR_PATH, 'test_data',
                                    'puf91taxdata.csv.gz')
        TAXDATA = pd.read_csv(TAXDATA_PATH, compression='gzip')
        WEIGHTS_PATH = os.path.join(CUR_PATH, 'test_data',
                                    'puf91weights.csv.gz')
        WEIGHTS = pd.read_csv(WEIGHTS_PATH, compression='gzip')
        from btax.get_taxcalc_rates import get_calculator
        calc = get_calculator(baseline=False,
                              calculator_start_year=start_year,
                              reform=iit_reform, data=TAXDATA,
                              weights=WEIGHTS,
                              records_start_year=RECORDS_START_YEAR)
        assert calc.current_year == start_year
    else:
        from btax.get_taxcalc_rates import get_rates
        indiv_rates = get_rates(baseline, start_year, iit_reform)
        tau_nc = indiv_rates['tau_nc']
        tau_div = indiv_rates['tau_div']
        tau_int = indiv_rates['tau_int']
        tau_scg = indiv_rates['tau_scg']
        tau_lcg = indiv_rates['tau_lcg']
        tau_xcg = 0.00  # tax rate on capital gains held to death
        tau_td = indiv_rates['tau_td']
        tau_h = indiv_rates['tau_h']

    # entity level tax rates - this changes how used in calculations
    # depending on how applied
    u_c = user_params['u_c']
    if user_params['u_nc'] == 0.0:
        u_nc = tau_nc
    else:
        u_nc = user_params['u_nc']
    u_array = np.array([u_c, u_nc])

    # Parameters for holding periods of assets
    Y_td = 8.
    Y_scg = 4 / 12.
    Y_lcg = 8.
    Y_v = 4 / 12.  # holding period for inventories
    gamma = 0.3

    # Miscellaneous parameters
    m = 0.44  # Divident payout rate
    p = 0.2  # Profit rate to compute EATR

    # Intermediate variables
    sprime_c_td = ((1 / Y_td) * np.log(((1 - tau_td) * np.exp(i * Y_td))
                                       + tau_td) - pi)
    s_c_d_td = gamma * (i - pi) + (1 - gamma) * sprime_c_td
    s_c_d = (alpha_c_d_ft * (((1 - tau_int) * i) - pi) + alpha_c_d_td *
             s_c_d_td + alpha_c_d_nt * (i - pi))
    s_nc_d_td = s_c_d_td
    s_nc_d = (alpha_nc_d_ft * (((1 - tau_int) * i) - pi) + alpha_nc_d_td
              * s_nc_d_td + alpha_nc_d_nt * (i - pi))

    g_scg = ((1 / Y_scg) * np.log(((1 - tau_scg) * np.exp((pi + m * E_c)
                                                          * Y_scg)) +
                                  tau_scg) - pi)
    g_lcg = ((1 / Y_lcg) * np.log(((1 - tau_lcg) * np.exp((pi + m * E_c)
                                                          * Y_lcg)) +
                                  tau_lcg) - pi)
    g = omega_scg * g_scg + omega_lcg * g_lcg + omega_xcg * m * E_c
    s_c_e_ft = (1 - m) * E_c * (1 - tau_div) + g
    s_c_e_td = ((1 / Y_td) * np.log(((1 - tau_td) * np.exp((pi + E_c) *
                                                           Y_td)) +
                                    tau_td) - pi)
    s_c_e = (alpha_c_e_ft * s_c_e_ft + alpha_c_e_td * s_c_e_td +
             alpha_c_e_nt * E_c)

    s_c = f_c * s_c_d + (1 - f_c) * s_c_e

    E_nc = s_c_e
    E_array = np.array([E_c, E_nc])
    s_nc_e = E_nc
    s_nc = f_nc * s_nc_d + (1 - f_nc) * s_nc_e
    s_array = np.array([[s_c, s_nc], [s_c_d, s_nc_d], [s_c_e, s_nc_e]])
    r = (f_array * (i * (1 - (1 - int_haircut) * u_array)) + (1 -
                                                              f_array) *
         (E_array + pi - E_array * r_ace * ace_array))
    r_prime = f_array * i + (1 - f_array) * (E_array + pi)

    # if no entity level taxes on pass-throughs, ensure mettr and metr
    # on non-corp entities the same
    if user_params['u_nc'] == 0.0:
        r_prime[:, 1] = s_array[:, 1] + pi
    # If entity level tax, assume distribute earnings at same rate corps
    # distribute dividends and these are taxed at dividends tax rate
    # (which seems likely).  Also implicitly assumed that if entity
    # level tax, then only additional taxes on pass-through income are
    # capital gains and dividend taxes
    else:
        # keep debt and equity financing ratio the same even though now
        # entity level tax that might now favor debt
        s_array[0, 1] = f_nc * s_nc_d + (1 - f_nc) * s_c_e
        s_array[2, 1] = s_c_e
    delta = get_econ_depr()
    tax_methods = {'DB 200%': 2.0, 'DB 150%': 1.5, 'SL': 1.0,
                   'Economic': 1.0, 'Expensing': 1.0}
    financing_list = ['', '_d', '_e']
    entity_list = ['_c', '_nc']
    z = calc_tax_depr_rates(r, pi, delta, bonus_deprec, deprec_system,
                            expense_inventory, expense_land, tax_methods,
                            financing_list, entity_list)

    '''
    ------------------------------------------
    Define asset categories
    ------------------------------------------
    '''
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

    parameters = {'inflation rate': pi, 'econ depreciation': delta,
                  'depr allow': z, 'tax rate': u_array,
                  'discount rate': r, 'after-tax rate': r_prime,
                  'return to savers': s_array, 'prop tax': w,
                  'inv_credit': inv_credit, 'ace': ace_array,
                  'int_haircut': int_haircut,
                  'financing_list': financing_list,
                  'entity_list': entity_list,
                  'delta': delta, 'Y_v': Y_v, 'phi': phi, 'p': p,
                  'expense_inventory': expense_inventory,
                  'asset_dict': asset_dict,
                  'ind_dict': ind_dict,
                  'major_asset_groups': major_asset_groups,
                  'bea_code_dict': bea_code_dict}

    return parameters
