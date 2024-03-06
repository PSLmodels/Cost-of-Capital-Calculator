from cs_kit import CoreTestFunctions
import pandas as pd
import numpy as np
import io
from cs_config import functions
from ccc.utils import DEFAULT_START_YEAR


def test_start_year_with_data_source():
    """
    Test interaction between PUF and CPS data sources and the start year.
    """
    data = functions.get_inputs({"data_source": "PUF"})
    assert (
        data["meta_parameters"]["year"]["validators"]["choice"]["choices"][0]
        == 2013
    )
    data = functions.get_inputs({"data_source": "CPS"})
    assert (
        data["meta_parameters"]["year"]["validators"]["choice"]["choices"][0]
        == 2014
    )

    ew = {
        "Business Tax Parameters": {"errors": {}, "warnings": {}},
        "Individual and Payroll Tax Parameters": {
            "errors": {},
            "warnings": {},
        },
    }
    res = functions.validate_inputs(
        {"data_source": "CPS", "year": 2013},
        {
            "Business Tax Parameters": {},
            "Individual and Payroll Tax Parameters": {},
        },
        ew,
    )
    assert res["errors_warnings"]["Business Tax Parameters"]["errors"].get(
        "year"
    )


class TestFunctions1(CoreTestFunctions):
    get_version = functions.get_version
    get_inputs = functions.get_inputs
    validate_inputs = functions.validate_inputs
    run_model = functions.run_model
    ok_adjustment = {
        "Business Tax Parameters": {
            "CIT_rate": [{"year": DEFAULT_START_YEAR, "value": 0.25}]
        },
        "Individual and Payroll Tax Parameters": {
            "FICA_ss_trt": [{"year": DEFAULT_START_YEAR, "value": 0.14}]
        },
    }
    bad_adjustment = {
        "Business Tax Parameters": {"CIT_rate": -0.1},
        "Individual and Payroll Tax Parameters": {"STD": -1},
    }


def test_param_effect():
    adjustment = {
        "Business Tax Parameters": {"CIT_rate": 0.35},
        "Individual and Payroll Tax Parameters": {},
    }
    comp_dict = functions.run_model({}, adjustment)
    df1 = pd.read_csv(io.StringIO(comp_dict["downloadable"][0]["data"]))
    df2 = pd.read_csv(io.StringIO(comp_dict["downloadable"][1]["data"]))
    assert max(np.absolute(df1["rho_mix"] - df2["rho_mix"])) > 0
