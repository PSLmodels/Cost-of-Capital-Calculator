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
    df = format_stuff(pd.read_excel(_AST_FILE, skiprows=2, skip_footer=6), ast_cross)
    # Cuts off the repeated columns so only the total data remains
    df03 = df.T.groupby(sort=False,level=0).first().T
    # Sums together the repeated codes into one industry
    df03 = df03.groupby('Codes:',sort=False).sum()
    # Fixing the index labels of the new dataframe
    df03.reset_index(inplace=True)
    # Keep only variables of interest
    df03['Fixed Assets'] = (df03['Depreciable assets']-
                                         df03['Less:  Accumulated depreciation'])
    df03 = df03[['Codes:','Item','Fixed Assets','Inventories','Land']]


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
    grouped = pd.DataFrame({'sum' : df05.groupby(['Codes:']).apply(abs_sum, 'net_inc')}).reset_index()
    # merge grouped data back to original df
    # One could make this more efficient - one line of code - with appropriate
    # pandas methods using groupby and apply above
    df05 = pd.merge(df05, grouped, how='left', left_on=['Codes:'],
      right_on=['Codes:'], left_index=False, right_index=False, sort=False,
      copy=True)
    df05['inc_ratio'] = (df05['net_inc'].astype(float).abs()/df05['sum'].replace({ 0 : np.nan })).replace({np.nan:0})
    df05 = df05[['Codes:','part_type','inc_ratio']]

    # add other sector codes for manufacturing
    manu = df05[df05['Codes:'] == 31]
    df_manu = (manu.append(manu)).reset_index()
    df_manu.loc[:len(part_types), 'Codes:'] = 32
    df_manu.loc[len(part_types):, 'Codes:'] = 33
    df05 = df05.append(df_manu,ignore_index=True).reset_index().copy()

    # load crosswalk for soi and bea industry codes
    soi_bea_ind_codes = pd.read_csv(_SOI_BEA_CROSS, dtype={'bea_ind_code':str})
    soi_bea_ind_codes.drop('notes', axis=1, inplace=True)

    # Merge SOI codes to BEA data
    df05 = pd.merge(soi_bea_ind_codes, df05, how='inner', left_on=['sector_code'],
      right_on=['Codes:'], left_index=False, right_index=False, sort=False,
      copy=True,indicator=True)
    df05 = df05[df05['_merge']=='both']
    df05.drop(['index','_merge','level_0','Codes:'], axis=1, inplace=True)

    # merge partner type ratios with partner asset data
    # likely better way to do this...
    df03_sector = df03[(df03['Codes:']>9) & (df03['Codes:']<100)]
    df03_major = df03[(df03['Codes:']>99) & (df03['Codes:']<1000)]
    df03_minor = df03[(df03['Codes:']>99999) & (df03['Codes:']<1000000)]
    sector_df = pd.merge(df03_sector, df05, how='inner', left_on=['Codes:'],
      right_on=['sector_code'], left_index=False, right_index=False, sort=False,
      copy=True,indicator=True)
    major_df = pd.merge(df03_major, df05, how='inner', left_on=['Codes:'],
      right_on=['major_code'], left_index=False, right_index=False, sort=False,
      copy=True,indicator=True)
    minor_df = pd.merge(df03_minor, df05, how='inner', left_on=['Codes:'],
      right_on=['minor_code'], left_index=False, right_index=False, sort=False,
      copy=True,indicator=True)

    part_assets = sector_df.append([major_df,minor_df],ignore_index=True).copy().reset_index()
    part_assets.drop(['index','_merge'], axis=1, inplace=True)

    part_assets['Fixed Assets_type'] = part_assets['Fixed Assets']*part_assets['inc_ratio']
    part_assets['Inventories_type'] = part_assets['Inventories']*part_assets['inc_ratio']
    part_assets['Land_type'] = part_assets['Land']*part_assets['inc_ratio']

    # drop repeats at level of industry codes- this best partner data can be identified at
    part_assets.drop_duplicates(subset=['Codes:','part_type'],inplace=True)

    part_assets.to_csv('TestDF.csv',encoding='utf-8')


    # sum at industry-partner type level
    part_data = pd.DataFrame({'Fixed Assets' :
                              part_assets.groupby(['Codes:'])['Fixed Assets_type'].sum()}).reset_index()
    part_data['Inventories'] = pd.DataFrame({'Inventories' :
                              part_assets.groupby(['Codes:'])['Inventories_type'].sum()}).reset_index()['Inventories']
    part_data['Land'] = pd.DataFrame({'Land' :
                              part_assets.groupby(['Codes:'])['Land_type'].sum()}).reset_index()['Land']
    part_data['inc_ratio'] = pd.DataFrame({'inc_ratio' :
                              part_assets.groupby(['Codes:'])['inc_ratio'].sum()}).reset_index()['inc_ratio']

    data = {'part_data':part_data}

    part_data.to_csv('TestDF2.csv',encoding='utf-8')
    quit()
     # merge codes to corp data
    all_corp = pd.merge(all_corp, soi_ind_codes, how='inner', left_on=['INDY_CD'], right_on=['minor_code_alt'],
      left_index=False, right_index=False, sort=False,
      suffixes=('_x', '_y'), copy=True, indicator=True)
    # keep only rows that match in both datasets - this should keep only unique soi minor industries
    all_corp = all_corp.drop(all_corp[all_corp['_merge']!='both' ].index)

    corp_ratios = all_corp[['INDY_CD','minor_code_alt','minor_code','major_code','sector_code']]
    for var in corp_data_variables_of_interest :
        corp_ratios[var+'_ratio'] = all_corp.groupby(['sector_code'])[var].apply(lambda x: x/float(x.sum()))

    return data

def abs_sum(group, avg_name):
    """
    Computes the sum of abs values
    """
    d = group[avg_name]
    return (np.absolute(d)).sum()

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
