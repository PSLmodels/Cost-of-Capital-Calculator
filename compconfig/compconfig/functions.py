from ccc.parameters import Specifications
from ccc.data import Assets
from ccc.calculator import Calculator
from ccc.utils import TC_LAST_YEAR
from bokeh.embed import components
import os
import paramtools

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
        }
    }


def get_inputs(meta_params_dict):
    '''
    Function to get user input parameters from COMP
    '''
    meta_params = MetaParams()
    meta_params.adjust(meta_params_dict)
    params = Specifications()
    params.specification(serializable=True)
    spec = params.specification(
        meta_data=True,
        year=meta_params.year
    )
    return meta_params.specification(meta_data=True), {"ccc": spec}


def validate_inputs(meta_param_dict, adjustment, errors_warnings):
    '''
    Validates user inputs for parameters
    '''
    # ccc doesn't look at meta_param_dict for validating inputs.
    params = Specifications()
    params.specification(serializable=True)
    params.adjust(adjustment["ccc"], raise_errors=False)
    errors_warnings["ccc"]["errors"].update(params.errors)
    return errors_warnings


def run_model(meta_param_dict, adjustment):
    '''
    Initiliazes classes from CCC that compute the model under
    different policies.  Then calls function get output objects.
    '''
    meta_params = MetaParams()
    meta_params.adjust(meta_param_dict)
    params = Specifications(year=meta_params.year)
    params.specification(serializable=True)
    params.adjust(adjustment["ccc"])
    assets = Assets()
    calc1 = Calculator(params, assets)
    params2 = Specifications(year=meta_params.year)
    calc2 = Calculator(params2, assets)
    comp_dict = comp_output(calc1, calc2)

    return comp_dict


def comp_output(calc1, calc2, out_var='mettr'):
    '''
    Function to create output for the COMP platform
    '''
    out_table = calc1.summary_table(calc2, output_variable=out_var,
                                    output_type='csv')
    df = calc1.summary_table(calc2, output_variable=out_var)
    plt = calc1.grouped_bar(calc2, output_variable=out_var)
    js, div = components(plt)
    comp_dict = {
        "renderable": [
            {
              "media_type": "bokeh",
              "title": str(plt.title),
              "data": {
                        "javascript": js,
                        "html": div
                    }
            },
            {
              "media_type": "table",
              "title":  out_var + "Summary Table",
              "data": df.to_html()
            },
          ],
        "downloadable": [
            {
              "media_type": "CSV",
              "title": out_var + "Summary Table",
              "data": out_table
            }
          ]
        }

    return comp_dict
