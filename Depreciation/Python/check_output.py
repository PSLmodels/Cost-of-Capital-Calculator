import pandas as pd

econ_dep_out = pd.read_csv("output/econDepreciation.csv")
econ_dep_ref = pd.read_csv("output/econ_depreciation.csv")
pd.util.testing.assert_frame_equal(econ_dep_out, econ_dep_ref)
tax_dep_out = pd.read_csv("output/taxDepreciation.csv")
tax_dep_ref = pd.read_csv("output/tax_depreciation.csv")
pd.util.testing.assert_frame_equal(tax_dep_out, tax_dep_ref)
