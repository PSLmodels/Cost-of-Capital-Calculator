# B-Tax
B-Tax is a model that can be used to evaluate the effect of US federal taxes on the investment incentives of corporate and non-corporate businesses.  Specifically, B-Tax uses data on the business assets and financial policy, as well as microdata on individual tax filers, to compute marginal effective tax rates on new investments.  In modeling the effects of changes to the individual income tax code, B-Tax works with [Tax-Calculator](https://github.com/open-source-economics/tax-calculator), another open source model of US federal tax policy.  B-Tax is written in Python, an interpreted language that can execute on Windows, Mac, or Linux.

## Disclaimer
Results will change as the underlying models improve. A fundamental reason for adopting open source methods in this project is so that people from all backgrounds can contribute to the models that our society uses to assess economic policy; when community-contributed improvements are incorporated, the model will produce different results.


##Getting Started

There are two common ways to get started with B-Tax:

The **first way** is to install the B-Tax repository on your
computer.  Do this by:

 * Clone this repo
 * From the cloned repo:
   * `source activate webapp` # see instructions in the webapp-public repo
   * `conda install --file conda-requirements.txt` # ensure you have xlrd
   * `python setup.py install`
   * `run-btax` # console entry point

After the installation you can read the source code and either use
B-Tax as is or develop new B-Tax capabilities.

When using B-Tax on your computer you will have to provide your own values 
for the marginal tax rates on individual income sources (to be enterered in
`parameters.py`) or, if you wish to use B-Tax with Tax-Calculator, you will 
have to supply your own input data on tax filing units.  Please see the 
[Tax-Calculator repo](https://github.com/open-source-economics/tax-calculator) for more information on this. 


The **second way** is to access B-Tax is through our web
application, [Cost of Capital Calculator](http://www.ospc.org/ccc).  This way
allows you to generate estimates of marginal effective tax rates and the cost of capital
across production industries, type of asset, and separately for corporate and non-corporate 
entites and different forms of financing.  The web application uses the Tax-Calculator with 
a nationally representative sample of tax filing units
that is not part of the B-Tax or Tax-Calculator repositories.

Of course, you can get started with B-Tax both ways.

## Citing the B-Tax Model
B-Tax (Version 0.1.5)[Source code], https://github.com/open-source-economics/B-Tax
