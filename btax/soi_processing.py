"""
SOI Auxiliary Script (soi_processing.py):
-------------------------------------------------------------------------------
Module that handles reading in the soi data (corporate, partners, and sole proprietorships). Makes calls to a different
script for each one of these entities. Also provides auxiliary scripts to format the partner and proprietorship dataframes and to
interpolate missing data.
Last updated: 7/26/2016.

"""
# Import packages
import os.path
import sys
import numpy as np
import pandas as pd
# Import custom modules
import pull_soi_corp as corp
import pull_soi_partner as prt
import pull_soi_proprietorship as prop
# Factor used to adjust dollar values
_FILE_FCTR = 10**3

def pull_soi_data():
    """Creates a dictionary that is updated with the soi entity data after each method.

        :returns: DataFrames organized by entity type (corp, partner, sole prop)
        :rtype: dictionary
    """
    entity_dfs = {}
    entity_dfs.update(corp.load_corp_data())

    entity_dfs.update(prt.load_partner_data(entity_dfs))

    entity_dfs.update(prop.load_proprietorship_data(entity_dfs))



    # make one big data frame - by industry and entity type
    


    return entity_dfs



def interpolate_data(entity_dfs, df):
    """Fills in the missing values using the proportion of corporate industry values

        :param entity_dfs: Contains all the soi data by entity type
        :param df: The datframe that will be updated with new values
        :type entity_dfs: dictionary
        :type df: DataFrame
        :returns: The new dataframe with values for all the industries
        :rtype: DataFrame
    """
    # Takes the total corp values as the baseline
    base_df = entity_dfs['tot_corp']
    # Stores the dataframe in a numpy array
    corp_data = np.array(base_df)
    # Stores the partner or prop data in a numpy array
    prt_data = np.array(df)
    # Iterates over each industry in the partner or prop data
    for i in xrange(0, len(prt_data)):
        # If it is a two digit code then it will appear in the denominator of the following calcs
        if(len(str(int(prt_data[i][0]))) == 2):
            # Grabs the parent data from the corporate array
            parent_ind = corp_data[i]
            # Grabs the partner or prop data as well
            prt_ind = prt_data[i][1:]
        # If the partner or prop data is missing a value
        if(prt_data[i][1] == 0):
            # Grabs the corporate data for the minor industry
            corp_ind = corp_data[i]
            # Divides the minor industry corporate data by the major industry data
            ratios = corp_ind / parent_ind
            # Mulitplies the partner or prop data for the major data to find minor partner data
            new_data = prt_ind * ratios[1:]
            # Sets new values in the partner or prop dataframe
            df.set_value(i, 'Fixed Assets', new_data[0])
            df.set_value(i, 'Inventories', new_data[1])
            df.set_value(i, 'Land', new_data[2])
    # Returns the partner or prop dataframe with all the missing values filled in
    return df
