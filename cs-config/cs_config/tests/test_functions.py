from cs_kit import CoreTestFunctions
import pandas as pd
import io
from cs_config import functions, helpers


class TestFunctions1(CoreTestFunctions):
    get_version = functions.get_version
    get_inputs = functions.get_inputs
    validate_inputs = functions.validate_inputs
    run_model = functions.run_model
    ok_adjustment = {"ccc": {"CIT_rate": 0.21}, "iit": {"STD": -1}}
    bad_adjustment = {"ccc": {"CIT_rate": -0.1}, "iit": {}}


def test_param_effect():
    adjustment = {"ccc": {"CIT_rate": 0.35}}
    comp_dict = functions.run_model({}, adjustment)
    df = pd.read_csv(io.StringIO(comp_dict['downloadable'][0]['data']))
    assert df.loc[0, 'Change from Baseline (pp)'] != 0


def test_convert_adj():
    adj = {
        "STD": [
            {"MARS": "single", "year": "2019", "value": 0},
            {"MARS": "mjoint", "year": 2019, "value": 1}
        ],
        "EITC_c": [{"EIC": "0kids", "year": "2019", "value": 1000.0}],
        "BEN_ssi_repeal": [
            {"year": 2019, "value": True}
        ]
    }
    res = helpers.convert_adj(adj, 2019)
    assert res == {
        "STD": {
            2019: [0, 1, 12268.8, 18403.2, 24537.6]
        },
        "EITC_c": {
            2019: [1000.0, 3538.53, 5844.04, 6575.05]
        },
        "BEN_ssi_repeal": {
            2019: True
        }
    }
