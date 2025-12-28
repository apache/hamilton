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

from inspect import cleandoc
from io import StringIO

import pandas as pd
from my_wrapper import TaxCalculator
from pandas import DataFrame


def read_table(table: str, delimiter="|") -> DataFrame:
    """
    Read table from string and return pandas DataFrame.
    """
    df = pd.read_table(StringIO(cleandoc(table)), delimiter=delimiter)
    df = df.loc[:, ~df.columns.str.match("Unnamed")]
    df.columns = df.columns.str.strip()
    return df


# ----------------------------------------------------------------------------------------------------------------------
# The Data to process
# ----------------------------------------------------------------------------------------------------------------------
input = read_table(
    """
    | Name     | Income | Children |
    | John     | 75600  | 2        |
    | Bob      | 34000  | 1        |
    | Chloe    | 111500 | 3        |
    | Thomas   | 234546 | 1        |
    | Ellis    | 144865 | 2        |
    | Deane    | 138500 | 4        |
    | Mariella | 69412  | 5        |
    | Carlos   | 65535  | 0        |
    | Toney    | 43642  | 3        |
    | Ramiro   | 117850 | 2        |
    """
)

# ----------------------------------------------------------------------------------------------------------------------
# Tax Rate & Credit rules
# ----------------------------------------------------------------------------------------------------------------------
tax_rates = {
    "Income < 50000": 0.15,  # < 50k: Tax rate is 15 %
    "Income > 50000 and Income < 70000": 0.18,  # 50k to 70k: Tax rate is 18 %
    "Income > 70000 and Income < 100000": 0.2,  # 70k to 100k: Tax rate is 20 %
    "Income > 100000 and Income < 120000": 0.22,  # 100k to 120k: Tax rate is 22 %
    "Income > 120000 and Income < 150000": 0.25,  # 120k to 150k: Tax rate is 25 %
    "Income > 150000": 0.28,  # over 150k: Tax rate is 28 %
}

tax_credits = {
    "Children == 0": 0.0,  # 0 child: Tax credit 0 %
    "Children == 1": 0.02,  # 1 child: Tax credit 2 %
    "Children == 2": 0.04,  # 2 children: Tax credit 4 %
    "Children == 3": 0.06,  # 3 children: Tax credit 6 %
    "Children == 4": 0.08,  # 4 children: Tax credit 8 %
    "Children > 4": 0.1,  # over 4 children: Tax credit 10 %
}

# ----------------------------------------------------------------------------------------------------------------------
# Run the Tax Calculator
# ----------------------------------------------------------------------------------------------------------------------

# Visualize the DAG
TaxCalculator.visualize()

# Calculate the taxes
output = TaxCalculator.calculate(input, tax_rates, tax_credits)
print(output.to_string())
