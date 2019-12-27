import pytest
import pandas as pd
from ccc.data import Assets
from ccc.utils import ASSET_DATA_CSV_YEAR, read_egg_csv, read_egg_json


def test_data_year():
    '''
    Test of Assets.data_year() method
    '''
    assets = Assets()

    assert assets.data_year == ASSET_DATA_CSV_YEAR


def test_array_length():
    '''
    Test of Assets.array_length() method
    '''
    assets = Assets()
    df = read_egg_csv('ccc_asset_data.csv')

    assert assets.array_length == df.shape[0]


def test_read_var_info():
    '''
    Test of Assets.read_var_info() method
    '''
    assets = Assets()
    expected_dict = read_egg_json('records_variables.json')
    test_dict = assets.read_var_info()
    for k, v in expected_dict.items():
        print('Item is ', k)
        assert v == test_dict[k]


def test_read_data():
    '''
    Test of Assets._read_data() method
    '''
    assets = Assets()
    df = read_egg_csv('ccc_asset_data.csv')

    pd.testing.assert_frame_equal(
        df, assets.df)
