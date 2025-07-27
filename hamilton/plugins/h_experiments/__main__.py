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

import argparse
import os
from pathlib import Path

from hamilton import telemetry
from hamilton.plugins.h_experiments.cache import JsonCache


def main():
    try:
        import fastapi  # noqa: F401
        import fastui  # noqa: F401
        import uvicorn
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(
            "Some dependencies are missing. Make sure to `pip install sf-hamilton[experiments]`"
        ) from e
    if telemetry.is_telemetry_enabled():
        telemetry.create_and_send_expt_server_event("startup")
    parser = argparse.ArgumentParser(prog="hamilton-experiments")
    parser.description = "Hamilton Experiment Server launcher"

    parser.add_argument(
        "path",
        metavar="path",
        type=str,
        default="./experiments",
        nargs="?",
        help="Set HAMILTON_EXPERIMENTS_PATH environment variable",
    )
    parser.add_argument("--host", default="127.0.0.1", type=str, help="Bind to this address")
    parser.add_argument("--port", default=8123, type=int, help="Bind to this port")

    args = parser.parse_args()

    try:
        JsonCache(args.path)
    except Exception as e:
        raise ValueError(f"Server failed to launch. No metadata cache found at {args.path}") from e

    # set environment variable that FastAPI will use
    os.environ["HAMILTON_EXPERIMENTS_PATH"] = str(Path(args.path).resolve())

    uvicorn.run("hamilton.plugins.h_experiments.server:app", host=args.host, port=args.port)
    if telemetry.is_telemetry_enabled():
        telemetry.create_and_send_expt_server_event("shutdown")


if __name__ == "__main__":
    main()
