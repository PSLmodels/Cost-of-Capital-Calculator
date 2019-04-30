import os


def get_paths():
    """
    Function to define constants that contain strings with paths to the
    various datafiles Cost-of-Capital-Calculator relies on.

    Args:
        None

    Returns:
        paths: list, list of strings that are the paths to data
    """
    paths = {}
    _CUR_DIR = _MAIN_DIR = os.path.dirname(os.path.abspath(__file__))
    _DATA_DIR = _MAIN_DIR
    paths['_CUR_DIR'] = _CUR_DIR
    paths['_MAIN_DIR'] = paths['_DATA_DIR'] = _MAIN_DIR
    paths['_RATE_DIR'] = os.path.join(_DATA_DIR, 'depreciation_rates')
    paths['_REF_DIR'] = os.path.join(_DATA_DIR, 'reference_data')
    paths['_RAW_DIR'] = _RAW_DIR = os.path.join(_DATA_DIR, 'raw_data')
    paths['_DEPR_DIR'] = _DEPR_DIR = os.path.join(_DATA_DIR,
                                                  'depreciation_rates')
    paths['_BEA_DIR'] = _BEA_DIR = os.path.join(_RAW_DIR, 'BEA')
    paths['_FIN_ACCT_DIR'] = _FIN_ACCT_DIR =\
        os.path.join(_RAW_DIR, 'national_accounts')
    paths['_BEA_ASSET_PATH'] = os.path.join(_BEA_DIR,
                                            "detailnonres_stk1.xlsx")
    paths['_SOI_BEA_CROSS'] = os.path.join(_BEA_DIR,
                                           'soi_bea_industry_codes.csv')
    paths['_BEA_INV'] = os.path.join(_BEA_DIR, 'NIPA_5.8.5B.xls')
    paths['_BEA_RES'] = os.path.join(_BEA_DIR,
                                     'BEA_StdFixedAsset_Table5.1.xls')
    paths['_LAND_PATH'] = os.path.join(_FIN_ACCT_DIR, '')
    paths['_B101_PATH'] = os.path.join(_FIN_ACCT_DIR, 'b101.csv')
    paths['_ECON_DEPR_IN_PATH'] = os.path.join(
        _DEPR_DIR, 'Economic Depreciation Rates.csv')
    paths['_TAX_DEPR'] = os.path.join(_DEPR_DIR,
                                      'tax_depreciation_rates.csv')
    paths['_SOI_DIR'] = _SOI_DIR = os.path.join(_RAW_DIR, 'soi')
    paths['_CORP_DIR'] = _CORP_DIR = os.path.join(_SOI_DIR, 'soi_corporate')
    paths['_TOT_CORP_IN_PATH'] = os.path.join(_CORP_DIR, '2013sb1.csv')
    paths['_S_CORP_IN_PATH'] = os.path.join(_CORP_DIR, '2013sb3.csv')
    paths['_PRT_DIR'] = _PRT_DIR = os.path.join(_SOI_DIR, 'soi_partner')
    paths['_DETAIL_PART_CROSS_PATH'] = os.path.join(
        _PRT_DIR, 'partner_crosswalk_detailed_industries.csv')
    paths['_INC_FILE'] = os.path.join(_PRT_DIR, '13pa01.xls')
    paths['_AST_FILE'] = os.path.join(_PRT_DIR, '13pa03.xls')
    paths['_TYP_IN_CROSS_PATH'] = os.path.join(_PRT_DIR,
                                               '13pa05_Crosswalk.csv')
    paths['_TYP_FILE'] = os.path.join(_PRT_DIR, '13pa05.xls')
    paths['_PROP_DIR'] = _PROP_DIR = os.path.join(_SOI_DIR,
                                                  'soi_proprietorship')
    paths['_PRT_DIR'] = _PRT_DIR = os.path.join(_SOI_DIR, 'soi_partner')
    paths['_NFARM_PATH'] = os.path.join(_PROP_DIR, '13sp01br.xls')
    paths['_NFARM_INV'] = os.path.join(_PROP_DIR, '13sp02is.xls')
    paths['_FARM_IN_PATH'] = os.path.join(_PROP_DIR, 'farm_data.csv')
    paths['_DETAIL_SOLE_PROP_CROSS_PATH'] = os.path.join(
        _PROP_DIR, 'detail_sole_prop_crosswalk.csv')
    paths['_SOI_CODES'] = os.path.join(_SOI_DIR, 'SOI_codes.csv')

    return paths
