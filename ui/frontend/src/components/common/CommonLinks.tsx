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
import { Link } from "react-router-dom";

const constructUrl = (
  projectId: number,
  versionId: number,
  nodeName: string | undefined
): string => {
  const focus = nodeName
    ? encodeURIComponent(JSON.stringify({ group: "node=" + nodeName }))
    : undefined;
  const out = `/dashboard/project/${projectId}/version/${versionId}/visualize?`;
  return focus ? out + "focus=" + focus : out;
};

export const VersionLink: React.FC<{
  projectId: number;
  versionId: number;
  nodeName: string | undefined;
}> = (props) => {
  const { projectId, versionId, nodeName } = props;
  const url = constructUrl(projectId, versionId, nodeName);

  return (
    <>
      {/* <ToolTip tooltip={props.name}> */}
      <Link
        className="text-white hover:underline bg-dwlightblue rounded-md px-1 py-1 hover:scale-105 font-normal"
        to={url}
      >
        {versionId}
      </Link>
      {/* </ToolTip> */}
    </>
  );
};

export const RunLink = (props: {
  projectId: number;
  runId: number;
  setHighlightedRun: (runId: number | null) => void;
  highlightedRun: number | null;
  taskName?: string;
}) => {
  const highlighted = props.highlightedRun === props.runId;
  // TODO -- figure out why the scale here doesn't work?
  let url = `/dashboard/project/${props.projectId}/runs/${props.runId}`;
  if (props.taskName) {
    url = `${url}/task/${props.taskName}`;
  }

  return (
    <Link
      className={`text-white hover:underline bg-dwdarkblue/90 rounded-md px-1 py-1 hover:scale-105 font-normal ${
        highlighted ? "scale-105" : ""
      }`}
      to={url}
      onMouseEnter={() => props.setHighlightedRun?.(props.runId)}
      onMouseLeave={() => props.setHighlightedRun?.(null)}
    >
      {props.runId}
    </Link>
  );
};
