"""
Runner Script (run_btax.py):
-------------------------------------------------------------------------------
Initial module that contains the method to start the calculations in B-Tax. Makes function calls to split out fixed assets by entity type
(pull_soi_data), allocate fixed assets to industries (read_bea), grab all the parameters for the final calculations (get_params), and
calculate the Cost of Capital, Marginal Effective Tax Rates, and Marginal Effective Total Tax Rates (asset_calcs). Additionally, this
method compares the calculated values with those produced by the CBO.
Last updated: 7/25/2016.

"""
# Import packages
import os.path
import sys
import pandas as pd
import numpy as np
import cPickle as pickle
from soi_processing import pull_soi_data
import calc_final_outputs
from check_output import check_output
from util import get_paths, read_from_egg
import read_bea
import soi_processing as soi
import parameters as params
import format_output as format_output
import visuals

globals().update(get_paths())

def run_btax(user_params):
	"""Runner script that kicks off the calculations for B-Tax

		:param user_params: The user input for implementing reforms
		:type user_params: dictionary
		:returns: METR (by industry and asset) and METTR (by asset)
		:rtype: DataFrame
	"""
	# break out the asset data by entity type (c corp, s corp, sole proprietorships, and partners)
	#entity_dfs = pull_soi_data()
	# read in the BEA data on fixed assets and separate them by corp and non-corp
	fixed_assets = read_bea.read_bea()

	# get parameters
	parameters = params.get_params()

	# make calculations by asset and create formated output
	output_by_asset = calc_final_outputs.asset_calcs(parameters)

	# check against CBO
	format_output.CBO_compare(output_by_asset)

	# make calculations by industry and create formated output
	output_by_industry = calc_final_outputs.industry_calcs(parameters, fixed_assets, output_by_asset)


	# create plots
	# by asset
	# visuals.asset_crossfilter(output_by_asset)

	print output_by_industry.head(n=50)
	return output_by_asset, output_by_industry

def main():
    run_btax(user_params={})

if __name__ == '__main__':
	main()
