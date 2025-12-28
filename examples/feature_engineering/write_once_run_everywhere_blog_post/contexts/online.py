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

from datetime import datetime

import click
import uvicorn
from components import aggregations, data_loaders, features, joins, model
from fastapi import FastAPI

from hamilton import base, driver

app = FastAPI()
dr = driver.Driver(
    {"mode": "online"},
    aggregations,
    data_loaders,
    joins,
    features,
    model,
    adapter=base.DefaultAdapter(),
)


@app.get("/predict")
def get_prediction(client_id: int) -> float:
    series_out = dr.execute(
        ["predictions"], inputs={"client_id": client_id, "execution_time": datetime.now()}
    )["predictions"]
    return series_out.values[0]


@click.group()
def cli():
    pass


@cli.command()
@click.option("--port", default=8000, help="Port to serve on")
def serve(port: int):
    """This command will start the server"""
    uvicorn.run(app, host="0.0.0.0", port=port)
    click.echo("Server is running...")


@cli.command()
@click.option("--output-file", default="./out", help="Output file to write to")
def visualize(output_file: str):
    """This command will visualize execution"""
    return dr.visualize_execution(
        ["predictions"],
        output_file,
        {"format": "png"},
        inputs={"client_id": 0, "execution_time": datetime.now()},
    )


if __name__ == "__main__":
    cli()
