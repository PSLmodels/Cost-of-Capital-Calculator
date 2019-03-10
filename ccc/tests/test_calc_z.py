import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
import pytest
from ccc import calc_z


def test_get_econ_depr():
    # Test retreiving econ depreciation from file
    test_df = calc_z.get_econ_depr()
    # Keep a few assets only
    asset_list = ['Land', 'Inventories',
                  'Scientific research and development services',
                  'Hospitals', 'Autos']
    test_df = test_df[test_df['Asset'].isin(asset_list)]
    test_df.reset_index(drop=True, inplace=True)

    correct_df = pd.DataFrame(
        {'Asset': ['Autos', 'Hospitals',
                   'Scientific research and development services',
                   'Land', 'Inventories'],
         'delta': [0.3333, 0.0188, 0.16, 0.0, 0.0],
         'bea_asset_code': ['ET20', 'SB31', 'RD70', 'LAND', 'INV']})
    correct_df = correct_df[['bea_asset_code', 'Asset', 'delta']]

    assert_frame_equal(
        test_df.reindex(sorted(test_df.columns), axis=1),
        correct_df.reindex(sorted(correct_df.columns), axis=1),
        check_dtype=False)


def test_calc_tax_depr_rates():
    # Test creation of df with tax depreciation rates
    delta = pd.DataFrame(
        {'Asset': ['Land', 'Inventories',
                   'Scientific research and development services',
                   'Hospitals', 'Autos'],
         'Amount': [1000, 500, 100, 200, 200],
         'bea_asset_code': ['LAND', 'INV', 'RD70', 'SB31', 'ET20'],
         'delta': [0.01, 0.1, 0.1, 0.02, 0.1]})
    r = np.array([[0.05, 0.06], [0.04, .03], [0.11, 0.12]])
    pi = 0.03
    tax_methods = {'DB 200%': 2.0, 'DB 150%': 1.5, 'SL': 1.0,
                   'Economic': 1.0, 'Expensing': 1.0}
    financing_list = ['', '_d', '_e']
    entity_list = ['_c', '_nc']
    bonus_deprec = {'10': 0.0, '15': 0.0, '20': 0.0, '25': 0.0,
                    '27_5': 0.0, '3': 0.0, '39': 0.2, '5': 0.5,
                    '7': 0.0, '100': 0.0}
    deprec_system = {'10': 'GDS', '15': 'GDS', '20': 'GDS', '25': 'GDS',
                     '27_5': 'GDS', '3': 'GDS', '39': 'GDS', '5': 'GDS',
                     '7': 'GDS', '100': 'GDS'}
    expense_inventory = False
    expense_land = 0.0
    test_df =\
        calc_z.calc_tax_depr_rates(r, pi, delta, bonus_deprec,
                                   deprec_system, expense_inventory,
                                   expense_land, tax_methods,
                                   financing_list, entity_list)
    # Keep just assets put in dummy data above
    asset_list = ['Land', 'Inventories',
                  'Scientific research and development services',
                  'Hospitals', 'Autos']
    test_df = test_df[test_df['Asset'].isin(asset_list)]
    test_df.reset_index(drop=True, inplace=True)

    # Dataframe of what results should be
    correct_df = pd.DataFrame(
        {'Asset': ['Autos', 'Hospitals', 'Land', 'Inventories',
                   'Scientific research and development services'],
         'Asset Type': ['Autos', 'Hospitals', 'Land', 'Inventories',
                        'Scientific research and development services'],
         'Amount': [200, 200, 1000, 500, 100],
         'bonus': [0.5, 0.2, 0.0, 0.0, 0.5],
         'delta': [0.1, 0.02, 0.01, 0.1, 0.1],
         'ADS Life': [5, 40, 100, 100, 6],
         'GDS Life': [5, 39, 100, 100, 5],
         'GDS Class Life': [5, 39, 100, 100, 5],
         'System': ['GDS', 'GDS', 'GDS', 'GDS', 'GDS'],
         'bea_asset_code': ['ET20', 'SB31', 'LAND', 'INV', 'RD70'],
         'Method': ['DB 200%', 'SL', 'SL', 'SL', 'Expensing'],
         'b': [2.0, 1.0, 1.0, 1.0, 1.0],
         'z_c': [0.952745, 0.545866, 0.000000, 0.000000, 1.000000],
         'z_c_d': [0.961625, 0.599052, 0.0, 0.0, 1.0],
         'z_c_e': [0.904727, 0.379586, 0.0, 0.0, 1.0],
         'z_nc': [0.944131, 0.503094, 0.0, 0.0, 1.0],
         'z_nc_d': [0.970780, 0.665871, 0.0, 0.0, 1.0],
         'z_nc_e': [0.897521, 0.365295, 0.0, 0.0, 1.0]})
    correct_df = correct_df[['Asset Type', 'GDS Class Life', 'GDS Life',
                             'ADS Life', 'System', 'Method', 'bonus',
                             'Amount', 'Asset', 'bea_asset_code',
                             'delta', 'b', 'z_c', 'z_nc', 'z_c_d',
                             'z_nc_d', 'z_c_e', 'z_nc_e']]

    assert_frame_equal(
        test_df.reindex(sorted(test_df.columns), axis=1),
        correct_df.reindex(sorted(correct_df.columns), axis=1),
        check_dtype=False)

    # Test with expensing of land and inventories
    expense_inventory = True
    expense_land = 1.0
    test_df = calc_z.calc_tax_depr_rates(
        r, pi, delta, bonus_deprec, deprec_system, expense_inventory,
        expense_land, tax_methods, financing_list, entity_list)
    # Keep just assets put in dummy data above
    asset_list = ['Land', 'Inventories',
                  'Scientific research and development services',
                  'Hospitals', 'Autos']
    test_df = test_df[test_df['Asset'].isin(asset_list)]
    test_df.reset_index(drop=True, inplace=True)

    # Dataframe of what results should be
    correct_df = pd.DataFrame(
        {'Asset': ['Autos', 'Hospitals', 'Land', 'Inventories',
                   'Scientific research and development services'],
         'Asset Type': ['Autos', 'Hospitals', 'Land', 'Inventories',
                        'Scientific research and development services'],
         'Amount': [200, 200, 1000, 500, 100],
         'bonus': [0.5, 0.2, 0.0, 0.0, 0.5],
         'delta': [0.1, 0.02, 0.01, 0.1, 0.1],
         'ADS Life': [5, 40, 100, 100, 6],
         'GDS Life': [5, 39, 100, 100, 5],
         'GDS Class Life': [5, 39, 100, 100, 5],
         'System': ['GDS', 'GDS', 'GDS', 'GDS', 'GDS'],
         'bea_asset_code': ['ET20', 'SB31', 'LAND', 'INV', 'RD70'],
         'Method': ['DB 200%', 'SL', 'SL', 'SL', 'Expensing'],
         'b': [2.0, 1.0, 1.0, 1.0, 1.0],
         'z_c': [0.952745, 0.545866, 1.0, 1.0, 1.000000],
         'z_c_d': [0.961625, 0.599052, 1.0, 1.0, 1.0],
         'z_c_e': [0.904727, 0.379586, 1.0, 1.0, 1.0],
         'z_nc': [0.944131, 0.503094, 1.0, 1.0, 1.0],
         'z_nc_d': [0.970780, 0.665871, 1.0, 1.0, 1.0],
         'z_nc_e': [0.897521, 0.365295, 1.0, 1.0, 1.0]})
    correct_df = correct_df[['Asset Type', 'GDS Class Life', 'GDS Life',
                             'ADS Life', 'System', 'Method', 'bonus',
                             'Amount', 'Asset', 'bea_asset_code',
                             'delta', 'b', 'z_c', 'z_nc', 'z_c_d',
                             'z_nc_d', 'z_c_e', 'z_nc_e']]

    assert_frame_equal(
        test_df.reindex(sorted(test_df.columns), axis=1),
        correct_df.reindex(sorted(correct_df.columns), axis=1),
        check_dtype=False)


def test_npv_tax_deprec():
    # Test created of df with NPV of tax depreciation
    df = pd.DataFrame(
        {'Asset': ['Land', 'Inventories', 'IP', 'Structures',
                   'Equipment'],
         'Amount': [1000, 500, 100, 200, 200],
         'bonus': [0.0, 0.0, 0.4, 1.0, 0.9],
         'delta': [0.01, 0.1, 0.1, 0.02, 0.1],
         'ADS Life': [40, 1, 10, 20, 8],
         'GDS Life': [40, 3, 10, 20, 8],
         'Method': ['DB 200%', 'DB 150%', 'SL', 'Expensing',
                    'Economic']})
    r = np.array([[0.05, 0.06], [0.04, .03], [0.11, 0.12]])
    pi = 0.03
    tax_methods = {'DB 200%': 2.0, 'DB 150%': 1.5, 'SL': 1.0,
                   'Economic': 1.0, 'Expensing': 1.0}
    financing_list = ['', '_d', '_e']
    entity_list = ['_c', '_nc']
    test_df = calc_z.npv_tax_deprec(df, r, pi, tax_methods,
                                    financing_list, entity_list)

    correct_df = pd.DataFrame(
        {'Asset': ['Land', 'Inventories', 'IP', 'Equipment',
                   'Structures'],
         'Amount': [1000, 500, 100, 200, 200],
         'bonus': [0.0, 0.0, 0.4, 0.9, 1.0],
         'delta': [0.01, 0.1, 0.1, 0.1, 0.02],
         'ADS Life': [40, 1, 10, 8, 20],
         'GDS Life': [40, 3, 10, 8, 20],
         'Method': ['DB 200%', 'DB 150%', 'SL', 'Economic',
                    'Expensing'],
         'b': [2.0, 1.5, 1.0, 1.0, 1.0],
         'z_c': [0.517881, 0.933631, 0.872163, 0.983333, 1.0],
         'z_c_d': [0.577504, 0.946392, 0.894520, 0.990909, 1.0],
         'z_c_e': [0.316237, 0.862037, 0.763888, 0.955556, 1.0],
         'z_nc': [0.468705, 0.921116, 0.851188, 0.976923, 1.0],
         'z_nc_d': [0.650637, 0.959403, 0.918364, 1.0, 1.0],
         'z_nc_e': [0.296946, 0.850885, 0.749403, 0.952632, 1.0]})
    correct_df = correct_df[['ADS Life', 'Amount', 'Asset', 'GDS Life',
                             'Method', 'bonus', 'delta', 'b', 'z_c',
                             'z_nc', 'z_c_d', 'z_nc_d', 'z_c_e',
                             'z_nc_e']]

    assert_frame_equal(
        test_df.reindex(sorted(test_df.columns), axis=1),
        correct_df.reindex(sorted(correct_df.columns), axis=1),
        check_dtype=False)


def test_dbsl():
    # Test computing declining balance with switch to straight line
    df = pd.DataFrame(
        {'Asset': ['Land', 'Inventories', 'IP', 'Structures',
                   'Equipment'],
         'Amount': [1000, 500, 100, 200, 200],
         'bonus': [0.0, 0.0, 0.4, 1.0, 0.9],
         'GDS Life': [40, 3, 10, 20, 8],
         'b': [1.2, 1.0, 1.5, 2.0, 1.8]})
    r = np.array([[0.05, 0.06], [0.04, .03], [0.11, 0.12]])
    financing_list = ['', '_d', '_e']
    entity_list = ['_c', '_nc']

    test_df = calc_z.dbsl(df, r, financing_list, entity_list)

    correct_df = pd.DataFrame(
        {'Asset': ['Land', 'Inventories', 'IP', 'Structures',
                   'Equipment'],
         'Amount': [1000, 500, 100, 200, 200],
         'bonus': [0.0, 0.0, 0.4, 1.0, 0.9],
         'GDS Life': [40, 3, 10, 20, 8],
         'b': [1.2, 1.0, 1.5, 2.0, 1.8],
         'z_c': [0.440513504372, 0.9286134905, 0.880930116585, 1.0,
                 0.984770923379],
         'z_c_d': [0.506162, 0.942330, 0.901805, 1.0, 0.987521],
         'z_c_e': [0.234526, 0.851746, 0.779383, 1.0, 0.970790],
         'z_nc': [0.387665, 0.91516549216, 0.861320485658, 1.0,
                  0.982153],
         'z_nc_d': [0.588563, 0.956320163653, 0.924042197883, 1.0,
                    0.990410],
         'z_nc_e': [0.216709485309, 0.839787983136, 0.765724715186, 1.0,
                    0.968820618024]})
    correct_df = correct_df[['Amount', 'Asset', 'GDS Life', 'b',
                             'bonus', 'z_c', 'z_nc', 'z_c_d', 'z_nc_d',
                             'z_c_e', 'z_nc_e']]

    assert_frame_equal(
        test_df.reindex(sorted(test_df.columns), axis=1),
        correct_df.reindex(sorted(correct_df.columns), axis=1),
        check_dtype=False)


def test_sl():
    # Test straight line deprecition
    df = pd.DataFrame(
        {'Asset': ['Land', 'Inventories', 'IP', 'Structures',
                   'Equipment'],
         'Amount': [1000, 500, 100, 200, 200],
         'bonus': [0.0, 0.0, 0.4, 1.0, 1.2],
         'ADS Life': [40, 1, 10, 20, 8]})
    r = np.array([[0.05, 0.06], [0.04, .03], [0.11, 0.12]])
    financing_list = ['', '_d', '_e']
    entity_list = ['_c', '_nc']

    test_df = calc_z.sl(df, r, financing_list, entity_list)

    correct_df = pd.DataFrame(
        {'Asset': ['Land', 'Inventories', 'IP', 'Structures',
                   'Equipment'],
         'Amount': [1000, 500, 100, 200, 200],
         'bonus': [0.0, 0.0, 0.4, 1.0, 1.2],
         'ADS Life': [40, 1, 10, 20, 8],
         'z_c': [0.432332358, 0.97541151, 0.872163208, 1.0,
                 1.035160023],
         'z_c_d': [0.498814676, 0.980264021, 0.894519931, 1.0,
                   1.028843148],
         'z_c_e': [0.224482423, 0.946962406, 0.7638885, 1.0,
                   1.066996116],
         'z_nc': [0.378867519, 0.970591107, 0.851188364, 1.0,
                  1.041159747],
         'z_nc_d': [0.582338157, 0.985148882, 0.918363559, 1.0,
                    1.022189884],
         'z_nc_e': [0.206618803, 0.942329694, 0.749402894, 1.0,
                    1.071436018]})
    correct_df = correct_df[['ADS Life', 'Amount', 'Asset', 'bonus',
                             'z_c', 'z_nc', 'z_c_d', 'z_nc_d', 'z_c_e',
                             'z_nc_e']]

    assert_frame_equal(
        test_df.reindex(sorted(test_df.columns), axis=1),
        correct_df.reindex(sorted(correct_df.columns), axis=1),
        check_dtype=False)


def test_econ():
    # Test economic depreciation
    df = pd.DataFrame(
        {'Asset': ['Land', 'Inventories', 'IP', 'Structures',
                   'Equipment'],
         'Amount': [1000, 500, 100, 200, 200],
         'bonus': [0.0, 0.0, 0.4, 1.0, 1.2],
         'delta': [0.01, 0.1, 0.1, 0.02, 0.1]})
    r = np.array([[0.05, 0.06], [0.04, .03], [0.11, 0.12]])
    pi = 0.03
    financing_list = ['', '_d', '_e']
    entity_list = ['_c', '_nc']

    test_df = calc_z.econ(df, r, pi, financing_list, entity_list)

    correct_df = pd.DataFrame(
        {'Asset': ['Land', 'Inventories', 'IP', 'Structures',
                   'Equipment'],
         'Amount': [1000, 500, 100, 200, 200],
         'bonus': [0.0, 0.0, 0.4, 1.0, 1.2],
         'delta': [0.01, 0.1, 0.1, 0.02, 0.1],
         'z_c': [0.333333333, 0.833333333, 0.9, 1.0, 1.033333333],
         'z_c_d': [0.5, 0.909090909, 0.945454545, 1.0, 1.018181818],
         'z_c_e': [0.111111111, 0.555555556, 0.733333333, 1.0,
                   1.088888889],
         'z_nc': [0.25, 0.769230769, 0.861538462, 1.0, 1.046153846],
         'z_nc_d': [1.0, 1.0, 1.0, 1.0, 1.0],
         'z_nc_e': [0.1, 0.526315789, 0.715789474, 1.0, 1.094736842]})
    correct_df = correct_df[['Amount', 'Asset', 'bonus', 'delta', 'z_c',
                             'z_nc', 'z_c_d', 'z_nc_d', 'z_c_e',
                             'z_nc_e']]

    assert_frame_equal(
        test_df.reindex(sorted(test_df.columns), axis=1),
        correct_df.reindex(sorted(correct_df.columns), axis=1),
        check_dtype=False)


def test_expensing():
    # Test expensing
    df = pd.DataFrame({'Asset': ['Land'], 'Amount': [1000]})
    r = np.array([[0.08, 0.07], [0.4, .3], [0.01, 0.02]])
    financing_list = ['', '_d', '_e']
    entity_list = ['_c', '_nc']

    test_df = calc_z.expensing(df, r, financing_list, entity_list)

    correct_df = pd.DataFrame({'Asset': ['Land'], 'Amount': [1000],
                               'z_c': [1.0], 'z_c_d': [1.0],
                               'z_c_e': [1.0], 'z_nc': [1.0],
                               'z_nc_d': [1.0], 'z_nc_e': [1.0]})
    correct_df = correct_df[['Amount', 'Asset', 'z_c', 'z_nc', 'z_c_d',
                             'z_nc_d', 'z_c_e', 'z_nc_e']]

    assert_frame_equal(
        test_df.reindex(sorted(test_df.columns), axis=1),
        correct_df.reindex(sorted(correct_df.columns), axis=1),
        check_dtype=False)
