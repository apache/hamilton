# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from __future__ import annotations

import dataclasses
import textwrap

try:
    import pandas  # noqa: F401

    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    import numpy  # noqa: F401

    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import polars  # noqa: F401

    HAS_POLARS = True
except ImportError:
    HAS_POLARS = False

try:
    import graphviz  # noqa: F401

    HAS_GRAPHVIZ = True
except ImportError:
    HAS_GRAPHVIZ = False

AVAILABLE_LIBS: dict[str, bool] = {
    "pandas": HAS_PANDAS,
    "numpy": HAS_NUMPY,
    "polars": HAS_POLARS,
    "graphviz": HAS_GRAPHVIZ,
}


@dataclasses.dataclass(frozen=True)
class ScaffoldTemplate:
    """A scaffold template with its library requirements."""

    name: str
    description: str
    code: str
    requires: frozenset[str] = frozenset()


ALL_TEMPLATES: list[ScaffoldTemplate] = [
    ScaffoldTemplate(
        name="basic_pure_python",
        description="Simple data processing pipeline using only built-in Python types.",
        requires=frozenset(),
        code=textwrap.dedent('''\
            """Basic Hamilton module example (pure Python, no external libraries)."""


            def raw_value(raw_value_input: int) -> int:
                """Pass-through for raw input value."""
                return raw_value_input


            def doubled(raw_value: int) -> int:
                """Double the value."""
                return raw_value * 2


            def message(doubled: int) -> str:
                """Create a summary message."""
                return f"Result: {doubled}"


            # --- Driver script ---
            # from hamilton import driver
            # import my_module
            #
            # dr = driver.Builder().with_modules(my_module).build()
            # result = dr.execute(
            #     ["message", "doubled"],
            #     inputs={"raw_value_input": 5},
            # )
            # print(result)
        '''),
    ),
    ScaffoldTemplate(
        name="basic",
        description="Simple data processing pipeline with pandas.",
        requires=frozenset({"pandas"}),
        code=textwrap.dedent('''\
            """Basic Hamilton module example."""
            import pandas as pd


            def raw_data(raw_data_input: pd.DataFrame) -> pd.DataFrame:
                """Pass-through for raw input data."""
                return raw_data_input


            def cleaned(raw_data: pd.DataFrame) -> pd.DataFrame:
                """Drop rows with missing values."""
                return raw_data.dropna()


            def row_count(cleaned: pd.DataFrame) -> int:
                """Count rows after cleaning."""
                return len(cleaned)


            # --- Driver script ---
            # from hamilton import driver
            # import my_module
            #
            # dr = driver.Builder().with_modules(my_module).build()
            # result = dr.execute(
            #     ["row_count", "cleaned"],
            #     inputs={"raw_data_input": pd.DataFrame({"a": [1, 2, None], "b": [4, None, 6]})},
            # )
            # print(result)
        '''),
    ),
    ScaffoldTemplate(
        name="parameterized",
        description="Using @parameterize to create multiple nodes from one function.",
        requires=frozenset({"pandas"}),
        code=textwrap.dedent('''\
            """Hamilton module using @parameterize to create multiple nodes."""
            import pandas as pd

            from hamilton.function_modifiers import parameterize, value


            @parameterize(
                weekly_mean={"window": value(7)},
                monthly_mean={"window": value(30)},
            )
            def rolling_mean(time_series: pd.Series, window: int) -> pd.Series:
                """Compute a rolling mean with a given window size."""
                return time_series.rolling(window).mean()


            def time_series(time_series_input: pd.Series) -> pd.Series:
                """Pass-through for time series input."""
                return time_series_input


            # --- Driver script ---
            # from hamilton import driver
            # import my_module
            #
            # dr = driver.Builder().with_modules(my_module).build()
            # result = dr.execute(
            #     ["weekly_mean", "monthly_mean"],
            #     inputs={"time_series_input": pd.Series(range(60))},
            # )
        '''),
    ),
    ScaffoldTemplate(
        name="config_based",
        description="Conditional logic with @config.when.",
        requires=frozenset({"pandas"}),
        code=textwrap.dedent('''\
            """Hamilton module using @config.when for conditional logic."""
            import pandas as pd

            from hamilton.function_modifiers import config


            @config.when(env="production")
            def data_source__prod(db_connection_string: str) -> pd.DataFrame:
                """Load data from production database."""
                # In real code: pd.read_sql("SELECT * FROM table", db_connection_string)
                return pd.DataFrame({"value": [1, 2, 3]})


            @config.when(env="development")
            def data_source__dev() -> pd.DataFrame:
                """Return sample data for development."""
                return pd.DataFrame({"value": [10, 20, 30]})


            def processed(data_source: pd.DataFrame) -> pd.DataFrame:
                """Process the data source."""
                return data_source.assign(doubled=data_source["value"] * 2)


            # --- Driver script ---
            # from hamilton import driver
            # import my_module
            #
            # dr = (
            #     driver.Builder()
            #     .with_modules(my_module)
            #     .with_config({"env": "development"})
            #     .build()
            # )
            # result = dr.execute(["processed"])
        '''),
    ),
    ScaffoldTemplate(
        name="data_pipeline",
        description="ETL workflow: ingest -> clean -> transform -> aggregate.",
        requires=frozenset({"pandas"}),
        code=textwrap.dedent('''\
            """Hamilton data pipeline: ingest -> clean -> transform -> aggregate."""
            import pandas as pd


            def raw_data(raw_data_input: pd.DataFrame) -> pd.DataFrame:
                """Ingest raw data."""
                return raw_data_input


            def cleaned_data(raw_data: pd.DataFrame) -> pd.DataFrame:
                """Remove nulls and duplicates."""
                return raw_data.dropna().drop_duplicates()


            def spend(cleaned_data: pd.DataFrame) -> pd.Series:
                """Extract the spend column."""
                return cleaned_data["spend"].abs()


            def avg_spend(spend: pd.Series) -> float:
                """Average spend across all records."""
                return spend.mean()


            def total_spend(spend: pd.Series) -> float:
                """Total spend across all records."""
                return spend.sum()


            # --- Driver script ---
            # from hamilton import driver
            # import my_module
            #
            # dr = driver.Builder().with_modules(my_module).build()
            # result = dr.execute(
            #     ["avg_spend", "total_spend"],
            #     inputs={"raw_data_input": pd.DataFrame({"spend": [-10, 20, -30]})},
            # )
        '''),
    ),
    ScaffoldTemplate(
        name="ml_pipeline",
        description="Feature engineering and train/test split with pandas and numpy.",
        requires=frozenset({"pandas", "numpy"}),
        code=textwrap.dedent('''\
            """Hamilton ML pipeline: features -> train/test split -> model -> metrics."""
            import pandas as pd
            import numpy as np


            def feature_matrix(feature_matrix_input: pd.DataFrame) -> pd.DataFrame:
                """Input feature matrix."""
                return feature_matrix_input


            def target(target_input: pd.Series) -> pd.Series:
                """Input target variable."""
                return target_input


            def train_fraction() -> float:
                """Fraction of data for training."""
                return 0.8


            def train_indices(
                feature_matrix: pd.DataFrame, train_fraction: float
            ) -> np.ndarray:
                """Random train indices."""
                n = len(feature_matrix)
                idx = np.arange(n)
                np.random.shuffle(idx)
                return idx[: int(n * train_fraction)]


            def test_indices(
                feature_matrix: pd.DataFrame, train_indices: np.ndarray
            ) -> np.ndarray:
                """Test indices (complement of train)."""
                all_idx = set(range(len(feature_matrix)))
                return np.array(sorted(all_idx - set(train_indices)))


            def train_X(feature_matrix: pd.DataFrame, train_indices: np.ndarray) -> pd.DataFrame:
                """Training features."""
                return feature_matrix.iloc[train_indices]


            def test_X(feature_matrix: pd.DataFrame, test_indices: np.ndarray) -> pd.DataFrame:
                """Test features."""
                return feature_matrix.iloc[test_indices]


            def train_y(target: pd.Series, train_indices: np.ndarray) -> pd.Series:
                """Training target."""
                return target.iloc[train_indices]


            def test_y(target: pd.Series, test_indices: np.ndarray) -> pd.Series:
                """Test target."""
                return target.iloc[test_indices]


            # --- Driver script ---
            # from hamilton import driver
            # import my_module
            #
            # dr = driver.Builder().with_modules(my_module).build()
            # result = dr.execute(
            #     ["train_X", "test_X", "train_y", "test_y"],
            #     inputs={
            #         "feature_matrix_input": pd.DataFrame({"a": range(100), "b": range(100)}),
            #         "target_input": pd.Series(range(100)),
            #     },
            # )
        '''),
    ),
    ScaffoldTemplate(
        name="data_quality",
        description="Data validation with @check_output.",
        requires=frozenset({"pandas", "numpy"}),
        code=textwrap.dedent('''\
            """Hamilton module with data quality checks using @check_output."""
            import pandas as pd
            import numpy as np

            from hamilton.function_modifiers import check_output


            @check_output(
                data_type=np.float64,
                range=(0, None),
            )
            def spend(spend_raw: pd.Series) -> pd.Series:
                """Clean spend: ensure non-negative floats."""
                return spend_raw.abs().astype(float)


            @check_output(
                data_type=np.float64,
            )
            def revenue(revenue_raw: pd.Series) -> pd.Series:
                """Clean revenue data."""
                return revenue_raw.astype(float)


            def profit(revenue: pd.Series, spend: pd.Series) -> pd.Series:
                """Profit = revenue - spend."""
                return revenue - spend


            # --- Driver script ---
            # from hamilton import driver
            # import my_module
            #
            # dr = driver.Builder().with_modules(my_module).build()
            # result = dr.execute(
            #     ["profit"],
            #     inputs={
            #         "spend_raw": pd.Series([10, 20, 30]),
            #         "revenue_raw": pd.Series([100, 200, 300]),
            #     },
            # )
        '''),
    ),
]


def get_available_templates(
    preferred_libraries: set[str] | None = None,
) -> dict[str, ScaffoldTemplate]:
    """Return templates filtered by library availability.

    If *preferred_libraries* is provided, only templates whose requirements
    are a subset of the preferred set are returned.  Otherwise, falls back
    to auto-detection via ``AVAILABLE_LIBS``.
    """
    if preferred_libraries is not None:
        return {t.name: t for t in ALL_TEMPLATES if t.requires <= preferred_libraries}
    return {
        t.name: t
        for t in ALL_TEMPLATES
        if all(AVAILABLE_LIBS.get(lib, False) for lib in t.requires)
    }


def get_capabilities(
    preferred_libraries: set[str] | None = None,
) -> dict:
    """Return capabilities, optionally filtered by user-specified libraries."""
    return {
        "libraries": dict(AVAILABLE_LIBS),
        "available_scaffolds": sorted(get_available_templates(preferred_libraries).keys()),
    }
