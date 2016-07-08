from calc_rates import calc_tax_depr_rates, get_econ_depr
import numpy as np

def get_params():
	#macro variables
	pi = 0.018
	i = 0.072
	E_c = 0.07
	f_c = 0.41
	f_nc = 0.32
	f_array = np.array([[f_c, f_nc], [1, 1], [0,0]])

	#calibration variables

	omega_scg = 0.03627
	omega_lcg = 0.48187 
	omega_xcg = 0.48187

	alpha_c_e_ft = 0.584
	alpha_c_e_td = 0.058
	alpha_c_e_nt = 0.358

	alpha_c_d_ft = 0.460
	alpha_c_d_td = 0.213
	alpha_c_d_nt = 0.327

	alpha_nc_d_ft = 0.691
	alpha_nc_d_td = 0.142
	alpha_nc_d_nt = 0.167 

	alpha_h_d_ft = 0.716
	alpha_h_d_td = 0.071
	alpha_h_d_nt = 0.213

	#user defined variables
	u_c = 0.35
	u_nc = 0.267
	u_array = np.array([u_c, u_nc])
	w = 0.0117
	tau_div = 0.121
	tau_int = 0.221
	tau_scg = 0.28
	tau_lcg = 0.145
	tau_xcg = 0.00
	tau_td = 0.209
	tau_h = 0.194
	Y_td = 8.
	Y_scg = 4/12.
	Y_lcg = 8.
	gamma = 0.3
	m = 0.4286

	

	#intermediate variables
	sprime_c_td = (1/Y_td)*np.log(((1-tau_td)*np.exp(i*Y_td))+tau_td)-pi
	s_c_d_td = gamma*(i-pi) + (1-gamma)*sprime_c_td
	s_c_d = alpha_c_d_ft*(((1-tau_int)*i)-pi) + alpha_c_d_td*s_c_d_td + alpha_c_d_nt*(i-pi)

	s_nc_d_td = s_c_d_td
	s_nc_d = alpha_nc_d_ft*(((1-tau_int)*i)-pi) + alpha_nc_d_td*s_nc_d_td + alpha_nc_d_nt*(i-pi)

	g_scg = (1/Y_scg)*np.log(((1-tau_scg)*np.exp((pi+m*E_c)*Y_scg))+tau_scg)-pi
	g_lcg = (1/Y_lcg)*np.log(((1-tau_lcg)*np.exp((pi+m*E_c)*Y_lcg))+tau_lcg)-pi
	g = omega_scg*g_scg + omega_lcg*g_lcg + omega_xcg*m*E_c
	s_c_e_ft = (1-m)*E_c*(1-tau_div)+g
	s_c_e_td = (1/Y_td)*np.log(((1-tau_td)*np.exp((pi+E_c)*Y_td))+tau_td)-pi
	s_c_e = alpha_c_e_ft*s_c_e_ft + alpha_c_e_td*s_c_e_td + alpha_c_e_nt*E_c

	s_c = f_c*s_c_d + (1-f_c)*s_c_e

	E_nc = s_c_e
	E_array = np.array([E_c, E_nc])
	s_nc_e = E_nc
	s_nc = f_nc*s_nc_d + (1-f_nc)*s_nc_e
	s_array = np.array([[s_c, s_nc], [s_c_d, s_nc_d], [s_c_e, s_nc_e]])

	r = f_array*(i*(1-u_array))+(1-f_array)*(E_array+pi)
	r_prime = f_array*i+(1-f_array)*(E_array+pi)
	tax_methods = {'GDS 200%': 2.0, 'GDS 150%': 1.5, 'GDS SL': 1.0, 'ADS SL': 1.0}
	z = calc_tax_depr_rates(r, tax_methods)
	delta = get_econ_depr()
	
	parameters = {'inflation rate': pi, 
	'econ depreciation': delta, 
	'depr allow': z,
	'tax rate': u_array,
	'discount rate': r,
	'after-tax rate': r_prime,
	'return to savers': s_array
	}

	return parameters