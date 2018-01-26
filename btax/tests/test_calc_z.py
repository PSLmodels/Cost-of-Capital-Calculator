import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
import pytest
from btax import calc_z


def test_get_econ_depr():
    # Test retreiving econ depreciation from file
    assert


def test_calc_tax_depr_rates():

    assert


def test_npv_tax_deprec():

    assert


def test_dbsl():
    # Test computing declining balance with switch to straight line
    assert


def test_sl():
    # Test straight line deprecition
    assert


def test_econ():
    # Test economic depreciation
    df = pd.DataFrame({'Asset': ['Land', 'Inventories', 'IP', 'Structures',
                                 'Equipment'],
                       'Amount': [1000, 500, 100, 200, 200],
                       'bonus': [0.0, 0.0, 0.4, 1.0, 1.2],
                       'delta': [0.01, 0.1, 0.1, 0.02, 0.1]})
    r = np.array([[0.05, 0.06], [0.04, .03], [0.11, 0.12]])
    pi = 0.03
    financing_list = ['', '_d', '_e']
    entity_list = ['_c', '_nc']

    test_exp_df = calc_z.econ(df, r, pi, financing_list, entity_list)

    results_df = pd.DataFrame({'Asset': ['Land', 'Inventories', 'IP', 'Structures',
                                         'Equipment'],
                               'Amount': [1000, 500, 100, 200, 200],
                               'bonus': [0.0, 0.0, 0.4, 1.0, 1.2],
                               'delta': [0.01, 0.1, 0.1, 0.02, 0.1],
                               'z_c': [0.333333333, 0.833333333, 0.9, 1.0, 1.033333333],
                               'z_c_d': [0.5, 0.909090909, 0.945454545, 1.0, 1.018181818],
                               'z_c_e': [0.111111111, 0.555555556, 0.733333333, 1.0, 1.088888889],
                               'z_nc': [0.25, 0.769230769, 0.861538462, 1.0, 1.046153846],
                               'z_nc_d': [1.0, 1.0, 1.0, 1.0, 1.0],
                               'z_nc_e': [0.1, 0.526315789, 0.715789474, 1.0, 1.094736842]})
    results_df = results_df[['Amount', 'Asset', 'bonus', 'delta', 'z_c', 'z_nc', 'z_c_d',
                             'z_nc_d', 'z_c_e', 'z_nc_e']]

    assert_frame_equal(test_exp_df, results_df, check_dtype=False)


def test_expensing():
    # Test expensing
    df = pd.DataFrame({'Asset': ['Land'], 'Amount': [1000]})
    r = np.array([[0.08, 0.07], [0.4, .3], [0.01, 0.02]])
    financing_list = ['', '_d', '_e']
    entity_list = ['_c', '_nc']

    test_exp_df = calc_z.expensing(df, r, financing_list, entity_list)

    results_df = pd.DataFrame({'Asset': ['Land'], 'Amount': [1000],
                               'z_c': [1.0], 'z_c_d': [1.0],
                               'z_c_e': [1.0], 'z_nc': [1.0],
                               'z_nc_d': [1.0], 'z_nc_e': [1.0]})
    results_df = results_df[['Amount', 'Asset', 'z_c', 'z_nc', 'z_c_d',
                             'z_nc_d', 'z_c_e', 'z_nc_e']]

    assert_frame_equal(test_exp_df, results_df, check_dtype=False)
