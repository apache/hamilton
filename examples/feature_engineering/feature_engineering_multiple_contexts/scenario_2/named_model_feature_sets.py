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

"""
This module is a light weight way to "record" feature sets that are used in a model; just define it in code!

No need for a database! Just use code and `git` to version what is or isn't used/available.
"""

model_x_features = [
    "is_summer",
    "has_pet",
    "has_children",
    "day_of_the_week_2",
    "day_of_the_week_3",
    "day_of_the_week_4",
    "day_of_the_week_5",
    "day_of_the_week_6",
    "age_zero_mean_unit_variance",
]
