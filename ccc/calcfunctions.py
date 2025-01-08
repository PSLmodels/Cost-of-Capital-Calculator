import numpy as np
import pandas as pd
from ccc.constants import TAX_METHODS


def update_depr_methods(df, p, dp):
    """
    Updates depreciation methods per changes from defaults that are
    specified by user.

    Args:
        df (Pandas DataFrame): assets by type and tax treatment
        p (CCC Specifications object): CCC parameters
        dp (CCC DepreciationParams object): asset-specific depreciation
            parameters

    Returns:
        df (Pandas DataFrame): assets by type and tax treatment with
            updated tax depreciation methods

    """
    # update tax_deprec_rates based on user defined parameters
    # create dataframe with depreciation policy parameters for all
    # known years
    deprec_df = dp.expanded_df()
    # keep just the current year in the CCC parameters object
    deprec_df = deprec_df[deprec_df.year == p.year]
    # merge depreciation policy parameters to asset dataframe
    df.drop(columns=deprec_df.keys(), inplace=True, errors="ignore")
    df = df.merge(
        deprec_df, how="left", left_on="bea_asset_code", right_on="BEA_code"
    )
    # add bonus depreciation to tax deprec parameters dataframe
    df["bonus"] = df["life"]
    # update tax_deprec_rates based on user defined parameters
    df.replace({"bonus": p.bonus_deprec}, inplace=True)
    # Compute b
    df["b"] = df["method"]
    df.replace({"b": TAX_METHODS}, regex=True, inplace=True)
    # use b value of 1 if method is not in TAX_METHODS
    # NOTE: not sure why the replae method doesn't work for this method
    # Related: had to comment this out in TAX_METHODS
    df.loc[df["b"] == "Income Forecast", "b"] = 1.0
    # cast b as float
    df["b"] = df["b"].astype(float)
    # Set Y to length of depreciable life
    df["Y"] = df["life"]

    return df


def dbsl(Y, b, bonus, r):
    r"""
    Makes the calculation for the declining balance with a switch to
    straight line (DBSL) method of depreciation.

    .. math::
        z = \frac{\beta}{\beta+r}\left[1-e^{-(\beta+r)Y^{*}}\right]+
            \frac{e^{-\beta Y^{*}}}{(Y-Y^{*})r}
            \left[e^{-rY^{*}}-e^{-rY}\right]

    Args:
        Y (array_like): asset life in years
        b (array_like): scale of declining balance (e.g., b=2 means
            double declining balance)
        bonus (array_like): rate of bonus depreciation
        r (scalar): discount rate

    Returns:
        z (array_like): net present value of depreciation deductions for
            $1 of investment

    """
    beta = b / Y
    Y_star = Y * (1 - (1 / b))
    z = bonus + (
        (1 - bonus)
        * (
            ((beta / (beta + r)) * (1 - np.exp(-1 * (beta + r) * Y_star)))
            + (
                (np.exp(-1 * beta * Y_star) / ((Y - Y_star) * r))
                * (np.exp(-1 * r * Y_star) - np.exp(-1 * r * Y))
            )
        )
    )
    return z


def sl(Y, bonus, r):
    r"""
    Makes the calculation for straight line (SL) method of depreciation.

    .. math::
        z = \frac{1 - e^{-rY}}{Yr}

    Args:
        Y (array_like): asset life in years
        bonus (array_like): rate of bonus depreciation
        r (scalar): discount rate

    Returns:
        z (array_like): net present value of depreciation deductions for
            $1 of investment

    """
    z = bonus + ((1 - bonus) * ((1 - np.exp(-1 * r * Y)) / (r * Y)))
    return z


def econ(delta, bonus, r, pi):
    r"""
    Makes the calculation for the NPV of depreciation deductions using
    economic depreciation rates.

    .. math::
        z = \frac{\delta}{(\delta + r - \pi)}

    Args:
        delta (array_like): rate of economic depreciation
        bonus (array_like): rate of bonus depreciation
        r (scalar): discount rate
        pi (scalar): inflation rate

    Returns:
        z (array_like): net present value of depreciation deductions for
            $1 of investment

    """
    z = bonus + ((1 - bonus) * (delta / (delta + r - pi)))
    return z


def income_forecast(Y, delta, bonus, r):
    r"""
    Makes the calculation for the Income Forecast method.

    The Income Forecast method involved deducting expenses in relation
    to forecasted income over the next 10 years. CCC follows the CBO
    methodology (CBO, 2018:
    https://www.cbo.gov/system/files/2018-11/54648-Intangible_Assets.pdf)
    and approximate this method with the DBSL method, but with a the "b"
    factor determined by economic depreciation rates.

    .. math::
        z = \frac{\beta}{\beta+r}\left[1-e^{-(\beta+r)Y^{*}}\right]+
            \frac{e^{-\beta Y^{*}}}{(Y-Y^{*})r}
            \left[e^{-rY^{*}}-e^{-rY}\right]

    Args:
        Y (array_like): asset life in years
        delta (array_like): rate of economic depreciation
        bonus (array_like): rate of bonus depreciation
        r (scalar): discount rate

    Returns:
        z (array_like): net present value of depreciation deductions for
            $1 of investment

    """
    b = 10 * delta
    beta = b / Y
    Y_star = Y * (1 - (1 / b))
    z = bonus + (
        (1 - bonus)
        * (
            ((beta / (beta + r)) * (1 - np.exp(-1 * (beta + r) * Y_star)))
            + (
                (np.exp(-1 * beta * Y_star) / ((Y - Y_star) * r))
                * (np.exp(-1 * r * Y_star) - np.exp(-1 * r * Y))
            )
        )
    )
    return z


def npv_tax_depr(df, r, pi, land_expensing):
    """
    Depending on the method of depreciation, makes calls to either
    the straight line or declining balance calculations.

    Args:
        df (Pandas DataFrame): assets by type and tax treatment
        r (scalar): discount rate
        pi (scalar): inflation rate
        land_expensing (scalar): rate of expensing on land

    Returns:
        z (Pandas series): NPV of depreciation deductions for all asset
                types and tax treatments

    """
    idx = (df["method"] == "DB 200%") | (df["method"] == "DB 150%")
    df.loc[idx, "z"] = dbsl(
        df.loc[idx, "Y"], df.loc[idx, "b"], df.loc[idx, "bonus"], r
    )
    idx = df["method"] == "SL"
    df.loc[idx, "z"] = sl(df.loc[idx, "Y"], df.loc[idx, "bonus"], r)
    idx = df["method"] == "Economic"
    df.loc[idx, "z"] = econ(df.loc[idx, "delta"], df.loc[idx, "bonus"], r, pi)
    idx = df["method"] == "Income Forecast"
    df.loc[idx, "z"] = income_forecast(
        df.loc[idx, "Y"], df.loc[idx, "delta"], df.loc[idx, "bonus"], r
    )
    idx = df["method"] == "Expensing"
    df.loc[idx, "z"] = 1.0
    idx = df["asset_name"] == "Land"
    df.loc[idx, "z"] = np.squeeze(land_expensing)
    idx = df["asset_name"] == "Inventories"
    df.loc[idx, "z"] = 0.0  # not sure why I have to do this with changes
    z = df["z"]

    return z


def eq_coc(
    delta,
    z,
    w,
    u,
    u_d,
    inv_tax_credit,
    psi,
    nu,
    pi,
    r,
    re_credit=None,
    asset_code=None,
    ind_code=None,
):
    r"""
    Compute the cost of capital

    .. math::
        \rho = \frac{(r-\pi+\delta)}{1-u}(1-u_dz(1-\psi k) - k\nu)+w-\delta

    Args:
        delta (array_like): rate of economic depreciation
        z (array_like): net present value of depreciation deductions for
            $1 of investment
        w (scalar): property tax rate
        u (scalar): marginal tax rate for the first layer of
            income taxes
        u_d (scalar): marginal tax rate on deductions
        inv_tax_credit (scalar): investment tax credit rate
        psi (scalar): fraction investment tax credit that affects
            depreciable basis of the investment
        nu (scalar): NPV of the investment tax credit
        pi (scalar): inflation rate
        r (scalar): discount rate
        re_credit (dict): rate of R&E credit by asset or industry
        asset_code (array_like): asset code
        ind_code (array_like): industry code

    Returns:
        rho (array_like): the cost of capital

    """
    # Initialize re_credit_rate (only needed if arrays are passed in --
    # if not, can include the R&E credit in the inv_tax_credit object)
    if isinstance(delta, np.ndarray):
        re_credit_rate_ind = np.zeros_like(delta)
        re_credit_rate_asset = np.zeros_like(delta)
        # Update by R&E credit rate amounts by industry
        if (ind_code is not None) and (re_credit is not None):
            idx = [
                index
                for index, element in enumerate(ind_code)
                if element in re_credit["By industry"].keys()
            ]
            ind_code_idx = [ind_code[i] for i in idx]
            re_credit_rate_ind[idx] = [
                re_credit["By industry"][ic] for ic in ind_code_idx
            ]
        # Update by R&E credit rate amounts by asset
        if (asset_code is not None) and (re_credit is not None):
            idx = [
                index
                for index, element in enumerate(asset_code)
                if element in re_credit["By asset"].keys()
            ]
            asset_code_idx = [asset_code[i] for i in idx]
            re_credit_rate_asset[idx] = [
                re_credit["By asset"][ac] for ac in asset_code_idx
            ]
        # take the larger of the two R&E credit rates
        inv_tax_credit += np.maximum(re_credit_rate_asset, re_credit_rate_ind)
    rho = (
        ((r - pi + delta) / (1 - u))
        * (1 - inv_tax_credit * nu - u_d * z * (1 - psi * inv_tax_credit))
        + w
        - delta
    )

    return rho


def eq_coc_inventory(u, phi, Y_v, pi, r):
    r"""
    Compute the cost of capital for inventories

    .. math::
        \rho = \phi \rho_{FIFO} + (1-\phi)\rho_{LIFO}

    Args:
        u (scalar): statutory marginal tax rate for the first layer of
            income taxes
        phi (scalar): fraction of inventories that use FIFO accounting
        Y_v (scalar): average number of year inventories are held
        pi (scalar): inflation rate
        r (scalar): discount rate

    Returns:
        rho (scalar): cost of capital for inventories

    """
    rho_FIFO = ((1 / Y_v) * np.log((np.exp(r * Y_v) - u) / (1 - u))) - pi
    rho_LIFO = (1 / Y_v) * np.log((np.exp((r - pi) * Y_v) - u) / (1 - u))
    rho = phi * rho_FIFO + (1 - phi) * rho_LIFO

    return rho


def eq_ucc(rho, delta):
    r"""
    Compute the user cost of capital

    .. math::
        ucc = \rho + \delta

    Args:
        rho (array_like): cost of capital
        delta (array_like): rate of economic depreciation

    Returns:
        ucc (array_like): the user cost of capital

    """
    ucc = rho + delta
    return ucc


def eq_metr(rho, r_prime, pi):
    r"""
    Compute the marginal effective tax rate (METR)

    .. math::
        metr = \frac{\rho - (r^{'}-\pi)}{\rho}

    Args:
        rho (array_like): cost of capital
        r_prime (array_like): after-tax rate of return
        pi (scalar): inflation rate

    Returns:
        metr (array_like): METR

    """
    metr = (rho - (r_prime - pi)) / rho
    return metr


def eq_mettr(rho, s):
    r"""
    Compute the marginal effective total tax rate (METTR)

    .. math::
        mettr = \frac{\rho - s}{\rho}

    Args:
        rho (array_like): cost of capital
        s (array_like): after-tax return on savings

    Returns:
        mettr (array_like): METTR

    """
    mettr = (rho - s) / rho
    return mettr


def eq_tax_wedge(rho, s):
    r"""
    Compute the tax wedge

    .. math::
        wedge = \rho - s

    Args:
        rho (array_like): cost of capital
        s (array_like): after-tax return on savings

    Returns:
        wedge (array_like): tax wedge

    """
    wedge = rho - s
    return wedge


def eq_eatr(rho, metr, p, u):
    r"""
    Compute the effective average tax rate (EATR).

    .. math::
        eatr = \left(\frac{p - rho}{p}\right)u +
            \left(\frac{\rho}{p}\right)metr

    Args:
        rho (array_like): cost of capital
        metr (array_like): marginal effective tax rate
        p (scalar): profit rate
        u (scalar): statutory marginal tax rate for the first layer of
            income taxes

    Returns:
        eatr (array_like): EATR

    """
    eatr = ((p - rho) / p) * u + (rho / p) * metr
    return eatr

def eq_tax_adjusted_q(z, u):
    r"""
    Compute the tax-adjusted q

    .. math::
        tax_adjusted_q = 

    Args:
        z (array_like): net present value of depreciation deductions for
            $1 of investment
        u (scalar): marginal tax rate for the first layer of
            income taxes

    Returns:
        tax_adjusted_q (array_like): TAX_ADJUSTED_Q

    """
    q = 0.5
    tax_adjusted_q = (q - 1 * (1 - z)) / (1 - u)
    return tax_adjusted_q