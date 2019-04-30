from compdevkit import TestFunctions
import sys
sys.path.append("..")
import ccc_comp


def test_get_parameters():
    ta = TestFunctions(
        model_parameters=ccc_comp.get_inputs,
        validate_inputs=ccc_comp.validate_inputs,
        run_model=ccc_comp.run_model,
        ok_adjustment={"ccc": {"CIT_rate": 0.21}},
        bad_adjustment={"ccc": {"CIT_rate": -0.1}}
    )
    ta.test()


test_get_parameters()
