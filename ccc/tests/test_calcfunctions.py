import pandas as pd
import numpy as np
import pytest
from pandas.testing import assert_frame_equal
from ccc import calcfunctions as cf


# def test_update_depr_methods(df, p):
#     test_df = cf.update_depr_methods(df, p)
#
#     assert_frame_equal(test_df, expected_df)
#


# Y = np.array([40, 3, 10, 20, 8])
# b = np.array([1.2, 1.0, 1.5, 2.0, 1.8])
# bonus = np.array([0.0, 0.0, 0.4, 1.0, 0.9])
# r = np.array([0.03, 0.03, 0.03, 0.03, 0.03])
# expected_val = np.array([0.588563059, 0.956320164, 0.924042198, 1,
#                          0.99041001])
# test_data = [(Y, b, bonus, r, expected_val)]
#
#
# @pytest.mark.parametrize('Y,b,bonus,r,expected_val', test_data,
#                          ids=['Test 0'])
# def test_dbsl(Y, b, bonus, r, expected_val):
#     test_val = cf.dbsl(Y, b, bonus, r)
#
#     assert(np.allclose(test_val, expected_val))


Y = np.array([40, 1, 10, 20, 8])
bonus = np.array([0, 0, 0.4, 1, 1.2])
r = np.array([0.12, 0.12, 0.12, 0.12, 0.12])
expected_val = np.array([0.206618803, 0.942329694, 0.749402894, 1,
                         1.071436018])
test_data = [(Y, bonus, r, expected_val)]


@pytest.mark.parametrize('Y,bonus,r,expected_val', test_data,
                         ids=['Test 0'])
def test_sl(Y, bonus, r, expected_val):
    test_val = cf.sl(Y, bonus, r)

    assert(np.allclose(test_val, expected_val))


delta = np.array([0.01, 0.1, 0.1, 0.02, 0.1])
bonus = np.array([0, 0, 0.4, 1, 1.2])
r = np.array([0.12, 0.12, 0.12, 0.12, 0.12])
pi = np.array([0.03, 0.03, 0.03, 0.03, 0.03])
expected_val = np.array([0.1, 0.526315789, 0.715789474, 1, 1.094736842])
test_data = [(delta, bonus, r, pi, expected_val)]


@pytest.mark.parametrize('delta,bonus,r,pi,expected_val', test_data,
                         ids=['Test 0'])
def test_econ(delta, bonus, r, pi, expected_val):
    test_val = cf.econ(delta, bonus, r, pi)

    assert(np.allclose(test_val, expected_val))


# def test_npv_tax_depr(df, r, pi):
#     test_df = cf.npv_tax_depr(df, r, pi)
#
#     assert_frame_equal(test_df, expected_df)


delta = np.array([0.1, 0.1, 0.1, 0.1, 0.1, 0.1])
z = np.array([0.1, 0, 0.5, 1, 0.55556, 0.8])
w = np.array([0.01, 0.01, 0.01, 0.01, 0.01, 0.01])
u = np.array([0.3, 0, 0.3, 0, 0.3, 0])
inv_tax_credit = np.array([0.08, 0.08, 0.08, 0.08, 0.08, 0.08])
pi = np.array([0.02, 0.02, 0.02, 0.02, 0.02, 0.02])
r = np.array([0.05, 0.06, 0.04, 0.03, 0.11, 0.12])

expected_val = np.array([0.075285714, 0.0388, 0.042, 0.0112,
                         0.114475829, 0.094])
test_data = [(delta, z, w, u, inv_tax_credit, pi, r, expected_val)]


@pytest.mark.parametrize('delta,z,w,u,inv_tax_credit,pi,r,expected_val',
                         test_data, ids=['Test 0'])
def test_eq_coc(delta, z, w, u, inv_tax_credit, pi, r, expected_val):
    test_val = cf.eq_coc(delta, z, w, u, inv_tax_credit, pi, r)

    assert(np.allclose(test_val, expected_val))


u = np.array([0.3, 0, 0.3, 0, 0.3, 0])
phi = np.array([0.33, 0.33, 0.33, 0.33, 0.33, 0.33])
Y_v = np.array([8, 8, 8, 8, 8, 8])
pi = np.array([0.02, 0.02, 0.02, 0.02, 0.02, 0.02])
r = np.array([0.05, 0.06, 0.04, 0.03, 0.11, 0.12])

expected_val = np.array([0.042779968, 0.04, 0.029723255, 0.01,
                         0.115882546, 0.1])
test_data = [(u, phi, Y_v, pi, r, expected_val)]


@pytest.mark.parametrize('u,phi,Y_v,pi,r,expected_val',
                         test_data, ids=['Test 0'])
def test_eq_coc_inventory(u, phi, Y_v, pi, r, expected_val):
    test_val = cf.eq_coc_inventory(u, phi, Y_v, pi, r)

    assert(np.allclose(test_val, expected_val))


rho = np.array([0.075285714, 0.0388, 0.042, 0.0112, 0.114475829, 0.094])
delta = np.array([0.05, 0.06, 0.04, 0.03, 0.11, 0.12])
expected_val = np.array([0.125285714, 0.0988, 0.082, 0.0412,
                         0.224475829, 0.214])
test_data = [(rho, delta, expected_val)]


@pytest.mark.parametrize('rho,delta,expected_val', test_data,
                         ids=['Test 0'])
def test_eq_ucc(rho, delta, expected_val):
    test_val = cf.eq_ucc(rho, delta)

    assert(np.allclose(test_val, expected_val))


rho = np.array([0.075285714, 0.0388, 0.042, 0.0112, 0.114475829, 0.094])
r_prime = np.array([0.05, 0.06, 0.04, 0.03, 0.11, 0.12])
pi = 0.02
expected_val = np.array([0.601518027, -0.030927835, 0.523809524,
                         0.107142857, 0.213807831, -0.063829787])
test_data = [(rho, r_prime, pi, expected_val)]


@pytest.mark.parametrize('rho,r_prime,pi,expected_val', test_data,
                         ids=['Test 0'])
def test_eq_metr(rho, r_prime, pi, expected_val):
    test_val = cf.eq_metr(rho, r_prime, pi)

    assert(np.allclose(test_val, expected_val))


rho = np.array([0.075285714, 0.0388, 0.042, 0.0112, 0.114475829, 0.094])
s = np.array([0.05, 0.06, 0.04, 0.03, 0.11, 0.12])
expected_val = np.array([0.335863378, -0.546391753, 0.047619048,
                         -1.678571429, 0.03909846, -0.276595745])
test_data = [(rho, s, expected_val)]


@pytest.mark.parametrize('rho,s,expected_val', test_data,
                         ids=['Test 0'])
def test_eq_mettr(rho, s, expected_val):
    test_val = cf.eq_mettr(rho, s)

    assert(np.allclose(test_val, expected_val))


rho = np.array([0.075285714, 0.0388, 0.042, 0.0112, 0.114475829, 0.094])
s = np.array([0.05, 0.06, 0.04, 0.03, 0.11, 0.12])
expected_val = np.array([0.02528571, -0.0212, 0.002, -0.0188,
                         0.00447583, -0.026])
test_data = [(rho, s, expected_val)]


@pytest.mark.parametrize('rho,s,expected_val', test_data,
                         ids=['Test 0'])
def test_eq_tax_wedge(rho, s, expected_val):
    test_val = cf.eq_tax_wedge(rho, s)

    assert(np.allclose(test_val, expected_val))


# def test_eq_eatr(rho, metr, profit_rate, u):
#     test_val = cf.eq_eatr(rho, metr, profit_rate, u)
#
#     assert(np.allclose(test_val, expected_val))
#

# correct_df0 = pd.DataFrame(
#     {'Asset Type': ['Inventories', 'Autos'],
#      'delta': [0.0, 0.1],
#      'z_c': [0.0, 0.1],
#      'z_c_d': [0.5, 0.5],
#      'z_c_e': [0.6, 0.55556],
#      'z_nc': [1.0, 0.0],
#      'z_nc_d': [0.1, 1.0],
#      'z_nc_e': [0.9, 0.8],
#      'rho_c': [0.028571, 0.066286],
#      'rho_c_d': [0.012143, 0.033571],
#      'rho_c_e': [0.093714, 0.114285],
#      'rho_nc': [0.03, 0.03],
#      'rho_nc_d': [0, 0],
#      'rho_nc_e': [0.09, 0.09],
#      'ucc_c': [0.028571, 0.166286],
#      'ucc_c_d': [0.012143, 0.133571],
#      'ucc_c_e': [0.093714, 0.214285],
#      'ucc_nc': [0.03, 0.13],
#      'ucc_nc_d': [0, 0.1],
#      'ucc_nc_e': [0.09, 0.19]})
# correct_df1 = pd.DataFrame(
#     {'Asset Type': ['Inventories', 'Autos'],
#      'delta': [0.0, 0.1],
#      'z_c': [0.0, 0.1],
#      'z_c_d': [0.5, 0.5],
#      'z_c_e': [0.6, 0.55556],
#      'z_nc': [1.0, 0.0],
#      'z_nc_d': [0.1, 1.0],
#      'z_nc_e': [0.9, 0.8],
#      'rho_c': [0.033055, 0.066286],
#      'rho_c_d': [0.019550, 0.033571],
#      'rho_c_e': [0.109878, 0.114285],
#      'rho_nc': [0.03, 0.03],
#      'rho_nc_d': [0, 0],
#      'rho_nc_e': [0.09, 0.09],
#      'ucc_c': [0.033055, 0.166286],
#      'ucc_c_d': [0.019550, 0.133571],
#      'ucc_c_e': [0.109878, 0.214285],
#      'ucc_nc': [0.03, 0.13],
#      'ucc_nc_d': [0, 0.1],
#      'ucc_nc_e': [0.09, 0.19]})
# correct_df2 = pd.DataFrame(
#     {'Asset Type': ['Inventories', 'Autos'],
#      'delta': [0.0, 0.1],
#      'z_c': [0.0, 0.1],
#      'z_c_d': [0.5, 0.5],
#      'z_c_e': [0.6, 0.55556],
#      'z_nc': [1.0, 0.0],
#      'z_nc_d': [0.1, 1.0],
#      'z_nc_e': [0.9, 0.8],
#      'rho_c': [0.042780, 0.075286],
#      'rho_c_d': [0.029723, 0.042000],
#      'rho_c_e': [0.115883, 0.114476],
#      'rho_nc': [0.0400, 0.0388],
#      'rho_nc_d': [0.0100, 0.0112],
#      'rho_nc_e': [0.100, 0.094],
#      'ucc_c': [0.042780, 0.175286],
#      'ucc_c_d': [0.029723, 0.142000],
#      'ucc_c_e': [0.115883, 0.214476],
#      'ucc_nc': [0.0400, 0.1388],
#      'ucc_nc_d': [0.0100, 0.1112],
#      'ucc_nc_e': [0.100, 0.194]})
# # tuple of params in order: expense_inventory, inflation_rate,
# # inv_credit, w, phi, Y_v
# test_data = [((True, 0.03, 0.0, 0.0, 0.5, 5.), correct_df0),
#              ((False, 0.03, 0.0, 0.0, 0.5, 5.), correct_df1),
#              ((False, 0.02, 0.08, 0.01, 0.33, 8.), correct_df2)]
#
#
# @pytest.mark.parametrize('changing_params,expected', test_data,
#                          ids=['Test 0', 'Test 1', 'Test 2'])
# def test_cost_of_capital(changing_params, expected):
#     expense_inventory, inflation_rate, inv_credit, w, phi, Y_v = changing_params
#     # Test cost of capital calculation
#     df = pd.DataFrame(
#         {'Asset Type': ['Inventories', 'Autos'],
#          'delta': [0.0, 0.1],
#          'z_c': [0.0, 0.1],
#          'z_c_d': [0.5, 0.5],
#          'z_c_e': [0.6, 0.55556],
#          'z_nc': [1.0, 0.0],
#          'z_nc_d': [0.1, 1.0],
#          'z_nc_e': [0.9, 0.8]})
#     discount_rate = np.array([[0.05, 0.06], [0.04, .03], [0.11, 0.12]])
#     financing_list = ['', '_d', '_e']
#     entity_list = ['_c', '_nc']
#     stat_tax = np.array([0.3, 0.0])
#     test_df = calc_final_outputs.cost_of_capital(
#         df, w, expense_inventory, stat_tax, inv_credit, phi, Y_v,
#         inflation_rate, discount_rate, entity_list,
#         financing_list
#         )
#
#     expected = expected[['Asset Type', 'delta', 'z_c', 'z_c_d', 'z_c_e',
#                          'z_nc', 'z_nc_d', 'z_nc_e', 'rho_c', 'ucc_c',
#                          'rho_nc', 'ucc_nc', 'rho_c_d', 'ucc_c_d',
#                          'rho_nc_d', 'ucc_nc_d', 'rho_c_e', 'ucc_c_e',
#                          'rho_nc_e', 'ucc_nc_e']]
#
#     assert_frame_equal(test_df, expected, check_dtype=False,
#                        check_less_precise=True)
#
#
# correct_df0 = pd.DataFrame(
#     {'Asset Type': ['Inventories', 'Autos'],
#      'delta': [0.0, 0.1],
#      'rho_c': [0.042780, 0.075286],
#      'rho_c_d': [0.029723, 0.042000],
#      'rho_c_e': [0.115883, 0.114476],
#      'rho_nc': [0.0400, 0.0388],
#      'rho_nc_d': [0.0100, 0.0112],
#      'rho_nc_e': [0.100, 0.094],
#      'metr_c': [0.298738, 0.601520],
#      'metr_c_d': [0.32712, 0.52381],
#      'metr_c_e': [0.223355, 0.213809],
#      'metr_nc': [0, -0.03092784],
#      'metr_nc_d': [0, 0.1071429],
#      'metr_nc_e': [0.0, -0.06382979],
#      'mettr_c': [0.228612, 0.561671],
#      'mettr_c_d': [0.32712, 0.52381],
#      'mettr_c_e': [-0.121821, -0.135609],
#      'mettr_nc': [0.0, -0.030927835],
#      'mettr_nc_d': [-24.000000, -21.321429],
#      'mettr_nc_e': [0.88000, 0.87234],
#      'tax_wedge_c': [0.009779968, 0.042285714],
#      'tax_wedge_c_d': [0.009723255, 0.022],
#      'tax_wedge_c_e': [-0.014117454, -0.015524171],
#      'tax_wedge_nc': [0.0, -0.0012],
#      'tax_wedge_nc_d': [-0.24, -0.2388],
#      'tax_wedge_nc_e': [0.088, 0.082]})
# correct_df1 = pd.DataFrame(
#     {'Asset Type': ['Inventories', 'Autos'],
#      'delta': [0.0, 0.1],
#      'rho_c': [0.042780, 0.075286],
#      'rho_c_d': [0.029723, 0.042000],
#      'rho_c_e': [0.115883, 0.114476],
#      'rho_nc': [0.0400, 0.0388],
#      'rho_nc_d': [0.0100, 0.0112],
#      'rho_nc_e': [0.100, 0.094],
#      'metr_c': [1.0, 1.0],
#      'metr_c_d': [1.336440, 1.238095],
#      'metr_c_e': [0.482236, 0.475873],
#      'metr_nc': [0.750000, 0.742268],
#      'metr_nc_d': [3.000000, 2.785714],
#      'metr_nc_e': [0.300000, 0.255319],
#      'mettr_c': [0.228612, 0.561671],
#      'mettr_c_d': [0.32712, 0.52381],
#      'mettr_c_e': [-0.121821, -0.135609],
#      'mettr_nc': [0.0, -0.030928],
#      'mettr_nc_d': [-24.000000, -21.321429],
#      'mettr_nc_e': [0.88000, 0.87234],
#      'tax_wedge_c': [0.009779968, 0.042285714],
#      'tax_wedge_c_d': [0.009723255, 0.022],
#      'tax_wedge_c_e': [-0.014117454, -0.015524171],
#      'tax_wedge_nc': [0.0, -0.0012],
#      'tax_wedge_nc_d': [-0.24, -0.2388],
#      'tax_wedge_nc_e': [0.088, 0.082]})
# test_data = [(0.02, correct_df0), (0.05, correct_df1)]
#
#
# @pytest.mark.parametrize('inflation_rate,expected', test_data,
#                          ids=['pi=0.02', 'pi=0.05'])
# def test_metr(inflation_rate, expected):
#     # Test METR and METTR calculations
#     df = pd.DataFrame(
#         {'Asset Type': ['Inventories', 'Autos'],
#          'delta': [0.0, 0.1],
#          'rho_c': [0.042780, 0.075286],
#          'rho_c_d': [0.029723, 0.042000],
#          'rho_c_e': [0.115883, 0.114476],
#          'rho_nc': [0.0400, 0.0388],
#          'rho_nc_d': [0.0100, 0.0112],
#          'rho_nc_e': [0.100, 0.094]})
#     r_prime = np.array([[0.05, 0.06], [0.04, .03], [0.11, 0.12]])
#     save_rate = np.array([[0.033, 0.04], [0.02, .25], [0.13, 0.012]])
#     financing_list = ['', '_d', '_e']
#     entity_list = ['_c', '_nc']
#     test_df = calc_final_outputs.metr(df, r_prime, inflation_rate,
#                                       save_rate, entity_list,
#                                       financing_list)
#     expected = expected[['Asset Type', 'delta', 'rho_c', 'rho_c_d',
#                          'rho_c_e', 'rho_nc', 'rho_nc_d', 'rho_nc_e',
#                          'metr_c', 'mettr_c', 'tax_wedge_c', 'metr_nc',
#                          'mettr_nc', 'tax_wedge_nc', 'metr_c_d',
#                          'mettr_c_d', 'tax_wedge_c_d', 'metr_nc_d',
#                          'mettr_nc_d', 'tax_wedge_nc_d', 'metr_c_e',
#                          'mettr_c_e', 'tax_wedge_c_e', 'metr_nc_e',
#                          'mettr_nc_e', 'tax_wedge_nc_e']]
#
#     assert_frame_equal(test_df, expected, check_dtype=False,
#                        check_less_precise=True)
#
#
# correct_df0 = pd.DataFrame(
#     {'Asset Type': ['Inventories', 'Autos'],
#      'delta': [0.0, 0.1],
#      'rho_c': [0.042780, 0.075286],
#      'rho_c_d': [0.029723, 0.042000],
#      'rho_c_e': [0.115883, 0.114476],
#      'rho_nc': [0.0400, 0.0388],
#      'rho_nc_d': [0.0100, 0.0112],
#      'rho_nc_e': [0.100, 0.094],
#      'metr_c': [0.298738, 0.601520],
#      'metr_c_d': [0.32712, 0.52381],
#      'metr_c_e': [0.223355, 0.213809],
#      'metr_nc': [0, -0.03092784],
#      'metr_nc_d': [0, 0.1071429],
#      'metr_nc_e': [0.0, -0.06382979],
#      'eatr_c': [0.299459779, 0.527],
#      'eatr_c_d': [0.308062784, 0.394],
#      'eatr_c_e': [0.211177821, 0.2013308],
#      'eatr_nc': [0.0, -0.012],
#      'eatr_nc_d': [0.0, 0.012],
#      'eatr_nc_e': [0.0, -0.06]})
# correct_df1 = pd.DataFrame(
#     {'Asset Type': ['Inventories', 'Autos'],
#      'delta': [0.0, 0.1],
#      'rho_c': [0.042780, 0.075286],
#      'rho_c_d': [0.029723, 0.042000],
#      'rho_c_e': [0.115883, 0.114476],
#      'rho_nc': [0.0400, 0.0388],
#      'rho_nc_d': [0.0100, 0.0112],
#      'rho_nc_e': [0.100, 0.094],
#      'metr_c': [0.298738, 0.601520],
#      'metr_c_d': [0.32712, 0.52381],
#      'metr_c_e': [0.223355, 0.213809],
#      'metr_nc': [0, -0.03092784],
#      'metr_nc_d': [0, 0.1071429],
#      'metr_nc_e': [0.0, -0.06382979],
#      'eatr_c': [0.298737211, 0.830621786],
#      'eatr_c_d': [0.318847088, 0.519728845],
#      'eatr_c_e': [0.092374524, 0.069356709],
#      'eatr_nc': [0.0, -0.028050491],
#      'eatr_nc_d': [0.0, 0.028050491],
#      'eatr_nc_e': [0.0, -0.140252454]})
# test_data = [(0.10, correct_df0), (0.042780, correct_df1)]
#
#
# @pytest.mark.parametrize('p,expected', test_data,
#                          ids=['p=0.10', 'p=0.042780'])
# def test_eatr(p, expected):
#     # Test METR and METTR calculations
#     df = pd.DataFrame(
#         {'Asset Type': ['Inventories', 'Autos'],
#          'delta': [0.0, 0.1],
#          'rho_c': [0.042780, 0.075286],
#          'rho_c_d': [0.029723, 0.042000],
#          'rho_c_e': [0.115883, 0.114476],
#          'rho_nc': [0.0400, 0.0388],
#          'rho_nc_d': [0.0100, 0.0112],
#          'rho_nc_e': [0.100, 0.094],
#          'metr_c': [0.298738, 0.601520],
#          'metr_c_d': [0.32712, 0.52381],
#          'metr_c_e': [0.223355, 0.213809],
#          'metr_nc': [0, -0.03092784],
#          'metr_nc_d': [0, 0.1071429],
#          'metr_nc_e': [0.0, -0.06382979]})
#     stat_tax = np.array([0.3, 0.0])
#     financing_list = ['', '_d', '_e']
#     entity_list = ['_c', '_nc']
#     test_df = calc_final_outputs.eatr(df, p, stat_tax, entity_list,
#                                       financing_list)
#     expected = expected[['Asset Type', 'delta', 'rho_c', 'rho_c_d',
#                          'rho_c_e', 'rho_nc', 'rho_nc_d', 'rho_nc_e',
#                          'metr_c', 'eatr_c', 'metr_nc', 'eatr_nc',
#                          'metr_c_d', 'eatr_c_d', 'metr_nc_d',
#                          'eatr_nc_d', 'metr_c_e', 'eatr_c_e',
#                          'metr_nc_e', 'eatr_nc_e']]
#     test_df = test_df[['Asset Type', 'delta', 'rho_c', 'rho_c_d',
#                          'rho_c_e', 'rho_nc', 'rho_nc_d', 'rho_nc_e',
#                          'metr_c', 'eatr_c', 'metr_nc', 'eatr_nc',
#                          'metr_c_d', 'eatr_c_d', 'metr_nc_d',
#                          'eatr_nc_d', 'metr_c_e', 'eatr_c_e',
#                          'metr_nc_e', 'eatr_nc_e']]
#
#     assert_frame_equal(test_df, expected, check_dtype=False,
#                        check_less_precise=True)
