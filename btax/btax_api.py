import json
import os
import six
import re
import numpy as np
import pickle
import scipy.interpolate as si
import pkg_resources

# import ogusa
from btax.parametersbase import ParametersBase
from btax import get_taxcalc_rates
from btax.util import read_from_egg, DEFAULT_START_YEAR, RECORDS_START_YEAR
# from ogusa import elliptical_u_est


class Specifications(ParametersBase):
    """
    Inherits ParametersBase. Implements the PolicyBrain API for OG-USA
    """
    DEFAULTS_FILENAME = 'default_parameters.json'

    def __init__(self,
                 run_micro=False, output_base=BASELINE_DIR,
                 baseline_dir=BASELINE_DIR, test=False, time_path=True,
                 baseline=False, reform={}, guid='', data='cps',
                 flag_graphs=False, client=None, num_workers=1):
        super(Specifications, self).__init__()

        # reads in default parameter values
        self._vals = self._params_dict_from_json_file()

        self.output_base = output_base
        self.baseline_dir = baseline_dir
        self.test = test
        self.time_path = time_path
        self.baseline = baseline
        self.reform = reform
        self.guid = guid
        self.data = data
        self.flag_graphs = flag_graphs
        self.num_workers = num_workers

        # put OG-USA version in parameters to save for reference
        self.ogusa_version = pkg_resources.get_distribution("ogusa").version

        # does cheap calculations to find parameter values
        self.initialize()

        # does more costly tax function estimation
        if run_micro:
            self.get_tax_function_parameters(self, client, run_micro=True)

        self.parameter_warnings = ''
        self.parameter_errors = ''
        self._ignore_errors = False

    def initialize(self):
        """
        ParametersBase reads JSON file and sets attributes to self
        Next call self.compute_default_params for further initialization
        Parameters:
        -----------
        run_micro: boolean that indicates whether to estimate tax funtions
                   from microsim model
        """
        for name, data in self._vals.items():
            intg_val = data.get('integer_value', None)
            bool_val = data.get('boolean_value', None)
            string_val = data.get('string_value', None)
            values = data.get('value', None)
            setattr(self, name, self._expand_array(values, intg_val,
                                                   bool_val, string_val))
        if self.test:
            # Make smaller statespace for testing
            self.S = int(40)
            self.lambdas = np.array([0.6, 0.4]).reshape(2, 1)
            self.J = self.lambdas.shape[0]
            self.maxiter = 35
            self.mindist_SS = 1e-6
            self.mindist_TPI = 1e-3
            self.nu = .4

        self.compute_default_params()

    def compute_default_params(self):
        """
        Does cheap calculations to return parameter values
        """
        # Find individual income tax rates from Tax-Calculator
        # maybe have an if statement to go to tax-calc?
        indiv_rates = get_taxcalc_rates.get_rates(baseline, start_year,
                                                  iit_reform, data)
        self.tau_nc = indiv_rates['tau_nc']
        self.tau_div = indiv_rates['tau_div']
        self.tau_int = indiv_rates['tau_int']
        self.tau_scg = indiv_rates['tau_scg']
        self.tau_lcg = indiv_rates['tau_lcg']
        self.tau_xcg = 0.00  # tax rate on capital gains held to death
        self.tau_td = indiv_rates['tau_td']
        self.tau_h = indiv_rates['tau_h']

        u_c = user_params['u_c']
        if user_params['u_nc'] == 0.0:
            u_nc = tau_nc
        else:
            u_nc = user_params['u_nc']
        u_array = np.array([u_c, u_nc])

        sprime_c_td = ((1 / Y_td) * np.log(((1 - tau_td) * np.exp(i * Y_td))
                                           + tau_td) - pi)
        s_c_d_td = gamma * (i - pi) + (1 - gamma) * sprime_c_td
        s_c_d = (alpha_c_d_ft * (((1 - tau_int) * i) - pi) + alpha_c_d_td *
                 s_c_d_td + alpha_c_d_nt * (i - pi))
        s_nc_d_td = s_c_d_td
        s_nc_d = (alpha_nc_d_ft * (((1 - tau_int) * i) - pi) + alpha_nc_d_td
                  * s_nc_d_td + alpha_nc_d_nt * (i - pi))

        g_scg = ((1 / Y_scg) * np.log(((1 - tau_scg) * np.exp((pi + m * E_c)
                                                              * Y_scg)) +
                                      tau_scg) - pi)
        g_lcg = ((1 / Y_lcg) * np.log(((1 - tau_lcg) * np.exp((pi + m * E_c)
                                                              * Y_lcg)) +
                                      tau_lcg) - pi)
        g = omega_scg * g_scg + omega_lcg * g_lcg + omega_xcg * m * E_c
        s_c_e_ft = (1 - m) * E_c * (1 - tau_div) + g
        s_c_e_td = ((1 / Y_td) * np.log(((1 - tau_td) * np.exp((pi + E_c) *
                                                               Y_td)) +
                                        tau_td) - pi)
        s_c_e = (alpha_c_e_ft * s_c_e_ft + alpha_c_e_td * s_c_e_td +
                 alpha_c_e_nt * E_c)

        s_c = f_c * s_c_d + (1 - f_c) * s_c_e

        E_nc = s_c_e
        E_array = np.array([E_c, E_nc])
        s_nc_e = E_nc
        s_nc = f_nc * s_nc_d + (1 - f_nc) * s_nc_e
        s_array = np.array([[s_c, s_nc], [s_c_d, s_nc_d], [s_c_e, s_nc_e]])
        r = (f_array * (i * (1 - (1 - int_haircut) * u_array)) + (1 -
                                                                  f_array) *
             (E_array + pi - E_array * r_ace * ace_array))
        r_prime = f_array * i + (1 - f_array) * (E_array + pi)

        # if no entity level taxes on pass-throughs, ensure mettr and metr
        # on non-corp entities the same
        if user_params['u_nc'] == 0.0:
            r_prime[:, 1] = s_array[:, 1] + pi
        # If entity level tax, assume distribute earnings at same rate corps
        # distribute dividends and these are taxed at dividends tax rate
        # (which seems likely).  Also implicitly assumed that if entity
        # level tax, then only additional taxes on pass-through income are
        # capital gains and dividend taxes
        else:
            # keep debt and equity financing ratio the same even though now
            # entity level tax that might now favor debt
            s_array[0, 1] = f_nc * s_nc_d + (1 - f_nc) * s_c_e
            s_array[2, 1] = s_c_e
        delta = get_econ_depr()
        tax_methods = {'DB 200%': 2.0, 'DB 150%': 1.5, 'SL': 1.0,
                       'Economic': 1.0, 'Expensing': 1.0}
        financing_list = ['', '_d', '_e']
        entity_list = ['_c', '_nc']
        z = calc_tax_depr_rates(r, pi, delta, bonus_deprec, deprec_system,
                                expense_inventory, expense_land, tax_methods,
                                financing_list, entity_list)



    def read_tax_func_estimate(self, pickle_path, pickle_file):
        '''
        --------------------------------------------------------------------
        This function reads in tax function parameters
        --------------------------------------------------------------------

        INPUTS:
        pickle_path = string, path to pickle with tax function parameter
                      estimates
        pickle_file = string, name of pickle file with tax function
                      parmaeter estimates

        OTHER FUNCTIONS AND FILES CALLED BY THIS FUNCTION:
        /picklepath/ = pickle file with dictionary of tax function
                       estimated parameters

        OBJECTS CREATED WITHIN FUNCTION:
        dict_params = dictionary, contains numpy arrays of tax function
                      estimates

        RETURNS: dict_params
        --------------------------------------------------------------------
        '''
        if os.path.exists(pickle_path):
            print('pickle path exists')
            with open(pickle_path, 'rb') as pfile:
                try:
                    dict_params = pickle.load(pfile, encoding='latin1')
                except TypeError:
                    dict_params = pickle.load(pfile)
        else:
            from pkg_resources import resource_stream, Requirement
            path_in_egg = pickle_file
            pkl_path = os.path.join(os.path.dirname(__file__), '..',
                                    path_in_egg)
            with open(pkl_path, 'rb') as pfile:
                try:
                    dict_params = pickle.load(pfile, encoding='latin1')
                except TypeError:
                    dict_params = pickle.load(pfile)

        return dict_params

    def default_parameters(self):
        """
        Return Policy object same as self except with current-law policy.
        Returns
        -------
        Specifications: Specifications instance with the default configuration
        """
        dp = Specifications()
        return dp

    def update_specifications(self, revision, raise_errors=True):
        """
        Updates parameter specification with values in revision dictionary
        Parameters
        ----------
        reform: dictionary of one or more PARAM:VALUE pairs
        raise_errors: boolean
            if True (the default), raises ValueError when parameter_errors
                    exists;
            if False, does not raise ValueError when parameter_errors exists
                    and leaves error handling to caller of
                    update_specifications.
        Raises
        ------
        ValueError:
            if raise_errors is True AND
              _validate_parameter_names_types generates errors OR
              _validate_parameter_values generates errors.
        Returns
        -------
        nothing: void
        Notes
        -----
        Given a reform dictionary, typical usage of the Policy class
        is as follows::
            specs = Specifications()
            specs.update_specifications(reform)
        An example of a multi-parameter specification is as follows::
            spec = {
                frisch: [0.03]
            }
        This method was adapted from the Tax-Calculator
        behavior.py-update_behavior method.
        """
        # check that all revisions dictionary keys are integers
        if not isinstance(revision, dict):
            raise ValueError('ERROR: revision is not a dictionary')
        if not revision:
            return  # no revision to implement
        revision_years = sorted(list(revision.keys()))
        # check range of remaining revision_years
        # validate revision parameter names and types
        self.parameter_errors = ''
        self.parameter_warnings = ''
        self._validate_parameter_names_types(revision)
        if not self._ignore_errors and self.parameter_errors:
            raise ValueError(self.parameter_errors)
        # implement the revision
        revision_parameters = set()
        revision_parameters.update(revision.keys())
        self._update(revision)
        # validate revision parameter values
        self._validate_parameter_values(revision_parameters)
        if self.parameter_errors and raise_errors:
            raise ValueError('\n' + self.parameter_errors)
        self.compute_default_params()

    @staticmethod
    def read_json_param_objects(revision):
        """
        Read JSON file and convert to dictionary
        Returns
        -------
        rev_dict: formatted dictionary
        """
        # next process first reform parameter
        if revision is None:
            rev_dict = dict()
        elif isinstance(revision, six.string_types):
            if os.path.isfile(revision):
                txt = open(revision, 'r').read()
            else:
                txt = revision
            # strip out //-comments without changing line numbers
            json_str = re.sub('//.*', ' ', txt)
            # convert JSON text into a Python dictionary
            try:
                rev_dict = json.loads(json_str)
            except ValueError as valerr:
                msg = 'Policy reform text below contains invalid JSON:\n'
                msg += str(valerr) + '\n'
                msg += 'Above location of the first error may be approximate.\n'
                msg += 'The invalid JSON reform text is between the lines:\n'
                bline = 'XX----.----1----.----2----.----3----.----4'
                bline += '----.----5----.----6----.----7'
                msg += bline + '\n'
                linenum = 0
                for line in json_str.split('\n'):
                    linenum += 1
                    msg += '{:02d}{}'.format(linenum, line) + '\n'
                msg += bline + '\n'
                raise ValueError(msg)
        else:
            raise ValueError('reform is neither None nor string')

        return rev_dict

    def _validate_parameter_names_types(self, revision):
        """
        Check validity of parameter names and parameter types used
        in the specified revision dictionary.
        Parameters
        ----------
        revision: parameter dictionary of form {parameter_name: [value]}
        Returns:
        --------
        nothing: void
        Notes
        -----
        copied from taxcalc.Behavior._validate_parameter_names_types
        """
        param_names = set(self._vals.keys())
        # print('Parameter names = ', param_names)
        revision_param_names = list(revision.keys())
        for param_name in revision_param_names:
            if param_name not in param_names:
                msg = '{} unknown parameter name'
                self.parameter_errors += (
                    'ERROR: ' + msg.format(param_name) + '\n'
                )
            else:
                # check parameter value type avoiding use of isinstance
                # because isinstance(True, (int,float)) is True, which
                # makes it impossible to check float parameters
                bool_param_type = self._vals[param_name]['boolean_value']
                int_param_type = self._vals[param_name]['integer_value']
                string_param_type = self._vals[param_name]['string_value']
                if isinstance(revision[param_name], list):
                    param_value = revision[param_name]
                else:
                    param_value = [revision[param_name]]
                for idx in range(0, len(param_value)):
                    pval = param_value[idx]
                    pval_is_bool = type(pval) == bool
                    pval_is_int = type(pval) == int
                    pval_is_float = type(pval) == float
                    pval_is_string = type(pval) == str
                    if bool_param_type:
                        if not pval_is_bool:
                            msg = '{} value {} is not boolean'
                            self.parameter_errors += (
                                'ERROR: ' +
                                msg.format(param_name, pval) +
                                '\n'
                            )
                    elif int_param_type:
                        if not pval_is_int:  # pragma: no cover
                            msg = '{} value {} is not integer'
                            self.parameter_errors += (
                                'ERROR: ' +
                                msg.format(param_name, pval) +
                                '\n'
                            )
                    elif string_param_type:
                        if not pval_is_string:  # pragma: no cover
                            msg = '{} value {} is not string'
                            self.parameter_errors += (
                                'ERROR: ' +
                                msg.format(param_name, pval) +
                                '\n'
                            )
                    else:  # param is float type
                        if not (pval_is_int or pval_is_float):
                            msg = '{} value {} is not a number'
                            self.parameter_errors += (
                                'ERROR: ' +
                                msg.format(param_name, pval) +
                                '\n'
                            )
        del param_names

    def _validate_parameter_values(self, parameters_set):
        """
        Check values of parameters in specified parameter_set using
        range information from the current_law_policy.json file.
        Parameters:
        -----------
        parameters_set: set of parameters whose values need to be validated
        Returns:
        --------
        nothing: void
        Notes
        -----
        copied from taxcalc.Policy._validate_parameter_values
        """
        dp = self.default_parameters()
        parameters = sorted(parameters_set)
        for param_name in parameters:
            param_value = getattr(self, param_name)
            if not hasattr(param_value, 'shape'):  # value is not a numpy array
                param_value = np.array([param_value])
            for validation_op, validation_value in self._vals[param_name]['range'].items():
                if validation_op == 'possible_values':
                    if param_value not in validation_value:
                        out_of_range = True
                        msg = '{} value {} not in possible values {}'
                        if out_of_range:
                            self.parameter_errors += (
                                'ERROR: ' + msg.format(param_name,
                                                       param_value,
                                                       validation_value) + '\n'
                                )
                else:
                    # print(validation_op, param_value, validation_value)
                    if isinstance(validation_value, six.string_types):
                        validation_value = self.simple_eval(validation_value)
                    else:
                        validation_value = np.full(param_value.shape,
                                                   validation_value)
                    assert param_value.shape == validation_value.shape
                    for idx in np.ndindex(param_value.shape):
                        out_of_range = False
                        if validation_op == 'min' and (param_value[idx] <
                                                       validation_value[idx]):
                            out_of_range = True
                            msg = '{} value {} < min value {}'
                            extra = self._vals[param_name]['out_of_range_minmsg']
                            if extra:
                                msg += ' {}'.format(extra)
                        if validation_op == 'max' and (param_value[idx] >
                                                       validation_value[idx]):
                            out_of_range = True
                            msg = '{} value {} > max value {}'
                            extra = self._vals[param_name]['out_of_range_maxmsg']
                            if extra:
                                msg += ' {}'.format(extra)
                        if out_of_range:
                            self.parameter_errors += (
                                'ERROR: ' + msg.format(
                                    param_name, param_value[idx],
                                    validation_value[idx]) + '\n')
        del dp
        del parameters


# copied from taxcalc.tbi.tbi.reform_errors_warnings--probably needs further
# changes
def reform_warnings_errors(user_mods):
    """
    Generate warnings and errors for OG-USA parameter specifications
    Parameters:
    -----------
    user_mods : dict created by read_json_param_objects
    Return
    ------
    rtn_dict : dict with endpoint specific warning and error messages
    """
    rtn_dict = {'ogusa': {'warnings': '', 'errors': ''}}

    # create Specifications object and implement reform
    specs = Specifications()
    specs._ignore_errors = True
    try:
        specs.update_specifications(user_mods['ogusa'], raise_errors=False)
        rtn_dict['ogusa']['warnings'] = specs.parameter_warnings
        rtn_dict['ogusa']['errors'] = specs.parameter_errors
    except ValueError as valerr_msg:
        rtn_dict['ogusa']['errors'] = valerr_msg.__str__()
    return rtn_dict
