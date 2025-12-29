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

import { useParams } from "react-router-dom";
import { parseListOfInts } from "../utils/parsing";

/**
 * Gets the URL parameters -- note that these will be undefined if they're not
 * present in the URL. This is supported if we have not navigated to a page that
 * has URL-specific information (runs, tasks, versions, projects, etc...).
 */
export const useURLParams = () => {
  const {
    projectId: projectIdsRaw,
    versionId: versionIdsRaw,
    runId: runIdRaw,
    taskName: taskNameRaw,
  } = useParams();
  return {
    projectId: projectIdsRaw ? parseInt(projectIdsRaw) : undefined,
    versionIds: versionIdsRaw ? parseListOfInts(versionIdsRaw) : undefined,
    runIds: runIdRaw ? parseListOfInts(runIdRaw) : undefined,
    taskName: taskNameRaw ? taskNameRaw : undefined,
  };
};
