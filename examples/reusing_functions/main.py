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

from typing import Any, Dict

import pandas as pd
import reusable_subdags

from hamilton.base import ResultMixin, SimplePythonGraphAdapter
from hamilton.driver import Driver

"""A pretty simple pipeline to demonstrate function reuse.
Note that this *also* demonstrates building a custom results builder!

Why not use the standard one? Well, because time-series joining is weird.
In this case, we're running the subdag for different granularities (daily, weekly, and monthly),
and we want the functions that provide outputs for these granularities to yield one
row per datapoint. This means that the weekly series will have 7x less much data as the daily
series. Monthly series will have less than the weekly series, etc...

This results builder handles it by upsampling them all to a specified granularity.

Specifically, it:
1. Up/down-samples all time-series to the granularity specified in the constructor
2. Joins them as normal (a full outer join)

Note that pandas also has capabilities for as-of joins, but those tend to be messy and tricky to work
with. Furthermore, the as-of joins don't usually work with multiple. Upsampling/downsampling does the
trick quite well and adds more control to the user.

Note that it might be nice to pass in an argument to say which data is the "spine" column,
allowing us to have a basis of data to join with. For now, however, this should be a useful piece
of code to help with time-series joining!

Furthermore, you could actually include upsampling *in* the DAG -- this has the added feature of
encoding an index/spine column, and could be run as the final step for each subdag. Doing so is left
as an exercise to the reader.

As an example, consider the following outputs:
1. monthly_unique_users_US

timestamp
2022-09-30    6
Freq: M, Name: user_id, dtype: int64

2. weekly_unique_users_US

2022-09-04    3
2022-09-11    3
2022-09-18    2
2022-09-25    4
2022-10-02    1
Freq: W-SUN, Name: user_id, dtype: int64

3. daily_unique_users_US
timestamp
2022-09-01    2
2022-09-02    1
2022-09-03    1
2022-09-04    0
...
2022-09-22    2
2022-09-23    0
2022-09-24    2
2022-09-25    1
2022-09-26    1
Freq: D, Name: user_id, dtype: int64

Joining these with upsample granularity of "D" would produce:

            daily_unique_users_US  weekly_unique_users_US  monthly_unique_users_US
timestamp
2022-09-01                    2.0                     3.0                      6.0
2022-09-02                    1.0                     3.0                      6.0
2022-09-03                    1.0                     3.0                      6.0
2022-09-04                    0.0                     3.0                      6.0
2022-09-05                    0.0                     3.0                      6.0
2022-09-06                    0.0                     3.0                      6.0
...
2022-09-28                    NaN                     1.0                      6.0
2022-09-29                    NaN                     1.0                      6.0
2022-09-30                    NaN                     1.0                      6.0
2022-10-01                    NaN                     1.0                      NaN
2022-10-02                    NaN                     1.0                      NaN
"""


class TimeSeriesJoinResultsBuilder(ResultMixin):
    def __init__(self, upsample_frequency: str):
        """Initializes a results builder that does a time-series join
        :param upsample_frequency: Argument to pandas sample() function.
        """
        self.sampling_methodology = upsample_frequency

    def resample(self, time_series: pd.Series):
        return time_series.resample(
            self.sampling_methodology
        ).bfill()  # TODO -- think through the right fill -- ffill()/bfill()/whatnot

    @staticmethod
    def is_time_series(series: Any):
        if not isinstance(series, pd.Series):
            return False
        if not series.index.inferred_type == "datetime64":
            return False
        return True

    def build_result(self, **outputs: Dict[str, Any]) -> Any:
        non_ts_output = [
            key
            for key, value in outputs.items()
            if not TimeSeriesJoinResultsBuilder.is_time_series(value)
        ]
        if len(non_ts_output) > 0:
            raise ValueError(
                f"All outputs from DAG must be time-series -- the following are not: {non_ts_output}"
            )
        resampled_results = {key: self.resample(value) for key, value in outputs.items()}
        return pd.DataFrame(resampled_results).bfill()


def main():
    dr = Driver(
        {},
        reusable_subdags,
        adapter=SimplePythonGraphAdapter(
            result_builder=TimeSeriesJoinResultsBuilder(upsample_frequency="D")
        ),
    )

    result = dr.execute(
        [
            "daily_unique_users_US",
            "daily_unique_users_CA",
            "weekly_unique_users_US",
            "weekly_unique_users_CA",
            "monthly_unique_users_US",
            "monthly_unique_users_CA",
        ]
    )
    # dr.visualize_execution([
    #         "daily_unique_users_US",
    #         "daily_unique_users_CA",
    #         "weekly_unique_users_US",
    #         "weekly_unique_users_CA",
    #         "monthly_unique_users_US",
    #         "monthly_unique_users_CA",
    #     ], "./reusable_subdags", {"format": "png"})
    print(result)


if __name__ == "__main__":
    main()
