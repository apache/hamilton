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
To run this you need to run it as a module via bytewax.

From the `write_once_run_everywhere_blog_post` directory:

  python -m bytewax.run contexts.streaming:flow

This will print out predictions as they are computed.
"""

import datetime
import logging
import pathlib

from bytewax.connectors.files import CSVInput
from bytewax.connectors.stdio import StdOutput
from bytewax.dataflow import Dataflow
from components import aggregations, data_loaders, features, joins, model

from hamilton import base, driver

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# instantiate the driver with the right context
dr = driver.Driver(
    {"mode": "streaming"},
    aggregations,
    data_loaders,
    joins,
    features,
    model,
    adapter=base.DefaultAdapter(),
)
# pip install "sf-hamilton[visualization]" for this next line to work
# dr.display_all_functions("streaming", {"format": "png"})


def hamilton_predict(payload: dict):
    """Map function that takes in a payload and returns a prediction.

    This is a simple way to integrate Hamilton. Use it as a map function in a dataflow.

    :param payload: the event to process
    :return: prediction
    """
    for int_key in ["client_id", "budget", "age"]:
        payload[int_key] = int(float(payload[int_key]))
    series_out = dr.execute(
        ["predictions"],
        inputs={"survey_event": payload, "execution_time": datetime.datetime.now()},
    )["predictions"]
    return {"prediction": series_out.values[0], "client_id": payload["client_id"]}


"""
Bytewax dataflow.

Note (1) : bytewax has ways to batch events (https://www.bytewax.io/apidocs/bytewax.dataflow#bytewax.dataflow.Dataflow.batch)
> e.g. flow.batch("batch_inputs", max_size=10, timeout=timedelta(.01))
We stick to mapping over single events in this example.

Note (2): bytewax has the ability to redistribute events for parallel computation (https://www.bytewax.io/apidocs/bytewax.dataflow#bytewax.dataflow.Dataflow.redistribute)
In this example we just stick to the simplest thing possible. Mapping over single events.

Note (3): you could also model the following code as Hamilton code too! But for this example we'll skip that extra
level of abstraction for now.
"""
# Bytewax dataflow.
flow = Dataflow()
# pull in the data
flow.input("surveys-in", CSVInput(pathlib.Path("survey_results.csv")))
if logger.isEnabledFor(logging.DEBUG):
    # this will print out the events as they come in using the logger.debug function.
    flow.inspect(logger.debug)
# run the hamilton_predict function on each event
flow.map(hamilton_predict)
# print the output -- in real life you'd put this back into the stream, or write it to a database.
flow.output("surveys-out", StdOutput())
