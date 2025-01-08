import numpy as np
import pytest
import os
from pathlib import Path
from ccc import get_taxcalc_rates as tc
from ccc.parameters import Specification
from ccc.utils import TC_LAST_YEAR


CUR_DIR = os.path.abspath(os.path.dirname(__file__))


@pytest.mark.parametrize(
    "reform",
    [(None), ({"FICA_ss_trt_employee": {2018: 0.0625}})],
    ids=["baseline", "reform"],
)
def test_get_calculator_cps(reform):
    """
    Test the get_calculator() function
    """
    calc1 = tc.get_calculator(
        2019,
        baseline_policy={"FICA_ss_trt_employee": {2018: 0.075}},
        reform=reform,
    )
    assert calc1.current_year == 2019
    if reform is None:
        assert calc1.policy_param("FICA_ss_trt_employee") == 0.075
    else:
        assert calc1.policy_param("FICA_ss_trt_employee") == 0.0625


@pytest.mark.needs_puf
@pytest.mark.parametrize(
    "data",
    [("puf.csv"), (None)],
    ids=["baseline,data=PUF", "baseline,data=None"],
)
def test_get_calculator_puf(data):
    """
    Test the get_calculator() function
    """
    calc1 = tc.get_calculator(
        2019,
        baseline_policy={"FICA_ss_trt_employee": {2018: 0.075}},
        reform={"FICA_ss_trt_employee": {2018: 0.0625}},
        data=data,
    )
    assert calc1.current_year == 2019


@pytest.mark.needs_tmd
@pytest.mark.parametrize(
    "data,weights,growfactors",
    [
        (
            Path(os.path.join(CUR_DIR, "tmd.csv")),
            Path(os.path.join(CUR_DIR, "tmd_weights.csv.gz")),
            Path(os.path.join(CUR_DIR, "tmd_growfactors.csv")),
        )
    ],
    ids=["baseline,data=TMD"],
)
def test_get_calculator_tmd(data, weights, growfactors):
    """
    Test the get_calculator() function
    """
    calc1 = tc.get_calculator(
        2021,
        baseline_policy={"FICA_ss_trt_employee": {2021: 0.075}},
        reform={"FICA_ss_trt_employee": {2022: 0.0625}},
        data=data,
        weights=weights,
        gfactors=growfactors,
    )
    assert calc1.current_year == 2021


def test_get_calculator_exception():
    """
    Test the get_calculator() function
    """
    with pytest.raises(Exception):
        assert tc.get_calculator(TC_LAST_YEAR + 1)


def test_get_rates():
    """
    Test of the get_rates() functions
    """
    p = Specification(year=2020)  # has default tax rates, with should equal TC
    test_dict = tc.get_rates(
        start_year=2020,
        baseline_policy={},
        reform={},
        data="cps",
    )
    for k, v in test_dict.items():
        print("Tax rate = ", k)
        assert np.allclose(v, p.__dict__[k], atol=1e-4)


@pytest.mark.parametrize(
    "reform,expected",
    [({"key1": {"key2": 1.0}}, False), ({"key1": "string"}, True)],
    ids=["assert False", "assert True"],
)
def test_is_paramtools_format(reform, expected):
    """
    Test get_taxcalc_rates.is_paramtools_format function.
    """
    returned_value = tc.is_paramtools_format(reform)

    assert expected == returned_value
