[![PSL cataloged](https://img.shields.io/badge/PSL-cataloged-a0a0a0.svg)](https://www.PSLmodels.org)
[![Python 3.9](https://img.shields.io/badge/python-3.9-blue.svg)](https://www.python.org/downloads/release/python-3916/)
[![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/downloads/release/python-3108/)
[![Build Status](https://travis-ci.org/PSLmodels/Cost-of-Capital-Calculator.svg?branch=master)](https://travis-ci.org/PSLmodels/Cost-of-Capital-Calculator)
[![codecov](https://codecov.io/gh/PSLmodels/Cost-of-Capital-Calculator/branch/master/graph/badge.svg?token=vOrtCdGu1c)](https://codecov.io/gh/PSLmodels/Cost-of-Capital-Calculator)

# Cost-of-Capital-Calculator
Cost-of-Capital-Calculator is a model that can be used to evaluate the effect of US federal taxes on the investment incentives of corporate and non-corporate businesses. Specifically, Cost-of-Capital-Calculator uses data on the business assets and financial policy, as well as microdata on individual tax filers, to compute marginal effective tax rates on new investments. In modeling the effects of changes to the individual income tax code, Cost-of-Capital-Calculator works with [Tax-Calculator](https://github.com/PSLmodels/tax-calculator), another open-source model of US federal tax policy. Cost-of-Capital-Calculator is written in Python, an interpreted language that can execute on Windows, Mac, or Linux.

## Installation

The `ccc` package can be installed with Anaconda via:

```conda install -c conda-forge ccc```

or with PyPI via:

```pip install cost-of-capital-calculator ```

## Web Application

Cost-of-Capital-Calculator is available through a web application, [Cost of Capital Calculator](https://compute.studio/PSLmodels/Cost-of-Capital-Calculator/). This app allows you to generate estimates of marginal effective tax rates and the cost of capital across production industries, type of asset, and separately for corporate and non-corporate
entities and different forms of financing. The web application is limited in that you cannot consider policy reforms to the individual income tax code.

## Contributing to Cost-of-Capital-Calculator

To contribute to Cost-of-Capital-Calculator, you'll want to clone the GitHub repository to your own machine, where you can work with and edit the source code. To do this, follow the following instructions:
* Install the [Anaconda distribution](https://www.anaconda.com/distribution/) of Python
* Clone this repository to a directory on your computer
* From the terminal (or Conda command prompt), navigate to the directory to which you cloned this repository and run `conda env create -f environment.yml`
* Then, `conda activate ccc-dev`
* Run the model with an example reform from terminal/command prompt by typing `python example.py`
* You can adjust the `example.py` by adjusting the individual income tax reform (using a dictionary or JSON file in a format that is consistent with [Tax Calculator](https://github.com/PSLmodels/Tax-Calculator)) or other model parameters specified in the `business_tax_adjustments` dictionary.
* Model outputs will be saved in the following files:
  * `./baseline_byasset.csv`
    * Cost of capital, marginal effective tax rates, effective average tax rates, and other model output for the baseline policy, organized by asset.
  * `./baseline_byindustry.csv`
    * Cost of capital, marginal effective tax rates, effective average tax rates, and other model output for the baseline policy, organized by production industry.
  * `./reform_byasset.csv`
    * Cost of capital, marginal effective tax rates, effective average tax rates, and other model output for the reform policy, organized by asset.
  * `./reform_byindustry.csv`
    * Cost of capital, marginal effective tax rates, effective average tax rates, and other model output for the refrom policy, organized by production industry.
  * `./changed_byasset.csv`
    * Differences in cost of capital, marginal effective tax rates, effective average tax rates, and other model output between the baseline and reform reform policies, organized by asset.
  * `./changed_byindustry.csv`
    * Differences in cost of capital, marginal effective tax rates, effective average tax rates, and other model output between the baseline and reform reform policies, organized by production industry.

The CSV output files can be compared to the `./example_output/*_expected.csv` files that are checked into the repository to confirm that you are generating the expected output.  The easiest way to do this is to use the `./example-diffs` command (or `example-diffs` on Windows).  If you run into errors running the example script, please open a new issue in the Cost-of-Capital-Calculator repo with a description of the issue and any relevant tracebacks you receive.


## Disclaimer
Results will change as the underlying models improve. A fundamental reason for adopting open source methods in this project is so that people from all backgrounds can contribute to the models that our society uses to assess economic policy; when community-contributed improvements are incorporated, the model will produce different results.


## Citing the Cost-of-Capital-Calculator Model
Cost-of-Capital-Calculator (Version 1.3.0)[Source code], https://github.com/PSLmodels/Cost-of-Capital-Calculator
