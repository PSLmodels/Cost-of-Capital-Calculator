import pytest
import pandas as pd
import numpy as np
import os
import ccc.utils as utils


def test_to_str():
    """
    Test of the to_str() function
    """
    number = "3"
    test_str = utils.to_str(number)
    assert isinstance(test_str, str)


def test_to_str_decode():
    """
    Test of the to_str() function
    """
    number = "3".encode()
    test_str = utils.to_str(number)
    assert isinstance(test_str, str)


test_data = [(27.5, "27_5"), (30, "30")]


@pytest.mark.parametrize(
    "number,expected", test_data, ids=["Decimal", "Integer"]
)
def test_str_modified(number, expected):
    """
    Test of the str_modified() function
    """
    number = "3"
    test_str = utils.str_modified(number)
    assert number == test_str


def test_diff_two_tables():
    """
    Test of the diff_two_tables() function
    """
    dict1 = {"var1": [1, 2, 3, 4, 5], "var2": [2, 4, 6, 8, 10]}
    dict2 = {"var1": [1, 2, 3, 4, 5], "var2": [2, 4, 6, 8, 10]}
    df1 = pd.DataFrame.from_dict(dict1)
    df2 = pd.DataFrame.from_dict(dict2)
    expected_dict = {"var1": [0, 0, 0, 0, 0], "var2": [0, 0, 0, 0, 0]}
    expected_df = pd.DataFrame.from_dict(expected_dict)
    test_df = utils.diff_two_tables(df1, df2)
    pd.testing.assert_frame_equal(test_df, expected_df)


def test_wavg():
    """
    Test of utils.wavg() function
    """
    dict1 = {
        "id": ["a", "a", "a"],
        "var1": [1, 2, 3],
        "var2": [2, 4, 6],
        "wgt_var": [0.25, 0.5, 0.25],
    }
    df1 = pd.DataFrame.from_dict(dict1)
    expected_val = 2.0
    test_val = utils.wavg(df1, "var1", "wgt_var")

    assert np.allclose(test_val, expected_val)


def test_read_egg_csv():
    """
    Test of utils.read_egg_csv() function
    """
    test_df = utils.read_egg_csv("ccc_asset_data.csv")

    assert isinstance(test_df, pd.DataFrame)


def test_read_egg_csv_exception():
    """
    Test of utils.read_egg_csv() function
    """
    with pytest.raises(Exception):
        assert utils.read_egg_csv("ccc_asset_data2.csv")


def test_read_egg_json():
    """
    Test of utils.read_egg_csv() function
    """
    test_dict = utils.read_egg_json("records_variables.json")

    assert isinstance(test_dict, dict)


def test_read_egg_json_exception():
    """
    Test of utils.read_egg_csv() function
    """
    with pytest.raises(Exception):
        assert utils.read_egg_json("records_variables2.json")


def test_json_to_dict():
    """
    Test of utils.json_to_dict() function
    """
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

    assert test_dict["read"]["asset_name"]["type"] == "string"


def test_json_to_dict_exception():
    """
    Test of utils.json_to_dict() function
    """
    json_string = """{
      "CIT_rate"
      }
     }"""
    with pytest.raises(Exception):
        assert utils.json_to_dict(json_string)


dict1 = {"var1": [1, 2, 3, 4, 5], "var2": [2, 4, 6, 8, 10]}
df1 = pd.DataFrame.from_dict(dict1)
test_data = [(df1, "tex", 0), (df1, "json", 2), (df1, "html", 3)]


@pytest.mark.parametrize(
    "df,output_type,precision", test_data, ids=["tex", "json", "html"]
)
def test_save_return_table(df, output_type, precision):
    test_str = utils.save_return_table(df, output_type, None, precision)
    assert isinstance(test_str, str)


def test_save_return_table_df():
    """
    Test that can return dataframe from utils.test_save_return_table
    """
    dict1 = {"var1": [1, 2, 3, 4, 5], "var2": [2, 4, 6, 8, 10]}
    df1 = pd.DataFrame.from_dict(dict1)
    test_df = utils.save_return_table(df1)
    assert isinstance(test_df, pd.DataFrame)


path1 = "output.tex"
path2 = "output.csv"
path3 = "output.json"
path4 = "output.xlsx"
# # writetoafile(file.strpath)  # or use str(file)
# assert file.read() == 'Hello\n'
test_data = [
    (df1, "tex", path1),
    (df1, "csv", path2),
    (df1, "json", path3),
    (df1, "excel", path4),
]


@pytest.mark.parametrize(
    "df,output_type,path", test_data, ids=["tex", "csv", "json", "excel"]
)
def test_save_return_table_write(df, output_type, path):
    """
    Test of the utils.save_return_table function for case wehn write to
    disk
    """
    utils.save_return_table(df, output_type, path=path)
    filehandle = open(path)
    try:
        assert filehandle.read() is not None
    except UnicodeDecodeError:
        from openpyxl import load_workbook

        wb = load_workbook(filename=path)
        assert wb is not None
    filehandle.close()


def test_save_return_table_exception():
    """
    Test that can return dataframe from utils.test_save_return_table
    """
    dict1 = {"var1": [1, 2, 3, 4, 5], "var2": [2, 4, 6, 8, 10]}
    df1 = pd.DataFrame.from_dict(dict1)
    with pytest.raises(Exception):
        assert utils.save_return_table(
            df1, output_type="xls", path="filename.tex"
        )
