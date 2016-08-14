'''
------------------------------------------------------------------------
Last updated 8/5/2016

This program reads in the btax output dataframes and plots the results.

This py-file calls the following other file(s):

This py-file creates the following other file(s):

------------------------------------------------------------------------
'''

# Packages
import numpy as np
import datetime
import re
import math
import pandas as pd

import plotly.plotly as py
import plotly.graph_objs as go


asset_categories_for_print = {'Computers and Software':'Computers and'+'\n'+'Software',
                              'Office and Residential Equipment':'Office and Residential'+'\n'+'Equipment',
    'Instruments and Communications Equipment':'Instruments and'+'\n'+'Communications'+'\n'+'Equipment',
    'Transportation Equipment':'Transportation Equipment',
    'Industrial Machinery':'Industrial Machinery',
    'Other Industrial Equipment':'Other Industrial'+'\n'+'Equipment',
    'Other Equipment':'Other Equipment',
    'Residential Buildings':'Residential Buildings',
    'Nonresidential Buildings':'Nonresidential Buildings',
    'Mining and Drilling Structures':'Mining and Drilling'+'\n'+'Structures',
    'Other Structures':'Other Structures',
    'Intellectual Property':'Intellectual Property'}


asset_category_order = {'Computers and Software':1,
    'Instruments and Communications Equipment':2,
    'Office and Residential Equipment':3,
    'Transportation Equipment':4,
    'Industrial Machinery':5,
    'Other Industrial Equipment':6,
    'Other Equipment':7,
    'Residential Buildings':8,
    'Nonresidential Buildings':9,
    'Mining and Drilling Structures':10,
    'Other Structures':11,
    'Intellectual Property':12}

# Drop cetain  IP assets until we get tax deprec better specified
IP_list = ['Scientific research and development services','Software publishers',
           'Financial and real estate services','Computer systems design and related services',
           'All other nonmanufacturing, n.e.c.','Private universities and colleges',
           'Other nonprofit institutions','Theatrical movies','Long-lived television programs',
           'Books','Music','Other entertainment originals']

'''
------------------------------------------
Plot results
------------------------------------------
'''

SIZES = list(range(6, 22, 3))
#COLORS = Reds9

def asset_bubble(output_by_assets):
    """Creates a crossfilter bokeh plot of results by asset

        :output_by_assets: Contains output by asset
        :type output_by_assets: dataframe
        :returns:
        :rtype:
    """
    df_all = output_by_assets.copy()

    df = df_all[df_all['asset_category']!='Intellectual Property'].copy()

    # sort categories
    df['sort_order'] = df['asset_category']
    df['sort_order'].replace(asset_category_order,inplace=True)
    df.sort_values(by="sort_order",axis=0,ascending=True,inplace=True)
    df.reset_index(inplace=True)


    # update asset_category names for better printing
    df['asset_category'].replace(asset_categories_for_print,inplace=True)

    df.iplot(kind='bubble', x='metr_c', y='asset_category', size='assets', text='Asset',
             xTitle='Marginal Effective Tax Rate', yTitle='Asset Category',
             filename='BubbleChart.png')
