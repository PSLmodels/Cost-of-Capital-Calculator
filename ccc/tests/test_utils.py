import pytest
import pandas as pd
import numpy as np
import ccc.utils as utils


def test_to_str():
    '''
    Test of the to_str() function
    '''
    number = '3'
    test_str = utils.to_str(number)
    assert isinstance(test_str, str)


test_data = [(27.5, '27_5'), (30, '30')]


@pytest.mark.parametrize('number,expected', test_data,
                         ids=['Decimal', 'Integer'])
def test_str_modified(number, expected):
    '''
    Test of the str_modified() function
    '''
    number = '3'
    test_str = utils.str_modified(number)
    assert (number == test_str)


def test_diff_two_tables():
    '''
    Test of the diff_two_tables() function
    '''
    dict1 = {'var1': [1, 2, 3, 4, 5], 'var2': [2, 4, 6, 8, 10]}
    dict2 = {'var1': [1, 2, 3, 4, 5], 'var2': [2, 4, 6, 8, 10]}
    df1 = pd.DataFrame.from_dict(dict1)
    df2 = pd.DataFrame.from_dict(dict2)
    expected_dict = {'var1': [0, 0, 0, 0, 0], 'var2': [0, 0, 0, 0, 0]}
    expected_df = pd.DataFrame.from_dict(expected_dict)
    test_df = utils.diff_two_tables(df1, df2)
    pd.testing.assert_frame_equal(test_df, expected_df)


def test_wavg():
    '''
    Test of utils.wavg() function
    '''
    dict1 = {'id': ['a', 'a', 'a'],
             'var1': [1, 2, 3],
             'var2': [2, 4, 6],
             'wgt_var': [0.25, 0.5, 0.25]}
    df1 = pd.DataFrame.from_dict(dict1)
    expected_val = 2.0
    test_val = utils.wavg(df1, 'var1', 'wgt_var')

    assert np.allclose(test_val, expected_val)


def test_read_egg_csv():
    '''
    Test of utils.read_egg_csv() function
    '''
    test_df = utils.read_egg_csv('ccc_asset_data.csv')

    assert isinstance(test_df, pd.DataFrame)


def test_read_egg_json():
    '''
    Test of utils.read_egg_csv() function
    '''
    test_dict = utils.read_egg_json('records_variables.json')

    assert isinstance(test_dict, dict)


def test_json_to_dict():
    '''
    Test of utils.json_to_dict() function
    '''
    json_string = """{
      "read": {
        "asset_name": {
          "type": "string",
          "desc": "Description of asset"
        },
        "assets": {
          "type": "float",
          "desc": "Dollar value of assets"
        }
      }
     }"""
    test_dict = utils.json_to_dict(json_string)

    assert test_dict['read']['asset_name']['type'] == 'string'


dict1 = {'var1': [1, 2, 3, 4, 5], 'var2': [2, 4, 6, 8, 10]}
df1 = pd.DataFrame.from_dict(dict1)
test_data = [(df1, 'tex', 0), (df1, 'json', 2), (df1, 'html', 3)]


@pytest.mark.parametrize('df,output_type,precision', test_data,
                         ids=['tex', 'json', 'html'])
def test_save_return_table(df, output_type, precision):

    test_str = utils.save_return_table(df, output_type, None, precision)
    assert isinstance(test_str, str)


def test_save_return_table_df():
    '''
    Test that can return dataframe from utils.test_save_return_table
    '''
    dict1 = {'var1': [1, 2, 3, 4, 5], 'var2': [2, 4, 6, 8, 10]}
    df1 = pd.DataFrame.from_dict(dict1)
    test_df = utils.save_return_table(df1)
    assert isinstance(test_df, pd.DataFrame)
