try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup

setup(name='btax',
	  version='0.1',
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
	  package_dir = {'btax': 'Python/btax'},
	  install_requires=['numpy','pandas']
	  )
