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

import { NodeTemplate } from "../../../state/api/friendlyApi";
import { getPythonTypeIconFromNode } from "../../../utils";

export type NodeType = "input" | "intermediate" | "output";
const colors = {
  output: "bg-dwdarkblue",
  input: "bg-dwdarkblue/50",
  intermediate: "bg-dwdarkblue",
};

export const NodeView: React.FC<{
  node: NodeTemplate;
  type: NodeType;
}> = ({ node, type }) => {
  const color = colors[type];
  const Icon = getPythonTypeIconFromNode(node);
  return (
    <div
      className={`rounded-lg p-1 px-2  text-white text-sm
      items-center flex flex-row gap-2 ${color}`}
    >
      <Icon></Icon>
      {node.name}
    </div>
  );
};
