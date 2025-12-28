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

"""This is a script at linearly walks through some lineage functionality that Hamilton has.

It mirrors the code that was presented for the Lineage + Hamilton in 10 minutes blog post.
"""

import pprint

import data_loading
import features
import model_pipeline
import sets

from hamilton import base, driver

# Determine configuration for creating the DAG.
config = {}  # This example has no configuration.
# instantiate the driver
adapter = base.DefaultAdapter()
dr = driver.Driver(config, data_loading, features, sets, model_pipeline, adapter=adapter)

# --- (1) What sequence of operations produced this data/model? ---
# How do the feature encoders get computed and what flows into them?
inputs = {
    "location": "data/train.csv",
    "index_col": "passengerid",
    "target_col": "survived",
    "random_state": 42,
    "max_depth": None,
    "validation_size_fraction": 0.33,
}
pprint.pprint("Visualizing how the encoders are computed")
dr.visualize_execution([features.encoders], "encoder_lineage", {"format": "png"}, inputs=inputs)

# --- (2) Whose/What data sources led to this artifact/model? ---
# There is something funky with the Random Forest model and we want to double-check
# for the current production model, what the data sources are and who owns them,
# so we can go ping them.
upstream_nodes = dr.what_is_upstream_of("fit_random_forest")
teams = []
# iterate through
for node in upstream_nodes:
    # filter to nodes that we're interested in getting information about
    if node.tags.get("source"):
        # append for output
        teams.append(
            {
                "team": node.tags.get("owner"),
                "function": node.name,
                "source": node.tags.get("source"),
            }
        )
pprint.pprint("Upstream data sources of fit_random_forest")
pprint.pprint(teams)

# --- (3) Who/What is downstream of this transform? ---
# Say we're on data engineering and want to change the source data. How could we determine
# what the artifacts that use this data are and who owns them?
downstream_nodes = dr.what_is_downstream_of("titanic_data")
artifacts = []
for node in downstream_nodes:
    # if it's an artifact function
    if node.tags.get("artifact"):
        # pull out the information we want
        artifacts.append(
            {
                "team": node.tags.get("owner"),
                "function": node.name,
                "artifact": node.tags.get("artifact"),
            }
        )
pprint.pprint("Downstream artifacts of titanic_data")
pprint.pprint(artifacts)

# --- (4) What is defined as PII data, and what does it end up in? ---
# Let's say our compliance team has come to us to understand how we're using PII data,
# i.e. what artifacts does it end up in? They want this report every month
pii_nodes = [n for n in dr.list_available_variables() if n.tags.get("PII") == "true"]
pii_to_artifacts = {}
# loop through each PII node
for node in pii_nodes:
    pii_to_artifacts[node.name] = []
    # ask what is downstream
    downstream_nodes = dr.what_is_downstream_of(node.name)
    for dwn_node in downstream_nodes:
        # Filter to nodes of interest
        if dwn_node.tags.get("artifact"):
            # pull out information
            pii_to_artifacts[node.name].append(
                {
                    "team": dwn_node.tags.get("owner"),
                    "function": dwn_node.name,
                    "artifact": dwn_node.tags.get("artifact"),
                }
            )
pprint.pprint("PII to artifacts")
pprint.pprint(pii_to_artifacts)
