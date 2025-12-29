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

import { FC, useState } from "react";
import CodeExplorer, { getFunctionIdentifier } from "./CodeExplorer";
import {
  CodeArtifact,
  DAGTemplateWithData,
  ProjectWithData,
} from "../../../state/api/friendlyApi";
import { ProjectVersionSelector } from "../../common/ProjectVersionSelector";
import { extractCodeContents } from "../../../utils/codeExtraction";
import FunctionView from "./Function";
import {
  getNodesProducedByFunction,
  getDirectlyUpstreamNodes,
} from "../../../utils/dagUtils";

interface CodeProps {
  dagTemplates: DAGTemplateWithData[];
  project: ProjectWithData;
}

export const Code: FC<CodeProps> = (props) => {
  // An array of booleans, one for each function, indicating whether it's expanded

  // Current + comparison one
  const [currentIndex, setCurrentIndex] = useState(0);
  const [compareToIndex, setCompareToIndex] = useState(0);

  const dagTemplate = props.dagTemplates[currentIndex];
  const compareToDagTemplate = props.dagTemplates[compareToIndex];

  const currentHashLink = window.location.hash;

  const [whichExpanded, setWhichExpanded] = useState(
    dagTemplate.code_artifacts.map(() => true)
  );

  const compareToDAGFunctionsByIdentifier =
    compareToDagTemplate.code_artifacts.reduce((acc, artifact) => {
      acc[artifact.name] = artifact;
      return acc;
    }, {} as Record<string, CodeArtifact>);

  // A convenience function to toggle the expanded state of an individual function
  const toggleExpanded = (index: number, all: boolean) => {
    // const currentState = whichExpanded[index]
    let newWhichExpanded = [...whichExpanded];
    if (all) {
      newWhichExpanded = whichExpanded.map(() => !whichExpanded[index]);
    } else {
      newWhichExpanded[index] = !newWhichExpanded[index];
    }
    setWhichExpanded(newWhichExpanded);
  };

  return (
    <div className="flex flex-row gap-8 justify-between pt-20">
      <div className="flex flex-col gap-4 fixed">
        {props.dagTemplates.length > 1 ? (
          <ProjectVersionSelector
            dagTemplates={props.dagTemplates}
            currentProjectVersionIndex={currentIndex}
            setCurrentProjectVersionIndex={setCurrentIndex}
            compareToProjectVersionIndex={compareToIndex}
            setCompareToProjectVersionIndex={setCompareToIndex}
          />
        ) : (
          <></>
        )}
        <div className="hidden lg:block max-w-sm">
          <CodeExplorer project={props.project} dagTemplate={dagTemplate} />
        </div>
      </div>

      <div className="rounded-md flex-1 scroll-smooth mt-10 lg:ml-[28rem]">
        <div role="list" className="space-y-5 !scroll-smooth">
          {dagTemplate.code_artifacts.map((codeArtifact, index) => {
            // TODO -- get the implied nodes by looking at the code artifact identifier
            // const { sinks, intermediate, upstream } = dag.getImpliedNodes(fn);
            const nodesProducedByFunction = getNodesProducedByFunction(
              dagTemplate,
              codeArtifact
            );
            const upstreamNodes = getDirectlyUpstreamNodes(
              dagTemplate,
              codeArtifact
            );
            const functionContents = extractCodeContents(
              codeArtifact,
              dagTemplate
            );
            const compareToContents =
              compareToIndex !== currentIndex &&
              compareToDAGFunctionsByIdentifier[codeArtifact.name]
                ? extractCodeContents(
                    compareToDAGFunctionsByIdentifier[codeArtifact.name],
                    compareToDagTemplate
                  )
                : undefined;
            const fnIdentifier = getFunctionIdentifier(codeArtifact);
            const isCurrent = currentHashLink === `#${fnIdentifier}`;

            return (
              <div
                key={index}
                id={getFunctionIdentifier(codeArtifact)}
                className="scroll-m-16 scroll-smooth"
              >
                <FunctionView
                  // TODO -- use multiple if needed
                  key={index}
                  codeArtifact={codeArtifact}
                  contents={functionContents}
                  compareToContents={compareToContents}
                  nodesProducedByFunction={nodesProducedByFunction}
                  upstreamNodes={upstreamNodes}
                  expanded={whichExpanded[index]}
                  toggleExpanded={(all: boolean) => toggleExpanded(index, all)}
                  compareCodeArtifact={
                    compareToDAGFunctionsByIdentifier[codeArtifact.name]
                  }
                  isHighlighted={isCurrent}
                  dagTemplate={dagTemplate}
                ></FunctionView>
              </div>
            );
          })}
        </div>
      </div>
      <div className="w-0"></div>
    </div>
  );
};
