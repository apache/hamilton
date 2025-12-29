/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */

import { skipToken } from "@reduxjs/toolkit/dist/query";
import { ErrorPage } from "../../common/Error";
import { Loading } from "../../common/Loading";
import { ProjectLogInstructions } from "./ProjectLogInstructions";
import {
  AttributeDocumentationLoom1,
  ProjectWithData,
  getProjectAttributes,
  useLatestDAGTemplates,
  useProjectByID,
  useUserInformation,
} from "../../../state/api/friendlyApi";
import { ProjectDocumentation } from "./ProjectDocumentation";
import ReactMarkdown from "react-markdown";
// import { VisualizeDAG } from "../Visualize/VisualizeNew";
// import { createLogicalDAG } from "../../../hamilton/dagTypes";
import { useURLParams } from "../../../state/urlState";

export const ProjectView = () => {
  const { projectId } = useURLParams();
  const whoAmI = useUserInformation();
  const latestProjectVersion = useLatestDAGTemplates(
    projectId !== undefined ? { projectId: projectId, limit: 1 } : skipToken
  );
  const project = useProjectByID(
    projectId !== undefined
      ? { projectId: projectId, attributeTypes: "documentation_loom" }
      : skipToken
  );
  if (
    latestProjectVersion.isFetching ||
    latestProjectVersion.isLoading ||
    latestProjectVersion.isUninitialized ||
    project.isFetching ||
    project.isLoading ||
    project.isUninitialized
  ) {
    return <Loading />;
  } else if (latestProjectVersion.isError || project.isError) {
    return (
      <ErrorPage
        message={`Failed to load project data for project: ${projectId}`}
      />
    );
  } else if (
    latestProjectVersion.isSuccess &&
    project.isSuccess &&
    project.data !== null
  ) {
    const out: JSX.Element[] = [
      <h1 className="text-xl font-semibold text-gray-700 px-5" key={"header"}>
        {project.data.name || ""}
      </h1>,
      <p className="text-lg text-gray-700 px-5" key={"description"}>
        <ReactMarkdown className="prose">
          {project.data.description}
        </ReactMarkdown>
      </p>,
    ];

    const projectData = project.data as ProjectWithData;
    const canWrite = projectData.role === "write";
    const loomDocs = getProjectAttributes<AttributeDocumentationLoom1>(
      projectData.attributes,
      "AttributeDocumentationLoom1"
    );
    if (loomDocs.length > 0) {
      out.push(<ProjectDocumentation loomDocs={loomDocs} />);
    }
    if (
      latestProjectVersion.data !== undefined &&
      project.data !== undefined &&
      project.data.role === "write"
    ) {
      // TODO -- add DAG Viz back in
      // out.push(
      //   <VisualizeDAG
      //     height={"h-[400px]"}
      //     dags={[createLogicalDAG(latestProjectVersion.data.dag)]}
      //     projectVersions={[latestProjectVersion.data]}
      //   />
      // );
      out.push(
        <ProjectLogInstructions
          canWrite={canWrite}
          projectId={projectId as number}
          username={whoAmI.data?.user.email || ""}
        />
      );
    }
    return <div className="pt-10 flex flex-col gap-10">{out}</div>;
  }
  return <></>;
};
