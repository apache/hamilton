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

import json
import sqlite3
from pathlib import Path

import pandas as pd
import pipeline
from openlineage.client import OpenLineageClient
from openlineage.client.transport.file import FileConfig, FileTransport
from sqlalchemy import create_engine

from hamilton import driver
from hamilton.plugins import h_openlineage

HERE = Path(__file__).parent


def seed_sales_db(path: Path) -> sqlite3.Connection:
    """A small sales database: two tables the report reads."""
    conn = sqlite3.connect(path)
    orders = pd.DataFrame(
        {
            "customer_id": [1, 1, 2, 2],
            "order_date": ["2026-09-01", "2026-09-01", "2026-09-01", "2026-09-02"],
            "amount": [10.0, 5.0, 7.5, 3.0],
            "status": ["paid", "paid", "paid", "open"],
        }
    )
    customers = pd.DataFrame({"id": [1, 2], "country": ["NL", "DE"]})
    orders.to_sql("orders", conn, index=False, if_exists="replace")
    customers.to_sql("customers", conn, index=False, if_exists="replace")
    return conn


if __name__ == "__main__":
    events_file = HERE / "pipeline.json"
    events_file.unlink(missing_ok=True)
    # if you don't have a running OpenLineage server, the FileTransport writes events to a file
    client = OpenLineageClient(
        transport=FileTransport(FileConfig(log_file_path=str(events_file), append=True))
    )
    # if you have a running OpenLineage server, e.g. marquez, use this instead:
    # client = OpenLineageClient(url="http://localhost:5000")
    adapter = h_openlineage.OpenLineageAdapter(
        client, "demo_namespace", "revenue_job", sql_dataset_identity="datasource"
    )

    sales_db = seed_sales_db(HERE / "sales.db")  # a raw sqlite3 connection ...
    warehouse_db = create_engine(
        f"sqlite:///{HERE / 'warehouse.db'}"
    )  # ... and a SQLAlchemy engine

    dr = driver.Builder().with_modules(pipeline).with_adapters(adapter).build()
    result = dr.execute(
        ["saved_revenue"], inputs={"sales_db": sales_db, "warehouse_db": warehouse_db}
    )
    sales_db.close()

    print("saver metadata:", json.dumps(result["saved_revenue"]["sql_metadata"], indent=2))
    print(
        "report:", pd.read_sql("SELECT * FROM daily_revenue", warehouse_db).to_string(index=False)
    )
    for line in events_file.read_text().splitlines():
        event = json.loads(line)
        for kind in ("inputs", "outputs"):
            for dataset in event.get(kind) or []:
                print(
                    f"{event['eventType']} {kind[:-1]}: {dataset['namespace']}  {dataset['name']}"
                )
