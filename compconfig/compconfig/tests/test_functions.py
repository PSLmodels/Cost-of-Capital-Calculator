from compdevkit import FunctionsTest

from compconfig import functions


def test_get_parameters():
    ta = FunctionsTest(
        get_inputs=functions.get_inputs,
        validate_inputs=functions.validate_inputs,
        run_model=functions.run_model,
        ok_adjustment={"ccc": {"CIT_rate": 0.21}},
        bad_adjustment={"ccc": {"CIT_rate": -0.1}}
    )
    ta.test()
