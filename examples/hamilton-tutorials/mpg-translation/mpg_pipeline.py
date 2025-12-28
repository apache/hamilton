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

import numpy as np  # noqa: F401
import pandas as pd  # noqa: F401
from sklearn.linear_model import LinearRegression  # noqa: F401
from sklearn.metrics import mean_absolute_error  # noqa: F401
from sklearn.preprocessing import StandardScaler  # noqa: F401

# Write 4 functions

# 1. load/create the pandas dataframe

# 2. Create the data_sets

# 3. Create the linear model

# 4. Evaluate the model


if __name__ == "__main__":
    import __main__
    from hamilton import driver

    dr = driver.Builder().with_modules(__main__).build()
    dr.display_all_functions("mpg_pipeline.png")
    result = dr.execute(["evaluated_model", "linear_model"])
    print(result)
