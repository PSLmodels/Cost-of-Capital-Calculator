import pytest
import pandas as pd
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


def test_calc_by_industry():
    '''
    Test calc_by_industry method
    '''
    assets = Assets()
    p = Specification()
    calc = Calculator(p, assets)
    ind_df = calc.calc_by_industry()
    assert ('major_industry' in ind_df.keys())


def test_summary_table():
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
    summary_df = calc1.summary_table(calc2)
    assert isinstance(summary_df, pd.DataFrame)


def test_asset_share_table():
    '''
    Test asset_share_table method.
    '''
    cyr = 2018
    assets = Assets()
    p = Specification(year=cyr)
    calc1 = Calculator(p, assets)
    assert calc1.current_year == cyr
    asset_df = calc1.asset_share_table()
    assert isinstance(asset_df, pd.DataFrame)


def test_asset_summary_table():
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
    asset_df = calc1.asset_summary_table(calc2)
    assert isinstance(asset_df, pd.DataFrame)


def test_industry_summary_table():
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
    ind_df = calc1.industry_summary_table(calc2)
    assert isinstance(ind_df, pd.DataFrame)


def test_range_plot():
    '''
    Test range_plot method.
    '''
    assets = Assets()
    p = Specification()
    calc = Calculator(p, assets)
    p2 = Specification(year=2026)
    p2.update_specification({'CIT_rate': 0.25})
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
    p = Specification()
    calc = Calculator(p, assets)
    p2 = Specification(year=2026)
    p2.update_specification({'CIT_rate': 0.25})
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
    p = Specification()
    calc = Calculator(p, assets)
    p2 = Specification(year=2026)
    p2.update_specification({'CIT_rate': 0.25})
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
    p = Specification()
    calc = Calculator(p, assets)
    p2 = Specification(year=2026)
    p2.update_specification({'CIT_rate': 0.25})
    calc2 = Calculator(p2, assets)
    fig = calc.bubble_widget(calc2)
    assert fig
