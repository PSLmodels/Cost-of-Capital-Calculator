from cs_kit import CoreTestFunctions
import pandas as pd
import numpy as np
import io
from cs_config import functions


class TestFunctions1(CoreTestFunctions):
    get_version = functions.get_version
    get_inputs = functions.get_inputs
    validate_inputs = functions.validate_inputs
    run_model = functions.run_model
    ok_adjustment = {
        "Business Tax Parameters": {
            "CIT_rate": [
                {
                    "year": 2021,
                    "value": 0.25
                }
            ]
        },
        "Individual and Payroll Tax Parameters": {
            "FICA_ss_trt": [
                {
                    "year": 2021,
                    "value": 0.14
                }
            ]
        }
    }
    bad_adjustment = {"Business Tax Parameters": {"CIT_rate": -0.1},
                      "Individual and Payroll Tax Parameters": {"STD": -1}}


def test_param_effect():
    adjustment = {"Business Tax Parameters": {"CIT_rate": 0.35},
                  "Individual and Payroll Tax Parameters": {}}
    comp_dict = functions.run_model({}, adjustment)
    df1 = pd.read_csv(io.StringIO(comp_dict['downloadable'][0]['data']))
    df2 = pd.read_csv(io.StringIO(comp_dict['downloadable'][1]['data']))
    assert max(np.absolute(df1['rho_mix']-df2['rho_mix'])) > 0
