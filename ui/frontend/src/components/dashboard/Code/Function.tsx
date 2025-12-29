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

import React, { FC, useState } from "react";
import ReactDiffViewer, { DiffMethod } from "react-diff-viewer-continued";

import Highlight, { defaultProps } from "prism-react-renderer";
import { MdOutlineExpand } from "react-icons/md";
import { TbDelta } from "react-icons/tb";

import { AiOutlineCode, AiOutlineGithub } from "react-icons/ai";

import dracula from "prism-react-renderer/themes/vsLight";

import { BiNetworkChart } from "react-icons/bi";
import { FunctionGraphView } from "./FunctionGraphView";
import { NodeView } from "./CodeViewUtils";
import {
  CodeArtifact,
  CodeVersionGit1,
  DAGTemplateWithData,
  NodeTemplate,
  getCodeVersion,
} from "../../../state/api/friendlyApi";

interface FunctionProps {
  contents: string | undefined;
  compareToContents: string | undefined;
  codeArtifact: CodeArtifact;
  compareCodeArtifact: CodeArtifact | undefined;
  // codeArtifact: CodeArtifact;
  // compareFn: HamiltonFunction | undefined;
  upstreamNodes: NodeTemplate[];
  nodesProducedByFunction: NodeTemplate[];
  expanded: boolean;
  toggleExpanded: (all: boolean) => void;
  isHighlighted: boolean;
  dagTemplate: DAGTemplateWithData; // Shouldn't be necessary but I don't want to refactor viz and I want to reuse it
}

const getCodeArtifactLink = (
  codeArtifact: CodeArtifact,
  dagTemplate: DAGTemplateWithData
) => {
  /**
   * Gets the link to the function in the git repo
   * TODO -- move this to the server side. We'll want to have:
   * (1) branch, if applicable
   * (2) commit hash, in case the branch changes
   * (3) generated perma-link to the function
   */
  const functionPath = codeArtifact.path;
  // TODO -- verify that this works
  const gitVersion = getCodeVersion<CodeVersionGit1>(
    dagTemplate,
    "CodeVersionGit1"
  );

  if (gitVersion === undefined || gitVersion.git_repo.startsWith("Error:")) {
    return undefined; // TODO -- add more support
  }
  const out = `https://${
    gitVersion?.git_repo
      .replace("https://", "")
      .replace("git@", "")
      .replace(":", "/")
      .replace(".git", "") // TODO -- re-parse this correctly
  }/blob/${gitVersion?.git_hash}/${functionPath}#L${codeArtifact.start}-L${
    codeArtifact.end - 1
  }`;
  return out;
};

export const CodeView: React.FC<{
  fnContents: string;
  displayFnExpand?: boolean;
}> = (props) => {
  const [expanded, setExpanded] = useState(true);
  return (
    <div className={`text-sm w-full`}>
      {/* <h1>{fn.name}</h1> */}
      <div className="flex justify-end relative">
        {props.displayFnExpand && (
          <MdOutlineExpand
            className="text-lg hover:scale-125"
            onClick={() => setExpanded(!expanded)}
          />
        )}
      </div>
      {expanded && (
        <Highlight
          {...defaultProps}
          theme={dracula}
          code={props.fnContents}
          language="python"
        >
          {({ className, style, tokens, getLineProps, getTokenProps }) => {
            const styleToRender = {
              ...style,
              backgroundColor: "transparent",
              "word-break": "break-all",
              "white-space": "pre-wrap",
            };
            className += "";
            return (
              <pre className={className} style={styleToRender}>
                {tokens.map((line, i) => (
                  // eslint-disable-next-line react/jsx-key
                  <div {...getLineProps({ line, key: i })}>
                    {line.map((token, key) => (
                      // eslint-disable-next-line react/jsx-key
                      <span hidden={false} {...getTokenProps({ token, key })} />
                    ))}
                  </div>
                ))}
              </pre>
            );
          }}
        </Highlight>
      )}
    </div>
  );
};

export const DiffView = (props: {
  fnContents: string;
  compareFnContents: string;
}) => (
  <ReactDiffViewer
    // leftTitle={props.codeTitle}
    // rightTitle={props.priorCodeTitle}
    compareMethod={DiffMethod.LINES}
    oldValue={props.fnContents}
    newValue={props.compareFnContents}
    splitView={false} //   <div>
    styles={{ line: { wordBreak: "break-all" } }}
  />
);

const NodeListView: React.FC<{
  nodes: NodeTemplate[];
  represents: "input" | "output";
}> = ({ nodes, represents }) => {
  return (
    <>
      {nodes.map((node, index) => (
        <NodeView key={index} node={node} type={represents}></NodeView>
      ))}
    </>
  );
};

const NodeInputOutputView: React.FC<{
  consumes: NodeTemplate[];
  produces: NodeTemplate[];
}> = ({ consumes, produces }) => {
  return (
    <div className="flex flex-col gap-1 py-2 cursor-default">
      <div className="flex flex-row flex-wrap gap-1 pr-1 items-center">
        <span className="text-gray-500 text-sm">input</span>
        <NodeListView nodes={consumes} represents="input" />
      </div>
      <div className="flex flex-row flex-wrap gap-1 pr-1 items-center">
        <span className="text-gray-500 text-sm">output</span>
        <NodeListView nodes={produces} represents="output" />
      </div>
    </div>
  );
};

const FunctionView: FC<FunctionProps> = ({
  codeArtifact,
  compareToContents,
  nodesProducedByFunction,
  upstreamNodes,
  expanded,
  toggleExpanded,
  contents,
  isHighlighted,
  dagTemplate,
}) => {
  /**
   * Basic function view -- allows for linking out, visualizing the DAG, etc...
   */
  // Probably don't need two but I'll mess with it
  const DisplayIcon = expanded ? MdOutlineExpand : MdOutlineExpand;
  const CodeLinkIcon = AiOutlineGithub;
  const GraphViewIcon = BiNetworkChart;
  const DiffViewIcon = TbDelta;
  const CodeViewIcon = AiOutlineCode;
  const functionLink = getCodeArtifactLink(codeArtifact, dagTemplate);
  const diffModeAvailable = compareToContents !== undefined;

  const handleExpand = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (e.altKey) {
      toggleExpanded(true);
    } else {
      toggleExpanded(false);
    }
  };
  type ViewState = "graph" | "nodes" | "hidden";
  type DisplayMode = "code" | "diff";
  const [displayMode, setDisplayMode] = React.useState<DisplayMode>("code");
  const [miniGraphView, setMiniGraphView] = React.useState<ViewState>("nodes");
  const toggleMiniGraphView = () => {
    const views: ViewState[] = ["nodes", "graph", "hidden"];
    const indexView = views.indexOf(miniGraphView);
    const nextView = views[(indexView + 1) % views.length];
    setMiniGraphView(nextView);
  };

  return (
    <div
      className={`flex flex-col gap-2 px-2 rounded-md shadow border border-gray-200 ${
        isHighlighted ? "bg-dwlightblue/10" : "bg-white"
      }`}
    >
      <div>
        <div
          className={`border-b border-gray-100 py-2 flex flex-row justify-between items-center relative top-0 z-0`}
        >
          <h3 className="font-medium leading-6 text-gray-900">
            {codeArtifact.name}
          </h3>
          <div className="flex flex-row text-gray-500 gap-2 text-lg z-0">
            {diffModeAvailable ? (
              displayMode === "code" ? (
                <DiffViewIcon
                  className="hover:scale-125 hover:cursor-pointer"
                  onClick={() => setDisplayMode("diff")}
                />
              ) : (
                <CodeViewIcon
                  className="hover:scale-125 hover:cursor-pointer"
                  onClick={() => setDisplayMode("code")}
                />
              )
            ) : (
              <></>
            )}
            <a
              href={functionLink}
              target="_blank"
              rel="noreferrer"
              className={
                functionLink === undefined
                  ? "pointer-events-none cursor-default"
                  : ""
              }
            >
              <CodeLinkIcon
                className={
                  functionLink === undefined
                    ? "opacity-30"
                    : "hover:scale-125 hover:cursor-pointer"
                }
              />
            </a>
            <DisplayIcon
              onClick={handleExpand}
              className="hover:scale-125 hover:cursor-pointer"
            />
            <GraphViewIcon
              className="hover:scale-125 hover:cursor-pointer"
              onClick={toggleMiniGraphView}
            />
          </div>
        </div>
      </div>
      {expanded && contents ? ( // TODO -- display a dummy if we don't have code...
        displayMode === "code" || !diffModeAvailable ? (
          <CodeView fnContents={contents} />
        ) : (
          <DiffView
            fnContents={contents}
            compareFnContents={compareToContents}
          />
        )
      ) : (
        <div className="flex items-center justify-center h-full  text-gray-400 italic font-code">
          No code recorded...
        </div>
      )}

      <div
        className={`w-full ${
          miniGraphView != "hidden" && "border-t"
        } border-gray-200`}
      >
        {miniGraphView === "graph" && (
          <FunctionGraphView
            upstreamNodes={upstreamNodes}
            nodesProducedByFunction={nodesProducedByFunction}
            dagTemplate={dagTemplate}
          />
        )}
        {miniGraphView == "nodes" && (
          <NodeInputOutputView
            consumes={[...upstreamNodes]}
            produces={[...nodesProducedByFunction]}
          />
        )}
      </div>
    </div>
  );
};

export default FunctionView;
