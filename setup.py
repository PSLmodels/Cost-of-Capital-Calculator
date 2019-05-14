try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open('README.md') as f:
        longdesc = f.read()

version = '1.0.0'

config = {
    'description': 'Cost-of-Capital-Calculator: A Cost of Capital Calculator',
    'url': 'https://github.com/open-source-economics/Cost-of-Capital-Calculator',
    'download_url': 'https://github.com/open-source-economics/Cost-of-Capital-Calculator',
    'long_description': longdesc,
    'version': version,
    'license': 'CC0 1.0 Universal public domain dedication',
    'packages': ['ccc'],
    'include_package_data': True,
    'name': 'ccc',
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
