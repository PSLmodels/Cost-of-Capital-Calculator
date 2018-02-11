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
# tuple of params in order: expense_inventory, inflation_rate,
# inv_credit, w, phi, Y_v
test_data = [((True, 0.03, 0.0, 0.0, 0.5, 5.), correct_df0),
             ((False, 0.03, 0.0, 0.0, 0.5, 5.), correct_df1),
             ((False, 0.02, 0.08, 0.01, 0.33, 8.), correct_df2)]


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


correct_df0 = pd.DataFrame(
    {'Asset Type': ['Inventories', 'Autos'],
     'delta': [0.0, 0.1],
     'rho_c': [0.042780, 0.075286],
     'rho_c_d': [0.029723, 0.042000],
     'rho_c_e': [0.115883, 0.114476],
     'rho_nc': [0.0400, 0.0388],
     'rho_nc_d': [0.0100, 0.0112],
     'rho_nc_e': [0.100, 0.094],
     'metr_c': [0.298738, 0.601520],
     'metr_c_d': [0.32712, 0.52381],
     'metr_c_e': [0.223355, 0.213809],
     'metr_nc': [0, -0.03092784],
     'metr_nc_d': [0, 0.1071429],
     'metr_nc_e': [0.0, -0.06382979],
     'mettr_c': [0.228612, 0.561671],
     'mettr_c_d': [0.32712, 0.52381],
     'mettr_c_e': [-0.121821, -0.135609],
     'mettr_nc': [0.0, -0.030928],
     'mettr_nc_d': [-24.000000, -21.321429],
     'mettr_nc_e': [0.88000, 0.87234]})
correct_df1 = pd.DataFrame(
    {'Asset Type': ['Inventories', 'Autos'],
     'delta': [0.0, 0.1],
     'rho_c': [0.042780, 0.075286],
     'rho_c_d': [0.029723, 0.042000],
     'rho_c_e': [0.115883, 0.114476],
     'rho_nc': [0.0400, 0.0388],
     'rho_nc_d': [0.0100, 0.0112],
     'rho_nc_e': [0.100, 0.094],
     'metr_c': [1.0, 1.0],
     'metr_c_d': [1.336440, 1.238095],
     'metr_c_e': [0.482236, 0.475873],
     'metr_nc': [0.750000, 0.742268],
     'metr_nc_d': [3.000000, 2.785714],
     'metr_nc_e': [0.300000, 0.255319],
     'mettr_c': [0.228612, 0.561671],
     'mettr_c_d': [0.32712, 0.52381],
     'mettr_c_e': [-0.121821, -0.135609],
     'mettr_nc': [0.0, -0.030928],
     'mettr_nc_d': [-24.000000, -21.321429],
     'mettr_nc_e': [0.88000, 0.87234]})
test_data = [(0.02, correct_df0), (0.05, correct_df1)]


@pytest.mark.parametrize('inflation_rate,expected', test_data,
                         ids=['pi=0.02', 'pi=0.05'])
def test_metr(inflation_rate, expected):
    # Test METR and METTR calculations
    df = pd.DataFrame(
        {'Asset Type': ['Inventories', 'Autos'],
         'delta': [0.0, 0.1],
         'rho_c': [0.042780, 0.075286],
         'rho_c_d': [0.029723, 0.042000],
         'rho_c_e': [0.115883, 0.114476],
         'rho_nc': [0.0400, 0.0388],
         'rho_nc_d': [0.0100, 0.0112],
         'rho_nc_e': [0.100, 0.094]})
    r_prime = np.array([[0.05, 0.06], [0.04, .03], [0.11, 0.12]])
    save_rate = np.array([[0.033, 0.04], [0.02, .25], [0.13, 0.012]])
    financing_list = ['', '_d', '_e']
    entity_list = ['_c', '_nc']
    test_df = calc_final_outputs.metr(df, r_prime, inflation_rate,
                                      save_rate, entity_list,
                                      financing_list)
    expected = expected[['Asset Type', 'delta', 'rho_c', 'rho_c_d',
                         'rho_c_e', 'rho_nc', 'rho_nc_d', 'rho_nc_e',
                         'metr_c', 'mettr_c', 'metr_nc', 'mettr_nc',
                         'metr_c_d', 'mettr_c_d', 'metr_nc_d',
                         'mettr_nc_d', 'metr_c_e', 'mettr_c_e',
                         'metr_nc_e', 'mettr_nc_e']]

    assert_frame_equal(test_df, expected, check_dtype=False,
                       check_less_precise=True)


# def test_asset_calcs():
#
#     assert_frame_equal(test_df, correct_df, check_dtype=False)
#
#
# def test_industry_calcs():
#
#     assert_frame_equal(test_df, correct_df, check_dtype=False)
