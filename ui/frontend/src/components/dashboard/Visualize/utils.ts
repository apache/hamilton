// Licensed to the Apache Software Foundation (ASF) under one
// or more contributor license agreements.  See the NOTICE file
// distributed with this work for additional information
// regarding copyright ownership.  The ASF licenses this file
// to you under the Apache License, Version 2.0 (the
// "License"); you may not use this file except in compliance
// with the License.  You may obtain a copy of the License at
//
//   http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing,
// software distributed under the License is distributed on an
// "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
// KIND, either express or implied.  See the License for the
// specific language governing permissions and limitations
// under the License.

import { BsFileEarmarkBreak } from "react-icons/bs";
import { IoEnter } from "react-icons/io5";
import {
  PiShareNetworkFill,
  PiFunction,
  PiDotsThreeCircleBold,
} from "react-icons/pi";
import { VscCircleFilled } from "react-icons/vsc";
import { extractTagFromNode, getPythonTypeIconFromNode } from "../../../utils";
import { DAGNode, TerminalVizNodeType } from "./types";
import { NodeTemplate } from "../../../state/api/friendlyApi";

export const nodeKey = (node: {
  nodeTemplate: NodeTemplate;
  dagIndex: number;
}) => {
  return `${node.nodeTemplate.name}-${node.dagIndex}`;
};

export const iconsForNodes = (nodes: DAGNode[]) => {
  const icons = new Set(
    nodes.flatMap((n) => {
      const iconsForNode = [];
      // if (n.userDefined) {
      //   iconsForNode.push(IoEnter);
      // }
      iconsForNode.push(getPythonTypeIconFromNode(n.nodeTemplate));
      return iconsForNode;
    })
  );
  return Array.from(icons);
};

export const iconForGroupSpecName = (groupSpecName: TerminalVizNodeType) => {
  if (groupSpecName === "module") {
    return BsFileEarmarkBreak;
  } else if (groupSpecName === "subdag") {
    return PiShareNetworkFill;
  } else if (groupSpecName === "function") {
    return PiFunction;
  } else if (groupSpecName === "input") {
    return IoEnter;
  } else if (groupSpecName === "dataQuality") {
    return PiDotsThreeCircleBold;
  }

  // } else if (groupSpecName === "subdag")
  // {
  // return BiNetworkChart;
  // }
  return VscCircleFilled;
};

export const getArtifactTypes = (nodes: DAGNode[]): Set<string> => {
  // TODO -- use the attributes to get the artifact types if we have them
  const artifactTypes = nodes
    .map(
      (n) =>
        extractTagFromNode(n.nodeTemplate, "hamilton.data_saver.sink") ||
        extractTagFromNode(n.nodeTemplate, "hamilton.data_loader.source")
    )
    .filter((n) => n !== undefined) as string[];

  return new Set(artifactTypes);
};
