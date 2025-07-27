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
Module to pull a few things from langchain objects.
"""

from typing import Any, Dict

from hamilton_sdk.tracking import data_observation
from langchain_core import documents as lc_documents
from langchain_core import messages as lc_messages


@data_observation.compute_stats.register(lc_messages.BaseMessage)
def compute_stats_lc_messages(
    result: lc_messages.BaseMessage, node_name: str, node_tags: dict
) -> Dict[str, Any]:
    result = {"value": result.content, "type": result.type}

    return {
        "observability_type": "dict",
        "observability_value": result,
        "observability_schema_version": "0.0.2",
    }


@data_observation.compute_stats.register(lc_documents.Document)
def compute_stats_lc_docs(
    result: lc_documents.Document, node_name: str, node_tags: dict
) -> Dict[str, Any]:
    if hasattr(result, "to_document"):
        return data_observation.compute_stats(result.to_document(), node_name, node_tags)
    else:
        # d.page_content  # hack because not all documents are serializable
        result = {"content": result.page_content, "metadata": result.metadata}
    return {
        "observability_type": "dict",
        "observability_value": result,
        "observability_schema_version": "0.0.2",
    }


if __name__ == "__main__":
    # Example usage
    from langchain_core import messages

    msg = messages.BaseMessage(content="Hello, World!", type="greeting")
    print(data_observation.compute_stats(msg, "greeting", {}))

    doc = lc_documents.Document(page_content="Hello, World!", metadata={"source": "local_dir"})
    print(data_observation.compute_stats(doc, "document", {}))
