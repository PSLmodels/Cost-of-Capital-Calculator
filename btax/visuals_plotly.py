'''
------------------------------------------------------------------------
Last updated 8/5/2016

This program reads in the btax output dataframes and plots the results.

This py-file calls the following other file(s):

This py-file creates the following other file(s):

------------------------------------------------------------------------
'''

# Packages
import datetime
import re
import math

from btax.visuals import (asset_categories_for_print,
                          asset_category_order,
                          IP_list)
'''
------------------------------------------
Plot results
------------------------------------------
'''

SIZES = list(range(6, 22, 3))

def asset_bubble(output_by_assets):
    """Creates a crossfilter bokeh plot of results by asset

        :output_by_assets: Contains output by asset
        :type output_by_assets: dataframe
        :returns:
        :rtype:
    """
    import numpy as np
    import pandas as pd
    import plotly.plotly as py
    import plotly.graph_objs as go

    df_all = output_by_assets.copy()

    df = df_all[df_all['asset_category'] != 'Intellectual Property'].copy()

    # sort categories
    df['sort_order'] = df['asset_category']
    df['sort_order'].replace(asset_category_order,inplace=True)
    df.sort_values(by="sort_order",axis=0,ascending=True,inplace=True)
    df.reset_index(inplace=True)


    # update asset_category names for better printing
    df['asset_category'].replace(asset_categories_for_print,inplace=True)

    df.iplot(kind='bubble', x='metr_c', y='asset_category',
             size='assets', text='Asset',
             xTitle='Marginal Effective Tax Rate',
             yTitle='Asset Category',
             filename='BubbleChart.png')
