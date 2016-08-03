"""
Output formatting script (format_output.py):
-------------------------------------------------------------------------------
This module takes in numpy arrays of the B-Tax final and intermediate
calculations and then puts them into Pandas Dataframes in a format suitable
for tabular representation in the web app.
Last updated: 8/2/2016.

"""
# Import packages
import os.path
import sys
import pandas as pd
import numpy as np
import cPickle as pickle
from util import get_paths, read_from_egg


globals().update(get_paths())

def create_dfs(rho, metr, mettr, delta, z, by_asset):
    """Runner script that kicks off the calculations for B-Tax

        :param user_params: The user input for implementing reforms
        :type user_params: dictionary
        :returns: METR (by industry and asset) and METTR (by asset)
        :rtype: DataFrame
    """
    # format output for results

    if by_asset:
        numberOfRows = delta.shape[0]
        column_list = ['Asset Type', 'delta', 'z_c', 'z_c_d', 'z_c_e', 'z_nc',
           'rho_c', 'rho_c_d', 'rho_c_e', 'rho_nc', 'metr_c', 'metr_c_d', 'metr_c_e',
           'metr_nc', 'mettr_c', 'mettr_c_d', 'mettr_c_e', 'mettr_nc']
        # fills out columns for asset names and economic depreciation
        tax_depr = pd.read_csv(_TAX_DEPR)
        df = pd.DataFrame(index=np.arange(0, numberOfRows), columns=column_list)
        df['Asset Type'] = tax_depr['Asset Type']
        df['delta'] = delta
    else:
        ind_naics = pd.read_csv(_IND_NAICS)
        numberOfRows = len(ind_naics)
        column_list = ['Industry', 'NAICS', 'rho_c', 'rho_c_d', 'rho_c_e', 'rho_nc', 'metr_c', 'metr_c_d', 'metr_c_e',
            'metr_nc']
        # fills out columns for asset names and economic depreciation
        tax_depr = pd.read_csv(_TAX_DEPR)
        df = pd.DataFrame(index=np.arange(0, numberOfRows), columns=column_list)
        df['Industry'] = ind_naics['Industry']
        df['NAICS'] = ind_naics['NAICS']

    # fill out the output DataFrame for a mix, debt, and equity financing and
    # by tax treatment
    financing_list = ['', '_d', '_e']
    entity_list = ['_c', '_nc']
    for i in range(rho.shape[1]):
        for j in range(rho.shape[2]):
            df['z'+entity_list[j]+financing_list[i]] = z[:,i,j]
            df['rho'+entity_list[j]+financing_list[i]] = rho[:,i,j]
            df['metr'+entity_list[j]+financing_list[i]] = metr[:,i,0]
            df['mettr'+entity_list[j]+financing_list[i]] = mettr[:,i,j]

    # # creates a .pkl file of the output DataFrame
    # with open(os.path.join(_OUT_DIR, 'final_output.pkl'), 'wb') as handle:
    # pickle.dump(vars_by_asset, handle)

    return df




def CBO_compare(vars_by_asset):
    """Function to compare B-Tax output to CBO calcuations

        :param user_params: The user input for implementing reforms
        :type user_params: dictionary
        :returns: METR (by industry and asset) and METTR (by asset)
        :rtype: DataFrame
    """
    # read in CBO file
    CBO_data = pd.read_excel(os.path.join(_REF_DIR, 'effective_taxrates.xls'),
        sheetname='Full detail', header=1, skiprows=0, skip_footer=8)
    CBO_data.columns = [col.encode('ascii', 'ignore') for col in CBO_data]
    CBO_data.rename(columns = {'Top page (Rows 3-35): Equipment        Bottom page (Rows 36-62): All Other ':'Asset Type'}, inplace = True)
    CBO_data.to_csv(_OUT_DIR+'/CBO_data.csv',encoding='utf-8')

    # creates a DataFrame for the intersection of the CBO and our calculations (joined on the asset name)
    CBO_v_OSPC = vars_by_asset.merge(CBO_data,how='inner',on='Asset Type')

    OSPC_list = ['delta','z_c','z_c_d','z_c_e','z_nc','rho_c','rho_c_d','rho_c_e','rho_nc',
           'metr_c', 'metr_c_d', 'metr_c_e', 'mettr_c', 'mettr_c_d', 'mettr_c_e',
           'mettr_nc']
    CBO_list = ['Economic deprecia- tion rate []','Corporate: total [z(c)]',
          'Corporate: debt-financed [z(c,d)]', 'Corporate: equity-financed [z(c,e)]',
          'Non-corporate [z(n)]', 'Corporate: total [(c)]', 'Corporate: debt-financed [(c,d)]',
          'Corporate: equity-financed [(c,e)]', 'Non-corporate [(n)]', 'Corporate: total [ETR(c)]',
          'Corporate: debt-financed [ETR(c,d)]', 'Corporate: equity-financed [ETR(c,e)]',
          'Corporate: total [ETTR(c)]', 'Corporate: debt-financed [ETTR(c,d)]',
          'Corporate: equity-financed [ETTR(c,e)]', 'Non-corporate [ETTR(n)]']
    CBO_v_OSPC = CBO_v_OSPC.T.drop_duplicates().T

    # compares the CBO's calculations with our calculations and calculates the difference
    diff_list = [None] * len(OSPC_list)
    for i in xrange(0,len(OSPC_list)):
        CBO_v_OSPC[OSPC_list[i]+'_diff'] = CBO_v_OSPC[OSPC_list[i]] - CBO_v_OSPC[CBO_list[i]]
        diff_list[i] = OSPC_list[i]+'_diff'

    # prints the comparison data
    cols_to_print = ['Asset Type']+OSPC_list + CBO_list + diff_list
    CBO_v_OSPC[cols_to_print].to_csv(_OUT_DIR+'/CBO_v_OSPC.csv',encoding='utf-8')
