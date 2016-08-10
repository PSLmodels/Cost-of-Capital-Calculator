"""
Parameters (parameters.py):
-------------------------------------------------------------------------------

This module contains all the parameters used for the calc_final_outputs.py script. It also
contains intermediate calculations that produce more relevant parameters. The parameters
are placed in a dictionary. Last Updated 7/27/2016
"""
from argparse import Namespace
import copy
import json
import os

from calc_z import calc_tax_depr_rates, get_econ_depr
import numpy as np

from util import read_from_egg

DEFAULTS = json.loads(read_from_egg(os.path.join('param_defaults', 'btax_defaults.json')))
DEFAULT_ASSET_COLS = json.loads(read_from_egg(os.path.join('param_defaults', 'btax_results_by_asset.json')))
DEFAULT_INDUSTRY_COLS = json.loads(read_from_egg(os.path.join('param_defaults', 'btax_results_by_industry.json')))


def translate_param_names(**user_mods):
    """Takes parameters names from UI and turns them into names used in btax

    """

    # btax_betr_entity_Switch # If this parameter =True, then u_nc default to corp rate

    defaults = dict(DEFAULTS)
    user_mods.update({k: v['value'][0] for k,v in defaults.iteritems()})
    radio_tags = ('gds', 'ads', 'tax',)
    class_list = [3, 5, 7, 10, 15, 20, 25, 27.5, 39]
    class_list_str = [(str(i) if i != 27.5 == 0 else '27_5') for i in class_list]
    gds_ads_econ_deprec = {}
    for cl in class_list_str:
        for tag in radio_tags:
            for key, value in user_mods.iteritems():
                if hasattr(value, '__in__') and ('_{}_'.format(tag) in value and '{}yr_'.format(cl) in key):
                    # Detect a key like:
                    #    btax_depr_39yr
                    # With a value like:
                    #    btax_depr_39yr_gds_Switch
                    gds_ads_econ_deprec[cl] = tag
                    break

    user_bonus_deprec = {cl: user_mods['btax_depr_{}yr_exp'.format(cl)]
                         for cl in class_list_str}
    #user_deprec_system = copy.deepcopy(user_bonus_deprec)

    btax_depr_10yr_ads_Switch = False
    btax_depr_10yr_exp = 0.
    btax_depr_10yr_gds_Switch = True
    btax_depr_10yr_tax_Switch = False
    btax_depr_15yr_ads_Switch = False
    btax_depr_15yr_exp = 0.
    btax_depr_15yr_gds_Switch = True
    btax_depr_15yr_tax_Switch = False
    btax_depr_20yr_ads_Switch = False
    btax_depr_20yr_exp = 0.
    btax_depr_20yr_gds_Switch = True
    btax_depr_20yr_tax_Switch = False
    btax_depr_25yr_ads_Switch = False
    btax_depr_25yr_exp = 0.
    btax_depr_25yr_gds_Switch = True
    btax_depr_25yr_tax_Switch = False
    btax_depr_27_5yr_ads_Switch = False
    btax_depr_27_5yr_exp = 0.
    btax_depr_27_5yr_gds_Switch = True
    btax_depr_27_5yr_tax_Switch = False
    btax_depr_39yr_ads_Switch = False
    btax_depr_39yr_exp = 0.
    btax_depr_39yr_gds_Switch = True
    btax_depr_39yr_tax_Switch = False
    btax_depr_3yr_ads_Switch = False
    btax_depr_3yr_exp =0.
    btax_depr_3yr_gds_Switch = True
    btax_depr_3yr_tax_Switch = False
    btax_depr_5yr_ads_Switch = False
    btax_depr_5yr_exp = 0.
    btax_depr_5yr_gds_Switch = True
    btax_depr_5yr_tax_Switch = False
    btax_depr_7yr_ads_Switch = False
    btax_depr_7yr_exp = 0.
    btax_depr_7yr_gds_Switch = True
    btax_depr_7yr_tax_Switch= False
    btax_depr_27_5yr_ads_Switch = False
    btax_depr_27_5yr_exp = 0.
    btax_depr_27_5yr_gds_Switch = True
    btax_depr_27_5yr_tax_Switch = False
    user_deprec_system = {}
    class_list = ('3', '5', '7', '10', '15', '20', '25', '39')
    for item in class_list:
     if 'btax_depr_'+str(item)+'yr_gds_Switch':
         user_deprec_system[item] = 'GDS'
     elif 'btax_depr_'+str(item)+'yr_ads_Switch':
        user_deprec_system[item] = 'ADS'
     elif 'btax_depr_'+str(item)+'yr_tax_Switch':
        user_deprec_system[item] = 'Economic'

    # can't do 27.5 yrs in loop
    if btax_depr_27_5yr_gds_Switch:
        user_deprec_system['27.5'] = 'GDS'
    elif btax_depr_27_5yr_ads_Switch:
        user_deprec_system['27.5'] = 'ADS'
    elif btax_depr_27_5yr_tax_Switch:
        user_deprec_system['27.5'] = 'Economic'

    if user_mods['btax_betr_entity_Switch'] in (True, 'True'):
        u_nc = user_mods['btax_betr_corp']
    else:
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
                'gds_ads_econ_deprec': gds_ads_econ_deprec,
    }

    return user_params


def get_params(**user_mods):
    """Contains all the parameters

        :returns: Inflation rate, depreciation, tax rate, discount rate, return to savers, property tax
        :rtype: dictionary
    """
    #macro variables
    E_c = 0.07
    f_c = 0.41
    f_nc = 0.32
    f_array = np.array([[f_c, f_nc], [1, 1], [0,0]])

    #calibration variables
    omega_scg = 0.03627
    omega_lcg = 0.48187
    omega_xcg = 0.48187

    alpha_c_e_ft = 0.584
    alpha_c_e_td = 0.058
    alpha_c_e_nt = 0.358

    alpha_c_d_ft = 0.460
    alpha_c_d_td = 0.213
    alpha_c_d_nt = 0.327

    alpha_nc_d_ft = 0.691
    alpha_nc_d_td = 0.142
    alpha_nc_d_nt = 0.167

    alpha_h_d_ft = 0.716
    alpha_h_d_td = 0.071
    alpha_h_d_nt = 0.213

    #user defined variables

    # those in UI now:
    user_params = translate_param_names(**user_mods)
    pi = user_params['pi']
    i = user_params['i']
    u_c = user_params['u_c']
    u_nc = user_params['u_nc']
    u_array = np.array([u_c, u_nc])
    w = user_params['w']
    inv_credit = user_params['inv_credit']
    ace_c = user_params['ace_c']
    ace_nc = 0.
    ace_array = np.array([ace_c, ace_nc])
    r_ace = i
    int_haircut = user_params['int_haircut']
    bonus_deprec = user_params['bonus_deprec']
    deprec_system = user_params['deprec_system']

    tau_div = 0.121 # tax rate on dividend income
    tau_int = 0.221 # tax rate on interest income
    tau_scg = 0.28 # tax rate on short term capital gains
    tau_lcg = 0.145 # tax rate on long term capital gains
    tau_xcg = 0.00 # tax rate on capital gains held to death
    tau_td = 0.209 # tax rate on return to equity held in tax defferred accounts
    tau_h = 0.194 # tax rate on non-corporate business income
    Y_td = 8.
    Y_scg = 4/12.
    Y_lcg = 8.
    gamma = 0.3
    m = 0.4286

    #intermediate variables
    sprime_c_td = (1/Y_td)*np.log(((1-tau_td)*np.exp(i*Y_td))+tau_td)-pi
    s_c_d_td = gamma*(i-pi) + (1-gamma)*sprime_c_td
    s_c_d = alpha_c_d_ft*(((1-tau_int)*i)-pi) + alpha_c_d_td*s_c_d_td + alpha_c_d_nt*(i-pi)

    s_nc_d_td = s_c_d_td
    s_nc_d = alpha_nc_d_ft*(((1-tau_int)*i)-pi) + alpha_nc_d_td*s_nc_d_td + alpha_nc_d_nt*(i-pi)

    g_scg = (1/Y_scg)*np.log(((1-tau_scg)*np.exp((pi+m*E_c)*Y_scg))+tau_scg)-pi
    g_lcg = (1/Y_lcg)*np.log(((1-tau_lcg)*np.exp((pi+m*E_c)*Y_lcg))+tau_lcg)-pi
    g = omega_scg*g_scg + omega_lcg*g_lcg + omega_xcg*m*E_c
    s_c_e_ft = (1-m)*E_c*(1-tau_div)+g
    s_c_e_td = (1/Y_td)*np.log(((1-tau_td)*np.exp((pi+E_c)*Y_td))+tau_td)-pi
    s_c_e = alpha_c_e_ft*s_c_e_ft + alpha_c_e_td*s_c_e_td + alpha_c_e_nt*E_c

    s_c = f_c*s_c_d + (1-f_c)*s_c_e

    E_nc = s_c_e
    E_array = np.array([E_c, E_nc])
    s_nc_e = E_nc
    s_nc = f_nc*s_nc_d + (1-f_nc)*s_nc_e
    s_array = np.array([[s_c, s_nc], [s_c_d, s_nc_d], [s_c_e, s_nc_e]])

    r = f_array*(i*(1-(1-int_haircut)*u_array))+(1-f_array)*(E_array+pi - E_array*r_ace*ace_array)
    r_prime = f_array*i+(1-f_array)*(E_array+pi)
    delta = get_econ_depr()
    tax_methods = {'GDS 200%': 2.0, 'GDS 150%': 1.5, 'GDS SL': 1.0, 'ADS SL': 1.0}
    financing_list = ['', '_d', '_e']
    entity_list = ['_c', '_nc']
    z = calc_tax_depr_rates(r, delta, bonus_deprec, deprec_system, tax_methods, financing_list, entity_list)


    parameters = {'inflation rate': pi,
    'econ depreciation': delta,
    'depr allow': z,
    'tax rate': u_array,
    'discount rate': r,
    'after-tax rate': r_prime,
    'return to savers': s_array,
    'prop tax': w,
    'inv_credit': inv_credit,
    'ace':ace_array,
    'int_haircut':int_haircut,
    'financing_list':financing_list,
    'entity_list':entity_list,
    'delta': delta
    }

    return parameters
