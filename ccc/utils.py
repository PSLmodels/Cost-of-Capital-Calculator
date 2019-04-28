import pkg_resources
from collections import OrderedDict
import warnings
import numbers
import os
import json
import pandas as pd

# Default year for model runs
DEFAULT_START_YEAR = 2019

# Year of asset data
ASSET_DATA_CSV_YEAR = 2013

# Start year for tax data (e.g. year of PUF)
RECORDS_START_YEAR = 2011

# Latest year TaxData extrapolates to
TC_LAST_YEAR = 2029


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
        buf = pkg_resources.resource_stream(
            pkg_resources.Requirement.parse("ccc"), path_in_egg)
        _bytes = buf.read()
        contents = str(_bytes)
    else:
        with open(template_path, 'r') as f:
            contents = f.read()
    return contents


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
        try:
            example = getattr(df1, c).iloc[0]
            can_diff = isinstance(example, numbers.Number)
            if can_diff:
                diffs[c] = getattr(df1, c) - getattr(df2, c)
            else:
                diffs[c] = getattr(df1, c)
        except AttributeError:
            pass
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
    warnings.filterwarnings('error')
    d = group[avg_name]
    w = group[weight_name]
    try:
        return (d * w).sum() / w.sum()
    except Warning:
        return d.mean()


def read_egg_csv(fname, index_col=None):
    """
    Read from egg the file named fname that contains CSV data and
    return pandas DataFrame containing the data.

    Args:
        fname: string, name of csv file
        index_col: string, name of column containing index

    Returns:
        vdf: pandas DataFrame, data from csv file
    """
    try:
        path_in_egg = os.path.join('ccc', fname)
        vdf = pd.read_csv(
            pkg_resources.resource_stream(
                pkg_resources.Requirement.parse('ccc'),
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

    Args:
        fname: string, name of JSON file

    Returns:
        pdict: dictionary, data from JSON file
    """
    try:
        path_in_egg = os.path.join('ccc', fname)
        pdict = json.loads(
            pkg_resources.resource_stream(
                pkg_resources.Requirement.parse('ccc'),
                path_in_egg).read().decode('utf-8'),
            object_pairs_hook=OrderedDict
        )
    except Exception:
        raise ValueError('could not read {} data from egg'.format(fname))
    # cannot call read_egg_ function in unit tests
    return pdict  # pragma: no cover


def json_to_dict(json_text):
    """
    Convert specified JSON text into an ordered Python dictionary.

    Args:
        json_text: string, JSON text

    Raises:
        ValueError: if json_text contains a JSON syntax error

    Returns:
        ordered_dict: collections.OrderedDict, JSON data expressed as
            an ordered Python dictionary.
    """
    try:
        ordered_dict = json.loads(json_text,
                                  object_pairs_hook=OrderedDict)
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
