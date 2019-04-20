"""
Cost-of-Capital-Calculator Calculator class.
"""
# CODING-STYLE CHECKS:
# pycodestyle calculator.py
# pylint --disable=locally-disabled calculator.py
#
# pylint: disable=invalid-name,no-value-for-parameter,too-many-lines

import copy
import pandas as pd
from ccc.calcfunctions import (update_depr_methods, npv_tax_depr,
                               eq_coc, eq_coc_inventory, eq_ucc,
                               eq_metr, eq_mettr, eq_tax_wedge, eq_eatr)
from ccc.parameters import Specifications
from ccc.data import Assets
from ccc.utils import wavg, diff_two_tables
from ccc.constants import VAR_DICT
# import pdb


class Calculator():
    """
    Constructor for the Calculator class.

    Parameters
    ----------
    p: Specifications class object
        this argument must be specified and object is copied for internal use

    assets: Assets class object
        this argument must be specified and object is copied for internal use

    verbose: boolean
        specifies whether or not to write to stdout data-loaded and
        data-extrapolated progress reports; default value is true.

    behavior: Behavior class object
        specifies behavioral responses used by Calculator; default is None,
        which implies no behavioral responses to p reform;
        when argument is an object it is copied for internal use

    Raises
    ------
    ValueError:
        if parameters are not the appropriate type.

    Returns
    -------
    class instance: Calculator

    Notes
    -----
    The most efficient way to specify current-law and reform Calculator
    objects is as follows:
         pol = Specifications()
         rec = Assets()
         calc1 = Calculator(p=pol, assets=rec)  # current-law
         pol.implement_reform(...)
         calc2 = Calculator(p=pol, assets=rec)  # reform
    All calculations are done on the internal copies of the Specifications and
    Assets objects passed to each of the two Calculator constructors.
    """
    # pylint: disable=too-many-public-methods

    def __init__(self, p=None, assets=None, verbose=True):
        # pylint: disable=too-many-arguments,too-many-branches
        if isinstance(p, Specifications):
            self.__p = copy.deepcopy(p)
        else:
            raise ValueError('must specify p as a Specifications object')
        if isinstance(assets, Assets):
            self.__assets = copy.deepcopy(assets)
        else:
            raise ValueError('must specify assets as a Assets object')
        self.__stored_assets = None

    def calc_other(self, df):
        '''
        Calculates variables that depend on z and rho
        '''
        dfs = {'c': df[df['tax_treat'] == 'corporate'].copy(),
               'nc': df[df['tax_treat'] == 'non-corporate'].copy()}
        # separate into corp and non-corp dataframe here
        for t in self.__p.entity_list:
            for f in self.__p.financing_list:
                dfs[t]['ucc_' + str(f)] = eq_ucc(
                    dfs[t]['rho_' + str(f)], dfs[t]['delta'])
                dfs[t]['metr_' + str(f)] = eq_metr(
                    dfs[t]['rho_' + str(f)], self.__p.r_prime[t][f],
                    self.__p.inflation_rate)
                dfs[t]['mettr_' + str(f)] = eq_mettr(
                    dfs[t]['rho_' + str(f)], self.__p.s[t][f])
                dfs[t]['tax_wedge_' + str(f)] = eq_tax_wedge(
                    dfs[t]['rho_' + str(f)], self.__p.s[t][f])
                dfs[t]['eatr_' + str(f)] = eq_eatr(
                    dfs[t]['rho_' + str(f)], dfs[t]['metr_' + str(f)],
                    self.__p.profit_rate, self.__p.u[t])
        df = pd.concat(dfs, ignore_index=True, copy=True)

        return df

    def calc_base(self):
        """
        Call functions for the current_year.  This involves
        updating depreciation methods, computing the npv of depreciation
        (z), and computing the cost of capital (rho) and then calling
        the calc_all() function to do computations that dependon rho and
        z.
        """
        # conducts static analysis of Calculator object for current_year
        self.__assets.df = update_depr_methods(self.__assets.df,
                                               self.__p)
        dfs = {'c': self.__assets.df[
               self.__assets.df['tax_treat'] == 'corporate'].copy(),
               'nc': self.__assets.df[
               self.__assets.df['tax_treat'] == 'non-corporate'].copy()}
        # separate into corp and non-corp dataframe here
        for t in self.__p.entity_list:
            for f in self.__p.financing_list:
                dfs[t]['z_' + str(f)] = npv_tax_depr(
                    dfs[t], self.__p.r[t][f], self.__p.inflation_rate,
                    self.__p.land_expensing)
                dfs[t]['rho_' + str(f)] = eq_coc(
                    dfs[t]['delta'], dfs[t]['z_' + str(f)],
                    self.__p.property_tax,
                    self.__p.u[t], self.__p.inv_tax_credit,
                    self.__p.inflation_rate, self.__p.r[t][f])
                if not self.__p.inventory_expensing:
                    idx = dfs[t]['asset_name'] == 'Inventories'
                    dfs[t].loc[idx, 'rho_' + str(f)] = eq_coc_inventory(
                        self.__p.u[t], self.__p.phi, self.__p.Y_v,
                        self.__p.inflation_rate, self.__p.r[t][f])
        self.__assets.df = pd.concat(dfs, ignore_index=True, copy=True,
                                     sort=True)

    def calc_all(self):
        '''
        Calculates all CCC variables for some CCC Assets object.
        '''
        self.calc_base()
        self.__assets.df = self.calc_other(self.__assets.df)

    def calc_by_asset(self):
        '''
        Calculates all variables by asset, including overall, and by
        major asset categories.
        '''
        self.calc_base()
        asset_df = pd.DataFrame(self.__assets.df.groupby(
            ['major_asset_group', 'bea_asset_code', 'asset_name',
             'tax_treat']).apply(self.__f)).reset_index()
        asset_df = self.calc_other(asset_df)
        major_asset_df = pd.DataFrame(self.__assets.df.groupby(
            ['major_asset_group', 'tax_treat']).apply(self.__f)).reset_index()
        major_asset_df['asset_name'] = major_asset_df['major_asset_group']
        major_asset_df = self.calc_other(major_asset_df)
        # Can put some if statements here if want to exclude land/inventory/etc
        overall_df = pd.DataFrame(self.__assets.df.groupby(
            ['tax_treat']).apply(self.__f)).reset_index()
        overall_df['major_asset_group'] = 'Overall'
        overall_df['asset_name'] = 'Overall'
        overall_df = self.calc_other(overall_df)
        df = pd.concat([asset_df, major_asset_df, overall_df],
                       ignore_index=True, copy=True,
                       sort=True).reset_index()
        # Drop duplicate rows in case, e.g., only one asset in major
        # asset group
        df.drop_duplicates(subset=['asset_name', 'major_asset_group',
                                   'tax_treat'], inplace=True)

        return df

    def calc_by_industry(self):
        '''
        Calculates all variables by industry, including overall, and by
        major asset categories.
        '''
        self.calc_base()
        ind_df = pd.DataFrame(self.__assets.df.groupby(
            ['major_industry', 'bea_ind_code', 'Industry',
             'tax_treat']).apply(self.__f)).reset_index()
        ind_df = self.calc_other(ind_df)
        major_ind_df = pd.DataFrame(self.__assets.df.groupby(
            ['major_industry', 'tax_treat']).apply(self.__f)).reset_index()
        major_ind_df['Industry'] = major_ind_df['major_industry']
        major_ind_df = self.calc_other(major_ind_df)
        # Can put some if statements here if want to exclude land/inventory/etc
        overall_df = pd.DataFrame(self.__assets.df.groupby(
            ['tax_treat']).apply(self.__f)).reset_index()
        overall_df['major_industry'] = 'Overall'
        overall_df['Industry'] = 'Overall'
        overall_df = self.calc_other(overall_df)
        df = pd.concat([ind_df, major_ind_df, overall_df],
                       ignore_index=True, copy=True,
                       sort=True).reset_index()
        # Drop duplicate rows in case, e.g., only one industry in major
        # industry group
        df.drop_duplicates(subset=['Industry', 'major_industry',
                                   'tax_treat'], inplace=True)

        return df

    def summary_table(self, calc, output_variable='mettr',
                      include_land=True, include_inventories=True,
                      output_type='csv', path=''):
        '''
        Create table summarizing the output_variable under the baseline
        and reform policies.

        Args:
            calc : Calculator object
                calc represents the reform while self represents the baseline
            output_variable : string
                specifies which output variable to summarize in the table
            include_land : boolean
                specifies whether to include land in overall calculations
            include_inventories : boolean
                specifies whether to include inventories in overall calculations
            output_type : string
                specifies the type of file to save table to:
                    - 'csv'
                    - 'tex'
                    - 'excel'
                    - 'json'
            path : string
                specifies path to save file with table to

        Returns:
            None, table saved to disk
        '''
        self.calc_base()
        calc.calc_base()
        base_df = self.__assets.df
        reform_df = calc.__assets.df
        dfs = [base_df, reform_df]
        dfs_out = []
        for df in dfs:
            if not include_land:
                df = df.drop(df[df.asset_name == 'Land'].index,
                             inplace=True)
            if not include_inventories:
                df = df.drop(df[df.asset_name == 'Inventories'].index,
                             inplace=True)
            # Compute overall separately by tax treatment
            treat_df = pd.DataFrame(df.groupby(
                ['tax_treat']).apply(self.__f)).reset_index()
            treat_df = self.calc_other(treat_df)
            # Compute overall values, across corp and non-corp
            # just making up a column with same value in all rows so can
            # continute to use groupby
            df['include'] = 1
            all_df = pd.DataFrame.from_dict(
                df.groupby(['include']).apply(self.__f).to_dict())
            # set tax_treat to corporate b/c only corp and non-corp
            # recognized in calc_other()
            all_df['tax_treat'] = 'corporate'
            all_df = self.calc_other(all_df)
            all_df['tax_treat'] = 'all'
            # Put df's together
            dfs_out.append(pd.concat([treat_df, all_df],
                                     ignore_index=True, copy=True,
                                     sort=True).reset_index())
        base_tab = dfs_out[0]
        reform_tab = dfs_out[1]
        # print('reform table = ', reform_tab)
        diff_tab = diff_two_tables(base_tab, reform_tab)
        table_dict = {
            '': ['Overall', 'Corporations', '   Equity Financed',
                 '   Debt Financed', 'Pass-Through Entities',
                 '   Equity Financed', '   Debt Financed'],
            VAR_DICT[output_variable]: [
                reform_tab[
                    reform_tab['tax_treat'] ==
                    'all'][output_variable + '_mix'].values[0],
                reform_tab[
                    reform_tab['tax_treat'] ==
                    'corporate'][output_variable + '_mix'].values[0],
                reform_tab[
                    reform_tab['tax_treat'] ==
                    'corporate'][output_variable + '_e'].values[0],
                reform_tab[
                    reform_tab['tax_treat'] ==
                    'corporate'][output_variable + '_d'].values[0],
                reform_tab[
                    reform_tab['tax_treat'] ==
                    'non-corporate'][output_variable + '_mix'].values[0],
                reform_tab[
                    reform_tab['tax_treat'] ==
                    'non-corporate'][output_variable + '_e'].values[0],
                reform_tab[
                    reform_tab['tax_treat'] ==
                    'non-corporate'][output_variable + '_d'].values[0]],
            'Change from Baseline (pp)': [
                diff_tab[
                    diff_tab['tax_treat'] ==
                    'all'][output_variable + '_mix'].values[0],
                diff_tab[
                    diff_tab['tax_treat'] ==
                    'corporate'][output_variable + '_mix'].values[0],
                diff_tab[
                    diff_tab['tax_treat'] ==
                    'corporate'][output_variable + '_e'].values[0],
                diff_tab[
                    diff_tab['tax_treat'] ==
                    'corporate'][output_variable + '_d'].values[0],
                diff_tab[
                    diff_tab['tax_treat'] ==
                    'non-corporate'][output_variable + '_mix'].values[0],
                diff_tab[
                    diff_tab['tax_treat'] ==
                    'non-corporate'][output_variable + '_e'].values[0],
                diff_tab[
                    diff_tab['tax_treat'] ==
                    'non-corporate'][output_variable + '_d'].values[0]]}
        # Make df with dict so can use pandas functions
        table_df = pd.DataFrame.from_dict(table_dict, orient='columns')
        if output_type == 'tex':
            table_df.to_latex(buf=path, index=False, na_rep='',
                              float_format=lambda x: '%.2f' % x)
        elif output_type == 'csv':
            table_df.to_csv(path_or_buf=path, index=False, na_rep='',
                            float_format="%.2f")
        elif output_type == 'json':
            table_df.to_json(path_or_buf=path, double_precision=2)
        elif output_type == 'excel':
            table_df.to_excel(excel_writer=path, index=False, na_rep='',
                              float_format="%.2f")
        else:
            print('Please enter a valid output format')
            assert(False)

    def asset_bubble_plot(self, calc, output_variable, include_land,
                          include_inventories, path):
        '''
        Create table summarizing the output_variable under the baseline
        and reform policies.

        Args:
            calc : Calculator object
                calc represents the reform while self represents the baseline
            output_variable : string
                specifies which output variable to summarize in the plot
            include_land : boolean
                specifies whether to include land in overall calculations
            include_inventories : boolean
                specifies whether to include inventories in overall calculations
            path : string
                specifies path to save file with table to

        Returns:
            None, table saved to disk
        '''
        

    def store_assets(self):
        """
        Make internal copy of embedded Assets object that can then be
        restored after interim calculations that make temporary changes
        to the embedded Assets object.
        """
        assert self.__stored_assets is None
        self.__stored_assets = copy.deepcopy(self.__assets)

    def restore_assets(self):
        """
        Set the embedded Assets object to the stored Assets object
        that was saved in the last call to the store_assets() method.
        """
        assert isinstance(self.__stored_assets, Assets)
        self.__assets = copy.deepcopy(self.__stored_assets)
        del self.__stored_assets
        self.__stored_assets = None

    def p_param(self, param_name, param_value=None):
        """
        If param_value is None, return named parameter in
         embedded Specifications object.
        If param_value is not None, set named parameter in
         embedded Specifications object to specified param_value and
         return None (which can be ignored).
        """
        if param_value is None:
            return getattr(self.__p, param_name)
        setattr(self.__p, param_name, param_value)
        return None

    @property
    def reform_warnings(self):
        """
        Calculator class embedded Specifications object's reform_warnings.
        """
        return self.__p.parameter_warnings

    @property
    def current_year(self):
        """
        Calculator class current calendar year property.
        """
        return self.__p.current_year

    @property
    def data_year(self):
        """
        Calculator class initial (i.e., first) assets data year property.
        """
        return self.__assets.data_year

    def __f(self, x):
        '''
        Private method.  A fuction to compute sums and weighted averages
        from a groubpy object.
        '''
        d = {}
        d['assets'] = x['assets'].sum()
        d['delta'] = wavg(x, 'delta', 'assets')
        d['rho_mix'] = wavg(x, 'rho_mix', 'assets')
        d['rho_d'] = wavg(x, 'rho_d', 'assets')
        d['rho_e'] = wavg(x, 'rho_e', 'assets')
        d['z_mix'] = wavg(x, 'z_mix', 'assets')
        d['z_d'] = wavg(x, 'z_d', 'assets')
        d['z_e'] = wavg(x, 'z_e', 'assets')

        return pd.Series(d, index=['assets', 'delta', 'rho_mix', 'rho_d',
                                   'rho_e', 'z_mix', 'z_d', 'z_e'])

# Can put functions for tabular, text, graphical output here
# create function to have table like CBO with groupings
# create function to have bubble plot
# create function to have tables like old B-Tax output?
