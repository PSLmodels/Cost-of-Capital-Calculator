'''
SOI Partner Tax Data (pull_soi_partner.py):
-------------------------------------------------------------------------------
Last updated: 6/29/2015.

This module creates functions for pulling the partnership soi tax data into
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
_PRT_DIR = os.path.join(_SOI_DIR, 'soi_partner')
# Importing custom modules:
import naics_processing as naics
import file_processing as fp
import constants as cst
# Dataframe names:
_INC_DF_NM = cst.INC_PRT_DF_NM
_AST_DF_NM = cst.AST_PRT_DF_NM
_TYP_DF_NM = cst.TYP_PRT_DF_NM
_TOT_CORP_DF_NM = cst.TOT_CORP_DF_NM
# (Optional) Hardcode the year that the partner data is from:
_YR = ''
_YR = str(_YR)
# Filenames:
_INC_IN_FILE = fp.get_file(dirct=_PRT_DIR, contains=[_YR+'pa01.xls'])
_AST_IN_FILE = fp.get_file(dirct=_PRT_DIR, contains=[_YR+'pa03.xls'])
_TYP_IN_FILE = fp.get_file(dirct=_PRT_DIR, contains=[_YR+'pa05.xls'])
_INC_IN_CROSS_FILE = fp.get_file(dirct=_PRT_DIR,
                                 contains=[_YR+'pa01_Crosswalk.csv'])
_AST_IN_CROSS_FILE = fp.get_file(dirct=_PRT_DIR,
                                 contains=[_YR+'pa03_Crosswalk.csv'])
_TYP_IN_CROSS_FILE = fp.get_file(dirct=_PRT_DIR,
                                 contains=[_YR+'pa05_Crosswalk.csv'])
_INC_OUT_FILE = _INC_DF_NM + '.csv'
_AST_OUT_FILE = _AST_DF_NM + '.csv'
_TYP_OUT_FILE = _TYP_DF_NM + '.csv'
# Full path for files:
_INC_IN_PATH = os.path.join(_PRT_DIR, _INC_IN_FILE)
_AST_IN_PATH = os.path.join(_PRT_DIR, _AST_IN_FILE)
_TYP_IN_PATH = os.path.join(_PRT_DIR, _TYP_IN_FILE)
_INC_IN_CROSS_PATH = os.path.join(_PRT_DIR, _INC_IN_CROSS_FILE)
_AST_IN_CROSS_PATH = os.path.join(_PRT_DIR, _AST_IN_CROSS_FILE)
_TYP_IN_CROSS_PATH = os.path.join(_PRT_DIR, _TYP_IN_CROSS_FILE)
_INC_OUT_PATH = os.path.join(_OUT_DIR, _INC_OUT_FILE)
_AST_OUT_PATH = os.path.join(_OUT_DIR, _AST_OUT_FILE)
_TYP_OUT_PATH = os.path.join(_OUT_DIR, _TYP_OUT_FILE)
_INC_FILE = os.path.join(_PRT_DIR, '12pa01.csv')
_AST_FILE = os.path.join(_PRT_DIR, '12pa03.csv')
_TYP_FILE = os.path.join(_PRT_DIR, '12pa05.csv')
_SOI_CODES = os.path.join(_SOI_DIR, 'SOI_codes.csv')
# Constant factors:
_INC_FILE_FCTR = 10**3
_AST_FILE_FCTR = 10**3
_TYP_FILE_FCTR = 10**3
#  Dataframe column names:
_INC_PRT_COLS_DICT = cst.DFLT_PRT_INC_DF_COL_NMS_DICT
_INC_NET_INC_COL_NM = _INC_PRT_COLS_DICT['NET_INC']
_INC_NET_LOSS_COL_NM = _INC_PRT_COLS_DICT['NET_LOSS']
_INC_DEPR_COL_NM = _INC_PRT_COLS_DICT['DEPR']
_INC_INT_PAID_COL_NM = _INC_PRT_COLS_DICT['INTRST_PD']
_INC_PRT_DF_COL_NMS = cst.DFLT_PRT_INC_DF_COL_NMS
# Input--relevant row/column names in the partnership income excel worksheet:
_INC_STRT_COL_NM = 'All\nindustries'
_INC_NET_INC_ROW_NM = 'total net income'
_INC_DEPR_ROW_NM = 'depreciation'
_INC_INT_PAID_ROW_NM = 'interest paid'
# Input--relevant row/column names in the partnership asset excel worksheet:
_AST_IN_ROW_NMS= ['Depreciable assets', 'Accumulated depreciation',
                  'Inventories', 'Land', 'Partners capital accounts']
_AST_IN_ROWS_DF_NET_DICT = dict([
                    ('Depreciable assets', 'DEPR_AST_NET'),
                    ('Accumulated depreciation', 'ACC_DEPR_NET'),
                    ('Inventories', 'INV_NET'),
                    ('Land', 'LAND_NET'),
                    ('Partners capital accounts', 'PCA_NET')
                    ])
_AST_IN_ROWS_DF_INC_DICT = dict([
                    ('Depreciable assets', 'DEPR_AST_INC'),
                    ('Accumulated depreciation', 'ACC_DEPR_INC'),
                    ('Inventories', 'INV_INC'),
                    ('Land', 'LAND_INC'),
                    ('Partners capital accounts', 'PCA_INC')
                    ])
_AST_IN_ROW_NMS = _AST_IN_ROWS_DF_NET_DICT.keys()
_AST_DF_DICT = cst.DFLT_PRT_AST_DF_COL_NMS_DICT
# Input--relevant row/column names in the partnership types excel worksheet:
_TYP_IN_ROWS_DF_DICT = dict([
                    ('Corporate general partners', 'CORP_GEN_PRT'),
                    ('Corporate limited partners', 'CORP_LMT_PRT'),
                    ('Individual general partners', 'INDV_GEN_PRT'),
                    ('Individual limited partners', 'INDV_LMT_PRT'),
                    ('Partnership general partners', 'PRT_GEN_PRT'),
                    ('Partnership limited partners', 'PRT_LMT_PRT'),
                    ('Tax-exempt organization general partners', 'EXMP_GEN_PRT'),
                    ('Tax-exempt organization limited partners', 'EXMP_LMT_PRT'),
                    ('Nominee and other general partners', 'OTHER_GEN_PRT'),
                    ('Nominee and other limited partners', 'OTHER_LMT_PRT')
                    ])
_TYP_IN_ROW_NMS = _TYP_IN_ROWS_DF_DICT.keys()
_TYP_DF_DICT = cst.DFLT_PRT_TYP_DF_COL_NMS_DICT
_SHAPE = (131,4)
_CODE_RANGE = ['32', '33', '45', '49']
_PARENTS = {'32':'31','33':'31','45':'44','49':'48'}


def load_income(data_tree,
                blue_tree=None, blueprint=None,
                from_out=False, out_path=None):
    ''' This function loads the soi partnership income data.
    
    :param data_tree: The NAICS tree to read the data into.
    :param blueprint: The key corresponding to a dataframe in a tree to be
           used as a 'blueprint' for populating the df_list dataframes forward.
    :param blue_tree: A NAICS tree with the 'blueprint' dataframe. The default
           is the original NAICS tree.
    :param from_out: Whether to read in the data from output.
    '''
    # Initializing the output path:
    if out_path == None:
        out_path = _INC_OUT_PATH
    # If from_out, load the data tree from output:
    if from_out:
        data_tree = naics.load_tree_dfs(input_path=out_path, 
                                        tree=data_tree)
        return data_tree
    # Opening data on net income/loss:
    wb = xlrd.open_workbook(_INC_IN_PATH)
    ws = wb.sheet_by_index(0)
    start_col = naics.search_ws(ws, _INC_STRT_COL_NM, 20)[1]
    # Initializing dataframe to hold pertinent income/loss data:
    data_df = pd.DataFrame(np.zeros((ws.ncols-start_col,4)), 
                           columns = _INC_PRT_DF_COL_NMS)
    # Extracting the data from the worksheet:
    for row in xrange(0, ws.nrows):
        # Going through each row of excel file, looking for input rows:
        if(_INC_NET_INC_ROW_NM in str(ws.cell_value(row,0)).lower()):
            data_df[_INC_NET_INC_COL_NM] = ws.row_values(row+1, start_col)
            data_df[_INC_NET_LOSS_COL_NM] = ws.row_values(row+2, start_col)
            break
        if(_INC_INT_PAID_ROW_NM in str(ws.cell_value(row,0)).lower()):
            data_df[_INC_INT_PAID_COL_NM] = ws.row_values(row, start_col)
        if(_INC_DEPR_ROW_NM in str(ws.cell_value(row,0)).lower()):
            data_df[_INC_DEPR_COL_NM] = ws.row_values(row, start_col)  
    # Scaling the data to the correct units:
    data_df = data_df * _INC_FILE_FCTR
    # Reading in the crosswalks between the columns and the NAICS codes:
    pa01cross = pd.read_csv(_INC_IN_CROSS_PATH)
    # Processing the inc/loss data into the NAICS tree:
    data_tree = naics.load_data_with_cross(
                    data_tree=data_tree, data_df=data_df,
                    cross_df=pa01cross, df_nm=_INC_DF_NM
                    )
    # Default blueprint is tot_corps:
    has_tot_df = _TOT_CORP_DF_NM in data_tree.enum_inds[0].data.dfs.keys()
    if blueprint == None and has_tot_df:
        blueprint = _TOT_CORP_DF_NM
    # Populate all levels of specificity in the NAICS tree:
    '''
    naics.pop_back(tree=data_tree, df_list=[_INC_DF_NM])
    naics.pop_forward(tree=data_tree, df_list=[_INC_DF_NM],
                      blueprint=blueprint, blue_tree=blue_tree)
    '''
    
    return data_tree
    
    
def load_asset(blue_tree=None, blueprint=None,
             from_out=False, out_path=None):
    ''' This function loads the soi partnership asset data.
    
    :param data_tree: The NAICS tree to read the data into.
    :param blueprint: The key corresponding to a dataframe in a tree to be
           used as a 'blueprint' for populating the df_list dataframes forward.
    :param blue_tree: A NAICS tree with the 'blueprint' dataframe. The default
           is the original NAICS tree.
    :param from_out: Whether to read in the data from output.
    '''
    # Initializing the output path:
    if out_path == None:
        out_path = _AST_OUT_PATH
    # If from_out, load the data tree from output:
    if from_out:
        data_tree = naics.load_tree_dfs(input_path=out_path,
                                        tree=data_tree)
        return data_tree
    # Opening data on depreciable fixed assets, inventories, and land:
    df = pd.read_csv(_AST_FILE).transpose()
    ast_cross = pd.read_csv(_AST_IN_CROSS_PATH)
    df = format_dataframe(df, ast_cross)
    df1 = df.T.groupby(sort=False,level=0).first().T
    df1 = df1.groupby('Codes:',sort=False).sum()
    codes = df1.index.tolist()
    df1.insert(0,'Codes:', codes)
    df1.index = np.arange(0,len(df1))
    df2 = df.T.groupby(sort=False,level=0).last().T
    df2 = df2.groupby('Codes:',sort=False).sum()
    codes = df2.index.tolist()
    df2.insert(0,'Codes:', codes)
    df2.index = np.arange(0,len(df2))
    codes = pd.read_csv(_SOI_CODES)

    tot_data = np.array(df1)
    inc_loss = pd.read_csv(_INC_FILE).transpose()
    inc_cross = pd.read_csv(_INC_IN_CROSS_PATH)
    inc_loss = format_dataframe(inc_loss, inc_cross)
    col_list = ['Item', 'Codes:', 'Net income', 'Loss']

    inc_loss = inc_loss.T.groupby(sort=False,level=0).last().T[col_list]
    inc_loss = inc_loss.groupby('Codes:',sort=False).sum()
    codes = inc_loss.index.tolist()
    inc_loss.insert(0,'Codes:', codes)
    inc_loss.index = np.arange(0,len(inc_loss))
    inc_loss = np.array(inc_loss)
    prof_fa_data = np.array(df2['Depreciable assets']-df2['Less:  Accumulated depreciation'])
    prof_inv_data = np.array(df2['Inventories'])
    prof_land_data = np.array(df2['Land'])
    loss_fa_data = np.array((df1['Depreciable assets']-df1['Less:  Accumulated depreciation']-
        df2['Depreciable assets']+df2['Less:  Accumulated depreciation']))
    loss_inv_data = np.array(df1['Inventories'] - prof_inv_data)
    loss_land_data = np.array(df1['Land'] - prof_land_data)

    prt_cstock = np.zeros(_SHAPE)
    loss_ratios = np.zeros(_SHAPE)
    prof_ratios = np.zeros(_SHAPE)
    for i in xrange(0,len(tot_data)):
        prt_cstock[i] = np.array([int(tot_data[i][0]),float(tot_data[i][16])- float(tot_data[i][17]),
             float(tot_data[i][9]), float(tot_data[i][20])])
        if(inc_loss[i][3] != 0):
            loss_ratios[i] = np.array([int(tot_data[i][0]),loss_fa_data[i] / float(inc_loss[i][3]),
                loss_inv_data[i] / float(inc_loss[i][3]), loss_land_data[i] / float(inc_loss[i][3])])
        
        if(inc_loss[i][2] != 0):
            prof_ratios[i] = np.array([int(tot_data[i][0]), prof_fa_data[i] / float(inc_loss[i][2]),
                prof_inv_data[i] / float(inc_loss[i][2]),prof_land_data[i] / float(inc_loss[i][2])])

    prt_types = pd.read_csv(_TYP_FILE).transpose()
    typ_cross = pd.read_csv(_TYP_IN_CROSS_PATH)
    prt_types = format_dataframe(prt_types, typ_cross)
    prt_data = np.array(prt_types)
    index = {}
    for i in xrange(0,len(codes)):
        index[codes[i]] = i

    capital_stock = []
    code_dict = {}
    j = 0
    for array in prt_data:
        fixed_assets = []
        land_data = []
        inventories = []
        code = int(array[1])
        code_dict[code] = j
        if(index.has_key(code)):
            i = index[code]
            for element in array[2:]:
                if(element > 0):
                    fixed_asset = prof_ratios[i][0] * float(element)
                    invs = prof_ratios[i][1] * float(element)
                    land = prof_ratios[i][2] * float(element)
                else:
                    fixed_asset = prof_ratios[i][0] * abs(float(element))
                    invs = prof_ratios[i][1] * abs(float(element))
                    land = prof_ratios[i][2] * abs(float(element))
                fixed_assets.append(fixed_asset)
                land_data.append(land)
                inventories.append(invs)
            capital_stock.append([code, np.array(fixed_assets), np.array(land_data), np.array(inventories)])
            j += 1

    prt_cap_stock = []
    for ind in prt_cstock:
        code1 = int(ind[0])
        if(code_dict.has_key(code1)):
            prt_cap_stock.append(capital_stock[code_dict[code1]])
        else:
            code2 = int(str(code1)[:2])
            if(str(code2) in _CODE_RANGE):
                code2 = int(_PARENTS[str(code2)])
            index1 = index[code2]
            prt_cap_stock.append([code1, capital_stock[code_dict[code2]][1] * ind[1] / prt_cstock[index1][1], 
            capital_stock[code_dict[code2]][2] * ind[2] / prt_cstock[index1][2],
            capital_stock[code_dict[code2]][3] * ind[3] / prt_cstock[index1][3]])

    prt_types = ['corp_gen', 'corp_lim', 'indv_gen', 'indv_lim', 'prt_gen', 'prt_lim', 'tax_gen', 'tax_lim', 'nom_gen', 'nom_lim']

    prt_data = {}
    baseline_codes = pd.read_csv(_SOI_CODES)
    for i in xrange(0,len(prt_types)):
        ind_capital = []
        for ind in prt_cap_stock:
            ind_capital.append([ind[0], ind[1][i+1], ind[2][i+1], ind[3][i+1]])      
        df = pd.DataFrame(ind_capital, index = np.arange(0,len(ind_capital)), columns = ['Codes:', 'FA', 'Inv', 'Land'])
        df = baseline_codes.merge(df, how = 'outer').fillna(0)
        df = baseline_codes.merge(df, how = 'inner')
        prt_data[prt_types[i]] = df

    return prt_data 
    '''    
    wb = xlrd.open_workbook(_AST_IN_PATH) 
    ws = wb.sheet_by_index(0)
    num_rows = ws.nrows
    # Columns of the asset dataframe:
    df_cols = _AST_DF_DICT.values()
    # Initializing dataframe to hold pertinent asset data:
    ast_df = pd.DataFrame(np.zeros((ws.ncols-1,len(df_cols))), columns=df_cols)
    
    Extracting the data (note that the rows with total data appear first).
    For each input row:
    for in_row_nm in _AST_IN_ROW_NMS:
        # Key corresponding to total asset column:
        df_net_col_key = _AST_IN_ROWS_DF_NET_DICT[in_row_nm]
        # Asset dataframes net income column name:
        df_net_col_nm = _AST_DF_DICT[df_net_col_key]
        # Key corresponding to assets of net income partnerships column:
        df_inc_col_key = _AST_IN_ROWS_DF_INC_DICT[in_row_nm]
        # Asset dataframes total income column name:
        df_inc_col_nm = _AST_DF_DICT[df_inc_col_key]
        in_row_nm = in_row_nm.lower()
        # Finding the first input row with in_row_nm:
        for in_row1 in xrange(0, num_rows):
            in_net_row_nm = str(ws.cell_value(in_row1,0)).lower()
            if(in_row_nm in in_net_row_nm):
                # Total asset data:
                ast_df[df_net_col_nm] = ws.row_values(in_row1, 1)
                # Finding the second input row with in_row_nm:
                for in_row2 in xrange(in_row1+1, num_rows):
                    in_inc_row_nm = str(ws.cell_value(in_row2,0)).lower()
                    if(in_row_nm in in_inc_row_nm):
                        # Asset data for companies with net income:
                        ast_df[df_inc_col_nm] = ws.row_values(in_row2,1)
                        break
                break
    # Scaling the data to the correct units:
    ast_df = ast_df * _AST_FILE_FCTR
    # Reading in the crosswalks between the columns and the NAICS codes:
    ast_cross = pd.read_csv(_AST_IN_CROSS_PATH)
    # Processing the asset data into the NAICS tree:
    data_tree = naics.load_data_with_cross(
                    data_tree=data_tree, data_df=ast_df,
                    cross_df=ast_cross, df_nm=_AST_DF_NM
                    )
    # Default blueprint is tot_corps:
    has_tot_df = _TOT_CORP_DF_NM in data_tree.enum_inds[0].data.dfs.keys()
    if blueprint == None and has_tot_df:
        blueprint = _TOT_CORP_DF_NM
    # Populate all levels of specificity in the NAICS tree:
    
    naics.pop_back(tree=data_tree, df_list=[_AST_DF_NM])
    naics.pop_forward(tree=data_tree, df_list=[_AST_DF_NM],
                      blueprint=blueprint, blue_tree=blue_tree)
    '''
    return data_tree

def format_dataframe(df, crosswalk):
    indices = []
    for string in df.index:
        indices.append(string.replace('\n',' '))
    df.insert(0,indices[0],indices)
    columns = df.iloc[0].tolist()
    df = df[df.Item != 'Item']
    for i in xrange(0,len(columns)):
        columns[i] = columns[i].strip()
    df.columns = columns
    
    df.index = np.arange(0,len(crosswalk['Codes:']))
    df.insert(1,'Codes:',crosswalk['Codes:'])
    names = df['Item']
    codes = df['Codes:'] 
    df = df * _AST_FILE_FCTR
    df['Item'] = names
    df['Codes:'] = codes
    return df

def calc_proportions(tree):
    codes = pd.read_csv(_TYP_IN_CROSS_PATH)['Codes:']
    naics = []
    for code in codes:
        if(len(str(code))==2 or '-' in str(code)):
            naics.append(code)
    for ind in tree.enum_inds:
        if(ind.prt_types[0] == 0 and ind.prt_cstock[0] != 0):
            if('-' in ind.parent.naics):
                code1 = ind.naics[:5]
            else:
                code1 = ind.naics[:2]
            code2 = ind.naics
            index1 = tree.codes[code1]
            index2 = tree.codes[code2]
            ind.prt_types = tree.enum_inds[index1].prt_types / tree.enum_inds[index1].prt_cstock[0] * tree.enum_inds[index2].prt_cstock[0]
            ind.inv_types = tree.enum_inds[index1].prt_inv / tree.enum_inds[index1].prt_cstock[1] * tree.enum_inds[index2].prt_cstock[1]
            ind.land_types = tree.enum_inds[index1].prt_land / tree.enum_inds[index1].prt_cstock[2] * tree.enum_inds[index2].prt_cstock[2]
    return tree



def load_type(data_tree,
               blue_tree = None, blueprint = None, 
               from_out=False, out_path=None):
    ''' This function loads the soi partnership asset data.
    
    :param data_tree: The NAICS tree to read the data into.
    :param blueprint: The key corresponding to a dataframe in a tree to be
           used as a 'blueprint' for populating the df_list dataframes forward.
    :param blue_tree: A NAICS tree with the 'blueprint' dataframe. The default
           is the original NAICS tree.
    :param from_out: Whether to read in the data from output.
    '''
    # Initializing the output path:
    if out_path == None:
        out_path = _TYP_OUT_PATH
    # If from_out, load the data tree from output:
    if from_out:
        data_tree = naics.load_tree_dfs(input_path=out_path,
                                        tree=data_tree)
        return data_tree
    # Opening data on income by partner type:
    wb = xlrd.open_workbook(_TYP_IN_PATH)
    ws = wb.sheet_by_index(0)
    num_rows = ws.nrows
    # Initializing dataframe to hold pertinent type income data:
    typ_df = pd.DataFrame(np.zeros((ws.ncols-1, len(_TYP_IN_ROW_NMS))),
                          columns=_TYP_DF_DICT.values())
    # Extracting the data. For each input row:
    for in_row_nm in _TYP_IN_ROW_NMS:
        
        df_col_key = _TYP_IN_ROWS_DF_DICT[in_row_nm]
        df_col_nm = _TYP_DF_DICT[df_col_key]
        in_row_nm = in_row_nm.lower()
        for ws_row_index in xrange(0, num_rows):
            ws_row_nm = str(ws.cell_value(ws_row_index,0)).lower()
            if(in_row_nm in ws_row_nm):
                typ_df[df_col_nm] = ws.row_values(ws_row_index,1)
                break
    # Scaling the data to the correct units:
    typ_df = typ_df * _TYP_FILE_FCTR
    # Reading in the crosswalks between the columns and the NAICS codes:
    typ_cross = pd.read_csv(_TYP_IN_CROSS_PATH)
    #
    data_tree = naics.load_data_with_cross(
                    data_tree=data_tree, data_df=typ_df,
                    cross_df=typ_cross, df_nm=_TYP_DF_NM
                    )
    # Default blueprint is partner income, and, if not, then tot_corps:
    has_inc_df = _INC_DF_NM in data_tree.enum_inds[0].data.dfs.keys()
    has_tot_df = _TOT_CORP_DF_NM in data_tree.enum_inds[0].data.dfs.keys()
    if blueprint == None and has_inc_df:
        blueprint = _INC_DF_NM
    elif blueprint == None and has_tot_df:
        blueprint = _TOT_CORP_DF_NM
    # Populate all levels of specificity in the NAICS tree:
    '''
    naics.pop_back(tree=data_tree, df_list=[_TYP_DF_NM])
    naics.pop_forward(tree=data_tree, df_list=[_TYP_DF_NM],
                      blueprint=blueprint, blue_tree=blue_tree)
    '''
    return data_tree

