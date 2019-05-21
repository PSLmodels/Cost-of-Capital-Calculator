import os
import tempfile
import pytest
from ccc.parameters import Specification, revision_warnings_errors


def test_create_specification_object():
    spec = Specification()
    assert spec


def test_update_specification_with_dict():
    cyr = 2020
    spec = Specification(year=cyr)
    new_spec_dict = {
        'profit_rate': {cyr: 0.4},
        'm': {cyr: 0.5}
    }
    spec.update_specification(new_spec_dict)
    assert spec.profit_rate == 0.4
    assert spec.m == 0.5
    assert len(spec.parameter_errors) == 0


def test_update_specification_with_json():
    cyr = 2020
    spec = Specification(year=cyr)
    new_spec_json = """
    {
        "profit_rate": {"2020": 0.4},
        "m": {"2020": 0.5}
    }
    """
    new_spec_dict = Specification.read_json_revision(new_spec_json)
    spec.update_specification(new_spec_dict)
    assert spec.profit_rate == 0.4
    assert spec.m == 0.5
    assert len(spec.parameter_errors) == 0


def test_update_bad_revision1():
    spec = Specification()
    # profit rate has an upper bound at 1.0
    revs = {
        'profit_rate': {spec.current_year: 1.2}
    }
    spec.update_specification(revs, raise_errors=False)
    assert len(spec.parameter_errors) > 0
    first_line = spec.parameter_errors.split('\n')[0]
    print(first_line)
    expected_first_line = 'ERROR: 2019 profit_rate value 1.2 > max value 1.0'
    assert first_line == expected_first_line


def test_update_bad_revsions2():
    spec = Specification()
    cyr = spec.current_year
    # Pick a category for depreciation that is out of bounds
    revs = {
        'profit_rate': {cyr: 0.5},
        'DeprecSystem_3yr': {cyr: 'not_a_deprec_system'}
    }
    spec.update_specification(revs, raise_errors=False)
    assert len(spec.parameter_errors) > 0
    first_line = spec.parameter_errors.split('\n')[0]
    print(first_line)
    expected_first_line = (
        "ERROR: 2019 DeprecSystem_3yr value 'not_a_deprec_sys' "
        "not in ['GDS', 'ADS', 'Economic']"
    )
    assert first_line == expected_first_line


def test_revision_warnings_errors():
    revs_dict_good = {'profit_rate': {2020: 0.30}}
    e_w = revision_warnings_errors(revs_dict_good)
    assert len(e_w['warnings']) == 0
    assert len(e_w['errors']) == 0
    revs_dict_bad = {'profit_rate': {2020: -0.10}}
    e_w = revision_warnings_errors(revs_dict_bad)
    assert len(e_w['warnings']) == 0
    assert len(e_w['errors']) > 0
