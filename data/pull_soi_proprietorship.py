"""
SOI Proprietorship Data (pull_soi_partner.py):
------------------------------------------------------------------------
Module that handles reading in the soi proprietorship data. Because no
fixed asset and land data is available for sole props, the depreciation
deduction is used along with the partner data. The ratio of land and
fixed assets to the depreciation deduction for partners is used to
impute the data for sole props. The sole prop inventory and farm data
is also loaded in.
"""

import re
import numpy as np
import pandas as pd
from ccc.utils import to_str
import pull_soi_partner as prt
from data_paths import get_paths

globals().update(get_paths())

_DDCT_FILE_FCTR = 10**3


def load_proprietorship_data(entity_dfs):
    """
    Using the partnership and sole prop data, the capital stock data is
    imputed.

    Args:
        entity_dfs (dictioinary): Dictionary of DataFrames of SOI data
            by industry

    Returns:
        data (dictionary): Dictionary with a DataFrame of SOI sole prop
            capital stock data organized by industry
    """

    # Opening data on depreciable fixed assets, inventories, and land
    # for non-farm sole props
    nonfarm_df = format_dataframe(
        pd.read_excel(_NFARM_PATH, skiprows=2, skipfooter=8)
    )
    # Cuts off the repeated columns so only the data for all sole props
    # remains
    nonfarm_df = nonfarm_df.T.groupby(sort=False, level=0).first().T
    # Fixing the index labels of the new dataframe
    nonfarm_df.reset_index(inplace=True, drop=True)
    # Keep only variables of interest
    nonfarm_df = nonfarm_df[["Industry", "Depreciation deduction [1,2]"]]
    nonfarm_df["Industry"] = nonfarm_df["Industry"].apply(
        lambda x: re.sub(r"[\s+]", "", x)
    )
    nonfarm_df.rename(
        columns={
            "Industry": "Item",
            "Depreciation deduction [1,2]": "Depreciation",
        },
        inplace=True,
    )

    # Opens the nonfarm inventory data
    nonfarm_inv = prt.format_excel(
        pd.read_excel(_NFARM_INV, skiprows=1, skipfooter=8)
    )
    # Cuts off the repeated columns so only the data for all sole props remains
    nonfarm_inv = nonfarm_inv.T.groupby(sort=False, level=0).first().T
    nonfarm_inv.columns = [to_str(c) for c in nonfarm_inv.columns]
    # Fixing the index labels of the new dataframe
    nonfarm_inv.reset_index(inplace=True, drop=True)
    # Keep only variables of interest
    nonfarm_inv = nonfarm_inv[
        ["Net income status, item", "Inventory, end of year"]
    ]
    nonfarm_inv["Net income status, item"] = nonfarm_inv[
        "Net income status, item"
    ].str.strip()
    nonfarm_inv.rename(
        columns={
            "Net income status, item": "Item",
            "Inventory, end of year": "Inventories",
        },
        inplace=True,
    )
    nonfarm_inv["Item"] = nonfarm_inv["Item"].apply(
        lambda x: re.sub(r"[\s+]", "", x)
    )
    # merge together two sole prop data sources
    # have to manually fix a couple names to be compatible
    nonfarm_df.loc[
        nonfarm_df["Item"]
        == "Otherambulatoryhealthcareservices(includingambulanceservices,bloodandorganbanks)",
        "Item",
    ] = "Otherambulatoryhealthcareservices(includingambulanceservices,blood,organbanks)"
    nonfarm_df.loc[
        nonfarm_df["Item"]
        == "Officesofrealestateagents,brokers,propertymanagers,andappraisers",
        "Item",
    ] = "Officesofrealestateagents,brokers,propertymanagersandappraisers"
    nonfarm_df.loc[
        nonfarm_df["Item"]
        == "OOtherautorepairandmaintenance(includingoilchange,lubrication,andcarwashes)",
        "Item",
    ] = "Otherautorepairandmaintenance(includingoilchange,lube,andcarwashes)"
    nonfarm_df = nonfarm_df.merge(
        nonfarm_inv, how="inner", on=["Item"], copy=True
    )

    # read in crosswalk for these data
    xwalk = pd.read_csv(_DETAIL_SOLE_PROP_CROSS_PATH)
    # keep only codes that help to identify complete industries
    xwalk = xwalk[xwalk["complete"] == 1]
    xwalk = xwalk[["Industry", "INDY_CD"]]
    xwalk["Industry"] = xwalk["Industry"].apply(
        lambda x: re.sub(r"[\s+]", "", x)
    )

    # merge industry codes to sole prop data
    nonfarm_df = nonfarm_df.merge(
        xwalk, how="inner", left_on=["Item"], right_on=["Industry"], copy=True
    )
    nonfarm_df.drop(["Item", "Industry"], axis=1, inplace=True)

    # Sums together the repeated codes into one industry
    nonfarm_df = nonfarm_df.groupby("INDY_CD", sort=False).sum()
    nonfarm_df.reset_index(inplace=True)

    # add some rows for industry codes not in the sole prop data because
    # they are zero
    df = pd.DataFrame(columns=("INDY_CD", "Depreciation", "Inventories"))
    missing_code_list = [
        312,
        517,
        519,
        524140,
        524142,
        524143,
        524156,
        524159,
        55,
        521,
        525,
        531115,
    ]
    for i in range(len(missing_code_list)):
        df.loc[i] = [int(missing_code_list[i]), 0.0, 0.0]
    nonfarm_df = (
        nonfarm_df.append(df, sort=True, ignore_index=True)
        .copy()
        .reset_index()
    )

    # attribute over a minor industry only idenfified in w/ other minor
    # ind in SOI
    nonfarm_df.loc[nonfarm_df["INDY_CD"] == 531115, "Depreciation"] = (
        nonfarm_df.loc[nonfarm_df["INDY_CD"] == 531135, "Depreciation"].values
        * 0.5
    )
    nonfarm_df.loc[nonfarm_df["INDY_CD"] == 531115, "Inventories"] = (
        nonfarm_df.loc[nonfarm_df["INDY_CD"] == 531135, "Inventories"].values
        * 0.5
    )
    nonfarm_df.loc[nonfarm_df["INDY_CD"] == 531135, "Depreciation"] = (
        nonfarm_df.loc[nonfarm_df["INDY_CD"] == 531135, "Depreciation"].values
        * 0.5
    )
    nonfarm_df.loc[nonfarm_df["INDY_CD"] == 531135, "Inventories"] = (
        nonfarm_df.loc[nonfarm_df["INDY_CD"] == 531135, "Inventories"].values
        * 0.5
    )

    # create ratios for minor industry assets using corporate data
    # read in crosswalk for bea and soi industry codes
    soi_bea_ind_codes = pd.read_csv(
        _SOI_BEA_CROSS, dtype={"bea_ind_code": str}
    )
    soi_bea_ind_codes.drop("notes", axis=1, inplace=True)
    # drop one repeated minor ind code in crosswalk
    soi_bea_ind_codes.drop_duplicates(subset=["minor_code_alt"], inplace=True)

    # merge codes to sole prop data
    # likely better way to do this...
    nonfarm_sector = nonfarm_df[
        (nonfarm_df["INDY_CD"] > 9) & (nonfarm_df["INDY_CD"] < 100)
    ]
    nonfarm_major = nonfarm_df[
        (nonfarm_df["INDY_CD"] > 99) & (nonfarm_df["INDY_CD"] < 1000)
    ]
    nonfarm_minor = nonfarm_df[
        (nonfarm_df["INDY_CD"] > 99999) & (nonfarm_df["INDY_CD"] < 1000000)
    ]
    sector_df = nonfarm_sector.merge(
        soi_bea_ind_codes,
        how="inner",
        left_on=["INDY_CD"],
        right_on=["sector_code"],
        copy=True,
        indicator=True,
    )
    major_df = nonfarm_major.merge(
        soi_bea_ind_codes,
        how="inner",
        left_on=["INDY_CD"],
        right_on=["major_code"],
        copy=True,
        indicator=True,
    )
    minor_df = nonfarm_minor.merge(
        soi_bea_ind_codes,
        how="inner",
        left_on=["INDY_CD"],
        right_on=["minor_code"],
        copy=True,
        indicator=True,
    )
    nonfarm_data = (
        sector_df.append([major_df, minor_df], sort=True, ignore_index=True)
        .copy()
        .reset_index()
    )
    nonfarm_data.drop(
        ["bea_inv_name", "bea_code", "_merge"], axis=1, inplace=True
    )

    # merge codes to total part data
    # inner join means that we keep only rows that match in both datasets
    # this should keep only unique soi minor industries
    columns = ["Inventories", "Depreciation"]
    part_data = entity_dfs["part_data"][
        ["minor_code_alt", "part_type"] + columns + ["Land", "Fixed Assets"]
    ].copy()

    # sum at industry-partner type level
    part_data = part_data.groupby(["minor_code_alt"]).sum().reset_index()
    part2 = part_data[["minor_code_alt"] + columns].copy()
    partner = part2.merge(
        soi_bea_ind_codes,
        how="inner",
        on=["minor_code_alt"],
        suffixes=("_x", "_y"),
        copy=True,
    )

    for var in columns:
        partner[var + "_ratio"] = partner.groupby(["major_code"])[var].apply(
            lambda x: x / float(x.sum())
        )

    partner.drop(
        ["bea_inv_name", "bea_code", "sector_code", "minor_code"] + columns,
        axis=1,
        inplace=True,
    )
    # merge these ratios to the sole prop data
    nonfarm = nonfarm_data.merge(
        partner,
        how="right",
        on=["minor_code_alt"],
        suffixes=("_x", "_y"),
        copy=True,
        indicator=True,
    )
    # filling in missing values.  This works ok now but need to be
    # careful as the ratio value could cause problems
    nonfarm["Inventories"].fillna(value=0.0, axis=0, inplace=True)
    nonfarm["Inventories_ratio"].fillna(value=1.0, axis=0, inplace=True)

    # allocate capital based on ratios
    for var in columns:
        nonfarm.loc[nonfarm["INDY_CD"] > 99999, var + "_ratio"] = 1.0
        nonfarm[var] = nonfarm[var] * nonfarm[var + "_ratio"]

    nonfarm.drop(list(x + "_ratio" for x in columns), axis=1, inplace=True)
    nonfarm.drop(
        [
            "index",
            "sector_code",
            "major_code_x",
            "minor_code",
            "major_code_y",
            "_merge",
        ],
        axis=1,
        inplace=True,
    )

    # data here totals out for allocable industries (so doesn't hit
    # SOI totals for all industries bc some not allocated to an industry)

    # merge in partner data to get ratios need to impute FA's and land
    part_ratios = part_data[
        ["minor_code_alt", "Fixed Assets", "Depreciation", "Land"]
    ].copy()
    part_ratios["FA_ratio"] = (
        part_ratios["Fixed Assets"] / part_ratios["Depreciation"]
    )
    part_ratios["Land_ratio"] = (
        part_ratios["Land"] / part_ratios["Fixed Assets"]
    )
    part_ratios = part_ratios[["minor_code_alt", "FA_ratio", "Land_ratio"]]
    nonfarm = nonfarm.merge(
        part_ratios,
        how="inner",
        on=["minor_code_alt"],
        suffixes=("_x", "_y"),
        copy=True,
        indicator=False,
    )

    # need to find ratio of assets from BEA to SOI
    bea_ratio = 1.0
    nonfarm["Fixed Assets"] = (
        nonfarm["FA_ratio"] * nonfarm["Depreciation"] * bea_ratio
    )
    nonfarm["Land"] = nonfarm["Land_ratio"] * nonfarm["Fixed Assets"]
    nonfarm.drop(["Land_ratio", "FA_ratio"], axis=1, inplace=True)

    # Calculates the FA and Land for Farm sole proprietorships.
    # Note: we should update so read in raw Census of Agriculture
    # What about inventories for farm sole props? Worry about??
    farm_df = pd.read_csv(_FARM_IN_PATH)
    asst_land = farm_df["R_p"][0] + farm_df["Q_p"][0]
    land_ratio = np.array(
        (
            part_data.loc[part_data["minor_code_alt"] == 111, "Land"]
            / (
                part_data.loc[
                    part_data["minor_code_alt"] == 111, "Fixed Assets"
                ]
                + part_data.loc[part_data["minor_code_alt"] == 111, "Land"]
            )
        )
    )
    part_land = land_ratio * asst_land
    sp_farm_land = farm_df["A_sp"][0] * part_land / farm_df["A_p"][0]
    sp_farm_assts = farm_df["R_sp"][0] + farm_df["Q_sp"][0] - sp_farm_land
    sp_farm_cstock = np.array([sp_farm_assts, 0, sp_farm_land])

    # Adds farm data to industry 111
    nonfarm.loc[nonfarm["INDY_CD"] == 111, "Fixed Assets"] += sp_farm_cstock[0]
    nonfarm.loc[nonfarm["INDY_CD"] == 111, "Land"] += sp_farm_cstock[2]

    # Creates the dictionary of sector : dataframe that is returned and
    # used to update entity_dfs
    data = {"sole_prop_data": nonfarm}

    return data


def format_columns(nonfarm_df):
    """
    Removes extra characters from the columns of the dataframe

    Args:
        nonfarm_df (DataFrame): nonfarm sole prop capital stock data

    Returns:
        nonfarm_df (DataFrame): formatted nonfarm sole prop capital
            stock data
    """
    columns = nonfarm_df.columns.tolist()
    for i in range(0, len(columns)):
        column = columns[i]
        if ".1" in column:
            column = column[:-2]
        if "\n" in column:
            column = column.replace("\n", " ").replace("\r", "")
        column = column.rstrip()
        columns[i] = column
    nonfarm_df.columns = columns
    return nonfarm_df


def format_dataframe(nonfarm_df):
    """
    Fixes the column headers, drops the unnecessary rows, inserts the
    SOI codes and multiplies by a factor of a thousand

    Args:
        nonfarm_df (DataFrame): nonfarm sole prop capital stock data

    Returns:
        nonfarm_df (DataFrame): formatted nonfarm sole prop capital
            stock data
    """

    # Creates a list from the first row of the dataframe
    columns = nonfarm_df.iloc[0].tolist()
    # Replaces the first item in the list with a new label
    columns[0] = "Industry"
    # Sets the values of the columns on the dataframes
    nonfarm_df.columns = list(to_str(x).replace("\n", " ") for x in columns)
    # Drops the first couple of rows and last row in the dataframe
    nonfarm_df.dropna(inplace=True)
    # Multiplies each value in the dataframe by a factor of 1000
    nonfarm_df.iloc[:, 1:] = nonfarm_df.iloc[:, 1:] * _DDCT_FILE_FCTR
    # Resets the index values to a normal range after some have been dropped
    nonfarm_df.reset_index(inplace=True, drop=True)

    return nonfarm_df
