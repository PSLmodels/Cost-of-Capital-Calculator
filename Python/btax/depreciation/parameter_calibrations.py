"""
Parameter Calibrations (parameter_calibrations.py):
-------------------------------------------------------------------------------
Last updated: 6/26/2015.

This module creates functions that carry out various parameter calibrations.
This is the most important firm calibrations module in that it brings all
the various firm calibrations together by calling all the various helper
modules.
"""
# Packages:
import os.path
import sys
import numpy as np
import pandas as pd
import cPickle as pickle
# Relevant directories:
_CUR_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(_CUR_DIR,'data')
_PKL_DIR = os.path.join(_DATA_DIR,'pickles')
sys.path.append(_PKL_DIR)
# Importing custom modules:
from btax.depreciation.calc_rates import calc_tax_depr_rates, calc_depr_rates

def calibrate_depr_rates(get_all=False,get_econ=False, get_tax=False):
    """ This calibrates a tree with all the depreciation rate parameters.
    :param get_all: Whether to get all the depreciation parameters or not.
    :param get_econ: Whether to get all the economic depreciation rates.
    :param get_tax: Whether to get all of the tax data.
    """
    # Initialize NAICS tree with all the soi tax data:
    #soi_tree = pull_soi_data(get_all=True, from_out=soi_from_out,output_data=(not soi_from_out))
    #asset_tree = calc_soi_assets(soi_tree=soi_tree)
    #Initialize NAICS tree with all assets--fixed assets, inventories, and land--by sector:
    # Use the asset_tree to initialize all the depreciation rates:
    fa_file = open(os.path.join(_PKL_DIR,'faTree.pkl'), 'rb')
    fixed_asset_tree = pickle.load(fa_file)
    fa_file.close()
    inv_file = open(os.path.join(_PKL_DIR,'invTree.pkl'), 'rb')
    inv_tree = pickle.load(inv_file)
    inv_file.close()
    land_file = open(os.path.join(_PKL_DIR,'landTree.pkl'), 'rb')
    land_tree = pickle.load(land_file)
    land_file.close()

    econ_depr = calc_depr_rates(fixed_asset_tree, inv_tree, land_tree)
    tax_depr = calc_tax_depr_rates(fixed_asset_tree, inv_tree, land_tree)
    tax_depr.columns =  ['NAICS', 'Tax_All', 'Tax_Corp', 'Tax_Non_Corp']
    econ_depr.columns = ['NAICS', 'Econ_All', 'Econ_Corp', 'Econ_Non_Corp'] 
    depr_rates = econ_depr.merge(tax_depr) 

    return depr_rates
'''
def calibrate_incomes(output_data=True):
    """ This calibrates a tree of all the income data parameters.
    
    :param out: Whether to output the dataframes in the final tree to the
           output file.
    """
    # The income directory:
    inc_dir = os.path.abspath(_PARAM_DIR + "//national_income")
    # Importing the module for gathering and processing the income data:
    sys.path.append(inc_dir)
    import national_income as inc
    # Get all the income data in an income tree:
    inc_tree = inc.get_incs()
    # Output the data to the income folder inside the output folder:
    if output_data:
        inc_out_dir = os.path.abspath(_OUT_DIR + "//income")
        # Make income folder if there isn't one:
        if not os.path.isdir(inc_out_dir):
            os.mkdir(inc_out_dir)
        # Print the data in the tree:
        naics.print_tree_dfs(inc_tree, inc_out_dir)
    return inc_tree
'''

'''
def calibrate_debt(debt_tree=naics.generate_tree(), soi_tree=None,
                   from_out=False, soi_from_out=False):
    """ This function is incomplete. This is supposed to do the debt
    calibrations.
    
    :param debt_tree: The NAICS tree to append the calibrated debt
           parameters to. Default is a newly generated tree.
    :param soi_tree: A tree with all of the relevant soi data.
    :
    """
    if soi_tree == None:
        soi_tree = pull_soi_data(get_corp=True, from_out=soi_from_out)
    #
    debt_dir = os.path.abspath(_PARAM_DIR + "//debt")
    debt_data_dir = os.path.abspath(debt_dir + "//data")
    sys.path.append(debt_dir)
    import debt_calibration as debt
    #
    lblty_file = os.path.abspath(debt_data_dir + "//liabilities.csv")
    print lblty_file
    lblty_df = pd.read_csv(lblty_file)
    eqty_file = os.path.abspath(debt_data_dir + "//equity.csv")
    eqty_df = pd.read_csv(eqty_file)
    debt_tree = naics.load_tree_dfs(input_file=lblty_file, dfs_name="liabilities", tree=debt_tree)
    debt_tree = naics.load_tree_dfs(input_file=eqty_file, dfs_name="equity", tree=debt_tree)
    #
    naics.pop_forward(tree=debt_tree, df_list=["liabilities"],
                      blue_tree=soi_tree, blueprint="tot_corps",
                      sub_print = ["Interest Paid"])
    #
    return debt_tree
    
'''
'''
def pull_soi_data(soi_tree, from_out=False,
                  get_all=False, get_corp=False,
                  get_tot=False, get_s=False,
                  get_c=False, get_prt=False,
                  get_prop=False, get_farm_prop=False,
                  output_data=False, out_path=None):
    # If get_all, set all booleans to true:
    if get_all:
        get_corp = True
        get_tot = True
        get_s = True
        get_c = True
        get_prt = True
        get_prop = True
        get_farm_prop = True
    # Import the soi_processing custom module:
    soi_dir = os.path.join(_DATA_DIR, "soi")
    sys.path.append(soi_dir)
    import soi_processing as soi
    # Loading the soi corporate data into the NAICS tree:
    if get_corp or get_tot or get_s or get_c:
        soi_tree = soi.load_corporate(
                                soi_tree=soi_tree, from_out=from_out,
                                get_all=get_corp, get_tot=get_tot,
                                get_s=get_s, get_c=get_c,
                                output_data=output_data, out_path=out_path
                                )
    # Loading the soi partnership data into the NAICS tree:
    if get_prt:
        soi_tree = soi.load_partner(soi_tree=soi_tree, from_out=from_out,
                                    output_data=output_data, out_path=out_path)
    # Loading the soi proprietorship data into the NAICS tree:
    if get_prop or get_farm_prop:
        soi_tree = soi.load_proprietorship(
                            soi_tree=soi_tree, from_out=from_out,
                            get_nonfarm=get_prop, get_farm=get_farm_prop,
                            output_data=output_data, out_path=out_path
                            )
    return soi_tree


def calc_soi_assets(soi_tree, asset_tree):
    """ Calculating a breakdown of the various sector type's assets
    into fixed assets, inventories, and land. 
    
    :param asset_tree: The NAICS tree to put all of the data in.
    :param soi_tree: A NAICS tree containing all the pertinent soi data.
    """
    # Import the soi_processing custom module:
    soi_dir = os.path.join(_DATA_DIR, "soi")
    sys.path.append(soi_dir)
    import soi_processing as soi
    # Use soi processing helper function to do all the work:
    return soi.calc_assets(asset_tree=asset_tree, soi_tree=soi_tree)
'''
