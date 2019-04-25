import numpy as np
from ccc.constants import TAX_METHODS
from ccc.utils import str_modified


def update_depr_methods(df, p):
    """
    Updates depreciation methods per changes from defaults that are
    specified by user.

    Args:
        df: pandas DataFrame, assets by type and tax treatment with
                current law tax depreciation methods
        p: CCC Specifications object, model parameters

    Returns:
        df: pandas DataFrame, assets by type and tax treatment with
            updated tax depreciation methods
    """
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
        Y: array_like, asset life in years
        b: array_like, scale of declining balance (e.g., b=2 means
            double declining balance)
        bonus: array_like, rate of bonus depreciation
        r: scalar, discount rate

    Returns:
        z: array_like, net present value of depreciation deductions for
            $1 of investment

    """
    beta = b / Y
    Y_star = Y * (1 - (1 / b))
    z = (
        bonus + ((1 - bonus) * (((beta / (beta + r)) *
                                 (1 - np.exp(-1 * (beta + r) * Y_star)))
                                + ((np.exp(-1 * beta * Y_star) /
                                    ((Y - Y_star) * r)) *
                                   (np.exp(-1 * r * Y_star) -
                                    np.exp(-1 * r * Y))))))

    return z


def sl(Y, bonus, r):
    """
    Makes the calculation for straight line (SL) method of depreciation.

    ..math::
        z = \frac{1 - e^{-rY}}{Yr}

    Args:
        Y: array_like, asset life in years
        bonus: array_like, rate of bonus depreciation
        r: scalar, discount rate

    Returns:
        z: array_like, net present value of depreciation deductions for
            $1 of investment

    """
    z = bonus + ((1 - bonus) * ((1 - np.exp(-1 * r * Y)) / (r * Y)))

    return z


def econ(delta, bonus, r, pi):
    """
    Makes the calculation for the NPV of depreciation deductions using
    economic depreciation rates.

    ..math::
        z = \frac{\delta}{(\delta + r - \pi)}

    Args:
        delta: array_like, rate of economic depreciation
        bonus: array_like, rate of bonus depreciation
        r: scalar, discount rate
        pi: scalar, inflation rate

    Returns:
        z: array_like, net present value of depreciation deductions for
            $1 of investment

    """
    z = bonus + ((1 - bonus) * (delta / (delta + r - pi)))

    return z


def npv_tax_depr(df, r, pi, land_expensing):
    """
    Depending on the method of depreciation, makes calls to either
    the straight line or declining balance calculations.

    Args:
        df: pandas DataFrame, assets by type and tax treatment
        r: scalar, discount rate
        pi: scalar, inflation rate
        land_expensing: scalar, rate of expensing on land

    Returns:
        z: pandas series, NPV of depreciation deductions for all asset
                types and tax treatments

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
    idx = df['asset_name'] == 'Land'
    df.loc[idx, 'z'] = land_expensing

    z = df['z']

    return z


def eq_coc(delta, z, w, u, inv_tax_credit, pi, r):
    """
    Compute the cost of capital

    ..math::
        \rho = \frac{(r-\pi+\delta)}{1-u(1-uz)+w-\delta

    Args:
        delta: array_like, rate of economic depreciation
        z: array_like, net present value of depreciation deductions for
            $1 of investment
        w: scalar, property tax rate
        u: scalar, statutory marginal tax rate for the first layer of
            income taxes
        inv_tax_credit: scalar, investment tax credit rate
        pi: scalar, inflation rate
        r: scalar, discount rate

    Returns:
        rho: array_like, the cost of capital
    """
    rho = (((r - pi + delta) / (1 - u)) *
           (1 - inv_tax_credit - u * z) + w - delta)

    return rho


def eq_coc_inventory(u, phi, Y_v, pi, r):
    """
    Compute the cost of capital for inventories

    ..math::
        \rho = \phi \rho_{FIFO} + (1-\phi)\rho_{LIFO}

    Args:
        u: scalar, statutory marginal tax rate for the first layer of
            income taxes
        phi: scalar, fraction of inventories that use FIFO accounting
        Y_v: scalar, average number of year inventories are held
        pi: scalar, inflation rate
        r: scalar, discount rate

    Returns:
        rho: scalar, cost of capital for inventories

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
        rho: array_like, cost of capital
        delta: array_like, rate of economic depreciation

    Returns:
        ucc: array_like, the user cost of capital
    """
    ucc = rho + delta

    return ucc


def eq_metr(rho, r_prime, pi):
    """
    Compute the marginal effective tax rate (METR)

    ..math::
        metr = \frac{\rho - (r^{'}-\pi)}{\rho}

    Args:
        rho: array_like, cost of capital
        r_prime: array_like, after-tax rate of return
        pi: scalar, inflation rate

    Returns:
        metr: array_like, METR

    """
    metr = (rho - (r_prime - pi)) / rho

    return metr


def eq_mettr(rho, s):
    """
    Compute the marginal effective total tax rate (METTR)

    ..math::
        mettr = \frac{\rho - s}{\rho}

    Args:
        rho: array_like, cost of capital
        s: array_like, after-tax return on savings

    Returns:
        mettr: array_like, METTR

    """
    mettr = (rho - s) / rho

    return mettr


def eq_tax_wedge(rho, s):
    """
    Compute the tax wedge

    ..math::
        wedge = \rho - s

    Args:
        rho: array_like, cost of capital
        s: array_like, after-tax return on savings

    Returns:
        wedge: array_like, tax wedge

    """
    wedge = rho - s

    return wedge


def eq_eatr(rho, metr, p, u):
    """
    Compute the effective average tax rate (EATR).

    ..math::
        eatr = \left(\frac{p - rho}{p}\right)u +
            \left(\frac{\rho}{p}\right)metr

    Args:
        rho: array_like, cost of capital
        metr: array_like, marginal effective tax rate
        p: scalar, profit rate
        u: scalar, statutory marginal tax rate for the first layer of
            income taxes

    Returns:
        eatr: array_like, EATR
    """
    eatr = ((p - rho) / p) * u + (rho / p) * metr

    return eatr
