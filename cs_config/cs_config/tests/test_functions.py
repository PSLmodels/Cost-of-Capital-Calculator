from cs_kit import CoreTestFunctions
import pandas as pd
import io
from cs_config import functions


class TestFunctions1(CoreTestFunctions):
    get_version = functions.get_version
    get_inputs = functions.get_inputs
    validate_inputs = functions.validate_inputs
    run_model = functions.run_model,
    ok_adjustment = {"ccc": {"CIT_rate": 0.21}},
    bad_adjustment = {"ccc": {"CIT_rate": -0.1}}


def test_param_effect():
    adjustment = {"ccc": {"CIT_rate": 0.35}}
    comp_dict = functions.run_model({}, adjustment)
    df = pd.read_csv(io.StringIO(comp_dict['downloadable'][0]['data']))
    assert df.loc[0, 'Change from Baseline (pp)'] != 0
