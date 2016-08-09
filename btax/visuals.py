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
from bokeh.palettes import Spectral5
from bokeh.plotting import curdoc, figure
from bokeh.sampledata.autompg import autompg
from bokeh.client import push_session


'''
------------------------------------------
Define asset categories
------------------------------------------
'''

asset_categories = {'Computers and Software', 'Office and Residential Equipment',
    'Instruments and Communications Equipment', 'Transportation Equipment',
    'Industrial Machinery', 'Other Industrial Equipment', 'Other Equipment',
    'Residential Buildings', 'Nonresidential Buildings',
    'Mining and Drilling Structures', 'Other Structures'}


asset_dict = dict.fromkeys(['Mainframes','PCs','DASDs','Printers',
      'Terminals','Tape drives','Storage devices','System integrators',
      'Prepackaged software','Custom software','Own account software'],'Computers and Software')
asset_dict.update(dict.fromkeys(['Communications','Nonelectro medical instruments',
      'Electro medical instruments','Nonmedical instruments','Photocopy and related equipment',
      'Office and accounting equipment'],'Instruments and Communications Equipment'))
asset_dict.update(dict.fromkeys(['Household furniture','Other furniture','Household appliances'],
      'Office and Residential Equipment'))
asset_dict.update(dict.fromkeys(['Light trucks (including utility vehicles)',
      'Other trucks, buses and truck trailers','Autos','Aircraft',
      'Ships and boats','Railroad equipment','Steam engines','Internal combustion engines'],
      'Transportation Equipment'))
asset_dict.update(dict.fromkeys(['Special industrial machinery','General industrial equipment'],
      'Industrial Machinery'))
asset_dict.update(dict.fromkeys(['Nuclear fuel','Other fabricated metals',
      'Metalworking machinery','Electric transmission and distribution',
      'Other agricultural machinery','Farm tractors','Other construction machinery',
      'Construction tractors','Mining and oilfield machinery'],
      'Other Industrial Equipment'))
asset_dict.update(dict.fromkeys(['Service industry machinery','Other electrical','Other'],
      'Other Equipment'))
# my_dict.update(dict.fromkeys([],
#       'Residential Buildings'))
asset_dict.update(dict.fromkeys(['Office','Hospitals','Special care','Medical buildings','Multimerchandise shopping',
      'Food and beverage establishments','Warehouses','Mobile structures','Other commercial',
      'Religious','Educational and vocational','Lodging'],
      'Nonresidential Buildings'))
asset_dict.update(dict.fromkeys(['Gas','Petroleum pipelines','Communication',
      'Petroleum and natural gas','Mining'],'Mining and Drilling Structures'))
asset_dict.update(dict.fromkeys(['Manufacturing','Electric','Wind and solar',
      'Amusement and recreation','Air transportation','Other transportation',
      'Other railroad','Track replacement','Local transit structures',
      'Other land transportation','Farm','Water supply','Sewage and waste disposal',
      'Public safety','Highway and conservation and development'],
      'Other Structures'))
asset_dict.update(dict.fromkeys(['Pharmaceutical and medicine manufacturing',
      'Chemical manufacturing, ex. pharma and med','Semiconductor and other component manufacturing',
      'Computers and peripheral equipment manufacturing','Communications equipment manufacturing',
      'Navigational and other instruments manufacturing','Other computer and electronic manufacturing, n.e.c.',
      'Motor vehicles and parts manufacturing','Aerospace products and parts manufacturing',
      'Other manufacturing','Scientific research and development services','Software publishers',
      'Financial and real estate services','Computer systems design and related services','All other nonmanufacturing, n.e.c.',
      'Private universities and colleges','Other nonprofit institutions','Theatrical movies','Long-lived television programs',
      'Books','Music'],'Intellectual Property'))

'''
------------------------------------------
Plot results
------------------------------------------
'''

def asset_crossfilter(output_by_assets):
    """Creates a crossfilter bokeh plot of results by asset

        :param entity_dfs: Contains all the soi data by entity type
        :type entity_dfs: dictionary
        :returns: Fixed asset data organized by industry, entity, and asset type
        :rtype: dictionary
    """
    df = output_by_assets.copy()

    SIZES = list(range(6, 22, 3))
    COLORS = Spectral5

    columns = sorted(df.columns)
    discrete = [x for x in columns if df[x].dtype == object]
    continuous = [x for x in columns if x not in discrete]
    quantileable = [x for x in continuous if len(df[x].unique()) > 20]

    x = Select(title='X-Axis', value='METR', options=columns)
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
    layout = row(controls, create_figure())

    curdoc().add_root(layout)
    curdoc().title = "Crossfilter"

def create_figure():
    xs = df[x.value].values
    ys = df[y.value].values
    x_title = x.value.title()
    y_title = y.value.title()

    kw = dict()
    if x.value in discrete:
        kw['x_range'] = sorted(set(xs))
    if y.value in discrete:
        kw['y_range'] = sorted(set(ys))
    kw['title'] = "%s vs %s" % (x_title, y_title)

    p = figure(plot_height=600, plot_width=800, tools='pan,box_zoom,reset', **kw)
    p.xaxis.axis_label = x_title
    p.yaxis.axis_label = y_title

    if x.value in discrete:
        p.xaxis.major_label_orientation = pd.np.pi / 4

    sz = 9
    if size.value != 'None':
        groups = pd.qcut(df[size.value].values, len(SIZES))
        sz = [SIZES[xx] for xx in groups.codes]

    c = "#31AADE"
    if color.value != 'None':
        groups = pd.qcut(df[color.value].values, len(COLORS))
        c = [COLORS[xx] for xx in groups.codes]
    p.circle(x=xs, y=ys, color=c, size=sz, line_color="white", alpha=0.6, hover_color='white', hover_alpha=0.5)

    return p


def update(attr, old, new):
    layout.children[1] = create_figure()
