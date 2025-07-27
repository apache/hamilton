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

from django.db import models
from trackingserver_auth.models import Team, User
from trackingserver_base.models import GenericAttribute, TimeStampedModel


class ProjectMembership(TimeStampedModel):
    class Role(models.TextChoices):
        WRITE = "write"
        READ = "read"

    project = models.ForeignKey("Project", on_delete=models.SET_NULL, null=True)
    role = models.CharField(choices=Role.choices)

    class Meta:
        abstract = True


class ProjectUserMembership(ProjectMembership):
    """Represents a membership between a user and a project. This is a many-to-many relationship,"""

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        unique_together = ("user", "project")

    def __str__(self):
        return f"{self.project_id} ({self.role}) by {self.user_id}"


class ProjectTeamMembership(ProjectMembership):
    """Represents a membership between a user and a project. This is a many-to-many relationship,"""

    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True)

    class Meta:
        unique_together = ("team", "project")

    def __str__(self):
        return f"{self.project_id} ({self.role}) by {self.team_id}"


# Static project management/tracking
class Project(TimeStampedModel):
    """Represents a project -- just the metadata associated with it"""

    name = models.CharField()
    description = models.TextField()
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    tags = models.JSONField()


class ProjectAttribute(GenericAttribute):
    """Represents a project attribute -- this is a key-value pair associated with a project"""

    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True)

    class Meta:
        unique_together = ("name", "project")
