import json
import os
import six
import re
import numpy as np
import pickle
import pkg_resources

# import ccc
from ccc.parametersbase import ParametersBase
from ccc.get_taxcalc_rates import get_rates
from ccc.utils import DEFAULT_START_YEAR


class Specifications(ParametersBase):
    """
    Inherits ParametersBase. Implements the PolicyBrain API for
    Cost-of-Capital-Calculator
    """
    DEFAULTS_FILENAME = 'default_parameters.json'

    def __init__(self, test=False, time_path=True, baseline=False,
                 year=DEFAULT_START_YEAR, call_tc=False, iit_reform={},
                 data='cps'):
        super(Specifications, self).__init__()

        # reads in default parameter values
        self._vals = self._params_dict_from_json_file()

        self.test = test
        self.baseline = baseline
        self.year = year
        self.iit_reform = iit_reform
        self.data = data

        # put Cost-of-Capital-Calculator version in parameters to save
        # for reference
        self.ccc_version = pkg_resources.get_distribution("ccc").version

        if call_tc:
            # Find individual income tax rates from Tax-Calculator
            indiv_rates = get_rates(self.baseline, self.year,
                                    self.iit_reform, self.data)
        else:
            # Set indiv rates to some values
            indiv_rates = {'tau_nc': np.array([0.1929392]),
                           'tau_div': np.array([0.1882453]),
                           'tau_int': np.array([0.31239301]),
                           'tau_scg': np.array([0.29068557]),
                           'tau_lcg': np.array([0.18837299]),
                           'tau_td': np.array([0.21860396]),
                           'tau_h': np.array([0.04376291])}
        self.tau_nc = indiv_rates['tau_nc']
        self.tau_div = indiv_rates['tau_div']
        self.tau_int = indiv_rates['tau_int']
        self.tau_scg = indiv_rates['tau_scg']
        self.tau_lcg = indiv_rates['tau_lcg']
        self.tau_xcg = 0.00  # tax rate on capital gains held to death
        self.tau_td = indiv_rates['tau_td']
        self.tau_h = indiv_rates['tau_h']

        # does cheap calculations to find parameter values
        self.initialize()

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
            # choose just value for one year
            data_startyear = data.get('start_year', None)
            try:
                if len(values) > 1:
                    value = values[self.year - data_startyear]
                else:
                    value = values
            except TypeError:
                value = values

            # this if statement is to avoid errors when trying to
            # expand list of all strings
            if string_val:
                # pass
                setattr(self, name, self._expand_array(
                    value, intg_val, bool_val, string_val))
            else:
                # setattr(self, name, self._expand_array(
                #     values, intg_val, bool_val, string_val))
                setattr(self, name, self._expand_array(
                    value, intg_val, bool_val, string_val))

        self.compute_default_params()

    def compute_default_params(self):
        """
        Does cheap calculations to return parameter values
        """
        self.financing_list = ['mix', 'd', 'e']
        self.entity_list = ['c', 'nc']

        # Compute required after-tax rates of return for savers
        sprime_c_td = ((1 / self.Y_td) *
                       np.log(((1 - self.tau_td) *
                               np.exp(self.nominal_interest_rate *
                                      self.Y_td)) + self.tau_td) -
                       self.inflation_rate)
        s_c_d_td = (self.gamma * (self.nominal_interest_rate -
                                  self.inflation_rate) +
                    (1 - self.gamma) * sprime_c_td)
        s_c_d = (self.alpha_c_d_ft * (((1 - self.tau_int) *
                                       self.nominal_interest_rate) -
                                      self.inflation_rate) +
                 self.alpha_c_d_td * s_c_d_td + self.alpha_c_d_nt *
                 (self.nominal_interest_rate - self.inflation_rate))
        s_nc_d_td = s_c_d_td
        s_nc_d = (self.alpha_nc_d_ft * (((1 - self.tau_int) *
                                         self.nominal_interest_rate) -
                                        self.inflation_rate) +
                  self.alpha_nc_d_td * s_nc_d_td + self.alpha_nc_d_nt *
                  (self.nominal_interest_rate - self.inflation_rate))

        g_scg = ((1 / self.Y_scg) * np.log(((1 - self.tau_scg) *
                                            np.exp((self.inflation_rate
                                                    + self.m * self.E_c)
                                                   * self.Y_scg)) +
                                           self.tau_scg) -
                 self.inflation_rate)
        g_lcg = ((1 / self.Y_lcg) * np.log(((1 - self.tau_lcg) *
                                            np.exp((self.inflation_rate
                                                    + self.m * self.E_c)
                                                   * self.Y_lcg)) +
                                           self.tau_lcg) -
                 self.inflation_rate)
        g = (self.omega_scg * g_scg + self.omega_lcg * g_lcg +
             self.omega_xcg * self.m * self.E_c)
        s_c_e_ft = (1 - self.m) * self.E_c * (1 - self.tau_div) + g
        s_c_e_td = ((1 / self.Y_td) *
                    np.log(((1 - self.tau_td) *
                            np.exp((self.inflation_rate + self.E_c) *
                                   self.Y_td)) + self.tau_td) -
                    self.inflation_rate)
        s_c_e = (self.alpha_c_e_ft * s_c_e_ft + self.alpha_c_e_td *
                 s_c_e_td + self.alpha_c_e_nt * self.E_c)

        s_c = self.f_c * s_c_d + (1 - self.f_c) * s_c_e

        E_nc = s_c_e
        s_nc_e = E_nc
        s_nc = self.f_nc * s_nc_d + (1 - self.f_nc) * s_nc_e
        self.u = {'c': self.CIT_rate}
        if not self.PT_entity_tax_ind:
            self.u['nc'] = self.tau_nc
        else:
            self.u['nc'] = self.PT_entity_tax_rate
        E_dict = {'c': self.E_c, 'nc': E_nc}
        # Allowance for Corporate Equity
        ace_dict = {'c': self.ace_c, 'nc': self.ace_nc}
        # Limitation on interest deduction
        int_haircut_dict = {'c': self.interest_deduct_haircut_corp,
                            'nc': self.interest_deduct_haircut_PT}
        self.s = {'c': {'mix': s_c, 'd': s_c_d, 'e': s_c_e},
                  'nc': {'mix': s_nc, 'd': s_nc_d, 'e': s_nc_e}}
        f_dict = {'c': {'mix': self.f_c, 'd': 1.0, 'e': 0.0},
                  'nc': {'mix': self.f_nc, 'd': 1.0, 'e': 0.0}}
        # Compute firm discount factors
        r = {}
        for t in self.entity_list:
            r[t] = {}
            for f in self.financing_list:
                r[t][f] = (
                    f_dict[t][f] * (self.nominal_interest_rate *
                                    (1 - (1 - int_haircut_dict[t]) *
                                     self.u[t])) + (1 - f_dict[t][f]) *
                    (E_dict[t] + self.inflation_rate - E_dict[t] *
                     self.ace_int_rate * ace_dict[t]))
        # Compute firm after-tax rates of return
        r_prime = {}
        for t in self.entity_list:
            r_prime[t] = {}
            for f in self.financing_list:
                r_prime[t][f] = (
                    f_dict[t][f] * self.nominal_interest_rate +
                    (1 - f_dict[t][f]) * (E_dict[t] +
                                          self.inflation_rate))

        # if no entity level taxes on pass-throughs, ensure mettr and metr
        # on non-corp entities the same
        if not self.PT_entity_tax_ind:
            for f in self.financing_list:
                r_prime['nc'][f] = self.s['nc'][f] + self.inflation_rate
        # If entity level tax, assume distribute earnings at same rate corps
        # distribute dividends and these are taxed at dividends tax rate
        # (which seems likely).  Also implicitly assumed that if entity
        # level tax, then only additional taxes on pass-through income are
        # capital gains and dividend taxes
        else:
            # keep debt and equity financing ratio the same even though now
            # entity level tax that might now favor debt
            self.s['nc']['mix'] = self.f_nc * s_nc_d + (1 - self.f_nc) * s_c_e
            self.s['c']['e'] = s_c_e
        self.tax_methods = {'DB 200%': 2.0, 'DB 150%': 1.5, 'SL': 1.0,
                            'Economic': 1.0, 'Expensing': 1.0}
        self.r = r
        self.r_prime = r_prime

        # Create dictionaries with depreciation system and rate of bonus
        # depreciation by asset class
        class_list = [3, 5, 7, 10, 15, 20, 25, 27.5, 39]
        class_list_str = [(str(i) if i != 27.5 else '27_5') for i in
                          class_list]
        self.deprec_system = {}
        self.bonus_deprec = {}
        for cl in class_list_str:
            self.deprec_system[cl] = getattr(self,
                                             'DeprecSystem_{}yr'.format(cl))
            self.bonus_deprec[cl] = getattr(self,
                                            'BonusDeprec_{}yr'.format(cl))
        # to handle land and inventories
        # this is fixed later, but should work on this
        self.bonus_deprec['100'] = 0.0

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
    Generate warnings and errors for Cost-of-Capital-Calculator parameter specifications
    Parameters:
    -----------
    user_mods : dict created by read_json_param_objects
    Return
    ------
    rtn_dict : dict with endpoint specific warning and error messages
    """
    rtn_dict = {'ccc': {'warnings': '', 'errors': ''}}

    # create Specifications object and implement reform
    specs = Specifications()
    specs._ignore_errors = True
    try:
        specs.update_specifications(user_mods['ccc'], raise_errors=False)
        rtn_dict['ccc']['warnings'] = specs.parameter_warnings
        rtn_dict['ccc']['errors'] = specs.parameter_errors
    except ValueError as valerr_msg:
        rtn_dict['ccc']['errors'] = valerr_msg.__str__()
    return rtn_dict
