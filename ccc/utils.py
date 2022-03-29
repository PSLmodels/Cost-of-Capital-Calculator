import pkg_resources
from collections import OrderedDict
import warnings
import numbers
import os
import json
import pandas as pd

PACKAGE_NAME = 'ccc'
PYPI_PACKAGE_NAME = 'cost-of-capital-calculator'

# Default year for model runs
DEFAULT_START_YEAR = 2022

# Year of asset data
ASSET_DATA_CSV_YEAR = 2013

# Start year for tax data (e.g. year of PUF)
RECORDS_START_YEAR = 2011

# Latest year TaxData extrapolates to
TC_LAST_YEAR = 2031


def to_str(x):
    '''
    Function to decode string.

    Args:
        x (string): string to decode

    Returns:
        x (string): decoded string

    '''
    if hasattr(x, 'decode'):
        return x.decode()
    return x


def str_modified(i):
    '''
    Function to deal with conversion of a decimal number to a string.

    Args:
        i (scalar): number that will convert to string

    Returns:
        str_i (string): number converted to a string

    '''
    if i == 27.5:
        str_i = '27_5'
    else:
        str_i = str(int(i))
    return str_i


def diff_two_tables(df1, df2):
    '''
    Create the difference between two dataframes.

    Args:
        df1 (Pandas DataFrame): first DataFrame in difference
        df2 (Pandas DataFrame): second DataFrame in difference

    Returns:
        diff_df (Pandas DataFrame): DataFrame with differences between
            two DataFrames

    '''
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


def wavg(group, avg_name, weight_name):
    '''
    Computes a weighted average.

    Args:
        group (Pandas DataFrame): data for the particular grouping
        avg_name (string): name of variable to compute wgt avg with
        weight_name (string): name of weighting variables

    Returns:
        d (scalar): weighted avg for the group

    '''
    warnings.filterwarnings('error')
    d = group[avg_name]
    w = group[weight_name]
    try:
        return (d * w).sum() / w.sum()
    except Warning:
        return d.mean()


def read_egg_csv(fname, index_col=None):
    '''
    Read from egg the file named fname that contains CSV data and
    return pandas DataFrame containing the data.

    Args:
        fname (string): name of csv file
        index_col (string): name of column containing index

    Returns:
        vdf (Pandas DataFrame): data from csv file
    '''
    # try:
    path_in_egg = os.path.join(PACKAGE_NAME, fname)
    try:
        vdf = pd.read_csv(
            pkg_resources.resource_stream(
                pkg_resources.Requirement.parse(PYPI_PACKAGE_NAME),
                path_in_egg),
            index_col=index_col
        )
    except Exception:
        raise ValueError('could not read {} data from egg'.format(fname))
    # cannot call read_egg_ function in unit tests
    return vdf  # pragma: no cover


def read_egg_json(fname):
    '''
    Read from egg the file named fname that contains JSON data and
    return dictionary containing the data.

    Args:
        fname (string): name of JSON file

    Returns:
        pdict (dict): data from JSON file

    '''
    try:
        path_in_egg = os.path.join(PACKAGE_NAME, fname)
        pdict = json.loads(
            pkg_resources.resource_stream(
                pkg_resources.Requirement.parse(PYPI_PACKAGE_NAME),
                path_in_egg).read().decode('utf-8'),
            object_pairs_hook=OrderedDict
        )
    except Exception:
        raise ValueError('could not read {} data from egg'.format(fname))
    # cannot call read_egg_ function in unit tests
    return pdict  # pragma: no cover


def json_to_dict(json_text):
    '''
    Convert specified JSON text into an ordered Python dictionary.

    Args:
        json_text (string): JSON text

    Raises:
        ValueError: if json_text contains a JSON syntax error

    Returns:
        ordered_dict (collections.OrderedDict): JSON data expressed as
            an ordered Python dictionary.

    '''
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


def save_return_table(table_df, output_type=None, path=None,
                      precision=0):
    '''
    Function to save or return a table of data.

    Args:
        table_df (Pandas DataFrame): table
        output_type (string): specifies the type of file to save
            table to: 'csv', 'tex', 'excel', 'json'
        path (string): specifies path to save file with table to
        precision (integer): number of significant digits to print.
            Defaults to 0.

    Returns:
        table_df (Pandas DataFrame): table

    '''
    if path is None:
        if output_type == 'tex':
            tab_str = table_df.to_latex(
                buf=path, index=False, na_rep='',
                float_format=lambda x: '%.' + str(precision) + '0f' % x)
            return tab_str
        elif output_type == 'json':
            tab_str = table_df.to_json(
                path_or_buf=path, double_precision=0)
            return tab_str
        elif output_type == 'html':
            with pd.option_context('display.precision', precision):
                tab_html = table_df.to_html(
                        index=False,
                        float_format=lambda x: '%10.0f' % x,
                        classes="table table-striped table-hover")
            return tab_html
        else:
            return table_df
    else:
        condition = (
            (path.split('.')[-1] == output_type) or
            (path.split('.')[-1] == 'xlsx' and output_type == 'excel') or
            (path.split('.')[-1] == 'xls' and output_type == 'excel'))
        if condition:
            if output_type == 'tex':
                table_df.to_latex(buf=path, index=False, na_rep='',
                                  float_format=lambda x: '%.' +
                                  str(precision) + '0f' % x)
            elif output_type == 'csv':
                table_df.to_csv(path_or_buf=path, index=False,
                                na_rep='', float_format='%.' +
                                str(precision) + '0f')
            elif output_type == 'json':
                table_df.to_json(path_or_buf=path,
                                 double_precision=precision)
            elif output_type == 'excel':
                table_df.to_excel(excel_writer=path, index=False,
                                  na_rep='', float_format='%.' +
                                  str(precision) + '0f')
        else:
            raise ValueError('Please enter a valid output format')
