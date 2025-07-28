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

import pandas as pd

from hamilton.function_modifiers import check_output


# @check_output(data_type=np.float) # TODO -- enable this once we fix the double-decorator issue
@check_output(range=(0, 1), importance="fail")
def data_might_be_in_range(data_quality_should_fail: bool) -> pd.Series:
    if data_quality_should_fail:
        return pd.Series([10.0])
    return pd.Series([0.5])


# TODO -- enable this once we fix the double-data-quality decorators with the same name bug
# @check_output(data_type=np.float)
# @check_output(range=(0, 1))
# def multi_layered_validator(data_quality_should_fail: bool) -> pd.Series:
#     if data_quality_should_fail:
#         return pd.Series([10.0])
#     return pd.Series([0.5])
