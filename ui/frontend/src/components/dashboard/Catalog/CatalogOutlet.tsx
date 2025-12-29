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

import { ErrorPage } from "../../common/Error";
import { Loading } from "../../common/Loading";
import { CatalogView } from "./SearchTable";
import { useURLParams } from "../../../state/urlState";
import { Project, useProjectByID } from "../../../state/api/friendlyApi";

// const DEFAULT_NUMBER_OF_VERSIONS = 5;
// const DEFAULT_NUMBER_OF_RUNS_PER_VERSION = 3;
export const CatalogOutlet = () => {
  const { projectId } = useURLParams();
  const project = useProjectByID({ projectId: projectId as number });

  if (project.isError) {
    return (
      <ErrorPage message={`Failed to load project with ID: ${projectId}`} />
    );
  } else if (
    project.isLoading ||
    project.isFetching ||
    project.isUninitialized
  ) {
    return <Loading />;
  }
  return <CatalogView project={project.data as Project} />;
};
