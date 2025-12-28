<!--
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.
-->

# Running the Apache Hamilton & the Apache Hamilton UI in Snowflake

This example is code for the ["Observability of Python code and application logic with Apache Hamilton UI on Snowflake Container Services" post](https://medium.com/@pkantyka/observability-of-python-code-and-application-logic-with-hamilton-ui-on-snowflake-container-services-a26693b46635) by
[Greg Kantyka](https://medium.com/@pkantyka).

Here we show the code required to be packaged up for use on Snowflake:

1. Docker file that runs the Apache Hamilton UI and a flask endpoint to exercise Apache Hamilton code
2. my_functions.py - the Apache Hamilton code that is exercised by the flask endpoint
3. pipeline_endpoint.py - the flask endpoint that exercises the Apache Hamilton code

To run see:
 - snowflake.sql that contains all the SQL to create the necessary objects in Snowflake and exercise things.

For more details see ["Observability of Python code and application logic with Apache Hamilton UI on Snowflake Container Services" post](https://medium.com/@pkantyka/observability-of-python-code-and-application-logic-with-hamilton-ui-on-snowflake-container-services-a26693b46635) by
[Greg Kantyka](https://medium.com/@pkantyka).
