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
    return paths
