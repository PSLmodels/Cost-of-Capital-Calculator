import glob
import os

import versioneer

try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup

def get_data_files():
    files = []
    root = os.path.join('btax', 'data')
    for r, d, f in os.walk(root):
        files.extend(os.path.join(r, fi) for fi in f)
    files += glob.glob(os.path.join('btax', 'param_defaults', '*.json'))
    return [os.path.relpath(f, 'btax') for f in files]

setup(    version=versioneer.get_version(),
          cmdclass=versioneer.get_cmdclass(),
          name='btax',
	  description ='Business tax calculator',
	  long_description = 'Calculates the marginal effective tax rate and marginal effective total tax rate by asset type',
	  classifiers =[
	  		'Programming Language :: Python :: 2.7'
	  		'Topic :: Software Development :: Libraries :: Python Modules'
	  ],
	  author='Benjamin Gardner',
	  author_email='bfgard@gmail.com',
	  url='https://github.com/open-source-economics/B-Tax',
	  packages=['btax'],
          package_data={'btax': get_data_files()},
	  install_requires=[],
          entry_points={
          'console_scripts': [
              'run-btax = btax.run_btax:main',
          ]}
)
