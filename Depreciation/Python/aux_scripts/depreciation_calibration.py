"""
Depreciation Rate Calibration (depreciation_calibration.py):
-------------------------------------------------------------------------------
Last updated: 6/26/2015.

This module calibrates the firm economic and tax depreciation parameters.
"""
# Packages:
import os.path
import sys
import numpy as np
import pandas as pd
import cPickle as pickle
# Directories:
_CUR_DIR = os.path.dirname(__file__)
_MAIN_DIR = os.path.dirname(_CUR_DIR)
_DATA_DIR = os.path.join(_MAIN_DIR, 'data')
_PKL_DIR = os.path.join(_DATA_DIR, 'pickles')
# Importing custom modules:
import naics_processing as naics
import constants as cst
# Importing depreciation helper custom modules:
import calc_rates as calc_rates
import read_bea as read_bea
import read_inventories as read_inv
import read_land as read_land
# Dataframe names:
_CODE_DF_NM = cst.CODE_DF_NM
# Dataframe column names:
_CORP_TAX_SECTORS_NMS_DICT = cst.CORP_TAX_SECTORS_NMS_DICT
_CORP_NMS = _CORP_TAX_SECTORS_NMS_DICT.values()
_NON_CORP_TAX_SECTORS_NMS_DICT = cst.NON_CORP_TAX_SECTORS_NMS_DICT
_NCORP_NMS = _NON_CORP_TAX_SECTORS_NMS_DICT.values()


def init_depr_rates(asset_tree):
    #all the fixed asset/inventroy/land trees are stored in memory in .pkl files
    
    fa_file = open(os.path.join(_PKL_DIR,'faTree.pkl'), 'rb')
    fixed_asset_tree = pickle.load(fa_file)
    fa_file.close()
    inv_file = open(os.path.join(_PKL_DIR,'invTree.pkl'), 'rb')
    inv_tree = pickle.load(inv_file)
    inv_file.close()
    land_file = open(os.path.join(_PKL_DIR,'landTree.pkl'), 'rb')
    land_tree = pickle.load(land_file)
    land_file.close()

    #If you ever need to recalculate the fixed asset/inventory/land values, these functions need to be rerun to calculate them instead of just loading them from memory
    # Calculating the fixed asset data:
    #fixed_asset_tree = read_bea.read_bea(asset_tree)
    # Calculating the inventory data:
    #inv_tree = read_inv.read_inventories(asset_tree)
    # Calculating the land data:
    #land_tree = read_land.read_land(asset_tree)
    # Calculating the depreciation rates:
    
    econ_depr_tree = calc_rates.calc_depr_rates(fixed_asset_tree, inv_tree, land_tree)
    tax_depr_tree = calc_rates.calc_tax_depr_rates(fixed_asset_tree, inv_tree, land_tree)
    #naics.pop_rates(tax_depr_tree)
    
    return {"Econ": econ_depr_tree, "Tax": tax_depr_tree}
