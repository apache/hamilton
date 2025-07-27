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

import json

from django.conf import settings
from django.contrib.postgres.fields import ArrayField as BaseArrayField
from django.db import models


class TimeStampedModel(models.Model):
    """A model that tracks the creation and update times of a model"""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class GenericAttribute(TimeStampedModel):
    """Represents a generic schema for attributes that are unstructured. These get tagged
    onto models, allowing for arbitrary metadata that the frontend can query and render.

    We're doing this so that we're not beholden too much by the schema, but we can easily store
    the commonalities. Plugins (on both the client and the FE) will define the types, which we intend to
    place in a centralized location.

    Note the design decision here -- we want to remain flexible and attach multiple attributes, for the following reasons:
    1. We may want to log more stuff over time
    2. We may want to log different stuff for different DAG types
    3. We might want to update the schema over time

    Take, for instance, the case of a NodeTemplate. We have a lot of information for Hamilton nodes that we want to store:
    - namespaces
    - whether its user-defined
    - the function location
    - tags
    - etc...

    We will very likely be changing it over time, and we don't want to have to conduct a migration
    as we do so. This design gives us the flexbility to store this data in a way that's easy to query
    (it'll be efficient enough as django automatically indexes on foreign keys), and we have flexibility.
    We can either store it all as a single json blog (E.G. a BaseHamiltonNode attribute type), or separate
    it out (or some combination).

    Furthermore, this design allows for fine-grained removal of information. Say, for instance, we
    accidentally store the code, and a customer wishes for us to remove it. Rather than looking through
    a JSON blob, we can delete the specific attributes.


    """

    name = models.CharField(max_length=63)
    type = models.CharField(max_length=63)
    schema_version = models.IntegerField()
    value = models.JSONField()

    class Meta:
        abstract = True


class ArrayField(models.Field):
    """
    A field that acts like an ArrayField when using PostgreSQL and as a serialized TextField when using SQLite.
    """

    def __init__(self, base_field, **kwargs):
        self.base_field = base_field
        self.array_field = BaseArrayField(base_field, **kwargs)
        super().__init__(**kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        return name, path, (self.base_field,) + tuple(args), kwargs

    def db_type(self, connection):
        return "text"

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return json.loads(value)

    def to_python(self, value):
        if isinstance(value, list) or value is None:
            return value
        return json.loads(value)

    def get_db_prep_save(self, value, connection):
        return json.dumps(value)

    def get_prep_value(self, value):
        return json.dumps(value)

    def value_to_string(self, obj):
        value = self.value_from_object(obj)
        if isinstance(value, list):
            return json.dumps(value)
        return value


ArrayField = ArrayField if settings.DB == "django.db.backends.sqlite3" else BaseArrayField
