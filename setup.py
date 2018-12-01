try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open('README.md') as f:
        longdesc = f.read()

version = '0.0.0'

config = {
    'description': 'B-Tax: A Cost of Capital Calculator',
    'url': 'https://github.com/open-source-economics/B-Tax',
    'download_url': 'https://github.com/open-source-economics/B-Tax',
    'long_description': longdesc,
    'version': version,
    'license': 'CC0 1.0 Universal public domain dedication',
    'packages': ['btax'],
    'include_package_data': True,
    'name': 'btax',
    'install_requires': ['numpy', 'pandas', 'taxcalc', 'scipy', 'xlrd'],
    'classifiers': [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: CC0 1.0 Universal public domain dedication',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries :: Python Modules'],
    'tests_require': ['pytest']
}

setup(**config)
