"""
Runs Cost-of-Capital-Calculator with TCJA as baseline and 2017 law as reform
----------------------------------------------------------------------------
"""
# import support packages and Cost-of-Capital-Calculator classes and function
from bokeh.io import show
import taxcalc
from ccc.data import Assets
from ccc.parameters import Specification, DepreciationParams
from ccc.calculator import Calculator
from ccc.utils import diff_two_tables

# specify individual income and business tax reform to compare against
# ... Note that TCJA is current-law baseline in Tax-Calculator,
#     so to compare TCJA to 2017 law, we'll use 2017 law as the reform
reform_url = ('https://raw.githubusercontent.com/'
              'PSLmodels/Tax-Calculator/master/taxcalc/'
              'reforms/2017_law.json')
iit_reform = taxcalc.Policy.read_json_reform(reform_url)
# ... specify reform that implements pre-TCJA business tax policy
cyr = 2019
business_tax_reform = {
    'CIT_rate': 0.35, 'BonusDeprec_3yr': 0.50, 'BonusDeprec_5yr': 0.50,
    'BonusDeprec_7yr': 0.50, 'BonusDeprec_10yr': 0.50,
    'BonusDeprec_15yr': 0.50, 'BonusDeprec_20yr': 0.50}

# specify baseline and reform Calculator objects for 2019 calculations
assets = Assets()
baseline_parameters = Specification(year=cyr)
dp = DepreciationParams()
calc1 = Calculator(baseline_parameters, dp, assets)
reform_parameters = Specification(year=cyr)
reform_parameters.update_specification(business_tax_reform)
calc2 = Calculator(reform_parameters, dp, assets)

# do calculations by asset and by industry
baseln_assets_df = calc1.calc_by_asset()
reform_assets_df = calc2.calc_by_asset()
baseln_industry_df = calc1.calc_by_industry()
reform_industry_df = calc2.calc_by_industry()

# generate dataframes with reform-minus-baseline differences
diff_assets_df = diff_two_tables(reform_assets_df, baseln_assets_df)
diff_industry_df = diff_two_tables(reform_industry_df, baseln_industry_df)

# save dataframes to disk as csv files in this directory
baseln_industry_df.to_csv('baseline_byindustry.csv', float_format='%.5f')
reform_industry_df.to_csv('reform_byindustry.csv', float_format='%.5f')
baseln_assets_df.to_csv('baseline_byasset.csv', float_format='%.5f')
reform_assets_df.to_csv('reform_byasset.csv', float_format='%.5f')
diff_industry_df.to_csv('changed_byindustry.csv', float_format='%.5f')
diff_assets_df.to_csv('changed_byasset.csv', float_format='%.5f')

# create and show in browser a range plot
p = calc1.range_plot(calc2)
show(p)
