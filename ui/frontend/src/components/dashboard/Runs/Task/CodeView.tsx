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

import ReactDiffViewer, { DiffMethod } from "react-diff-viewer-continued";
import { useState } from "react";
import { NodeRunWithAttributes } from "../../../../state/api/friendlyApi";
import { CodeView } from "../../Visualize/DAGViz";

function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(" ");
}

const DiffCompareView = (props: {
  code: string;
  priorCode: string;
  codeTitle: string;
  priorCodeTitle: string;
}) => {
  return (
    <ReactDiffViewer
      leftTitle={props.codeTitle}
      rightTitle={props.priorCodeTitle}
      compareMethod={DiffMethod.LINES}
      oldValue={props.priorCode}
      newValue={props.code}
      splitView={true}
      showDiffOnly={false}
    />
  );
};

// TODO -- break this out into two...

export const CodeSummaryView = (props: {
  codes: string[];
  nodeRunData: (NodeRunWithAttributes | null)[];
}) => {
  const [currentRunIndex, setCurrentRunIndex] = useState(0);
  const [priorRunIndex, setPriorRunIndex] = useState(
    props.nodeRunData.length > 1 ? 1 : null
  );

  const currentRun = props.nodeRunData[currentRunIndex];
  const priorRun =
    priorRunIndex !== null ? props.nodeRunData[priorRunIndex] : null;
  const currentCode = props.codes[currentRunIndex];
  const priorCode = priorRunIndex !== null ? props.codes[priorRunIndex] : null;

  return (
    <div className="pt-4">
      <div className="flex flex-col gap-10">
        <div className="sm:hidden">
          <label htmlFor="tabs" className="sr-only">
            Select a tab
          </label>
          <select
            id="tabs"
            name="tabs"
            className="block w-full rounded-md border-gray-300 focus:border-indigo-500 focus:ring-indigo-500"
            defaultValue={currentRun?.dag_run || undefined}
          >
            {props.nodeRunData.map((run) => (
              <option key={run?.dag_run}>{run?.dag_run}</option>
            ))}
          </select>
        </div>
        <div className="hidden sm:block">
          <nav className="flex space-x-4" aria-label="Tabs">
            {props.nodeRunData.map((nodeRun, i) => (
              <button
                onClick={() => {
                  setCurrentRunIndex(i);
                  setPriorRunIndex(currentRunIndex);
                }}
                key={nodeRun?.dag_run}
                // href={tab.href}
                className={classNames(
                  nodeRun?.dag_run === currentRun?.dag_run
                    ? "bg-gray-200 text-gray-700"
                    : currentRun?.dag_run === priorRun?.dag_run
                    ? "bg-gray-100"
                    : "text-gray-500 hover:text-gray-700",
                  "rounded-md px-3 py-2 text-sm font-medium"
                )}
              >
                {nodeRun?.dag_run}
              </button>
            ))}
          </nav>
        </div>
        {priorCode === null || priorRun === null || priorRun === currentRun ? (
          <CodeView fnContents={currentCode} />
        ) : (
          <DiffCompareView
            code={currentCode}
            priorCode={priorCode}
            codeTitle={`${currentRun?.dag_run}`}
            priorCodeTitle={`${priorRun?.dag_run}`}
          />
        )}
      </div>
    </div>
  );
};
