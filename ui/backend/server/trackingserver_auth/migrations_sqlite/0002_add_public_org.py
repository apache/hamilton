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

from django.db import migrations
from trackingserver_auth.models import Team


def forwards(apps, schema_editor):
    if Team.objects.filter(name="Public").exists():
        return
    # This is purely due to backwards compatibility -- public was team #11 in the old repo
    public = Team(
        id=11,
        name="Public",
        auth_provider_organization_id="dummy",  # Dummy org -- this is (for now) going to be the only one of its kind
        auth_provider_type="public",
    )
    public.save()


class Migration(migrations.Migration):
    dependencies = [
        ("trackingserver_auth", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(forwards),
        migrations.RunSQL(
            "UPDATE sqlite_sequence SET seq = (SELECT MAX(id) FROM trackingserver_auth_team) WHERE name = 'trackingserver_auth_team';"
        ),
    ]
