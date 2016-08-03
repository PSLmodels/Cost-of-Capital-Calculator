"""
Fixed Asset Breakdown (read_bea.py):
-------------------------------------------------------------------------------

Using the BEA data spreadsheet fixed assets are allocated to several different industries.
Based on the SOI data the fixed asset data is divided into both corporate and non-corporate entitities.
Because of discrepancies in the BEA classifications, NAICS classifications, and the SOI classifications,
several different crosswalks are used to match the data. The majority of the script takes these crosswalks
and creates dictionaries to map the codes. Last updated 7/27/2016
"""
# Packages:
import os.path
import numpy as np
import pandas as pd
import xlrd

# Directories:
globals().update(get_paths())

# Constant factors:
_BEA_IN_FILE_FCTR = 10**6
_START_POS = 8
_SKIP1 = 47
_SKIP2 = 80
_CORP_PRT = [1,2]
_NCORP_PRT = [3,4,5,6,7,8,9,10]

def read_bea(entity_dfs):
    """Opens the BEA workbook and pulls out the asset info

        :param entity_dfs: Contains all the soi data by entity type
        :type entity_dfs: dictionary
        :returns: Fixed asset data organized by industry, entity, and asset type
        :rtype: dictionary
    """
    # Opening BEA's excel file on depreciable assets by industry:
    bea_book = xlrd.open_workbook(_BEA_ASSET_PATH)
    sht_names = bea_book.sheet_names()
    num_shts = bea_book.nsheets
    # Opening the BEA crosswalk and converting it to a dictionary
    bea_cross = pd.read_csv(_BEA_CROSS)
    bea_cross = bea_cross.set_index('BEA').to_dict()['NAICS']
    for k, v in bea_cross.iteritems():
        if '.' in v:
            ind_list = v.split('.')
            bea_cross[k] = ind_list
        else:
            bea_cross[k] = [v]
    # Specifying the corp and non-corp entity breakdown
    corp_tax_entity = ['c_corp','corp_gen', 'corp_lim']
    non_corp_entity = ['indv_gen', 'indv_lim', 'prt_gen',
     'prt_lim', 'tax_gen', 'tax_lim', 'nom_gen', 'nom_lim', 'sole_prop']
    entities = corp_tax_entity + non_corp_entity
    # Opening the crosswalk that maps SOI codes to BEA codes
    bea_soi_cross = pd.read_csv(_SOI_CROSS)
    soi_codes = bea_soi_cross['SOI Codes'].tolist()
    # Formatting the soi data to combine industries that are grouped in the crosswalk
    # First the industries are all given the same code
    for i in xrange(0,len(soi_codes)):
        if isinstance(soi_codes[i], float):
            continue
        if ',' in soi_codes[i]:
            code_list = soi_codes[i].split(', ')
            for entity in entities:
                df = entity_dfs[entity]
                for code in code_list:
                   df.replace(float(code), soi_codes[i], inplace=True)

    # Second the industries with identical codes are summed together
    for entity in entities:
        df = entity_dfs[entity]
        df = df.groupby('Codes:',sort=False).sum()
        codes = df.index.tolist()
        df.insert(0,'Codes:', codes)
        df.index = np.arange(0,len(df))
        entity_dfs[entity] = df

    # For each different industry the ratio of corp fixed assets and non-corp fixed assets are calculated
    ratios = []
    for i in xrange(0,len(entity_dfs['c_corp'])):
        corp_fa = 0
        non_corp_fa = 0
        # Iterates over each entity and produces a sum
        for entity in corp_tax_entity:
            corp_fa += entity_dfs[entity]['FA'][i]
        for entity in non_corp_entity:
            non_corp_fa += entity_dfs[entity]['FA'][i]
        total_fa = non_corp_fa + corp_fa
        if(total_fa != 0):
            corp_ratio = corp_fa / total_fa
            non_corp_ratio = non_corp_fa / total_fa
            ratios.append((entity_dfs['corp_gen']['Codes:'][i],corp_ratio, non_corp_ratio))
    # The results of the corp and non-corp ratio calculations are stored in a dataframe
    rate_df = pd.DataFrame(ratios, index = np.arange(0,len(ratios)), columns = ['Codes:', 'corp', 'non_corp'])

    # Creates tuples that are one to one matches of NAICS codes to SOI codes
    cross_dict = {}
    for i in xrange(0, len(bea_soi_cross)):
        bea_code = str(bea_soi_cross.iloc[i]['BEA CODE'])
        if bea_code == 'nan':
            continue

        elif '-' not in bea_code:
            naics_code = bea_soi_cross.iloc[i]['2007 NAICS Codes']
            soi_codes = bea_soi_cross.iloc[i]['SOI Codes']
            # Maps the BEA inudstry code to these tuples
            cross_dict[bea_code] = (naics_code, soi_codes)

    rates = rate_df.to_dict()
    codes = rate_df.to_dict()['Codes:']
    # Creates a dictionary of SOI codes to NAICS codes
    code_dict={}
    for y,x in codes.iteritems():
        if isinstance(x, float):
            code_dict[str(int(x))] = y
        else:
            code_dict[x] = y
    # Iterates over columns in each spreadsheet and loads in the fixed asset information
    total_fa={}
    for sheet in bea_book.sheets():
        if(sheet.name != 'readme' and sheet.name != 'Datasets'):
            code = sheet.cell_value(0,0).encode('ascii','ignore').partition(' ')[0]
            asst_vals = []
            for index in xrange(_START_POS, sheet.nrows):
                if(index != _SKIP1 and index != _SKIP2):
                    asst_vals.append(sheet.cell_value(index, sheet.ncols-1)*_BEA_IN_FILE_FCTR)
            key = cross_dict[code][1]
            key1 = code_dict[key]
            # Using the SOI dictionary the correct ratio is taken from the rate df and used in the calculation
            corp_asst_vals = np.array(asst_vals) * rates['corp'][key1]
            non_corp_vals = np.array(asst_vals) * rates['non_corp'][key1]
            # Creates a dictionary that maps the NAICS code to a 2x96 array
            ind_fa = {cross_dict[code][0]: np.array([corp_asst_vals, non_corp_vals])}
            # Stores the values in a dictionary {industry code: fixed asset arrays}
            total_fa.update(ind_fa)

    return total_fa
