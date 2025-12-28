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

from typing import Dict

import numpy as np
import pandas
import pandas as pd
from pandas import DataFrame, Series

from hamilton.function_modifiers import extract_columns, extract_fields, inject, pipe, source, step

# ----------------------------------------------------------------------------------------------------------------------
# Tax calculation private functions
# ----------------------------------------------------------------------------------------------------------------------


def _tax_rate(df: DataFrame, tax_rates: Dict[str, float]) -> DataFrame:
    """
    Add a series 'Tax Rate' to the DataFrame based on the tax_rates rules.
    :param df: The DataFrame
    :param tax_rates: Tax rates rules
    :return: the DataFrame with the 'Tax Rate' Series
    """
    output = DataFrame()
    for tax_rate_formula, tax_rate in tax_rates.items():
        selected = df.query(tax_rate_formula)
        if selected.empty:
            continue
        tmp = DataFrame({"Tax Rate": tax_rate}, index=selected.index)
        output = pd.concat([output, tmp], axis=0)
    df = pd.concat([df, output], axis=1)
    return df


def _tax_credit(df: DataFrame, tax_credits: Dict[str, float]) -> DataFrame:
    """
    Add a series 'Tax Credit' to the DataFrame based on the tax_credits rules.
    :param df: The DataFrame
    :param tax_credits: Tax credits rules
    :return: the DataFrame with the 'Tax Credit' Series
    """
    output = DataFrame()
    for tax_credit_formula, tax_credit in tax_credits.items():
        selected = df.query(tax_credit_formula)
        if selected.empty:
            continue
        tmp = DataFrame({"Tax Credit": tax_credit}, index=selected.index)
        output = pd.concat([output, tmp], axis=0)
    df = pd.concat([df, output], axis=1)
    return df


# ----------------------------------------------------------------------------------------------------------------------
# DataFlow: The functions defined below are displayed in the order of execution
# ----------------------------------------------------------------------------------------------------------------------


@extract_fields({"under_100k": DataFrame, "over_100k": DataFrame})
# Step 1: DataFrame is split in 2 DataFrames
def split_dataframe(input: DataFrame) -> Dict[str, DataFrame]:
    """
    That function takes the DataFrame in input and split it in 2 DataFrames:
      - under_100k: Rows where 'Income' is under 100k
      - over_100k: Rows where 'Income' is over 100k

    :param input: the DataFrame to process
    :return: a Dict with the DataFrames and the Tax Rates & Credit rules
    """
    return {
        "under_100k": input.query("Income < 100000"),
        "over_100k": input.query("Income >= 100000"),
    }


@pipe(
    step(_tax_rate, tax_rates=source("tax_rates")),  # apply the _tax_rate step
    step(_tax_credit, tax_credits=source("tax_credits")),  # apply the _tax_credit step
)
# Step 2: DataFrame for Income under 100k applies a tax calculation pipeline
def under_100k_tax(under_100k: DataFrame) -> DataFrame:
    """
    Tax calculation pipeline for 'Income' under 100k.
    :param under_100k: The DataFrame  where 'Income' is under 100k
    :return: the DataFrame with the 'Tax' Series
    """
    return under_100k


@pipe(
    step(_tax_rate, tax_rates=source("tax_rates")),  # apply the _tax_rate step
)
# Step 2: DataFrame for Income over 100k applies a tax calculation pipeline
def over_100k_tax(over_100k: DataFrame) -> DataFrame:
    """
    Tax calculation pipeline for 'Income' over 100k.
    :param over_100k: The DataFrame where 'Income' is over 100k
    :return: the DataFrame with the 'Tax' Series
    """
    return over_100k


@extract_columns("Income", "Tax Rate", "Tax Credit")
# Step 3: DataFrames are combined. Series 'Income', 'Tax Rate', 'Tax Credit' are extracted for next processing step
def combined_dataframe(under_100k_tax: DataFrame, over_100k_tax: DataFrame) -> DataFrame:
    """
    That function combine the DataFrames under_100k_tax and over_100k_tax

    The @extract_columns decorator is making the Series available for processing.
    """
    combined = pd.concat([under_100k_tax, over_100k_tax], axis=0).sort_index()
    return combined


# We use @inject decorator here because we have spaces in the names of columns.
# If column names are valid python variable names we wouldn't need this.
@inject(income=source("Income"), tax_rate=source("Tax Rate"), tax_credit=source("Tax Credit"))
# Step 4: 'Tax Formula' is calculated from 'Income', 'Tax Rate' and 'Tax Credit' series
def tax_formula(income: Series, tax_rate: Series, tax_credit: Series) -> Series:
    """
    Return a DataFrame with a series 'Tax Formula' from 'Income', 'Tax Rate' and 'Tax Credit' series.

    :param income: the 'Income' series
    :param tax_rate: the 'Tax Rate' series
    :param tax_credit: the 'Tax Credit' series

    :return: the DataFrame with the 'Tax Formula' Series
    """
    df = DataFrame({"income": income, "tax_rate": tax_rate, "tax_credit": tax_credit})
    df["Tax Formula"] = df.apply(
        lambda x: (
            f"({int(x['income'])} * {x['tax_rate']})"
            if np.isnan(x["tax_credit"])
            else f"({int(x['income'])} * {x['tax_rate']}) - ({int(x['income'])} * {x['tax_rate']}) * {x['tax_credit']}"
        ),
        axis=1,
    )
    return df["Tax Formula"]


# Step 5: 'Tax' is calculated from 'Tax Formula' series
def tax(tax_formula: Series) -> Series:
    """
    Return a series 'Tax' from 'Tax Formula' series.
    :param tax_formula: the 'Tax Formula' series.
    :return: the 'Tax Formula' Series
    """
    df = tax_formula.to_frame()
    df["Tax"] = df["Tax Formula"].apply(lambda x: round(pandas.eval(x)))
    return df["Tax"]


# Step 6 (final): DataFrame and Series computed are combined
def final_tax_dataframe(
    combined_dataframe: DataFrame, tax_formula: Series, tax: Series
) -> DataFrame:
    """
    That function combine the DataFrame and the 'Tax' and 'Tax Formula' series
    """
    df = combined_dataframe.copy(deep=True)

    # Set the 'Tax' and 'Tax Formula' series
    df["Tax Formula"] = tax_formula
    df["Tax"] = tax

    # Transform  the 'Tax Rate' and 'Tax Credit' series to display percentage
    df["Tax Rate"] = df["Tax Rate"].apply(lambda x: f"{int(x * 100)} %")
    df["Tax Credit"] = df["Tax Credit"].apply(
        lambda x: f"{int(x * 100)} %" if not np.isnan(x) else ""
    )

    # Define the order the DataFrame will be displayed
    order = ["Name", "Income", "Children", "Tax Rate", "Tax Credit", "Tax", "Tax Formula"]

    return df.reindex(columns=order)
