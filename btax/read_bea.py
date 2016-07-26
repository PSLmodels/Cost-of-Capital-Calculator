'''
Fixed Asset Breakdown (read_bea.py):
-------------------------------------------------------------------------------
Last updated 7/1/2015

For each NAICS code, this module creates a breakdown of the fixed assets onto
a level of detail close to the IRS 946. The IRS 946 assigns different tax
depreciation rates for the various fixed asset categories. The module uses
BEA fixed asset data as well as preprocessed SOI Tax data given as input.
'''
# Packages:
import os.path
import numpy as np
import pandas as pd
import xlrd
# Directories:
_CUR_DIR = os.path.dirname(__file__)
_MAIN_DIR = os.path.dirname(_CUR_DIR)
_DATA_DIR = os.path.abspath(_CUR_DIR + '//data' + '//raw_data')
_BEA_DIR = os.path.join(_DATA_DIR, 'BEA') # Directory with BEA data.
# Full file paths:
_BEA_ASSET_PATH = os.path.join(_BEA_DIR, "detailnonres_stk1.xlsx")
_BEA_CROSS = os.path.join(_BEA_DIR, 'BEA_Crosswalk.csv')
_SOI_CROSS = os.path.join(_BEA_DIR, 'NAICS_SOI_crosswalk.csv')
# Constant factors:
_BEA_IN_FILE_FCTR = 10**6
_START_POS = 8
_SKIP1 = 47
_SKIP2 = 80
_CORP_PRT = [1,2]
_NCORP_PRT = [3,4,5,6,7,8,9,10]
'''
Reads in the detailnonres_stk1.xlsx BEA file:
'''
def read_bea(sector_dfs):
    # Opening BEA's excel file on depreciable assets by industry:

    bea_book = xlrd.open_workbook(_BEA_ASSET_PATH)
    sht_names = bea_book.sheet_names()
    num_shts = bea_book.nsheets
    bea_cross = pd.read_csv(_BEA_CROSS)
    bea_cross = bea_cross.set_index('BEA').to_dict()['NAICS']
    for k, v in bea_cross.iteritems():
        if '.' in v:
            ind_list = v.split('.')
            bea_cross[k] = ind_list
        else:
            bea_cross[k] = [v]
    bea_data = []

    corp_tax_entity = ['c_corp','corp_gen', 'corp_lim']
    non_corp_entity = ['indv_gen', 'indv_lim', 'prt_gen',
     'prt_lim', 'tax_gen', 'tax_lim', 'nom_gen', 'nom_lim', 'sole_prop']
    entities = corp_tax_entity + non_corp_entity
    bea_soi_cross = pd.read_csv(_SOI_CROSS)
    soi_codes = bea_soi_cross['SOI Codes'].tolist()
    for i in xrange(0,len(soi_codes)):
        if isinstance(soi_codes[i], float):
            continue
        if ',' in soi_codes[i]:
            code_list = soi_codes[i].split(', ')
            for entity in entities:
                df = sector_dfs[entity]
                for code in code_list:
                   df.replace(float(code), soi_codes[i], inplace=True)
              
    for entity in entities:
        df = sector_dfs[entity]
        df = df.groupby('Codes:',sort=False).sum()
        codes = df.index.tolist()
        df.insert(0,'Codes:', codes)
        df.index = np.arange(0,len(df))
        sector_dfs[entity] = df
             
    ratios = []
    for i in xrange(0,len(sector_dfs['c_corp'])):
        corp_fa = 0
        non_corp_fa = 0
        for entity in corp_tax_entity:
            corp_fa += sector_dfs[entity]['FA'][i]
        for entity in non_corp_entity:
            non_corp_fa += sector_dfs[entity]['FA'][i]
        total_fa = non_corp_fa + corp_fa
        if(total_fa != 0):    
            corp_ratio = corp_fa / total_fa
            non_corp_ratio = non_corp_fa / total_fa
            ratios.append((sector_dfs['corp_gen']['Codes:'][i],corp_ratio, non_corp_ratio))
    rate_df = pd.DataFrame(ratios, index = np.arange(0,len(ratios)), columns = ['Codes:', 'corp', 'non_corp'])

    cross_dict = {}
    for i in xrange(0, len(bea_soi_cross)):
        bea_code = str(bea_soi_cross.iloc[i]['BEA CODE'])
        if bea_code == 'nan':
            continue

        elif '-' not in bea_code:
            naics_code = bea_soi_cross.iloc[i]['2007 NAICS Codes']
            soi_codes = bea_soi_cross.iloc[i]['SOI Codes']
            cross_dict[bea_code] = (naics_code, soi_codes)

    rates = rate_df.to_dict()
    codes = rate_df.to_dict()['Codes:']
    code_dict={}
    for y,x in codes.iteritems():
        if isinstance(x, float):
            code_dict[str(int(x))] = y
        else:
            code_dict[x] = y
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
            corp_asst_vals = np.array(asst_vals) * rates['corp'][key1]
            non_corp_vals = np.array(asst_vals) * rates['non_corp'][key1]
            ind_fa = {cross_dict[code][0]: np.array([corp_asst_vals, non_corp_vals])}
            total_fa.update(ind_fa)
    return total_fa
    '''
    # Opening "readme" sheet:
    try:
        bea_readme = bea_book.sheet_by_name("readme")
    except xlrd.XLRDError:
        bea_readme = bea_book.sheet_by_index(0)
    # Finding relevant positions in the readme sheet:
    sht_pos = naics.search_ws(bea_readme, "Industry Title", 25, False)
    if(sht_pos == [-1,-1]):
        sht_pos = naics.search_ws(bea_readme, "bea code", 25, False, [0,0], True)
        sht_pos[1] = sht_pos[1] - 1
    if(sht_pos == [-1,-1]):
        print "Error in reading BEA fixed asset \"readme\" sheet."
        return None
    cur_row = sht_pos[0] + 1
    cur_col = sht_pos[1]
    # Finding the number of industries (includes those without bea codes):
    number_of_industries = 0
    while cur_row < bea_readme.nrows:
        #if(str(bea_readme.cell_value(cur_row, cur_col)) != ""):
        if(unicode(bea_readme.cell_value(cur_row, cur_col)).encode('utf8') != ""):    
       # for rownum in xrange(sh.nrows):
    #wr.writerow([unicode(c).encode('utf8') for c in sh.row_values(rownum)])    
            number_of_industries += 1
        cur_row += 1
    # Making a list of BEA codes based on the names of the worksheets:
    bea_codes1 = np.zeros(num_shts-1, dtype=object)
    for index in xrange(1, num_shts):
        bea_codes1[index-1] = str(sht_names[index])
    # Making a list of BEA codes based on info in the readme sheet:
    code_index = 0
    cur_row = sht_pos[0] + 1
    cur_col = sht_pos[1]
    bea_codes2 = np.zeros(number_of_industries, dtype=object)
    while cur_row < bea_readme.nrows:
        if(unicode(bea_readme.cell_value(cur_row, cur_col)).encode('utf8') != ""):
            cur_code = str(bea_readme.cell_value(cur_row, cur_col+1))
            cur_code = cur_code.replace("\xa0", " ").strip()
            bea_codes2[code_index] = cur_code
            code_index += 1
        cur_row += 1
    # Reading in a list of the assets in the BEA file:
    list_file = os.path.join(_BEA_DIR, "detailnonres_list.csv")
    asset_list = pd.read_csv(list_file)
    for i in xrange(0, asset_list.shape[0]):
        asset_list.iloc[i,0] = asset_list.iloc[i,0].replace("\xa0", " ")
        asset_list.iloc[i,0] = asset_list.iloc[i,0].strip()
    # Reading in the corresponding naics codes:
    naics_file = os.path.join(_BEA_DIR, "detailnonres_naics.csv")
    naics_cross = pd.read_csv(naics_file).replace("\xa0", " ")
    naics_inds = naics_cross["Industry"]
    for i in xrange(0, naics_cross.shape[0]):
        naics_inds[i] = naics_inds[i].replace("\xa0", " ").strip()
    # Creating a chart cross-referencing industry names, BEA and NAICS codes.
    chart_cols = ["Industry","BEA Code","NAICS Code"]
    bea_chart = pd.DataFrame(np.zeros(shape=(num_shts-2,3), dtype=object),
                             columns = chart_cols)
    bea_inds = bea_chart["Industry"]
    bea_naics = bea_chart["NAICS Code"]
    cur_row = sht_pos[0] + 1
    cur_col = sht_pos[1]
    num_naics = naics_cross.shape[0]
    # Filling chart with naics codes that are in both lists and the crosswalk:
    naics_counter = 0
    #for i in range(0, num_shts-2):
    i = 0
    for cur_row in range(sht_pos[0]+1, bea_readme.nrows):
        bea_code = unicode(bea_readme.cell_value(cur_row,cur_col+1)).encode('utf8')
        if(str(bea_codes1[i]) == bea_code):
            bea_ind = unicode(bea_readme.cell_value(cur_row,cur_col)).encode('utf8')
            bea_ind = bea_ind.replace('\xa0', ' ').strip()
            bea_ind = bea_ind.replace('\xc2', '').strip()
            bea_inds[i] = bea_ind
            bea_chart["BEA Code"][i] = bea_code
            for k in xrange(0, num_naics):
                naics_counter = (naics_counter+1) % num_naics
                if(naics_inds[naics_counter] == bea_chart["Industry"][i]):
                   bea_naics[i] = naics_cross["NAICS"][naics_counter]
                   i += 1
                   break
        # If they match except one has ".0" at the end:
        elif(str(bea_codes1[i]) == str(bea_readme.cell_value(cur_row, cur_col+1))[:-2]):
            bea_ind = unicode(bea_readme.cell_value(cur_row,cur_col)).encode('utf8')
            bea_ind = bea_ind.replace('\xa0', ' ').strip()
            bea_ind = bea_ind.replace('\xc2', '').strip()
            bea_chart["Industry"][i] = bea_ind
            cur_code = str(bea_readme.cell_value(cur_row, cur_col+1))[:-2]
            bea_chart["BEA Code"][i] = cur_code
            for k in xrange(0, num_naics):
                naics_counter = (naics_counter+1) % num_naics
                if(naics_inds[naics_counter] == bea_inds[i]):
                    bea_naics[i] = naics_cross["NAICS"][naics_counter]
                    i += 1
                    break
    # Initializing the table of assets:
    #cur_sht = bea_book.sheet_by_name(bea_chart["BEA Code"][0])
    #sht_pos = naics.search_ws(cur_sht, "asset codes", 25, False)
    bea_table = pd.DataFrame(np.zeros((asset_list.shape[0],
                                       bea_chart.shape[0])), 
                             columns = bea_chart["BEA Code"])
    # For each industry, calculating 
    for i in bea_chart["BEA Code"]:
        cur_sht = bea_book.sheet_by_name(i)
        sht_pos = naics.search_ws(cur_sht, "asset codes", 25, False)
        for j in xrange(0, len(asset_list)): #xrange(sht_pos[0]+2, cur_sht.nrows):
            cur_asset = asset_list.iloc[j,0]
            for k in xrange(sht_pos[0]+2, cur_sht.nrows):
                cur_cell = unicode(cur_sht.cell_value(k, sht_pos[1]+1)).encode('utf8')
                cur_cell = cur_cell.replace("\xa0", " ").strip()
                if(cur_asset == cur_cell):
                    bea_table[i][j] = float(cur_sht.cell_value(k, cur_sht.ncols-1))
        #bea_table[i] = np.array(cur_sht.col_values(cur_sht.ncols-1, sht_pos[0]+2, cur_sht.nrows))
    # The dollar amounts are in millions:
    bea_table = bea_table.convert_objects(convert_numeric=True).fillna(0)
    bea_table = bea_table * _BEA_IN_FILE_FCTR
    # Initialize tree for assets data:
    fixed_asset_tree = naics.generate_tree()
    for i in xrange(0, len(fixed_asset_tree.enum_inds)):
        fixed_asset_tree.enum_inds[i].data.append(("All", 
                pd.DataFrame(np.zeros((1, asset_list.shape[0])), 
                             columns = asset_list.iloc[:,0])))
        fixed_asset_tree.enum_inds[i].data.append(("Corp", 
                pd.DataFrame(np.zeros((1, asset_list.shape[0])),
                             columns = asset_list.iloc[:,0])))
        fixed_asset_tree.enum_inds[i].data.append(("Non-Corp", 
                pd.DataFrame(np.zeros((1, asset_list.shape[0])),
                             columns = asset_list.iloc[:,0])))
    # Fill in data from BEA's fixed asset table:
    enum_index = len(asset_tree.enum_inds) - 1
    for i in xrange(0, bea_table.shape[1]):
        cur_codes = str(bea_chart["NAICS Code"][i]).split(".")
        tot_share = 0
        all_proportions = naics.get_proportions(cur_codes, asset_tree, 
                                          "FA").iloc[1,:]
        corp_proportions = naics.get_proportions(cur_codes, asset_tree, "FA", 
                                           _CORP_NMS).iloc[1,:]
        non_corp_proportions = naics.get_proportions(cur_codes, asset_tree, 
                                               "FA", _NCORP_NMS).iloc[1,:]
        for code_index in xrange(0, len(cur_codes)):
            for j in xrange(0, len(fixed_asset_tree.enum_inds)):
                enum_index = (enum_index+1) % len(fixed_asset_tree.enum_inds)
                out_dfs = asset_tree.enum_inds[enum_index].data.dfs
                if(sum(out_dfs["FA"].iloc[0,:]) == 0):
                    continue
                all_ratio = 1.0
                corp_ratio = 0.0
                non_corp_ratio = 0.0
                for category in _CORP_NMS:
                    corp_ratio += (out_dfs["FA"][category][0]/
                                        sum(out_dfs["FA"].iloc[0,:]))
                for category in _NCORP_NMS:
                    non_corp_ratio += (out_dfs["FA"][category][0]/
                                            sum(out_dfs["FA"].iloc[0, :]))
                cur_data = fixed_asset_tree.enum_inds[enum_index].data
                ind_codes = cur_data.dfs["Codes:"].iloc[:,0]
                share = naics.compare_codes(cur_codes, ind_codes)
                tot_share += share
                if(share == 0):
                    continue
                num_assets = fixed_asset_tree.enum_inds[0].data.dfs["All"].shape[1]
                for k in xrange(0, num_assets):
                    cur_data.dfs["All"].iloc[0,k] = (bea_table.iloc[k,i]*
                                            all_ratio*
                                            all_proportions[code_index])
                    cur_data.dfs["Corp"].iloc[0,k] = (bea_table.iloc[k,i]*
                                            corp_ratio*
                                            corp_proportions[code_index])
                    cur_data.dfs["Non-Corp"].iloc[0,k] = (bea_table.iloc[k,i]*
                                            non_corp_ratio*
                                            non_corp_proportions[code_index])
                break
            if(tot_share == 1):
                break
    #
    '''
    naics.pop_back(fixed_asset_tree, ["All", "Corp", "Non-Corp"])
    naics.pop_forward(tree=fixed_asset_tree, df_list=["All"],
                      blueprint="FA", blue_tree=asset_tree)
    naics.pop_forward(tree=fixed_asset_tree, df_list=["Corp"],
                      blueprint="FA", blue_tree=asset_tree,
                      sub_print=_CORP_NMS)
    naics.pop_forward(tree=fixed_asset_tree, df_list=["Non-Corp"],
                      blueprint="FA", blue_tree=asset_tree, 
                      sub_print=_NCORP_NMS)
    '''
    return fixed_asset_tree
'''