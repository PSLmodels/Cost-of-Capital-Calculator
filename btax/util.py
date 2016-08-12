import os
from pkg_resources import resource_stream, Requirement

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
    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), tfile)
    if not os.path.exists(template_path):
        path_in_egg = os.path.join("btax", tfile)
        buf = resource_stream(Requirement.parse("btax"), path_in_egg)
        _bytes = buf.read()
        contents = str(_bytes)
    else:
        with open(template_path, 'r') as f:
            contents = f.read()
    return contents

def get_paths():
    paths = {}
    _CUR_DIR = os.environ.get('BTAX_CUR_DIR', '.')
    if _CUR_DIR:
         _CUR_DIR = os.path.expanduser(_CUR_DIR)
    if not _CUR_DIR or not os.path.exists(_CUR_DIR):
         paths['_CUR_DIR'] = _CUR_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    else:
         paths['_CUR_DIR'] = _CUR_DIR
    data_dir_guesses = (os.path.join(_CUR_DIR, 'data'),
                        os.path.join(_CUR_DIR, 'btax', 'data'),)
    _MAIN_DIR = None
    for _DATA_DIR in data_dir_guesses:
        if os.path.exists(_DATA_DIR):
            if 'btax' in _DATA_DIR:
                _MAIN_DIR = _CUR_DIR
            else:
                _MAIN_DIR = os.path.dirname(_CUR_DIR)
            break
    if _MAIN_DIR is None:
        raise IOError('Expected one of {} to exist.  Change '
                      'working directory or define '
                      'BTAX_CUR_DIR env var'.format(data_dir_guesses))
    paths['_MAIN_DIR'] = _MAIN_DIR
    paths['_RATE_DIR'] = _RATE_DIR = os.path.join(_DATA_DIR, 'depreciation_rates')
    paths['_REF_DIR'] = os.path.join(_DATA_DIR, 'reference_data')
    paths['_RAW_DIR'] = _RAW_DIR = os.path.join(_DATA_DIR, 'raw_data')
    paths['_DEPR_DIR'] = _DEPR_DIR = os.path.join(_DATA_DIR, 'depreciation_rates')
    paths['_BEA_DIR'] = _BEA_DIR = os.path.join(_RAW_DIR, 'BEA')
    paths['_OUT_DIR'] = os.environ.get('BTAX_OUT_DIR', 'btax_output_dir')
    if not os.path.exists(paths['_OUT_DIR']):
        os.mkdir(paths['_OUT_DIR'])
    paths['_TAX_DEPR'] = os.path.join(_RATE_DIR, 'BEA_IRS_Crosswalk.csv')
    paths['_IND_NAICS'] = os.path.join(_BEA_DIR, 'Industries.csv')
    paths['_BEA_ASSET_PATH'] = _BEA_ASSET_PATH = os.path.join(_BEA_DIR, "detailnonres_stk1.xlsx")
    paths['_BEA_CROSS'] = _BEA_CROSS = os.path.join(_BEA_DIR, 'BEA_Crosswalk.csv')
    paths['_SOI_CROSS'] = _SOI_CROSS = os.path.join(_BEA_DIR, 'NAICS_SOI_crosswalk.csv')
    paths['_SOI_BEA_CROSS'] = _SOI_BEA_CROSS = os.path.join(_BEA_DIR, 'soi_bea_industry_codes.csv')
    paths['_ECON_DEPR_IN_PATH'] = _ECON_DEPR_IN_PATH = os.path.join(_DEPR_DIR, 'Economic Depreciation Rates.csv')
    paths['_TAX_DEPR'] = _TAX_DEPR = os.path.join(_DEPR_DIR, 'BEA_IRS_Crosswalk.csv')
    paths['_NAICS_CODE_PATH'] = _NAICS_CODE_PATH = os.path.join(_DATA_DIR, 'NAICS_Codes.csv')
    paths['_NAICS_PATH'] = _NAICS_PATH = os.path.join(_BEA_DIR, 'NAICS_SOI_crosswalk.csv')
    paths['_SOI_DIR'] = _SOI_DIR = os.path.join(_RAW_DIR, 'soi')
    paths['_CORP_DIR'] = _CORP_DIR = os.path.join(_SOI_DIR, 'soi_corporate')
    paths['_TOT_CORP_IN_PATH'] = _TOT_CORP_IN_PATH = os.path.join(_CORP_DIR, '2011sb1.csv')
    paths['_S_CORP_IN_PATH'] = _S_CORP_IN_PATH = os.path.join(_CORP_DIR, '2011sb3.csv')
    paths['_PRT_DIR'] = _PRT_DIR = os.path.join(_SOI_DIR, 'soi_partner')
    paths['_INC_IN_CROSS_PATH'] = _INC_IN_CROSS_PATH = os.path.join(_PRT_DIR, '12pa01_Crosswalk.csv')
    paths['_AST_IN_CROSS_PATH'] = _AST_IN_CROSS_PATH = os.path.join(_PRT_DIR, '12pa03_Crosswalk.csv')
    paths['_TYP_IN_CROSS_PATH'] = _TYP_IN_CROSS_PATH = os.path.join(_PRT_DIR, '12pa05_Crosswalk.csv')
    paths['_XLS_FILE_1'] = _XLS_FILE_1 = os.path.join(_PRT_DIR, '12pa01.xls')
    paths['_XLS_FILE_2'] = _XLS_FILE_2 = os.path.join(_PRT_DIR, '12pa03.xlsx')
    paths['_INC_FILE'] = _INC_FILE = os.path.join(_PRT_DIR, '12pa01.csv')
    paths['_AST_FILE'] = _AST_FILE = os.path.join(_PRT_DIR, '12pa03.csv')
    paths['_TYP_FILE'] = _TYP_FILE = os.path.join(_PRT_DIR, '12pa05.csv')
    paths['_PROP_DIR'] = _PROP_DIR = os.path.join(_SOI_DIR, 'soi_proprietorship')
    paths['_PRT_DIR'] = _PRT_DIR = os.path.join(_SOI_DIR, 'soi_partner')
    paths['_NFARM_PATH'] = _NFARM_PATH = os.path.join(_PROP_DIR, '12sp01br.csv')
    paths['_FARM_IN_PATH'] = _FARM_IN_PATH = os.path.join(_PROP_DIR, 'farm_data.csv')
    paths['_PRT_INC'] = _PRT_INC = os.path.join(_PRT_DIR, '12pa01.csv')
    paths['_PRT_ASST'] = _PRT_ASST = os.path.join(_PRT_DIR, '12pa03.csv')
    paths['_NFARM_INV'] = _NFARM_INV = os.path.join(_PROP_DIR, '12sp02is.csv')
    paths['_PRT_CROSS'] = _PRT_CROSS = os.path.join(_PRT_DIR, '12pa01_Crosswalk.csv')
    paths['_DDCT_IN_CROSS_PATH'] = _DDCT_IN_CROSS_PATH = os.path.join(_PROP_DIR, '12sp01br_Crosswalk.csv')
    paths['_SOI_CODES'] = _SOI_CODES = os.path.join(_SOI_DIR, 'SOI_codes.csv')
    return paths


def str_modified(i):
    if i == 27.5:
        str_i = '27_5'
    else:
        str_i = str(i)
    return str_i


def _dataframe_to_json_table(df, defaults, label):
    df.to_pickle('check_df1.pkl')
    groups = [x[1]['table_id'] for x in defaults]
    tables = {}
    for group in set(groups):
        new_column_names = [x[1]['col_label'] for x in defaults
                            if x[1]['table_id'] in (group, 'all')]
        keep_columns = [x[0] for x in defaults
                        if x[1]['table_id'] in (group, 'all')]
        df2 = df[keep_columns]
        df2.columns = new_column_names
        header = list(df2.columns)
        df2.to_pickle('check_df2.pkl')
        rows = [[k,] + list(v) for k, v in df2.T.iteritems()]
        tables['{}_{}'.format(label, group)] = header + rows
    return tables

def output_by_asset_to_json_table(df):
    from btax.parameters import DEFAULT_ASSET_COLS

    return _dataframe_to_json_table(df, DEFAULT_ASSET_COLS, 'asset')


def output_by_industry_to_json_table(df):
    from btax.parameters import DEFAULT_INDUSTRY_COLS
    return _dataframe_to_json_table(df, DEFAULT_INDUSTRY_COLS, 'industry')

