'''
------------------------------------------------------------------------
This program extracts weighted average marginal tax rates from the
microsimulation model (tax-calculator).

This module defines the following functions:
    get_data()

This Python script calls the following functions:
    taxcalc

This py-file creates the following other file(s):
------------------------------------------------------------------------
'''
from __future__ import print_function
import numpy as np
from taxcalc import Policy, Records, Calculator
from ccc.utils import DEFAULT_START_YEAR, TC_LAST_YEAR


def get_calculator(baseline, calculator_start_year, reform=None,
                   data='cps', weights=None, records_start_year=None):
    '''
    This function creates the tax calculator object for the microsim

    Args:
        baseline: boolean, True if baseline tax policy
        calculator_start_year: integer, first year of budget window
        reform: dictionary, reform parameters
        data: DataFrame, DataFrame for Records object (opt.)
        weights: DataFrame, weights DataFrame for Records object (opt.)
        records_start_year: integer, the start year for the data and
                            weights dfs

    Returns:
        calc1: Tax Calculator Calculator object with a current_year
            equal to calculator_start_year
    '''
    # create a calculator
    policy1 = Policy()
    if data is not None and "cps" in data:
        records1 = Records.cps_constructor()
        # impute short and long term capital gains if using CPS data
        # in 2012 SOI data 6.587% of CG as short-term gains
        records1.p22250 = 0.06587 * records1.e01100
        records1.p23250 = (1 - 0.06587) * records1.e01100
        # set total capital gains to zero
        records1.e01100 = np.zeros(records1.e01100.shape[0])
    elif data is not None:
        records1 = Records(data=data, weights=weights,
                           start_year=records_start_year)
    else:
        records1 = Records()

    if baseline:
        # Should not be a reform if baseline is True
        assert not reform

    if not baseline:
        policy1.implement_reform(reform)

    # the default set up increments year to 2013
    calc1 = Calculator(records=records1, policy=policy1)

    # this increment_year function extrapolates all PUF variables to
    # the next year so this step takes the calculator to the start_year
    if calculator_start_year > TC_LAST_YEAR:
        raise RuntimeError("Start year is beyond data extrapolation.")
    while calc1.current_year < calculator_start_year:
        calc1.increment_year()

    return calc1


def get_rates(baseline=False, start_year=DEFAULT_START_YEAR, reform={},
              data='cps'):
    '''
    This function computes weighted average marginal tax rates using
    micro data from the tax calculator

    Args:
        baseline: boolean, =True if baseline tax policy, =False if reform
        start_year: integer, first year of budget window
        reform: dictionary, reform parameters

    Returns:
        individual_rates: dictionary, individual income (IIT+payroll)
                          marginal tax rates
    '''

    calc1 = get_calculator(baseline=baseline,
                           calculator_start_year=start_year,
                           reform=reform, data=data)

    # running all the functions and calculates taxes
    calc1.calc_all()

    # Loop over years in window of calculations
    end_year = start_year
    tau_nc = np.zeros(end_year - start_year + 1)
    tau_div = np.zeros_like(tau_nc)
    tau_int = np.zeros_like(tau_nc)
    tau_scg = np.zeros_like(tau_nc)
    tau_lcg = np.zeros_like(tau_nc)
    tau_td = np.zeros_like(tau_nc)
    tau_h = np.zeros_like(tau_nc)
    for year in range(start_year, end_year + 1):
        calc1.advance_to_year(year)
        print('year: ', str(calc1.current_year))
        # get mtrs
        # sch c
        [mtr_fica_schC, mtr_iit_schC, mtr_combined_schC] =\
            calc1.mtr('e00900p')
        # sch e (not s corp or partnership)
        [mtr_fica_schE, mtr_iit_schE, mtr_combined_schE] =\
            calc1.mtr('e02000')
        # Partnership and s corp income
        [mtr_fica_PT, mtr_iit_PT, mtr_combined_PT] = calc1.mtr('e26270')
        # dividends
        [mtr_fica_div, mtr_iit_div, mtr_combined_div] =\
            calc1.mtr('e00650')
        # interest income
        # taxable
        [mtr_fica_int, mtr_iit_int, mtr_combined_int] =\
            calc1.mtr('e00300')
        # non-taxable
        [mtr_fica_int_te, mtr_iit_int_te, mtr_combined_int_te] =\
            calc1.mtr('e00400')
        # short term capital gains
        [mtr_fica_scg, mtr_iit_scg, mtr_combined_scg] =\
            calc1.mtr('p22250')
        # long term capital gains
        [mtr_fica_lcg, mtr_iit_lcg, mtr_combined_lcg] =\
            calc1.mtr('p23250')

        # pension distributions
        # does PUF have e01500?  Do we want IRA distributions here?
        # Weird - I see e01500 in PUF, but error when try to call it
        [mtr_fica_pension, mtr_iit_pension, mtr_combined_pension] =\
            calc1.mtr('e01700')
        # mortgage interest and property tax deductions
        # do we also want mtg ins premiums here?
        # mtg interest
        [mtr_fica_mtg, mtr_iit_mtg, mtr_combined_mtg] =\
            calc1.mtr('e19200')
        # prop tax
        [mtr_fica_prop, mtr_iit_prop, mtr_combined_prop] =\
            calc1.mtr('e18500')
        pos_ti = calc1.array("c04800") > 0
        tau_nc[year - start_year] = (
            (((mtr_iit_schC * np.abs(calc1.array("e00900p"))) +
              (mtr_iit_schE * np.abs(calc1.array("e02000") -
                                     calc1.array("e26270")))
              + (mtr_iit_PT * np.abs(calc1.array("e26270")))) *
             pos_ti * calc1.array("s006")).sum() /
            ((np.abs(calc1.array("e00900p")) +
              np.abs(calc1.array("e02000") - calc1.array("e26270")) +
              np.abs(calc1.array("e26270"))) *
             pos_ti * calc1.array("s006")).sum())
        tau_div[year - start_year] = (
            (mtr_iit_div * calc1.array("e00650") * pos_ti *
             calc1.array("s006")).sum() /
            (calc1.array("e00650") * pos_ti *
             calc1.array("s006")).sum())
        tau_int[year - start_year] = (
            (mtr_iit_int * calc1.array("e00300") * pos_ti *
             calc1.array("s006")).sum() /
            (calc1.array("e00300") * pos_ti *
             calc1.array("s006")).sum())
        tau_scg[year - start_year] = (
            (mtr_iit_scg * np.abs(calc1.array("p22250")) *
             (calc1.array("p22250") > 0.) * pos_ti *
             calc1.array("s006")).sum() /
            (np.abs(calc1.array("p22250")) *
             (calc1.array("p22250") > 0.) * pos_ti *
             calc1.array("s006")).sum())
        tau_lcg[year - start_year] = (
            (mtr_iit_lcg * np.abs(calc1.array("p23250")) *
             (calc1.array("p23250") > 0.) * pos_ti *
             calc1.array("s006")).sum() /
            (np.abs(calc1.array("p23250")) *
             (calc1.array("p23250") > 0.) * pos_ti *
             calc1.array("s006")).sum())
        tau_td[year - start_year] = (
            (mtr_iit_pension * calc1.array("e01500") * pos_ti *
             calc1.array("s006")).sum() /
            (calc1.array("e01500") * pos_ti *
             calc1.array("s006")).sum())
        tau_h[year - start_year] = -1 * (
            ((mtr_iit_mtg * calc1.array("e19200")) +
             (mtr_iit_prop * calc1.array("e18500")) * pos_ti *
             calc1.array("s006")).sum() / (
                 (calc1.array("e19200")) + (calc1.array("e18500")) *
                 pos_ti * calc1.array("s006")).sum())

    individual_rates = {'tau_nc': tau_nc, 'tau_div': tau_div,
                        'tau_int': tau_int, 'tau_scg': tau_scg,
                        'tau_lcg': tau_lcg, 'tau_td': tau_td,
                        'tau_h': tau_h}
    print(individual_rates)
    return individual_rates
