"""
Runs Cost-of-Capital-Calculator with TCJA as baseline and 2017 law as
the reform.
------------------------------------------------------------------------
"""
# Import support packages and Cost-of-Capital-Calculator classes
import os
from bokeh.io import show
import taxcalc
from ccc.data import Assets
from ccc.parameters import Specifications
from ccc.calculator import Calculator

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
# Do calculations by industry
base_industry_df = calc1.calc_by_industry()
reform_industry_df = calc2.calc_by_industry()

# Generate dataframes with differences
diff_assets_df = ccc.utils.diff_two_tables(reform_assets_df,
                                           base_assets_df)
diff_industry_df = ccc.utils.diff_two_tables(reform_industry_df,
                                             base_industry_df)

# Save dataframes to disk as csv files in the example_output subdirectory
OUT = os.path.join(os.path.abspath(
    os.path.dirname(__file__)), 'example_output'
)
base_industry_df.to_csv(os.path.join(OUT, 'baseline_byindustry.csv'))
reform_industry_df.to_csv(os.path.join(OUT, 'reform_byindustry.csv'))
base_assets_df.to_csv(os.path.join(OUT, 'baseline_byasset.csv'))
reform_assets_df.to_csv(os.path.join(OUT, 'reform_byasset.csv'))
diff_industry_df.to_csv(os.path.join(OUT, 'changed_byindustry.csv'))
diff_assets_df.to_csv(os.path.join(OUT, 'changed_byasset.csv'))

# Create bokeh plot
p = calc1.range_plot(calc2)
show(p)
