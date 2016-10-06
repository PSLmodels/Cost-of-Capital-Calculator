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
import btax.pull_soi_corp as corp
import btax.pull_soi_partner as prt
import btax.pull_soi_proprietorship as prop
from btax.util import get_paths
globals().update(get_paths())


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
    c_corp = entity_dfs['c_corp'][['minor_code_alt','Land','Fixed Assets','Inventories']].copy()
    c_corp.loc[:,'entity_type'] = 'c_corp'
    s_corp = entity_dfs['s_corp'][['minor_code_alt','Land','Fixed Assets','Inventories']].copy()
    s_corp.loc[:,'entity_type'] = 's_corp'
    partner = entity_dfs['part_data'][['minor_code_alt','Land','Fixed Assets','Inventories','part_type']].copy()
    partner.loc[:,'entity_type'] = 'partnership'
    sole_prop = entity_dfs['sole_prop_data'][['minor_code_alt','Land','Fixed Assets','Inventories']].copy()
    sole_prop.loc[:,'entity_type'] = 'sole_prop'

    soi_data = c_corp.append([s_corp,partner,sole_prop],ignore_index=True).copy().reset_index()
    # soi_data.loc[soi_data['part_type'] == None, 'part_type'] = 'Not a partnership'
    soi_data['part_type'] = soi_data['part_type'].fillna('Not a partnership')

    # merge to industry codes xwalk, which will be helpful when merging with
    # BEA data
    ## create ratios for minor industry assets using corporate data
    # read in crosswalk for bea and soi industry codes
    soi_bea_ind_codes = pd.read_csv(_SOI_BEA_CROSS, dtype={'bea_ind_code':str})
    soi_bea_ind_codes.drop('notes', axis=1, inplace=True)
    # drop one repeated minor ind code in crosswalk
    soi_bea_ind_codes.drop_duplicates(subset=['minor_code_alt'],inplace=True)

    soi_data['tax_treat'] = 'non-corporate'
    soi_data.ix[soi_data['entity_type']=='c_corp', 'tax_treat'] = 'corporate'
    soi_data.ix[(soi_data['entity_type']=='partnership') & (soi_data['part_type']=='Corporate general partners'), 'tax_treat'] = 'corporate'
    soi_data.ix[(soi_data['entity_type']=='partnership') & (soi_data['part_type']=='Corporate limited partners'), 'tax_treat'] = 'corporate'
    soi_data = pd.merge(soi_data, soi_bea_ind_codes, how='left', left_on=['minor_code_alt'],
      right_on=['minor_code_alt'], left_index=False, right_index=False, sort=False,
      copy=True)

    return soi_data
