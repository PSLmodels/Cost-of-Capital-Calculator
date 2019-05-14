import pytest
import pandas as pd
from ccc.parameters import Specifications
from ccc.data import Assets
from ccc.calculator import Calculator


def test_range_plot():
    '''
    Test range_plot method.
    '''
    assets = Assets()
    p = Specifications()
    calc = Calculator(p, assets)
    p2 = Specifications(year=2026)
    p2.update_specifications({'CIT_rate': 0.25})
    calc2 = Calculator(p2, assets)
    fig = calc.range_plot(calc2)
    assert fig
    fig = calc.range_plot(calc2, output_variable='rho')
    assert fig


def test_grouped_bar():
    '''
    Test grouped_bar method.
    '''
    assets = Assets()
    p = Specifications()
    calc = Calculator(p, assets)
    p2 = Specifications(year=2026)
    p2.update_specifications({'CIT_rate': 0.25})
    calc2 = Calculator(p2, assets)
    fig = calc.grouped_bar(calc2)
    assert fig
    fig = calc.grouped_bar(calc2, output_variable='rho',
                           group_by_asset=False)
    assert fig


def test_asset_bubble():
    '''
    Test asset bubble plot method.
    '''
    assets = Assets()
    p = Specifications()
    calc = Calculator(p, assets)
    p2 = Specifications(year=2026)
    p2.update_specifications({'CIT_rate': 0.25})
    calc2 = Calculator(p2, assets)
    fig = calc.asset_bubble(calc2)
    assert fig
    fig = calc.asset_bubble(calc2, output_variable='rho_mix')
    assert fig


def test_bubble_widget():
    '''
    Test asset bubble plot method.
    '''
    assets = Assets()
    p = Specifications()
    calc = Calculator(p, assets)
    p2 = Specifications(year=2026)
    p2.update_specifications({'CIT_rate': 0.25})
    calc2 = Calculator(p2, assets)
    fig = calc.bubble_widget(calc2)
    assert fig


def test_calc_by_asset():
    '''
    Test difference_table method.
    '''
    yr = 2018
    assets = Assets()
    p = Specifications(year=yr)
    calc1 = Calculator(p, assets)
    assert calc1.current_year == yr
    asset_df = calc1.calc_by_asset()
    assert isinstance(asset_df, pd.DataFrame)


def test_calc_by_industry():
    '''
    Test difference_table method.
    '''
    yr = 2018
    assets = Assets()
    p = Specifications(year=yr)
    calc1 = Calculator(p, assets)
    assert calc1.current_year == yr
    asset_df = calc1.calc_by_industry()
    assert isinstance(asset_df, pd.DataFrame)


def test_summary_table():
    '''
    Test difference_table method.
    '''
    yr = 2018
    assets = Assets()
    p = Specifications(year=yr)
    calc1 = Calculator(p, assets)
    assert calc1.current_year == yr
    reform = {'CIT_rate': 0.38}
    p.update_specifications(reform)
    calc2 = Calculator(p, assets)
    assert calc2.current_year == yr
    summary_df = calc1.summary_table(calc2)
    assert isinstance(summary_df, pd.DataFrame)


def test_asset_share_table():
    '''
    Test difference_table method.
    '''
    yr = 2018
    assets = Assets()
    p = Specifications(year=yr)
    calc1 = Calculator(p, assets)
    assert calc1.current_year == yr
    asset_df = calc1.asset_share_table()
    assert isinstance(asset_df, pd.DataFrame)


def test_asset_summary_table():
    '''
    Test difference_table method.
    '''
    yr = 2018
    assets = Assets()
    p = Specifications(year=yr)
    calc1 = Calculator(p, assets)
    assert calc1.current_year == yr
    reform = {'CIT_rate': 0.38}
    p.update_specifications(reform)
    calc2 = Calculator(p, assets)
    assert calc2.current_year == yr
    asset_df = calc1.asset_summary_table(calc2)
    assert isinstance(asset_df, pd.DataFrame)


def test_industry_summary_table():
    '''
    Test difference_table method.
    '''
    yr = 2018
    assets = Assets()
    p = Specifications(year=yr)
    calc1 = Calculator(p, assets)
    assert calc1.current_year == yr
    reform = {'CIT_rate': 0.38}
    p.update_specifications(reform)
    calc2 = Calculator(p, assets)
    assert calc2.current_year == yr
    ind_df = calc1.industry_summary_table(calc2)
    assert isinstance(ind_df, pd.DataFrame)