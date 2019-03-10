import pytest
import os
import pandas as pd
import json
import numpy as np
from pandas.util.testing import assert_frame_equal
from btax import run_btax
from btax.parameters import Specifications

CUR_PATH = os.path.abspath(os.path.dirname(__file__))

# Load input values
input_tuple = tuple(json.load(open(os.path.join(
    CUR_PATH, 'run_btax_inputs.json'))))
test_run, baseline, start_year, iit_reform, data, user_params = input_tuple
result_by_asset = pd.read_json(os.path.join(
    CUR_PATH, 'run_btax_asset_output.json'))
result_by_industry = pd.read_json(os.path.join(
    CUR_PATH, 'run_btax_industry_output.json'))
parameters = Specifications(year=start_year, call_tc=True,
                            iit_reform=iit_reform)
test_by_asset, test_by_industry = run_btax.run_btax(
    parameters, baseline, data='cps')

# Lists of variables to compare
asset_var_list = ['delta', 'z_c', 'z_c_d', 'z_c_e', 'z_nc',
                  'z_nc_d', 'z_nc_e', 'rho_c', 'rho_c_d', 'rho_c_e',
                  'rho_nc', 'rho_nc_d', 'rho_nc_e', 'ucc_c',
                  'ucc_c_d', 'ucc_c_e', 'ucc_nc', 'ucc_nc_d',
                  'ucc_nc_e', 'metr_c', 'metr_c_d', 'metr_c_e',
                  'metr_nc', 'metr_nc_d', 'metr_nc_e', 'mettr_c',
                  'mettr_c_d', 'mettr_c_e', 'mettr_nc',
                  'mettr_nc_d', 'mettr_nc_e', 'assets_c',
                  'assets_nc']
industry_var_list = ['delta_c', 'delta_c', 'z_c', 'z_c_d', 'z_c_e',
                     'z_nc', 'z_nc_d', 'z_nc_e', 'rho_c', 'rho_c_d',
                     'rho_c_e', 'rho_nc', 'rho_nc_d', 'rho_nc_e',
                     'ucc_c', 'ucc_c_d', 'ucc_c_e', 'ucc_nc',
                     'ucc_nc_d', 'ucc_nc_e', 'metr_c', 'metr_c_d',
                     'metr_c_e', 'metr_nc', 'metr_nc_d',
                     'metr_nc_e', 'mettr_c', 'mettr_c_d',
                     'mettr_c_e', 'mettr_nc', 'mettr_nc_d',
                     'mettr_nc_e', 'assets_c', 'assets_nc']


@pytest.mark.parametrize('test_params,expected',
                         [((asset_var_list, test_by_asset),
                           result_by_asset),
                          ((industry_var_list, test_by_industry),
                           result_by_industry)],
                         ids=['by assset', 'by industry'])
def test_run_btax_asset(test_params, expected):
    # Test the run_btax.run_btax() function by reading in inputs and
    # confirming that output variables have the same values.
    var_list, test_df = test_params
    test_df.sort_index(inplace=True)
    test_df.reset_index(inplace=True)
    expected.sort_index(inplace=True)
    expected.reset_index(inplace=True)

    for item in var_list:
        assert np.allclose(test_df[item], expected[item], atol=1e-5)
    # assert_frame_equal(test_df[var_list], expected[var_list],
    #                    check_dtype=False, check_index_type=False,
    #                    check_exact=False, check_less_precise=2)
