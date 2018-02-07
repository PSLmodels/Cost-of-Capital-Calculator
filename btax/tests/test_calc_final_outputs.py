import pandas as pd
import numpy as np
import pytest
from pandas.testing import assert_frame_equal
from btax import calc_final_outputs

correct_df0 = pd.DataFrame(
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
correct_df1 = pd.DataFrame(
    {'Asset Type': ['Inventories', 'Autos'],
     'delta': [0.0, 0.1],
     'z_c': [0.0, 0.1],
     'z_c_d': [0.5, 0.5],
     'z_c_e': [0.6, 0.55556],
     'z_nc': [1.0, 0.0],
     'z_nc_d': [0.1, 1.0],
     'z_nc_e': [0.9, 0.8],
     'rho_c': [0.033055, 0.066286],
     'rho_c_d': [0.019550, 0.033571],
     'rho_c_e': [0.109878, 0.114285],
     'rho_nc': [0.03, 0.03],
     'rho_nc_d': [0, 0],
     'rho_nc_e': [0.09, 0.09],
     'ucc_c': [0.033055, 0.166286],
     'ucc_c_d': [0.019550, 0.133571],
     'ucc_c_e': [0.109878, 0.214285],
     'ucc_nc': [0.03, 0.13],
     'ucc_nc_d': [0, 0.1],
     'ucc_nc_e': [0.09, 0.19]})
correct_df2 = pd.DataFrame(
    {'Asset Type': ['Inventories', 'Autos'],
     'delta': [0.0, 0.1],
     'z_c': [0.0, 0.1],
     'z_c_d': [0.5, 0.5],
     'z_c_e': [0.6, 0.55556],
     'z_nc': [1.0, 0.0],
     'z_nc_d': [0.1, 1.0],
     'z_nc_e': [0.9, 0.8],
     'rho_c': [0.042780, 0.075286],
     'rho_c_d': [0.029723, 0.042000],
     'rho_c_e': [0.115883, 0.114476],
     'rho_nc': [0.0400, 0.0388],
     'rho_nc_d': [0.0100, 0.0112],
     'rho_nc_e': [0.100, 0.094],
     'ucc_c': [0.042780, 0.175286],
     'ucc_c_d': [0.029723, 0.142000],
     'ucc_c_e': [0.115883, 0.214476],
     'ucc_nc': [0.0400, 0.1388],
     'ucc_nc_d': [0.0100, 0.1112],
     'ucc_nc_e': [0.100, 0.194]})
test_data = [((True, 0.03, 0.0, 0.0, 0.5, 5), correct_df0),
             ((False, 0.03, 0.0, 0.0, 0.5, 5), correct_df1),
             ((False, 0.02, 0.08, 0.01, 0.33, 8), correct_df2)]
@pytest.mark.parametrize('changing_params,expected', test_data,
                         ids=['Test 0', 'Test 1', 'Test 2'])
def test_cost_of_capital(changing_params, expected):
    expense_inventory, inflation_rate, inv_credit, w, phi, Y_v = changing_params
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
    financing_list = ['', '_d', '_e']
    entity_list = ['_c', '_nc']
    stat_tax = np.array([0.3, 0.0])
    # expense_inventory = False
    # inflation_rate = 0.02
    # inv_credit = 0.08
    # w = 0.01
    # phi = 0.33
    # Y_v = 8
    test_df = calc_final_outputs.cost_of_capital(
        df, w, expense_inventory, stat_tax, inv_credit, phi, Y_v,
        inflation_rate, discount_rate, entity_list,
        financing_list
        )

    expected = expected[['Asset Type', 'delta', 'z_c', 'z_c_d', 'z_c_e',
                         'z_nc', 'z_nc_d', 'z_nc_e', 'rho_c', 'ucc_c',
                         'rho_nc', 'ucc_nc', 'rho_c_d', 'ucc_c_d',
                         'rho_nc_d', 'ucc_nc_d', 'rho_c_e', 'ucc_c_e',
                         'rho_nc_e', 'ucc_nc_e']]

    assert_frame_equal(test_df, expected, check_dtype=False,
                       check_less_precise=True)


# def test_metr():
#
#     assert_frame_equal(test_df, correct_df, check_dtype=False)
#
#
# def test_asset_calcs():
#
#     assert_frame_equal(test_df, correct_df, check_dtype=False)
#
#
# def test_industry_calcs():
#
#     assert_frame_equal(test_df, correct_df, check_dtype=False)
