import numpy as np
from ccc.constants import TAX_METHODS
from ccc.utils import str_modified


def update_depr_methods(df, p):
    # update tax_deprec_rates based on user defined parameters
    df['System'] = df['GDS Life'].apply(str_modified)
    df['System'].replace(p.deprec_system, inplace=True)
    df.loc[df['System'] == 'ADS', 'Method'] = 'SL'
    df.loc[df['System'] == 'Economic', 'Method'] = 'Economic'

    # add bonus depreciation to tax deprec parameters dataframe
    df['bonus'] = df['GDS Class Life'].apply(str_modified)
    df['bonus'].replace(p.bonus_deprec, inplace=True)

    df['b'] = df['Method']
    df['b'].replace(TAX_METHODS, inplace=True)

    df.loc[df['System'] == 'ADS', 'Y'] = df.loc[df['System'] == 'ADS',
                                                'ADS Life']
    df.loc[df['System'] == 'GDS', 'Y'] = df.loc[df['System'] == 'GDS',
                                                'GDS Life']

    return df


def dbsl(Y, b, bonus, r):
    """
    Makes the calculation for the declining balance with a switch to
    straight line (DBSL) method of depreciation.

    ..math::
        z = \frac{\beta}{\beta+r}\left[1-e^{-(\beta+r)Y^{*}}\right]+
        \frac{e^{-\beta Y^{*}}}{(Y-Y^{*})r}\left[e^{-rY^{*}}-e^{-rY}\right]

    Args:
        df: dataframe, contains economic depreciation and tax
            depreciation schedules for all assets where DBSL depreciation
            will be applied.
        r: numpy array, nominal discount rate for each tax treatment
           and type of financing
        financing_list: list, list of strings defining financing options
                        (e.g., typically financed, debt financed,
                        equity financed)
        entity_list = list, list of strings of different entity types

    Returns:
        df: dataframe, NPV of depreciation deductions for all asset
            using DBSL depreciation, all financing types, and all tax
            treatment types

    """

    beta = Y / b
    Y_star = Y * (1 - (1 / b))
    z = (
        bonus + ((1 - bonus) * (((beta / (beta + r)) *
                                 (1 - np.exp(-1 * (beta + r) * Y_star)))
                                + ((np.exp(-1 * beta * Y_star) /
                                    ((Y - Y_star * r)) *
                                    np.exp(-1 * r * Y_star) -
                                    np.exp(-1 * r * Y))))))

    return z


def sl(Y, bonus, r):
    """
    Makes the calculation for straight line (SL) method of depreciation.

    ..math::
        z = \frac{e^{-rY}}{Yr}

    Args:
        df: dataframe, contains economic depreciation and tax
            depreciation schedules for all assets where DBSL depreciation
            will be applied.
        r: numpy array, nominal discount rate for each tax treatment
           and type of financing
        financing_list: list, list of strings defining financing options
                        (e.g., typically financed, debt financed,
                        equity financed)
        entity_list = list, list of strings of different entity types

    Returns:
        df: dataframe, NPV of depreciation deductions for all asset
            using SL depreciation, all financing types, and all tax
            treatment types

    """
    z = bonus + ((1 - bonus) * ((1 - np.exp(-1 * r * Y)) / (r * Y)))

    return z


def econ(delta, bonus, r, pi):
    """
    Makes the calculation for the NPV of depreciation using economic
    depreciation rates.

    ..math::
        z = \frac{\delta}{(\delta + r - \pi)}

    Args:
        df: dataframe, contains economic depreciation and tax
            depreciation schedules for all assets where DBSL depreciation
            will be applied.
        r: numpy array, nominal discount rate for each tax treatment
           and type of financing
        pi: scalar, inflatino rate
        financing_list: list, list of strings defining financing options
                        (e.g., typically financed, debt financed,
                        equity financed)
        entity_list = list, list of strings of different entity types

    Returns:
        df: dataframe, NPV of depreciation deductions for all asset
            using economics depreciation, all financing types, and all
            tax treatment types

    """
    z = bonus + ((1 - bonus) * (delta / (delta + r - pi)))

    return z


# def npv_tax_depr(df, p):
def npv_tax_depr(df, r, pi):
    """
    Depending on the method of depreciation, makes calls to either
    the straight line or declining balance calculations.

    Args:
        r: numpy array, nominal discount rate for each tax treatment
           and type of financing
        pi: scalar, inflation rate
        tax_methods: dictionary, maps tax methods from data into model
        financing_list: list, list of strings defining financing options
                        (e.g., typically financed, debt financed,
                        equity financed)
        entity_list = list, list of strings of different entity types

    Returns:
        df_all: dataframe, NPV of depreciation deductions for all asset
                types, all financing types, and all tax treatment types

    """
    idx = (df['Method'] == 'DB 200%') | (df['Method'] == 'DB 150%')
    df.loc[idx, 'z'] = dbsl(df.loc[idx, 'Y'], df.loc[idx, 'b'],
                            df.loc[idx, 'bonus'], r)
    idx = df['Method'] == 'SL'
    df.loc[idx, 'z'] = sl(df.loc[idx, 'Y'], df.loc[idx, 'bonus'], r)
    idx = df['Method'] == 'Economic'
    df.loc[idx, 'z'] = econ(df.loc[idx, 'delta'], df.loc[idx, 'bonus'],
                            r, pi)
    idx = df['Method'] == 'Expensing'
    df.loc[idx, 'z'] = 1.0

    return df['z']


def eq_coc(delta, z, w, u, inv_tax_credit, Y_v, pi, r):
    """
    Compute the cost of capital

    ..math::
        \rho = \frac{(r-\pi+\delta)}{1-u(1-uz)+w-\delta

    Args:
        df: DataFrame, assets by type with depreciation rates
        w: scalar, property tax rate
        inventory_expensing: boolean, whether inventories are expensed
        stat_tax: Numpy array, entity level taxes for corp and noncorp
        inv_tax_credit: scalar, investment tax credit
        phi: scalar, fraction of inventories using FIFO
        Y_v: integer, number of years inventories held
        inflation_rate: scalar, rate of inflation
        discount_rate: Numpy array, discount rate used by entity type
                                    and financing used
        entity_list: list, identifiers for entity type
        financing_list: list, indentifiers for financing used

    Returns:
        df: DataFrame, assets by type with depreciation and cost of
                      capital

    """
    rho = (((r - pi + delta) / (1 - u)) *
           (1 - inv_tax_credit - u * z) + w - delta)

    return rho



def eq_coc_inventory(delta, u, phi, Y_v, pi, r):
    """
    Compute the cost of capital

    ..math::
        \rho = \frac{(r-\pi+\delta)}{1-u(1-uz)+w-\delta

    Args:
        df: DataFrame, assets by type with depreciation rates
        w: scalar, property tax rate
        inventory_expensing: boolean, whether inventories are expensed
        stat_tax: Numpy array, entity level taxes for corp and noncorp
        inv_tax_credit: scalar, investment tax credit
        phi: scalar, fraction of inventories using FIFO
        Y_v: integer, number of years inventories held
        inflation_rate: scalar, rate of inflation
        discount_rate: Numpy array, discount rate used by entity type
                                    and financing used
        entity_list: list, identifiers for entity type
        financing_list: list, indentifiers for financing used

    Returns:
        df: DataFrame, assets by type with depreciation and cost of
                      capital

    """
    rho_FIFO = (((1 / Y_v) * np.log((np.exp(r * Y_v) - u) /
                                    (1 - u))) - pi)
    rho_LIFO = ((1 / Y_v) * np.log((np.exp((r - pi) * Y_v) - u) /
                                   (1 - u)))
    rho = phi * rho_FIFO + (1 - phi) * rho_LIFO

    return rho

def eq_ucc(rho, delta):
    """
    Compute the user cost of capital

    ..math::
        ucc = \rho + \delta

    Args:
        rho =
        delta ():

    Returns:
        ucc
    """
    ucc = rho + delta

    return ucc


def eq_metr(rho, r_prime, pi):
    """
    Compute the marginal effective tax rate (METR)

    ..math::
        metr = \frac{\rho - (r^{'}-\pi)}{\rho}

    Args:
        df: DataFrame, assets by type with depreciation rates and cost
                       of capital
        r_prime: Numpy array, discount rate used by entity type
                                    and financing used
        inflation_rate: scalar, rate of inflation
        save_rate: Numpy array, after-tax return on savings
        entity_list: list, identifiers for entity type
        financing_list: list, indentifiers for financing used

    Returns:
        df: DataFrame, assets by type with depreciation and cost of
                      capital and METR and METTR and tax wedge

    """
    metr = (rho - (r_prime - pi)) / rho

    return metr


def eq_mettr(rho, s):
    """
    Compute the marginal effective total tax rate (METTR)

    ..math::
        mettr = \frac{\rho - s}{\rho}

    Args:
        df: DataFrame, assets by type with depreciation rates and cost
                       of capital
        r_prime: Numpy array, discount rate used by entity type
                                    and financing used
        inflation_rate: scalar, rate of inflation
        save_rate: Numpy array, after-tax return on savings
        entity_list: list, identifiers for entity type
        financing_list: list, indentifiers for financing used

    Returns:
        df: DataFrame, assets by type with depreciation and cost of
                      capital and METR and METTR and tax wedge

    """
    mettr = (rho - s) / rho

    return mettr


def eq_tax_wedge(rho, s):
    """
    Compute the tax wedge

    ..math::
        wedge = \rho - s

    Args:
        df: DataFrame, assets by type with depreciation rates and cost
                       of capital
        r_prime: Numpy array, discount rate used by entity type
                                    and financing used
        inflation_rate: scalar, rate of inflation
        save_rate: Numpy array, after-tax return on savings
        entity_list: list, identifiers for entity type
        financing_list: list, indentifiers for financing used

    Returns:
        df: DataFrame, assets by type with depreciation and cost of
                      capital and METR and METTR and tax wedge

    """
    wedge = rho - s

    return wedge


def eq_eatr(rho, metr, profit_rate, u):
    """
    Compute the effective average tax rate (EATR)

    ..math::
        eatr = \left(\frac{p - rho}{p}\right)u +
            \left(\frac{\rho}{p}\right)metr

    Args:
        df: DataFrame, assets by type with depreciation rates and cost
                       of capital and METR
        p: scalar, profit rate
        stat_tax: Numpy array, entity level taxes for corp and noncorp
        entity_list: list, identifiers for entity type
        financing_list: list, indentifiers for financing used

    Returns:
        df: DataFrame, assets by type with depreciation and cost of
                      capital and METR and METTR and EATR
    """
    eatr = (((profit_rate - rho) / profit_rate) * u +
            (rho / profit_rate) * metr)

    return eatr
