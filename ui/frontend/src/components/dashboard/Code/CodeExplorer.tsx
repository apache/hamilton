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

import React, { FC } from "react";
import { HiChevronRight, HiChevronDown } from "react-icons/hi";
import { IconType } from "react-icons/lib";
import {
  AiOutlineProject,
  AiOutlineFileText,
  AiOutlineFunction,
} from "react-icons/ai";
import { GoDot } from "react-icons/go";
import { HashLink } from "react-router-hash-link";
import {
  CodeArtifact,
  DAGTemplateWithData,
  NodeTemplate,
  Project,
  ProjectWithData,
} from "../../../state/api/friendlyApi";
import { getNodesProducedByFunction } from "../../../utils/dagUtils";

interface CodeExplorerProps {
  dagTemplate: DAGTemplateWithData;
  project: ProjectWithData;
}

const IconClose = HiChevronDown;
const IconOpen = HiChevronRight;

interface RecursiveNodeView {
  children: RecursiveNodeView[];
  icon: IconType;
  name: string;
  link: string | undefined;
  level: number;
  classNames: string;
}

export const getFunctionIdentifier = (fn: CodeArtifact) => {
  return fn.name.replace(/\./g, "_");
};

const getLink = (fn: CodeArtifact) => {
  return `#${getFunctionIdentifier(fn)}`;
};

const generateNodeViews = (
  nodes: NodeTemplate[],
  codeArtifact: CodeArtifact
) => {
  const children: RecursiveNodeView[] = [];
  return nodes.map((node) => {
    return {
      children: children,
      icon: GoDot,
      name: node.name,
      link: getLink(codeArtifact),
      level: 3,
      classNames: "text-gray-500",
    };
  });
};

const generateFunctionViews = (
  code: CodeArtifact[],
  dag: DAGTemplateWithData
) => {
  return code.map((code) => {
    const fnName = code.name.split(".").slice(-1)[0];
    const nodes = getNodesProducedByFunction(dag, code);
    return {
      children: generateNodeViews(nodes, code),
      icon: AiOutlineFunction,
      name: fnName,
      link: getLink(code),
      level: 2,
      classNames: "text-gray-600",
    };
  });
};

const generateFunctionGroupingLevelViews = (
  dag: DAGTemplateWithData,
  grouper: (codeArtifact: CodeArtifact) => string
) => {
  // Break into groups
  const groups = new Map<string, CodeArtifact[]>();
  dag.code_artifacts.forEach((fn) => {
    const group = grouper(fn);
    if (groups.has(group)) {
      groups.get(group)?.push(fn);
    } else {
      groups.set(group, [fn]);
    }
  });
  const sortedGroups = Array.from(groups.keys()).sort();
  const retval = sortedGroups.flatMap((group) => {
    const fns = groups.get(group);
    if (fns === undefined) {
      const out: RecursiveNodeView[] = [];
      return out;
    }
    return [
      {
        // children: out,
        children: generateFunctionViews(fns, dag),
        icon: AiOutlineFileText,
        name: group,
        link: undefined,
        level: 1,
        classNames: "text-gray-700",
      },
    ];
  });
  return retval;
};

const generateTopLevelView = (dag: DAGTemplateWithData, project: Project) => {
  /**
   * Generates top level recursive view with project node
   * And a subtree below
   */
  return {
    // TODO -- consider making grouping somewhat configurable...

    children: generateFunctionGroupingLevelViews(dag, (code) =>
      code.name.split(".").slice(0, -1).join(".")
    ),
    icon: AiOutlineProject,
    name: project.name,
    link: "#",
    level: 0,
    classNames: "text-gray-900 font-semibold",
  };
};
const RecursiveExplorer = ({ view }: { view: RecursiveNodeView }) => {
  const [open, setOpen] = React.useState(view.level <= 1);
  const toggleOpen = () => {
    setOpen(!open);
  };

  const ToggleIcon = open ? IconClose : IconOpen;
  const Icon = view.icon;
  return (
    <>
      <div
        className={`flex flex-row items-center ${
          view.level > 0 ? "hover:bg-gray-200" : ""
        } text-gray-600 gap-1 cursor-pointer ${view.classNames}`}
        style={{ paddingLeft: `${view.level + 0.1}rem` }}
      >
        {view.children.length > 0 && (
          <ToggleIcon className="hover:scale-125" onClick={toggleOpen} />
        )}
        <Icon className="text-lg" onClick={toggleOpen} />
        {view.link ? (
          <HashLink
            className="truncate"
            scroll={(el) =>
              el.scrollIntoView({ behavior: "smooth", block: "end" })
            }
            to={view.link}
          >
            {view.name}
          </HashLink>
        ) : (
          <span className="truncate">{view.name}</span>
        )}
      </div>
      {open &&
        view.children.map((child, index) => {
          return <RecursiveExplorer view={child} key={index} />;
        })}
    </>
  );
};
const CodeExplorer: FC<CodeExplorerProps> = ({ dagTemplate, project }) => {
  const topLevelView = generateTopLevelView(dagTemplate, project);
  return (
    <div className="text-md rounded-md overflow-clip py-1 sticky top-[4.0rem] max-h-[90vh] ">
      <RecursiveExplorer view={topLevelView} />
    </div>
  );
};

export default CodeExplorer;
