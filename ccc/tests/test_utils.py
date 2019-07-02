import pytest
import pandas as pd
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
