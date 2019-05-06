import pytest
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
