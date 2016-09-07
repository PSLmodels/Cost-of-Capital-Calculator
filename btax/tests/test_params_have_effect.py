import pytest

from btax.parameters import DEFAULTS, get_params, translate_param_names
from btax.run_btax import run_btax_to_json_tables

def tst_once(**user_params):
    tables = run_btax_to_json_tables(**user_params)
    has_changed = False
    for k in tables:
        changed = tables[k]['changed']

        for row in changed:
            for item in row:
                if isinstance(item, (float, int)) and item:
                    has_changed = True
                    break
            if has_changed:
                break
        if has_changed:
            break
    assert has_changed


@pytest.mark.parametrize('k,v', DEFAULTS)
@pytest.mark.slow
def test_each_param_has_effect(k, v):
    '''For each parameter in param_defaults/btax_default.json,
    assert that changing the parameter has at least once
    change in the changes tables relative to baseline.
    (Slower-running test)'''
    default = v['value'][0]
    # come up with a reasonable non-default value to put in
    if isinstance(default, bool):
        val = not default
    elif v.get('min') and v.get('max'):
        val = (v['max'][0] + v['min'][0]) / 2.1
    elif isinstance(default, int):
        val = default + 1
    else:
        val = default + 0.05
    # Run it with one parameter in non-default mode
    tst_once(**{k: val})


def test_gds_ads_econ_switch():
    params = translate_param_names(btax_depr_10yr_ads_Switch=True)
    assert params['deprec_system']['10'] == 'ADS'
    params = translate_param_names()
    assert params['deprec_system']['10'] == 'GDS'
    params = translate_param_names(btax_depr_10yr_tax_Switch=True)
    assert params['deprec_system']['10'] == 'Economic'
