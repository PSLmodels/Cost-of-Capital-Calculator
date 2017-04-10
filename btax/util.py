from __future__ import unicode_literals
from collections import OrderedDict, defaultdict
import numbers
import os
from os.path import join
from pkg_resources import resource_stream, Requirement

import pandas as pd

# Default year for model runs
DEFAULT_START_YEAR = 2017


def to_str(x):
    if hasattr(x, 'decode'):
        return x.decode()
    return x


def read_from_egg(tfile):
    '''Read a relative path, getting the contents
    locally or from the installed egg, parsing the contents
    based on file_type if given, such as yaml
    Params:
        tfile: relative package path
        file_type: file extension such as "json" or "yaml" or None

    Returns:
        contents: yaml or json loaded or raw
    '''
    path = os.path.dirname(os.path.abspath(__file__))
    template_path = join(path, tfile)
    if not os.path.exists(template_path):
        path_in_egg = join("btax", tfile)
        buf = resource_stream(Requirement.parse("btax"), path_in_egg)
        _bytes = buf.read()
        contents = str(_bytes)
    else:
        with open(template_path, 'r') as f:
            contents = f.read()
    return contents


def get_paths():
    paths = {}
    _CUR_DIR = _MAIN_DIR = os.path.dirname(os.path.abspath(__file__))
    _DATA_DIR = os.path.join(_MAIN_DIR, 'data')
    paths['_MAIN_DIR'] = paths['_DATA_DIR'] = _MAIN_DIR
    paths['_RATE_DIR'] = _RATE_DIR = join(_DATA_DIR, 'depreciation_rates')
    paths['_REF_DIR'] = join(_DATA_DIR, 'reference_data')
    paths['_RAW_DIR'] = _RAW_DIR = join(_DATA_DIR, 'raw_data')
    paths['_DEPR_DIR'] = _DEPR_DIR = join(_DATA_DIR, 'depreciation_rates')
    paths['_BEA_DIR'] = _BEA_DIR = join(_RAW_DIR, 'BEA')
    fname = join(_RAW_DIR, 'national_accounts')
    paths['_FIN_ACCT_DIR'] = _FIN_ACCT_DIR = fname
    paths['_OUT_DIR'] = os.environ.get('BTAX_OUT_DIR', 'btax_output_dir')
    if not os.path.exists(paths['_OUT_DIR']):
        os.mkdir(paths['_OUT_DIR'])
    paths['_BEA_ASSET_PATH'] = join(_BEA_DIR, "detailnonres_stk1.xlsx")
    paths['_SOI_BEA_CROSS'] = join(_BEA_DIR, 'soi_bea_industry_codes.csv')
    paths['_BEA_INV'] = join(_BEA_DIR, 'NIPA_5.8.5B.xls')
    paths['_BEA_RES'] = join(_BEA_DIR, 'BEA_StdFixedAsset_Table5.1.xls')
    paths['_LAND_PATH'] = join(_FIN_ACCT_DIR, '')
    paths['_B101_PATH'] = join(_FIN_ACCT_DIR, 'b101.csv')
    fname = join(_DEPR_DIR, 'Economic Depreciation Rates.csv')
    paths['_ECON_DEPR_IN_PATH'] = fname
    paths['_TAX_DEPR'] = join(_DEPR_DIR, 'tax_depreciation_rates.csv')
    paths['_SOI_DIR'] = _SOI_DIR = join(_RAW_DIR, 'soi')
    paths['_CORP_DIR'] = _CORP_DIR = join(_SOI_DIR, 'soi_corporate')
    paths['_TOT_CORP_IN_PATH'] = join(_CORP_DIR, '2013sb1.csv')
    paths['_S_CORP_IN_PATH'] = join(_CORP_DIR, '2013sb3.csv')
    paths['_PRT_DIR'] = _PRT_DIR = join(_SOI_DIR, 'soi_partner')
    fname = join(_PRT_DIR, 'partner_crosswalk_detailed_industries.csv')
    paths['_DETAIL_PART_CROSS_PATH'] = fname
    paths['_INC_FILE'] = join(_PRT_DIR, '13pa01.xls')
    paths['_AST_FILE'] = join(_PRT_DIR, '13pa03.xls')
    paths['_TYP_IN_CROSS_PATH'] = join(_PRT_DIR, '13pa05_Crosswalk.csv')
    paths['_TYP_FILE'] = join(_PRT_DIR, '13pa05.xls')
    paths['_PROP_DIR'] = _PROP_DIR = join(_SOI_DIR, 'soi_proprietorship')
    paths['_PRT_DIR'] = join(_SOI_DIR, 'soi_partner')
    paths['_NFARM_PATH'] = join(_PROP_DIR, '13sp01br.xls')
    paths['_NFARM_INV'] = join(_PROP_DIR, '13sp02is.xls')
    paths['_FARM_IN_PATH'] = join(_PROP_DIR, 'farm_data.csv')
    fname = join(_PROP_DIR, 'detail_sole_prop_crosswalk.csv')
    paths['_DETAIL_SOLE_PROP_CROSS_PATH'] = fname
    paths['_SOI_CODES'] = join(_SOI_DIR, 'SOI_codes.csv')
    return paths


def str_modified(i):
    if i == 27.5:
        str_i = '27_5'
    else:
        str_i = str(int(i))
    return str_i


def diff_two_tables(df1, df2):
    assert tuple(df1.columns) == tuple(df2.columns)
    diffs = OrderedDict()
    for c in df1.columns:
        example = getattr(df1, c).iloc[0]
        can_diff = isinstance(example, numbers.Number)
        if can_diff:
            diffs[c] = getattr(df1, c) - getattr(df2, c)
        else:
            diffs[c] = getattr(df1, c)
    return pd.DataFrame(diffs)


def filter_user_params_for_econ(**user_params):
    return {k: v for k, v in user_params.items()
            if k.startswith('btax_econ_')}
