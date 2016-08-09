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
    user_deprec_system = copy.deepcopy(user_bonus_deprec)
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
                'user_bonus_deprec': user_bonus_deprec,
                'user_deprec_system': user_deprec_system,
                'gds_ads_econ_deprec': gds_ads_econ_deprec,
    }

    return user_params


def get_base_param_defaults(**user_mods):

    """Returns namespace of user-given params

    Parameters:

        user_mods:  variable keyword args from the UI, if given
                    may include the key "no_defaults" to skip
                    loading the json defaults as an update
                    to the parameters
    """

    f_c = 0.41
    f_nc = 0.32
    u_c = 0.35
    u_nc = 0.267
    ace_c = 0.
    ace_nc = 0.
    i = 0.072
    params =  Namespace(pi=0.018,          #macro variables
                    	i=i,
                    	E_c=0.07,
                    	f_c=f_c,
                    	f_nc=f_nc,
                    	f_array=np.array([[f_c, f_nc], [1, 1], [0,0]]),
                    	omega_scg=0.03627, #calibration variables
                    	omega_lcg=0.48187,
                    	omega_xcg=0.48187,
                    	alpha_c_e_ft=0.584,
                    	alpha_c_e_td=0.058,
                    	alpha_c_e_nt=0.358,
                    	alpha_c_d_ft=0.460,
                    	alpha_c_d_td=0.213,
                    	alpha_c_d_nt=0.327,
                    	alpha_nc_d_ft=0.691,
                    	alpha_nc_d_td=0.142,
                    	alpha_nc_d_nt=0.167,
                    	alpha_h_d_ft=0.716,
                    	alpha_h_d_td=0.071,
                    	alpha_h_d_nt=0.213,
                    	u_c=u_c,    #user defined variables
                    	u_nc=u_nc,
                    	u_array=np.array([u_c, u_nc]),
                    	w=0., #0.0117
                    	inv_credit=0.,
                    	ace_c=ace_c,
                    	ace_nc=ace_nc,
                    	ace_array=np.array([ace_c, ace_nc]),
                    	r_ace=i,
                    	int_haircut=0.,
                    	bonus_deprec=0.,
                    	tau_div=0.121,
                    	tau_int=0.221,
                    	tau_scg=0.28,
                    	tau_lcg=0.145,
                    	tau_xcg=0.00,
                    	tau_td=0.209,
                    	tau_h=0.194,
                    	Y_td=8.,
                    	Y_scg=4/12.,
                    	Y_lcg=8.,
                    	gamma=0.3,
                    	m=0.4286)
    if user_mods:
        vars(params).update(translate_param_names(**user_mods))
    return params

def get_params(**user_mods):
	#intermediate variables
    params = get_base_param_defaults(**user_mods)
    sprime_c_td = (1/params.Y_td)*np.log(((1-params.tau_td)*np.exp(params.i*params.Y_td))+params.tau_td)-params.pi
    s_c_d_td = params.gamma*(params.i-params.pi) + (1-params.gamma)*sprime_c_td
    s_c_d = params.alpha_c_d_ft*(((1-params.tau_int)*params.i)-params.pi) + params.alpha_c_d_td*s_c_d_td + params.alpha_c_d_nt*(params.i-params.pi)

    s_nc_d_td = s_c_d_td
    s_nc_d = params.alpha_nc_d_ft*(((1-params.tau_int)*params.i)-params.pi) + params.alpha_nc_d_td*s_nc_d_td + params.alpha_nc_d_nt*(params.i-params.pi)

    g_scg = (1/params.Y_scg)*np.log(((1-params.tau_scg)*np.exp((params.pi+params.m*params.E_c)*params.Y_scg))+params.tau_scg)-params.pi
    g_lcg = (1/params.Y_lcg)*np.log(((1-params.tau_lcg)*np.exp((params.pi+params.m*params.E_c)*params.Y_lcg))+params.tau_lcg)-params.pi
    g = params.omega_scg*g_scg + params.omega_lcg*g_lcg + params.omega_xcg*params.m*params.E_c
    s_c_e_ft = (1-params.m)*params.E_c*(1-params.tau_div)+g
    s_c_e_td = (1/params.Y_td)*np.log(((1-params.tau_td)*np.exp((params.pi+params.E_c)*params.Y_td))+params.tau_td)-params.pi
    s_c_e = params.alpha_c_e_ft*s_c_e_ft + params.alpha_c_e_td*s_c_e_td + params.alpha_c_e_nt*params.E_c

    s_c = params.f_c*s_c_d + (1-params.f_c)*s_c_e

    E_nc = s_c_e
    E_array = np.array([params.E_c, E_nc])
    s_nc_e = E_nc
    s_nc = params.f_nc*s_nc_d + (1-params.f_nc)*s_nc_e
    s_array = np.array([[s_c, s_nc], [s_c_d, s_nc_d], [s_c_e, s_nc_e]])

    r = params.f_array*(params.i*(1-(1-params.int_haircut)*params.u_array))+(1-params.f_array)*(E_array+params.pi - E_array*params.r_ace*params.ace_array)
    r_prime = params.f_array*params.i+(1-params.f_array)*(E_array+params.pi)
    tax_methods = {'GDS 200%': 2.0, 'GDS 150%': 1.5, 'GDS SL': 1.0, 'ADS SL': 1.0}
    financing_list = ['', '_d', '_e']
    entity_list = ['_c', '_nc']
    z = calc_tax_depr_rates(r, params.bonus_deprec, tax_methods, financing_list, entity_list)
    delta = get_econ_depr()

    parameters =  { 'inflation rate': params.pi,
                    'econ depreciation': delta,
                    'depr allow': z,
                    'tax rate': params.u_array,
                    'discount rate': r,
                    'after-tax rate': r_prime,
                    'return to savers': s_array,
                    'prop tax': params.w,
                    'inv_credit': params.inv_credit,
                    'ace': params.ace_array,
                    'int_haircut': params.int_haircut,
                    'financing_list':financing_list,
                    'entity_list':entity_list,
                }

    return parameters
