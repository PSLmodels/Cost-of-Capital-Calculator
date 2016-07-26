import os.path
import cPickle as pickle
import pandas as pd
from btax.util import get_paths

globals().update(get_paths())

def check_output():
	# load the baseline .pkl file
	with open(os.path.join(_OUT_DIR,'baseline.pkl'), 'rb') as handle:
	  base_out = pickle.load(handle)
	# load the new output .pkl
	with open(os.path.join(_OUT_DIR,'final_output.pkl'), 'rb') as handle:
	  new_out = pickle.load(handle)
	# assert that the two dataframes from the .pkl files are equivalent
	pd.util.testing.assert_frame_equal(new_out, base_out)

if __name__ == '__main__':
	check_output()
