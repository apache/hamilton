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

import os.path
import uuid

from django.apps import AppConfig
from django.conf import settings
from django.db import models

from hamilton.telemetry import API_KEY, BASE_PROPERTIES, is_telemetry_enabled, send_event_json


def create_server_event_json(telemetry_key: str) -> dict:
    """Function to create payload for tracking server event.

    :param event_name: the name of the server event
    :return: dict representing the JSON to send.
    """
    old_anonymous_id = BASE_PROPERTIES["distinct_id"]
    event = {
        "event": "os_hamilton_ui_server_start",
        "api_key": API_KEY,
        "properties": {"telemetry_key": telemetry_key, "old_anonymous_id": old_anonymous_id},
    }
    event["properties"].update(BASE_PROPERTIES)
    event["properties"]["distinct_id"] = telemetry_key
    return event


def set_max_length_for_charfield(model_class, field_name, max_length=1024):
    field = model_class._meta.get_field(field_name)
    field.max_length = max_length


class TrackingServerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "trackingserver_base"

    def enable_telemetry(self):
        if is_telemetry_enabled() and settings.HAMILTON_ENV in ["local"]:
            if not os.path.exists("/data/telemetry.txt"):
                telemetry_key = str(uuid.uuid4())
                with open("/data/telemetry.txt", "w") as f:
                    f.write(telemetry_key)
            else:
                with open("/data/telemetry.txt", "r") as f:
                    telemetry_key = f.read().strip()
            send_event_json(create_server_event_json(telemetry_key))

    def sqllite_compatibility(self):
        if settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
            from django.apps import apps

            for model in apps.get_models():
                for field in model._meta.fields:
                    if isinstance(field, models.CharField) and not field.max_length:
                        set_max_length_for_charfield(model, field.name)

    def ready(self):
        self.enable_telemetry()
        self.sqllite_compatibility()
