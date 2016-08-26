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
from bokeh.layouts import row, widgetbox
from bokeh.models import Select
from bokeh.palettes import Spectral5, Reds9
from bokeh.plotting import curdoc, figure
from bokeh.client import push_session
from bokeh.resources import CDN
from bokeh.embed import file_html
from bokeh.models import HoverTool
from bokeh.models import ColumnDataSource
from bokeh.charts.attributes import ColorAttr, CatAttr


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
COLORS = Reds9

def asset_crossfilter(output_by_assets,baseline):
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


    columns = sorted(df.columns)
    discrete = [x for x in columns if df[x].dtype == object]
    continuous = [x for x in columns if x not in discrete]
    quantileable = [x for x in continuous if len(df[x].unique()) > 20]

    x = Select(title='X-Axis', value='metr_c', options=columns)
    x.on_change('value', update)

    y = Select(title='Y-Axis', value='asset_category', options=columns)
    y.on_change('value', update)

    size = Select(title='Size', value='assets_c', options=['None'] + quantileable)
    size.on_change('value', update)

    # color = Select(title='Color', value='None', options=['None'] + quantileable)
    # color.on_change('value', update)
    color = Select(title='Color', value='None', options=['None'] + discrete)
    color.on_change('value', update)

    controls = widgetbox([x, y, color, size], width=200)
    #layout = row(controls, create_figure(df,x,y,discrete,quantileable,continuous,size,color,controls))
    layout = row(create_figure(df,x,y,discrete,quantileable,continuous,size,color,controls))


    curdoc().add_root(layout)
    curdoc().title = "Crossfilter"

    # # open a session to keep our local document in sync with server
    # session = push_session(curdoc())
    # session.show() # open the document in a browser
    #
    # session.loop_until_closed() # run forever

    # save plot to html
    plot = curdoc()
    #plot.circle([1,2], [3,4])
    html = file_html(plot, CDN, "my plot")
    file = open(baseline+"crossfilter_html.html","wb") #open file in binary mode
    file.writelines(html)
    file.close()


def create_figure(df,x,y,discrete,quantileable,continuous,size,color,controls):
    xs = df[x.value].values
    ys = df[y.value].values

    # x_title = x.value.title()
    # y_title = y.value.title()
    x_title = "Marginal Effective Tax Rate"
    y_title = "Asset Category"

    source = ColumnDataSource(ColumnDataSource.from_df(df))

    kw = dict()
    if x.value in discrete:
        kw['x_range'] = sorted(set(xs))
    if y.value in discrete:
        kw['y_range'] = sorted(set(ys))
    # kw['title'] = "%s vs %s" % (x_title, y_title)
    #kw['title'] = "Marginal Effective Tax Rates on Typically Financed Corporate Investments, 2016 Law"
    # kw['title'] = "Marginal Effective Tax Rates on Corporate Investments, 2016 Law"
    kw['title'] = "METRs on Corporate Investments, 2016 Law"

    p = figure(plot_height=400, plot_width=600, tools='pan,box_zoom,reset,hover', **kw)
    p.xaxis.axis_label = x_title
    p.yaxis.axis_label = y_title

    hover = p.select(dict(type=HoverTool))
    hover.tooltips = [('Asset', '@Asset')]

    if x.value in discrete:
        p.xaxis.major_label_orientation = pd.np.pi / 4

    sz = 9
    if size.value != 'None':
        groups = pd.qcut(df[size.value].values, len(SIZES))
        sz = [SIZES[xx] for xx in groups.codes]

    c = "#73000A"
    if color.value != 'None':
        groups = pd.qcut(df[color.value].values, len(COLORS))
        c = [COLORS[xx] for xx in groups.codes]
    p.circle(x=xs, y=ys, source=source, color=c, size=sz, line_color="white", alpha=0.6, hover_color='white', hover_alpha=0.5)

    # p.title.text_color = "black"
    # p.title.text_font = "Georgia"

    return p


def update(attr, old, new):
    layout.children[1] = create_figure()
