import numpy as np
import pytest
from ccc import paramfunctions as pf
from ccc.parameters import Specification


def test_calc_sprime_c_td():
    '''
    Test of the paramfunctions.calc_sprime_c_td function
    '''
    Y_td, tau_td, i, pi = 8, 0.2, 0.08, 0.02
    test_value = pf.calc_sprime_c_td(Y_td, tau_td, i, pi)

    assert(np.allclose(test_value, 0.047585769))


def test_calc_s_c_d_td():
    '''
    Test of the paramfunctions.calc_s_c_d_td function
    '''
    sprime_c_td = 0.047585769
    gamma, i, pi = 0.5, 0.08, 0.02
    test_value = pf.calc_s_c_d_td(sprime_c_td, gamma, i, pi)

    assert(np.allclose(test_value, 0.053792884))


def test_calc_s__d():
    '''
    Test of the paramfunctions.calc_s__d function
    '''
    s_d_td = 0.053792884
    alpha_d_ft, alpha_d_td, alpha_d_nt = 0.3, 0.5, 0.2
    tau_int, tau_w, i, pi = 0.3, 0.02, 0.08, 0.02
    test_value = pf.calc_s__d(s_d_td, alpha_d_ft, alpha_d_td,
                              alpha_d_nt, tau_int, tau_w, i, pi)

    assert(np.allclose(test_value, 0.029696442))


def test_calc_g__g():
    '''
    Test of the paramfunctions.calc_g__g function
    '''
    Y_g, tau_cg, m, E_c, pi = 2.0, 0.35, 0.4, 0.09, 0.02
    test_value = pf.calc_g__g(Y_g, tau_cg, m, E_c, pi)

    assert(np.allclose(test_value, 0.017105186))


def test_calc_g():
    '''
    Test of the paramfunctions.calc_g function
    '''
    g_scg, g_lcg = 0.017105186, 0.030329578
    omega_scg, omega_lcg, omega_xcg = 0.7, 0.1, 0.2
    m, E_c = 0.4, 0.09
    g_xcg = m * E_c
    test_value = pf.calc_g(
        g_scg, g_lcg, g_xcg, omega_scg, omega_lcg, omega_xcg, m, E_c)

    assert(np.allclose(test_value, 0.022206588))


def test_calc_s_c_e_td():
    '''
    Test of the paramfunctions.calc_s_c_e_td function
    '''
    Y_td, tau_td, i, pi, E_c = 8, 0.2, 0.08, 0.02, 0.09
    test_value = pf.calc_s_c_e_td(Y_td, tau_td, i, pi, E_c)

    assert(np.allclose(test_value, 0.074440094))


def test_calc_s_c_e():
    '''
    Test of the paramfunctions.calc_s_c_e function
    '''
    s_c_e_ft, s_c_e_td = 0.062706588, 0.074440094
    alpha_c_e_ft, alpha_c_e_td, alpha_c_e_nt = 0.6, 0.3, 0.1
    tau_w, E_c = 0.02, 0.09
    test_value = pf.calc_s_c_e(
        s_c_e_ft, s_c_e_td, alpha_c_e_ft, alpha_c_e_td, alpha_c_e_nt,
        tau_w, E_c)

    assert(np.allclose(test_value, 0.048955981))


p = Specification()
revisions = {'Y_td': 8, 'Y_scg': 2, 'Y_lcg': 7, 'tau_td': 0.2,
             'tau_int': 0.3, 'tau_scg': 0.35, 'tau_lcg': 0.12,
             'tau_div': 0.25, 'tau_w': 0.02, 'gamma': 0.5, 'm': 0.4,
             'E_c': 0.09, 'nominal_interest_rate': 0.08,
             'inflation_rate': 0.02, 'alpha_c_d_ft': 0.3,
             'alpha_c_d_td': 0.5, 'alpha_c_d_nt': 0.2,
             'alpha_pt_d_ft': 0.5, 'alpha_pt_d_td': 0.4,
             'alpha_pt_d_nt': 0.1, 'alpha_c_e_ft': 0.6,
             'alpha_c_e_td': 0.3, 'alpha_c_e_nt': 0.1, 'omega_scg': 0.7,
             'omega_lcg': 0.1, 'omega_xcg': 0.2, 'f_c': 0.32,
             'f_pt': 0.42}
p.update_specification(revisions)
expected_dict = {
    'c': {'mix': 0.042792929, 'd': 0.029696442, 'e': 0.048955981},
    'pt': {'mix': 0.027511674, 'd': 0.025517154, 'e': 0.028955981}}


@pytest.mark.parametrize('entity_type,p,expected_dict',
                         [('c', p, expected_dict),
                          ('pt', p, expected_dict)],
                         ids=['Corporate', 'Pass-Throughs'])
def test_calc_s(entity_type, p, expected_dict):
    '''
    Test of the paramfunctions.calc_s function
    '''
    test_dict, test_E_pt = pf.calc_s(p)

    for k, v in test_dict[entity_type].items():
        assert(np.allclose(v, expected_dict[entity_type][k]))

    assert(np.allclose(test_E_pt, 0.048955981))


p = Specification()
revisions = {
    'f_c': 0.4, 'f_pt': 0.2, 'interest_deduct_haircut_c': 0.0,
    'interest_deduct_haircut_pt': 0.0, 'ace_c': 0.0, 'ace_pt': 0.0,
    'CIT_rate': 0.25, 'tau_pt': 0.22, 'nominal_interest_rate': 0.05,
    'inflation_rate': 0.02, 'E_c': 0.08}
p.update_specification(revisions)
expected_r_dict = {
    'c': {'mix': np.array([0.075]), 'd': np.array([0.0375]),
          'e': np.array([0.1])},
    'pt': {'mix': np.array([0.0798]), 'd': np.array([0.039]),
           'e': np.array([0.09])}}


@pytest.mark.parametrize('p,expected_dict',
                         [(p, expected_r_dict)],
                         ids=['Test 1'])
def test_calc_r(p, expected_dict):
    '''
    Test of the calculation of the discount rate function
    '''
    f_dict = {'c': {'mix': p.f_c, 'd': 1.0, 'e': 0.0},
              'pt': {'mix': p.f_pt, 'd': 1.0, 'e': 0.0}}
    int_haircut_dict = {'c': p.interest_deduct_haircut_c,
                        'pt': p.interest_deduct_haircut_pt}
    E_dict = {'c': p.E_c, 'pt': 0.07}
    print('E dict = ', E_dict)
    ace_dict = {'c': p.ace_c, 'pt': p.ace_pt}
    test_dict = pf.calc_r(p, f_dict, int_haircut_dict, E_dict, ace_dict)

    for k, v in test_dict.items():
        for k2, v2 in v.items():
            assert(np.allclose(v2, expected_dict[k][k2]))


expected_rprime_dict = {
    'c': {'mix': np.array([0.08]), 'd': np.array([0.05]),
          'e': np.array([0.1])},
    'pt': {'mix': np.array([0.082]), 'd': np.array([0.05]),
           'e': np.array([0.09])}}


@pytest.mark.parametrize('p,expected_dict',
                         [(p, expected_rprime_dict)],
                         ids=['Test 1'])
def test_calc_rprime(p, expected_dict):
    '''
    Test of the calculation of the after-tax rate of return function
    '''
    f_dict = {'c': {'mix': p.f_c, 'd': 1.0, 'e': 0.0},
              pt: {'mix': p.f_pt, 'd': 1.0, 'e': 0.0}}
    E_dict = {'c': p.E_c, 'pt': 0.07}
    test_dict = pf.calc_r_prime(p, f_dict, E_dict)

    for k, v in test_dict.items():
        for k2, v2 in v.items():
            assert(np.allclose(v2, expected_dict[k][k2]))
