import pytest
from ccc.parameters import Specification, revision_warnings_errors
from ccc.parameters import DepreciationParams


test_data = [(27.5, '27_5'), (30, '30')]


@pytest.mark.parametrize('call_tc', [False, True],
                         ids=['Not use TC', 'Use TC'])
def test_create_specification_object(call_tc):
    spec = Specification(call_tc=call_tc)
    assert spec


def test_default_parameters():
    spec = Specification()
    dps = spec.default_parameters()
    assert dps


def test_update_specification_with_dict():
    cyr = 2020
    spec = Specification(year=cyr)
    new_spec_dict = {
        'profit_rate': 0.4,
        'm': 0.5
    }
    spec.update_specification(new_spec_dict)
    assert spec.profit_rate == 0.4
    assert spec.m == 0.5
    assert len(spec.errors) == 0


def test_new_view():
    cyr = 2020
    spec = Specification(year=cyr)
    new_spec_dict = {
        'new_view': True,
    }
    spec.update_specification(new_spec_dict)
    assert spec.new_view
    assert spec.m == 1


def test_PT_tax():
    cyr = 2020
    spec = Specification(year=cyr)
    new_spec_dict = {
        'PT_entity_tax_ind': True,
        'PT_entity_tax_rate': 0.44
    }
    spec.update_specification(new_spec_dict)
    assert spec.PT_entity_tax_ind
    assert spec.u['nc'] == 0.44


def test_update_specification_with_json():
    cyr = 2020
    spec = Specification(year=cyr)
    new_spec_json = """
    {
    "profit_rate": [
        {
            "year": 2020,
            "value": 0.4
        }
    ],
    "m": [
        {
            "year": 2020,
            "value": 0.5
        }
    ]
    }
    """
    spec.update_specification(new_spec_json)
    assert spec.profit_rate == 0.4
    assert spec.m == 0.5
    assert len(spec.errors) == 0


def test_update_bad_revision1():
    spec = Specification()
    # profit rate has an upper bound at 1.0
    revs = {
        'profit_rate': [{'year': spec.year, 'value': 1.2}]
    }
    spec.update_specification(revs, raise_errors=False)
    assert len(spec.errors) > 0
    first_line = spec.errors['profit_rate'][0]
    print(first_line)
    expected_first_line =\
        'profit_rate[year=2020] 1.2 > max 1.0 '
    assert first_line == expected_first_line


def test_update_bad_revsions2():
    spec = Specification()
    # Pick a category for depreciation that is out of bounds
    revs = {
        'profit_rate': 0.5,
        'PT_entity_tax_rate': 1.2}
    spec.update_specification(revs, raise_errors=False)
    assert len(spec.errors) > 0
    first_line = spec.errors['PT_entity_tax_rate'][0]
    print('First line = ', first_line)
    expected_first_line = (
        'PT_entity_tax_rate 1.2 > max 1.0 '
    )
    assert first_line == expected_first_line


def test_update_bad_revsions3():
    spec = Specification()
    revs = 0.5
    with pytest.raises(Exception):
        assert spec.update_specification(revs, raise_errors=False)


def test_update_bad_revsions4():
    spec = Specification()
    revs = None
    with pytest.raises(Exception):
        assert spec.update_specification(revs, raise_errors=True)


def test_update_bad_revsions5():
    spec = Specification()
    # profit rate has an upper bound at 1.0
    revs = {
        'profit_rate': [{'year': spec.year, 'value': 1.2}]
    }
    with pytest.raises(Exception):
        assert spec.update_specification(revs, raise_errors=True)


def test_read_json_revision():
    """
    Check read_json_revision logic.
    """
    good_revision = """
    {
    "profit_rate": [
        {
            "year": 2020,
            "value": 0.4
        }
    ],
    "m": [
        {
            "year": 2020,
            "value": 0.5
        }
    ]
    }
    """
    # pllint: disable=private-method
    with pytest.raises(ValueError):
        # error because obj argument is neither None nor a string
        Specification._read_json_revision(list())


def test_revision_warnings_errors():
    revs_dict_good = {'profit_rate': [{'year': 2020, 'value': 0.30}]}
    e_w = revision_warnings_errors(revs_dict_good)
    assert len(e_w['warnings']) == 0
    assert len(e_w['errors']) == 0
    revs_dict_bad = {'profit_rate': [{'year': 2020, 'value': -0.10}]}
    e_w = revision_warnings_errors(revs_dict_bad)
    assert len(e_w['warnings']) == 0
    assert len(e_w['errors']) > 0
    revs_dict_badder = 999
    e_w = revision_warnings_errors(revs_dict_badder)
    assert e_w['errors'] ==\
        'ERROR: revision is not a dictionary or string'


def test_create_depreciation_parameters_object():
    dp = DepreciationParams()
    assert dp


def test_update_depreciation_params_with_dict():
    expected_result = [{
        'year': 2020, 'value': {'method': 'Expensing', 'life': 5},
        'GDS_life': 3.0, 'ADS_life': 3.0,
        'major_asset_group': 'Equipment',
        'minor_asset_group': 'Computers and Software', 'system': 'GDS',
        'asset_name': 'Custom software', 'BEA_code': 'ENS2'}]
    dp = DepreciationParams()
    new_dp_dict = {"asset": [
        {"year": 2020,
         "asset_name": "Custom software",
         "value": {"life": 5, "method": "Expensing"}}]}
    dp.adjust(new_dp_dict)
    test_result = dp.select_eq(
        param="asset", exact_match=False, year=2020, BEA_code="ENS2")
    assert test_result == expected_result


def test_update_depreciation_params_with_json():
    expected_result = [{
        'year': 2020, 'value': {'method': 'Expensing', 'life': 5},
        'GDS_life': 3.0, 'ADS_life': 3.0,
        'major_asset_group': 'Equipment',
        'minor_asset_group': 'Computers and Software', 'system': 'GDS',
        'asset_name': 'Custom software', 'BEA_code': 'ENS2'}]
    dp = DepreciationParams()
    new_dp_json = """
        {"asset": [
        {"year": 2020,
         "asset_name": "Custom software",
         "value": {"life": 5, "method": "Expensing"}}]}
         """
    dp.adjust(new_dp_json)
    test_result = dp.select_eq(
        param="asset", exact_match=False, year=2020, BEA_code="ENS2")
    assert test_result == expected_result


def test_update_depreciation_params_as_a_group():
    dp = DepreciationParams()
    new_dp_dict = {
        "asset": [{"major_asset_group": "Intellectual Property",
                   "value": {"life": 12, "method": "DB 200%"}}]}
    dp.adjust(new_dp_dict)
    test_result = dp.select_eq(
        param="asset", exact_match=False, year=2020, major_asset_group="Intellectual Property")
    assert test_result[0]['value']['life'] == 12
    assert test_result[1]['value']['life'] == 12
    assert test_result[2]['value']['life'] == 12


# def test_update_depreciation_bad_revision():
#     '''
#     Check that parameter out of range raises exception
#     '''
#     dp = DepreciationParams()
#     new_dp_dict = {"asset": [
#         {"year": 2020,
#          "asset_name": "Custom software",
#          "value": {"life": 12, "method": "Expensing2"}}]}
#     with pytest.raises(Exception):
#         assert dp.adjust(new_dp_dict)
#
#
# def test_update_depreciation_bad_revision2():
#     '''
#     Check that parameter out of range raises exception
#     '''
#     dp = DepreciationParams()
#     new_dp_dict = {"asset": [
#         {"year": 2020,
#          "asset_name": "Custom software",
#          "value": {"life": 122.0, "method": "Expensing"}}]}
#     with pytest.raises(Exception):
#         assert dp.adjust(new_dp_dict)
