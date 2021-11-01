# imports
import numpy as np
from taxcalc import Policy, Records, Calculator
from ccc.utils import DEFAULT_START_YEAR, TC_LAST_YEAR, RECORDS_START_YEAR


def get_calculator(baseline, calculator_start_year, reform=None,
                   data='cps', gfactors=None, weights=None,
                   records_start_year=RECORDS_START_YEAR):
    '''
    This function creates the tax calculator object for the microsim

    Args:
        baseline (bool): `True` if baseline tax policy
        calculator_start_year (integer): first year of budget window
        reform (dictionary): IIT reform parameters
        data (string or Pandas DataFrame): path to file or DataFrame
            for Tax-Calculator Records object (optional)
        weights (DataFrame): weights DataFrame for Tax-Calculator
            Records object (optional)
        records_start_year (integer): the start year for the data and
            weights dfs

    Returns:
        calc1 (Tax Calculator Calculator object): TC Calculator object
            with a current_year equal to calculator_start_year
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
    elif data is not None:  # pragma: no cover
        records1 = Records(
            data=data, gfactors=gfactors, weights=weights,
            start_year=records_start_year)  # pragma: no cover
    else:
        records1 = Records()  # pragma: no cover

    if baseline:
        # Should not be a reform if baseline is True
        assert not reform

    if not baseline:
        update_policy(policy1, reform)

    # the default set up increments year to 2013
    calc1 = Calculator(records=records1, policy=policy1)
    print('Calculator initial year = ', calc1.current_year)

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
        baseline (bool): `True` if baseline tax policy, `False` if reform
        start_year (integer): first year of budget window
        reform (dict): reform parameters

    Returns:
        individual_rates (dict): individual income (IIT+payroll)
            marginal tax rates

    '''
    calc1 = get_calculator(baseline=baseline,
                           calculator_start_year=start_year,
                           reform=reform, data=data)

    # running all the functions and calculates taxes
    calc1.calc_all()

    # Loop over years in window of calculations
    end_year = start_year
    array_size = end_year - start_year + 1
    rates_dict = {'tau_div': 'e00650', 'tau_int': 'e00300',
                  'tau_scg': 'p22250', 'tau_lcg': 'p23250'}
    individual_rates = {
        'tau_pt': np.zeros(array_size), 'tau_div': np.zeros(array_size),
        'tau_int': np.zeros(array_size), 'tau_scg': np.zeros(array_size),
        'tau_lcg': np.zeros(array_size), 'tau_td': np.zeros(array_size),
        'tau_h': np.zeros(array_size)}
    for year in range(start_year, end_year + 1):
        print('Calculator year = ', calc1.current_year)
        calc1.advance_to_year(year)
        print('year: ', str(calc1.current_year))
        # Compute mtrs
        # Sch C
        [mtr_fica_schC, mtr_iit_schC, mtr_combined_schC] =\
            calc1.mtr('e00900p')
        # Sch E  - includes partnership and s corp income
        [mtr_fica_schE, mtr_iit_schE, mtr_combined_schE] =\
            calc1.mtr('e02000')
        # Partnership and s corp income
        [mtr_fica_PT, mtr_iit_PT, mtr_combined_PT] = calc1.mtr('e26270')
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
        individual_rates['tau_pt'][year - start_year] = (
            (((mtr_iit_schC * np.abs(calc1.array("e00900p"))) +
              (mtr_iit_schE * np.abs(calc1.array("e02000") -
                                     calc1.array("e26270"))) +
              (mtr_iit_PT * np.abs(calc1.array("e26270")))) *
             pos_ti * calc1.array("s006")).sum() /
            ((np.abs(calc1.array("e00900p")) +
              np.abs(calc1.array("e02000") - calc1.array("e26270")) +
              np.abs(calc1.array("e26270"))) *
             pos_ti * calc1.array("s006")).sum())
        individual_rates['tau_td'][year - start_year] = (
            (mtr_iit_pension * calc1.array("e01500") * pos_ti *
             calc1.array("s006")).sum() /
            (calc1.array("e01500") * pos_ti *
             calc1.array("s006")).sum())
        individual_rates['tau_h'][year - start_year] = -1 * (
            ((mtr_iit_mtg * calc1.array("e19200")) +
             (mtr_iit_prop * calc1.array("e18500")) * pos_ti *
             calc1.array("s006")).sum() / (
                 (calc1.array("e19200")) + (calc1.array("e18500")) *
                 pos_ti * calc1.array("s006")).sum())
        # Loop over MTRs that have only one income source
        for k, v in rates_dict.items():
            [mtr_fica, mtr_iit, mtr_combined] = calc1.mtr(v)
            individual_rates[k][year - start_year] = (
                (mtr_iit * calc1.array(v) * pos_ti *
                 calc1.array("s006")).sum() /
                (calc1.array(v) * pos_ti * calc1.array("s006")).sum())

    print(individual_rates)
    return individual_rates


def update_policy(policy_obj, reform, **kwargs):
    """
    Convenience method that updates the Policy object with the reform
    dict using the appropriate method, given the reform format.
    """
    if is_paramtools_format(reform):
        policy_obj.adjust(reform, **kwargs)
    else:
        policy_obj.implement_reform(reform, **kwargs)


def is_paramtools_format(reform):
    """
    Check first item in reform to determine if it is using the ParamTools
    adjustment or the Tax-Calculator reform format.
    If first item is a dict, then it is likely be a Tax-Calculator reform:
    {
        param: {2020: 1000}
    }
    Otherwise, it is likely to be a ParamTools format.
    Returns:
        format (bool): True if reform is likely to be in PT format.
    """
    for _, data in reform.items():
        if isinstance(data, dict):
            return False  # taxcalc reform
        else:
            # Not doing a specific check to see if the value is a list
            # since it could be a list or just a scalar value.
            return True
