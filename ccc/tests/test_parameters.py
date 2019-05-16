import os
import tempfile
import pytest
from ccc.parameters import Specifications, revisions_warnings_errors


def test_create_specs_object():
    specs = Specifications()
    assert specs


def test_update_specifications_with_dict():
    cyr = 2020
    specs = Specifications(year=cyr)
    new_specs_dict = {
        'profit_rate': {cyr: 0.4},
        'm': {cyr: 0.5}
    }
    specs.update_specifications(new_specs_dict)
    assert specs.profit_rate == 0.4
    assert specs.m == 0.5
    assert len(specs.parameter_errors) == 0


def test_update_specifications_with_json():
    cyr = 2020
    specs = Specifications(year=cyr)
    new_specs_json = """
    {
        "profit_rate": {"2020": 0.4},
        "m": {"2020": 0.5}
    }
    """
    new_specs_dict = Specifications.read_json_revisions(new_specs_json)
    specs.update_specifications(new_specs_dict)
    assert specs.profit_rate == 0.4
    assert specs.m == 0.5
    assert len(specs.parameter_errors) == 0


def test_update_bad_revisions1():
    specs = Specifications()
    # profit rate has an upper bound at 1.0
    revs = {
        'profit_rate': {specs.current_year: 1.2}
    }
    specs.update_specifications(revs, raise_errors=False)
    assert len(specs.parameter_errors) > 0
    first_line = specs.parameter_errors.split('\n')[0]
    print(first_line)
    expected_first_line = 'ERROR: 2019 profit_rate value 1.2 > max value 1.0'
    assert first_line == expected_first_line


def test_update_bad_revsions2():
    specs = Specifications()
    cyr = specs.current_year
    # Pick a category for depreciation that is out of bounds
    revs = {
        'profit_rate': {cyr: 0.5},
        'DeprecSystem_3yr': {cyr: 'not_a_deprec_system'}
    }
    specs.update_specifications(revs, raise_errors=False)
    assert len(specs.parameter_errors) > 0
    first_line = specs.parameter_errors.split('\n')[0]
    print(first_line)
    expected_first_line = (
        "ERROR: 2019 DeprecSystem_3yr value 'not_a_deprec_sys' "
        "not in ['GDS', 'ADS', 'Economic']"
    )
    assert first_line == expected_first_line


def test_revisions_warnings_errors():
    revs_dict_good = {'profit_rate': {2020: 0.30}}
    e_w = revisions_warnings_errors(revs_dict_good)
    assert len(e_w['warnings']) == 0
    assert len(e_w['errors']) == 0
    revs_dict_bad = {'profit_rate': {2020: -0.10}}
    e_w = revisions_warnings_errors(revs_dict_bad)
    assert len(e_w['warnings']) == 0
    assert len(e_w['errors']) > 0
