VAR_DICT = {'mettr': 'Marginal Effective Total Tax Rate',
            'metr': 'Marginal Effective Tax Rate',
            'rho': 'Cost of Capital',
            'ucc': 'User Cost of Capital',
            'tax_wedge': 'Tax Wedge',
            'z': 'NPV of Depreciation Deductions'}

OUTPUT_VAR_LIST = ['metr', 'mettr', 'rho', 'ucc', 'z', 'delta',
                   'tax_wedge', 'eatr']

OUTPUT_DATA_FORMATS = ['csv', 'tex', 'excel', 'json', 'html', None]

MAJOR_IND_ORDERED = [
    'Agriculture, forestry, fishing, and hunting',
    'Mining', 'Utilities', 'Construction', 'Manufacturing',
    'Wholesale trade', 'Retail trade',
    'Transportation and warehousing', 'Information',
    'Finance and insurance',
    'Real estate and rental and leasing',
    'Professional, scientific, and technical services',
    'Management of companies and enterprises',
    'Administrative and waste management services',
    'Educational services',
    'Health care and social assistance',
    'Arts, entertainment, and recreation',
    'Accommodation and food services',
    'Other services, except government']

TAX_METHODS = {'DB 200%': 2.0, 'DB 150%': 1.5, 'SL': 1.0,
               'Economic': 1.0, 'Expensing': 1.0}

MINOR_ASSET_GROUPS = dict.fromkeys(
    ['Mainframes', 'PCs', 'DASDs', 'Printers', 'Terminals',
     'Tape drives', 'Storage devices', 'System integrators',
     'Prepackaged software', 'Custom software'],
    'Computers and Software')
MINOR_ASSET_GROUPS.update(dict.fromkeys(
    ['Communications', 'Nonelectro medical instruments',
     'Electro medical instruments', 'Nonmedical instruments',
     'Photocopy and related equipment',
     'Office and accounting equipment'],
    'Instruments and Communications Equipment'))
MINOR_ASSET_GROUPS.update(dict.fromkeys(
    ['Household furniture', 'Other furniture', 'Household appliances'],
    'Office and Residential Equipment'))
MINOR_ASSET_GROUPS.update(dict.fromkeys(
    ['Light trucks (including utility vehicles)',
     'Other trucks, buses and truck trailers', 'Autos', 'Aircraft',
     'Ships and boats', 'Railroad equipment', 'Steam engines',
     'Internal combustion engines'], 'Transportation Equipment'))
MINOR_ASSET_GROUPS.update(dict.fromkeys(
    ['Special industrial machinery', 'General industrial equipment'],
    'Industrial Machinery'))
MINOR_ASSET_GROUPS.update(dict.fromkeys(
    ['Nuclear fuel', 'Other fabricated metals',
     'Metalworking machinery', 'Electric transmission and distribution',
     'Other agricultural machinery', 'Farm tractors',
     'Other construction machinery', 'Construction tractors',
     'Mining and oilfield machinery'], 'Other Industrial Equipment'))
MINOR_ASSET_GROUPS.update(dict.fromkeys(
    ['Service industry machinery', 'Other electrical', 'Other'],
    'Other Equipment'))
MINOR_ASSET_GROUPS.update(dict.fromkeys(
    ['Residential'], 'Residential Buildings'))
MINOR_ASSET_GROUPS.update(dict.fromkeys(
    ['Manufacturing', 'Office', 'Hospitals', 'Special care',
     'Medical buildings', 'Multimerchandise shopping',
     'Food and beverage establishments', 'Warehouses',
     'Other commercial', 'Air transportation', 'Other transportation',
     'Religious', 'Educational and vocational', 'Lodging',
     'Public safety'], 'Nonresidential Buildings'))
MINOR_ASSET_GROUPS.update(dict.fromkeys(
    ['Gas', 'Petroleum pipelines', 'Communication',
     'Petroleum and natural gas', 'Mining'],
    'Mining and Drilling Structures'))
MINOR_ASSET_GROUPS.update(dict.fromkeys(
    ['Electric', 'Wind and solar', 'Amusement and recreation',
     'Other railroad', 'Track replacement', 'Local transit structures',
     'Other land transportation', 'Farm', 'Water supply',
     'Sewage and waste disposal',
     'Highway and conservation and development', 'Mobile structures'],
    'Other Structures'))
MINOR_ASSET_GROUPS.update(dict.fromkeys(
    ['Pharmaceutical and medicine manufacturing',
     'Chemical manufacturing, ex. pharma and med',
     'Semiconductor and other component manufacturing',
     'Computers and peripheral equipment manufacturing',
     'Communications equipment manufacturing',
     'Navigational and other instruments manufacturing',
     'Other computer and electronic manufacturing, n.e.c.',
     'Motor vehicles and parts manufacturing',
     'Aerospace products and parts manufacturing',
     'Other manufacturing',
     'Scientific research and development services',
     'Software publishers', 'Financial and real estate services',
     'Computer systems design and related services',
     'All other nonmanufacturing, n.e.c.',
     'Private universities and colleges',
     'Other nonprofit institutions', 'Theatrical movies',
     'Long-lived television programs', 'Books', 'Music',
     'Other entertainment originals', 'Own account software'],
    'Intellectual Property'))

# major asset groups
MAJOR_ASSET_GROUPS = dict.fromkeys(
    ['Mainframes', 'PCs', 'DASDs', 'Printers', 'Terminals',
     'Tape drives', 'Storage devices', 'System integrators',
     'Prepackaged software', 'Custom software', 'Communications',
     'Nonelectro medical instruments', 'Electro medical instruments',
     'Nonmedical instruments', 'Photocopy and related equipment',
     'Office and accounting equipment', 'Household furniture',
     'Other furniture', 'Household appliances',
     'Light trucks (including utility vehicles)',
     'Other trucks, buses and truck trailers', 'Autos', 'Aircraft',
     'Ships and boats', 'Railroad equipment', 'Steam engines',
     'Internal combustion engines', 'Special industrial machinery',
     'General industrial equipment', 'Nuclear fuel',
     'Other fabricated metals', 'Metalworking machinery',
     'Electric transmission and distribution',
     'Other agricultural machinery', 'Farm tractors',
     'Other construction machinery', 'Construction tractors',
     'Mining and oilfield machinery', 'Service industry machinery',
     'Other electrical', 'Other'], 'Equipment')
MAJOR_ASSET_GROUPS.update(dict.fromkeys(
    ['Residential', 'Manufacturing', 'Office', 'Hospitals',
     'Special care', 'Medical buildings', 'Multimerchandise shopping',
     'Food and beverage establishments', 'Warehouses',
     'Other commercial', 'Air transportation', 'Other transportation',
     'Religious', 'Educational and vocational', 'Lodging',
     'Public safety', 'Gas', 'Petroleum pipelines', 'Communication',
     'Petroleum and natural gas', 'Mining', 'Electric',
     'Wind and solar', 'Amusement and recreation', 'Other railroad',
     'Track replacement', 'Local transit structures',
     'Other land transportation', 'Farm', 'Water supply',
     'Sewage and waste disposal',
     'Highway and conservation and development', 'Mobile structures'],
    'Structures'))
MAJOR_ASSET_GROUPS.update(dict.fromkeys(
    ['Pharmaceutical and medicine manufacturing',
     'Chemical manufacturing, ex. pharma and med',
     'Semiconductor and other component manufacturing',
     'Computers and peripheral equipment manufacturing',
     'Communications equipment manufacturing',
     'Navigational and other instruments manufacturing',
     'Other computer and electronic manufacturing, n.e.c.',
     'Motor vehicles and parts manufacturing',
     'Aerospace products and parts manufacturing',
     'Other manufacturing',
     'Scientific research and development services',
     'Software publishers', 'Financial and real estate services',
     'Computer systems design and related services',
     'All other nonmanufacturing, n.e.c.',
     'Private universities and colleges',
     'Other nonprofit institutions', 'Theatrical movies',
     'Long-lived television programs', 'Books', 'Music',
     'Other entertainment originals', 'Own account software'],
    'Intellectual Property'))
MAJOR_ASSET_GROUPS.update(dict.fromkeys(['Inventories'], 'Inventories'))
MAJOR_ASSET_GROUPS.update(dict.fromkeys(['Land'], 'Land'))

# define major industry groupings
IND_DICT = dict.fromkeys(
    ['Farms', 'Forestry, fishing, and related activities'],
    'Agriculture, forestry, fishing, and hunting')
IND_DICT.update(dict.fromkeys(
    ['Oil and gas extraction', 'Mining, except oil and gas',
     'Support activities for mining'], 'Mining'))
IND_DICT.update(dict.fromkeys(['Utilities'], 'Utilities'))
IND_DICT.update(dict.fromkeys(['Construction'], 'Construction'))
IND_DICT.update(dict.fromkeys(
    ['Wood products', 'Nonmetallic mineral products', 'Primary metals',
     'Fabricated metal products', 'Machinery',
     'Computer and electronic products',
     'Electrical equipment, appliances, and components',
     'Motor vehicles, bodies and trailers, and parts',
     'Other transportation equipment', 'Furniture and related products',
     'Miscellaneous manufacturing',
     'Food, beverage, and tobacco products',
     'Textile mills and textile products',
     'Apparel and leather and allied products',
     'Paper products', 'Printing and related support activities',
     'Petroleum and coal products', 'Chemical products',
     'Plastics and rubber products'], 'Manufacturing'))
IND_DICT.update(dict.fromkeys(['Wholesale trade'], 'Wholesale trade'))
IND_DICT.update(dict.fromkeys(['Retail trade'], 'Retail trade'))
IND_DICT.update(dict.fromkeys(
    ['Air transportation', 'Railroad transportation',
     'Water transportation', 'Truck transportation',
     'Transit and ground passenger transportation',
     'Pipeline transportation',
     'Other transportation and support activitis',
     'Warehousing and storage'], 'Transportation and warehousing'))
IND_DICT.update(dict.fromkeys(
    ['Publishing industries (including software)',
     'Motion picture and sound recording industries',
     'Broadcasting and telecommunications',
     'Information and telecommunications'], 'Information'))
IND_DICT.update(dict.fromkeys(
    ['Federal Reserve banks',
     'Credit intermediation and related activities',
     'Securities, commodity contracts, and investments',
     'Insurance carriers and related activities',
     'Funds, trusts, and other financial vehicles'],
    'Finance and insurance'))
IND_DICT.update(dict.fromkeys(
    ['Real estate',
     'Rental and leasing services and lessors of intangible assets'],
    'Real estate and rental and leasing'))
IND_DICT.update(dict.fromkeys(
    ['Legal services', 'Computer systems design and related services',
     'Miscellaneous professional, scientific, and technical services'],
    'Professional, scientific, and technical services'))
IND_DICT.update(dict.fromkeys(
    ['Management of companies and enterprises'],
    'Management of companies and enterprises'))
IND_DICT.update(dict.fromkeys(
    ['Administrative and support services',
     'Waster management and remediation services'],
    'Administrative and waste management services'))
IND_DICT.update(dict.fromkeys(['Educational services'],
                              'Educational services'))
IND_DICT.update(dict.fromkeys(
    ['Ambulatory health care services', 'Hospitals',
     'Nursing and residential care facilities', 'Social assistance'],
    'Health care and social assistance'))
IND_DICT.update(dict.fromkeys(
    ['Performing arts, spectator sports, museums, and related activities',
     'Amusements, gambling, and recreation industries'],
    'Arts, entertainment, and recreation'))
IND_DICT.update(dict.fromkeys(
    ['Accomodation', 'Food services and drinking places'],
    'Accommodation and food services'))
IND_DICT.update(dict.fromkeys(
    ['Other services, except government'],
    'Other services, except government'))

BEA_CODE_DICT = dict.fromkeys(
    ['110C', '113F'], 'Agriculture, forestry, fishing, and hunting')
BEA_CODE_DICT.update(dict.fromkeys(
    ['2110', '2120', '2130'], 'Mining'))
BEA_CODE_DICT.update(dict.fromkeys(['2200'], 'Utilities'))
BEA_CODE_DICT.update(dict.fromkeys(['2300'], 'Construction'))
BEA_CODE_DICT.update(dict.fromkeys(
    ['3210', '3270', '3310', '3320', '3330', '3340', '3350', '336M',
     '336O', '3370', '338A', '311A', '313T', '315A', '3220', '3230',
     '3240', '3250', '3260'], 'Manufacturing'))
BEA_CODE_DICT.update(dict.fromkeys(['4200'], 'Wholesale trade'))
BEA_CODE_DICT.update(dict.fromkeys(['44RT'], 'Retail trade'))
BEA_CODE_DICT.update(dict.fromkeys(
    ['4810', '4820', '4830', '4840', '4850', '4860', '487S', '4930'],
    'Transportation and warehousing'))
BEA_CODE_DICT.update(dict.fromkeys(
    ['5110', '5120', '5130', '5140'], 'Information'))
BEA_CODE_DICT.update(dict.fromkeys(
    ['5210', '5220', '5230', '5240', '5250'], 'Finance and insurance'))
BEA_CODE_DICT.update(dict.fromkeys(
    ['5310', '5320'], 'Real estate and rental and leasing'))
BEA_CODE_DICT.update(dict.fromkeys(
    ['5411', '5415', '5412'],
    'Professional, scientific, and technical services'))
BEA_CODE_DICT.update(dict.fromkeys(
    ['5500'], 'Management of companies and enterprises'))
BEA_CODE_DICT.update(dict.fromkeys(
    ['5610', '5620'], 'Administrative and waste management services'))
BEA_CODE_DICT.update(dict.fromkeys(['6100'], 'Educational services'))
BEA_CODE_DICT.update(dict.fromkeys(
    ['6210', '622H', '6230', '6240'],
    'Health care and social assistance'))
BEA_CODE_DICT.update(dict.fromkeys(
    ['711A', '7130'], 'Arts, entertainment, and recreation'))
BEA_CODE_DICT.update(dict.fromkeys(
    ['7210', '7220'], 'Accommodation and food services'))
BEA_CODE_DICT.update(dict.fromkeys(
    ['8100'], 'Other services, except government'))
