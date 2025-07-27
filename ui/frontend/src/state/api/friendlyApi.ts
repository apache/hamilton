// Licensed to the Apache Software Foundation (ASF) under one
// or more contributor license agreements.  See the NOTICE file
// distributed with this work for additional information
// regarding copyright ownership.  The ASF licenses this file
// to you under the Apache License, Version 2.0 (the
// "License"); you may not use this file except in compliance
// with the License.  You may obtain a copy of the License at
//
//   http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing,
// software distributed under the License is distributed on an
// "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
// KIND, either express or implied.  See the License for the
// specific language governing permissions and limitations
// under the License.

/**
 * "Friendly" API -- this takes the BE API and does one of two things:
 * 1. Renames it -- this is in the case that the constructs we have are in the right shape and should be fed through the rest of the project
 * 2. Transforms it -- this is in the case that we want to change the constructs to a shape the user needs
 *
 * This means that *nothing* should be calling out to backendApiRaw.ts -- it should be calling out to wrappers in this file instead.
 */

import {
  AllAttributeTypes,
  AllCodeVersionTypes,
  useTrackingserverAuthApiWhoamiQuery,
  DagTemplateOut,
  useTrackingserverProjectsApiGetProjectByIdQuery,
  useTrackingserverTemplateApiGetFullDagTemplatesQuery,
  DagRunUpdate,
  ProjectOut,
  useTrackingserverTemplateApiGetLatestDagTemplatesQuery,
  ProjectAttributeOut,
  ProjectOutWithAttributes,
  useTrackingserverProjectsApiUpdateProjectMutation,
  useTrackingserverProjectsApiGetProjectsQuery,
  useTrackingserverProjectsApiCreateProjectMutation,
  WhoAmIResult,
  useTrackingserverTemplateApiUpdateDagTemplateMutation,
  useTrackingserverRunTrackingApiGetLatestDagRunsQuery,
  DagRunOut,
  useTrackingserverTemplateApiGetDagTemplateCatalogQuery,
  NodeTemplateOut,
  AllNodeMetadataTypes,
  CodeArtifactOut,
  useTrackingserverRunTrackingApiGetLatestTemplateRunsQuery,
  NodeRunOutWithExtraData,
  DagRunOutWithData,
  NodeRunOutWithAttributes,
  useTrackingserverRunTrackingApiGetDagRunsQuery,
  useTrackingserverRunTrackingApiGetNodeRunForDagsQuery,
  NodeRunAttributeOut,
  useTrackingserverAuthApiDeleteApiKeyMutation,
  useTrackingserverAuthApiGetApiKeysQuery,
  useTrackingserverAuthApiCreateApiKeyMutation,
  ApiKeyOut,
  DagTemplateOutWithData,
  useTrackingserverAuthApiPhoneHomeQuery,
} from "./backendApiRaw";

/**
 * Account information
 */
export const useUserInformation = useTrackingserverAuthApiWhoamiQuery;
export const useDeleteAPIKey = useTrackingserverAuthApiDeleteApiKeyMutation;
export const useAPIKeysFromUser = useTrackingserverAuthApiGetApiKeysQuery;
export const useCreateAPIKey = useTrackingserverAuthApiCreateApiKeyMutation;

export type APIKey = ApiKeyOut;
export type UserInformation = WhoAmIResult;

/**
 * Project/version/template information
 */

export const useProjectByID = useTrackingserverProjectsApiGetProjectByIdQuery;
export const useDAGTemplatesByID =
  useTrackingserverTemplateApiGetFullDagTemplatesQuery;
export const useLatestDAGTemplates =
  useTrackingserverTemplateApiGetLatestDagTemplatesQuery;
export const useUpdateProject =
  useTrackingserverProjectsApiUpdateProjectMutation;
export const useAllProjects = useTrackingserverProjectsApiGetProjectsQuery;
export const useCreateProject =
  useTrackingserverProjectsApiCreateProjectMutation;
export const useUpdateDAGTemplate =
  useTrackingserverTemplateApiUpdateDagTemplateMutation;

export const useCatalogView =
  useTrackingserverTemplateApiGetDagTemplateCatalogQuery;

export type Project = ProjectOut;
export type ProjectWithData = ProjectOutWithAttributes;

const nodeMetadataTypeMap = {
  NodeMetadataPythonType1: { version: 1, type: "python_type" },
};

export function getNodeOutputType<T>(
  nodeTemplate: NodeTemplate,
  cls: keyof typeof nodeMetadataTypeMap
): T | undefined {
  const { version, type } = nodeMetadataTypeMap[cls];
  if (
    version !== nodeTemplate.output_schema_version ||
    type !== nodeTemplate.output_type
  ) {
    return undefined;
  }
  return nodeTemplate.output as T;
}

export type NodeMetadataPythonType1 = AllNodeMetadataTypes["python_type__1"];

// export type CodeVersionGit1 = AllCodeVersionTypes["git__1"];

/**
 * DAG Template information
 */

export type DAGTemplateWithoutData = DagTemplateOut;
export type DAGTemplateWithData = DagTemplateOutWithData;
export type NodeTemplate = NodeTemplateOut;
export type CodeArtifact = CodeArtifactOut;

export type Classification =
  | "transform"
  | "artifact"
  | "data_loader"
  | "data_saver"
  | "input";

const codeVersionTypeMap = {
  CodeVersionGit1: { version: 1, type: "git" },
};

export function getCodeVersion<T>(
  projectVersion: DAGTemplateWithoutData,
  cls: keyof typeof codeVersionTypeMap
): T | undefined {
  const { version, type } = codeVersionTypeMap[cls];
  if (
    version !== projectVersion.code_version_info_schema ||
    type !== projectVersion.code_version_info_type
  ) {
    return undefined;
  }
  return projectVersion.code_version_info as T;
}

export type CodeVersionGit1 = AllCodeVersionTypes["git__1"];

/**
 * Run tracking information
 */

export const useLatestDAGRuns =
  useTrackingserverRunTrackingApiGetLatestDagRunsQuery;

export const useDAGRunsByIds = useTrackingserverRunTrackingApiGetDagRunsQuery;

export const useNodeRunsByTemplateAndProject =
  useTrackingserverRunTrackingApiGetLatestTemplateRunsQuery;

export const useIndividualNodeRunData =
  useTrackingserverRunTrackingApiGetNodeRunForDagsQuery;

export type RunStatusType = DagRunUpdate["run_status"] | "NOT_RUN" | "TIMEOUT";
export const RUN_SUCCESS_STATUS = "SUCCESS";
export const RUN_FAILURE_STATUS = "FAILURE";

export type DAGRun = DagRunOut;
export type DAGRunWithData = DagRunOutWithData;
export type NodeRunWithAttributes = NodeRunOutWithAttributes;
export type NodeRunAttribute = NodeRunAttributeOut;
export type CatalogNodeRun = NodeRunOutWithExtraData;

/**
 * Attributes
 */

const projectAttributeTypeMap = {
  AttributeDocumentationLoom1: { version: 1, type: "documentation_loom" },
};

export type AttributeDocumentationLoom1 =
  AllAttributeTypes["documentation_loom__1"];

export function getProjectAttributes<T>(
  allAttributes: ProjectAttributeOut[],
  cls: keyof typeof projectAttributeTypeMap
): { name: string; value: T }[] {
  const { version, type } = projectAttributeTypeMap[cls];
  return allAttributes
    .filter((attr) => attr.schema_version === version && attr.type === type)
    .map((item) => {
      return {
        name: item.name,
        value: item.value as T,
      };
    });
}

export type AttributePrimitive1 = AllAttributeTypes["primitive__1"];

export type AttributeUnsupported1 = AllAttributeTypes["unsupported__1"];

export type AttributePandasDescribe1 = AllAttributeTypes["pandas_describe__1"];

export type AttributeError1 = AllAttributeTypes["error__1"];

export type AttributeDict1 = AllAttributeTypes["dict__1"];

export type AttributeDict2 = AllAttributeTypes["dict__2"];

export type AttributeDagworksDescribe3 =
  AllAttributeTypes["dagworks_describe__3"];

export type AttributeHTML1 = AllAttributeTypes["html__1"];

export type AttributeSchema1 = AllAttributeTypes["schema__1"];

export const nodeAttributeTypeMap = {
  AttributePrimitive1: { version: 1, type: "primitive" },
  AttributeUnsupported1: { version: 1, type: "unsupported" },
  AttributePandasDescribe1: { version: 1, type: "pandas_describe" },
  AttributeError1: { version: 1, type: "error" },
  AttributeDict1: { version: 1, type: "dict" },
  AttributeDict2: { version: 2, type: "dict" },
  AttributeDagworksDescribe3: { version: 3, type: "dagworks_describe" },
  AttributeHTML1: {version: 1, type: "html"},
  AttributeSchema1: {version: 1, type: "schema"},
};

export type DAGWorksDescribeColumn =
  AttributeDagworksDescribe3[keyof AttributeDagworksDescribe3];

export function getNodeRunAttributes<T>(
  allAttributes: NodeRunAttribute[],
  dagRunIds: number[],
  cls: keyof typeof nodeAttributeTypeMap
): { name: string; value: T; runId: number }[] {
  const { version, type } = nodeAttributeTypeMap[cls];
  return allAttributes
    .map((item, i) => {
      return {
        name: item.name,
        value: item.value as T,
        schema_version: item.schema_version,
        type: item.type,
        runId: dagRunIds[i],
      };
    })
    .filter((attr) => attr.schema_version === version && attr.type === type);
}

export const usePhoneHome = useTrackingserverAuthApiPhoneHomeQuery;
