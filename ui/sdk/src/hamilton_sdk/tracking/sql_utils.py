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

import sqlglot


def parse_sql_query(query: str) -> dict:
    """Parses a sql query and returns a string that can be used as a filename.

    TODO: figure out best long term place for this.

    :param query: The query to parse.
    :return: metadata about the query
    """
    parsed = sqlglot.parse_one(query)
    metadata = {}
    for idx, table in enumerate(parsed.find_all(sqlglot.exp.Table)):
        if not table.catalog or not table.db:
            continue
        metadata[f"table-{idx}"] = {
            "catalog": table.catalog,
            "database": table.db,
            "name": table.name,
        }
    return metadata
