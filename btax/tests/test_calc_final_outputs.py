import pandas as pd
import numpy as np
import pytest
from pandas.testing import assert_frame_equal
from btax import calc_final_outputs


def test_cost_of_capital():
    # Test cost of capital calculation
    df = pd.DataFrame(
        {'Asset Type': ['Inventories', 'Autos'],
         'delta': [0.0, 0.1],
         'z_c': [0.0, 0.1],
         'z_c_d': [0.5, 0.5],
         'z_c_e': [0.6, 0.55556],
         'z_nc': [1.0, 0.0],
         'z_nc_d': [0.1, 1.0],
         'z_nc_e': [0.9, 0.8]})
    discount_rate = np.array([[0.05, 0.06], [0.04, .03], [0.11, 0.12]])
    inflation_rate = 0.03
    financing_list = ['', '_d', '_e']
    entity_list = ['_c', '_nc']
    expense_inventory = True
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
        {'Asset Type': ['Inventories', 'Autos'],
         'delta': [0.0, 0.1],
         'z_c': [0.0, 0.1],
         'z_c_d': [0.5, 0.5],
         'z_c_e': [0.6, 0.55556],
         'z_nc': [1.0, 0.0],
         'z_nc_d': [0.1, 1.0],
         'z_nc_e': [0.9, 0.8],
         'rho_c': [0.028571, 0.066286],
         'rho_c_d': [0.012143, 0.033571],
         'rho_c_e': [0.093714, 0.114285],
         'rho_nc': [0.03, 0.03],
         'rho_nc_d': [0, 0],
         'rho_nc_e': [0.09, 0.09],
         'ucc_c': [0.028571, 0.166286],
         'ucc_c_d': [0.012143, 0.133571],
         'ucc_c_e': [0.093714, 0.214285],
         'ucc_nc': [0.03, 0.13],
         'ucc_nc_d': [0, 0.1],
         'ucc_nc_e': [0.09, 0.19]})
    correct_df = correct_df[['Asset Type', 'delta', 'z_c', 'z_c_d',
                             'z_c_e', 'z_nc', 'z_nc_d', 'z_nc_e',
                             'rho_c', 'ucc_c', 'rho_nc', 'ucc_nc',
                             'rho_c_d', 'ucc_c_d', 'rho_nc_d',
                             'ucc_nc_d', 'rho_c_e', 'ucc_c_e',
                             'rho_nc_e', 'ucc_nc_e']]

    assert_frame_equal(test_df, correct_df, check_dtype=False,
                       check_less_precise=True)


def test_metr():

    assert_frame_equal(test_df, correct_df, check_dtype=False)


def test_asset_calcs():

    assert_frame_equal(test_df, correct_df, check_dtype=False)


def test_industry_calcs():

    assert_frame_equal(test_df, correct_df, check_dtype=False)
