import os
import json

def convert(params):
    for param, item in params.copy().items():
        values = []

        if not isinstance(item["value"], list):
            values = item["value"]
        else:
            for year in range(len(item["value"])):
                values.append({"year": item["start_year"] + year,
                               "value": item["value"][year]})

        params[param]['value'] = values
        params[param]['title'] = params[param]["long_name"]
        if params[param]["boolean_value"]:
            params[param]["type"] = "bool"
        elif params[param]["integer_value"]:
            params[param]["type"] = "int"
        elif params[param]["string_value"]:
            params[param]["type"] = "str"
        else:
            params[param]["type"] = "float"
        if params[param]["range"].get("min", None) is not None:
            params[param]["validators"] = {"range": params[param]["range"]}
        elif params[param]["range"].get("possible_values", None) is not None:
            params[param]["validators"] = {"choice": {"choices": params[param]["range"]["possible_values"]}}
        else:
            raise ValueError(f"Error: {param}: range")

        to_pop = ["long_name", "boolean_value", "integer_value", "string_value", "row_var",
                  "row_label", "col_var", "col_label", "range", "compatible_data",
                  "cpi_inflated", "cpi_inflatable", "out_of_range_minmsg", "out_of_range_maxmsg",
                  "out_of_range_action", "irs_ref"]
        for var in to_pop:
            params[param].pop(var, None)


    return params


if __name__ == "__main__":
    current_path = os.path.abspath(os.path.dirname(__file__))
    params_path = os.path.join(
        current_path, "ccc/default_parameters.json"
    )

    with open(params_path, 'r') as f:
        params = json.loads(f.read())

    with open("default_parameters.json", 'w') as f:
        f.write(json.dumps(convert(params), indent=4))

