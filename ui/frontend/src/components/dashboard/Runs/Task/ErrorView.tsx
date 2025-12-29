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

import { AttributeError1 } from "../../../../state/api/backendApiRaw";
import { useState } from "react";
import {
  NodeRunWithAttributes,
  getNodeRunAttributes,
} from "../../../../state/api/friendlyApi";

function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(" ");
}

/**
 * Pretty basic error view that diffs two functions
 * We'll need to fix the access methods for the data as this is a
 * bunch of manual stuff that really should be centralized
 * For now, however, we can use this to test out the value of diffing.
 * @param props
 * @returns
 */
export const ErrorView = (props: {
  codes: string[];
  nodeRunData: (NodeRunWithAttributes | null)[];
}) => {
  const failedRuns = props.nodeRunData
    .map((data, i) => [data, i])
    .filter(
      (data, i) =>
        data[0] !== null && props.nodeRunData[i]?.status === "FAILURE"
    ) as [NodeRunWithAttributes[], number][];

  const currentRunSeedIndex = failedRuns.length > 0 ? failedRuns[0][1] : 0;

  const [currentRunIndex, setCurrentRunIndex] = useState(currentRunSeedIndex);

  const errorAttributes = getNodeRunAttributes<AttributeError1>(
    props.nodeRunData.flatMap((i) => i?.attributes || []),
    props.nodeRunData.map((i) => i?.dag_run || 0),
    "AttributeError1"
  );
  const [priorRunIndex, setPriorRunIndex] = useState(
    (currentRunSeedIndex + 1) % props.nodeRunData.length
  );

  const currentTask = props.nodeRunData[currentRunIndex];
  const error = errorAttributes.find(
    (error) => error.runId === currentTask?.dag_run
  );
  const priorTask = props.nodeRunData[priorRunIndex];
  return (
    <div>
      <div className="flex flex-col gap-10">
        <div className="sm:hidden">
          <label htmlFor="tabs" className="sr-only">
            Select a tab
          </label>
          <select
            id="tabs"
            name="tabs"
            className="block w-full rounded-md border-gray-300 focus:border-indigo-500 focus:ring-indigo-500"
            defaultValue={currentTask?.dag_run || undefined}
          >
            {props.nodeRunData.map((nodeRun) => (
              <option key={nodeRun?.dag_run}>{nodeRun?.dag_run}</option>
            ))}
          </select>
        </div>
        <div className="hidden sm:block">
          <nav className="flex space-x-4" aria-label="Tabs">
            {props.nodeRunData.map((nodeRunData, i) => (
              <button
                onClick={() => {
                  setCurrentRunIndex(i);
                  setPriorRunIndex(currentRunIndex);
                }}
                key={nodeRunData?.dag_run}
                className={classNames(
                  nodeRunData?.dag_run === currentTask?.dag_run
                    ? "bg-gray-200 text-gray-700"
                    : nodeRunData?.dag_run === priorTask?.dag_run
                    ? "bg-gray-100"
                    : "text-gray-500 hover:text-gray-700",
                  "rounded-md px-3 py-2 text-sm font-medium"
                )}
              >
                {nodeRunData?.dag_run}
              </button>
            ))}
          </nav>
        </div>
        <div>
          {error ? (
            <pre className="whitespace-pre-wrap break-words text-gray-500">
              {error.value.stack_trace.join("\n")}
            </pre>
          ) : (
            <div className="text-gray-600">
              {" "}
              <code>{currentTask?.node_name}</code> produced no errors!{" "}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
