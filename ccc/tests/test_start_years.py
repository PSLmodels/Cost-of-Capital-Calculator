import pytest
import numpy as np
from ccc.parameters import Specification
from ccc.get_taxcalc_rates import get_rates


@pytest.mark.parametrize(
        'year',
        [2014, 2015, 2017, 2027],
        ids=['2014', '2015', '2017', '2027'])
def test_tc_start_year(year):
    '''
    Test that different start years work in functions calling
    Tax-Calculator
    '''
    get_rates(True, year)


@pytest.mark.parametrize(
        'year,expected_values',
        [(2014, [0.35, 0.5, 0.5]), (2015, [0.35, 0.5, 0.5]),
         (2017, [0.35, 0.5, 0.5]), (2026, [0.21, 0.2, 0.5]),
         (2027, [0.21, 0.0, 0.5])],
        ids=['2014', '2015', '2017', '2026', '2027'])
def test_params_start_year(year, expected_values):
    '''
    Test that different start years return the expected parameter values
    as specificed in the default_parameters.json file.
    '''
    p = Specification(year=year)
    assert(np.allclose(p.u['c'], expected_values[0]))
    assert(np.allclose(p.bonus_deprec['3'], expected_values[1]))
    assert(np.allclose(p.phi, expected_values[2]))
