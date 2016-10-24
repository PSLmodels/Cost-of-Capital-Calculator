'''
------------------------------------------------------------------------
Late updated 8/26/2016

This program extracts weighted average marginal tax rates from the
microsimulation model (tax-calculator).

This module defines the following functions:
    get_data()


This Python script calls the following functions:
    taxcalc

This py-file creates the following other file(s):

------------------------------------------------------------------------
'''

import taxcalc
from taxcalc import *
import pandas as pd
from pandas import DataFrame
import numpy as np
import copy
import numba
import pickle

def only_growth_assumptions(user_mods, start_year):
    """
    Extract any reform parameters that are pertinent to growth
    assumptions
    """
    growth_dd = taxcalc.growth.Growth.default_data(start_year=start_year)
    ga = {}
    for year, reforms in user_mods.items():
        overlap = set(growth_dd.keys()) & set(reforms.keys())
        if overlap:
            ga[year] = {param:reforms[param] for param in overlap}
    return ga


def only_reform_mods(user_mods, start_year):
    """
    Extract parameters that are just for policy reforms
    """
    pol_refs = {}
    beh_dd = Behavior.default_data(start_year=start_year)
    growth_dd = taxcalc.growth.Growth.default_data(start_year=start_year)
    policy_dd = taxcalc.policy.Policy.default_data(start_year=start_year)
    for year, reforms in user_mods.items():
        all_cpis = {p for p in reforms.keys() if p.endswith("_cpi") and
                    p[:-4] in policy_dd.keys()}
        pols = set(reforms.keys()) - set(beh_dd.keys()) - set(growth_dd.keys())
        pols &= set(policy_dd.keys())
        pols ^= all_cpis
        if pols:
            pol_refs[year] = {param:reforms[param] for param in pols}
    return pol_refs

def get_calculator(baseline, calculator_start_year, reform=None, data=None,
weights=None, records_start_year=None):
    '''
    --------------------------------------------------------------------
    This function creates the tax calculator object for the microsim
    --------------------------------------------------------------------
    INPUTS:
    baseline                 = boolean, True if baseline tax policy
    calculator_start_year    = integer, first year of budget window
    reform                   = dictionary, reform parameters
    data                     = DataFrame for Records object (opt.)
    weights                  = weights DataFrame for Records object (opt.)
    records_start_year       = the start year for the data and weights dfs

    RETURNS: Calculator object with a current_year equal to
             calculator_start_year
    --------------------------------------------------------------------

    '''
    # create a calculator
    policy1 = Policy()
    if data is not None:
        records1 = Records(data=data, weights=weights, start_year=records_start_year)
    else:
        records1 = Records()

    if baseline:
        #Should not be a reform if baseline is True
        assert not reform

    growth_assumptions = only_growth_assumptions(reform, calculator_start_year)
    reform_mods = only_reform_mods(reform, calculator_start_year)

    if not baseline:
        policy1.implement_reform(reform_mods)

    # the default set up increments year to 2013
    calc1 = Calculator(records=records1, policy=policy1)

    if growth_assumptions:
        calc1.growth.update_economic_growth(growth_assumptions)

    # this increment_year function extrapolates all PUF variables to the next year
    # so this step takes the calculator to the start_year
    for i in range(calculator_start_year-2013):
        calc1.increment_year()

    return calc1


def get_rates(baseline=False, start_year=2016, reform={}):
    '''
    --------------------------------------------------------------------
    This function computes weighted average marginal tax rates using
    micro data from the tax calculator
    --------------------------------------------------------------------
    INPUTS:
    baseline        = boolean, =True if baseline tax policy, =False if reform
    start_year      = integer, first year of budget window
    reform          = dictionary, reform parameters

    OTHER FUNCTIONS AND FILES CALLED BY THIS FUNCTION: None

    OBJECTS CREATED WITHIN FUNCTION:
    micro_data_dict = dictionary, contains pandas dataframe for each year
                      of budget window.  Dataframe contain mtrs, etrs, income variables, age
                      from tax-calculator and PUF-CPS match

    OUTPUT:
        individual_rates: a dictionary of individual (IIT+payroll) marginal tax rates

    RETURNS: individual_rates
    --------------------------------------------------------------------
    '''

    calc1 = get_calculator(baseline=baseline, calculator_start_year=start_year,
                           reform=reform)

    # running all the functions and calculates taxes
    calc1.calc_all()

    ##get mtrs
    # sch c
    [mtr_fica_schC, mtr_iit_schC, mtr_combined_schC] = calc1.mtr('e00900p')
    # sch e (not s corp or partnership)
    [mtr_fica_schE, mtr_iit_schE, mtr_combined_schE] = calc1.mtr('e02000')
    # Partnership and s corp income
    [mtr_fica_PT, mtr_iit_PT, mtr_combined_PT] = calc1.mtr('e26270')
    # dividends
    [mtr_fica_div, mtr_iit_div, mtr_combined_div] = calc1.mtr('e00650')
    # interest income
    # taxable
    [mtr_fica_int, mtr_iit_int, mtr_combined_int] = calc1.mtr('e00300')
    # non-taxable
    [mtr_fica_int_te, mtr_iit_int_te, mtr_combined_int_te] = calc1.mtr('e00400')
    # short term capital gains
    [mtr_fica_scg, mtr_iit_scg, mtr_combined_scg] = calc1.mtr('p22250')
    # long term capital gains
    [mtr_fica_lcg, mtr_iit_lcg, mtr_combined_lcg] = calc1.mtr('p23250')

    # pension distributions
    # does PUF have e01500?  Do we want IRA distributions here?
    # Weird - I see e01500 in PUF, but error when try to call it
    [mtr_fica_pension, mtr_iit_pension, mtr_combined_pension] = calc1.mtr('e01700')
    # mortgage interest and property tax deductions
    # do we also want mtg ins premiums here?
    # mtg interest
    [mtr_fica_mtg, mtr_iit_mtg, mtr_combined_mtg] = calc1.mtr('e19200')
    # prop tax
    [mtr_fica_prop, mtr_iit_prop, mtr_combined_prop] = calc1.mtr('e18500')

    businc = (calc1.records.e00900p+calc1.records.e02000)
    pos_businc = businc > 0
    pos_ti = calc1.records.c04800>0
    tau_nc = ((((mtr_iit_schC*np.abs(calc1.records.e00900p))+
                (mtr_iit_schE*np.abs(calc1.records.e02000-calc1.records.e26270))
               + (mtr_iit_PT*np.abs(calc1.records.e26270))) *
                             pos_ti * calc1.records.s006).sum() /
                     ((np.abs(calc1.records.e00900p)+
                       np.abs(calc1.records.e02000-calc1.records.e26270)+
                       np.abs(calc1.records.e26270))
                      *  pos_ti * calc1.records.s006).sum())
    tau_div = ((mtr_iit_div * calc1.records.e00650 * pos_ti *
                           calc1.records.s006).sum() /
                     (calc1.records.e00650 * pos_ti * calc1.records.s006).sum())
    tau_int = ((mtr_iit_int * calc1.records.e00300 * pos_ti *
                           calc1.records.s006).sum() /
                     (calc1.records.e00300 * pos_ti * calc1.records.s006).sum())

    tau_scg = ((mtr_iit_scg * np.abs(calc1.records.p22250) *
                           (calc1.records.p22250>0.) *
                           pos_ti * calc1.records.s006).sum() /
                     (np.abs(calc1.records.p22250) * (calc1.records.p22250>0.) *
                      pos_ti * calc1.records.s006).sum())
    tau_lcg = ((mtr_iit_lcg * np.abs(calc1.records.p23250) *
                          (calc1.records.p23250>0.)*
                          pos_ti * calc1.records.s006).sum() /
                     (np.abs(calc1.records.p23250)* (calc1.records.p23250>0.)*
                      pos_ti * calc1.records.s006).sum())
    tau_td = ((mtr_iit_pension * calc1.records.e01500 * pos_ti *
                           calc1.records.s006).sum() /
                     (calc1.records.e01500 * pos_ti * calc1.records.s006).sum())
    tau_h = -1*(((mtr_iit_mtg*calc1.records.e19200)+(mtr_iit_prop*calc1.records.e18500) *
                            pos_ti * calc1.records.s006).sum() /
                     ((calc1.records.e19200)+(calc1.records.e18500)
                      * pos_ti * calc1.records.s006).sum())


    individual_rates = {'tau_nc':tau_nc,'tau_div':tau_div,'tau_int':tau_int,
                        'tau_scg':tau_scg,'tau_lcg':tau_lcg,'tau_td':tau_td,
                        'tau_h':tau_h}

    return individual_rates
