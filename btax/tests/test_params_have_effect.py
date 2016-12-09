from __future__ import unicode_literals
import re

import pytest

from btax.parameters import DEFAULTS, get_params, translate_param_names
from btax.run_btax import run_btax_to_json_tables
import btax.front_end_util as front_end

front_end.DO_ASSERTIONS = True # Override env var
                               # Always assert table format okay

'''
In [5]: out.keys()
Out[5]:
[u'result_years',
 u'asset_coc',
 u'row_grouping',
 u'asset_metr',
 u'industry_coc',
 u'industry_metr',
 u'asset_d',
 u'asset_mettr',
 u'industry_mettr',
 u'industry_d']

In [6]: out['asset_coc'].keys()
Out[6]: [u'changed', u'baseline', u'reform']

In [7]: out['asset_coc']['reform'].keys()
Out[7]: [u'rows', u'cols', u'col_labels', u'label']

In [8]: out['asset_coc']['reform']['rows'][0]
Out[8]:
{u'cells': [{u'format': {u'decimals': 3, u'divisor': 1},
   u'value': 0.054075875868831835},
  {u'format': {u'decimals': 3, u'divisor': 1}, u'value': 0.049378622614844193},
  {u'format': {u'decimals': 3, u'divisor': 1}, u'value': 0.068006044700832463},
  {u'format': {u'decimals': 3, u'divisor': 1}, u'value': 0.058667865312829387},
  {u'format': {u'decimals': 3, u'divisor': 1}, u'value': 0.024835825969646917},
  {u'format': {u'decimals': 3, u'divisor': 1},
   u'value': 0.026810612762980194}],
 u'label': u'Equipment',
 u'major_grouping': u'Equipment',
 u'summary_c': u'0.167',
 u'summary_nc': u'0.101'}

In [9]: out['asset_coc']['reform']['cols'][0]
Out[9]:
{u'decimals': 3,
 u'divisor': 1,
 u'label': u'Cost of capital, typically-financed corporate investment',
 u'units': u''}

In [10]: out['asset_coc']['reform']['col_labels']
Out[10]:
[u'Cost of capital, typically-financed corporate investment',
 u'Cost of capital, typically-financed non-corporate investment',
 u'Cost of capital, equity-financed corporate investment',
 u'Cost of capital, equity-financed non-corporate investment',
 u'Cost of capital, debt-financed corporate investment',
 u'Cost of capital, debt-financed non-corporate investment']

In [11]: out['asset_coc']['reform']['label']
Out[11]: u'reform'
'''
def tst_once(fast_or_slow, **user_params):
    if fast_or_slow == 'slow':
        # actually run the model
        # and look at the "changed" tables
        tables = run_btax_to_json_tables(**user_params)
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
    else:
        # just check that when parameter
        # names are standardized a difference
        # is seen from defaults
        user_params = translate_param_names(**user_params)
        default_params = translate_param_names()
        assert user_params != default_params


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
    # Run it with one parameter in non-default mode
    user_mods[k] = val
    tst_once(fast_or_slow, **user_mods)


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
