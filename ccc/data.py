"""
Cost-of-Capital-Calculator asset data class.
"""
# CODING-STYLE CHECKS:
# pycodestyle records.py
# pylint --disable=locally-disabled records.py

import os
import numpy as np
import pandas as pd
from ccc.utils import read_egg_csv, read_egg_json, json_to_dict
from ccc.utils import ASSET_DATA_CSV_YEAR


class Assets():
    """
    Constructor for the asset-entity type Records class.

    Parameters
    ----------
    data: string or Pandas DataFrame
        string describes CSV file in which records data reside;
        DataFrame already contains records data;
        default value is the string 'asset_data.csv'

    start_year: integer
        specifies calendar year of the input data;
        default value is ASSET_DATA_CSV_YEAR.

    Raises
    ------
    ValueError:
        if data is not the appropriate type.
        if start_year is not an integer.
        if files cannot be found.

    Returns
    -------
    class instance: Records

    Notes
    -----
    Typical usage when using ccc_asset_data.csv input data is as follows::

        assets = Assets()

    which uses all the default parameters of the constructor.

    """
    # suppress pylint warnings about unrecognized Records variables:
    # pylint: disable=no-member
    # suppress pylint warnings about uppercase variable names:
    # pylint: disable=invalid-name
    # suppress pylint warnings about too many class instance attributes:
    # pylint: disable=too-many-instance-attributes

    ASSET_YEAR = ASSET_DATA_CSV_YEAR

    CUR_PATH = os.path.abspath(os.path.dirname(__file__))
    VAR_INFO_FILENAME = 'records_variables.json'

    def __init__(self,
                 data='ccc_asset_data.csv',
                 start_year=ASSET_DATA_CSV_YEAR):
        # pylint: disable=too-many-arguments,too-many-locals
        self.__data_year = start_year
        # read specified data
        self._read_data(data)
        # If have any checks on data, do there here...
        # specify that variable values do not include behavioral responses
        self.behavioral_responses_are_included = False

    @property
    def data_year(self):
        """
        Records class original data year property.
        """
        return self.__data_year

    @property
    def current_year(self):
        """
        Records class current calendar year property.
        """
        return self.__current_year

    @property
    def array_length(self):
        """
        Length of arrays in Records class's DataFrame.
        """
        return self.__dim

    @staticmethod
    def read_var_info():
        """
        Read Assets variables metadata from JSON file;
        returns dictionary and specifies static varname sets listed below.
        """
        var_info_path = os.path.join(Assets.CUR_PATH,
                                     Assets.VAR_INFO_FILENAME)
        if os.path.exists(var_info_path):
            with open(var_info_path) as vfile:
                json_text = vfile.read()
            vardict = json_to_dict(json_text)
        else:
            # cannot call read_egg_ function in unit tests
            vardict = read_egg_json(
                Assets.VAR_INFO_FILENAME)  # pragma: no cover
        Assets.INTEGER_READ_VARS = set(k for k, v in vardict['read'].items()
                                       if v['type'] == 'int')
        FLOAT_READ_VARS = set(k for k, v in vardict['read'].items()
                              if v['type'] == 'float')
        Assets.MUST_READ_VARS = set(k for k, v in vardict['read'].items()
                                    if v.get('required'))
        Assets.USABLE_READ_VARS = Assets.INTEGER_READ_VARS | FLOAT_READ_VARS
        Assets.INTEGER_VARS = Assets.INTEGER_READ_VARS
        return vardict

    # specify various sets of variable names
    INTEGER_READ_VARS = set()
    MUST_READ_VARS = set()
    USABLE_READ_VARS = set()
    INTEGER_VARS = set()

    def _read_data(self, data):
        """
        Read Records data from file or use specified DataFrame as data.
        """
        # pylint: disable=too-many-statements,too-many-branches
        if Assets.INTEGER_VARS == set():
            Assets.read_var_info()
        # read specified data
        if isinstance(data, pd.DataFrame):
            assetdf = data
        elif isinstance(data, str):
            if os.path.isfile(data):
                assetdf = pd.read_csv(data)
            else:
                # cannot call read_egg_ function in unit tests
                assetdf = read_egg_csv(data)  # pragma: no cover
        else:
            msg = 'data is neither a string nor a Pandas DataFrame'
            raise ValueError(msg)
        self.__dim = len(assetdf.index)
        self.__index = assetdf.index

        self.df = assetdf
        # # create class variables using assetdf column names
        # READ_VARS = set()
        # self.IGNORED_VARS = set()
        # for varname in list(assetdf.columns.values):
        #     if varname in Assets.USABLE_READ_VARS:
        #         READ_VARS.add(varname)
        #         if varname in Assets.INTEGER_READ_VARS:
        #             setattr(self, varname,
        #                     assetdf[varname].astype(np.int32).values)
        #         else:
        #             setattr(self, varname,
        #                     assetdf[varname].astype(np.float64).values)
        #     else:
        #         self.IGNORED_VARS.add(varname)
        # # check that MUST_READ_VARS are all present in assetdf
        # if not Assets.MUST_READ_VARS.issubset(READ_VARS):
        #     msg = 'Records data missing one or more MUST_READ_VARS'
        #     raise ValueError(msg)
        # # delete intermediate assetdf object
        # del assetdf
        # # create other class variables that are set to all zeros
        # UNREAD_VARS = Assets.USABLE_READ_VARS - READ_VARS
        # ZEROED_VARS = UNREAD_VARS
        # for varname in ZEROED_VARS:
        #     if varname in Assets.INTEGER_VARS:
        #         setattr(self, varname,
        #                 np.zeros(self.array_length, dtype=np.int32))
        #     else:
        #         setattr(self, varname,
        #                 np.zeros(self.array_length, dtype=np.float64))
        # # delete intermediate variables
        # del READ_VARS
        # del UNREAD_VARS
        # del ZEROED_VARS
