import pandas as pd
import numpy as np
import pytest
from pandas.testing import assert_frame_equal
from btax import calc_final_outputs


def test_cost_of_capital():
    # Test cost of capital calculation
    df = pd.DataFrame(
        {'Asset': ['Land', 'Inventories',
                   'Scientific research and development services',
                   'Hospitals', 'Autos'],
         'delta': [0.01, 0.1, 0.1, 0.02, 0.1]})
    discount_rate = np.array([[0.05, 0.06], [0.04, .03], [0.11, 0.12]])
    inflation_rate = 0.03
    financing_list = ['', '_d', '_e']
    entity_list = ['_c', '_nc']
    expense_inventory = False
    stat_tax = np.array([0.3, 0.0])
    inv_credit = 0.0  # should do a pymark.parameterize over expense inventory, land, inv credit, w, phi, Y_v
    w = 0.0
    phi = 0.5
    Y_v = 5
    test_df = calc_final_outputs.cost_of_capital(
        df, w, expense_inventory, stat_tax, inv_credit, phi, Y_v,
        inflation_rate, discount_rate, entity_list,
        financing_list
        )

    correct_df = pd.DataFrame(
        {'Asset': ['Land', 'Inventories',
                   'Scientific research and development services',
                   'Hospitals', 'Autos'],
         'delta': [0.01, 0.1, 0.1, 0.02, 0.1],
         'rho_c': [],
         'rho_c_d': [],
         'rho_c_e': [],
         'rho_nc': [],
         'rho_nc_d': [],
         'rho_nc_e': []})
    correct_df = correct_df[['bea_asset_code', 'Asset', 'delta']]

    assert_frame_equal(test_df, correct_df, check_dtype=False)


def test_metr():

    assert_frame_equal(test_df, correct_df, check_dtype=False)


def test_asset_calcs():

    assert_frame_equal(test_df, correct_df, check_dtype=False)


def test_industry_calcs():

    assert_frame_equal(test_df, correct_df, check_dtype=False)
