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
import { classNames } from "../../utils";
import { DAGTemplateWithoutData } from "../../state/api/friendlyApi";

export const ProjectVersionSelector = (props: {
  dagTemplates: DAGTemplateWithoutData[];
  currentProjectVersionIndex: number;
  setCurrentProjectVersionIndex: (i: number) => void;
  compareToProjectVersionIndex: number;
  setCompareToProjectVersionIndex: (i: number) => void;
}) => {
  const {
    currentProjectVersionIndex,
    setCurrentProjectVersionIndex,
    compareToProjectVersionIndex,
    setCompareToProjectVersionIndex,
  } = props;

  return (
    <div className="">
      <nav className="flex space-x-2" aria-label="Tabs">
        {props.dagTemplates.map((dagTemplates, i) => (
          <button
            onClick={() => {
              setCurrentProjectVersionIndex(i);
              setCompareToProjectVersionIndex(currentProjectVersionIndex);
            }}
            key={dagTemplates.id}
            // href={tab.href}
            className={classNames(
              currentProjectVersionIndex === i
                ? "bg-gray-200 text-gray-700"
                : compareToProjectVersionIndex === i
                ? "bg-gray-100"
                : "text-gray-500 hover:text-gray-700",
              "rounded-md px-3 py-2 text-sm font-medium"
            )}
          >
            {dagTemplates.id}
          </button>
        ))}
      </nav>
    </div>
  );
};

export const MultiProjectVersionSelector = (props: {
  dagTemplates: DAGTemplateWithoutData[];
  projectVersionsIndices: Set<number>;
  setProjectVersionsIndices: (projectVersionIndices: Set<number>) => void;
}) => {
  return (
    <div className="z-50">
      <nav className="flex space-x-2" aria-label="Tabs">
        {props.dagTemplates.map((dagTemplate, i) => (
          <button
            onClick={() => {
              const newProjectVersionIndices = new Set(
                props.projectVersionsIndices
              );
              if (props.projectVersionsIndices.has(i)) {
                newProjectVersionIndices.delete(i);
              } else {
                newProjectVersionIndices.add(i);
              }
              props.setProjectVersionsIndices(newProjectVersionIndices);
            }}
            key={dagTemplate.id}
            // href={tab.href}
            className={classNames(
              props.projectVersionsIndices.has(i)
                ? "bg-dwdarkblue text-white"
                : "bg-dwdarkblue/50 text-white",
              "rounded-md px-3 py-2 text-sm font-medium"
            )}
          >
            v. {dagTemplate.id}
          </button>
        ))}
      </nav>
    </div>
  );
};
