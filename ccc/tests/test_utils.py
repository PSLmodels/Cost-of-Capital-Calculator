import pytest
import pandas as pd
import ccc.utils as utils


def test_to_str():
    '''
    Test of the to_str() function
    '''
    number = '3'
    test_str = utils.to_str(number)
    print('test_str = ', test_str)
    assert isinstance(test_str, str)
