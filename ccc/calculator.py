'''
Cost-of-Capital-Calculator Calculator class.
'''
# CODING-STYLE CHECKS:
# pycodestyle calculator.py
# pylint --disable=locally-disabled calculator.py
#
# pylint: disable=invalid-name,no-value-for-parameter,too-many-lines

import copy
import pandas as pd
import numpy as np
from ccc.calcfunctions import (update_depr_methods, npv_tax_depr,
                               eq_coc, eq_coc_inventory, eq_ucc,
                               eq_metr, eq_mettr, eq_tax_wedge, eq_eatr)
from ccc.parameters import Specification, DepreciationParams
from ccc.data import Assets
from ccc.utils import wavg, diff_two_tables, save_return_table
from ccc.constants import (VAR_DICT, MAJOR_IND_ORDERED, OUTPUT_VAR_LIST,
                           OUTPUT_DATA_FORMATS)
# import pdb
# importing Bokeh libraries
from bokeh.plotting import figure
from bokeh.transform import dodge
from bokeh.models import (ColumnDataSource, CustomJS, LabelSet, Title,
                          FuncTickFormatter, BoxAnnotation, HoverTool,
                          NumeralTickFormatter, Span)
from bokeh.models.widgets import Panel, Tabs, RadioButtonGroup
from bokeh.models.tickers import FixedTicker
from bokeh.layouts import gridplot, column


# import styles and callback
from ccc.styles import (PLOT_FORMATS, TITLE_FORMATS, RED, BLUE)
from ccc.controls_callback_script import CONTROLS_CALLBACK_SCRIPT


class Calculator():
    '''
    Constructor for the Calculator class.

    Args:
        p (CCC Specifications class object): contains parameters, this
            argument must be specified and object is copied for internal
            use
        dp (CCC Depreciation Parameters class object): contains parameters
            descripting depreciation rules for each asset, this argument
            must be specified and object is copied for internal use
        assets (CCC Assets class object): contains asset data, this
            argument must be specified and object is copied for
            internal use
        verbose (bool): specifies whether or not to write to stdout
            data-loaded and data-extrapolated progress reports; default
            value is `True`.

    Raises:
        ValueError: if parameters are not the appropriate type.

    Returns:
        Calculator: class instance

    Notes:
        All calculations are done on the internal copies of the
        Specifications and Assets objects passed to each of the two
        Calculator constructors.

    Example:
        The most efficient way to specify current-law and reform Calculator
            objects is as follows::
                >>> `params = Specifications()``
                >>> `rec = Assets()``
                >>> `calc1 = Calculator(p=params, assets=rec)  # current-law`
                >>> `params2 = Specifications(...reform parameters...)``
                >>> `calc2 = Calculator(p=params2, assets=rec)  # reform`

    '''
    # pylint: disable=too-many-public-methods

    def __init__(self, p=None, dp=None, assets=None, verbose=True):
        # pylint: disable=too-many-arguments,too-many-branches
        if isinstance(p, Specification):
            self.__p = copy.deepcopy(p)
        else:
            raise ValueError('must specify p as a Specification object')
        if isinstance(dp, DepreciationParams):
            self.__dp = copy.deepcopy(dp)
        else:
            raise ValueError('must specify p as an DepreciationParams object')
        if isinstance(assets, Assets):
            self.__assets = copy.deepcopy(assets)
        else:
            raise ValueError('must specify assets as a Assets object')
        self.__stored_assets = None

    def calc_other(self, df):
        '''
        Calculates variables that depend on z and rho such as metr, ucc

        Args:
            df (Pandas DataFrame): assets by indusry and tax_treatment
                with depreciation rates, cost of capital, etc.

        Returns:
            df (Pandas DataFrame): input dataframe, but with additional
                columns (ucc, metr, mettr, tax_wedge, eatr)

        '''
        dfs = {'c': df[df['tax_treat'] == 'corporate'].copy(),
               'pt': df[df['tax_treat'] == 'non-corporate'].copy()}
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
        '''
        Call functions for the current_year.  This involves
        updating depreciation methods, computing the npv of depreciation
        (z), and computing the cost of capital (rho) and then calling
        the calc_all() function to do computations that dependon rho and
        z.

        '''
        # conducts static analysis of Calculator object for current_year
        self.__assets.df = update_depr_methods(
            self.__assets.df, self.__p, self.__dp)
        dfs = {'c': self.__assets.df[
               self.__assets.df['tax_treat'] == 'corporate'].copy(),
               'pt': self.__assets.df[
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
                    dfs[t].loc[idx, 'rho_' + str(f)] = np.squeeze(
                        eq_coc_inventory(
                            self.__p.u[t], self.__p.phi, self.__p.Y_v,
                            self.__p.inflation_rate, self.__p.r[t][f]))
        self.__assets.df = pd.concat(dfs, ignore_index=True, copy=True,
                                     sort=True)

    def calc_all(self):
        '''
        Calculates all CCC variables for some CCC Assets object.

        '''
        self.calc_base()
        self.__assets.df = self.calc_other(self.__assets.df)

    def calc_by_asset(self, include_inventories=True,
                      include_land=True):
        '''
        Calculates all variables by asset, including overall, and by
        major asset categories.

        Args:
            include_inventories (bool): whether to include inventories
                in calculations.  Defaults to `True`.
            include_land (bool): whether to include land in
                calculations.  Defaults to `True`.

        Returns:
            df (pandas DataFrame): rows are assets and major asset
                groupings with columns for all output variables

        '''
        self.calc_base()
        asset_df = pd.DataFrame(self.__assets.df.groupby(
            ['major_asset_group', 'minor_asset_group', 'bea_asset_code',
             'asset_name', 'tax_treat']).apply(self.__f)).reset_index()
        asset_df = self.calc_other(asset_df)
        # Find values across minor asset groups
        minor_asset_df = pd.DataFrame(self.__assets.df.groupby(
            ['minor_asset_group', 'major_asset_group',
             'tax_treat']).apply(self.__f)).reset_index()
        minor_asset_df['asset_name'] =\
            minor_asset_df['minor_asset_group']
        minor_asset_df = self.calc_other(minor_asset_df)
        # Find values across major asset_groups
        major_asset_df = pd.DataFrame(self.__assets.df.groupby(
            ['major_asset_group', 'tax_treat']).apply(self.__f)).reset_index()
        major_asset_df['minor_asset_group'] =\
            major_asset_df['major_asset_group']
        major_asset_df['asset_name'] = major_asset_df['major_asset_group']
        major_asset_df = self.calc_other(major_asset_df)
        # Drop land and inventories if conditions met
        df1 = self.__assets.df
        if not include_land:
            df1.drop(df1[df1.asset_name == 'Land'].index, inplace=True)
        if not include_inventories:
            df1.drop(df1[df1.asset_name == 'Inventories'].index,
                     inplace=True)
        overall_df = pd.DataFrame(df1.groupby(
            ['tax_treat']).apply(self.__f)).reset_index()
        overall_df['major_asset_group'] = 'Overall'
        overall_df['minor_asset_group'] = 'Overall'
        overall_df['asset_name'] = 'Overall'
        overall_df = self.calc_other(overall_df)
        df = pd.concat([asset_df, minor_asset_df, major_asset_df,
                        overall_df], ignore_index=True, copy=True,
                       sort=True).reset_index()
        # Drop duplicate rows in case, e.g., only one asset in major
        # or minor asset group
        df.drop_duplicates(subset=['asset_name', 'minor_asset_group',
                                   'major_asset_group', 'tax_treat'],
                           inplace=True)

        return df

    def calc_by_industry(self, include_inventories=True,
                         include_land=True):
        '''
        Calculates all variables by industry, including overall, and by
        major asset categories.

        Args:
            include_inventories (bool): whether to include inventories
                in calculations.  Defaults to `True`.
            include_land (bool): whether to include land in
                calculations.  Defaults to `True`.

        Returns:
            df (Pandas DataFrame): rows are minor industries and major
                industry groupings with columns for all output variables

        '''
        self.calc_base()
        df1 = self.__assets.df
        if not include_land:
            df1.drop(df1[df1.asset_name == 'Land'].index, inplace=True)
        if not include_inventories:
            df1.drop(df1[df1.asset_name == 'Inventories'].index,
                     inplace=True)
        ind_df = pd.DataFrame(df1.groupby(
            ['major_industry', 'bea_ind_code', 'Industry',
             'tax_treat']).apply(self.__f)).reset_index()
        ind_df = self.calc_other(ind_df)
        major_ind_df = pd.DataFrame(df1.groupby(
            ['major_industry', 'tax_treat']).apply(self.__f)).reset_index()
        major_ind_df['Industry'] = major_ind_df['major_industry']
        major_ind_df = self.calc_other(major_ind_df)
        # Can put some if statements here if want to exclude land/inventory/etc
        overall_df = pd.DataFrame(df1.groupby(
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
                      output_type=None, path=None):
        '''
        Create table summarizing the output_variable under the baseline
        and reform policies.

        Args:
            calc (CCC Calculator object): calc represents the reform
                while self represents the baseline
            output_variable (string): specifies which output variable to
                summarize in the table.  Default is the marginal
                effective total tax rate (`mettr`).
            include_inventories (bool): whether to include inventories
                in calculations.  Defaults to `True`.
            include_land (bool): whether to include land in
                calculations.  Defaults to `True`.
            output_type (string): specifies the type of file to save
                table to: 'csv', 'tex', 'excel', 'json'.  If 'None' a
                DataFrame is returned. Default is None.
            path (string): specifies path to save file with table to.
                If `None`, then returns DataFrame or string object,
                depending on `output_type`. Default is `None`.

        Returns:
            table_df (Pandas DataFrame): table

        '''
        assert output_variable in OUTPUT_VAR_LIST
        assert output_type in OUTPUT_DATA_FORMATS
        self.calc_base()
        calc.calc_base()
        base_df = self.__assets.df
        reform_df = calc.__assets.df
        dfs = [base_df, reform_df]
        dfs_out = []
        for df in dfs:
            if not include_land:
                df.drop(df[df.asset_name == 'Land'].index, inplace=True)
            if not include_inventories:
                df.drop(df[df.asset_name == 'Inventories'].index,
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
        diff_tab = diff_two_tables(reform_tab, base_tab)
        table_dict = {
            '': ['Overall', 'Corporations', '   Equity Financed',
                 '   Debt Financed', 'Pass-Through Entities',
                 '   Equity Financed', '   Debt Financed'],
            VAR_DICT[output_variable] + ' Under Baseline Policy': [
                base_tab[
                    base_tab['tax_treat'] ==
                    'all'][output_variable + '_mix'].values[0],
                base_tab[
                    base_tab['tax_treat'] ==
                    'corporate'][output_variable + '_mix'].values[0],
                base_tab[
                    base_tab['tax_treat'] ==
                    'corporate'][output_variable + '_e'].values[0],
                base_tab[
                    base_tab['tax_treat'] ==
                    'corporate'][output_variable + '_d'].values[0],
                base_tab[
                    base_tab['tax_treat'] ==
                    'non-corporate'][output_variable + '_mix'].values[0],
                base_tab[
                    base_tab['tax_treat'] ==
                    'non-corporate'][output_variable + '_e'].values[0],
                base_tab[
                    base_tab['tax_treat'] ==
                    'non-corporate'][output_variable + '_d'].values[0]],
            VAR_DICT[output_variable] + ' Under Reform Policy': [
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
        # Put in percentage points
        table_df[VAR_DICT[output_variable] +
                 ' Under Baseline Policy'] *= 100
        table_df[VAR_DICT[output_variable] +
                 ' Under Reform Policy'] *= 100
        table_df['Change from Baseline (pp)'] *= 100
        table = save_return_table(table_df, output_type, path)

        return table

    def asset_share_table(self, include_land=True,
                          include_inventories=True, output_type=None,
                          path=None):
        '''
        Create table summarizing the output_variable under the baseline
        and reform policies.

        Args:
            include_inventories (bool): whether to include inventories
                in calculations.  Defaults to `True`.
            include_land (bool): whether to include land in
                calculations.  Defaults to `True`.
            output_type (string): specifies the type of file to save
                table to: 'csv', 'tex', 'excel', 'json'.  If 'None' a
                DataFrame is returned. Default is None.
            path (string): specifies path to save file with table to.
                If `None`, then returns DataFrame or string object,
                depending on `output_type`. Default is `None`.

        Returns:
            table_df (Pandas DataFrame): table

        '''
        assert output_type in OUTPUT_DATA_FORMATS
        df = self.__assets.df.copy()
        if not include_land:
            df.drop(df[df.asset_name == 'Land'].index, inplace=True)
        if not include_inventories:
            df.drop(df[df.asset_name == 'Inventories'].index,
                    inplace=True)
        df1 = pd.DataFrame(df.groupby(
                ['tax_treat', 'major_industry'])
                          ['assets'].sum()).reset_index()
        df2 = df1.pivot(index='major_industry', columns='tax_treat',
                        values='assets').reset_index()
        df2['c_share'] = (df2['corporate'] / (df2['corporate'] +
                                              df2['non-corporate']))
        df2['nc_share'] = (df2['non-corporate'] / (df2['corporate'] +
                                                   df2['non-corporate']))
        df2.drop(labels=['corporate', 'non-corporate'], axis=1,
                 inplace=True)
        df2.rename(columns={'c_share': 'Corporate',
                            'nc_share': 'Pass-Through',
                            'major_industry': 'Industry'}, inplace=True)
        # Create dictionary for table to get industry's in specific order
        table_dict = {'Industry': [], 'Corporate': [], 'Pass-Through': []}
        for item in MAJOR_IND_ORDERED:
            table_dict['Industry'].append(item)
            table_dict['Corporate'].append(
                df2[df2.Industry == item]['Corporate'].values[0])
            table_dict['Pass-Through'].append(
                df2[df2.Industry == item]['Pass-Through'].values[0])
        table_df = pd.DataFrame.from_dict(table_dict, orient='columns')
        table = save_return_table(table_df, output_type, path,
                                  precision=2)

        return table

    def asset_summary_table(self, calc, output_variable='mettr',
                            financing='mix', include_land=True,
                            include_inventories=True, output_type=None,
                            path=None):
        '''
        Create table summarizing the output_variable under the baseline
        and reform policies by major asset grouping.

        Args:
            calc (CCC Calculator object): calc represents the reform
                while self represents the baseline
            output_variable (string): specifies which output variable to
                summarize in the table.  Default is the marginal
                effective total tax rate (`mettr`).
            financing (string): marginal source of finance for the new
                investment: 'mix' for mix of debt and equity, 'd' for
                debt, or 'e' for equity.
            include_inventories (bool): whether to include inventories
                in calculations.  Defaults to `True`.
            include_land (bool): whether to include land in
                calculations.  Defaults to `True`.
            output_type (string): specifies the type of file to save
                table to: 'csv', 'tex', 'excel', 'json'.  If 'None' a
                DataFrame is returned. Default is None.
            path (string): specifies path to save file with table to.
                If `None`, then returns DataFrame or string object,
                depending on `output_type`. Default is `None`.

        Returns:
            table_df (Pandas DataFrame): table

        '''
        assert financing in self.__p.financing_list
        assert output_variable in OUTPUT_VAR_LIST
        assert output_type in OUTPUT_DATA_FORMATS
        self.calc_base()
        calc.calc_base()
        base_df = self.__assets.df
        reform_df = calc.__assets.df
        dfs = [base_df, reform_df]
        dfs_out = []
        for df in dfs:
            if not include_land:
                df.drop(df[df.asset_name == 'Land'].index, inplace=True)
            if not include_inventories:
                df.drop(df[df.asset_name == 'Inventories'].index,
                        inplace=True)
            # Make dataframe with just results for major asset cateogries
            major_asset_df = pd.DataFrame(df.groupby(
                ['major_asset_group',
                 'tax_treat']).apply(self.__f)).reset_index()
            major_asset_df['asset_name'] =\
                major_asset_df['major_asset_group']
            major_asset_df = self.calc_other(major_asset_df)
            # Compute overall separately by tax treatment
            treat_df = pd.DataFrame(df.groupby(
                ['tax_treat']).apply(self.__f)).reset_index()
            treat_df = self.calc_other(treat_df)
            treat_df['major_asset_group'] = 'Overall'
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
            all_df['major_asset_group'] = 'Overall'
            # Put df's together
            dfs_out.append(pd.concat([major_asset_df, treat_df, all_df],
                                     ignore_index=True, copy=True,
                                     sort=True).reset_index())
        base_tab = dfs_out[0]
        reform_tab = dfs_out[1]
        diff_tab = diff_two_tables(reform_tab, base_tab)
        major_groups = ['Equipment', 'Structures',
                        'Intellectual Property']
        if include_inventories:
            major_groups.append('Inventories')
        if include_land:
            major_groups.append('Land')
        category_list = ['Overall', 'Corporate']
        base_out_list = [
            base_tab[base_tab['tax_treat'] ==
                     'all'][output_variable + '_' + financing].values[0],
            base_tab[(
                base_tab['tax_treat'] == 'corporate') &
                     (base_tab['major_asset_group'] == 'Overall')]
            [output_variable + '_' + financing].values[0]]
        reform_out_list = [
            reform_tab[reform_tab['tax_treat'] == 'all']
            [output_variable + '_' + financing].values[0],
            reform_tab[(
                reform_tab['tax_treat'] == 'corporate') &
                     (reform_tab['major_asset_group'] == 'Overall')]
            [output_variable + '_' + financing].values[0]]
        diff_out_list = [
            diff_tab[diff_tab['tax_treat'] == 'all']
            [output_variable + '_' + financing].values[0],
            diff_tab[(
                diff_tab['tax_treat'] == 'corporate') &
                     (diff_tab['major_asset_group'] == 'Overall')]
            [output_variable + '_' + financing].values[0]]
        for item in major_groups:
            category_list.append('   ' + item)
            base_out_list.append(
                base_tab[(base_tab['tax_treat'] == 'corporate') &
                         (base_tab['major_asset_group'] == item)]
                [output_variable + '_' + financing].values[0])
            reform_out_list.append(
                reform_tab[(reform_tab['tax_treat'] == 'corporate') &
                           (reform_tab['major_asset_group'] == item)]
                [output_variable + '_' + financing].values[0])
            diff_out_list.append(
                diff_tab[(diff_tab['tax_treat'] == 'corporate') &
                         (diff_tab['major_asset_group'] == item)]
                [output_variable + '_' + financing].values[0])
        category_list.append('Pass-through')
        base_out_list.append(base_tab[
            (base_tab['tax_treat'] == 'non-corporate') &
            (base_tab['major_asset_group'] == 'Overall')]
                             [output_variable + '_' + financing].values[0])
        reform_out_list.append(reform_tab[
            (reform_tab['tax_treat'] == 'non-corporate') &
            (reform_tab['major_asset_group'] == 'Overall')]
                               [output_variable + '_' + financing].values[0])
        diff_out_list.append(diff_tab[
            (diff_tab['tax_treat'] == 'non-corporate') &
            (diff_tab['major_asset_group'] == 'Overall')]
                             [output_variable + '_' + financing].values[0])
        for item in major_groups:
            category_list.append('   ' + item)
            base_out_list.append(
                base_tab[(base_tab['tax_treat'] == 'non-corporate') &
                         (base_tab['major_asset_group'] == item)]
                [output_variable + '_' + financing].values[0])
            reform_out_list.append(
                reform_tab[
                    (reform_tab['tax_treat'] == 'non-corporate') &
                    (reform_tab['major_asset_group'] == item)]
                [output_variable + '_' + financing].values[0])
            diff_out_list.append(
                diff_tab[
                    (diff_tab['tax_treat'] == 'non-corporate') &
                    (diff_tab['major_asset_group'] == item)]
                [output_variable + '_' + financing].values[0])
        table_dict = {
            'Category': category_list,
            VAR_DICT[output_variable] + ' Under Baseline Policy':
            base_out_list,
            VAR_DICT[output_variable] + ' Under Reform Policy':
            reform_out_list,
            'Change from Baseline (pp)': diff_out_list}
        # Make df with dict so can use pandas functions
        table_df = pd.DataFrame.from_dict(table_dict, orient='columns')
        # Put in percentage points
        table_df[VAR_DICT[output_variable] +
                 ' Under Baseline Policy'] *= 100
        table_df[VAR_DICT[output_variable] +
                 ' Under Reform Policy'] *= 100
        table_df['Change from Baseline (pp)'] *= 100
        table = save_return_table(table_df, output_type, path)

        return table

    def industry_summary_table(self, calc, output_variable='mettr',
                               financing='mix', include_land=True,
                               include_inventories=True,
                               output_type=None, path=None):
        '''
        Create table summarizing the output_variable under the baseline
        and reform policies by major asset grouping.

        Args:
            calc (CCC Calculator object): calc represents the reform
                while self represents the baseline
            output_variable (string): specifies which output variable to
                summarize in the table.  Default is the marginal
                effective total tax rate (`mettr`).
            financing (string): marginal source of finance for the new
                investment: 'mix' for mix of debt and equity, 'd' for
                debt, or 'e' for equity.
            include_inventories (bool): whether to include inventories
                in calculations.  Defaults to `True`.
            include_land (bool): whether to include land in
                calculations.  Defaults to `True`.
            output_type (string): specifies the type of file to save
                table to: 'csv', 'tex', 'excel', 'json'.  If 'None' a
                DataFrame is returned. Default is None.
            path (string): specifies path to save file with table to.
                If `None`, then returns DataFrame or string object,
                depending on `output_type`. Default is `None`.

        Returns:
            table_df (Pandas DataFrame): table

        '''
        assert financing in self.__p.financing_list
        assert output_variable in OUTPUT_VAR_LIST
        assert output_type in OUTPUT_DATA_FORMATS
        self.calc_base()
        calc.calc_base()
        base_df = self.__assets.df
        reform_df = calc.__assets.df
        dfs = [base_df, reform_df]
        dfs_out = []
        for df in dfs:
            if not include_land:
                df.drop(df[df.asset_name == 'Land'].index, inplace=True)
            if not include_inventories:
                df.drop(df[df.asset_name == 'Inventories'].index,
                        inplace=True)
            # Make dataframe with just results for major industry
            major_ind_df = pd.DataFrame(df.groupby(
                ['major_industry', 'tax_treat']).apply(
                    self.__f)).reset_index()
            major_ind_df['Industry'] = major_ind_df['major_industry']
            major_ind_df = self.calc_other(major_ind_df)
            # Compute overall separately by tax treatment
            treat_df = pd.DataFrame(df.groupby(
                ['tax_treat']).apply(self.__f)).reset_index()
            treat_df = self.calc_other(treat_df)
            treat_df['major_industry'] = 'Overall'
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
            all_df['major_industry'] = 'Overall'
            # Put df's together
            dfs_out.append(pd.concat([major_ind_df, treat_df, all_df],
                                     ignore_index=True, copy=True,
                                     sort=True).reset_index())
        base_tab = dfs_out[0]
        reform_tab = dfs_out[1]
        diff_tab = diff_two_tables(reform_tab, base_tab)
        category_list = ['Overall', 'Corporate']
        base_out_list = [
            base_tab[base_tab['tax_treat'] ==
                     'all'][output_variable + '_' + financing].values[0],
            base_tab[(base_tab['tax_treat'] == 'corporate') &
                     (base_tab['major_industry'] == 'Overall')]
            [output_variable + '_' + financing].values[0]]
        reform_out_list = [
            reform_tab[reform_tab['tax_treat'] == 'all']
            [output_variable + '_' + financing].values[0],
            reform_tab[(reform_tab['tax_treat'] == 'corporate') &
                       (reform_tab['major_industry'] == 'Overall')]
            [output_variable + '_' + financing].values[0]]
        diff_out_list = [
            diff_tab[diff_tab['tax_treat'] == 'all']
            [output_variable + '_' + financing].values[0],
            diff_tab[(diff_tab['tax_treat'] == 'corporate') &
                     (diff_tab['major_industry'] == 'Overall')]
            [output_variable + '_' + financing].values[0]]
        for item in MAJOR_IND_ORDERED:
            category_list.append('   ' + item)
            base_out_list.append(
                base_tab[(base_tab['tax_treat'] == 'corporate') &
                         (base_tab['major_industry'] == item)]
                [output_variable + '_' + financing].values[0])
            reform_out_list.append(
                reform_tab[(reform_tab['tax_treat'] == 'corporate') &
                           (reform_tab['major_industry'] == item)]
                [output_variable + '_' + financing].values[0])
            diff_out_list.append(
                diff_tab[(diff_tab['tax_treat'] == 'corporate') &
                         (diff_tab['major_industry'] == item)]
                [output_variable + '_' + financing].values[0])
        category_list.append('Pass-through')
        base_out_list.append(base_tab[
            (base_tab['tax_treat'] == 'non-corporate') &
            (base_tab['major_industry'] == 'Overall')]
                             [output_variable + '_' + financing].values[0])
        reform_out_list.append(reform_tab[
            (reform_tab['tax_treat'] == 'non-corporate') &
            (reform_tab['major_industry'] == 'Overall')]
                               [output_variable + '_' + financing].values[0])
        diff_out_list.append(diff_tab[
            (diff_tab['tax_treat'] == 'non-corporate') &
            (diff_tab['major_industry'] == 'Overall')]
                             [output_variable + '_' + financing].values[0])
        for item in MAJOR_IND_ORDERED:
            category_list.append('   ' + item)
            base_out_list.append(
                base_tab[(base_tab['tax_treat'] == 'non-corporate') &
                         (base_tab['major_industry'] == item)]
                [output_variable + '_' + financing].values[0])
            reform_out_list.append(
                reform_tab[
                    (reform_tab['tax_treat'] == 'non-corporate') &
                    (reform_tab['major_industry'] == item)]
                [output_variable + '_' + financing].values[0])
            diff_out_list.append(
                diff_tab[
                    (diff_tab['tax_treat'] == 'non-corporate') &
                    (diff_tab['major_industry'] == item)]
                [output_variable + '_' + financing].values[0])
        table_dict = {
            'Category': category_list,
            VAR_DICT[output_variable] + ' Under Baseline Policy':
            base_out_list,
            VAR_DICT[output_variable] + ' Under Reform Policy':
            reform_out_list,
            'Change from Baseline (pp)': diff_out_list}
        # Make df with dict so can use pandas functions
        table_df = pd.DataFrame.from_dict(table_dict, orient='columns')
        # Put in percentage points
        table_df[VAR_DICT[output_variable] +
                 ' Under Baseline Policy'] *= 100
        table_df[VAR_DICT[output_variable] +
                 ' Under Reform Policy'] *= 100
        table_df['Change from Baseline (pp)'] *= 100
        table = save_return_table(table_df, output_type, path)

        return table

    def grouped_bar(self, calc, output_variable='mettr',
                    financing='mix', group_by_asset=True,
                    corporate=True, include_land=True,
                    include_inventories=True, include_title=False):
        '''
        Create a grouped bar plot (grouped by major industry or major
        asset group).

        Args:
            calc (CCC Calculator object): calc represents the reform
                while self represents the baseline
            output_variable (string): specifies which output variable to
                summarize in the table.  Default is the marginal
                effective total tax rate (`mettr`).
            financing (string): marginal source of finance for the new
                investment: 'mix' for mix of debt and equity, 'd' for
                debt, or 'e' for equity.
            group_by_asset (bool): whether to group by major asset
                group.  If `False`, then grouping is by major industry.
                Defaults to `True`.
            corporate (bool): whether to use data for corporate entities.
                If `False`, then uses data for pass-through entities.
                Defaults to `True`.
            include_inventories (bool): whether to include inventories
                in calculations.  Defaults to `True`.
            include_land (bool): whether to include land in
                calculations.  Defaults to `True`.
            include_title (bool): whether to include a title on the plot

        Returns:
            p (Bokeh plot object): bar plot

        '''
        assert financing in self.__p.financing_list
        assert output_variable in OUTPUT_VAR_LIST
        if group_by_asset:
            base_df = self.calc_by_asset(
                include_land=include_land,
                include_inventories=include_inventories)
            reform_df = calc.calc_by_asset(
                    include_land=include_land,
                    include_inventories=include_inventories
            )
            base_df.drop(base_df[base_df.asset_name !=
                                 base_df.major_asset_group].index,
                         inplace=True)
            reform_df.drop(
                reform_df[reform_df.asset_name !=
                          reform_df.major_asset_group].index,
                inplace=True)
            plot_label = 'major_asset_group'
            plot_title = VAR_DICT[output_variable] + ' by Asset Category'
        else:
            base_df = self.calc_by_industry(
                include_land=include_land,
                include_inventories=include_inventories)
            reform_df = calc.calc_by_industry(
                include_land=include_land,
                include_inventories=include_inventories)
            base_df.drop(base_df[base_df.Industry !=
                                 base_df.major_industry].index,
                         inplace=True)
            reform_df.drop(
                reform_df[reform_df.Industry !=
                          reform_df.major_industry].index,
                inplace=True)
            plot_label = 'major_industry'
            plot_title = VAR_DICT[output_variable] + ' by Industry'
        # Append dfs together so base policies in one
        base_df['policy'] = 'Baseline'
        reform_df['policy'] = 'Reform'
        df = pd.concat([base_df, reform_df])
        # Drop corporate or non-corporate per arguments
        if corporate:
            df.drop(df[df.tax_treat == 'non-corporate'].index,
                    inplace=True)
            plot_title = plot_title + ' for Corporate Investments'
        else:
            df.drop(df[df.tax_treat == 'corporate'].index,
                    inplace=True)
            plot_title = plot_title + ' for Pass-Through Investments'
        # Get mean overall for baseline and reform
        mean_base = df[(df[plot_label] == 'Overall') &
                       (df.policy == 'Baseline')][
                           output_variable + '_' + financing].values[0]
        mean_reform = df[(df[plot_label] == 'Overall') &
                         (df.policy == 'Reform')][
                             output_variable + '_' + financing].values[0]
        # Drop overall means from df
        df.drop(df[df[plot_label] == 'Overall'].index, inplace=True)
        # Drop extra vars and make wide format
        df1 = df[[plot_label, output_variable + '_mix', 'policy']]
        df2 = df1.pivot(index=plot_label, columns='policy',
                        values=output_variable + '_' + financing)
        df2.reset_index(inplace=True)
        # Create grouped barplot
        source = ColumnDataSource(data=df2)

        if not include_title:
            plot_title = None
        p = figure(x_range=df2[plot_label], plot_height=350,
                   title=plot_title, toolbar_location=None, tools="")
        p.vbar(x=dodge(plot_label,  0.0,  range=p.x_range),
               top='Baseline', width=0.2, source=source, color=BLUE,
               legend_label='Baseline')
        p.vbar(x=dodge(plot_label,  0.25, range=p.x_range),
               top='Reform', width=0.2, source=source, color=RED,
               legend_label='Reform')
        p.x_range.range_padding = 0.1
        p.xgrid.grid_line_color = None
        p.legend.location = "top_left"
        p.legend.orientation = "horizontal"
        if not group_by_asset:
            p.xaxis.major_label_orientation = 45
            p.plot_height = 800
            p.plot_width = 800

        # Add lines for overall mean for baseline and reform
        bline = Span(location=mean_base, dimension='width',
                     line_color=BLUE,
                     line_alpha=0.2, line_width=2, line_dash='dashed')
        rline = Span(location=mean_reform, dimension='width',
                     line_color=RED,
                     line_alpha=0.2, line_width=2, line_dash='dashed')
        p.renderers.extend([bline, rline])

        return p

    def range_plot(self, calc, output_variable='mettr',
                   corporate=True, include_land=True,
                   include_inventories=True, include_title=False):
        '''
        Create a range plot.

        Args:
            calc (CCC Calculator object): calc represents the reform
                while self represents the baseline
            output_variable (string): specifies which output variable to
                summarize in the table.  Default is the marginal
                effective total tax rate (`mettr`)
            corporate (bool): whether to use data for corporate entities
                If `False`, then uses data for pass-through entities
                Defaults to `True`
            include_inventories (bool): whether to include inventories
                in calculations.  Defaults to `True`
            include_land (bool): whether to include land in
                calculations.  Defaults to `True`
            include_title (bool): whether to include a title on the plot

        Returns:
            p (Bokeh plot object): bar plot

        '''
        assert output_variable in OUTPUT_VAR_LIST
        base_df = self.calc_by_asset(
            include_land=include_land,
            include_inventories=include_inventories)
        reform_df = calc.calc_by_asset(
            include_land=include_land,
            include_inventories=include_inventories)
        base_df.drop(base_df[
            (base_df.asset_name != base_df.major_asset_group) &
            (base_df.asset_name != 'Overall') &
            (base_df.asset_name != 'Land') &
            (base_df.asset_name != 'Inventories')].index, inplace=True)
        reform_df.drop(reform_df[
                (reform_df.asset_name != reform_df.major_asset_group) &
                (reform_df.asset_name != 'Overall') &
                (reform_df.asset_name != 'Land') &
                (reform_df.asset_name != 'Inventories')].index,
                       inplace=True)
        # Append dfs together so base policies in one
        base_df['policy'] = 'Baseline'
        reform_df['policy'] = 'Reform'
        # Drop corporate or non-corporate per arguments
        if corporate:
            base_df.drop(base_df[base_df.tax_treat ==
                                 'non-corporate'].index, inplace=True)
            reform_df.drop(reform_df[reform_df.tax_treat ==
                                     'non-corporate'].index,
                           inplace=True)
            plot_subtitle = 'Corporate Investments'
        else:
            base_df.drop(base_df[base_df.tax_treat ==
                                 'corporate'].index, inplace=True)
            reform_df.drop(reform_df[reform_df.tax_treat ==
                                     'corporate'].index, inplace=True)
            plot_subtitle = 'Pass-Through Investments'
        dfs = [base_df, reform_df]
        policy_list = ['baseline', 'reform']
        # Create dictionary for source data
        source_dict = {
            'baseline': {'mins': [], 'maxes': [], 'means': [],
                         'min_asset': [], 'max_asset': [],
                         'mean_asset': [],
                         'types': ["Typically Financed",
                                   "Debt Financed", "Equity Financed"],
                         'positions': [-0.1, 0.9, 1.9]},
            'reform': {'mins': [], 'maxes': [], 'means': [],
                       'min_asset': [], 'max_asset': [],
                       'mean_asset': [],
                       'types': ["Typically Financed",
                                 "Debt Financed", "Equity Financed"],
                       'positions': [0.1, 1.1, 2.1]}}
        for i, df in enumerate(dfs):
            for fin in ('_mix', '_d', '_e'):
                max_index = df[output_variable + fin].idxmax()
                min_index = df[output_variable + fin].idxmin()
                maxval = df.loc[max_index][output_variable + fin]
                minval = df.loc[min_index][output_variable + fin]
                minasset = df.loc[min_index]['asset_name']
                maxasset = df.loc[max_index]['asset_name']
                meanval = df[df.asset_name ==
                             'Overall'][output_variable + fin].values[0]
                meanasset = 'Overall'

                # put values in dictionary
                source_dict[policy_list[i]]['mins'].append(minval)
                source_dict[policy_list[i]]['maxes'].append(maxval)
                source_dict[policy_list[i]]['means'].append(meanval)
                source_dict[policy_list[i]]['min_asset'].append(minasset)
                source_dict[policy_list[i]]['max_asset'].append(maxasset)
                source_dict[policy_list[i]]['mean_asset'].append(meanasset)

        base_source = ColumnDataSource(data=source_dict['baseline'])
        reform_source = ColumnDataSource(data=source_dict['reform'])

        # Create figure on which to plot
        p = figure(plot_width=500, plot_height=500, x_range=(-0.5, 2.5),
                   toolbar_location=None, tools='')

        # Format graph title and features
        # Add title
        if include_title:
            p.add_layout(Title(text=plot_subtitle,
                               text_font_style="italic"), 'above')
            p.add_layout(Title(text=VAR_DICT[output_variable],
                               text_font_size="16pt"), 'above')
        # p.title.text = plot_title
        # p.title.align = 'center'
        # p.title.text_font_size = '16pt'
        p.title.text_font = 'Helvetica'
        p.xgrid.grid_line_color = None
        p.ygrid.grid_line_color = None

        # Format axis labels
        p.xaxis.axis_label = "Method of Financing"
        p.xaxis[0].ticker = FixedTicker(ticks=[0, 1, 2])
        # Done as a custom function instead of a categorical axis because
        # categorical axes do not work well with other features
        p.xaxis.formatter = FuncTickFormatter(code='''
        var types = ["Typically Financed", "Debt Financed", "Equity Financed"]
        return types[tick]
        ''')
        p.yaxis.axis_label = VAR_DICT[output_variable]
        p.yaxis[0].formatter = NumeralTickFormatter(format="0%")

        # Line separating positive and negative values
        zline = Span(location=0, dimension='width', line_alpha=0.2,
                     line_width=2, line_dash='dashed')
        p.renderers.extend([zline])

        # Color different regions
        standard_region = BoxAnnotation(right=0.5, fill_alpha=0.2,
                                        fill_color='white')
        debt_region = BoxAnnotation(left=0.5, right=1.5, fill_alpha=0.1,
                                    fill_color='white')
        equity_region = BoxAnnotation(left=1.5, fill_alpha=0.2,
                                      fill_color='white')

        p.add_layout(standard_region)
        p.add_layout(debt_region)
        p.add_layout(equity_region)

        # Draw baseline ranges onto graph
        p.segment('positions', 'mins', 'positions', 'maxes', color=BLUE,
                  line_width=2, source=base_source)
        # Add circles for means
        p.circle('positions', 'means', size=12, color=BLUE,
                 source=base_source, legend_label='Baseline')
        # Add circles for maxes and mins
        p.circle('positions', 'mins', size=12, color=BLUE,
                 source=base_source, legend_label='Baseline')
        p.circle('positions', 'maxes', size=12, color=BLUE,
                 source=base_source, legend_label='Baseline')

        # Draw reformed ranges onto graph
        p.segment('positions', 'mins', 'positions', 'maxes', color=RED,
                  line_width=2, source=reform_source)
        # Add circles for means
        p.circle('positions', 'means', size=12, color=RED,
                 source=reform_source, legend_label='Reform')
        # Add circles for maxes and mins
        p.circle('positions', 'mins', size=12, color=RED,
                 source=reform_source, legend_label='Reform')
        p.circle('positions', 'maxes', size=12, color=RED,
                 source=reform_source, legend_label='Reform')

        # Set legend location
        p.legend.location = "bottom_right"

        # Display rate and asset type when hovering over a glyph
        # hover = HoverTool(
        #         tooltips=[(output_variable, "@mins"),
        #                     ("Asset",  "@min_asset")])
        # p.add_tools(hover)

        return p

    def bubble_widget(self, calc, output_variable='mettr',
                      include_land=False, include_inventories=False,
                      include_IP=False):
        '''
        Create a bubble plot widget.  The x-axis shows the value of the
        output variable, the y are groups (e.g., asset type or industry).
        The widget allows for one to click buttons to view the values for
        different output variables, choose to look at the baseline
        policy values, the reform policy values, or the difference,
        switch between values for the corporate and non-corporate
        sector.  The bubbles' size represent the total assets of a
        specific type.

        Args:
            calc (CCC Calculator object): calc represents the reform
                while self represents the baseline
            output_variable (string): specifies which output variable to
                summarize in the table.  Default is the marginal
                effective total tax rate (`mettr`)
            include_inventories (bool): whether to include inventories
                in calculations.  Defaults to `False`
            include_land (bool): whether to include land in
                calculations.  Defaults to `False`
            include_IP (bool): whether to include intellectual
                property in calculations.  Defaults to `False`

        Returns:
            layout (Bokeh Layout object): widget

        '''
        assert output_variable in OUTPUT_VAR_LIST
        base_df = self.calc_by_asset()
        reform_df = calc.calc_by_asset()
        change_df = diff_two_tables(reform_df, base_df)

        list_df = [base_df, change_df, reform_df]
        list_string = ['base', 'change', 'reform']

        data_sources = {}
        for i, df_i in enumerate(list_df):
            for t in ['c', 'pt']:
                if t == 'c':
                    df = df_i.drop(df_i[df_i.tax_treat !=
                                        'corporate'].index)
                else:
                    df = df_i.drop(df_i[df_i.tax_treat !=
                                        'non-corporate'].index)
                # Remove data from Intellectual Property, Land, and
                # Inventories Categories
                if not include_land:
                    df.drop(df[df.asset_name == 'Land'].index,
                            inplace=True)
                if not include_inventories:
                    df.drop(df[df.asset_name ==
                               'Inventories'].index, inplace=True)
                if not include_IP:
                    df.drop(df[df.major_asset_group ==
                               'Intellectual Property'].index,
                            inplace=True)
                # define the size DataFrame, if change, use base sizes
                if list_string[i] != 'change':
                    SIZES = list(range(20, 80, 15))
                    size = pd.qcut(df['assets'].values, len(SIZES),
                                   labels=SIZES)
                    df['size'] = size
                else:
                    df['size'] = size
                # Form the two categories: Equipment and Structures
                equipment_df = df.drop(
                    df[df.major_asset_group.str.contains(
                        'Structures')].index).copy()
                equipment_df.drop(equipment_df[
                    equipment_df.major_asset_group.str.contains(
                        'Buildings')].index, inplace=True)
                # Drop overall category and overall equipment
                equipment_df.drop(
                    equipment_df[equipment_df.asset_name ==
                                 'Overall'].index, inplace=True)
                equipment_df.drop(
                    equipment_df[equipment_df.asset_name ==
                                 'Equipment'].index, inplace=True)
                structure_df = df.drop(df[
                    ~df.major_asset_group.str.contains(
                        'Structures|Buildings')].index).copy()
                # Drop value for all structures
                structure_df.drop(structure_df[
                    structure_df.asset_name == 'Structures'].index,
                                  inplace=True)

                # Output variables available in plot
                format_fields = ['metr_mix', 'metr_d', 'metr_e',
                                 'mettr_mix', 'mettr_d', 'mettr_e',
                                 'rho_mix', 'rho_d', 'rho_e', 'z_mix',
                                 'z_d', 'z_e']

                # Make short category
                make_short = {
                    'Instruments and Communications Equipment':
                    'Instruments and Communications',
                    'Office and Residential Equipment':
                    'Office and Residential',
                    'Other Equipment': 'Other',
                    'Transportation Equipment': 'Transportation',
                    'Other Industrial Equipment': 'Other Industrial',
                    'Nonresidential Buildings': 'Nonresidential Bldgs',
                    'Residential Buildings': 'Residential Bldgs',
                    'Mining and Drilling Structures': 'Mining and Drilling',
                    'Other Structures': 'Other',
                    'Computers and Software': 'Computers and Software',
                    'Industrial Machinery': 'Industrial Machinery'}

                equipment_df['short_category'] =\
                    equipment_df['minor_asset_group']
                equipment_df['short_category'].replace(make_short,
                                                       inplace=True)
                structure_df['short_category'] =\
                    structure_df['minor_asset_group']
                structure_df['short_category'].replace(make_short,
                                                       inplace=True)

                # Add the Reform and the Baseline to Equipment Asset
                for f in format_fields:
                    equipment_copy = equipment_df.copy()
                    equipment_copy['rate'] = equipment_copy[f]
                    equipment_copy['hover'] = equipment_copy.apply(
                        lambda x: "{0:.1f}%".format(x[f] * 100), axis=1)
                    simple_equipment_copy = equipment_copy.filter(
                        items=['size', 'rate', 'hover', 'short_category',
                               'asset_name'])
                    data_sources[list_string[i] + '_equipment_' + f +
                                 '_' + t] =\
                        ColumnDataSource(simple_equipment_copy)

                # Add the Reform and the Baseline to Structures Asset
                for f in format_fields:
                    structure_copy = structure_df.copy()
                    structure_copy['rate'] = structure_copy[f]
                    structure_copy['hover'] = structure_copy.apply(
                        lambda x: "{0:.1f}%".format(x[f] * 100), axis=1)
                    simple_structure_copy = structure_copy.filter(
                        items=['size', 'rate', 'hover', 'short_category',
                               'asset_name'])
                    data_sources[list_string[i] + '_structure_' + f +
                                 '_' + t] =\
                        ColumnDataSource(simple_structure_copy)

                # Create initial data sources to plot on load
                if (list_string[i] == 'base' and t == 'c'):
                    equipment_copy = equipment_df.copy()
                    equipment_copy['rate'] = equipment_copy['mettr_mix']
                    equipment_copy['hover'] = equipment_copy.apply(
                        lambda x: "{0:.1f}%".format(x['mettr_mix'] * 100),
                        axis=1)
                    simple_equipment_copy = equipment_copy.filter(
                        items=['size', 'rate', 'hover', 'short_category',
                               'asset_name'])
                    data_sources['equip_source'] =\
                        ColumnDataSource(simple_equipment_copy)

                    structure_copy = structure_df.copy()
                    structure_copy['rate'] = structure_copy['mettr_mix']
                    structure_copy['hover'] = structure_copy.apply(
                        lambda x: "{0:.1f}%".format(x['mettr_mix'] * 100),
                        axis=1)
                    simple_structure_copy = structure_copy.filter(
                        items=['size', 'rate', 'hover', 'short_category',
                               'asset_name'])
                    data_sources['struc_source'] =\
                        ColumnDataSource(simple_structure_copy)

        # Define categories for Equipments assets
        equipment_assets = [
            'Computers and Software', 'Instruments and Communications',
            'Office and Residential', 'Transportation',
            'Industrial Machinery', 'Other Industrial', 'Other']

        # Define categories for Structures assets
        structure_assets = [
            'Residential Bldgs', 'Nonresidential Bldgs',
            'Mining and Drilling', 'Other']

        # Equipment plot
        p = figure(plot_height=540, plot_width=990,
                   y_range=list(reversed(equipment_assets)),
                   tools='hover', background_fill_alpha=0,
                   title='Marginal Effective Total Tax Rates on ' +
                   'Corporate Investments in Equipment')
        p.title.align = 'center'
        p.title.text_color = '#6B6B73'

        hover = p.select(dict(type=HoverTool))
        hover.tooltips = [('Asset', ' @asset_name (@hover)')]

        p.xaxis.axis_label = "Marginal effective total tax rate"
        p.xaxis[0].formatter = NumeralTickFormatter(format="0.1%")

        p.toolbar_location = None
        p.min_border_right = 5

        p.outline_line_width = 5
        p.border_fill_alpha = 0
        p.xaxis.major_tick_line_color = "firebrick"
        p.xaxis.major_tick_line_width = 3
        p.xaxis.minor_tick_line_color = "orange"

        p.outline_line_width = 1
        p.outline_line_alpha = 1
        p.outline_line_color = "black"

        p.circle(x='rate', y='short_category', color=BLUE, size='size',
                 line_color="#333333", fill_alpha=.4,
                 source=data_sources['equip_source'], alpha=.4)

        # Define and add a legend
        legend_cds = ColumnDataSource(
            {'size': SIZES, 'label': ['<$20B', '', '', '<$1T'],
             'x': [0, .15, .35, .6]})
        p_legend = figure(height=150, width=380, x_range=(-0.075, 75),
                          title='Asset Amount', tools='')
        # p_legend.circle(y=None, x='x', size='size', source=legend_cds,
        #                 color=BLUE, fill_alpha=.4, alpha=.4,
        #                 line_color="#333333")
        # l1 = LabelSet(y=None, x='x', text='label', x_offset=-20,
        #               y_offset=-50, source=legend_cds)
        # p_legend.add_layout(l1)
        p_legend.axis.visible = False
        p_legend.grid.grid_line_color = None
        p_legend.toolbar.active_drag = None

        # data_sources['equip_plot'] = p

        # Structures plot
        p2 = figure(plot_height=540, plot_width=990,
                    y_range=list(reversed(structure_assets)),
                    tools='hover', background_fill_alpha=0,
                    title='Marginal Effective Total Tax Rates on ' +
                    'Corporate Investments in Structures')
        p2.title.align = 'center'
        p2.title.text_color = '#6B6B73'

        hover = p2.select(dict(type=HoverTool))
        hover.tooltips = [('Asset', ' @asset_name (@hover)')]
        p2.xaxis.axis_label = "Marginal effective total tax rate"
        p2.xaxis[0].formatter = NumeralTickFormatter(format="0.1%")
        p2.toolbar_location = None
        p2.min_border_right = 5
        p2.outline_line_width = 0
        p2.border_fill_alpha = 0

        p2.xaxis.major_tick_line_color = "firebrick"
        p2.xaxis.major_tick_line_width = 3
        p2.xaxis.minor_tick_line_color = "orange"

        p2.circle(x='rate', y='short_category', color=RED, size='size',
                  line_color="#333333", fill_alpha=.4,
                  source=data_sources['struc_source'], alpha=.4)

        p2.outline_line_width = 1
        p2.outline_line_alpha = 1
        p2.outline_line_color = "black"

        # Define and add a legend
        p2_legend = figure(height=150, width=380, x_range=(-0.075, .75),
                           title='Asset Amount', tools='')
        # p2_legend.circle(y=None, x='x', size='size', source=legend_cds,
        #                  color=RED, fill_alpha=.4, alpha=.4,
        #                  line_color="#333333")
        # l2 = LabelSet(y=None, x='x', text='label', x_offset=-20,
        #               y_offset=-50, source=legend_cds)
        # p2_legend.add_layout(l2)
        p2_legend.axis.visible = False
        p2_legend.grid.grid_line_color = None
        p2_legend.toolbar.active_drag = None

        # add buttons
        controls_callback = CustomJS(
            args=data_sources, code=CONTROLS_CALLBACK_SCRIPT)
        c_pt_buttons = RadioButtonGroup(
            labels=['Corporate', 'Noncorporate'], active=0)
        c_pt_buttons.js_on_change('value', controls_callback)
        controls_callback.args['c_pt_buttons'] = c_pt_buttons
        format_buttons = RadioButtonGroup(
            labels=['Baseline', 'Reform', 'Change'], active=0)
        format_buttons.js_on_change('value', controls_callback)
        controls_callback.args['format_buttons'] = format_buttons
        interest_buttons = RadioButtonGroup(
            labels=['METTR', 'METR', 'Cost of Capital',
                    'NPV of Depreciation'], active=0, width=700)
        interest_buttons.js_on_change('value', controls_callback)
        controls_callback.args['interest_buttons'] = interest_buttons
        type_buttons = RadioButtonGroup(
            labels=['Typically Financed', 'Equity Financed',
                    'Debt Financed'], active=0, width=700)
        type_buttons.js_on_change('value', controls_callback)
        controls_callback.args['type_buttons'] = type_buttons

        # Create Tabs
        tab = Panel(child=column([p, p_legend]), title='Equipment')
        tab2 = Panel(child=column([p2, p2_legend]), title='Structures')
        tabs = Tabs(tabs=[tab, tab2])
        layout = gridplot(
            children=[[tabs],
                      [c_pt_buttons, interest_buttons],
                      [format_buttons, type_buttons]]
        )
        # layout = gridplot([p, p2], ncols=2, plot_width=250, plot_height=250)
        # doc = curdoc()
        # doc.add_root(layout)

        # Create components
        # js, div = components(layout)
        # cdn_js = CDN.js_files[0]
        # cdn_css = CDN.css_files[0]

        # Set up an application
        # from bokeh.application.handlers import FunctionHandler
        # from bokeh.application import Application
        # # handler = FunctionHandler(doc)
        # # app = Application(handler)
        # app = Application(doc)

        return layout

    def asset_bubble(self, calc, output_variable='mettr_mix',
                     include_inventories=False, include_land=False,
                     include_IP=False, include_title=False, path=''):
        '''
        Create a bubble plot showing the value of the output variable
        along the x-axis, asset type groupings on the y-axis, and
        bubbles whose size represent the total assets of a specific type.

        Args:
            calc (CCC Calculator object): calc represents the reform
                while self represents the baseline
            output_variable (string): specifies which output variable to
                summarize in the table.  Default is the marginal
                effective total tax rate (`mettr_mix`).
            include_inventories (bool): whether to include inventories
                in calculations.  Defaults to `False`
            include_land (bool): whether to include land in
                calculations.  Defaults to `False`
            include_IP (bool): whether to include intellectual
                property in calculations.  Defaults to `False`
            include_title (bool): whether to include a title on the plot
            path (string): path to save file to

        Returns:
            tabs (Bokeh Tabs object): bubble plots

        '''
        # Load data as DataFrame
        df = self.calc_by_asset()
        # Keep only corporate
        df.drop(df[df.tax_treat != 'corporate'].index, inplace=True)
        # Remove data from Intellectual Property, Land, and
        # Inventories Categories
        if not include_land:
            df.drop(df[df.asset_name == 'Land'].index,
                    inplace=True)
        if not include_inventories:
            df.drop(df[df.asset_name ==
                       'Inventories'].index, inplace=True)
        if not include_IP:
            df.drop(df[df.major_asset_group ==
                       'Intellectual Property'].index,
                    inplace=True)

        # define the size DataFrame
        SIZES = list(range(20, 80, 15))
        df['size'] = pd.qcut(df['assets'].values, len(SIZES), labels=SIZES)

        # Form the two Categories: Equipment and Structures
        equipment_df = df.drop(
            df[df.minor_asset_group.str.contains(
                'Structures')].index).copy()
        equipment_df.drop(equipment_df[
            equipment_df.minor_asset_group.str.contains(
                'Buildings')].index, inplace=True)
        # Drop overall category and overall equipment
        equipment_df.drop(
            equipment_df[equipment_df.asset_name ==
                         'Overall'].index, inplace=True)
        equipment_df.drop(
            equipment_df[equipment_df.asset_name ==
                         'Equipment'].index, inplace=True)
        structure_df = df.drop(df[
            ~df.minor_asset_group.str.contains(
                'Structures|Buildings')].index).copy()

        # Make short category
        make_short = {
            'Instruments and Communications Equipment':
            'Instruments and Communications',
            'Office and Residential Equipment':
            'Office and Residential',
            'Other Equipment': 'Other',
            'Transportation Equipment': 'Transportation',
            'Other Industrial Equipment': 'Other Industrial',
            'Nonresidential Buildings': 'Nonresidential Bldgs',
            'Residential Buildings': 'Residential Bldgs',
            'Mining and Drilling Structures': 'Mining and Drilling',
            'Other Structures': 'Other',
            'Computers and Software': 'Computers and Software',
            'Industrial Machinery': 'Industrial Machinery'}

        equipment_df['short_category'] =\
            equipment_df['minor_asset_group']
        equipment_df['short_category'].replace(make_short,
                                               inplace=True)
        structure_df['short_category'] =\
            structure_df['minor_asset_group']
        structure_df['short_category'].replace(make_short,
                                               inplace=True)
        # Set up datasources
        data_sources = {}
        format_fields = [output_variable]
        # Add the Reform and the Baseline to Equipment Asset
        for f in format_fields:
            equipment_copy = equipment_df.copy()
            equipment_copy['baseline'] = equipment_copy[f]
            equipment_copy['hover'] = equipment_copy.apply(
                lambda x: "{0:.1f}%".format(x[f] * 100), axis=1)
            data_sources['equipment_' + f] = ColumnDataSource(
                equipment_copy[['baseline', 'size', 'hover', 'assets',
                                'short_category', 'asset_name']])
        # A spacer for the y-axis label
        fudge_factor = '                          '

        # Add the Reform and the Baseline to Structures Asset
        for f in format_fields:
            structure_copy = structure_df.copy()
            structure_copy['baseline'] = structure_copy[f]
            structure_copy['hover'] = structure_copy.apply(
                lambda x: "{0:.1f}%".format(x[f] * 100), axis=1)
            structure_copy['short_category'] =\
                structure_copy['short_category'].str.replace(
                    'Residential Bldgs', fudge_factor +
                    'Residential Bldgs')
            data_sources['structure_' + f] = ColumnDataSource(
                structure_copy[['baseline', 'size', 'hover', 'assets',
                                'short_category', 'asset_name']])

        # Define categories for Equipments assets
        equipment_assets = ['Computers and Software',
                            'Instruments and Communications',
                            'Office and Residential',
                            'Transportation',
                            'Industrial Machinery',
                            'Other Industrial',
                            'Other']

        # Define categories for Structures assets
        structure_assets = ['Residential Bldgs',
                            'Nonresidential Bldgs',
                            'Mining and Drilling',
                            'Other']

        # Equipment plot
        p = figure(plot_height=540,
                   plot_width=990,
                   x_range=(-.05, .51),
                   y_range=list(reversed(equipment_assets)),
                   # x_axis_location="above",
                   # toolbar_location=None,
                   tools='hover',
                   background_fill_alpha=0,
                   # change things on all axes
                   **PLOT_FORMATS)
        if include_title:
            p.add_layout(Title(
                text=('Marginal Effective Tax Rates on Corporate Investments' +
                      ' in Equipment'), **TITLE_FORMATS), 'above')

        hover = p.select(dict(type=HoverTool))
        hover.tooltips = [('Asset', ' @asset_name (@hover)')]

        # source = data_sources['equipment_' + output_variable]

        # Format axes
        p.xaxis.axis_label = "Marginal Effective Tax Rate"
        p.xaxis[0].formatter = NumeralTickFormatter(format="0.1%")
        # p.yaxis.axis_label = "Equipment"
        p.toolbar_location = None
        p.min_border_right = 5
        # p.min_border_bottom = -10
        p.outline_line_width = 5
        p.border_fill_alpha = 0
        p.xaxis.major_tick_line_color = "firebrick"
        p.xaxis.major_tick_line_width = 3
        p.xaxis.minor_tick_line_color = "orange"
        p.outline_line_width = 1
        p.outline_line_alpha = 1
        p.outline_line_color = "black"

        p.circle(x='baseline',
                 y='short_category',
                 color=BLUE,
                 size='size',
                 line_color="#333333",
                 line_alpha=.1,
                 fill_alpha=0.4,
                 source=ColumnDataSource(
                     data_sources['equipment_' + output_variable].data),
                 alpha=.4)

        # Define and add a legend
        legend_cds = ColumnDataSource(
            {'size': SIZES, 'label': ['<$20B', '', '', '<$1T'],
             'x': [0, .15, .35, .6]})
        p_legend = figure(height=150, width=380, x_range=(-0.075, 75),
                          title='Asset Amount', tools='')
        # p_legend.circle(y=None, x='x', size='size', source=legend_cds,
        #                 color=BLUE, fill_alpha=.4, alpha=.4,
        #                 line_color="#333333")
        # l1 = LabelSet(y=None, x='x', text='label', x_offset=-20,
        #               y_offset=-50, source=legend_cds)
        # p_legend.add_layout(l1)
        p_legend.axis.visible = False
        p_legend.grid.grid_line_color = None
        p_legend.toolbar.active_drag = None

        # Style the tools
        # p.add_tools(WheelZoomTool(), ResetTool(), SaveTool())
        # p.toolbar_location = "right"
        # p.toolbar.logo = None

        # Structures plot
        p2 = figure(plot_height=540,
                    plot_width=990,
                    x_range=(-.05, .51),
                    y_range=list(reversed(structure_assets)),
                    # toolbar_location=None,
                    tools='hover',
                    background_fill_alpha=0,
                    **PLOT_FORMATS)
        p2.add_layout(Title(
            text=('Marginal Effective Tax Rates on Corporate ' +
                  'Investments in Structures'), **TITLE_FORMATS),
                  'above')

        hover = p2.select(dict(type=HoverTool))
        hover.tooltips = [('Asset', ' @asset_name (@hover)')]
        # Format axes
        p2.xaxis.axis_label = "Marginal Effective Tax Rate"
        p2.xaxis[0].formatter = NumeralTickFormatter(format="0.1%")
        # p2.yaxis.axis_label = "Structures"
        p2.toolbar_location = None
        p2.min_border_right = 5
        # p2.min_border_top = -13
        p2.outline_line_width = 0
        p2.border_fill_alpha = 0
        p2.xaxis.major_tick_line_color = "firebrick"
        p2.xaxis.major_tick_line_width = 3
        p2.xaxis.minor_tick_line_color = "orange"

        p2.circle(x='baseline',
                  y='short_category',
                  color=RED,
                  size='size',
                  line_color="#333333",
                  # line_alpha=.1,
                  fill_alpha=0.4,
                  source=ColumnDataSource(
                      data_sources['structure_' + output_variable].data),
                  alpha=.4)

        p2.outline_line_width = 1
        p2.outline_line_alpha = 1
        p2.outline_line_color = "black"

        # Define and add a legend
        p2_legend = figure(height=150, width=380, x_range=(-0.075, .75),
                           title='Asset Amount', tools='')
        # p2_legend.circle(y=None, x='x', size='size', source=legend_cds,
        #                  color=RED, fill_alpha=.4, alpha=.4,
        #                  line_color="#333333")
        # l2 = LabelSet(y=None, x='x', text='label', x_offset=-20,
        #               y_offset=-50, source=legend_cds)
        # p2_legend.add_layout(l2)
        p2_legend.axis.visible = False
        p2_legend.grid.grid_line_color = None
        p2_legend.toolbar.active_drag = None

        # Create Tabs
        tab = Panel(child=column([p, p_legend]), title='Equipment')
        tab2 = Panel(child=column([p2, p2_legend]), title='Structures')
        tabs = Tabs(tabs=[tab, tab2])

        return tabs

    def store_assets(self):
        '''
        Make internal copy of embedded Assets object that can then be
        restored after interim calculations that make temporary changes
        to the embedded Assets object.

        '''
        assert self.__stored_assets is None
        self.__stored_assets = copy.deepcopy(self.__assets)

    def restore_assets(self):
        '''
        Set the embedded Assets object to the stored Assets object
        that was saved in the last call to the store_assets() method.

        '''
        assert isinstance(self.__stored_assets, Assets)
        self.__assets = copy.deepcopy(self.__stored_assets)
        del self.__stored_assets
        self.__stored_assets = None

    def p_param(self, param_name, param_value=None):
        '''
        If param_value is None, return named parameter in
         embedded Specification object.
        If param_value is not None, set named parameter in
         embedded Specification object to specified param_value and
         return None (which can be ignored).

         Args:
             param_name (string): parameter name
             param_value (python object): value to set parameter to

         Returns:
             None
        '''
        if param_value is None:
            return getattr(self.__p, param_name)
        setattr(self.__p, param_name, param_value)
        return None

    @property
    def current_year(self):
        '''
        Calculator class current calendar year property.

        '''
        return self.__p.year

    @property
    def data_year(self):
        '''
        Calculator class initial (i.e., first) assets data year property.

        '''
        return self.__assets.data_year

    def __f(self, x):
        '''
        Private method.  A function to compute sums and weighted averages
        from a groubpy object.

        Args:
            x (Pandas DataFrame): data for the particular grouping

        Returns:
            d (Pandas Series): computed variables for the group

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
        d['Y'] = wavg(x, 'Y', 'assets')

        return pd.Series(d, index=['assets', 'delta', 'rho_mix', 'rho_d',
                                   'rho_e', 'z_mix', 'z_d', 'z_e', 'Y'])
