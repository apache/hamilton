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

from typing import List, Optional

from ninja import ModelSchema, Schema
from trackingserver_template.models import CodeArtifact, DAGTemplate, NodeTemplate


class CodeArtifactIn(ModelSchema):
    class Meta:
        model = CodeArtifact
        exclude = ["id", "created_at", "updated_at"]


class NodeTemplateIn(ModelSchema):
    class Meta:
        model = NodeTemplate
        # Exclude the foreign keys
        exclude = ["id", "dag_template", "created_at", "updated_at", "code_artifacts"]

    code_artifact_pointers: List[
        str
    ]  # Pointers to code artifacts, which are uniue by DAGTemplate/Name


class NodeTemplateOut(ModelSchema):
    dag_template_id: int

    class Meta:
        model = NodeTemplate
        fields = "__all__"

    primary_code_artifact: Optional[str] = None


class File(Schema):
    path: str
    contents: str


class CodeLog(Schema):
    files: List[File]


class DAGTemplateIn(ModelSchema):
    nodes: List[NodeTemplateIn]
    code_artifacts: List[CodeArtifactIn]
    code_log: CodeLog

    class Meta:
        model = DAGTemplate
        fields = [
            "name",
            "template_type",
            "config",
            "dag_hash",
            "tags",
            "code_hash",
            "code_version_info_type",
            "code_version_info",
            "code_version_info_schema",
        ]


class DAGTemplateOut(ModelSchema):
    class Meta:
        model = DAGTemplate
        # Note that if you call this without `prefetch_related` in an async context it will break, so ensure you use that!
        fields = "__all__"


class DAGTemplateUpdate(Schema):
    is_active: bool = True


class CodeArtifactOut(ModelSchema):
    class Meta:
        model = CodeArtifact
        fields = "__all__"


class DAGTemplateOutWithData(DAGTemplateOut):
    nodes: List[NodeTemplateOut]
    code_artifacts: List[CodeArtifactOut]
    code: Optional[CodeLog]


class CatalogResponse(Schema):
    nodes: List[NodeTemplateOut]
    code_artifacts: List[CodeArtifactOut]
