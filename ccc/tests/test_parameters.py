import os
import tempfile
import pytest
from ccc.parameters import Specifications, reform_warnings_errors


JSON_REVISION_FILE = """{
    "revision": {
        "CIT_rate": 0.3
    }
}"""


@pytest.fixture(scope='module')
def revision_file():
    f = tempfile.NamedTemporaryFile(mode="a", delete=False)
    f.write(JSON_REVISION_FILE)
    f.close()
    # Must close and then yield for Windows platform
    yield f
    os.remove(f.name)


def test_create_specs_object():
    specs = Specifications()
    assert specs


def test_read_json_params_objects(revision_file):
    exp = {"revision": {"CIT_rate": 0.3}}
    act1 = Specifications.read_json_param_objects(JSON_REVISION_FILE)
    assert exp == act1
    act2 = Specifications.read_json_param_objects(JSON_REVISION_FILE)
    assert exp == act2


def test_implement_reform():
    specs = Specifications()
    new_specs = {
        'profit_rate': 0.4,
        'm': 0.5
    }

    specs.update_specifications(new_specs)
    assert specs.profit_rate == 0.4
    assert specs.m == 0.5
    assert len(specs.errors) == 0


def test_implement_bad_reform1():
    specs = Specifications()
    # profit rate has an upper bound at 1.0
    new_specs = {
        'profit_rate': 1.2
    }

    specs.update_specifications(new_specs, raise_errors=False)

    assert len(specs.errors) > 0
    print(specs.errors)
    exp = {'profit_rate': ['profit_rate 1.2 must be less than 1.0.']}
    assert specs.errors == exp


def test_implement_bad_reform2():
    specs = Specifications()
    # Pick a category for depreciation that is out of bounds
    new_specs = {
        'profit_rate': 0.5,
        'DeprecSystem_3yr': 'not_a_deprec_system'
    }

    specs.update_specifications(new_specs, raise_errors=False)

    assert len(specs.errors) > 0
    exp = {
        'DeprecSystem_3yr': [
            'DeprecSystem_3yr "not_a_deprec_system" must be in list of choices GDS, ADS, Economic.'
        ]
    }
    assert specs.errors == exp



def test_reform_warnings_errors():
    user_mods = {'ccc': {'profit_rate': 0.3}}

    ew = reform_warnings_errors(user_mods)
    assert len(ew['ccc']['errors']) == 0
    assert len(ew['ccc']['warnings']) == 0

    user_mods = {'ccc': {'profit_rate': -0.1}}

    bad_ew = reform_warnings_errors(user_mods)
    assert len(bad_ew['ccc']['errors']) > 0
    assert len(bad_ew['ccc']['warnings']) == 0


# def test_simple_eval():
#     specs = Specifications()
#     specs.profit_rate = 1.0
#     assert specs.simple_eval('profit_rate / 2') == 0.5
#     assert specs.simple_eval('profit_rate * 2') == 2.0
#     assert specs.simple_eval('profit_rate - 2') == -1.0
#     assert specs.simple_eval('profit_rate + 2') == 3.0
