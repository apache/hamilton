"""Module for testing pandas column stats."""

import polars as pl
import pytest
from hamilton_sdk.tracking import polars_col_stats as pcs


@pytest.fixture
def example_df():
    return pl.DataFrame(
        {
            "a": [1, 2, 3, 4, 5],
            "b": [6, 7, 8, 9, 10],
            "c": [11, 12, 13, 14, 15],
            "d": [16, 17, 18, 19, 20],
            "e": [21, 22, 23, 24, 25],
        }
    )


def test_data_type(example_df):
    assert pcs.data_type(example_df["a"]) == "Int64"


def test_count(example_df):
    assert pcs.count(example_df["a"]) == 5


def test_missing(example_df):
    assert pcs.missing(example_df["a"]) == 0


def test_zeros(example_df):
    assert pcs.zeros(example_df["a"]) == 0


def test_min(example_df):
    assert pcs.min(example_df["a"]) == 1


def test_max(example_df):
    assert pcs.max(example_df["a"]) == 5


def test_mean(example_df):
    assert pcs.mean(example_df["a"]) == 3.0


def test_std(example_df):
    assert pcs.std(example_df["a"]) == 1.5811388300841898


def test_quantile_cuts():
    assert pcs.quantile_cuts() == [0.1, 0.25, 0.5, 0.75, 0.9]


def test_quantiles(example_df):
    assert pcs.quantiles(example_df["a"], pcs.quantile_cuts()) == {
        0.1: 1.0,
        0.25: 2.0,
        0.5: 3.0,
        0.75: 4.0,
        0.9: 5.0,
    }


def test_histogram(example_df):
    assert pcs.histogram(example_df["a"], num_hist_bins=3) == {
        "[1.0, 2.333333]": 2,
        "(2.333333, 3.666667]": 1,
        "(3.666667, 5.0]": 2,
    }


# test string column stats
@pytest.fixture
def example_df_string():
    return pl.DataFrame(
        {
            "a": ["a", "b", "c", "d", "e"],
            "b": ["f", "g", "h", "i", "j"],
            "c": ["k", "l", "m", "n", "o"],
            "d": ["p", "q", "r", "s", "t"],
            "e": ["u", "v", "w", "x", "y"],
        }
    )


def test_data_type_string(example_df_string):
    assert pcs.data_type(example_df_string["a"]) == "String"


def test_count_string(example_df_string):
    assert pcs.count(example_df_string["a"]) == 5


def test_missing_string(example_df_string):
    assert pcs.missing(example_df_string["a"]) == 0


def test_zeros_string(example_df_string):
    assert pcs.zeros(example_df_string["a"]) == 0


def test_min_string(example_df_string):
    assert pcs.min(example_df_string["a"]) == "a"


def test_max_string(example_df_string):
    assert pcs.max(example_df_string["a"]) == "e"


def test_str_len(example_df_string):
    assert pcs.str_len(example_df_string["a"]).to_list() == [1, 1, 1, 1, 1]
