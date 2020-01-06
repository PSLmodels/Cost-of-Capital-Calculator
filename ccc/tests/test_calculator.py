import pytest
import pandas as pd
import numpy as np
from ccc.parameters import Specification
from ccc.data import Assets
from ccc.calculator import Calculator


def test_Caculator_exception1():
    '''
    Raise exception for not passing parameters object
    '''
    assets = Assets()
    with pytest.raises(Exception):
        assert Calculator(assets=assets)


def test_Caculator_exception2():
    '''
    Raise exception for not passing assets object
    '''
    p = Specification()
    with pytest.raises(Exception):
        assert Calculator(p=p)


def test_calc_other():
    '''
    Test calc_other method
    '''
    assets = Assets()
    p = Specification()
    calc = Calculator(p, assets)
    df = calc.calc_by_asset()
    calc_other_df = calc.calc_other(df)
    assert ('ucc_mix' in calc_other_df.keys())
    assert ('metr_mix' in calc_other_df.keys())
    assert ('mettr_mix' in calc_other_df.keys())
    assert ('tax_wedge_mix' in calc_other_df.keys())
    assert ('eatr_mix' in calc_other_df.keys())


def test_calc_base():
    '''
    Test calc_base method
    '''
    assets = Assets()
    p = Specification()
    calc = Calculator(p, assets)
    calc.calc_base()
    calc_base_df = calc._Calculator__assets.df
    assert ('z_mix' in calc_base_df.keys())
    assert ('rho_mix' in calc_base_df.keys())


def test_calc_all():
    '''
    Test calc_all method
    '''
    assets = Assets()
    p = Specification()
    calc = Calculator(p, assets)
    calc.calc_all()
    calc_all_df = calc._Calculator__assets.df
    assert ('z_mix' in calc_all_df.keys())
    assert ('rho_mix' in calc_all_df.keys())
    assert ('ucc_mix' in calc_all_df.keys())
    assert ('metr_mix' in calc_all_df.keys())
    assert ('mettr_mix' in calc_all_df.keys())
    assert ('tax_wedge_mix' in calc_all_df.keys())
    assert ('eatr_mix' in calc_all_df.keys())


def test_calc_by_asset():
    '''
    Test calc_by_asset method
    '''
    assets = Assets()
    p = Specification()
    calc = Calculator(p, assets)
    asset_df = calc.calc_by_asset()
    assert ('major_asset_group' in asset_df.keys())


@pytest.mark.parametrize('include_land,include_inventories',
                         [(False, False), (True, True)],
                         ids=['No land or inv', 'Both land and inv'])
def test_calc_by_industry(include_land, include_inventories):
    '''
    Test calc_by_industry method
    '''
    assets = Assets()
    p = Specification()
    calc = Calculator(p, assets)
    ind_df = calc.calc_by_industry(
        include_land=include_land,
        include_inventories=include_inventories)
    assert ('major_industry' in ind_df.keys())


@pytest.mark.parametrize('include_land,include_inventories',
                         [(False, False), (True, True)],
                         ids=['No land or inv', 'Both land and inv'])
def test_summary_table(include_land, include_inventories):
    '''
    Test summary_table method.
    '''
    cyr = 2018
    assets = Assets()
    p = Specification(year=cyr)
    calc1 = Calculator(p, assets)
    assert calc1.current_year == cyr
    p.update_specification({'CIT_rate': 0.38})
    calc2 = Calculator(p, assets)
    assert calc2.current_year == cyr
    summary_df = calc1.summary_table(
        calc2, include_land=include_land,
        include_inventories=include_inventories)
    assert isinstance(summary_df, pd.DataFrame)


@pytest.mark.parametrize('include_land,include_inventories',
                         [(False, False), (True, True)],
                         ids=['No land or inv', 'Both land and inv'])
def test_asset_share_table(include_land, include_inventories):
    '''
    Test asset_share_table method.
    '''
    cyr = 2018
    assets = Assets()
    p = Specification(year=cyr)
    calc1 = Calculator(p, assets)
    assert calc1.current_year == cyr
    asset_df = calc1.asset_share_table(
        include_land=include_land,
        include_inventories=include_inventories)
    assert isinstance(asset_df, pd.DataFrame)


@pytest.mark.parametrize('include_land,include_inventories',
                         [(False, False), (True, True)],
                         ids=['No land or inv', 'Both land and inv'])
def test_asset_summary_table(include_land, include_inventories):
    '''
    Test asset_summary_table method.
    '''
    cyr = 2018
    assets = Assets()
    p = Specification(year=cyr)
    calc1 = Calculator(p, assets)
    assert calc1.current_year == cyr
    p.update_specification({'CIT_rate': 0.38})
    calc2 = Calculator(p, assets)
    assert calc2.current_year == cyr
    asset_df = calc1.asset_summary_table(
        calc2, include_land=include_land,
        include_inventories=include_inventories)
    assert isinstance(asset_df, pd.DataFrame)


@pytest.mark.parametrize('include_land,include_inventories',
                         [(False, False), (True, True)],
                         ids=['No land or inv', 'Both land and inv'])
def test_industry_summary_table(include_land, include_inventories):
    '''
    Test industry_summary_table method.
    '''
    cyr = 2018
    assets = Assets()
    p = Specification(year=cyr)
    calc1 = Calculator(p, assets)
    assert calc1.current_year == cyr
    p.update_specification({'CIT_rate': 0.38})
    calc2 = Calculator(p, assets)
    assert calc2.current_year == cyr
    ind_df = calc1.industry_summary_table(
        calc2, include_land=include_land,
        include_inventories=include_inventories)
    assert isinstance(ind_df, pd.DataFrame)


@pytest.mark.parametrize('corporate', [True, False],
                         ids=['Corporate', 'Non-Corporate'])
def test_range_plot(corporate):
    '''
    Test range_plot method.
    '''
    assets = Assets()
    p = Specification()
    calc = Calculator(p, assets)
    p2 = Specification(year=2026)
    p2.update_specification({'CIT_rate': 0.25})
    calc2 = Calculator(p2, assets)
    fig = calc.range_plot(calc2, corporate=corporate,
                          include_title=True)
    assert fig
    fig = calc.range_plot(calc2, output_variable='rho',
                          corporate=corporate, include_title=True)
    assert fig


@pytest.mark.parametrize('corporate', [True, False],
                         ids=['Corporate', 'Non-Corporate'])
def test_grouped_bar(corporate):
    '''
    Test grouped_bar method.
    '''
    assets = Assets()
    p = Specification()
    calc = Calculator(p, assets)
    p2 = Specification(year=2026)
    p2.update_specification({'CIT_rate': 0.25})
    calc2 = Calculator(p2, assets)
    fig = calc.grouped_bar(calc2, corporate=corporate)
    assert fig
    fig = calc.grouped_bar(calc2, output_variable='rho',
                           corporate=corporate, group_by_asset=False)
    assert fig


def test_asset_bubble():
    '''
    Test asset bubble plot method.
    '''
    assets = Assets()
    p = Specification()
    calc = Calculator(p, assets)
    p2 = Specification(year=2026)
    p2.update_specification({'CIT_rate': 0.25})
    calc2 = Calculator(p2, assets)
    fig = calc.asset_bubble(calc2, include_title=True)
    assert fig
    fig = calc.asset_bubble(calc2, output_variable='rho_mix',
                            include_title=True)
    assert fig


def test_bubble_widget():
    '''
    Test asset bubble plot method.
    '''
    assets = Assets()
    p = Specification()
    calc = Calculator(p, assets)
    p2 = Specification(year=2026)
    p2.update_specification({'CIT_rate': 0.25})
    calc2 = Calculator(p2, assets)
    fig = calc.bubble_widget(calc2)
    assert fig


def test_store_assets():
    assets = Assets()
    p = Specification()
    calc1 = Calculator(p, assets)
    calc1.store_assets()
    assert isinstance(calc1, Calculator)


def test_restore_assets():
    assets = Assets()
    p = Specification()
    calc1 = Calculator(p, assets)
    calc1.store_assets()
    calc1.restore_assets()
    assert isinstance(calc1, Calculator)


def test_p_param():
    assets = Assets()
    p = Specification()
    calc1 = Calculator(p, assets)
    obj = calc1.p_param('tau_int')
    assert np.allclose(obj, np.array([0.31500528]))


def test_data_year():
    assets = Assets()
    p = Specification()
    calc1 = Calculator(p, assets)
    assert calc1.data_year == 2013
