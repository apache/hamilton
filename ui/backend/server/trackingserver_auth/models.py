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

import uuid

from django.db import models
from django.utils.translation import gettext as _
from trackingserver_base.models import TimeStampedModel


class AccountTier(models.TextChoices):
    COMMUNITY = "community", _("community")
    TEAM = "team", _("team")
    ENTERPRISE = "enterprise", _("enterprise")


class UserAccountMembership(TimeStampedModel):
    class Role(models.TextChoices):
        # Admin can invite/control
        ADMINISTRATOR = "administrator", _("administrator")
        # Member is required to be on any of the account's teams
        MEMBER = "member", _("member")

    """Represents a membership between a user and an account. This is a many-to-many relationship,
    as a user can be part of many accounts, and an account can have many users."""
    user = models.ForeignKey("User", on_delete=models.SET_NULL, null=True)
    account = models.ForeignKey("Account", on_delete=models.SET_NULL, null=True)
    role = models.CharField(choices=Role.choices)

    # TODO -- add a constraint on AccountTier


class Account(TimeStampedModel):
    """Represents an account tier. This can be associated with some number of users (individual),
    as well as some number of teams."""

    account_name = models.CharField(max_length=255, unique=True)
    team = models.ManyToManyField("Team")
    tier = models.CharField(max_length=20, choices=AccountTier.choices)

    def __str__(self):
        return f"{self.account_name}: {self.tier}"


class TeamAccountMembership(TimeStampedModel):
    """Represents a membership between a team and an account."""

    # Teams can only be a member of one account
    team = models.OneToOneField("Team", on_delete=models.SET_NULL, null=True)
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True)


class AuthProvider(models.TextChoices):
    PROPEL_AUTH = "propel_auth", _("propel_auth")
    PUBLIC = "public", _("public")
    TEST = "test", _("test")


class Team(TimeStampedModel):
    """A team can be synchronized with the external source of truth (e.g. propelauth)
    Currently we store the links to the external sources of truth (say, the auth provider URL)
    outside of this (in env variables), but one could imagine storing here as well
    """

    name = models.CharField(unique=True)
    auth_provider_type = models.CharField(max_length=20, choices=AuthProvider.choices)
    auth_provider_organization_id = models.CharField(max_length=255)

    def __str__(self):
        # returns the name of the organization + the source
        return f"{self.name}: {self.auth_provider_type}"


class UserTeamMembership(TimeStampedModel):
    """Represents a membership between a user and a team"""

    user = models.ForeignKey("User", on_delete=models.SET_NULL, null=True)
    team = models.ForeignKey("Team", on_delete=models.SET_NULL, null=True)

    class Meta:
        # Only one allowed per user/team
        unique_together = ("user", "team")


class User(TimeStampedModel):
    """Represents a basic user, synchronized with propelauth.
    Note we get access-level permissions from propelauth"""

    email = models.EmailField(unique=True)
    first_name = models.TextField(unique=False)
    last_name = models.TextField(unique=False)
    auth_provider_type = models.CharField(max_length=20, choices=AuthProvider.choices)
    auth_provider_user_id = models.CharField(max_length=255)
    salt = models.UUIDField(default=uuid.uuid4)  # For API keys

    def __str__(self):
        return f"{self.email} ({self.first_name} {self.last_name}): {self.auth_provider_type}"


class APIKey(TimeStampedModel):
    key_name = models.CharField(max_length=255)
    key_start = models.CharField(max_length=5)
    hashed_key = models.CharField(max_length=256, unique=True)
    user = models.ForeignKey("User", on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=True)
