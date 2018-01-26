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
    assert


def test_expensing():
    # Test expensing
    df = pd.DataFrame({'Asset': ['Land'], 'Amount': [1000]})
    r = np.array([[0.5, 0.4], [1, 1], [0, 0]])
    financing_list = ['', '_d', '_e']
    entity_list = ['_c', '_nc']

    test_exp_df = cal_z.expensing(df, r, financing_list, entity_list)

    results_df = pd.DataFrame({'Asset': ['Land'], 'Amount': [1000]})
    for i in range(r.shape[0]):
        for j in range(r.shape[1]):
            results_df['z' + entity_list[j] + financing_list[i]] = 1.0

    assert_frame_equal(test_exp_df, results_df, check_dtype=False)
