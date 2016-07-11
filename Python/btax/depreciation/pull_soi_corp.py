"""
SOI Corporate Tax Data (pull_soi_corp.py):
-------------------------------------------------------------------------------
Last updated: 6/26/2015.

This module creates functions for pulling the corporate soi tax data into
NAICS trees. The data is categorized into C, S, and their aggregate.
Note that only the S and aggregate corporation data are explicitly given.
The C-corporation data is inferred from the two.
"""
# Packages:
import os.path
import numpy as np
import pandas as pd
# Directory names:
_CUR_DIR = os.path.dirname(__file__)
_DATA_DIR = os.path.join(_CUR_DIR, 'data')
_RAW_DIR = os.path.join(_DATA_DIR, 'raw_data')
_SOI_DIR = os.path.join(_RAW_DIR, 'soi')
_OUT_DIR = os.path.join(os.path.join(_CUR_DIR, 'output'),'soi')
_INT_DIR = os.path.join(_OUT_DIR, 'intermed_out')
_CORP_DIR = os.path.join(_SOI_DIR, 'soi_corporate')
# Importing custom modules:
import naics_processing as naics
import file_processing as fp
import constants as cst
# Dataframe names:
_TOT_DF_NM = cst.TOT_CORP_DF_NM
_S_DF_NM = cst.S_CORP_DF_NM
_C_DF_NM = cst.C_CORP_DF_NM
# (Optional) Hardcode the year that the partner data is from:
_YR = ""
_YR = str(_YR)
# Filenames:
_TOT_CORP_IN_FILE = fp.get_file(dirct=_CORP_DIR, contains=[_YR+"sb1.csv"])
_S_CORP_IN_FILE = fp.get_file(dirct=_CORP_DIR, contains=[_YR+"sb3.csv"])
# Full path for files:
_TOT_CORP_IN_PATH = os.path.join(_CORP_DIR, _TOT_CORP_IN_FILE)
_S_CORP_IN_PATH = os.path.join(_CORP_DIR, _S_CORP_IN_FILE)
_TOT_CORP_OUT_PATH = os.path.join(_OUT_DIR, _TOT_DF_NM+".csv")
_S_CORP_OUT_PATH = os.path.join(_OUT_DIR, _S_DF_NM+".csv")
_C_CORP_OUT_PATH = os.path.join(_OUT_DIR, _C_DF_NM+".csv")
# Constant factors:
_TOT_CORP_IN_FILE_FCTR = 10**3
_S_CORP_IN_FILE_FCTR = 10**3
# Input--default dictionaries for df-columns to input-columns.
_DFLT_TOT_CORP_COLS_DICT = cst.DFLT_TOT_CORP_COLS_DICT
_DFLT_S_CORP_COLS_DICT = cst.DFLT_S_CORP_COLS_DICT
# Input--NAICS column:
_NAICS_COL_NM = "INDY_CD"
_CODE_RANGE = ['32', '33', '45', '49']
_PARENTS = {'32':'31','33':'31','45':'44','49':'48'}

'''
def load_soi_tot_corp(data_tree,
                      cols_dict=_DFLT_TOT_CORP_COLS_DICT, 
                      blueprint=None, blue_tree=None,
                      from_out=False, output_path=_TOT_CORP_OUT_PATH):
    """ This function pulls the soi total corporation data.
    
    :param data_tree: The NAICS tree to read the data into.
    :param cols_dict: A dictionary mapping dataframe columns to the name of
           the column names in the input file
    :param blueprint: The key corresponding to a dataframe in a tree to be
           used as a "blueprint" for populating the df_list dataframes forward.
    :param blue_tree: A NAICS tree with the "blueprint" dataframe. The default
           is the original NAICS tree.
    :param from_out: Whether to read in the data from output.
    :param output_path: The path of the output file.
    """
    # If from_out, load the data tree from output:
    if from_out:
        data_tree = naics.load_tree_dfs(input_path=output_path, tree=data_tree)
        return data_tree
    # Pertinent information:
    num_inds = len(data_tree.enum_inds) # Number of industries in NAICS tree.
    data_cols = cols_dict.keys() # Dataframe column names.
    # Opening the soi total corporate data file:
    try:
        tot_corp_data = pd.read_csv(_TOT_CORP_IN_PATH).fillna(0)
    except IOError:
        print "IOError: Tot-Corp soi data file not found."
        return None
    # Initializing dataframes for all NAICS industries:
    data_tree.append_all(df_nm=_TOT_DF_NM, df_cols=data_cols)
    # Reading the total corporation data into the NAICS tree:
    enum_index = 0
    for code_num in np.unique(tot_corp_data[_NAICS_COL_NM]):
        # Find the industry with a code that matches "code_num":
        ind_found = False
        for i in range(0, num_inds):
            enum_index = (enum_index + 1) % num_inds
            cur_ind = data_tree.enum_inds[enum_index]
            cur_dfs = cur_ind.data.dfs[cst.CODE_DF_NM]
            for j in range(0, cur_dfs.shape[0]):
                if(cur_dfs.iloc[j,0] == code_num):
                    # Industry with the matching code has been found:
                    ind_found = True
                    cur_dfs = cur_ind.data.dfs[_TOT_DF_NM]
                    break
            # If the matching industry has been found stop searching for it:
            if ind_found:
                break
        # If no match was found, then ignore data.
        if not ind_found:
            continue
        # Indicators for if rows in tot_corp_data match current industry code:
        indicators = (tot_corp_data[_NAICS_COL_NM] == code_num)
        # Calculating the data:
        for j in cols_dict:
            # Some of the data may not be reported:
            if cols_dict[j] == "":
                cur_dfs[j] = 0
            else:
                # Note: double counting the data in the original dataset.
                cur_dfs[j][0] = sum(indicators * tot_corp_data[cols_dict[j]])/2.0
                cur_dfs[j][0] = cur_dfs[j] * _TOT_CORP_IN_FILE_FCTR
    # Populate all levels of specificity in the NAICS tree:

    naics.pop_back(tree=data_tree, df_list=[_TOT_DF_NM])
    naics.pop_forward(tree=data_tree, df_list=[_TOT_DF_NM],
                      blueprint=blueprint, blue_tree=blue_tree)

    naics.pop_back(tree=data_tree, df_list=[_TOT_DF_NM])
    naics.pop_forward(tree=data_tree, df_list=[_TOT_DF_NM],
                      blueprint=blueprint, blue_tree=blue_tree)

    return data_tree
'''

def load_soi_s_corp(cols_dict=_DFLT_S_CORP_COLS_DICT,
                    blue_tree=None, blueprint=None,
                    from_out=False, out_path=_S_CORP_OUT_PATH):
    """ This function pulls the soi s-corporation data.
    
    :param data_tree: The tree to read the data into.
    :param cols_dict: A dictionary mapping dataframe columns to the name of
           the column names in the input file
    :param blueprint: The key corresponding to a dataframe in a tree to be
           used as a "blueprint" for populating the df_list dataframes forward.
    :param blue_tree: A NAICS tree with the "blueprint" dataframe. The default
           is the original NAICS tree.
    :param from_out: Whether to read in the data from output.
    :param output_path: The path of the output file.
    """
    # Dataframe column names
    data_cols = cols_dict.keys()
    # Opening the soi S-corporate data file:
    try:
        s_corp_data = pd.read_csv(_S_CORP_IN_PATH).fillna(0)
    except IOError:
        print "IOError: S-Corp soi data file not found."
        return None  
    # Opening the soi Total-corporate data file:      
    try:
        tot_corp_data = pd.read_csv(_TOT_CORP_IN_PATH).fillna(0)
    except IOError:
        print "IOError: S-Corp soi data file not found."
        return None

    # Formatting the list of columns that will be used to trim the dataframe for the necessary data
    columns = cols_dict.values()
    columns.remove('')
    columns.insert(0,'INDY_CD')
    # Selecting out only the total industry values for the s corp data
    s_corp_data = s_corp_data[(s_corp_data.AC == 1)]
    s_corp_data = s_corp_data[columns] * _S_CORP_IN_FILE_FCTR
    s_corp_data['INDY_CD'] = s_corp_data['INDY_CD'] / _S_CORP_IN_FILE_FCTR
    # Repeating the same process of trimming and selecting on the total corp data
    tot_corp_data = tot_corp_data[(tot_corp_data.AC == 1)]
    tot_corp_data = tot_corp_data[columns] * _TOT_CORP_IN_FILE_FCTR
    tot_corp_data['INDY_CD'] = tot_corp_data['INDY_CD'] / _TOT_CORP_IN_FILE_FCTR
    # Assigns values to the missing s corp data based on the proportions of the total data
    s_corp_data = calc_proportions(tot_corp_data, s_corp_data, columns)
    # Calculates the c corp data by subtracting the s corp data from the total corp data
    c_corp = np.array(tot_corp_data) - np.array(s_corp_data)
    # Creates a dataframe and .csv file for all the industries for which we have soi corporate data
    codes = tot_corp_data['INDY_CD'].tolist()
    code_csv = pd.DataFrame(codes, index=np.arange(0,len(codes)), columns = ['Codes:'])
    code_csv.to_csv(os.path.join(_SOI_DIR,'SOI_codes.csv'),index=False)
    # Adds the missing codes back into the c corp data (lost in the subtraction step)
    for i in xrange(0,len(codes)):
        c_corp[i][0] = codes[i]
    # Creates a dataframe for the c corp data
    c_corp_data = pd.DataFrame(c_corp, index=np.arange(0,len(c_corp)), columns = columns)
    # Creates a list of the columns we want to keep in the corp dataframes
    cstock = ['INDY_CD', 'FA', 'INVNTRY', 'LAND']
    # Calculates the amount of fixed assets: Depreciables assets - accumulated depreciated
    tot_corp_data['FA'] = tot_corp_data['DPRCBL_ASSTS'] - tot_corp_data['ACCUM_DPR']
    s_corp_data['FA'] = s_corp_data['DPRCBL_ASSTS'] - s_corp_data['ACCUM_DPR']
    c_corp_data['FA'] = c_corp_data['DPRCBL_ASSTS'] - c_corp_data['ACCUM_DPR']
    # Trims off the extra columns in the corporate dataframes
    tot_corp_data = tot_corp_data[cstock]
    s_corp_data = s_corp_data[cstock]
    c_corp_data = c_corp_data[cstock]
    # Changes the column name for the codes of each dataframe
    tot_corp_data.columns.values[0] = 'Codes:'
    s_corp_data.columns.values[0] = 'Codes:'
    c_corp_data.columns.values[0] = 'Codes:'
    # Reformats the indices of the total corp data so it can be indexed correctly
    tot_corp_data.index = np.arange(0,len(tot_corp_data))
    # Creates a dictionary of a sector : dataframe
    corp_data = {'tot_corp': tot_corp_data, 'c_corp': c_corp_data, 's_corp': s_corp_data}

    return corp_data
    '''
    # Loads the total and s corp data into the tree, stored at the industry level
    data_tree = populate_tree(data_tree, tot_corp_data, s_corp)
    # Uses the loaded data to calculate the c corp data: c corp = tot corp - s corp
    data_tree = calc_corp(data_tree)
    
    # Initializing dataframes for all NAICS industries:
    data_tree.append_all(df_nm=_S_DF_NM, df_cols=data_cols)
    # Reading the S-corporation data into the NAICS tree:
    enum_index = 0
    for code_num in np.unique(s_corp_data[_NAICS_COL_NM]):
        # Find the industry with a code that matches "code_num":
        ind_found = False
        for i in range(0, len(data_tree.enum_inds)):
            enum_index = (enum_index + 1) % num_inds
            cur_ind = data_tree.enum_inds[i]
            cur_dfs = cur_ind.data.dfs[cst.CODE_DF_NM]
            for j in range(0, cur_dfs.shape[0]):
                if(cur_dfs.iloc[j,0] == code_num):
                    # Industry with the matching code has been found:
                    ind_found = True
                    cur_dfs = cur_ind.data.dfs[cst.S_CORP_DF_NM]
                    break
            # If the matching industry has been found stop searching for it.
            if ind_found:
                break
        # If no match was found, then ignore data.
        if not ind_found:
            continue
        # Indicators for if rows in s_corp_data match current industry code:
        indicators = (s_corp_data[_NAICS_COL_NM] == code_num)
        # Calculating the data:
        for j in cols_dict:
            # Some are not reported for S Corporations:
            if cols_dict[j] == "":
                cur_dfs[j] = 0
            else:
                cur_dfs.loc[0,j] = sum(indicators * s_corp_data[cols_dict[j]])/2.0
                cur_dfs.loc[0,j] = cur_dfs.loc[0,j] * _S_CORP_IN_FILE_FCTR
    # Default blueprint is tot_corps:
    has_tot_df = _TOT_DF_NM in data_tree.enum_inds[0].data.dfs.keys()
    if blueprint == None and has_tot_df:
        blueprint = _TOT_DF_NM
    # Populate all levels of specificity in the NAICS tree:

    naics.pop_back(tree=data_tree, df_list=[_S_DF_NM])
    naics.pop_forward(tree=data_tree, df_list=[_S_DF_NM],
                      blueprint=blueprint, blue_tree=blue_tree)

    return data_tree
'''    
# Receives two dataframes and the column names that will be used to create a new dataframe
def calc_proportions(tot_corp_data, s_corp_data, columns):
    # Puts the dataframes into numpy arrays for easier data manipulation
    tot_corp = np.array(tot_corp_data)
    code = str(int(tot_corp[0][0]))
    old_array = np.array(s_corp_data[s_corp_data.INDY_CD == float(code[:1])])
    # Iterates over the arrays in total corp data
    for array in tot_corp[1:]:
        code = str(int(array[0]))
        # Uses the two digit naics codes as the denominator in the ratio calculations
        if(len(code) == 2):
            tot_data = array[1:]
            new_array = np.array(s_corp_data[s_corp_data.INDY_CD == float(code[:2])])
            old_array = np.concatenate((old_array, new_array))
        # Takes the finer-detailed data for the numerator of the ratio calculations  
        else:
            data = array[1:]
            # Calculates the ratio of finer-detailed to coarser-detailed data
            ratio = data / tot_data
            if(code[:2] in _CODE_RANGE):
                parent_code = _PARENTS[code[:2]]
            else:
                parent_code = code[:2]
            ratio = np.insert(ratio, 0, array[0] / float(parent_code))
            # Multiplies the ratio by the two digit naics code data and puts it in the finer-detailed industry
            new_array = np.array(s_corp_data[s_corp_data.INDY_CD == float(parent_code)]) * ratio
            old_array = np.concatenate((old_array, new_array)) 
    # Loads the array back into a dataframe with all the finer-detailed industries filled out                       
    s_corp_data = pd.DataFrame(old_array, index=np.arange(0,len(old_array)), columns = columns)     

    return s_corp_data
'''
def populate_tree(tree, tot_corp, s_corp):
    tot_corp = np.array(tot_corp)
    for ind_array in tot_corp:
        code = str(int(ind_array[0]))
        if(tree.codes.has_key(code)):
            index = tree.codes[code]
            tree.enum_inds[index].tot_corp = ind_array[1:]
            tree.enum_inds[index].tot_corp_cstock = np.array([ind_array[6]-ind_array[8],ind_array[9],ind_array[2]]) 

    s_corp = np.array(s_corp)
    for ind_array in s_corp:
        code = str(int(ind_array[0]))
        if(tree.codes.has_key(code)):
            index = tree.codes[code]
            tree.enum_inds[index].s_corp = ind_array[1:]
            tree.enum_inds[index].s_corp_cstock = np.array([ind_array[6]-ind_array[8],ind_array[9],ind_array[2]])
    return tree    

def calc_corp(tree):
    for ind in tree.enum_inds:
        if(ind.tot_corp[0] != 0 and ind.s_corp[0] != 0):
            ind.c_corp = ind.tot_corp - ind.s_corp
            ind.c_corp_cstock = ind.tot_corp_cstock - ind.s_corp_cstock
    return tree        

def calc_c_corp(data_tree, from_out=False,
                out_path=_C_CORP_OUT_PATH):
    """ This function calculates the soi c-corporation data based of the
    s and the aggregate corporation data.
    
    :param data_tree: The tree to read the data into.
    :param cols_dict: A dictionary mapping dataframe columns to the name of
           the column names in the input file
    :param blueprint: The key corresponding to a dataframe in a tree to be
           used as a "blueprint" for populating the df_list dataframes forward.
    :param blue_tree: A NAICS tree with the "blueprint" dataframe. The default
           is the original NAICS tree.
    :param from_out: Whether to read in the data from output.
    :param output_path: The path of the output file.
    """
    # If from_out, load the data tree from output:
    if from_out:
        data_tree = naics.load_tree_dfs(input_path=out_path, tree=data_tree)
        return data_tree
    For each industry, subtract the s-corporation data from the total to
    get the c-corporation data.
    for ind in data_tree.enum_inds:
        try:
            # Industry's total-corporation data:
            cur_tot = ind.data.dfs[_TOT_DF_NM]
        except KeyError:
            print "Total-Corp data not initialized when interpolating C-Corp."
        try:
            # Industry's S-corporation data:
            cur_s = ind.data.dfs[_S_DF_NM]
        except KeyError:
            print "S-Corp data not initialized when interpolating C-Corp."
        data_cols = cur_tot.columns.values.tolist()
        # Append C-corporation dataframe:
        ind.append_dfs((_C_DF_NM, pd.DataFrame(np.zeros((1,len(data_cols))),
                                                columns = data_cols)))
        # C-corporation data:
        ind.data.dfs[_C_DF_NM] = cur_tot - cur_s
    return data_tree
'''
