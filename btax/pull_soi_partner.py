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


from btax.util import get_paths
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
    import btax.soi_processing as soi

    # Opening data on depreciable fixed assets, inventories, and land for parnterhsips
    # with net profits:
    ast_cross = pd.read_csv(_AST_IN_CROSS_PATH)
    #I am cheating here, reading in a created file with only profitable partnerships
    # data - the format_stuff() losses these when trying to read the raw file
    df = format_stuff(pd.read_excel(_AST_profit_FILE, skiprows=2, skip_footer=6), ast_cross)
    # Cuts off the repeated columns so only the total data remains
    df03 = df.T.groupby(sort=False,level=0).first().T
    # Sums together the repeated codes into one industry
    df03 = df03.groupby('Codes:',sort=False).sum()
    # Fixing the index labels of the new dataframe
    df03.reset_index(inplace=True)
    # Cuts off the total data so only the totals for partnerships with net income remain
    # This doesn't seem to do what it intends to do
    df03_gain = df03.T.groupby(sort=False,level=0).last().T
    # Keep only variables of interest
    df03_gain['Fixed Assets'] = (df03_gain['Depreciable assets']-
                                         df03_gain['Less:  Accumulated depreciation'])
    df03_gain = df03_gain[['Codes:','Item','Fixed Assets','Inventories','Land']]


    # Opening data on depreciable fixed assets, inventories, and land for parnterhsips
    # with net profits:
    ast_cross = pd.read_csv(_AST_IN_CROSS_PATH)
    #I am cheating here, reading in a created file with only profitable partnerships
    # data - the format_stuff() losses these when trying to read the raw file
    df = format_stuff(pd.read_excel(_AST_FILE, skiprows=2, skip_footer=6), ast_cross)
    # Cuts off the repeated columns so only the total data remains
    df03 = df.T.groupby(sort=False,level=0).first().T
    # Sums together the repeated codes into one industry
    df03 = df03.groupby('Codes:',sort=False).sum()
    # Fixing the index labels of the new dataframe
    df03.reset_index(inplace=True)
    # keep only variables of interest
    df03['Fixed Assets'] = (df03['Depreciable assets']-
                                         df03['Less:  Accumulated depreciation'])
    df03 = df03[['Codes:','Item','Fixed Assets','Inventories','Land']]


    # merge those with profits with those without
    df03_loss = pd.merge(df03, df03_gain, how='inner', on=['Codes:'],
      left_index=False, right_index=False, sort=False, suffixes=('_all','_profit'),
      copy=True)
    df03_loss['Fixed Assets'] = df03_loss['Fixed Assets_all'] - df03_loss['Fixed Assets_profit']
    df03_loss['Inventories'] = df03_loss['Inventories_all'] - df03_loss['Inventories_profit']
    df03_loss['Land'] = df03_loss['Land_all'] - df03_loss['Land_profit']
    df03_loss['Item'] = df03_loss['Item_all']
    df03_loss['gain'] = False
    df03_loss = df03_loss[['Codes:','Item','Fixed Assets','Inventories','Land','gain']]

    # add gain boolean to dataframe of profitable partnerships
    df03_gain['gain'] = True

    # append data by loss and gain together
    df03_all = df03_gain.append(df03_loss,ignore_index=True)

    # Read in data by partner type (gives allocation by partner type)
    df05 = pd.read_csv(_TYP_FILE_CSV).T
    typ_cross = pd.read_csv(_TYP_IN_CROSS_PATH)
    df05 = soi.format_dataframe(df05, typ_cross)
    df05 = pd.melt(df05, id_vars=['Item', 'Codes:'], value_vars=['Corporate general partners',
                'Corporate limited partners','Individual general partners',
                'Individual limited partners','Partnership general partners',
                'Partnership limited partners', 'Tax-exempt organization general partners',
                'Tax-exempt organization limited partners','Nominee and other general partners',
                'Nominee and other limited partners'],var_name='part_type',value_name='net_inc')
    # create boolean for net gain or loss to partner type
    df05['gain'] = df05['net_inc'] > 0

    # update partner type names to something shorter
    # Not currnetly used except to count number of types
    part_types = {'Corporate general partners':'corp_gen',
                 'Corporate limited partners':'corp_lim',
                 'Individual general partners':'indv_gen',
                 'Individual limited partners':'indv_lim',
                 'Partnership general partners':'prt_gen',
                 'Partnership limited partners':'prt_lim',
                 'Tax-exempt organization general partners':'tax_gen',
                 'Tax-exempt organization limited partners':'tax_lim',
                 'Nominee and other general partners':'nom_gen',
                 'Nominee and other limited partners':'nom_lim'}

    # create sums by group
    grouped = pd.DataFrame({'sum' : df05.groupby(['Codes:','gain'])['net_inc'].sum()}).reset_index()
    # merge grouped data back to original df
    # One could make this more efficient - one line of code - with appropriate
    # pandas methods using groupby and apply above
    df05 = pd.merge(df05, grouped, how='left', left_on=['Codes:', 'gain'],
      right_on=['Codes:', 'gain'], left_index=False, right_index=False, sort=False,
      copy=True)
    df05['inc_ratio'] = (df05['net_inc']/df05['sum'].replace({ 0 : np.nan })).replace({np.nan:0})
    df05 = df05[['Codes:','part_type','gain','inc_ratio']]

    # add other sector codes for manufacturing
    manu = df05[df05['Codes:'] == 31]
    df_manu = (manu.append(manu)).reset_index()
    df_manu.loc[:len(part_types), 'Codes:'] = 32
    df_manu.loc[len(part_types):, 'Codes:'] = 33
    df05 = df05.append(df_manu,ignore_index=True).reset_index().copy()

    # df05_all_ind = df05[len(df05['Codes:']==1)]
    # df05_sector = df05[len(df05['Codes:']==2)]
    # df05_major = df05[len(df05['Codes:']==3)]
    # df05_minor = df05[len(df05['Codes:']==6)] # NEED to go over partnership crosswalks - why some 4 and 5 digit codes????
    #

    # merge with cross walk for more specific industry categories
    soi_bea_ind_codes = pd.read_csv(_SOI_BEA_CROSS, dtype={'bea_ind_code':str})
    soi_bea_ind_codes.drop('notes', axis=1, inplace=True)

    # Merge SOI codes to BEA data
    df05 = pd.merge(soi_bea_ind_codes, df05, how='outer', left_on=['sector_code'],
      right_on=['Codes:'], left_index=False, right_index=False, sort=False,
      copy=True,indicator=True)
    df05 = df05[df05['_merge']=='both']

    ## Want to do a series of these merges - after match on sector_code, match on major industry
    # if major industry identified in data, then do for minor_industry - only replacing what
    # is in dataframe w
    ## E.g.:
    # df05_sector = pd.merge(soi_bea_ind_codes, df05_sector, how='outer', left_on=['sector_code'],
    #   right_on=['Codes:'], left_index=False, right_index=False, sort=False,
    #   copy=True)
    # df05_major = pd.merge(soi_bea_ind_codes, df05_major, how='outer', left_on=['major_code'],
    #   right_on=['Codes:'], left_index=False, right_index=False, sort=False,
    #   copy=True)
    # df05_minor = pd.merge(soi_bea_ind_codes, df05_minor, how='outer', left_on=['minor_code'],
    #   right_on=['Codes:'], left_index=False, right_index=False, sort=False,
    #   copy=True)
    # df05_final = (df05_sector.append((df05_major,df05_minor,df_all_ind),ignore_index=True)).copy().reset_index()

    df05.drop(['index','_merge'], axis=1, inplace=True)


    # merge partner type ratios with partner asset data by income and loss
    sector_df = pd.merge(df03_all, df05, how='left', left_on=['Codes:','gain'],
      right_on=['sector_code','gain'], left_index=False, right_index=False, sort=False,
      copy=True,indicator=True)
    major_df = pd.merge(df03_all, df05, how='left', left_on=['Codes:','gain'],
      right_on=['major_code','gain'], left_index=False, right_index=False, sort=False,
      copy=True,indicator=True)
    minor_df = pd.merge(df03_all, df05, how='left', left_on=['Codes:','gain'],
      right_on=['minor_code','gain'], left_index=False, right_index=False, sort=False,
      copy=True,indicator=True)

    part_assets = sector_df.append([major_df,minor_df],ignore_index=True).copy().reset_index()
    part_assets = part_assets[part_assets['_merge']=='both']

    part_assets['Fixed Assets_type'] = part_assets['Fixed Assets']*part_assets['inc_ratio']
    part_assets['Inventories_type'] = part_assets['Inventories']*part_assets['inc_ratio']
    part_assets['Land_type'] = part_assets['Land']*part_assets['inc_ratio']

    part_assets.rename(columns={'Codes:_x':'Codes:'},inplace=True)
    # sum over gain/loss to get at industry-partner type level
    # part_assets.groupby(['Codes:','part_type'])['Fixed Assets_type','Inventories_type',
    #                            'Land_type'].sum()
    part_data = pd.DataFrame({'Fixed Assets' :
                              part_assets.groupby(['Codes:','part_type'])['Fixed Assets_type'].sum()}).reset_index()
    part_data['Inventories'] = pd.DataFrame({'Inventories' :
                              part_assets.groupby(['Codes:','part_type'])['Inventories_type'].sum()}).reset_index()['Inventories']
    part_data['Land'] = pd.DataFrame({'Land' :
                              part_assets.groupby(['Codes:','part_type'])['Land_type'].sum()}).reset_index()['Land']

    # part_assets = part_assets[['Codes:','Fixed Assets_type','Inventories_type',
    #                            'Land_type',]]
    # part_assets.rename(columns={'Fixed Assets_type':'Fixed Assets',
    #                             'Inventories_type':'Inventories',
    #                            'Land_type':'Land'},inplace=True)

    part_data.to_csv('testDF.csv',encoding='utf-8')
    quit()

    # want to do some heirarchical merge as above

    codes = pd.read_csv(_SOI_CODES)
    # Transfers the total data to a numpy array
    tot_data = np.array(df1)
    # Reads in the income information (profit/loss) and stores it in a dataframe
    #inc_loss = pd.read_csv(_INC_FILE).T
    # Loads the crosswalk and formats the dataframe
    inc_cross = pd.read_csv(_INC_IN_CROSS_PATH)
    #inc_loss = soi.format_dataframe(inc_loss, inc_cross)
    inc_loss = format_stuff(pd.read_excel(_INC_FILE, skiprows=2, skip_footer=6), inc_cross)
    #p2 = format_stuff(pd.read_excel(_AST_FILE, skiprows=2, skip_footer=6), ast_cross)
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
    prt_types = pd.read_csv(_TYP_FILE_CSV).T
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
