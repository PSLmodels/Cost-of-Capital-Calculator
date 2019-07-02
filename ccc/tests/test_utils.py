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
