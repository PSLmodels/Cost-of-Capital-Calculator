from __future__ import unicode_literals
from collections import OrderedDict, defaultdict
import numbers
import os
import json
from pkg_resources import resource_stream, Requirement
import pandas as pd

# Default year for model runs
DEFAULT_START_YEAR = 2018

# Year of asset data
ASSET_DATA_CSV_YEAR = 2013

# Start year for tax data (e.g. year of PUF)
RECORDS_START_YEAR = 2011

# Latest year TaxData extrapolates to
TC_LAST_YEAR = 2027


def to_str(x):
    """
    Function to decode string.

    Args:
        x: string, string to decode

    Returns:
        x: string, decoded string
    """
    if hasattr(x, 'decode'):
        return x.decode()
    return x


def read_from_egg(tfile):
    '''
    Read a relative path, getting the contents locally or from the
    installed egg, parsing the contents based on file_type if given,
    such as yaml.

    Args:
        tfile: string, relative package path

    Returns:
        contents: yaml or json, loaded or raw
    '''
    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 tfile)
    if not os.path.exists(template_path):
        path_in_egg = os.path.join("ccc", tfile)
        buf = resource_stream(Requirement.parse("ccc"), path_in_egg)
        _bytes = buf.read()
        contents = str(_bytes)
    else:
        with open(template_path, 'r') as f:
            contents = f.read()
    return contents


DEFAULT_ASSET_COLS = json.loads(read_from_egg
                                (os.path.join('param_defaults',
                                              'ccc_results_by_asset.json')))
DEFAULT_INDUSTRY_COLS = json.loads(read_from_egg
                                   (os.path.join('param_defaults',
                                                 'ccc_results_by_industry.json')))


def get_paths():
    """
    Function to define constants that contain strings with paths to the
    various datafiles Cost-of-Capital-Calculator relies on.

    Args:
        None

    Returns:
        paths: list, list of strings that are the paths to data
    """
    paths = {}
    _CUR_DIR = _MAIN_DIR = os.path.dirname(os.path.abspath(__file__))
    _DATA_DIR = os.path.join(_MAIN_DIR, 'data')
    paths['_MAIN_DIR'] = paths['_DATA_DIR'] = _MAIN_DIR
    paths['_RATE_DIR'] = _RATE_DIR = os.path.join(_DATA_DIR,
                                                  'depreciation_rates')
    paths['_REF_DIR'] = os.path.join(_DATA_DIR, 'reference_data')
    paths['_RAW_DIR'] = _RAW_DIR = os.path.join(_DATA_DIR, 'raw_data')
    paths['_DEPR_DIR'] = _DEPR_DIR = os.path.join(_DATA_DIR,
                                                  'depreciation_rates')
    paths['_BEA_DIR'] = _BEA_DIR = os.path.join(_RAW_DIR, 'BEA')
    paths['_FIN_ACCT_DIR'] = _FIN_ACCT_DIR =\
    os.path.join(_RAW_DIR, 'national_accounts')
    # paths['_OUT_DIR'] = os.environ.get('ccc_OUT_DIR', 'ccc_output_dir')
    # if not os.path.exists(paths['_OUT_DIR']):
    #     os.mkdir(paths['_OUT_DIR'])
    paths['_BEA_ASSET_PATH'] = _BEA_ASSET_PATH =\
        os.path.join(_BEA_DIR, "detailnonres_stk1.xlsx")
    paths['_SOI_BEA_CROSS'] = _SOI_BEA_CROSS =\
        os.path.join(_BEA_DIR, 'soi_bea_industry_codes.csv')
    paths['_BEA_INV'] = _BEA_INV = os.path.join(_BEA_DIR, 'NIPA_5.8.5B.xls')
    paths['_BEA_RES'] = _BEA_RES =\
        os.path.join(_BEA_DIR, 'BEA_StdFixedAsset_Table5.1.xls')
    paths['_LAND_PATH'] = _LAND_PATH = os.path.join(_FIN_ACCT_DIR, '')
    paths['_B101_PATH'] = _B101_PATH = os.path.join(_FIN_ACCT_DIR, 'b101.csv')
    paths['_ECON_DEPR_IN_PATH'] = _ECON_DEPR_IN_PATH =\
        os.path.join(_DEPR_DIR, 'Economic Depreciation Rates.csv')
    paths['_TAX_DEPR'] = _TAX_DEPR =\
        os.path.join(_DEPR_DIR, 'tax_depreciation_rates.csv')
    paths['_SOI_DIR'] = _SOI_DIR = os.path.join(_RAW_DIR, 'soi')
    paths['_CORP_DIR'] = _CORP_DIR = os.path.join(_SOI_DIR, 'soi_corporate')
    paths['_TOT_CORP_IN_PATH'] = F_TOT_CORP_IN_PATH =\
        os.path.join(_CORP_DIR, '2013sb1.csv')
    paths['_S_CORP_IN_PATH'] = _S_CORP_IN_PATH =\
        os.path.join(_CORP_DIR, '2013sb3.csv')
    paths['_PRT_DIR'] = _PRT_DIR = os.path.join(_SOI_DIR, 'soi_partner')
    paths['_DETAIL_PART_CROSS_PATH'] = _DETAIL_PART_CROSS_PATH =\
        os.path.join(_PRT_DIR, 'partner_crosswalk_detailed_industries.csv')
    paths['_INC_FILE'] = _INC_FILE = os.path.join(_PRT_DIR, '13pa01.xls')
    paths['_AST_FILE'] = _AST_FILE = os.path.join(_PRT_DIR, '13pa03.xls')
    paths['_TYP_IN_CROSS_PATH'] = _TYP_IN_CROSS_PATH =\
        os.path.join(_PRT_DIR, '13pa05_Crosswalk.csv')
    paths['_TYP_FILE'] = _TYP_FILE = os.path.join(_PRT_DIR, '13pa05.xls')
    paths['_PROP_DIR'] = _PROP_DIR = os.path.join(_SOI_DIR,
                                                  'soi_proprietorship')
    paths['_PRT_DIR'] = _PRT_DIR = os.path.join(_SOI_DIR, 'soi_partner')
    paths['_NFARM_PATH'] = _NFARM_PATH = os.path.join(_PROP_DIR,
                                                      '13sp01br.xls')
    paths['_NFARM_INV'] = _NFARM_INV = os.path.join(_PROP_DIR,
                                                    '13sp02is.xls')
    paths['_FARM_IN_PATH'] = _FARM_IN_PATH = os.path.join(_PROP_DIR,
                                                          'farm_data.csv')
    paths['_DETAIL_SOLE_PROP_CROSS_PATH'] =\
        _DETAIL_SOLE_PROP_CROSS_PATH =\
        os.path.join(_PROP_DIR, 'detail_sole_prop_crosswalk.csv')
    paths['_SOI_CODES'] =\
        _SOI_CODES = os.path.join(_SOI_DIR, 'SOI_codes.csv')

    return paths


def str_modified(i):
    """
    Function to deal with conversion of a decimal number to a string.

    Args:
        i: scalar, number that will convert to string

    Returns:
        str_i: string, number converted to a string
    """
    if i == 27.5:
        str_i = '27_5'
    else:
        str_i = str(int(i))
    return str_i


def diff_two_tables(df1, df2):
    """
    Create the difference betweeen two dataframes.

    Args:
        df1: DataFrame, first DataFrame in difference
        df2: DataFrame, second DataFrame in difference

    Returns:
        diff_df: DataFrame, DataFrame with differences between to DataFrames
    """
    assert tuple(df1.columns) == tuple(df2.columns)
    diffs = OrderedDict()
    for c in df1.columns:
        example = getattr(df1, c).iloc[0]
        can_diff = isinstance(example, numbers.Number)
        if can_diff:
            diffs[c] = getattr(df1, c) - getattr(df2, c)
        else:
            diffs[c] = getattr(df1, c)
    diff_df = pd.DataFrame(diffs)
    return diff_df


def filter_user_params_for_econ(**user_params):
    """
    Filter out parameters that are economic (not tax) parameters.

    Args:
        user_params: dictionary, user defined parameters

    Returns:
        econ_params: dictionary, economic parameters
    """
    econ_params = {k: v for k, v in user_params.items() if
                   k.startswith('ccc_econ_')}

    return econ_params


def wavg(group, avg_name, weight_name):
    """
    Computes a weighted average.

    Args:
        group: grouby object, groups of variable
        avg_name: string, name of variable to compute wgt avg with
        weight_name: string, name of weighting variables

    Returns:
        d: groupby object, weighted avg by group
    """
    d = group[avg_name]
    w = group[weight_name]
    try:
        return (d * w).sum() / w.sum()
    except ZeroDivisionError:
        return d.mean()


def read_egg_csv(fname, index_col=None):
    """
    Read from egg the file named fname that contains CSV data and
    return pandas DataFrame containing the data.
    """
    try:
        path_in_egg = os.path.join('taxcalc', fname)
        vdf = pd.read_csv(
            pkg_resources.resource_stream(
                pkg_resources.Requirement.parse('taxcalc'),
                path_in_egg),
            index_col=index_col
        )
    except Exception:
        raise ValueError('could not read {} data from egg'.format(fname))
    # cannot call read_egg_ function in unit tests
    return vdf  # pragma: no cover


def read_egg_json(fname):
    """
    Read from egg the file named fname that contains JSON data and
    return dictionary containing the data.
    """
    try:
        path_in_egg = os.path.join('taxcalc', fname)
        pdict = json.loads(
            pkg_resources.resource_stream(
                pkg_resources.Requirement.parse('taxcalc'),
                path_in_egg).read().decode('utf-8'),
            object_pairs_hook=collections.OrderedDict
        )
    except Exception:
        raise ValueError('could not read {} data from egg'.format(fname))
    # cannot call read_egg_ function in unit tests
    return pdict  # pragma: no cover


def json_to_dict(json_text):
    """
    Convert specified JSON text into an ordered Python dictionary.
    Parameters
    ----------
    json_text: string
        JSON text.
    Raises
    ------
    ValueError:
        if json_text contains a JSON syntax error.
    Returns
    -------
    dictionary: collections.OrderedDict
        JSON data expressed as an ordered Python dictionary.
    """
    try:
        ordered_dict = json.loads(json_text,
                                  object_pairs_hook=collections.OrderedDict)
    except ValueError as valerr:
        text_lines = json_text.split('\n')
        msg = 'Text below contains invalid JSON:\n'
        msg += str(valerr) + '\n'
        msg += 'Above location of the first error may be approximate.\n'
        msg += 'The invalid JSON text is between the lines:\n'
        bline = ('XXXX----.----1----.----2----.----3----.----4'
                 '----.----5----.----6----.----7')
        msg += bline + '\n'
        linenum = 0
        for line in text_lines:
            linenum += 1
            msg += '{:04d}{}'.format(linenum, line) + '\n'
        msg += bline + '\n'
        raise ValueError(msg)
    return ordered_dict
