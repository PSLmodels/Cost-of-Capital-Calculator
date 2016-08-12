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
    CBO_data['Asset Type'] = CBO_data['Asset Type'].str.strip()

    # creates a DataFrame for the intersection of the CBO and our calculations (joined on the asset name)
    CBO_v_OSPC = vars_by_asset.merge(CBO_data,how='inner',on='Asset Type',
                        left_index=False, right_index=False, sort=False,
                        copy=True)

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

    CBO_v_OSPC.to_csv(_OUT_DIR+'/CBO_v_OSPC.csv',columns=cols_to_print, encoding='utf-8')
