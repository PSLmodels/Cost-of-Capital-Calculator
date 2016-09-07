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

    # with new cross walk:
    """
    1) read in partner data - 12pa03
    2) read in detailed xwalk to go from string names for industries to SOI codes
    3) In xwalk, keep only "complete = 1" codes
    3) do an inner join of the two to keep only unique codes
    4) summ over the ind code from crosswalk- because some repeated, those rep more detailed classifcations summing to
    larger SOI category
    5) Now have partner assets at as detailed industry codes as we can get
    6) merge these partner codes to the soi_bea_ind_codes xwalk to get the sector, major, minor industry
        codes
            - need to do 3 merges, 1 for those id's at two digit, 1 for those at 3 and one for those at 6
    7) Take corp data and summ assets by major ind to create ratios for each of 195 inds
    id'd in corp data - ratio of assets for that ind as a share of all in that major ind

    8) merge these ratios to part data, will join on partner ind code to indy_cd from corp data
     and will have partner assets repeat for minor ind
    9) multiply ratios by assets - unless part already at minor ind- should have what want now

    could do at major industry
    - do have 811 at minor industry
    """
    # Opening data on depreciable fixed assets, inventories, and land for parnterhsips
    xwalk = pd.read_csv(_DETAIL_PART_CROSS_PATH)
    # keep only codes that help to identify complete industries
    xwalk = xwalk[xwalk['complete']==1]
    # read in partner data - partner assets
    df = format_excel(pd.read_excel(_AST_FILE, skiprows=2, skip_footer=6))
    # Cuts off the repeated columns so only the data for all partnerships remains
    df03 = df.T.groupby(sort=False,level=0).first().T
    # Fixing the index labels of the new dataframe
    df03.reset_index(inplace=True,drop=True)
    # Keep only variables of interest
    df03['Fixed Assets'] = (df03['Depreciable assets']-
                                         df03['Less:  Accumulated depreciation'])
    df03 = df03[['Item','Fixed Assets','Inventories','Land']]
    df03['Item'] = df03['Item'].str.strip()

     # partner data - income
    df01 = format_excel(pd.read_excel(_INC_FILE, skiprows=2, skip_footer=6))
    # Cuts off the repeated columns so only the data for all partnerships remains
    df01 = df01.T.groupby(sort=False,level=0).first().T
    # Fixing the index labels of the new dataframe
    df01.reset_index(inplace=True,drop=True)
    # Keep only variables of interest
    df01 = df01[['Item','Depreciation']]
    df01['Item'] = df01['Item'].str.strip()
    # merge two partner data sources together so that all variables together
    df03 = pd.merge(df03, df01, how='inner', left_on=['Item'],
      right_on=['Item'], left_index=False, right_index=False, sort=False,
      copy=True)

    # merge industry codes to partner data
    df03 = pd.merge(df03, xwalk, how='inner', left_on=['Item'],
      right_on=['Industry:'], left_index=False, right_index=False, sort=False,
      copy=True)
    df03.drop(['Item','Industry:','Codes:','Notes:','complete'], axis=1, inplace=True)

    # Sums together the repeated codes into one industry
    df03 = df03.groupby('INDY_CD',sort=False).sum()
    df03.reset_index(level=0, inplace=True)

    ## create ratios for minor industry assets using corporate data
    # read in crosswalk for bea and soi industry codes
    soi_bea_ind_codes = pd.read_csv(_SOI_BEA_CROSS, dtype={'bea_ind_code':str})
    soi_bea_ind_codes.drop('notes', axis=1, inplace=True)
    # drop one repeated minor ind code in crosswalk
    soi_bea_ind_codes.drop_duplicates(subset=['minor_code_alt'],inplace=True)

    # merge codes to partner data
    # likely better way to do this...
    df03_sector = df03[(df03['INDY_CD']>9) & (df03['INDY_CD']<100)]
    df03_major = df03[(df03['INDY_CD']>99) & (df03['INDY_CD']<1000)]
    df03_minor = df03[(df03['INDY_CD']>99999) & (df03['INDY_CD']<1000000)]
    sector_df = pd.merge(df03_sector, soi_bea_ind_codes, how='inner', left_on=['INDY_CD'],
      right_on=['sector_code'], left_index=False, right_index=False, sort=False,
      copy=True,indicator=True)
    major_df = pd.merge(df03_major, soi_bea_ind_codes, how='inner', left_on=['INDY_CD'],
      right_on=['major_code'], left_index=False, right_index=False, sort=False,
      copy=True,indicator=True)
    minor_df = pd.merge(df03_minor, soi_bea_ind_codes, how='inner', left_on=['INDY_CD'],
      right_on=['minor_code'], left_index=False, right_index=False, sort=False,
      copy=True,indicator=True)
    # df03 = pd.merge(df03, soi_bea_ind_codes, how='inner', left_on=['INDY_CD'],
    #                     right_on=['major_code'],left_index=False,
    #                     right_index=False, sort=False,suffixes=('_x', '_y'),
    #                     copy=True)
    part_data = sector_df.append([major_df,minor_df],ignore_index=True).copy().reset_index()
    part_data.drop(['bea_inv_name','bea_code','_merge'], axis=1, inplace=True)

    # merge codes to total corp data
    # inner join means that we keep only rows that match in both datasets
    # this should keep only unique soi minor industries
    # in total corp data - note that s corp data already unique by sector
    columns = ['Fixed Assets','Inventories','Land','Depreciation']
    s_corp = entity_dfs['s_corp'][['minor_code_alt']+columns]
    corp = pd.merge(s_corp, soi_bea_ind_codes, how='inner', left_on=['minor_code_alt'],
                        right_on=['minor_code_alt'],left_index=False,
                        right_index=False, sort=False,suffixes=('_x', '_y'),
                        copy=True)
    for var in columns :
        corp[var+'_ratio'] = corp.groupby(['major_code'])[var].apply(lambda x: x/float(x.sum()))

    corp.drop(['bea_inv_name','bea_code','sector_code',
               'minor_code']+columns, axis=1, inplace=True)

    # merge these ratios to the partner data
    part_data = pd.merge(part_data, corp, how='right', left_on=['minor_code_alt'],
                        right_on=['minor_code_alt'],left_index=False,
                        right_index=False, sort=False,suffixes=('_x', '_y'),
                        copy=True)

    # allocate capital based on ratios
    for var in columns :
        part_data.ix[part_data['minor_code_alt']>99999, var+'_ratio'] = 1.
        part_data[var] = part_data[var]*part_data[var+'_ratio']

    part_data.drop(map(lambda (x,y): x+y, zip(columns, ['_ratio']*len(columns))), axis=1, inplace=True)
    part_data.drop(['index','sector_code','major_code_x','minor_code',
                    'INDY_CD','major_code_y'],axis=1,inplace=True)

    df05 = format_excel(pd.read_excel(_TYP_FILE, skiprows=1, skip_footer=5))
    df05 = df05[['All partners','Corporate general partners','Corporate limited partners',
    'Individual general partners','Individual limited partners','Partnership general partners', 
    'Partnership limited partners','Tax-exempt organization general partners', 
    'Tax-exempt organization limited partners','Nominee and other general partners',
    'Nominee and other limited partners']]

    ### !!! Partner data has right industry breakouts, and ratio sum to 1 in ind,
    ## but totals not adding up to SOI controls. Not quite sure why. figure this out,
    # then attribute over partner types
    # then do same for sole props (looks like xwalk very close to detail partnership one - let's hope!)
    # then inventories and land can be split same for all entity types



    # # Read in data by partner type (gives allocation by partner type)
    # df05 = pd.read_csv(_TYP_FILE_CSV).T
    # typ_cross = pd.read_csv(_TYP_IN_CROSS_PATH)
    # df05 = soi.format_dataframe(df05, typ_cross)
    # df05 = pd.melt(df05, id_vars=['Item', 'Codes:'], value_vars=['Corporate general partners',
    #             'Corporate limited partners','Individual general partners',
    #             'Individual limited partners','Partnership general partners',
    #             'Partnership limited partners', 'Tax-exempt organization general partners',
    #             'Tax-exempt organization limited partners','Nominee and other general partners',
    #             'Nominee and other limited partners'],var_name='part_type',value_name='net_inc')
    #
    # # update partner type names to something shorter
    # # Not currnetly used except to count number of types
    # part_types = {'Corporate general partners':'corp_gen',
    #              'Corporate limited partners':'corp_lim',
    #              'Individual general partners':'indv_gen',
    #              'Individual limited partners':'indv_lim',
    #              'Partnership general partners':'prt_gen',
    #              'Partnership limited partners':'prt_lim',
    #              'Tax-exempt organization general partners':'tax_gen',
    #              'Tax-exempt organization limited partners':'tax_lim',
    #              'Nominee and other general partners':'nom_gen',
    #              'Nominee and other limited partners':'nom_lim'}
    #
    # # create sums by group
    # grouped = pd.DataFrame({'sum' : df05.groupby(['Codes:']).apply(abs_sum, 'net_inc')}).reset_index()
    # # merge grouped data back to original df
    # # One could make this more efficient - one line of code - with appropriate
    # # pandas methods using groupby and apply above
    # df05 = pd.merge(df05, grouped, how='left', left_on=['Codes:'],
    #   right_on=['Codes:'], left_index=False, right_index=False, sort=False,
    #   copy=True)
    # df05['inc_ratio'] = (df05['net_inc'].astype(float).abs()/df05['sum'].replace({ 0 : np.nan })).replace({np.nan:0})
    # df05 = df05[['Codes:','part_type','inc_ratio']]
    #
    # # add other sector codes for manufacturing
    # manu = df05[df05['Codes:'] == 31]
    # df_manu = (manu.append(manu)).reset_index()
    # df_manu.loc[:len(part_types), 'Codes:'] = 32
    # df_manu.loc[len(part_types):, 'Codes:'] = 33
    # df05 = df05.append(df_manu,ignore_index=True).reset_index().copy()
    #
    # # load crosswalk for soi and bea industry codes
    # soi_bea_ind_codes = pd.read_csv(_SOI_BEA_CROSS, dtype={'bea_ind_code':str})
    # soi_bea_ind_codes.drop('notes', axis=1, inplace=True)
    #
    # # Merge SOI codes to BEA data
    # df05 = pd.merge(soi_bea_ind_codes, df05, how='inner', left_on=['sector_code'],
    #   right_on=['Codes:'], left_index=False, right_index=False, sort=False,
    #   copy=True,indicator=True)
    # df05 = df05[df05['_merge']=='both']
    # df05.drop(['index','_merge','level_0','Codes:'], axis=1, inplace=True)
    #
    # # merge partner type ratios with partner asset data
    # # likely better way to do this...
    # df03_sector = df03[(df03['Codes:']>9) & (df03['Codes:']<100)]
    # df03_major = df03[(df03['Codes:']>99) & (df03['Codes:']<1000)]
    # df03_minor = df03[(df03['Codes:']>99999) & (df03['Codes:']<1000000)]
    # sector_df = pd.merge(df03_sector, df05, how='inner', left_on=['Codes:'],
    #   right_on=['sector_code'], left_index=False, right_index=False, sort=False,
    #   copy=True,indicator=True)
    # major_df = pd.merge(df03_major, df05, how='inner', left_on=['Codes:'],
    #   right_on=['major_code'], left_index=False, right_index=False, sort=False,
    #   copy=True,indicator=True)
    # minor_df = pd.merge(df03_minor, df05, how='inner', left_on=['Codes:'],
    #   right_on=['minor_code'], left_index=False, right_index=False, sort=False,
    #   copy=True,indicator=True)
    #
    # part_assets = sector_df.append([major_df,minor_df],ignore_index=True).copy().reset_index()
    # part_assets.drop(['index','_merge'], axis=1, inplace=True)
    #
    # part_assets['Fixed Assets_type'] = part_assets['Fixed Assets']*part_assets['inc_ratio']
    # part_assets['Inventories_type'] = part_assets['Inventories']*part_assets['inc_ratio']
    # part_assets['Land_type'] = part_assets['Land']*part_assets['inc_ratio']
    #
    # # drop repeats at level of industry codes- this best partner data can be identified at
    # part_assets.drop_duplicates(subset=['Codes:','part_type'],inplace=True)
    #
    # # sum at industry-partner type level
    # part_data = pd.DataFrame({'Fixed Assets' :
    #                           part_assets.groupby(['Codes:'])['Fixed Assets_type'].sum()}).reset_index()
    # part_data['Inventories'] = pd.DataFrame({'Inventories' :
    #                           part_assets.groupby(['Codes:'])['Inventories_type'].sum()}).reset_index()['Inventories']
    # part_data['Land'] = pd.DataFrame({'Land' :
    #                           part_assets.groupby(['Codes:'])['Land_type'].sum()}).reset_index()['Land']
    # part_data['inc_ratio'] = pd.DataFrame({'inc_ratio' :
    #                           part_assets.groupby(['Codes:'])['inc_ratio'].sum()}).reset_index()['inc_ratio']
    #
    # data = {'part_data':part_data}
    #
    # part_data.to_csv('TestDF2.csv',encoding='utf-8')
    # quit()
    #  # merge codes to corp data
    # all_corp = pd.merge(all_corp, soi_ind_codes, how='inner', left_on=['INDY_CD'], right_on=['minor_code_alt'],
    #   left_index=False, right_index=False, sort=False,
    #   suffixes=('_x', '_y'), copy=True, indicator=True)
    # # keep only rows that match in both datasets - this should keep only unique soi minor industries
    # all_corp = all_corp.drop(all_corp[all_corp['_merge']!='both' ].index)
    #
    # corp_ratios = all_corp[['INDY_CD','minor_code_alt','minor_code','major_code','sector_code']]
    # for var in corp_data_variables_of_interest :
    #     corp_ratios[var+'_ratio'] = all_corp.groupby(['sector_code'])[var].apply(lambda x: x/float(x.sum()))

    part_data = {'part_data': part_data}


    return part_data

def abs_sum(group, avg_name):
    """
    Computes the sum of abs values
    """
    d = group[avg_name]
    return (np.absolute(d)).sum()

def format_excel(df):

    for i, element in enumerate(df.iloc[0,:]):
        j=1
        while isinstance(element, float):
            element = df.iloc[j,:][i]
            j+=1
        df.iloc[0,:][i] = element.replace('\n', ' ').replace('  ', ' ')
    
    df.dropna(inplace=True)
    df = df.T
    column_names = df.iloc[0,:].tolist()
    column_names = map(lambda x : x.encode('ascii','ignore').lstrip().rstrip(), column_names)
    df.columns = column_names
    df = df.drop(df.index[[0,len(df)-1]])
    df = df.fillna(0)
    df = df.replace('[d]', 0)
    df = df.replace('[2]  ', 0)
    df.reset_index(inplace=True, drop=True)
    df.iloc[:,1:] = df.iloc[:,1:] * _AST_FILE_FCTR

    return df
