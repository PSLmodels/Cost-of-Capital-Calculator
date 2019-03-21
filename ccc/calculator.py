"""
Cost-of-Capital-Calculator Calculator class.
"""
# CODING-STYLE CHECKS:
# pycodestyle calculator.py
# pylint --disable=locally-disabled calculator.py
#
# pylint: disable=invalid-name,no-value-for-parameter,too-many-lines

import os
import re
import copy
import urllib
import numpy as np
import pandas as pd
from ccc.calcfunctions import (update_depr_methods, npv_tax_depr,
                               eq_coc, eq_coc_inventory, eq_ucc,
                               eq_metr, eq_mettr, eq_tax_wedge, eq_eatr)
from ccc.parameters import Specifications
from ccc.assets import Assets
from ccc.utils import json_to_dict
# import pdb


class Calculator():
    """
    Constructor for the Calculator class.

    Parameters
    ----------
    p: Specifications class object
        this argument must be specified and object is copied for internal use

    assets: Assets class object
        this argument must be specified and object is copied for internal use

    verbose: boolean
        specifies whether or not to write to stdout data-loaded and
        data-extrapolated progress reports; default value is true.

    behavior: Behavior class object
        specifies behavioral responses used by Calculator; default is None,
        which implies no behavioral responses to p reform;
        when argument is an object it is copied for internal use

    Raises
    ------
    ValueError:
        if parameters are not the appropriate type.

    Returns
    -------
    class instance: Calculator

    Notes
    -----
    The most efficient way to specify current-law and reform Calculator
    objects is as follows:
         pol = Specifications()
         rec = Assets()
         calc1 = Calculator(p=pol, assets=rec)  # current-law
         pol.implement_reform(...)
         calc2 = Calculator(p=pol, assets=rec)  # reform
    All calculations are done on the internal copies of the Specifications and
    Assets objects passed to each of the two Calculator constructors.
    """
    # pylint: disable=too-many-public-methods

    def __init__(self, p=None, assets=None, verbose=True):
        # pylint: disable=too-many-arguments,too-many-branches
        if isinstance(p, Specifications):
            self.__p = copy.deepcopy(p)
        else:
            raise ValueError('must specify p as a Specifications object')
        if isinstance(assets, Assets):
            self.__assets = copy.deepcopy(assets)
        else:
            raise ValueError('must specify assets as a Assets object')
        self.__stored_assets = None

    def calc_all(self, zero_out_calc_vars=False):
        """
        Call all tax-calculation functions for the current_year.
        """
        # conducts static analysis of Calculator object for current_year
        df = update_depr_methods(assets.df, p)
        df['z']= npv_tax_depr(df, p.r['c']['mix'], p.inflation_rate)
        df['rho'] = eq_coc(df['delta'], df['z'], p.property_tax, p.u['c'], p.inv_tax_credit,
                     p.Y_v, p.inflation_rate, p.r['c']['e'])
        if not p.inventory_expensing:
            idx = df['asset_name'] == 'Inventories'
            df.loc[idx, 'rho'] = eq_coc_inventory(df.loc[idx, 'delta'], p.u['c'], p.phi, p.Y_v, p.inflation_rate, p.r['c']['mix'])
        df['ucc'] = eq_ucc(df['rho'], df['delta'])
        df['metr'] = eq_metr(df['rho'], p.r_prime['c']['mix'], p.inflation_rate)
        df['mettr'] = eq_mettr(df['rho'], p.s['c']['mix'])
        df['tax_wedge'] = eq_tax_wedge(df['rho'], p.s['c']['mix'])
        df['eatr'] = eq_eatr(df['rho'], df['metr'], p.profit_rate, p.u['c'])

    def store_assets(self):
        """
        Make internal copy of embedded Assets object that can then be
        restored after interim calculations that make temporary changes
        to the embedded Assets object.
        """
        assert self.__stored_assets is None
        self.__stored_assets = copy.deepcopy(self.__assets)

    def restore_assets(self):
        """
        Set the embedded Assets object to the stored Assets object
        that was saved in the last call to the store_assets() method.
        """
        assert isinstance(self.__stored_assets, Assets)
        self.__assets = copy.deepcopy(self.__stored_assets)
        del self.__stored_assets
        self.__stored_assets = None

    def p_param(self, param_name, param_value=None):
        """
        If param_value is None, return named parameter in
         embedded Specifications object.
        If param_value is not None, set named parameter in
         embedded Specifications object to specified param_value and
         return None (which can be ignored).
        """
        if param_value is None:
            return getattr(self.__p, param_name)
        setattr(self.__p, param_name, param_value)
        return None

    @property
    def reform_warnings(self):
        """
        Calculator class embedded Specifications object's reform_warnings.
        """
        return self.__p.parameter_warnings

    @property
    def current_year(self):
        """
        Calculator class current calendar year property.
        """
        return self.__p.current_year

    @property
    def data_year(self):
        """
        Calculator class initial (i.e., first) assets data year property.
        """
        return self.__assets.data_year

# Can put functions for tabular, text, graphical output here
