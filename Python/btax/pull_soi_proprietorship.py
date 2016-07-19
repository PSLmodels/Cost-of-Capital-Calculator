import os.path
import sys
import numpy as np
import pandas as pd

import soi_processing as soi

# Directories:
_CUR_DIR = os.path.dirname(__file__)
_DATA_DIR = os.path.join(_CUR_DIR, 'data')
_RAW_DIR = os.path.join(_DATA_DIR, 'raw_data')
_SOI_DIR = os.path.join(_RAW_DIR, 'soi')
_PROP_DIR = os.path.join(_SOI_DIR, 'soi_proprietorship')
_PRT_DIR = os.path.join(_SOI_DIR, 'soi_partner')

_NFARM_PATH = os.path.join(_PROP_DIR, '12sp01br.csv')
_FARM_IN_PATH = os.path.join(_PROP_DIR, 'farm_data.csv')
_PRT_INC = os.path.join(_PRT_DIR, '12pa01.csv')
_PRT_ASST = os.path.join(_PRT_DIR, '12pa03.csv')
_NFARM_INV = os.path.join(_PROP_DIR, '12sp02is.csv')
_PRT_CROSS = os.path.join(_PRT_DIR, '12pa01_Crosswalk.csv')
_DDCT_IN_CROSS_PATH = os.path.join(_PROP_DIR, '12sp01br_Crosswalk.csv')
_SOI_CODES = os.path.join(_SOI_DIR, 'SOI_codes.csv')
_DDCT_FILE_FCTR = 10**3

def load_proprietorship_data(sector_dfs):
	# Opens the file that contains the non farm sole prop data
    nonfarm_df = pd.read_csv(_NFARM_PATH)
    # Opens the nonfarm data crosswalk
    crosswalk = pd.read_csv(_DDCT_IN_CROSS_PATH)
    # Opens the nonfarm inventory data
    nonfarm_inv = soi.format_dataframe(pd.read_csv(_NFARM_INV).T,crosswalk)
    # Opens the crosswalk for the partner data
    prt_crosswalk = pd.read_csv(_PRT_CROSS)
    # Opens and formatting the partner depreciation deduction data 
    prt_deduct = pd.read_csv(_PRT_INC).T
    prt_deduct = soi.format_dataframe(prt_deduct, prt_crosswalk)
    # Opens and formatting the partner asset data
    prt_asst = pd.read_csv(_PRT_ASST).T
    prt_asst = soi.format_dataframe(prt_asst, prt_crosswalk)
    # Inserts the codes into the nonfarm dataframe
    nonfarm_df.insert(1, 'Codes:', crosswalk['Codes:'])
    # Formats the column names for the nonfarm dataframe 
    nonfarm_df = format_columns(nonfarm_df)
    # Saves the industry names and codes so they can be reused later
    names = nonfarm_df['Industrial sector']
    codes = nonfarm_df['Codes:']
    nonfarm_df = nonfarm_df * _DDCT_FILE_FCTR
    # Puts back the original industry names and codes 
    nonfarm_df['Industrial sector'] = names
    nonfarm_df['Codes:'] = codes
    # Takes only the overall values and removes duplicate columns for all the partner and sole prop data
    nonfarm_df = nonfarm_df.T.groupby(sort=False,level=0).first().T
    prt_deduct = prt_deduct.T.groupby(sort=False,level=0).first().T
    prt_asst = prt_asst.T.groupby(sort=False,level=0).first().T
    nonfarm_inv = nonfarm_inv.T.groupby(sort=False,level=0).first().T
    # Trims off all the extra columns and only leaves pertinent depreciation info
    sp_inv = nonfarm_inv[['Codes:', 'Inventory, beginning of year']]
    sp_depr = nonfarm_df[['Codes:','Depreciation deduction']]
    prt_depr = prt_deduct[['Codes:', 'Depreciation']]
    # Combines duplicate codes to create aggregate industries
    prt_depr = prt_depr.groupby('Codes:',sort=False).sum()
    codes = prt_depr.index.tolist()
    prt_depr.insert(0,'Codes:', codes)
    prt_depr.index = np.arange(0,len(prt_depr))
    # Trims and combines the partner capital data
    prt_capital = prt_asst[['Codes:', 'Depreciable assets', 'Less:  Accumulated depreciation', 'Land']]
    prt_capital = prt_capital.groupby('Codes:',sort=False).sum()
    codes = prt_capital.index.tolist()
    prt_capital.insert(0,'Codes:', codes)
    prt_capital.index = np.arange(0,len(prt_depr))
    # Joins all four of the dataframes into one (the common column is the industry codes) and stores the data in numpy arrays
    capital_data = np.array(sp_inv.merge(sp_depr.merge(prt_capital.merge(prt_depr))))
    
    fixed_assets = []
    land_data =[]
    inv_data = []
    # Iterates over each array in the new data structure and pulls out the relevant info for FA, Inv, and Land
    for array in capital_data:
        if(array[6] != 0):
            # Multiplies the ratio of land to depreciation deduction for partners by the depreciation deduction taken by sole props
            land = np.array([array[0],(array[5]*array[2]/float(array[6]))])
            # Multiplies the ratio of depreciable assets to depreciation deduction by the sole prop depreciation deduction
            fixed_asset = np.array([array[0],(array[3]-array[4])*array[2]/float(array[6])])
            # Takes the inventory value for sole props
            inventory = np.array([array[0], array[1]])
            # Adds these values to the capital stock lists
            fixed_assets.append(fixed_asset)
            land_data.append(land)
            inv_data.append(inventory)
    cstock_list = []
    # Iterates over the filled capital stock lists and converts them to numpy industry arrays
    for i in xrange(0,len(fixed_assets)):    
        nfarm_cstock = np.array([int(fixed_assets[i][0]), float(fixed_assets[i][1]), float(inv_data[i][1]), float(land_data[i][1])])
        cstock_list.append(nfarm_cstock)
    # Stores the newly created sole proprietorship capital stock data in a dataframe then sums duplicate codes    
    nfarm_df = pd.DataFrame(cstock_list, index=np.arange(0,len(cstock_list)), columns=['Codes:', 'FA', 'Inv', 'Land'])
    nfarm_df = nfarm_df.groupby('Codes:',sort=False).sum()
    codes = nfarm_df.index.tolist()
    nfarm_df.insert(0,'Codes:', codes)
    nfarm_df.index = np.arange(0,len(nfarm_df))
    # Similar to the method for partners, the baseline codes are added and holes are filled based on the corporate proportions
    baseline_codes = pd.read_csv(_SOI_CODES)
    nfarm_df = baseline_codes.merge(nfarm_df, how = 'outer').fillna(0)
    nfarm_df = baseline_codes.merge(nfarm_df, how = 'inner')
    nfarm_df = soi.interpolate_data(sector_dfs, nfarm_df)

    # Calculates the FA and Land for Farm sole proprietorships. Should be placed in data for industry 11
    farm_df = pd.read_csv(_FARM_IN_PATH)
    asst_land = farm_df['R_p'][0] + farm_df['Q_p'][0]
    agr_capital = prt_capital[prt_capital.index == 1]
    assts_agr = float(agr_capital['Depreciable assets'][1] - agr_capital['Less:  Accumulated depreciation'][1])
    land_agr = float(agr_capital['Land'])
    prt_farm_land = land_agr / (land_agr + assts_agr) * asst_land
    sp_farm_land = farm_df['A_sp'][0] * prt_farm_land / farm_df['A_p'][0]
    sp_farm_assts = farm_df['R_sp'][0] + farm_df['Q_sp'][0] - sp_farm_land
    sp_farm_cstock = np.array([sp_farm_assts, 0, sp_farm_land])

    # Creates the dictionary of sector : dataframe that is returned and used to update sector_dfs
    sole_prop_cstock = {'sole_prop': nfarm_df}

    return sole_prop_cstock

def format_columns(nonfarm_df):
    columns = nonfarm_df.columns.tolist()
    for i in xrange(0,len(columns)):
        column = columns[i]
        if '.1' in column:
            column = column[:-2]
        if '\n' in column:
            column = column.replace('\n', ' ').replace('\r','')
        column = column.rstrip()
        columns[i] = column
    nonfarm_df.columns = columns
    return nonfarm_df
