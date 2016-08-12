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


'''
------------------------------------------
Plot results
------------------------------------------
'''

SIZES = list(range(6, 22, 3))
COLORS = Reds9

def asset_crossfilter(output_by_assets):
    """Creates a crossfilter bokeh plot of results by asset

        :output_by_assets: Contains output by asset
        :type output_by_assets: dataframe
        :returns:
        :rtype:
    """
    df = output_by_assets.copy()

    columns = sorted(df.columns)
    discrete = [x for x in columns if df[x].dtype == object]
    continuous = [x for x in columns if x not in discrete]
    quantileable = [x for x in continuous if len(df[x].unique()) > 20]

    x = Select(title='X-Axis', value='metr_c', options=columns)
    x.on_change('value', update)

    y = Select(title='Y-Axis', value='asset_category', options=columns)
    y.on_change('value', update)

    size = Select(title='Size', value='assets', options=['None'] + quantileable)
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
    file = open("crossfilter_html.html","wb") #open file in binary mode
    file.writelines(html)
    file.close()


def create_figure(df,x,y,discrete,quantileable,continuous,size,color,controls):
    xs = df[x.value].values
    ys = df[y.value].values
    ass = df['Asset'].values

    # x_title = x.value.title()
    # y_title = y.value.title()
    x_title = "Marginal Effective Tax Rate"
    y_title = "Asset Category"

    source = ColumnDataSource(df)

    kw = dict()
    if x.value in discrete:
        kw['x_range'] = sorted(set(xs))
    if y.value in discrete:
        kw['y_range'] = sorted(set(ys))
    # kw['title'] = "%s vs %s" % (x_title, y_title)
    kw['title'] = "Marginal Effective Tax Rates on Typically Financed Corporate Investments, 2016 Law"


    p = figure(plot_height=600, plot_width=800, tools='pan,box_zoom,reset,hover', **kw)
    p.xaxis.axis_label = x_title
    p.yaxis.axis_label = y_title

    hover = p.select(dict(type=HoverTool))
    hover.tooltips = [('Asset', '@ass')]

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
    p.circle(x=xs, y=ys, color=c, size=sz, line_color="white", alpha=0.6, hover_color='white', hover_alpha=0.5)

    return p


def update(attr, old, new):
    layout.children[1] = create_figure()
