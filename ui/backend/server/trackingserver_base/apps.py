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

from django.apps import AppConfig
from django.conf import settings
from django.db import models


def set_max_length_for_charfield(model_class, field_name, max_length=1024):
    field = model_class._meta.get_field(field_name)
    field.max_length = max_length


class TrackingServerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "trackingserver_base"

    def sqllite_compatibility(self):
        if settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
            from django.apps import apps

            for model in apps.get_models():
                for field in model._meta.fields:
                    if isinstance(field, models.CharField) and not field.max_length:
                        set_max_length_for_charfield(model, field.name)

    def ready(self):
        self.sqllite_compatibility()
