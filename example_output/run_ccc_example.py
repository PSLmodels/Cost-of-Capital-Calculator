"""
Runs Cost-of-Capital-Calculator with TCJA as baseline and 2017 law as
the reform.
------------------------------------------------------------------------
"""
# import support packages and Cost-of-Capital-Calculator classes
import os
from bokeh.io import show
import taxcalc
from ccc.data import Assets
from ccc.parameters import Specifications
from ccc.calculator import Calculator
from ccc.utils import diff_two_tables

"""
# Read in a reform to compare against
# Note that TCJA is current law baseline in TC 0.16+
# Thus to compare TCJA to 2017 law, we'll use 2017 law as the reform
reform_url = ('https://raw.githubusercontent.com/'
              'PSLmodels/Tax-Calculator/master/taxcalc/'
              'reforms/2017_law.json')
reform_dict = taxcalc.Policy.read_json_reform(reform_url)
iit_reform = reform_dict
"""

# specify baseline and reform Calculator objects
cyr = 2019
assets = Assets()
baseline_parameters = Specifications(year=cyr)
calc1 = Calculator(baseline_parameters, assets)
reform_parameters = Specifications(year=cyr)
business_tax_adjustments = {
    'CIT_rate': {cyr: 0.35},
    'BonusDeprec_3yr': {cyr: 0.50},
    'BonusDeprec_5yr': {cyr: 0.50},
    'BonusDeprec_7yr': {cyr: 0.50},
    'BonusDeprec_10yr': {cyr: 0.50},
    'BonusDeprec_15yr': {cyr: 0.50},
    'BonusDeprec_20yr': {cyr: 0.50}
}
reform_parameters.update_specifications(business_tax_adjustments)
calc2 = Calculator(reform_parameters, assets)

# do calculations by asset and by industry
baseln_assets_df = calc1.calc_by_asset()
reform_assets_df = calc2.calc_by_asset()
baseln_industry_df = calc1.calc_by_industry()
reform_industry_df = calc2.calc_by_industry()

# generate dataframes with reform-minus-baseline differences
diff_assets_df = diff_two_tables(reform_assets_df, baseln_assets_df)
diff_industry_df = diff_two_tables(reform_industry_df, baseln_industry_df)

# save dataframes to disk as csv files in this directory
OUT = os.path.join(os.path.abspath(os.path.dirname(__file__)))
baseln_industry_df.to_csv(os.path.join(OUT, 'baseline_byindustry.csv'),
                          float_format='%.5f')
reform_industry_df.to_csv(os.path.join(OUT, 'reform_byindustry.csv'),
                          float_format='%.5f')
baseln_assets_df.to_csv(os.path.join(OUT, 'baseline_byasset.csv'),
                        float_format='%.5f')
reform_assets_df.to_csv(os.path.join(OUT, 'reform_byasset.csv'),
                        float_format='%.5f')
diff_industry_df.to_csv(os.path.join(OUT, 'changed_byindustry.csv'),
                        float_format='%.5f')
diff_assets_df.to_csv(os.path.join(OUT, 'changed_byasset.csv'),
                      float_format='%.5f')

# create and show in browser a range plot
p = calc1.range_plot(calc2)
show(p)
