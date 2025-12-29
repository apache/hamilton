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

import React from "react";
import {
  Project,
  useLatestDAGRuns,
  useLatestDAGTemplates,
} from "../../../state/api/friendlyApi";
import { Loading } from "../../common/Loading";
import { RunSummary } from "./RunSummary";
import { skipToken } from "@reduxjs/toolkit/dist/query";

export const MAX_RUNS_QUERIED = 100;

const Runs: React.FC<{ project: Project }> = ({ project }) => {
  // TODO -- figure out what happens if the project hasn't loaded yet
  const runs = useLatestDAGRuns({
    projectId: project.id as number,
    limit: MAX_RUNS_QUERIED,
  });
  // This is lazy and loads them all
  // TODO -- add to the API the ability to *also* get the project versions required
  const projectVersions = useLatestDAGTemplates(
    runs.data !== undefined
      ? {
          projectId: project.id as number,
        }
      : skipToken
  );
  if (runs.error || projectVersions.error) {
    return <span>error</span>;
  } else if (
    runs.isLoading ||
    runs.isFetching ||
    projectVersions.isLoading ||
    projectVersions.isFetching
  ) {
    return <Loading />;
  } else if (runs.isUninitialized || runs.data === undefined) {
    return <span>uninitialized, figure out why this is happening...</span>;
  }
  return (
    <RunSummary
      runs={runs.data || []}
      projectId={project.id as number}
      dagTemplates={projectVersions.data || []}
    />
  );
};

export default Runs;
