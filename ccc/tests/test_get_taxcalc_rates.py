import numpy as np
import pytest
from ccc import get_taxcalc_rates as tc
from ccc.parameters import Specification
from ccc.utils import TC_LAST_YEAR


def test_get_calculator_cps():
    """
    Test the get_calculator() function
    """
    calc1 = tc.get_calculator(True, 2019)
    assert calc1.current_year == 2019


@pytest.mark.needs_puf
@pytest.mark.parametrize(
    "baseline,data",
    [(True, "puf.csv"), (True, None), (False, None)],
    ids=["baseline,data=PUF", "baseline,data=None", "reform,data=None"],
)
def test_get_calculator(baseline, data):
    """
    Test the get_calculator() function
    """
    calc1 = tc.get_calculator(
        baseline,
        2019,
        baseline_policy={"FICA_ss_trt": {2018: 0.15}},
        reform={"FICA_ss_trt": {2018: 0.125}},
        data=data,
    )
    assert calc1.current_year == 2019


def test_get_calculator_exception():
    """
    Test the get_calculator() function
    """
    with pytest.raises(Exception):
        assert tc.get_calculator(True, TC_LAST_YEAR + 1)


def test_get_rates():
    """
    Test of the get_rates() functions
    """
    p = Specification(year=2020)  # has default tax rates, with should equal TC
    test_dict = tc.get_rates(
        baseline=False,
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
