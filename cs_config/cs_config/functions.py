import ccc
from ccc.parameters import Specification
from ccc.data import Assets
from ccc.calculator import Calculator
from ccc.utils import TC_LAST_YEAR
from bokeh.embed import components
import os
import paramtools
from .helpers import retrieve_puf

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
            "value": 2019,
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
    meta_params = MetaParams()
    meta_params.adjust(meta_params_dict)
    ccc_params = Specification(year=meta_params.year)
    return {
         "meta_parameters": meta_params.dump(),
         "model_parameters": {
             "ccc": ccc_params.dump()
         }
     }


def validate_inputs(meta_param_dict, adjustment, errors_warnings):
    '''
    Validates user inputs for parameters
    '''
    # ccc doesn't look at meta_param_dict for validating inputs.
    params = Specification()
    params.adjust(adjustment["ccc"], raise_errors=False)

    return {"errors_warnings": {"ccc": {"errors": params.errors}}}


def get_version():
    return ccc.__version__


def run_model(meta_param_dict, adjustment):
    '''
    Initializes classes from CCC that compute the model under
    different policies.  Then calls function get output objects.
    '''
    meta_params = MetaParams()
    meta_params.adjust(meta_param_dict)
    if meta_params.data_source == "PUF":
        data = retrieve_puf(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    else:
        data = "cps"
    params = Specification(year=meta_params.year, call_tc=False,
                           data=data)
    assets = Assets()
    calc1 = Calculator(params, assets)
    params2 = Specification(year=meta_params.year, call_tc=False,
                            data=data)
    params2.update_specification(adjustment["ccc"])
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
    plt = calc1.grouped_bar(calc2, output_variable=out_var)
    js, div = components(plt)
    comp_dict = {
        "model_version": ccc.__version__,
        "renderable": [
            {
              "media_type": "bokeh",
              "title": plt.title._property_values['text'],
              "data": {
                        "javascript": js,
                        "html": div
                    }
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
