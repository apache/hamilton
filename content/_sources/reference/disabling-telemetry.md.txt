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

# Telemetry

If you do not wish to participate in telemetry capture, one can opt-out with one of the following methods:
1. Set it to false programmatically in your code before creating a Hamilton Driver:
   ```python
   from hamilton import telemetry
   telemetry.disable_telemetry()
   ```
2. Set the key `telemetry_enabled` to `false` in ~/.hamilton.conf under the `DEFAULT` section:
   ```
   [DEFAULT]
   telemetry_enabled = False
   ```
3. Set HAMILTON_TELEMETRY_ENABLED=false as an environment variable. Either setting it for your shell session:
   ```bash
   export HAMILTON_TELEMETRY_ENABLED=false
   ```
   or passing it as part of the run command:
   ```bash
   HAMILTON_TELEMETRY_ENABLED=false python NAME_OF_MY_DRIVER.py
   ```
