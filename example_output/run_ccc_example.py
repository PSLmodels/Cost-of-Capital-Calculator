"""
Runs Cost-of-Capital-Calculator with TCJA as baseline and 2017 law as
the reform.
------------------------------------------------------------------------
"""
# Import packages and classes
import ccc
import taxcalc
from ccc.data import Assets
from ccc.parameters import Specifications
from ccc.calculator import Calculator
from bokeh.io import show

# Read in a reform to compare against
# Note that TCJA is current law baseline in TC 0.16+
# Thus to compare TCJA to 2017 law, we'll use 2017 law as the reform
reform_url = ('https://raw.githubusercontent.com/'
              'PSLmodels/Tax-Calculator/master/taxcalc/'
              'reforms/2017_law.json')
ref = taxcalc.Calculator.read_json_param_objects(reform_url, None)
iit_reform = ref['policy']

# Initialize Asset and Calculator Objects
assets = Assets()
# Baseline
baseline_parameters = Specifications(year=2019, call_tc=False,
                                     iit_reform={})
calc1 = Calculator(baseline_parameters, assets)
# Reform
reform_parameters = Specifications(year=2019, call_tc=False,
                                   iit_reform={})
business_tax_adjustments = {
    'CIT_rate': 0.35, 'BonusDeprec_3yr': 0.50, 'BonusDeprec_5yr': 0.50,
    'BonusDeprec_7yr': 0.50, 'BonusDeprec_10yr': 0.50,
    'BonusDeprec_15yr': 0.50, 'BonusDeprec_20yr': 0.50}
reform_parameters.update_specifications(business_tax_adjustments)
calc2 = Calculator(reform_parameters, assets)

# Do calculations by asset
base_assets_df = calc1.calc_by_asset()
reform_assets_df = calc2.calc_by_asset()
# Do Calculations by Industry
base_industry_df = calc1.calc_by_industry()
reform_industry_df = calc2.calc_by_industry()

# Generate dataframes with differences
diff_assets_df = ccc.utils.diff_two_tables(
    reform_assets_df, base_assets_df)
diff_industry_df = ccc.utils.diff_two_tables(
    reform_industry_df, base_industry_df)

# Save dataframes to disk as csv files
base_industry_df.to_csv('baseline_byindustry.csv', encoding='utf-8')
reform_industry_df.to_csv('reform_byindustry.csv', encoding='utf-8')
base_assets_df.to_csv('baseline_byasset.csv', encoding='utf-8')
reform_assets_df.to_csv('reform_byasset.csv', encoding='utf-8')
diff_industry_df.to_csv('changed_byindustry.csv', encoding='utf-8')
diff_assets_df.to_csv('changed_byasset.csv', encoding='utf-8')

# # create bokeh plot
p = calc1.range_plot(calc2)
show(p)
