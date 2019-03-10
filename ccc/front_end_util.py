from __future__ import unicode_literals
from collections import defaultdict
import os
import json
from ccc.util import DEFAULT_ASSET_COLS, DEFAULT_INDUSTRY_COLS
from ccc.util import DEFAULT_START_YEAR

# Row labels, in order, including minor headings like "Durable goods"
ccc_TABLE_ASSET_ORDER = ("All Investments", "Equipment", "Mainframes",
                          "PCs", "DASDs", "Printers", "Terminals",
                          "Tape drives", "Storage devices",
                          "System integrators", "Communications",
                          "Nonelectro medical instruments",
                          "Electro medical instruments",
                          "Nonmedical instruments",
                          "Photocopy and related equipment",
                          "Office and accounting equipment",
                          "Nuclear fuel", "Other fabricated metals",
                          "Steam engines", "Internal combustion engines",
                          "Metalworking machinery",
                          "Special industrial machinery",
                          "General industrial equipment",
                          "Electric transmission and distribution",
                          "Light trucks (including utility vehicles)",
                          "Other trucks, buses and truck trailers",
                          "Autos", "Aircraft", "Ships and boats",
                          "Railroad equipment", "Household furniture",
                          "Other furniture",
                          "Other agricultural machinery",
                          "Farm tractors", "Other construction machinery",
                          "Construction tractors",
                          "Mining and oilfield machinery",
                          "Service industry machinery",
                          "Household appliances", "Other electrical",
                          "Other", "Structures", "Office", "Hospitals",
                          "Special care", "Medical buildings",
                          "Multimerchandise shopping",
                          "Food and beverage establishments",
                          "Warehouses", "Mobile structures",
                          "Other commercial", "Manufacturing",
                          "Electric", "Wind and solar", "Gas",
                          "Petroleum pipelines", "Communication",
                          "Petroleum and natural gas", "Mining",
                          "Educational and vocational", "Lodging",
                          "Amusement and recreation",
                          "Air transportation", "Other transportation",
                          "Other railroad", "Track replacement",
                          "Local transit structures",
                          "Other land transportation", "Farm",
                          "Water supply", "Sewage and waste disposal",
                          "Public safety",
                          "Highway and conservation and development",
                          "Intellectual Property", "Own account software",
                          "Software publishers",
                          "Computer systems design and related services",
                          "Theatrical movies",
                          "Long-lived television programs", "Books",
                          "Music", "Other entertainment originals",
                          "Pharmaceutical and medicine manufacturing",
                          "Chemical manufacturing, ex. pharma and med",
                          "Semiconductor and other component manufacturing",
                          "Computers and peripheral equipment manufacturing",
                          "Communications equipment manufacturing",
                          "Navigational and other instruments manufacturing",
                          "Other computer and electronic manufacturing, n.e.c.",
                          "Motor vehicles and parts manufacturing",
                          "Aerospace products and parts manufacturing",
                          "Other manufacturing",
                          "Scientific research and development services",
                          "Financial and real estate services",
                          "All other nonmanufacturing, n.e.c.",
                          "Inventories", "Land")
ccc_TABLE_INDUSTRY_ORDER = ("All Investments",
                             "Agriculture, forestry, fishing, and hunting",
                             "Farms",
                             "Forestry, fishing, and related activities",
                             "Mining", "Oil and gas extraction",
                             "Mining, except oil and gas",
                             "Support activities for mining", "Utilities",
                             "Construction", "Manufacturing",
                             "Durable goods", "Wood products",
                             "Nonmetallic mineral products",
                             "Primary metals",
                             "Fabricated metal products",
                             "Machinery",
                             "Computer and electronic products",
                             "Electrical equipment, appliances, and components",
                             "Motor vehicles, bodies and trailers, and parts",
                             "Other transportation equipment",
                             "Furniture and related products",
                             "Miscellaneous manufacturing",
                             "Nondurable goods",
                             "Food, beverage, and tobacco products",
                             "Textile mills and textile product mills",
                             "Apparel and leather and allied products",
                             "Paper products",
                             "Printing and related support activities",
                             "Petroleum and coal products",
                             "Chemical products",
                             "Plastics and rubber products",
                             "Wholesale trade", "Retail trade",
                             "Transportation and warehousing",
                             "Air transportation",
                             "Railroad transportation",
                             "Water transportation",
                             "Truck transportation",
                             "Transit and ground passenger transportation",
                             "Pipeline transportation",
                             "Other transportation and support activities",
                             "Warehousing and storage", "Information",
                             "Publishing industries (including software)",
                             "Motion picture and sound recording industries",
                             "Broadcasting and telecommunications",
                             "Information and data processing services",
                             "Finance and insurance",
                             "Credit intermediation and related activities",
                             "Securities, commodity contracts, and investments",
                             "Insurance carriers and related activities",
                             "Funds, trusts, and other financial vehicles",
                             "Real estate and rental and leasing",
                             "Real estate",
                             "Rental and leasing services and lessors of intangible assets",
                             "Professional, scientific, and technical services",
                             "Legal services",
                             "Computer systems design and related services",
                             "Miscellaneous professional, scientific, and technical services",
                             "Management of companies and enterprises",
                             "Administrative and waste management services",
                             "Administrative and support services",
                             "Waste management and remediation services",
                             "Educational services",
                             "Health care and social assistance",
                             "Ambulatory health care services",
                             "Hospitals",
                             "Nursing and residential care facilities",
                             "Social assistance",
                             "Arts, entertainment, and recreation",
                             "Performing arts, spectator sports, museums, and related activities",
                             "Amusements, gambling, and recreation industries",
                             "Accommodation and food services",
                             "Accommodation",
                             "Food services and drinking places",
                             "Other services, except government")
# If any minor headings are needed, such as "Durable goods", put them
# in "breaks" below
ccc_TABLE_BREAKS = {'industry': ['Durable goods', 'Nondurable goods'],
                     'asset': []}
SPACES = (u'\xa0', u'\u00a0', u' ')


ASSET_COL_META = dict(DEFAULT_ASSET_COLS)
INDUSTRY_COL_META = dict(DEFAULT_INDUSTRY_COLS)

DO_ASSERTIONS = int(os.environ.get('ccc_TABLE_ASSERTIONS', False))


def runner_json_tables(test_run=False, start_year=DEFAULT_START_YEAR,
                       iit_reform=None, **user_params):
    """
    Run Cost-of-Capital-Calculator nad create JSON files for PolicyBrain tables.

    Args:
        test_run: boolean, whether test (don't use PUF/Tax-Calc)
        start_year: integer, tax year draft policy from
        iit_reform: dictionary, tax parameters for Tax-Calculator
        user_params: dictionary, user defined parameters for Cost-of-Capital-Calculator

    Returns:
        json_table: json object, serialized DataFrames
    """
    from ccc.execute import runner, TABLE_ORDER
    out = runner(test_run, start_year, iit_reform, **user_params)

    all_dataframes = {'base_output_by_asset': out[0].to_json(),
                      'reform_output_by_asset': out[1].to_json(),
                      'changed_output_by_asset': out[2].to_json(),
                      'base_output_by_industry': out[3].to_json(),
                      'reform_output_by_industry': out[4].to_json(),
                      'changed_output_by_industry': out[5].to_json()}
    serialized_dataframes = json.dumps(all_dataframes)

    tables = {'row_grouping': out.row_grouping}
    for label, table in zip(TABLE_ORDER, out[:-1]):
        table.to_pickle(label + '.pkl')

    for table_name, table in zip(TABLE_ORDER, out[:-1]):
        if 'asset' in table_name:
            tab = output_by_asset_to_json_table(table, table_name)
            for k, v in tab.items():
                for k2, v2 in v.items():
                    k1 = 'asset_{}'.format(k)
                    if k1 not in tables:
                        tables[k1] = {}
                    tables[k1][k2] = v2
        elif 'industry' in table_name:
            tab = output_by_industry_to_json_table(table, table_name)
            for k, v in tab.items():
                for k2, v2 in v.items():
                    k1 = 'industry_{}'.format(k)
                    if k1 not in tables:
                        tables[k1] = {}
                    tables[k1][k2] = v2
        else:
            raise ValueError('Expected an "asset" or "industry" related table')
    return json.dumps({
        'json_table': add_summary_rows_and_breaklines(dict(tables),
                                                      start_year,
                                                      do_assertions=test_run),
        'dataframes': serialized_dataframes,
        })


def add_summary_rows_and_breaklines(results, first_budget_year,
                                    do_assertions=False):
    """
    Take various results from i.e. mY_dec, mX_bin, df_dec, etc
    Return organized and labeled table results for display

    Args:
        results: dictionary, Cost-of-Capital-Calculator results tables
        first_budget_year: integer, first year in budget window/start_year
        do_assertions: boolean, whether or not to do assertions

    Returns:
        tables: dictionary, tables of Cost-of-Capital-Calculator results formatted
    """
    do_assertions = do_assertions or DO_ASSERTIONS
    tables_to_process = {k: v for k, v in results.items()
                         if k.startswith(('asset_', 'industry_'))}
    row_grouping = results.get('row_grouping', {})
    tables = {k: results[k] for k in (set(results) - set(tables_to_process))}
    stats = defaultdict(lambda: defaultdict(lambda: {}))
    for upper_key, table_data0 in tables_to_process.items():
        if upper_key not in tables:
            tables[upper_key] = {}
        for table_id, table_data in table_data0.items():
            col_labels = list(table_data.columns)
            # Note the logic in this functions addresses
            # the fact that row_labels is not the final
            # order of table
            row_labels = table_data.index
            table = {
                'col_labels': col_labels,
                'cols': [],
                'label': table_id,
                'rows': [],
            }
            is_asset = 'asset_' in upper_key
            meta = ASSET_COL_META if is_asset else INDUSTRY_COL_META
            # Add the column metadata for this
            # Industry or Asset reform /baseline/ or change table
            for col_key, label in enumerate(col_labels):
                col_dict = [v for k, v in meta.items()
                            if v['col_label'] == label][0]
                table['cols'].append({
                    'label': label,
                    'divisor': col_dict.get('divisor', 1),
                    'units': '',
                    'decimals': col_dict.get('decimals', 0),
                })

            col_count = len(col_labels)
            group_data = row_grouping['asset' if is_asset else 'industry']
            keys = tuple(group_data)
            # This is the actual row order
            if is_asset:
                row_order = ccc_TABLE_ASSET_ORDER
            else:
                row_order = ccc_TABLE_INDUSTRY_ORDER
            # breaks and befores below deal with
            # putting breaklines in the table
            # for "Durable Goods" and "Nondurable Goods"
            breaks = ccc_TABLE_BREAKS['asset' if is_asset else 'industry']
            befores = []
            for b in breaks:
                before = [r1 for r1, r2 in zip(row_order[:-1], row_order[1:])
                          if r2 == b][0]
                befores.append(before)

            if not is_asset and do_assertions:
                assert len(befores) == 2  # Nondurable Goods, Durable Goods
                assert "Manufacturing" in befores, (repr(befores))
            row_order = [r for r in row_order if r not in breaks]
            for idx, row_label in enumerate(row_order):
                if row_label in befores:
                    # Create a breakline row for something like
                    # "Durable Goods".  Note by including
                    # summary_c and summary_nc as "breakline",
                    # the js assets know to format differently.
                    # These breakline rows have no numbers
                    lab = breaks[befores.index(row_label)]
                    extra_row = {'label': lab,
                                 'summary_c': 'breakline',
                                 'summary_nc': 'breakline',
                                 'major_grouping': lab,
                                 'cells': []}
                else:
                    extra_row = None
                # Logic to find the group that a row
                # falls into and display the weighted
                # mean of that row as a bold row summary.
                # If row['label'] == row['major_grouping'],
                # then it is a summary row, otherwise
                # the label differs from the grouping.
                try:
                    group = group_data[row_label]
                except KeyError:
                    raise KeyError('Failed on key lookup {} in {}'.format(group_data, row_label))
                row = {
                    'label': row_label,
                    'cells': [],
                    'major_grouping': group['major_grouping'],
                    'summary_c': '{:.03f}'.format(group['summary_c']),
                    'summary_nc': '{:.03f}'.format(group['summary_nc']),
                }

                for col_key in range(0, col_count):
                    try:
                        this_row = table_data.loc[row_label].values
                    except:
                        raise KeyError('Failed on lookup of {} in {}'.format(row_label, table_data.index))
                    value = this_row[col_key]
                    if do_assertions:
                        # Do assertions to make sure
                        # the weighted mean rows, after
                        # all this reshaping, end up
                        # being in the right range
                        key1 = row['major_grouping']
                        key2 = row['major_grouping'] == row['label']
                        if col_key not in stats[key1][key2]:
                            minn, maxx = stats[key1][key2][col_key] = [None, None]
                        if minn is None or minn > value:
                            minn = value
                        if maxx is None or maxx < value:
                            maxx = value
                        stats[key1][key2][col_key] = [minn, maxx]
                    cell = {
                        'format': {
                            'divisor': table['cols'][col_key]['divisor'],
                            'decimals': table['cols'][col_key]['decimals'],
                        },
                        'value': value,
                    }
                    cell['value'] = value
                    row['cells'].append(cell)
                table['rows'].append(row)
                if extra_row:
                    # If we made a breakline row,
                    # add it next because we are
                    # currently processing the preceding
                    # row
                    table['rows'].append(extra_row)

            tables[upper_key][table_id] = table
    if do_assertions:
        assertions_on_stats(stats)
    tables['result_years'] = [first_budget_year]
    return tables


def _dataframe_to_json_table(df, defaults, label, index_col):
    """
    Turn a DataFrame into a JSON table.

    Args:
        df: DataFrame, DataFrame to serialize
        defaults: DataFrame, default DataFrame(?)
        label: string, label for table
        index_col:

    Returns:
        tables: JSON, JSON table
    """
    groups = [x[1]['table_id'] for x in defaults]
    tables = defaultdict(lambda: {})
    for group in set(groups):
        if group == 'all':
            continue
        new_column_names = [x[1]['col_label'] for x in defaults
                            if x[1]['table_id'] == group]
        keep_columns = [x[0] for x in defaults
                        if x[1]['table_id'] in (group, 'all')]
        df2 = df[keep_columns]
        df2.loc[:, index_col] = [replace_unicode_spaces(s) for s in
                                 df2[index_col]]
        df2.set_index(index_col, inplace=True)
        df2.columns = new_column_names
        if 'reform' in label:
            label2 = 'reform'
        elif 'changed' in label:
            label2 = 'changed'
        elif 'base' in label:
            label2 = 'baseline'
        print(label, label2, group)
        tables[group][label2] = df2
    return tables


def output_by_asset_to_json_table(df, table_name):
    from ccc.parameters import DEFAULT_ASSET_COLS
    return _dataframe_to_json_table(df, DEFAULT_ASSET_COLS,
                                    table_name, 'Asset Type')


def output_by_industry_to_json_table(df, table_name):
    from ccc.parameters import DEFAULT_INDUSTRY_COLS
    return _dataframe_to_json_table(df, DEFAULT_INDUSTRY_COLS,
                                    table_name, 'Industry')


def assertions_on_stats(stats):
    """
    Run assertions on stats accumulated while making tables

    Args:
        stats: Dictionary, dict of dict of dict
            First key: True or False - is a summary row or not
            Second key: Major grouping, such as Manufacturing
            Third key: Column idx, 0 through 6

    Returns: None or raises AssertionError
    """
    for group, v in stats.items():
        # For each summary row
        # (v[True] means summaries, v[False] means data rows)
        for col_idx, compare in v[True].items():
            # Ensure we always have min and max
            assert len(compare) == 2
            # If it is a summary row, assert max
            # of rows is equal to min of rows (zero variance
            # because it is only one row)
            assert compare[0] - compare[1] < 1e-7
            # Find the corresponding non-summary rows
            if group in v[False]:
                vals = v[False][group][col_idx]
                # Assert the summary weighted means are within
                # the min/ max of the rows being summarized
                assert vals[0] <= compare[0] and vals[1] >= compare[0] or vals[0] == vals[1], repr((group, vals, compare))
            else:
                # the summary row is the only one in the group
                # E.g. Construction
                pass


def replace_unicode_spaces(s):
    for space in SPACES:
        s = s.replace(space, u' ')
    return s
