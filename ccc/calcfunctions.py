import numpy as np


def dbsl(Y, b, bonus, r):
    """
    Makes the calculation for the declining balance with a switch to
    straight line (DBSL) method of depreciation.

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


def npv_tax_deprec(Y, b, delta, bonus, r, pi, method):
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

    if method == 'dbsl':
        z = dbsl(Y, b, bonus, r)
    elif method == 'sl':
        z = sl(Y, bonus, r)
    elif method == 'econ':
        z = econ(delta, bonus, r, pi)
    elif method == 'expensing':
        z = np.ones(len(Y))
    else:
        err = 'Not a valid depreication method'
        raise RuntimeError(err)

    return z


def cost_of_capital(delta, z, w, expense_inventory, u, inv_credit, phi,
                    Y_v, pi, r):
    """
    Compute the cost of capital

    Args:
        df: DataFrame, assets by type with depreciation rates
        w: scalar, property tax rate
        expense_inventory: boolean, whether inventories are expensed
        stat_tax: Numpy array, entity level taxes for corp and noncorp
        inv_credit: scalar, investment tax credit
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
    if not expense_inventory:
        rho_FIFO = (((1 / Y_v) * np.log((np.exp(r * Y_v) - u) /
                                        (1 - u))) - pi)
        rho_LIFO = ((1 / Y_v) * np.log((np.exp((r - pi) * Y_v) - u) /
                                       (1 - u)))
        rho = phi * rho_FIFO + (1 - phi) * rho_LIFO
    else:
        rho = (((r - pi + delta) / (1 - u)) * (1 - inv_credit - u * z) +
               w - delta)

    return rho


def ucc(rho, delta):
    """
    Compute the user cost of capital
    """
    ucc = rho + delta

    return ucc


def metr(rho, r_prime, pi):
    """
    Compute the marginal effective tax rate (METR)

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


def mettr(rho, s):
    """
    Compute the marginal effective total tax rate (METTR)

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


def tax_wedge(rho, s):
    """
    Compute the tax wedge

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


def eatr(rho, metr, profit_rate, u):
    """
    Compute the effective average tax rate (EATR)

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
