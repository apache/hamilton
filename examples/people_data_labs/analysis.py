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

from pathlib import Path

import pandas as pd


def pdl_data(pdl_file: str, data_dir: str = "data/") -> pd.DataFrame:
    """Load raw People Data Labs data stored locally"""
    return pd.read_json(Path(data_dir, pdl_file))


def stock_data(stock_file: str, data_dir: str = "data/") -> pd.DataFrame:
    """Load raw stock data stored locally"""
    return pd.read_json(Path(data_dir, stock_file))


def company_info(pdl_data: pd.DataFrame) -> pd.DataFrame:
    """Select columns containing general company info"""
    columns = [
        "id",
        "ticker",
        "website",
        "name",
        "display_name",
        "legal_name",
        "founded",
        "industry",
        "type",
        "summary",
        "total_funding_raised",
        "latest_funding_stage",
        "number_funding_rounds",
        "last_funding_date",
        "inferred_revenue",
    ]
    return pdl_data[columns]


def employee_count_by_month_df(pdl_data: pd.DataFrame) -> pd.DataFrame:
    """Normalized employee count data"""
    return (
        pd.json_normalize(pdl_data["employee_count_by_month"])
        .assign(ticker=pdl_data["ticker"])
        .melt(
            id_vars="ticker",
            var_name="year_month",
            value_name="employee_count",
        )
        .astype({"year_month": "datetime64[ns]"})
    )


def n_company_by_funding_stage(company_info: pd.DataFrame) -> pd.Series:
    """Get the number of company per funding stage"""
    return (
        company_info.groupby("latest_funding_stage")["latest_funding_stage"]
        .value_counts()
        .sort_values(ascending=False)
    )


def selected_companies(company_info: pd.DataFrame, rounds_selection: list[str]) -> pd.DataFrame:
    """Companies with `latest_funding_stage` included in `rounds_selection"""
    return company_info.loc[company_info.latest_funding_stage.isin(rounds_selection)]


def employees_since_last_funding_round(
    employee_count_by_month_df: pd.DataFrame,
    selected_companies: pd.DataFrame,
) -> pd.DataFrame:
    """Select employee count data since the last funding round"""
    employee_count_by_month_df = employee_count_by_month_df.loc[
        employee_count_by_month_df.ticker.isin(selected_companies.ticker)
    ]
    df = pd.merge(
        left=employee_count_by_month_df,
        right=selected_companies[["ticker", "last_funding_date"]],
        on="ticker",
        how="left",
    )
    return df.loc[df.year_month > df.last_funding_date]


def _growth_rate(group):
    """aggregation for growth rate; data needs to be sorted"""
    return (group.iloc[-1] - group.iloc[0]) / group.iloc[0]


def employee_growth_rate_since_last_funding_round(
    employees_since_last_funding_round: pd.DataFrame,
) -> pd.DataFrame:
    """Employee count growth rate since last funding round"""
    return (
        employees_since_last_funding_round.sort_values(by="year_month", ascending=True)
        .groupby("ticker")["employee_count"]
        .aggregate(_growth_rate)
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={"employee_count": "employee_growth"})
    )


def stock_growth_rate_since_last_funding_round(
    stock_data: pd.DataFrame,
    employees_since_last_funding_round: pd.DataFrame,
) -> pd.DataFrame:
    """Stock data since last funding round.
    Returns None is no stock history or window found.

    NOTE. We use the minimum date from the employee count history instead of the true
    funding round date to ensure growth rates cover the same period
    """
    period_start = (
        employees_since_last_funding_round.groupby("ticker")["year_month"].min().reset_index()
    )
    df = pd.merge(left=stock_data, right=period_start, on="ticker", how="inner")

    stock_growth = dict()
    for _, row in df.iterrows():
        history = pd.json_normalize(row["historical_price"]).astype({"date": "datetime64[ns]"})

        # skip ticker if history is empty
        if history.empty:
            stock_growth[row.ticker] = None
            continue

        window = history[history.date > row.year_month]

        # skip ticker if window is empty
        if window.empty:
            stock_growth[row.ticker] = None
            continue

        stock_growth[row.ticker] = _growth_rate(window["close"])

    return (
        pd.DataFrame()
        .from_dict(stock_growth, orient="index")
        .reset_index()
        .rename(columns={"index": "ticker", 0: "stock_growth"})
    )


def augmented_company_info(
    selected_companies: pd.DataFrame,
    employee_growth_rate_since_last_funding_round: pd.DataFrame,
    stock_growth_rate_since_last_funding_round: pd.DataFrame,
) -> pd.DataFrame:
    """Merge employee count and stock growth with company info"""
    df = pd.merge(
        selected_companies,
        employee_growth_rate_since_last_funding_round,
        on="ticker",
        how="left",
    )
    df = pd.merge(
        df,
        stock_growth_rate_since_last_funding_round,
        on="ticker",
        how="left",
    )
    return df
