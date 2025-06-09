import pandas as pd

from hamilton.function_modifiers import does, extract_columns, extract_fields, tag


def _sum_multiply(param0: int, param1: int, param2: int) -> pd.DataFrame:
    return pd.DataFrame([{"param0a": param0, "param1b": param1, "param2c": param2}])


def _sum(param0: int, param1: int, param2: int) -> dict:
    return {"total": param0 + param1 + param2}


@extract_columns("param1b")
@does(_sum_multiply)
def to_modify(param0: int, param1: int, param2: int = 2) -> pd.DataFrame:
    """This is a dummy function showing extract_columns with does."""
    pass


@extract_fields({"total": int})
@does(_sum)
def to_modify_2(param0: int, param1: int, param2: int = 2) -> dict:
    """This is a dummy function showing extract_fields with does."""
    pass


def _dummy(**values) -> dict:
    return {f"out_{k.split('_')[1]}": v for k, v in values.items()}


@extract_fields({"out_value1": int, "out_value2": str})
@tag(test_key="test-value")
# @check_output(data_type=dict, importance="fail")  To fix see https://github.com/apache/hamilton/issues/249
@does(_dummy)
def uber_decorated_function(in_value1: int, in_value2: str) -> dict:
    pass
