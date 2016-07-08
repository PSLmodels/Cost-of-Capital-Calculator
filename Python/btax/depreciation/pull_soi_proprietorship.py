'''
SOI Proprietorship Tax Data (pull_soi_proprietorship.py):
-------------------------------------------------------------------------------
Last updated: 6/29/2015.

This module creates functions for pulling the proprietorship soi tax data into
NAICS trees.
'''
# Packages:
import os.path
import numpy as np
import pandas as pd
import xlrd
# Directories:
_CUR_DIR = os.path.dirname(__file__)
_DATA_DIR = os.path.join(_CUR_DIR, 'data')
_RAW_DIR = os.path.join(_DATA_DIR, 'raw_data')
_SOI_DIR = os.path.join(_RAW_DIR, 'soi')
_OUT_DIR = os.path.join(os.path.join(_CUR_DIR, 'output'),'soi')
_INT_DIR = os.path.join(_OUT_DIR, 'intermed_out')
_PROP_DIR = os.path.join(_SOI_DIR, 'soi_proprietorship')
_PRT_DIR = os.path.join(_SOI_DIR, 'soi_partner')
# Importing custom packages:
import naics_processing as naics
import file_processing as fp
import constants as cst
import pull_soi_partner as prt
# Dataframe names:
_FARM_DF_NM = cst.FARM_PROP_DF_NM
_NFARM_DF_NM = cst.NON_FARM_PROP_DF_NM
_CODE_DF_NM = cst.CODE_DF_NM
_TOT_CORP_DF_NM = cst.TOT_CORP_DF_NM
_AST_PRT_DF_NM = cst.AST_PRT_DF_NM
# (Optional) Hardcode the year that the partner data is from:
_YR = ''
_YR = str(_YR)
# Filenames:
_DDCT_IN_FILE = fp.get_file(dirct=_PROP_DIR, contains=[_YR+'sp01br.xls'])
_FARM_IN_FILE = fp.get_file(dirct=_PROP_DIR, contains=['farm_data.csv'])
_DDCT_IN_CROSS_FILE = fp.get_file(dirct=_PROP_DIR,
                                  contains=[_YR+'sp01br_Crosswalk.csv'])
# Full path for files:
_DDCT_IN_PATH = os.path.join(_PROP_DIR, _DDCT_IN_FILE)
_NFARM_PATH = os.path.join(_PROP_DIR, '12sp01br.csv')
_PRT_INC = os.path.join(_PRT_DIR, '12pa01.csv')
_PRT_ASST = os.path.join(_PRT_DIR, '12pa03.csv')
_NFARM_INV = os.path.join(_PROP_DIR, '12sp02is.csv')
_PRT_CROSS = os.path.join(_PRT_DIR, '12pa01_Crosswalk.csv')
_SOI_CODES = os.path.join(_SOI_DIR, 'SOI_codes.csv')
_FARM_IN_PATH = os.path.join(_PROP_DIR, _FARM_IN_FILE)
_DDCT_IN_CROSS_PATH = os.path.join(_PROP_DIR, _DDCT_IN_CROSS_FILE)
_NFARM_PROP_OUT_PATH = os.path.join(_OUT_DIR, _NFARM_DF_NM+'.csv')
_FARM_PROP_OUT_PATH = os.path.join(_OUT_DIR, _FARM_DF_NM+'.csv')
# Constant factors:
_DDCT_FILE_FCTR = 10**3
# Dataframe columns:
_NFARM_DF_COL_NMS = cst.DFLT_PROP_NFARM_DF_COL_NMS_DICT
_NFARM_DF_COL_NM = _NFARM_DF_COL_NMS['DEPR_DDCT']
_NFARM_DF_COL_INT = _NFARM_DF_COL_NMS['INT_PAID']
_AST_DF_COL_NMS_DICT = cst.DFLT_PRT_AST_DF_COL_NMS_DICT
_LAND_COL_NM = _AST_DF_COL_NMS_DICT['LAND_NET']
_DEPR_COL_NM = _AST_DF_COL_NMS_DICT['DEPR_AST_NET']
# Input--relevant row/column names in the nonfarm prop types excel worksheet:
_IN_COL_DF_DICT = dict([
                    ('Depreciation\ndeduction', 'DEPR_DDCT'),
                    ('Interest paid\ndeduction', 'INT_PAID')
                    ])
_SECTOR_COL = 'Industrial sector'
_DDCT_COL1 = 'Depreciation\ndeduction'
_DDCT_COL2 = 'Depreciation\ndeduction'
_DDCT_COL3 = 'Interest paid\ndeduction'
_DDCT_COL4 = 'Interest paid\ndeduction'


def load_soi_nonfarm_prop(sector_dfs, blue_tree=None, blueprint=None, 
                          from_out=False, out_path=_NFARM_PROP_OUT_PATH):
    ''' This function loads the soi nonfarm proprietorship data:
    
    :param data_tree: The NAICS tree to read the data into.
    :param cols_dict: A dictionary mapping dataframe columns to the name of
           the column names in the input file
    :param blueprint: The key corresponding to a dataframe in a tree to be
           used as a 'blueprint' for populating the df_list dataframes forward.
    :param blue_tree: A NAICS tree with the 'blueprint' dataframe. The default
           is the original NAICS tree.
    :param from_out: Whether to read in the data from output.
    :param output_path: The path of the output file.
    '''

    # Opens the file that contains the non farm sole prop data
    nonfarm_df = pd.read_csv(_NFARM_PATH)
    # Opens the nonfarm data crosswalk
    crosswalk = pd.read_csv(_DDCT_IN_CROSS_PATH)
    # Opens the nonfarm inventory data
    nonfarm_inv = prt.format_dataframe(pd.read_csv(_NFARM_INV).T,crosswalk)
    # Opens the crosswalk for the partner data
    prt_crosswalk = pd.read_csv(_PRT_CROSS)
    # Opens and formatting the partner depreciation deduction data 
    prt_deduct = pd.read_csv(_PRT_INC).T
    prt_deduct = prt.format_dataframe(prt_deduct, prt_crosswalk)
    # Opens and formatting the partner asset data
    prt_asst = pd.read_csv(_PRT_ASST).T
    prt_asst = prt.format_dataframe(prt_asst, prt_crosswalk)
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
    nfarm_df = interpolate_data(sector_dfs, nfarm_df)

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

    # If from_out, load the data tree from output:
    '''
    if from_out:
        data_tree = naics.load_tree_dfs(input_path=out_path, tree=data_tree)
        return data_tree
    # Opening nonfarm proprietor data:
    wb = xlrd.open_workbook(_DDCT_IN_PATH)
    ws = wb.sheet_by_index(0)
    cross = pd.read_csv(_DDCT_IN_CROSS_PATH)
    # Finding the relevant positions in worksheet:
    pos1 = naics.search_ws(ws, _SECTOR_COL, 20, True, [0,0], True)
    pos2 = naics.search_ws(ws, _DDCT_COL1, 20)
    pos3 = naics.search_ws(ws,_DDCT_COL2, 20,
                           True, np.array(pos2) + np.array([0,1]))
    pos4 = naics.search_ws(ws, _DDCT_COL3, 20)
    pos5 = naics.search_ws(ws,_DDCT_COL3, 20, True, np.array(pos4) + np.array([0,1]))
    #
    data_tree.append_all(df_nm=_NFARM_DF_NM, df_cols=[_NFARM_DF_COL_NM, _NFARM_DF_COL_INT])
    #
    cross_index = cross.shape[0]-1
    enum_index = len(data_tree.enum_inds)-1
    for i in xrange(pos1[0],ws.nrows):
        cur_cell = str(ws.cell_value(i,pos1[1])).lower().strip()
        #
        tot_proportions = 0
        for j in xrange(0, cross.shape[0]):
            cross_index = (cross_index+1) % cross.shape[0]
            cur_ind_name = str(cross.iloc[cross_index,0]).lower().strip()
            if(cur_cell == cur_ind_name):
                if pd.isnull(cross.iloc[cross_index,1]):
                    continue
                ind_codes = str(cross.iloc[cross_index,1]).split('.')
                for k in xrange(0, len(data_tree.enum_inds)):
                    enum_index = (enum_index+1) % len(data_tree.enum_inds)
                    cur_data = data_tree.enum_inds[enum_index].data
                    cur_codes = cur_data.dfs[_CODE_DF_NM]
                    cur_proportions = naics.compare_codes(ind_codes, cur_codes.iloc[:,0])
                    if cur_proportions == 0:
                        continue
                    tot_proportions += cur_proportions
                    cur_dfs_1 = cur_data.dfs[_NFARM_DF_NM][_NFARM_DF_COL_NM]
                    cur_dfs_2 = cur_data.dfs[_NFARM_DF_NM][_NFARM_DF_COL_INT]
                    cur_dfs_1[0] += (_DDCT_FILE_FCTR * cur_proportions 
                                        * (ws.cell_value(i,pos2[1]) 
                                        + ws.cell_value(i,pos3[1])))
                    cur_dfs_2[0] += (_DDCT_FILE_FCTR * cur_proportions 
                                        * (ws.cell_value(i,pos4[1]) 
                                        + ws.cell_value(i,pos5[1])))
            if(tot_proportions == 1):
                break
    # Default:
    if blueprint == None and _TOT_CORP_DF_NM in data_tree.enum_inds[0].data.dfs.keys():
        blueprint = _TOT_CORP_DF_NM
    naics.pop_back(tree=data_tree, df_list=[_NFARM_DF_NM])
    naics.pop_forward(tree=data_tree, df_list=[_NFARM_DF_NM],
                      blueprint=blueprint, blue_tree=blue_tree)
    #
    return data_tree
'''
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


# Fills in the missing values using the proportion of corporate industry values
def interpolate_data(sector_dfs, df):
    # Takes the total corp values as the baseline
    base_df = sector_dfs['tot_corp']
    # Stores the dataframe in a numpy array
    corp_data = np.array(base_df)
    # Stores the sole prop data in a numpy array
    prop_data = np.array(df)
    # Iterates over each industry in the partner data
    for i in xrange(0, len(prop_data)):
        # If it is a two digit code then it will appear in the denominator of the following calcs
        if(len(str(int(prop_data[i][0]))) == 2):
            # Grabs the parent data from the corporate array
            parent_ind = corp_data[i]
            # Grabs the sole prop data as well
            prop_ind = prop_data[i][1:]
        # If the partner data is missing a value
        if(prop_data[i][1] == 0):
            # Grabs the corporate data for the minor industry
            corp_ind = corp_data[i]
            # Divides the minor industry corporate data by the major industry data
            ratios = corp_ind / parent_ind
            # Mulitplies the sole prop data for the major data to find minor partner data
            new_data = prop_ind * ratios[1:]
            # Sets new values in the sole prop dataframe
            df.set_value(i, 'FA', new_data[0])
            df.set_value(i, 'Inv', new_data[1])
            df.set_value(i, 'Land', new_data[2])
    # Returns the sole prop dataframe with all the missing values filled in        
    return df
'''
def load_soi_farm_prop(data_tree,
                       blue_tree=None, blueprint=None,
                       from_out=False, out_path=_FARM_PROP_OUT_PATH):
    This function loads the soi nonfarm proprietorship data:
    
    :param data_tree: The NAICS tree to read the data into.
    :param cols_dict: A dictionary mapping dataframe columns to the name of
           the column names in the input file
    :param blueprint: The key corresponding to a dataframe in a tree to be
           used as a 'blueprint' for populating the df_list dataframes forward.
    :param blue_tree: A NAICS tree with the 'blueprint' dataframe. The default
           is the original NAICS tree.
    :param from_out: Whether to read in the data from output.
    :param output_path: The path of the output file.

    # If from_out, load the data tree from output:
    if from_out:
        data_tree = naics.load_tree_dfs(input_path=out_path, tree=data_tree)
        return data_tree
    # Load Farm Proprietorship data:
    farm_data = pd.read_csv(_FARM_IN_PATH)
    new_farm_cols = ['Land', 'FA']
    #
    data_tree.append_all(df_nm=_FARM_DF_NM, df_cols=new_farm_cols)
    #
    land_mult = ((farm_data['R_sp'][0] + farm_data['Q_sp'][0]) * 
                        (float(farm_data['A_sp'][0])/farm_data['A_p'][0]))
    total = farm_data['R_p'][0] + farm_data['Q_p'][0]
    total_pa = 0
    cur_codes = [111,112]
    proportions = np.zeros(len(cur_codes))
    proportions = naics.get_proportions(cur_codes, data_tree, _AST_PRT_DF_NM, 
                                 [_LAND_COL_NM, _DEPR_COL_NM])
    #
    for ind_code in cur_codes:
        cur_ind = naics.find_naics(data_tree, ind_code)
        cur_df = cur_ind.data.dfs[_AST_PRT_DF_NM]
        total_pa += (cur_df[_LAND_COL_NM][0] + cur_df[_DEPR_COL_NM][0])
    #
    for i in xrange(0,len(cur_codes)):
        cur_ind = naics.find_naics(data_tree, cur_codes[i])
        cur_ind.data.dfs[_FARM_DF_NM]['Land'][0] = (land_mult * 
                            cur_ind.data.dfs[_AST_PRT_DF_NM][_LAND_COL_NM][0]/
                            total_pa)
        cur_ind.data.dfs[_FARM_DF_NM]['FA'][0] = ((proportions.iloc[1,i]*total)
                                    - cur_ind.data.dfs[_FARM_DF_NM]['Land'][0])
    # Default:            
    if blueprint == None and _TOT_CORP_DF_NM in data_tree.enum_inds[0].data.dfs.keys():
        blueprint = _TOT_CORP_DF_NM
    naics.pop_back(tree=data_tree, df_list=[_FARM_DF_NM])
    naics.pop_forward(tree=data_tree, df_list=[_FARM_DF_NM],
                      blueprint=blueprint, blue_tree=blue_tree)
    #
    return data_tree
'''
