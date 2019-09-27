import numpy as np


def calc_s(p):
    '''
    Compute the after-tax rate of return to savers, s.

    .. math::
        s = ...

    Args:
        p (CCC Specification Object): model parameters

    Returns:
        (tuple): return to savers and required return to pass-through
            entities:

            * s_dict (dict): dictionary of s for investments in
                corporate and pass-through businesses and by type of
                financing
            * E_nc (scalar): required pre-tax return on pass-through
                investments

    '''
    sprime_c_td = ((1 / p.Y_td) *
                   np.log(((1 - p.tau_td) *
                           np.exp(p.nominal_interest_rate *
                                  p.Y_td)) + p.tau_td) -
                   p.inflation_rate)
    s_c_d_td = (p.gamma * (p.nominal_interest_rate - p.inflation_rate) +
                (1 - p.gamma) * sprime_c_td)
    s_c_d = (p.alpha_c_d_ft *
             (((1 - p.tau_int) * p.nominal_interest_rate) -
              p.inflation_rate) +
             p.alpha_c_d_td * s_c_d_td + p.alpha_c_d_nt *
             (p.nominal_interest_rate - p.inflation_rate) -
             p.tau_w)
    s_nc_d_td = s_c_d_td
    s_nc_d = (p.alpha_nc_d_ft *
              (((1 - p.tau_int) *
                p.nominal_interest_rate) - p.inflation_rate) +
              p.alpha_nc_d_td * s_nc_d_td + p.alpha_nc_d_nt *
              (p.nominal_interest_rate - p.inflation_rate) -
              p.tau_w)

    g_scg = ((1 / p.Y_scg) *
             np.log(((1 - p.tau_scg) *
                     np.exp((p.inflation_rate +
                             p.m * p.E_c) * p.Y_scg)) +
                    p.tau_scg) - p.inflation_rate)
    g_lcg = ((1 / p.Y_lcg) *
             np.log(((1 - p.tau_lcg) *
                     np.exp((p.inflation_rate + p.m * p.E_c) *
                            p.Y_lcg)) +
                    p.tau_lcg) - p.inflation_rate)
    g = (
        p.omega_scg * g_scg + p.omega_lcg * g_lcg +
        p.omega_xcg * p.m * p.E_c
    )
    s_c_e_ft = (1 - p.m) * p.E_c * (1 - p.tau_div) + g
    s_c_e_td = (
        (1 / p.Y_td) *
        np.log(((1 - p.tau_td) *
                np.exp((p.inflation_rate + p.E_c) * p.Y_td)) +
               p.tau_td) - p.inflation_rate
    )
    s_c_e = (
        p.alpha_c_e_ft * s_c_e_ft + p.alpha_c_e_td *
        s_c_e_td + p.alpha_c_e_nt * p.E_c - p.tau_w
    )

    s_c = p.f_c * s_c_d + (1 - p.f_c) * s_c_e

    E_nc = s_c_e
    s_nc_e = E_nc - p.tau_w
    s_nc = p.f_nc * s_nc_d + (1 - p.f_nc) * s_nc_e

    s_dict = {'c': {'mix': s_c, 'd': s_c_d, 'e': s_c_e},
              'nc': {'mix': s_nc, 'd': s_nc_d, 'e': s_nc_e}}

    return s_dict, E_nc
