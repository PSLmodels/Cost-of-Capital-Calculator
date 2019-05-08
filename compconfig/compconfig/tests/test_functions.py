from compdevkit import FunctionsTest
import sys
import os.path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__),
                                 os.path.pardir)))
import functions


def test_get_parameters():
    ta = FunctionsTest(
        model_parameters=functions.get_inputs,
        validate_inputs=functions.validate_inputs,
        run_model=functions.run_model,
        ok_adjustment={"ccc": {"CIT_rate": 0.21}},
        bad_adjustment={"ccc": {"CIT_rate": -0.1}}
    )
    ta.test()
