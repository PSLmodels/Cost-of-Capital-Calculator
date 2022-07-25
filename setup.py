try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open('README.md') as f:
    longdesc = f.read()

version = '1.2.11'

config = {
    'description': 'CCC: A Cost of Capital Calculator',
    'url': 'https://github.com/PSLmodels/Cost-of-Capital-Calculator',
    'download_url': 'https://github.com/PSLmodels/Cost-of-Capital-Calculator',
    'long_description_content_type': 'text/markdown',
    'long_description': longdesc,
    'version': version,
    'license': 'CC0 1.0 Universal (CC0 1.0) Public Domain Dedication',
    'packages': ['ccc'],
    'include_package_data': True,
    'name': 'cost-of-capital-calculator',
    'install_requires': ['taxcalc', 'psutil', 'pandas', 'bokeh', 'numpy',
                         'paramtools'],
    'classifiers': [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Software Development :: Libraries :: Python Modules'],
    'tests_require': ['pytest']
}

setup(**config)
