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

import datetime
from typing import Optional

import pandas as pd
from scipy import stats


def probability_distribution() -> stats.rv_continuous:
    """These were reverse engineered from https://datayze.com/labor-probability-calculator -- see notes on how it was done (at the end)."""
    params = {"a": -4.186168447183817, "loc": 294.44465059093034, "scale": 20.670154416450384}
    return stats.skewnorm(**params)


def full_pdf(
    start_date: datetime.datetime,
    due_date: datetime.datetime,
    probability_distribution: stats.rv_continuous,
    current_date: Optional[datetime.datetime] = None,
    induction_post_due_date_days: int = 14,
) -> pd.Series:
    """Probabilities of delivery on X date on the *full* date range. We'll filter later.
    Note this does
    """
    all_dates = pd.date_range(
        start_date, start_date + datetime.timedelta(days=365)
    )  # Wide range but we'll cut it down later
    raw_pdf = probability_distribution.pdf(
        [(item - pd.Timestamp(start_date)).days for item in all_dates]
    )
    pdf = pd.Series(index=all_dates, data=raw_pdf)
    if current_date is not None:
        # rejuggle pdf
        # Use a simple parficle filter approach: https://en.wikipedia.org/wiki/Particle_filter
        pdf[pdf.index < current_date] = 0
        pdf_sum = sum(pdf)
        pdf = pdf / pdf_sum
    induction_date = due_date + datetime.timedelta(days=induction_post_due_date_days)
    probability_past_induction_date = sum(pdf[pdf.index > induction_date])
    pdf[pdf.index > induction_date] = 0
    pdf[induction_date] = probability_past_induction_date
    return pdf


def full_cdf(full_pdf: pd.Series) -> pd.Series:
    """Probability of delivery prior to X date on the *full* date range. We'll filter later."""
    return full_pdf.cumsum()


def probability_on_date(full_pdf: pd.Series, possible_dates: pd.Series) -> pd.Series:
    """Probability of deliver *on* a date for every date in the specified date range"""
    return full_pdf[possible_dates]


def probability_before_date(full_cdf: pd.Series, possible_dates: pd.Series) -> pd.Series:
    """Probability of delivery *before* a date for every date in the specified date range"""
    return full_cdf[possible_dates]
