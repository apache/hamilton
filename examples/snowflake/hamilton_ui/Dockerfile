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

FROM python:3.13.1-slim

RUN apt update
RUN apt upgrade sqlite3 -y
RUN pip install "sf-hamilton[ui,sdk]"
RUN pip install flask

ENV HAMILTON_ALLOWED_HOSTS=".snowflakecomputing.app"
ENV SERVER_PORT=8001

COPY pipeline_endpoint.py /pipeline_endpoint.py
COPY my_functions.py /my_functions.py

ENTRYPOINT /bin/bash -c "(hamilton ui --base-dir /hamilton-basedir &) && python /pipeline_endpoint.py"
