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
                    ('paid_capital_surplus', 'PD_CAP_SRPLS')
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
    # Opening the soi S-corporate data file:
    try:
        s_corp_data = pd.read_csv(_S_CORP_IN_PATH).fillna(0)
    except IOError:
        print "IOError: S-Corp soi data file not found."
        raise
    # Opening the soi Total-corporate data file:
    try:
        tot_corp_data = pd.read_csv(_TOT_CORP_IN_PATH).fillna(0)
    except IOError:
        print "IOError: S-Corp soi data file not found."
        raise

    # Formatting the list of columns that will be used to trim the dataframe for the necessary data
    columns = cols_dict.values()
    columns.remove('')
    columns.insert(0,'INDY_CD')
    # Selecting out only the total industry values for the s corp data
    s_corp_data = s_corp_data[(s_corp_data.AC == 1)]
    s_corp_data = s_corp_data[columns] * _CORP_FILE_FCTR
    s_corp_data['INDY_CD'] = s_corp_data['INDY_CD'] / _CORP_FILE_FCTR
    # Repeating the same process of trimming and selecting on the total corp data
    tot_corp_data = tot_corp_data[(tot_corp_data.AC == 1)]
    tot_corp_data = tot_corp_data[columns] * _CORP_FILE_FCTR
    tot_corp_data['INDY_CD'] = tot_corp_data['INDY_CD'] / _CORP_FILE_FCTR
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
    cstock = ['INDY_CD', 'Fixed Assets', 'INVNTRY', 'LAND']
    # Calculates the amount of fixed assets: Depreciables assets - accumulated depreciated
    tot_corp_data['Fixed Assets'] = tot_corp_data['DPRCBL_ASSTS'] - tot_corp_data['ACCUM_DPR']
    s_corp_data['Fixed Assets'] = s_corp_data['DPRCBL_ASSTS'] - s_corp_data['ACCUM_DPR']
    c_corp_data['Fixed Assets'] = c_corp_data['DPRCBL_ASSTS'] - c_corp_data['ACCUM_DPR']
    # Trims off the extra columns in the corporate dataframes
    tot_corp_data = tot_corp_data[cstock]
    s_corp_data = s_corp_data[cstock]
    c_corp_data = c_corp_data[cstock]
    # Make column names consistent with other dataframes
    tot_corp_data.rename(columns={"INVNTRY": "Inventories","LAND":"Land"},inplace=True)
    s_corp_data.rename(columns={"INVNTRY": "Inventories","LAND":"Land"},inplace=True)
    c_corp_data.rename(columns={"INVNTRY": "Inventories","LAND":"Land"},inplace=True)
    # Changes the column name for the codes of each dataframe
    tot_corp_data.columns.values[0] = 'Codes:'
    s_corp_data.columns.values[0] = 'Codes:'
    c_corp_data.columns.values[0] = 'Codes:'
    # Reformats the indices of the total corp data so it can be indexed correctly
    tot_corp_data.index = np.arange(0,len(tot_corp_data))
    # Creates a dictionary of a sector : dataframe
    corp_data = {'tot_corp': tot_corp_data, 'c_corp': c_corp_data, 's_corp': s_corp_data}

    return corp_data

def calc_proportions(tot_corp_data, s_corp_data, columns):
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
