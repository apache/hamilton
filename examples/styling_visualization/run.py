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

import data_loading
import features
import model_pipeline
import sets

from hamilton import driver


def custom_style(*, node, node_class):
    """Custom style function for the visualization."""
    if node.tags.get("PII"):
        style = ({"fillcolor": "aquamarine"}, node_class, "PII")

    elif node.tags.get("owner") == "data-science":
        style = ({"fillcolor": "olive"}, node_class, "data-science")

    elif node.tags.get("owner") == "data-engineering":
        style = ({"fillcolor": "lightsalmon"}, node_class, "data-engineering")

    else:
        style = ({}, node_class, None)

    return style


dr = driver.Builder().with_modules(data_loading, features, sets, model_pipeline).build()


dr.display_all_functions("dag", custom_style_function=custom_style)
