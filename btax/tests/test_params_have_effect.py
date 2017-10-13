from __future__ import unicode_literals
import re

import pytest
import json

from btax.parameters import DEFAULTS, get_params, translate_param_names
from btax.execute import runner
import btax.front_end_util as front_end
from btax.front_end_util import runner_json_tables

front_end.DO_ASSERTIONS = True # Override env var
                               # Always assert table format okay
try:
    unicode
except NameError:
    unicode = str

def tst_once(fast_or_slow, **user_params):
    if fast_or_slow == 'slow':
        # actually run the model
        # and look at the "changed" tables
        json_out = runner_json_tables(**user_params)
        dict_out = json.loads(json_out)
        tables = dict_out['json_table']
        assert isinstance(tables, dict)
        for k, v in tables.items():
            if k in ('row_grouping', 'result_years',):
                continue
            assert 'industry' in k or 'asset' in k
            assert sorted(v) == ['baseline', 'changed', 'reform']
            for base_change_reform, table in v.items():
                expected = set(('rows', 'cols', 'col_labels', 'label'))
                assert expected == set(table)
                rows = table['rows']
                assert rows and isinstance(rows, list)
                for row in rows:
                    assert 'cells' in row and isinstance(row['cells'], list)
                    cells = row['cells']
                    if row.get('summary_c') != 'breakline':
                        assert len(cells) == 6
                        for cell in cells:
                            assert 'value' in cell
                            assert 'format' in cell and isinstance(cell['format'], dict)
                col_labels = table['col_labels']
                assert isinstance(col_labels, list) and len(col_labels) == 6
                assert isinstance(table['label'], unicode) and table['label']
                assert rows[0]['label'] == rows[0]['major_grouping'] == 'All Investments'

    else:
        # just check that when parameter
        # names are standardized a difference
        # is seen from defaults
        user_params = translate_param_names(**user_params)
        default_params = translate_param_names()
        assert user_params != default_params, repr((user_params, default_params))


def tst_each_param_has_effect(fast_or_slow, k, v):
    '''For each parameter in param_defaults/btax_default.json,
    assert that changing the parameter has at least once
    change in the changes tables relative to baseline.
    (Slower-running test)'''
    if 'btax_depr_25yr_exp' == k:
        return # no change expected
    if '_econ_' in k:
        return # this would affect baseline as well as reform
    if k == 'btax_betr_entity_Switch':
        # one may not see a change with this
        # switch unless one of these other params is changed
        user_mods = {'btax_betr_corp': 0.41, 'btax_betr_pass': 0.41}
    else:
        user_mods = {}
    if k in ('btax_betr_corp', 'btax_betr_pass'):
        return # these are tested by btax_betr_entity_Switch test
    pat = 'btax_depr_([\d\w_]+)yr_exp'
    match = re.search(pat, k)
    if match:
        yr = match.groups()[0]
        if yr == 'all':
            return # check all boxes handled by front end
        user_mods['btax_depr_{}yr_tax_Switch'.format(yr)] = True
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
    if isinstance(val, float) and val == 0.:
        val = 0.01
    # Run it with one parameter in non-default mode
    user_mods[k] = val
    try:
        tst_once(fast_or_slow, **user_mods)
    except:
        print(user_mods, val)
        raise


@pytest.mark.parametrize('k,v', [(k,v) for k,v in DEFAULTS
                                  if not (('depr' in k and 'Switch' in k) or 'hover' in k)])
@pytest.mark.needs_puf
@pytest.mark.slow
def test_each_param_has_effect_slow(k, v):
    tst_each_param_has_effect('slow', k, v)


@pytest.mark.parametrize('k,v', [(k,v) for k,v in DEFAULTS
                                  if not (('depr' in k and 'Switch' in k) or 'hover' in k)])
def test_each_param_has_effect_fast(k, v):
    tst_each_param_has_effect('fast', k, v)


def test_gds_ads_econ_switch():
    params = translate_param_names(btax_depr_10yr_ads_Switch=True)
    assert params['deprec_system']['10'] == 'ADS'
    params = translate_param_names()
    assert params['deprec_system']['10'] == 'GDS'
    params = translate_param_names(btax_depr_10yr_tax_Switch=True)
    assert params['deprec_system']['10'] == 'Economic'
