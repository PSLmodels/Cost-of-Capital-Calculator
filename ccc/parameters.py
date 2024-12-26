import os
import pandas as pd
import itertools
import paramtools
import marshmallow as ma

# import ccc
from ccc.get_taxcalc_rates import get_rates
from ccc.utils import DEFAULT_START_YEAR, RECORDS_START_YEAR
import ccc.paramfunctions as pf

CURRENT_PATH = os.path.abspath(os.path.dirname(__file__))


class Specification(paramtools.Parameters):
    """
    Specification class, contains model parameters.
    Inherits ParamTools Parameters abstract base class.
    """

    defaults = os.path.join(CURRENT_PATH, "default_parameters.json")
    label_to_extend = "year"
    array_first = True

    def __init__(
        self,
        test=False,
        year=DEFAULT_START_YEAR,
        call_tc=False,
        baseline_policy=None,
        iit_reform=None,
        data="cps",
        gfactors=None,
        weights=None,
        records_start_year=RECORDS_START_YEAR,
    ):
        super().__init__()
        self.set_state(year=year)
        self.test = test
        self.year = year
        self.baseline_policy = baseline_policy
        self.iit_reform = iit_reform
        self.data = data
        # initialize parameter values from JSON
        self.ccc_initialize(
            call_tc=call_tc,
            gfactors=gfactors,
            weights=weights,
            records_start_year=records_start_year,
        )

    def ccc_initialize(
        self,
        call_tc=False,
        gfactors=None,
        weights=None,
        records_start_year=RECORDS_START_YEAR,
    ):
        """
        ParametersBase reads JSON file and sets attributes to self
        Next call self.compute_default_params for further initialization

        Args:
            test (bool): whether to run in test mode
            year (int): start year for simulation
            call_tc (bool): whether to use Tax-Calculator to estimate
                marginal tax rates
            baseline_policy (dict): individual income tax baseline
                policy parameters, reform dict makes changes relative
                to this baseline
            iit_reform (dict): individual income tax reform parameters
            data (str): data source for Tax-Calculator
            gfactors (dict): growth factors for Tax-Calculator
            weights (str): weights for Tax-Calculator

        Returns:
            None

        """
        if call_tc:
            # Find individual income tax rates from Tax-Calculator
            indiv_rates = get_rates(
                self.year,
                self.baseline_policy,
                self.iit_reform,
                self.data,
                gfactors,
                weights,
                records_start_year,
            )
            self.tau_pt = indiv_rates["tau_pt"]
            self.tau_div = indiv_rates["tau_div"]
            self.tau_int = indiv_rates["tau_int"]
            self.tau_scg = indiv_rates["tau_scg"]
            self.tau_lcg = indiv_rates["tau_lcg"]
            self.tau_td = indiv_rates["tau_td"]
            self.tau_h = indiv_rates["tau_h"]
        # does cheap calculations to find parameter values
        self.compute_default_params()

    def compute_default_params(self):
        """
        Does cheap calculations to return parameter values

        """
        self.financing_list = ["mix", "d", "e"]
        self.entity_list = ["c", "pt"]

        # If new_view, then don't assume don't pay out any dividends
        # This because under new view, equity investments are financed
        # with retained earnings
        if self.new_view:
            self.m = 1

        # Get after-tax return to savers
        self.s, E_pt = pf.calc_s(self)

        # Set rate of 1st layer of taxation on investment income
        self.u = {"c": self.CIT_rate}
        self.u_d = {"c": self.CIT_rate_ded}
        if not self.pt_entity_tax_ind.all():
            self.u["pt"] = self.tau_pt
        else:
            self.u["pt"] = self.pt_entity_tax_rate
        self.u_d["pt"] = self.pt_scale_tax_rate_ded * self.u["pt"]
        E_dict = {"c": self.E_c, "pt": E_pt}

        # Allowance for Corporate Equity
        ace_dict = {"c": self.ace_c, "pt": self.ace_pt}

        # Handle R&E credits which vary by industry and asset type
        self.re_credit = {
            "By asset": self.re_credit_asset,
            "By industry": self.re_credit_industry,
        }

        # Limitation on interest deduction
        int_haircut_dict = {
            "c": self.interest_deduct_haircut_c,
            "pt": self.interest_deduct_haircut_pt,
        }
        # Debt financing ratios
        f_dict = {
            "c": {"mix": self.f_c, "d": 1.0, "e": 0.0},
            "pt": {"mix": self.f_pt, "d": 1.0, "e": 0.0},
        }

        # Compute firm discount factors
        self.r = {}
        for t in self.entity_list:
            self.r[t] = {}
            for f in self.financing_list:
                self.r[t][f] = pf.calc_r(
                    self.u[t],
                    self.nominal_interest_rate,
                    self.inflation_rate,
                    self.ace_int_rate,
                    f_dict[t][f],
                    int_haircut_dict[t],
                    E_dict[t],
                    ace_dict[t],
                )

        # Compute firm after-tax rates of return
        r_prime = {}
        for t in self.entity_list:
            r_prime[t] = {}
            for f in self.financing_list:
                r_prime[t][f] = pf.calc_r_prime(
                    self.nominal_interest_rate,
                    self.inflation_rate,
                    f_dict[t][f],
                    E_dict[t],
                )

        # if no entity level taxes on pass-throughs, ensure mettr and metr
        # on non-corp entities the same
        if not self.pt_entity_tax_ind:
            for f in self.financing_list:
                r_prime["pt"][f] = self.s["pt"][f] + self.inflation_rate
        # if entity level tax, assume distribute earnings at same rate corps
        # distribute dividends and these are taxed at dividends tax rate
        # (which seems likely).  Also implicitly assumed that if entity
        # level tax, then only additional taxes on pass-through income are
        # capital gains and dividend taxes
        else:
            # keep debt and equity financing ratio the same even though now
            # entity level tax that might now favor debt
            self.s["pt"]["mix"] = (
                self.f_pt * self.s["pt"]["d"]
                + (1 - self.f_pt) * self.s["c"]["e"]
            )
        self.r_prime = r_prime

        # Map string tax methods into multiple of declining balance
        self.tax_methods = {
            "DB 200%": 2.0,
            "DB 150%": 1.5,
            "SL": 1.0,
            "Economic": 1.0,
            "Expensing": 1.0,
        }

        # Create dictionaries with depreciation system and rate of bonus
        # depreciation by asset class
        class_list = [3, 5, 7, 10, 15, 20, 25, 27.5, 39]
        class_list_str = [
            (str(i) if i != 27.5 else "27_5") for i in class_list
        ]
        self.bonus_deprec = {}
        for i, cl in enumerate(class_list_str):
            self.bonus_deprec[class_list[i]] = getattr(
                self, "BonusDeprec_{}yr".format(cl)
            )[0]
        # to handle land and inventories
        # this is fixed later, but should work on this
        self.bonus_deprec[100] = 0.0

    def default_parameters(self):
        """
        Return Specification object same as self except it contains
        default values of all the parameters.

        Returns:
            dps (CCC Specification object): Specification instance with
                the default parameter values

        """
        dps = Specification()
        return dps

    def update_specification(self, revision, raise_errors=True):
        """
        Updates parameter specification with values in revision dictionary.

        Args:
            revision (dict): dictionary or JSON string with one or more
                `PARAM: YEAR-VALUE-DICTIONARY` pairs

            raise_errors (boolean):
                if True (the default), raises ValueError when
                   `parameter_errors` exists;
                if False, does not raise ValueError when
                   `parameter_errors` exists and leaves error handling
                   to caller of the update_specification method.

        Returns:
            None

        Raises:
            ValueError: if `raise_errors` is True AND
                `_validate_parameter_names_types` generates errors OR
                `_validate_parameter_values` generates errors.

        Notes:
            Given a revision dictionary, typical usage of the
                Specification class is as follows::
                    >>> spec = Specification()
                    >>> spec.update_specification(revision)
            An example of a multi-parameter revision dictionary is as follows::
                >>> revison = {
                    'CIT_rate': {2021: [0.25]},
                    'BonusDeprec_3yr': {2021: 0.60},
                    }

        """
        if not (isinstance(revision, dict) or isinstance(revision, str)):
            raise ValueError("ERROR: revision is not a dictionary or string")
        self.adjust(revision, raise_errors=raise_errors)
        self.compute_default_params()

    @staticmethod
    def _read_json_revision(obj):
        """
        Return a revision dictionary, which is suitable for use with the
        update_specification method, that is derived from the specified
        JSON object, which can be None or a string containing
        a local filename,
        a URL beginning with 'http' pointing to a JSON file hosted
        online, or a valid JSON text.

        """
        return paramtools.Parameters.read_params(obj, "revision")


# end of Specification class


class DepreciationRules(ma.Schema):
    # set some field validation ranges that can't set in JSON
    system = ma.fields.String(
        validate=ma.validate.OneOf(
            choices=[
                "GDS",
                "ADS",
                "Economic",
                "Expensing",
                "Income Forecast",
            ]
        )
    )
    life = ma.fields.Float(validate=ma.validate.Range(min=0, max=100))
    method = ma.fields.String(
        validate=ma.validate.OneOf(
            choices=[
                "SL",
                "Expensing",
                "DB 150%",
                "DB 200%",
                "Economic",
                "Income Forecast",
            ]
        )
    )


# Register custom type defined above
paramtools.register_custom_type(
    "depreciation_rules", ma.fields.Nested(DepreciationRules())
)


class DepreciationParams(paramtools.Parameters):
    """
    Depreciation parameters class, contains model depreciation
    parameters.
    Inherits ParamTools Parameters abstract base class.
    """

    defaults = os.path.join(CURRENT_PATH, "tax_depreciation_rules.json")

    def to_df(self):
        """
        Return a DataFrame containing the depreciation parameters.
        """
        nested_dict = self.to_dict()
        # Prepare lists to collect data
        data = []
        # Iterate through the nested dictionary
        for key, value_list in nested_dict.items():
            # Extract the OrderedDict(s) in the list
            for item in value_list:
                # Prepare a dictionary to hold the row data
                row_data = {}
                # Extract 'value' dictionary contents
                row_data.update(item["value"])
                # Add the year
                row_data["year"] = item["year"]
                # Add the asset code
                row_data["BEA_code"] = key
                # Append the row data and index key
                data.append(row_data)

        # Create DataFrame with the extracted data and specified index
        df = pd.DataFrame(data)

        return df

    def expanded_df(self):
        df = self.to_df()
        unique_bea_codes = df["BEA_code"].unique()
        years = self.label_grid["year"]
        # Create all combinations of years and BEA codes
        combinations = list(itertools.product(years, unique_bea_codes))
        # Create a new DataFrame with these combinations
        expanded_df = pd.DataFrame(combinations, columns=["year", "BEA_code"])
        # Merge with the original DataFrame to preserve known values
        expanded_df = expanded_df.merge(
            df, on=["year", "BEA_code"], how="left"
        )
        # Sort the DataFrame to ensure we can forward fill from the last known year
        expanded_df = expanded_df.sort_values(["BEA_code", "year"])
        # Group by BEA_code and forward fill missing values
        expanded_df = (
            expanded_df[["life", "method", "system", "year", "BEA_code"]]
            .groupby("BEA_code")
            .apply(lambda group: group.ffill(), include_groups=False)
            .reset_index()
        )
        column_order = ["life", "method", "system", "year", "BEA_code"]
        expanded_df = expanded_df[column_order]

        return expanded_df

    def adjust_from_csv(self, fname):
        """
        Read from a CSV file and adjust the parameter values.

        CSV must have columns for year, BEA_code, year, life, method, and system.

        Args:
            fname (str): name of the CSV file

        Returns:
            None

        """
        df = pd.read_csv(fname)
        # set the index to BEA_code
        df.set_index("BEA_code", inplace=True)
        # convert to dictionary
        df_dict = df.to_dict(orient="index")
        # put life, method, and system in a value dictionary
        for k, v in df_dict.items():
            df_dict[k] = [
                {
                    "year": int(v["year"]),
                    "value": {
                        "life": v["life"],
                        "method": v["method"],
                        "system": v["system"],
                    },
                }
            ]
        self.adjust(df_dict)


def revision_warnings_errors(spec_revision):
    """
    Return warnings and errors for the specified Cost-of-Capital-Calculator
    Specificaton revision in parameter values.

    Args:
        spec_revision (dict): dictionary suitable for use with the
            `Specification.update_specification method`.

    Returns:
        rtn_dict (dict): dicionary containing any warning or error messages

    """
    rtn_dict = {"warnings": "", "errors": ""}
    spec = Specification()
    try:
        spec.update_specification(spec_revision, raise_errors=False)
        if spec._errors:
            rtn_dict["errors"] = spec._errors
    except ValueError as valerr_msg:
        rtn_dict["errors"] = valerr_msg.__str__()
    return rtn_dict
