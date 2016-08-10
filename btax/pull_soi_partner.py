"""
SOI Partner Data (pull_soi_partner.py):
-------------------------------------------------------------------------------
Module that handles reading in the soi partner data. Contains one long script that loads in the capital stock,
income and entity information. Using the different asset and income information (ratios of assets to income),
data can be allocated to all the industries in the different partner entities.
Last updated: 7/26/2016.

"""
# Packages:
import os.path
import numpy as np
import pandas as pd
import xlrd

import soi_processing as soi
from util import get_paths
globals().update(get_paths())

# Constants
_AST_FILE_FCTR = 10**3
_SHAPE = (131,4)
_CODE_RANGE = ['32', '33', '45', '49']
_PARENTS = {'32':'31','33':'31','45':'44','49':'48'}

def load_partner_data(entity_dfs):
    """Reads in the partner data and creates new dataframes for each partner type and stores them in the soi dictionary

        :param entity_dfs: Contains all the soi data by entity type
        :type entity_dfs: dictionary
        :returns: The soi dictionary updated with the partner dataframe
        :rtype: dictionary
    """
    # Opening data on depreciable fixed assets, inventories, and land:
    df = pd.read_csv(_AST_FILE).T
    # Opening the crosswalk for the asset data
    ast_cross = pd.read_csv(_AST_IN_CROSS_PATH)
    # Formatting the dataframe so each row represents an industry and each column an asset value
    df = soi.format_dataframe(df, ast_cross)
    # Cuts off the repeated columns so only the total data remains
    df1 = df.T.groupby(sort=False,level=0).first().T
    # Sums together the repeated codes into one industry
    df1 = df1.groupby('Codes:',sort=False).sum()
    # Fixing the index labels of the new dataframe
    codes = df1.index.tolist()
    df1.insert(0,'Codes:', codes)
    df1.index = np.arange(0,len(df1))
    # Cuts off the total data so only the partners with net income remain
    df2 = df.T.groupby(sort=False,level=0).last().T
    # Sums together the repeated codes once again and fixes the indices
    df2 = df2.groupby('Codes:',sort=False).sum()
    codes = df2.index.tolist()
    df2.insert(0,'Codes:', codes)
    df2.index = np.arange(0,len(df2))
    codes = pd.read_csv(_SOI_CODES)
    # Transfers the total data to a numpy array
    tot_data = np.array(df1)
    # Reads in the income information (profit/loss) and stores it in a dataframe
    inc_loss = pd.read_csv(_INC_FILE).T
    # Loads the crosswalk and formats the dataframe
    inc_cross = pd.read_csv(_INC_IN_CROSS_PATH)
    inc_loss = soi.format_dataframe(inc_loss, inc_cross)
    p1 = format_stuff(pd.read_excel(_XLS_FILE_1, skiprows=2, skip_footer=5), inc_cross)
    p2 = format_stuff(pd.read_excel(_XLS_FILE_2, skiprows=2, skip_footer=5), ast_cross)
    # Creates a list of columns that will be used to trim the data
    col_list = ['Item', 'Codes:', 'Net income', 'Loss']

    # Removes the duplicate columns and leaves only the income and loss data
    inc_loss = inc_loss.T.groupby(sort=False,level=0).last().T[col_list]
    inc_loss = inc_loss.groupby('Codes:',sort=False).sum()
    codes = inc_loss.index.tolist()
    inc_loss.insert(0,'Codes:', codes)
    inc_loss.index = np.arange(0,len(inc_loss))
    inc_loss = np.array(inc_loss)
    # Subtracts the accumulated depreciation from the depreciable assets for the profitable partners
    prof_fa_data = np.array(df2['Depreciable assets']-df2['Less:  Accumulated depreciation'])
    # Adds in the inventory data for profitable partners
    prof_inv_data = np.array(df2['Inventories'])
    # Adds on the land data for profitable partners
    prof_land_data = np.array(df2['Land'])
    # Subtracts the fixed assets for profitable partners from the total fixed assets to find capital stock for partners in the red
    loss_fa_data = np.array((df1['Depreciable assets']-df1['Less:  Accumulated depreciation']-
        df2['Depreciable assets']+df2['Less:  Accumulated depreciation']))
    loss_inv_data = np.array(df1['Inventories'] - prof_inv_data)
    loss_land_data = np.array(df1['Land'] - prof_land_data)

    # Creates empty arrays that will be modified in the for loop to initialize the capital stock and ratio of income / capital stock
    prt_cstock = np.zeros(_SHAPE)
    loss_ratios = np.zeros(_SHAPE)
    prof_ratios = np.zeros(_SHAPE)
    for i in xrange(0,len(tot_data)):
        # Pulls out the SOI code, FA, Inventories, and Land data from the total partner data
        prt_cstock[i] = np.array([int(tot_data[i][0]),float(tot_data[i][16])- float(tot_data[i][17]),
             float(tot_data[i][9]), float(tot_data[i][20])])
        # If the loss is not zero then store the ratios of Loss / FA, Loss / Inv, Loss / Land
        if(inc_loss[i][3] != 0):
            loss_ratios[i] = np.array([int(tot_data[i][0]),loss_fa_data[i] / float(inc_loss[i][3]),
                loss_inv_data[i] / float(inc_loss[i][3]), loss_land_data[i] / float(inc_loss[i][3])])
        # If the net income is not zero then store the Income / Capital stock ratios
        if(inc_loss[i][2] != 0):
            prof_ratios[i] = np.array([int(tot_data[i][0]), prof_fa_data[i] / float(inc_loss[i][2]),
                prof_inv_data[i] / float(inc_loss[i][2]),prof_land_data[i] / float(inc_loss[i][2])])

    # Load and format the income data, which is separated by the different partner types
    prt_types = pd.read_csv(_TYP_FILE).T
    typ_cross = pd.read_csv(_TYP_IN_CROSS_PATH)
    prt_types = soi.format_dataframe(prt_types, typ_cross)
    prt_data = np.array(prt_types)
    # Creates a dictionary {soi code : index} that wil be used to access the correct industries in the df
    index = {}
    for i in xrange(0,len(codes)):
        index[codes[i]] = i

    capital_stock = []
    code_dict = {}
    j = 0
    # For each array (contains a list of income values) in the partner data
    for array in prt_data:
        # Creates unitialized lists for the capital stock
        fixed_assets = []
        land_data = []
        inventories = []
        code = int(array[1])
        code_dict[code] = j
        if(index.has_key(code)):
            i = index[code]
            # For each element in the list of partner data
            for element in array[2:]:
                # If the overall income was positive then mulitply the capital stock by the profit ratios
                if(element > 0):
                    fixed_asset = prof_ratios[i][0] * float(element)
                    invs = prof_ratios[i][1] * float(element)
                    land = prof_ratios[i][2] * float(element)
                # If the overall income was negative then multiply by the loss ratios (absolute value taken)
                else:
                    fixed_asset = prof_ratios[i][0] * abs(float(element))
                    invs = prof_ratios[i][1] * abs(float(element))
                    land = prof_ratios[i][2] * abs(float(element))
                # Adds all the new values to the capital stock lists
                fixed_assets.append(fixed_asset)
                land_data.append(land)
                inventories.append(invs)
            # Stores all the capital stock lists, along with the SOI code, in one list
            capital_stock.append([code, np.array(fixed_assets), np.array(land_data), np.array(inventories)])
            j += 1
    # Fills in the missing values by taking the ratio of finer industry to broader industry multiplied by broader income values
    prt_cap_stock = []
    for ind in prt_cstock:
        code1 = int(ind[0])
        if(code_dict.has_key(code1)):
            # If the capital stock has already has already been calculated add it to the list
            prt_cap_stock.append(capital_stock[code_dict[code1]])
        else:
            # Finds the corresponding 'parent' industry
            code2 = int(str(code1)[:2])
            if(str(code2) in _CODE_RANGE):
                code2 = int(_PARENTS[str(code2)])
            # Uses the dictionary to find the index of that industry
            index1 = index[code2]
            # Performs the calculation as outlined at the beginning of the for loop and adds it to the list
            prt_cap_stock.append([code1, capital_stock[code_dict[code2]][1] * ind[1] / prt_cstock[index1][1],
            capital_stock[code_dict[code2]][2] * ind[2] / prt_cstock[index1][2],
            capital_stock[code_dict[code2]][3] * ind[3] / prt_cstock[index1][3]])

    # Creates a list of all the different partner types to be used for keys in the final dictionary
    prt_types = ['corp_gen', 'corp_lim', 'indv_gen', 'indv_lim', 'prt_gen', 'prt_lim', 'tax_gen', 'tax_lim', 'nom_gen', 'nom_lim']

    prt_data = {}
    baseline_codes = pd.read_csv(_SOI_CODES)
    # Uses the corporate codes as a baseline to fill in missing values, also converts the lists to dataframes
    for i in xrange(0,len(prt_types)):
        ind_capital = []
        # Organizes the data by partner type instead of industry
        for ind in prt_cap_stock:
            ind_capital.append([ind[0], ind[1][i+1], ind[2][i+1], ind[3][i+1]])
        # Stores the new partner type lists in a dataframe
        df = pd.DataFrame(ind_capital, index = np.arange(0,len(ind_capital)), columns = ['Codes:', 'FA', 'Inv', 'Land'])
        # Performs a union to add in the corporate codes that are missing
        df = baseline_codes.merge(df, how = 'outer').fillna(0)
        # Uses an intersection to remove any data that only exists for partners
        df = baseline_codes.merge(df, how = 'inner')
        # Uses the corporate ratio of capital stock to further fill in missing information
        df = soi.interpolate_data(entity_dfs, df)
        # Adds the dataframe to the dictionary
        prt_data[prt_types[i]] = df

    return prt_data

def format_stuff(p1, cross):
    for i in xrange(0,len(p1.iloc[0,:])):
        element = p1.iloc[0,:][i]
        if isinstance(element, float):
            element = p1.iloc[1,:][i]
            if(isinstance(element,float)):
                element = p1.iloc[2,:][i]
        p1.iloc[0,:][i] = element.replace('\n', ' ').replace('  ', ' ')
    p1 = p1.drop(p1.index[[1,2,3,4,5,6,7,8,12]])
    p1 = p1.T
    column_names = p1.iloc[0,:].tolist()
    for i in xrange(0,len(column_names)):
        column_names[i] = column_names[i].encode('ascii','ignore').lstrip().rstrip()
    p1.columns = column_names
    p1 = p1.drop(p1.index[[0,136]])
    p1 = p1.fillna(0)
    p1 = p1.replace('[2]  ', 0)
    p1.index = np.arange(0,len(p1))
    info = p1['Item']
    p1 = p1 * _AST_FILE_FCTR
    p1['Item'] = info
    p1.insert(1,'Codes:',cross['Codes:'])

    return p1
