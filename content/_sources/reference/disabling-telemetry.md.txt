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
