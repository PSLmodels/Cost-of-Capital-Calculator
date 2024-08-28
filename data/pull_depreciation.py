"""
This model has functions to read in depreciation data
"""

# imports
import numpy as np
import pandas as pd
from data_paths import get_paths

globals().update(get_paths())


def get_depr():
    """
    Reads in the list of assets and their economic depreciation values
    from BEA data and the tax depriation system for each asset type from
    the IRS

    Args:
        None

    Returns:
        econ_deprec_rates (DataFrame): economic depreciation rates for
                           all asset types

    """
    econ_deprec_rates = pd.read_csv(_ECON_DEPR_IN_PATH)
    econ_deprec_rates = econ_deprec_rates.fillna(0)
    econ_deprec_rates.rename(
        columns={
            "Code": "bea_asset_code",
            "Economic Depreciation Rate": "delta",
        },
        inplace=True,
    )
    econ_deprec_rates["Asset"] = econ_deprec_rates["Asset"].str.strip()
    econ_deprec_rates["bea_asset_code"] = econ_deprec_rates[
        "bea_asset_code"
    ].str.strip()

    tax_deprec = pd.read_csv(_TAX_DEPR)
    tax_deprec["Asset Type"] = tax_deprec["Asset Type"].str.strip()

    deprec_rates = tax_deprec.merge(
        econ_deprec_rates,
        how="left",
        left_on=["Asset Type"],
        right_on=["Asset"],
        copy=True,
    )

    return deprec_rates
