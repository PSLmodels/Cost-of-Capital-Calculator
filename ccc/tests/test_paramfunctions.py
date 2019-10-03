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
    Test of the paramfunctions.calc_s__d function
    '''
    Y_g, tau_cg, m, E_c, pi = 2.0, 0.35, 0.4, 0.09, 0.02
    test_value = pf.calc_g__g(Y_g, tau_cg, m, E_c, pi)

    assert(np.allclose(test_value, 0.017105186))


def test_calc_g():
    '''
    Test of the paramfunctions.calc_s__d function
    '''
    g_scg, g_lcg = 0.017105186, 0.030329578
    omega_scg, omega_lcg, omega_xcg = 0.7, 0.1, 0.2
    m, E_c = 0.4, 0.09
    test_value = pf.calc_g(
        g_scg, g_lcg, omega_scg, omega_lcg, omega_xcg, m, E_c)

    assert(np.allclose(test_value, 0.022206588))


def test_calc_s_c_e_td():
    '''
    Test of the paramfunctions.calc_s__d function
    '''
    Y_td, tau_td, i, pi, E_c = 8, 0.2, 0.08, 0.02, 0.09
    test_value = pf.calc_s_c_e_td(Y_td, tau_td, i, pi, E_c)

    assert(np.allclose(test_value, 0.074440094))


def test_calc_s_c_e():
    '''
    Test of the paramfunctions.calc_s__d function
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
             'alpha_nc_d_ft': 0.5, 'alpha_nc_d_td': 0.4,
             'alpha_nc_d_nt': 0.1, 'alpha_c_e_ft': 0.6,
             'alpha_c_e_td': 0.3, 'alpha_c_e_nt': 0.1, 'omega_scg': 0.7,
             'omega_lcg': 0.1, 'omega_xcg': 0.2, 'f_c': 0.32,
             'f_nc': 0.42}
p.update_specification(revisions)
expected_dict = {
    'c': {'mix': 0.042792929, 'd': 0.029696442, 'e': 0.048955981},
    'nc': {'mix': 0.027511674, 'd': 0.025517154, 'e': 0.028955981}}


@pytest.mark.parametrize('entity_type,p,expected_dict',
                         [('c', p, expected_dict),
                          ('nc', p, expected_dict)],
                         ids=['Corporate', 'Pass-Throughs'])
def test_calc_s(entity_type, p, expected_dict):
    '''
    Test of the paramfunctions.calc_s function
    '''
    test_dict, test_E_nc = pf.calc_s(p)

    for k, v in test_dict[entity_type].items():
        assert(np.allclose(v, expected_dict[entity_type][k]))

    assert(np.allclose(test_E_nc, 0.048955981))
