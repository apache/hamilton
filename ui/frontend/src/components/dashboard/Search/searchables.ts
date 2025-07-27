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

import { IconType } from "react-icons";
import { FaProjectDiagram } from "react-icons/fa";
import { AiOutlineFunction, AiOutlineNodeIndex } from "react-icons/ai";
import { resolveNav } from "../nav";
import {
  CodeArtifact,
  DAGTemplateWithData,
  NodeTemplate,
  Project,
} from "../../../state/api/friendlyApi";
import { CatalogResponse } from "../../../state/api/backendApiRaw";

// SearchableCategory is a category of items that can be searched for
export type SearchableCategory = {
  name: string; // Name of the category
  shortcut: string; // Shortcut within search dialogue for the category
  displayAll: boolean;
};

export type SearchableItem = {
  name: string;
  href: string; // TODO -- determine what else we need to render this in the react context
  searchableText: string[];
  category: SearchableCategory;
  icon: IconType; // Icon to display next to the category
};

// Currently displayAll is not used, but
// it should be used to determine whether to display all items on default or
// require the user to type something to search for items
// TODO -- use displayAll
const SEARCHABLE_CATEGORIES = {
  project: {
    name: "projects",
    // icon: (item: SearchableItem) => FaProjectDiagram,
    shortcut: ">",
    displayAll: true,
  },
  node: {
    name: "nodes",
    // icon: AiOutlineNodeIndex,
    shortcut: ".",
    displayAll: false,
  },
  fn: {
    name: "functions",
    // icon: AiOutlineFunction,
    shortcut: ":",
    displayAll: false,
  },
  page: {
    name: "navigation",
    // icon: IoNavigateOutline,
    shortcut: "/",
    displayAll: false,
  },
};

const extractProjectSearchables = (projects: Project[]): SearchableItem[] => {
  return projects.map((project) => {
    return {
      name: project.name,
      href: `/dashboard/project/${project.id}`, // TODO -- figure out where to put this -- probably to the containing function? Or the catalog location?
      searchableText: [project.name, project.description],
      category: SEARCHABLE_CATEGORIES.project,
      icon: FaProjectDiagram,
    };
  });
};

const extractNodeSearchables = (
  nodeTemplates: NodeTemplate[],
  projectId: number
): SearchableItem[] => {
  // Group by node template name -- this allows us to get each implementation then filter through them to get the comparison for every one we encounter...
  const nodeTemplatesGroupedByName = nodeTemplates.reduce(
    (acc, nodeTemplate) => {
      const { name } = nodeTemplate;
      if (acc.get(name) === undefined) {
        acc.set(name, []);
      }
      acc.get(name)?.push(nodeTemplate);
      return acc;
    },
    new Map<string, NodeTemplate[]>()
  );
  return Array.from(nodeTemplatesGroupedByName.entries()).map(
    ([nodeTemplateName, nodeTemplates]) => {
      const projectVersionIdsJoined = nodeTemplates
        .map((i) => i.dag_template)
        .sort()
        .join(",");
      return {
        name: nodeTemplateName,
        href: `/dashboard/project/${projectId}/version/${projectVersionIdsJoined}/visualize?focus=${JSON.stringify(
          { node: nodeTemplateName }
        )}`,
        searchableText: [nodeTemplateName],
        category: SEARCHABLE_CATEGORIES.node,
        icon: AiOutlineNodeIndex,
      };
    }
  );
};

const extractCodeSearchables = (
  codeArtifacts: CodeArtifact[],
  projectId: number
): SearchableItem[] => {
  // Group by node template name -- this allows us to get each implementation then filter through them to get the comparison for every one we encounter...
  const codeArtifactsGroupedByName = codeArtifacts.reduce(
    (acc, codeArtifact) => {
      const { name } = codeArtifact;
      if (acc.get(name) === undefined) {
        acc.set(name, []);
      }
      acc.get(name)?.push(codeArtifact);
      return acc;
    },
    new Map<string, CodeArtifact[]>()
  );
  const out = Array.from(codeArtifactsGroupedByName.entries()).map(
    ([codeArtifactName, codeArtifacts]) => {
      const projectVersionIdsJoined = codeArtifacts
        .map((artifact) => artifact.dag_template)
        .sort()
        .join(",");
      return {
        name: codeArtifactName,
        href: `/dashboard/project/${projectId}/version/${projectVersionIdsJoined}/visualize?focus=${JSON.stringify(
          { function: codeArtifactName }
        )}`,
        searchableText: [codeArtifactName],
        category: SEARCHABLE_CATEGORIES.fn,
        icon: AiOutlineFunction,
      };
    }
  );
  return out;
};

const getDefaultSearchables = (
  projectId: number | undefined,
  projectVersion: DAGTemplateWithData[] | undefined
) => {
  return resolveNav(projectId?.toString(), projectVersion).map(
    ({ name, href, icon }) => {
      return {
        name,
        href,
        searchableText: [name],
        category: SEARCHABLE_CATEGORIES.page,
        icon: icon,
      };
    }
  );
};

export const extractSearchables = (
  projectId: number | undefined,
  allProjects: Project[] | undefined,
  currentProjectVersions: DAGTemplateWithData[] | undefined,
  catalogData: CatalogResponse | undefined
): SearchableItem[] => {
  /**
   * Parsing node templates -- we want to give priority to anything from the current project versions (dictated by the URL).
   * That way, if we go to those, we get the full comparison.
   *
   * Then, we can add in the rest of the node templates from the catalog if we haven't seen them -- this allows us to search.
   * The catalog query is also not super fast, so this enables us to search without having to wait for the catalog query to finish,
   * although its likely we'll do that eagerly anyway
   */
  const nodeTemplatesInProjectVersions = new Set<string>();
  currentProjectVersions?.forEach((projectVersion) => {
    projectVersion.nodes.forEach((nodeTemplate) => {
      nodeTemplatesInProjectVersions.add(nodeTemplate.name);
    });
  });
  const allNodeTemplates = [
    // First add in all the ones that are part of the current project version
    ...(currentProjectVersions?.flatMap((i) => i.nodes) || []),
    // Then add in all the ones that aren't
    ...(catalogData?.nodes.filter(
      (item) => !nodeTemplatesInProjectVersions.has(item.name)
    ) || []),
  ];

  /**
   * Parsing code artifacts -- we want to basically do the same as the above
   * If its in the curret project version, we want to use that one.
   * Otherwise, we want to use the one from the catalog.
   */

  const codeArtifactsInProjectVersions = new Set<string>();
  currentProjectVersions?.forEach((projectVersion) => {
    projectVersion.code_artifacts.forEach((codeArtifact) => {
      codeArtifactsInProjectVersions.add(codeArtifact.name);
    });
  });

  const allCodeArtifacts = [
    ...(currentProjectVersions?.flatMap((i) => i.code_artifacts) || []),
    ...(catalogData?.code_artifacts.filter(
      (item) => !codeArtifactsInProjectVersions.has(item.name)
    ) || []),
  ];
  return [
    ...extractProjectSearchables(allProjects || []),
    ...(projectId !== undefined
      ? extractNodeSearchables(allNodeTemplates, projectId)
      : []),
    ...(projectId !== undefined
      ? extractCodeSearchables(allCodeArtifacts, projectId)
      : []),
    ...(projectId !== undefined
      ? getDefaultSearchables(projectId, currentProjectVersions)
      : []),
  ];
};

export const getSearchableCategories = () => {
  return Object.values(SEARCHABLE_CATEGORIES);
};
