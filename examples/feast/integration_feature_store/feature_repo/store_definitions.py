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

"""This module contains the definitions of Feast objects pushed to the registry
It allows you to define your Feast objects dependencies as a Hamilton DAG and create
lineage with your feature transforms defined in Hamilton.
"""

import inspect
from datetime import timedelta

import feast
import feature_transformations
import pandas as pd

# new integration code, not present in simple_feature_store/


def trips_stats_3h_source(trips_stats_3h_path: str) -> feast.FileSource:
    # assert that timestamp_field exist in the result dataframe of hamilton_func
    # cannot be inferred from hamilton_func directly.
    # otherwise, Feast will eventually throw an error anyways
    transformation_func = feature_transformations.trips_stats_3h
    return feast.FileSource(
        name=transformation_func.__name__,
        path=trips_stats_3h_path,
        timestamp_field="event_timestamp",
        description=inspect.getdoc(transformation_func),
    )


def trips_stats_3h_push(trips_stats_3h_source: feast.FileSource) -> feast.data_source.PushSource:
    return feast.data_source.PushSource(
        name=trips_stats_3h_source.name + "_fresh", batch_source=trips_stats_3h_source
    )


def trips_stats_3h_fv(
    driver_entity: feast.Entity, trips_stats_3h_source: feast.FileSource
) -> feast.FeatureView:
    return feast.FeatureView(
        name=trips_stats_3h_source.name,
        source=trips_stats_3h_source,
        entities=[driver_entity],
        description=trips_stats_3h_source.description,
        ttl=timedelta(days=365),
        online=True,
    )


def trips_stats_3h_fs(
    trips_stats_3h_fv: feast.FeatureView,
    driver_hourly_stats_fv: feast.FeatureView,
) -> feast.FeatureService:
    """Feast definition: grouping of features relative to driver activity"""
    return feast.FeatureService(
        name="driver_trips_v1",
        features=[
            trips_stats_3h_fv,
            driver_hourly_stats_fv,
        ],
    )


# below is code from simple_feature_store/
# at the bottom, there is a more sophisticated approach to creating feast registry diffs


def driver_entity() -> feast.Entity:
    """Feast definition: driver entity"""
    return feast.Entity(name="driver", join_keys=["driver_id"], value_type=feast.ValueType.INT64)


def driver_hourly_stats_source(driver_source_path: str) -> feast.FileSource:
    """Feast definition: source with hourly stats of driver"""
    return feast.FileSource(
        name="driver_hourly_stats",
        path=driver_source_path,
        timestamp_field="event_timestamp",
        created_timestamp_column="created",
    )


def input_request_source() -> feast.RequestSource:
    """Feast definition: mock feature values only available at request time"""
    return feast.RequestSource(
        name="vals_to_add",
        schema=[
            feast.Field(name="val_to_add", dtype=feast.types.Int64),
            feast.Field(name="val_to_add_2", dtype=feast.types.Int64),
        ],
    )


def driver_stats_push_source(driver_hourly_stats_source: feast.FileSource) -> feast.PushSource:
    """Feast definition: push data to your store (offline, online, both)"""
    return feast.PushSource(name="driver_stats_push", batch_source=driver_hourly_stats_source)


def driver_hourly_stats_fv(
    driver_entity: feast.Entity, driver_hourly_stats_source: feast.FileSource
) -> feast.FeatureView:
    """Feast definition: feature view with hourly stats of driver"""
    return feast.FeatureView(
        name="driver_hourly_stats",
        entities=[driver_entity],
        ttl=timedelta(days=1),
        schema=[
            feast.Field(name="conv_rate", dtype=feast.types.Float32),
            feast.Field(name="acc_rate", dtype=feast.types.Float32),
            feast.Field(
                name="avg_daily_trips", dtype=feast.types.Int64, description="Average daily trips"
            ),
        ],
        online=True,
        source=driver_hourly_stats_source,
        tags={"team": "driver_performance"},
    )


def driver_hourly_stats_fresh_fv(
    driver_entity: feast.Entity,
    driver_stats_push_source: feast.PushSource,
) -> feast.FeatureView:
    """Feast definition: feature view with fresh hourly stats of driver from push source"""
    return feast.FeatureView(
        name="driver_hourly_stats_fresh",
        entities=[driver_entity],
        ttl=timedelta(days=1),
        schema=[
            feast.Field(name="conv_rate", dtype=feast.types.Float32),
            feast.Field(name="acc_rate", dtype=feast.types.Float32),
            feast.Field(name="avg_daily_trips", dtype=feast.types.Int64),
        ],
        online=True,
        source=driver_stats_push_source,  # Changed from above
        tags={"team": "driver_performance"},
    )


def _transformed_conv_rate_udf(df: pd.DataFrame) -> pd.DataFrame:
    """UDF to compute the adjusted conversion rate at request time"""
    out_df = pd.DataFrame()
    out_df["conv_rate_plus_val1"] = df["conv_rate"] + df["val_to_add"]
    out_df["conv_rate_plus_val2"] = df["conv_rate"] + df["val_to_add_2"]
    return out_df


def transformed_conv_rate(
    driver_hourly_stats_fv: feast.FeatureView, input_request_source: feast.RequestSource
) -> feast.on_demand_feature_view.OnDemandFeatureView:
    """Feast definition: feature view with features only available at request time"""
    return feast.on_demand_feature_view.OnDemandFeatureView(
        name="transformed_conv_rate",
        schema=[
            feast.Field(name="conv_rate_plus_val1", dtype=feast.types.Float64),
            feast.Field(name="conv_rate_plus_val2", dtype=feast.types.Float64),
        ],
        sources=[
            driver_hourly_stats_fv,
            input_request_source,
        ],
        udf=_transformed_conv_rate_udf,
    )


def transformed_conv_rate_fresh(
    driver_hourly_stats_fresh_fv: feast.FeatureView, input_request_source: feast.RequestSource
) -> feast.on_demand_feature_view.OnDemandFeatureView:
    """Feast definition: feature view with fresh data and
    features only available at request time"""
    return feast.on_demand_feature_view.OnDemandFeatureView(
        name="transformed_conv_rate_fresh",
        schema=[
            feast.Field(name="conv_rate_plus_val1", dtype=feast.types.Float64),
            feast.Field(name="conv_rate_plus_val2", dtype=feast.types.Float64),
        ],
        sources=[
            driver_hourly_stats_fresh_fv,
            input_request_source,
        ],
        udf=_transformed_conv_rate_udf,
    )


def driver_activity_v1_fs(
    driver_hourly_stats_fv: feast.FeatureView,
    transformed_conv_rate: feast.on_demand_feature_view.OnDemandFeatureView,
) -> feast.FeatureService:
    """Feast definition: grouping of features relative to driver activity"""
    return feast.FeatureService(
        name="driver_activity_v1",
        features=[
            driver_hourly_stats_fv[
                ["conv_rate"]
            ],  # selecting a single column of driver_hourly_stats_fv
            transformed_conv_rate,
        ],
    )


def driver_activity_v2_fs(
    driver_hourly_stats_fv: feast.FeatureView,
    transformed_conv_rate: feast.on_demand_feature_view.OnDemandFeatureView,
) -> feast.FeatureService:
    """Feast definition: grouping of features relative to driver activity"""
    return feast.FeatureService(
        name="driver_activity_v2",
        features=[
            driver_hourly_stats_fv,
            transformed_conv_rate,
        ],
    )


def driver_activity_v3_fs(
    driver_hourly_stats_fresh_fv: feast.FeatureView,
    transformed_conv_rate_fresh: feast.on_demand_feature_view.OnDemandFeatureView,
) -> feast.FeatureService:
    """Feast definition: grouping of features relative to driver activity"""
    return feast.FeatureService(
        name="driver_activity_v3",
        features=[
            driver_hourly_stats_fresh_fv,
            transformed_conv_rate_fresh,
        ],
    )


# Functions below group Feast objects by type to create the RepoContents object.
# Passing this object to the internals of Feast apply allows to have a detailed diff
# when updating the Feast registry.


def feast_entities(driver_entity: feast.Entity) -> list[feast.Entity]:
    """Collect all Feast entities"""
    return [driver_entity]


def feast_data_sources(
    driver_hourly_stats_source: feast.FileSource,
    input_request_source: feast.RequestSource,
    driver_stats_push_source: feast.data_source.PushSource,
    trips_stats_3h_source: feast.FileSource,
    trips_stats_3h_push: feast.data_source.PushSource,
) -> list[feast.data_source.DataSource]:
    """Collect all Feast data sources"""
    return [
        driver_hourly_stats_source,
        input_request_source,
        driver_stats_push_source,
        trips_stats_3h_source,
        trips_stats_3h_push,
    ]


def feast_feature_services(
    driver_activity_v1_fs: feast.FeatureService,
    driver_activity_v2_fs: feast.FeatureService,
    driver_activity_v3_fs: feast.FeatureService,
    trips_stats_3h_fs: feast.FeatureService,
) -> list[feast.FeatureService]:
    """Collect all Feast feature services"""
    return [
        driver_activity_v1_fs,
        driver_activity_v2_fs,
        driver_activity_v3_fs,
        trips_stats_3h_fs,
    ]


def feast_feature_views(
    driver_hourly_stats_fv: feast.FeatureView,
    driver_hourly_stats_fresh_fv: feast.FeatureView,
    trips_stats_3h_fv: feast.FeatureView,
) -> list[feast.FeatureView]:
    """Collect all Feast feature views"""
    return [driver_hourly_stats_fv, driver_hourly_stats_fresh_fv, trips_stats_3h_fv]


def feast_on_demand_feature_views(
    transformed_conv_rate: feast.on_demand_feature_view.OnDemandFeatureView,
    transformed_conv_rate_fresh: feast.on_demand_feature_view.OnDemandFeatureView,
) -> list[feast.on_demand_feature_view.OnDemandFeatureView]:
    """Collect all Feast on demand feature views"""
    return [transformed_conv_rate, transformed_conv_rate_fresh]


def feast_repository_content(
    feast_data_sources: list[feast.data_source.DataSource],
    feast_entities: list[feast.Entity],
    feast_feature_services: list[feast.FeatureService],
    feast_feature_views: list[feast.FeatureView],
    feast_on_demand_feature_views: list[feast.on_demand_feature_view.OnDemandFeatureView],
) -> feast.repo_contents.RepoContents:
    return feast.repo_contents.RepoContents(
        data_sources=feast_data_sources,
        entities=feast_entities,
        feature_services=feast_feature_services,
        feature_views=feast_feature_views,
        on_demand_feature_views=feast_on_demand_feature_views,
        request_feature_views=[],
        stream_feature_views=[],
    )
