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

from dagster import AssetSelection, Definitions, EnvVar, define_asset_job, load_assets_from_modules

from . import assets
from .resources import DataGeneratorResource

all_assets = load_assets_from_modules([assets])

hackernews_job = define_asset_job("hackernews_job", selection=AssetSelection.all())

datagen = DataGeneratorResource(num_days=EnvVar.int("HACKERNEWS_NUM_DAYS_WINDOW"))

defs = Definitions(
    assets=all_assets,
    jobs=[hackernews_job],
    resources={
        "hackernews_api": datagen,
    },
)
