import ccc
from ccc.parameters import Specification
from ccc.data import Assets
from ccc.calculator import Calculator
from ccc.utils import TC_LAST_YEAR, DEFAULT_START_YEAR
from bokeh.embed import json_item
import os
import json
import inspect
import paramtools
from taxcalc import Policy
from collections import OrderedDict
from .helpers import retrieve_puf, convert_adj, convert_defaults

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")

# Get Tax-Calculator default parameters
TCPATH = inspect.getfile(Policy)
TCDIR = os.path.dirname(TCPATH)
with open(os.path.join(TCDIR, "policy_current_law.json"), "r") as f:
    pcl = json.loads(f.read())
RES = convert_defaults(pcl)


class TCParams(paramtools.Parameters):
    defaults = RES


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
            "validators": {"range": {"min": 2015, "max": TC_LAST_YEAR}}
        },
        "data_source": {
            "title": "Data source",
            "description": "Data source for Tax-Calculator to use",
            "type": "str",
            "value": "CPS",
            "validators": {"choice": {"choices": ["PUF", "CPS"]}}
        }
    }


def get_inputs(meta_params_dict):
    '''
    Function to get user input parameters from COMP
    '''
    # Get meta-params from web app
    meta_params = MetaParams()
    meta_params.adjust(meta_params_dict)
    # Set default CCC params
    ccc_params = Specification(year=meta_params.year)
    # Set default TC params
    iit_params = TCParams()
    iit_params.set_state(year=meta_params.year.tolist())
    filtered_iit_params = OrderedDict()
    for k, v in iit_params.dump().items():
        if k == "schema" or v.get("section_1", False):
            filtered_iit_params[k] = v

    default_params = {
        "Business Tax Parameters": ccc_params.dump(),
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
    # ccc doesn't look at meta_param_dict for validating inputs.
    params = Specification()
    params.adjust(adjustment["Business Tax Parameters"],
                  raise_errors=False)
    errors_warnings["Business Tax Parameters"]["errors"].update(
        params.errors)
    # Validate TC parameter inputs
    pol_params = {}
    # drop checkbox parameters.
    for param, data in list(adjustment[
        "Individual and Payroll Tax Parameters"].items()):
        if not param.endswith("checkbox"):
            pol_params[param] = data
    iit_params = TCParams()
    iit_params.adjust(pol_params, raise_errors=False)
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
    iit_mods = convert_adj(adjustment[
        "Individual and Payroll Tax Parameters"],
                           meta_params.year.tolist())
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
    calc1 = Calculator(params, assets)
    # Reform CCC calculator - includes TC adjustments
    params2 = Specification(year=meta_params.year, call_tc=True,
                            iit_reform=iit_mods, data=data)
    params2.update_specification(adjustment["Business Tax Parameters"])
    calc2 = Calculator(params2, assets)
    comp_dict = comp_output(calc1, calc2)

    return comp_dict


def comp_output(calc1, calc2, out_var='mettr'):
    '''
    Function to create output for the COMP platform
    '''
    out_table = calc1.summary_table(calc2, output_variable=out_var,
                                    output_type='csv')
    html_table = calc1.summary_table(calc2, output_variable=out_var,
                                     output_type='html')
    plt = calc1.grouped_bar(calc2, output_variable=out_var,
                            include_title=True)
    plot_data = json_item(plt)
    comp_dict = {
        "renderable": [
            {
              "media_type": "bokeh",
              "title": plt.title._property_values['text'],
              "data": plot_data
            },
            {
              "media_type": "table",
              "title":  out_var.upper() + " Summary Table",
              "data": html_table
            },
          ],
        "downloadable": [
            {
              "media_type": "CSV",
              "title": out_var.upper() + " Summary Table",
              "data": out_table.to_csv()
            }
          ]
        }

    return comp_dict
