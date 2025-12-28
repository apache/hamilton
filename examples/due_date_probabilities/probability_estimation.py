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

from typing import List

import pandas as pd
from scipy import stats

from hamilton.function_modifiers import extract_fields


def raw_data() -> str:
    s = (
        """31 weeks	< 0.1%	< 0.1%	> 99.9%
31 weeks, 1 day	< 0.1%	< 0.1%	> 99.9%
31 weeks, 2 days	< 0.1%	< 0.1%	> 99.9%
31 weeks, 3 days	< 0.1%	< 0.1%	> 99.9%
31 weeks, 4 days	0.1%	< 0.1%	99.9%
31 weeks, 5 days	0.1%	< 0.1%	99.9%
31 weeks, 6 days	0.1%	< 0.1%	99.9%
32 weeks	0.1%	< 0.1%	99.9%
32 weeks, 1 day	0.1%	< 0.1%	99.9%
32 weeks, 2 days	0.1%	< 0.1%	99.9%
32 weeks, 3 days	0.1%	< 0.1%	99.8%
32 weeks, 4 days	0.2%	< 0.1%	99.8%
32 weeks, 5 days	0.2%	< 0.1%	99.8%
32 weeks, 6 days	0.2%	< 0.1%	99.7%
33 weeks	0.3%	< 0.1%	99.7%
33 weeks, 1 day	0.3%	< 0.1%	99.6%
33 weeks, 2 days	0.4%	0.1%	99.6%
33 weeks, 3 days	0.4%	0.1%	99.5%
33 weeks, 4 days	0.5%	0.1%	99.4%
33 weeks, 5 days	0.6%	0.1%	99.3%
33 weeks, 6 days	0.7%	0.1%	99.2%
34 weeks	0.8%	0.1%	99.1%
34 weeks, 1 day	0.9%	0.1%	99%
34 weeks, 2 days	1%	0.1%	98.9%
34 weeks, 3 days	1.2%	0.1%	98.7%
34 weeks, 4 days	1.3%	0.2%	98.5%
34 weeks, 5 days	1.5%	0.2%	98.3%
34 weeks, 6 days	1.7%	0.2%	98.1%
35 weeks	2%	0.2%	97.8%
35 weeks, 1 day	2.2%	0.3%	97.5%
35 weeks, 2 days	2.5%	0.3%	97.2%
35 weeks, 3 days	2.9%	0.3%	96.8%
35 weeks, 4 days	3.2%	0.4%	96.4%
35 weeks, 5 days	3.6%	0.4%	96%
35 weeks, 6 days	4.1%	0.4%	95.5%
36 weeks	4.6%	0.5%	95%
36 weeks, 1 day	5.1%	0.5%	94.4%
36 weeks, 2 days	5.7%	0.6%	93.7%
36 weeks, 3 days	6.3%	0.6%	93%
36 weeks, 4 days	7%	0.7%	92.2%
36 weeks, 5 days	7.8%	0.8%	91.4%
36 weeks, 6 days	8.7%	0.8%	90.5%
37 weeks	9.6%	0.9%	89.5%
37 weeks, 1 day	10.6%	1%	88.5%
37 weeks, 2 days	11.6%	1.1%	87.3%
37 weeks, 3 days	12.8%	1.1%	86.1%
37 weeks, 4 days	14%	1.2%	84.8%
37 weeks, 5 days	15.3%	1.3%	83.4%
37 weeks, 6 days	16.7%	1.4%	81.8%
38 weeks	18.3%	1.5%	80.2%
38 weeks, 1 day	19.9%	1.6%	78.5%
38 weeks, 2 days	21.6%	1.7%	76.7%
38 weeks, 3 days	23.4%	1.8%	74.8%
38 weeks, 4 days	25.3%	1.9%	72.8%
38 weeks, 5 days	27.4%	2%	70.6%
38 weeks, 6 days	29.5%	2.1%	68.4%
39 weeks	31.7%	2.2%	66%
39 weeks, 1 day	34.1%	2.4%	63.5%
39 weeks, 2 days	36.6%	2.5%	61%
39 weeks, 3 days	39.1%	2.6%	58.3%
39 weeks, 4 days	41.8%	2.7%	55.5%
39 weeks, 5 days	44.6%	2.8%	52.6%
39 weeks, 6 days	47.5%	2.9%	49.6%
40 weeks	50.5%	3%	46.5%
40 weeks, 1 day	53.6%	3.1%	43.4%
40 weeks, 2 days	56.7%	3.2%	40.1%
40 weeks, 3 days	59.9%	3.2%	36.8%
40 weeks, 4 days	63.2%	3.3%	33.5%
40 weeks, 5 days	66.5%	3.3%	30.2%
40 weeks, 6 days	69.8%	3.3%	26.9%
41 weeks	73.1%	3.3%	23.6%
41 weeks, 1 day	76.3%	3.2%	20.4%
41 weeks, 2 days	79.5%	3.1%	17.4%
41 weeks, 3 days	82.4%	3%	14.6%
41 weeks, 4 days	85.2%	2.8%	12%
41 weeks, 5 days	87.8%	2.6%	9.6%
41 weeks, 6 days	90.1%	2.3%	7.5%
42 weeks	92.2%	2%	5.8%
42 weeks, 1 day	93.9%	1.8%	4.3%
42 weeks, 2 days	95.4%	1.5%	3.1%
42 weeks, 3 days	96.6%	1.2%	2.2%
42 weeks, 4 days	97.6%	0.9%	1.5%
42 weeks, 5 days	98.3%	0.7%	1%
42 weeks, 6 days	98.8%	0.5%	0.6%
43 weeks	99.2%	0.4%	0.4%
43 weeks, 1 day	99.5%	0.3%	0.2%
43 weeks, 2 days	99.7%	0.2%	0.1%
43 weeks, 3 days	99.8%	0.1%	0.1%
43 weeks, 4 days	99.9%	0.1%	< 0.1%
43 weeks, 5 days	99.9%	< 0.1%	< 0.1%
43 weeks, 6 days	> 99.9%	< 0.1%""".replace("weeks\t", "weeks, 0 days ")
        .replace("\t", " ")
        .split("\n")
    )
    return s


def raw_probabilities(raw_data: str) -> pd.DataFrame:
    # filter out the outliers, we'll want them back in at some point but we'll let the fitting do the job
    raw_data = [item for item in raw_data if "<" not in item and ">" not in item]
    weeks = [
        int(item.split(",")[0].split()[0])
        for item in raw_data
        if "<" not in raw_data and ">" not in raw_data
    ]
    days = [int(item.split(", ")[1].split()[0]) for item in raw_data]
    probability = [float(item.split()[5].replace("%", "")) / 100 for item in raw_data]
    probabilities_data = [
        (week * 7 + day, probability) for week, day, probability in zip(weeks, days, probability)
    ]
    probabilities_df = pd.DataFrame(probabilities_data)
    probabilities_df.columns = ["days", "probability"]
    return probabilities_df  # .set_index("days")


def resampled(raw_probabilities: pd.DataFrame) -> List[int]:
    sample_data = []
    for _idx, row in raw_probabilities.iterrows():
        count = row.probability * 1000
        sample_data.extend([row.days] * int(count))
    return sample_data


@extract_fields(fields={"a": float, "loc": float, "scale": float})
def distribution_params(resampled: list[int]) -> dict[str, float]:
    a, loc, scale = stats.skewnorm.fit(resampled)
    return {"a": a, "loc": loc, "scale": scale}


def distribution(distribution_params: dict[str, float]) -> stats.rv_continuous:
    return stats.skewnorm(**distribution_params)
