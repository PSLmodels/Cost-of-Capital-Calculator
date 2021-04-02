import ccc
from ccc.parameters import Specification, DepreciationParams
from ccc.data import Assets
from ccc.calculator import Calculator
from ccc.utils import TC_LAST_YEAR, DEFAULT_START_YEAR
from bokeh.embed import json_item
import os
import paramtools
from taxcalc import Policy
from collections import OrderedDict
from .helpers import retrieve_puf
import cs2tc

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")


class MetaParams(paramtools.Parameters):
    '''
    Meta parameters class for COMP.  These parameters will be in a drop
    down menu on COMP.
    '''
    array_first = True
    defaults = {
        "year": {
            "title": "Start year",
            "description": "Year for parameters.",
            "type": "int",
            "value": DEFAULT_START_YEAR,
            "validators": {
              "when": {
                  "param": "data_source",
                  "is": "CPS",
                  "then": {"range": {"min": 2014, "max": TC_LAST_YEAR}},
                  "otherwise": {"range": {"min": 2013, "max": TC_LAST_YEAR}}
                  }
              },
        },
        "data_source": {
            "title": "Data source",
            "description": "Data source for Tax-Calculator to use",
            "type": "str",
            "value": "CPS",
            "validators": {"choice": {"choices": ["PUF", "CPS"]}}
        }
    }

    def dump(self, *args, **kwargs):
        """
        This method extends the default ParamTools dump method by
        swapping the when validator for a choice validator. This is
        required because C/S does not yet implement the when validator.
        """
        data = super().dump(*args, **kwargs)
        if self.data_source == "CPS":
            data["year"]["validators"] = {
                "choice": {
                    "choices": list(range(2014, TC_LAST_YEAR))
                }
            }
        else:
            data["year"]["validators"] = {
                "choice": {
                    "choices": list(range(2013, TC_LAST_YEAR))
                }
            }
        return data


def get_inputs(meta_params_dict):
    '''
    Function to get user input parameters from COMP
    '''
    # Get meta-params from web app
    meta_params = MetaParams()
    meta_params.adjust(meta_params_dict)
    # Set default CCC params
    ccc_params = Specification(year=meta_params.year)
    filtered_ccc_params = OrderedDict()
    # filter out parameters that can be changed with Tax-Calc params or
    # that users unlikely to use (so reduce clutter on screen)
    filter_list = [
        'tau_div', 'tau_nc', 'tau_int', 'tau_scg', 'tau_lcg', 'tau_td',
        'tau_h', 'alpha_c_e_ft', 'alpha_c_e_td', 'alpha_c_e_nt',
        'alpha_c_d_ft', 'alpha_c_d_td', 'alpha_c_d_nt', 'alpha_nc_d_ft',
        'alpha_nc_d_td', 'alpha_nc_d_nt', 'alpha_h_d_ft', 'alpha_h_d_td',
        'alpha_h_d_nt', 'Y_td', 'Y_scg', 'Y_lcg', 'Y_xcg', 'Y_v', 'gamma',
        'phi']
    for k, v in ccc_params.dump().items():
        if k not in filter_list:
            filtered_ccc_params[k] = v

    # Set default TC params
    iit_params = Policy()
    iit_params.set_state(year=meta_params.year.tolist())

    filtered_iit_params = cs2tc.convert_policy_defaults(
      meta_params, iit_params)

    default_params = {
        "Business Tax Parameters": filtered_ccc_params,
        "Individual and Payroll Tax Parameters": filtered_iit_params
    }

    return {
         "meta_parameters": meta_params.dump(),
         "model_parameters": default_params
     }


def validate_inputs(meta_param_dict, adjustment, errors_warnings):
    '''
    Validates user inputs for parameters
    '''
    # Validate meta parameter inputs
    meta_params = MetaParameters()
    meta_params.adjust(meta_params_dict, raise_errors=False)
    errors_warnings["policy"]["errors"].update(meta_params.errors)
    # Validate CCC parameter inputs
    params = Specification()
    params.adjust(adjustment["Business Tax Parameters"],
                  raise_errors=False)
    errors_warnings["Business Tax Parameters"]["errors"].update(
        params.errors)
    # Validate TC parameter inputs
    iit_adj = cs2tc.convert_policy_adjustment(
        adjustment["Individual and Payroll Tax Parameters"])

    iit_params = Policy()
    iit_params.adjust(iit_adj, raise_errors=False, ignore_warnings=True)
    errors_warnings["Individual and Payroll Tax Parameters"][
        "errors"].update(iit_params.errors)

    return {"errors_warnings": errors_warnings}


def get_version():
    return ccc.__version__


def run_model(meta_param_dict, adjustment):
    '''
    Initializes classes from CCC that compute the model under
    different policies.  Then calls function get output objects.
    '''
    # update MetaParams
    meta_params = MetaParams()
    meta_params.adjust(meta_param_dict)
    # Get data chosen by user
    if meta_params.data_source == "PUF":
        data = retrieve_puf(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    else:
        data = "cps"
    # Get TC params adjustments
    iit_mods = cs2tc.convert_policy_adjustment(adjustment[
        "Individual and Payroll Tax Parameters"])
    filtered_ccc_params = {}
    # filter out CCC params that will not change between baeline and
    # reform runs (These are the Household Savings Behavior and
    # Economic Assumptions)
    constant_param_list = [
        'omega_scg', 'omega_lcg', 'omega_xcg', 'alpha_c_e_ft',
        'alpha_c_e_td', 'alpha_c_e_nt', 'alpha_c_d_ft', 'alpha_c_d_td',
        'alpha_c_d_nt', 'alpha_nc_d_ft', 'alpha_nc_d_td',
        'alpha_nc_d_nt', 'alpha_h_d_ft', 'alpha_h_d_td', 'alpha_h_d_nt',
        'Y_td', 'Y_scg', 'Y_lcg', 'gamma', 'E_c', 'inflation_rate',
        'nominal_interest_rate']
    filtered_ccc_params = OrderedDict()
    for k, v in adjustment['Business Tax Parameters'].items():
        if k in constant_param_list:
            filtered_ccc_params[k] = v
    # Baseline CCC calculator
    params = Specification(year=meta_params.year, call_tc=False,
                           iit_reform={}, data=data)
    params.update_specification(filtered_ccc_params)
    assets = Assets()
    dp = DepreciationParams()
    calc1 = Calculator(params, dp, assets)
    # Reform CCC calculator - includes TC adjustments
    params2 = Specification(year=meta_params.year, call_tc=True,
                            iit_reform=iit_mods, data=data)
    params2.update_specification(adjustment["Business Tax Parameters"])
    calc2 = Calculator(params2, dp, assets)
    comp_dict = comp_output(calc1, calc2)

    return comp_dict


def comp_output(calc1, calc2, out_var='mettr'):
    '''
    Function to create output for the COMP platform
    '''
    baseln_assets_df = calc1.calc_by_asset()
    reform_assets_df = calc2.calc_by_asset()
    baseln_industry_df = calc1.calc_by_industry()
    reform_industry_df = calc2.calc_by_industry()
    html_table = calc1.summary_table(calc2, output_variable=out_var,
                                     output_type='html')
    plt1 = calc1.grouped_bar(calc2, output_variable=out_var,
                             include_title=True)
    plot_data1 = json_item(plt1)
    plt2 = calc1.grouped_bar(calc2, output_variable=out_var,
                             group_by_asset=False,
                             include_title=True)
    plot_data2 = json_item(plt2)
    plt3 = calc1.range_plot(calc2, output_variable='mettr',
                            include_title=True)
    plot_data3 = json_item(plt3)
    comp_dict = {
        "renderable": [
            {
              "media_type": "table",
              "title":  out_var.upper() + " Summary Table",
              "data": html_table
            },
            {
              "media_type": "bokeh",
              "title": plt1.title._property_values['text'],
              "data": plot_data1
            },
            {
              "media_type": "bokeh",
              "title": plt2.title._property_values['text'],
              "data": plot_data2
            },
            {
              "media_type": "bokeh",
              "title": "Marginal Effective Total Tax Rates by Method of Financing",
              "data": plot_data3
            }
          ],
        "downloadable": [
            {
              "media_type": "CSV",
              "title": "Baseline Results by Asset",
              "data": baseln_assets_df.to_csv(float_format='%.5f')
            },
            {
              "media_type": "CSV",
              "title": "Reform Results by Asset",
              "data": reform_assets_df.to_csv(float_format='%.5f')
            },
            {
              "media_type": "CSV",
              "title": "Baseline Results by Industry",
              "data": baseln_industry_df.to_csv(float_format='%.5f')
            },
            {
              "media_type": "CSV",
              "title": "Reform Results by Industry",
              "data": reform_industry_df.to_csv(float_format='%.5f')
            }
          ]
        }

    return comp_dict
