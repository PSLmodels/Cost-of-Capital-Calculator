"""
SOI Corp Data (pull_soi_corp.py):
-------------------------------------------------------------------------------
Module that handles reading in the soi corporate data. Contains a script that loads in the capital stock
information for total corporations and s corporations. Based on the ratio of assets for total corporations,
data for s corporations is imputed. Finally, using the difference between the two, the c corporation
data can be allocated to all the industries.
Last updated: 7/26/2016.

"""
# Packages:
import os.path
import numpy as np
import pandas as pd
# Directory names:
from btax.util import get_paths
globals().update(get_paths())

_DFLT_S_CORP_COLS_DICT = DFLT_S_CORP_COLS_DICT = dict([
                    ('depreciable_assets','DPRCBL_ASSTS'),
                    ('accumulated_depreciation', 'ACCUM_DPR'),
                    ('land', 'LAND'),
                    ('inventories', 'INVNTRY'),
                    ('interest_paid', 'INTRST_PD'),
                    ('Capital_stock', 'CAP_STCK'),
                    ('additional_paid-in_capital', 'PD_CAP_SRPLS'),
                    ('earnings_(rtnd_appr.)', ''),
                    ('earnings_(rtnd_unappr.)', 'COMP_RTND_ERNGS_UNAPPR'),
                    ('cost_of_treasury_stock', 'CST_TRSRY_STCK'),
                    ('depreciation', 'NET_DPR')
                    ])
_CORP_FILE_FCTR = 10**3
_NAICS_COL_NM = 'INDY_CD'
_CODE_RANGE = ['32', '33', '45', '49']
_PARENTS = {'32':'31','33':'31','45':'44','49':'48'}

def load_corp_data():
    """Reads in the total corp and s corp data and calculates the c corp data.

        :returns: soi corporate capital stock data
        :rtype: dictionary
    """
    cols_dict=_DFLT_S_CORP_COLS_DICT
    # Dataframe column names
    data_cols = cols_dict.keys()
    columns = cols_dict.values()
    columns.remove('')
    # Opening the soi S-corporate data file:
    try:
        s_corp = pd.read_csv(_S_CORP_IN_PATH).fillna(0)
        s_corp = s_corp.drop(s_corp[s_corp['AC']> 1.].index)
        # drop total across all industries
        s_corp = s_corp.drop(s_corp[s_corp['INDY_CD']== 1.].index)
        # put in dollars (data in 1000s)
        # for var in columns:
        #     s_corp[var] = s_corp[var]*_CORP_FILE_FCTR
        s_corp[columns]=s_corp[columns]*_CORP_FILE_FCTR
    except IOError:
        print "IOError: S-Corp soi data file not found."
        raise
    # Opening the soi Total-corporate data file:
    try:
        tot_corp = pd.read_csv(_TOT_CORP_IN_PATH).fillna(0)
        tot_corp = tot_corp.drop(tot_corp[tot_corp['AC']> 1.].index)
        # drop total across all industries
        tot_corp = tot_corp.drop(tot_corp[tot_corp['INDY_CD']== 1.].index)
        tot_corp = tot_corp[['INDY_CD']+columns].copy()
        # put in dollars (data in 1000s)
        tot_corp[columns]=tot_corp[columns]*_CORP_FILE_FCTR
    except IOError:
        print "IOError: S-Corp soi data file not found."
        raise

    # read in crosswalk for bea and soi industry codes
    soi_bea_ind_codes = pd.read_csv(_SOI_BEA_CROSS, dtype={'bea_ind_code':str})
    soi_bea_ind_codes.drop('notes', axis=1, inplace=True)
    # drop one repeated minor ind code in crosswalk
    soi_bea_ind_codes.drop_duplicates(subset=['minor_code_alt'],inplace=True)


    # merge codes to total corp data
    # inner join means that we keep only rows that match in both datasets
    # this should keep only unique soi minor industries
    # in total corp data - note that s corp data already unique by sector
    tot_corp = pd.merge(tot_corp, soi_bea_ind_codes, how='inner', left_on=['INDY_CD'],
                        right_on=['minor_code_alt'],left_index=False,
                        right_index=False, sort=False,suffixes=('_x', '_y'),
                        copy=True, indicator=False)

    # apportion s corp data across industries within sectors so has same level of
    # industry detail as total corp data
    s_corp = calc_proportions(tot_corp, s_corp, columns)

    # merge s corp and total corp to find c corp only
    c_corp = pd.merge(tot_corp, s_corp, how='inner', on=['INDY_CD'],
                        left_index=False, right_index=False, sort=False,suffixes=('_x', '_y'),
                        copy=True, indicator=False)

    #calculate s corp values by minor industry using ratios
    for var in columns:
        c_corp[var] = c_corp[var+'_x']-c_corp[var+'_y']

    # clean up data by dropping and renaming columns
    c_corp.drop(map(lambda (x,y): x+y, zip(columns, ['_x']*len(columns))), axis=1, inplace=True)
    c_corp.drop(map(lambda (x,y): x+y, zip(columns, ['_y']*len(columns))), axis=1, inplace=True)

    ## NOTE:
    # totals in s_corp match totals in SOI data
    # totals in tot_corp match totals in SOI data if you sum over industries -
    # but here and in raw SOI, summing over industries does not return value
    # for "all industries". It's within 1%, but difference can't be accounted for
    # (sum over industry > totals for all industries)

    s_corp.rename(columns={"LAND": "Land", "INVNTRY": "Inventories",
                           "DPRCBL_ASSTS": "Fixed Assets",
                           "NET_DPR":"Depreciation","INDY_CD":"minor_code_alt"},inplace=True)
    c_corp.rename(columns={"LAND": "Land", "INVNTRY": "Inventories",
                           "DPRCBL_ASSTS": "Fixed Assets",
                           "NET_DPR":"Depreciation"},inplace=True)
    tot_corp.rename(columns={"LAND": "Land", "INVNTRY": "Inventories",
                           "DPRCBL_ASSTS": "Fixed Assets",
                           "NET_DPR":"Depreciation","INDY_CD":"minor_code_alt"},inplace=True)

    # Creates a dictionary of a sector : dataframe
    corp_data = {'tot_corp': tot_corp, 'c_corp': c_corp, 's_corp': s_corp}

    return corp_data

def calc_proportions(tot_corp, s_corp, columns):
    """Uses the ratio of the minor industry to the major industry to fill in missing s corp data.

        :param tot_corp_data: capital stock for all the corporations
        :param s_corp_data: capital stock for the s corporations
        :param columns: column names for the new DataFrame
        :type tot_corp_data: DataFrame
        :type s_corp_data: DataFrame
        :type columns: list
        :returns: capital stock for the s corporations with all the industries filled in
        :rtype: DataFrame
    """
    # find ratio of variable in minor industry to variable in sector
    # in total corp data
    corp_ratios = tot_corp[['INDY_CD','sector_code']+columns].copy()
    for var in columns :
        corp_ratios[var+'_ratio'] = tot_corp.groupby(['sector_code'])[var].apply(lambda x: x/float(x.sum()))

    corp_ratios.drop(columns, axis=1, inplace=True)

    # new data w just ratios that will then merge to s corp data by sector code (many to one merge)
    # first just keep s corp columns want_
    # merge ratios to s corp data
    s_corp = pd.merge(corp_ratios, s_corp, how='inner', left_on=['sector_code'], right_on=['INDY_CD'],
      left_index=False, right_index=False, sort=False,
      suffixes=('_x', '_y'), copy=True, indicator=True)

    #calculate s corp values by minor industry using ratios
    for var in columns:
        s_corp[var+'_final'] = s_corp[var]*s_corp[var+'_ratio']

    # clean up data by dropping and renaming columns
    s_corp.drop(['INDY_CD_y','_merge','sector_code']+columns, axis=1, inplace=True)
    s_corp.drop(map(lambda (x,y): x+y, zip(columns, ['_ratio']*len(columns))), axis=1, inplace=True)
    s_corp.rename(columns={"INDY_CD_x": "INDY_CD"},inplace=True)
    s_corp.columns = s_corp.columns.str.replace('_final', '')

    return s_corp
