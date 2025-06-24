import dataclasses
import datetime
from enum import Enum

import numpy as np
import pandas as pd
from hamilton_sdk.tracking import utils


class TestEnum(Enum):
    VALUE1 = "value1"
    VALUE2 = "value2"


@dataclasses.dataclass
class TestDataclass:
    field1: str
    field2: int


def test_make_json_safe_with_dict():
    input_dict = {"key1": "value1", "key2": datetime.datetime.now()}
    result = utils.make_json_safe(input_dict)
    assert isinstance(result, dict)
    assert isinstance(result["key2"], str)


def test_make_json_safe_with_list():
    input_list = ["value1", datetime.datetime.now()]
    result = utils.make_json_safe(input_list)
    assert isinstance(result, list)
    assert isinstance(result[1], str)


def test_make_json_safe_with_numpy_array():
    input_array = np.array([1, 2, 3])
    result = utils.make_json_safe(input_array)
    assert isinstance(result, list)


def test_make_json_safe_with_datetime():
    input_datetime = datetime.datetime.now()
    result = utils.make_json_safe(input_datetime)
    assert isinstance(result, str)


def test_make_json_safe_with_dataclass():
    input_dataclass = TestDataclass("value1", 2)
    result = utils.make_json_safe(input_dataclass)
    assert isinstance(result, dict)


def test_make_json_safe_with_enum():
    input_enum = TestEnum.VALUE1
    result = utils.make_json_safe(input_enum)
    assert result == "value1"


def test_make_json_safe_with_object_having_to_dict():
    class TestClass:
        def to_dict(self):
            return {"field1": "value1", "field2": 2}

    input_object = TestClass()
    result = utils.make_json_safe(input_object)
    assert isinstance(result, dict)


def test_make_json_safe_with_json_serializable_types():
    input_str = "value1"
    result = utils.make_json_safe(input_str)
    assert result == "value1"

    input_int = 2
    result = utils.make_json_safe(input_int)
    assert result == 2

    input_float = 2.0
    result = utils.make_json_safe(input_float)
    assert result == 2.0

    input_bool = True
    result = utils.make_json_safe(input_bool)
    assert result is True


def test_make_json_safe_with_pandas_dataframe():
    input_dataframe = pd.DataFrame(
        {
            "A": 1.0,
            "B": pd.Timestamp("20130102"),
            "C": pd.Series(1, index=list(range(4)), dtype=np.float64),
            "D": np.array([3] * 4, dtype="int32"),
            "E": pd.Categorical(["test", "train", "test", "train"]),
            "F": "foo",
        }
    )
    actual = utils.make_json_safe(input_dataframe)
    assert actual == {
        "A": {"0": 1.0, "1": 1.0, "2": 1.0, "3": 1.0},
        "B": {"0": 1357, "1": 1357, "2": 1357, "3": 1357},
        "C": {"0": 1.0, "1": 1.0, "2": 1.0, "3": 1.0},
        "D": {"0": 3, "1": 3, "2": 3, "3": 3},
        "E": {"0": "test", "1": "train", "2": "test", "3": "train"},
        "F": {"0": "foo", "1": "foo", "2": "foo", "3": "foo"},
    }


def test_make_json_safe_with_pandas_dataframe_duplicate_indexes():
    """to_json failes with duplicate indexes"""
    input_dataframe = pd.DataFrame(
        {
            "A": 1.0,
            "B": pd.Timestamp("20130102"),
            "C": pd.Series(1, index=list(range(4)), dtype=np.float64),
            "D": np.array([3] * 4, dtype="int32"),
            "E": pd.Categorical(["test", "train", "test", "train"]),
            "F": "foo",
        },
        index=[0, 1, 0, 1],
    )
    actual = utils.make_json_safe(input_dataframe)
    assert actual == (
        "     A          B    C  D      E    F\n"
        "0  1.0 2013-01-02  1.0  3   test  foo\n"
        "1  1.0 2013-01-02  1.0  3  train  foo\n"
        "0  1.0 2013-01-02  1.0  3   test  foo\n"
        "1  1.0 2013-01-02  1.0  3  train  foo..."
    )


def test_make_json_safe_with_pandas_series():
    index = pd.date_range("2022-01-01", periods=6, freq="w")
    input_series = pd.Series([1, 10, 50, 100, 200, 400], index=index)
    actual = utils.make_json_safe(input_series)
    assert actual == {
        "1641081600000": 1,
        "1641686400000": 10,
        "1642291200000": 50,
        "1642896000000": 100,
        "1643500800000": 200,
        # "1644105600000": 400, -- skipped due to `.head()` being called
    }


def test_make_json_safe_with_file_object(tmp_path):
    with open(tmp_path / "test.txt", "w") as f:
        f.write("test")
        result = utils.make_json_safe(f)
    assert isinstance(result, str)


def test_make_json_safe_str_with_null_byte():
    """Test that null bytes are escaped"""
    input_dict = {"key1": "value1", "key2": "value\x00"}
    result = utils.make_json_safe(input_dict)
    assert isinstance(result, dict)
    assert isinstance(result["key2"], str)
    assert result["key2"] == "value\\x00"


def test_make_json_safe_with_nan():
    """Test that NaN and Infinity values are properly handled in make_json_safe"""
    import math

    # Test with a dictionary
    input_dict = {"a": math.nan, "b": np.nan, "c": 1.0, "d": math.inf, "e": -math.inf}
    result = utils.make_json_safe(input_dict)
    assert isinstance(result, dict)
    assert result["a"] == "nan"  # NaN should be represented as "nan"
    assert result["b"] == "nan"  # …same for numpy.nan
    assert result["c"] == 1.0  # Regular float should remain unchanged
    assert result["d"] == "inf"  # Infinity should be represented as "inf"
    assert result["e"] == "-inf"  # Negative infinity should be represented as "-inf"

    # Test with a list
    input_list = [math.nan, np.nan, 1.0, math.inf, -math.inf]
    result = utils.make_json_safe(input_list)
    assert isinstance(result, list)
    assert result[0] == "nan"  # NaN should be represented as "nan"
    assert result[1] == "nan"  # …same for numpy.nan
    assert result[2] == 1.0  # Regular float should remain unchanged
    assert result[3] == "inf"  # Infinity should be represented as "inf"
    assert result[4] == "-inf"  # Negative infinity should be represented as "-inf"
