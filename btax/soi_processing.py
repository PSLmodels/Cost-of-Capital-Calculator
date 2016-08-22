"""
SOI Auxiliary Script (soi_processing.py):
-------------------------------------------------------------------------------
Module that handles reading in the soi data (corporate, partners, and sole proprietorships). Makes calls to a different
script for each one of these entities. Also provides auxiliary scripts to format the partner and proprietorship dataframes and to
interpolate missing data.
Last updated: 7/26/2016.

"""
# Import packages
import os.path
import sys
import numpy as np
import pandas as pd
# Import custom modules
import pull_soi_corp as corp
import pull_soi_partner as prt
import pull_soi_proprietorship as prop
# Factor used to adjust dollar values
_FILE_FCTR = 10**3

def pull_soi_data():
    """Creates a dictionary that is updated with the soi entity data after each method.

        :returns: DataFrames organized by entity type (corp, partner, sole prop)
        :rtype: dictionary
    """
    entity_dfs = {}
    entity_dfs.update(corp.load_corp_data())

    entity_dfs.update(prt.load_partner_data(entity_dfs))

    entity_dfs.update(prop.load_proprietorship_data(entity_dfs))



    # make one big data frame - by industry and entity type
    c_corp = entity_dfs['c_corp'][['minor_code_alt','Land','Fixed Assets','Inventories']]
    c_corp['entity_type'] = 'c_corp'
    s_corp = entity_dfs['s_corp'][['minor_code_alt','Land','Fixed Assets','Inventories']]
    s_corp['entity_type'] = 's_corp'
    partner = entity_dfs['part_data'][['minor_code_alt','Land','Fixed Assets','Inventories']]
    partner['entity_type'] = 'partnership'
    sole_prop = entity_dfs['sole_prop_data'][['minor_code_alt','Land','Fixed Assets','Inventories']]
    sole_prop['entity_type'] = 'sole_prop'

    soi_data = c_corp.append([s_corp,partner,sole_prop],ignore_index=True).copy().reset_index()



    return soi_data
