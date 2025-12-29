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

import { FC, useMemo, useState } from "react";

import Fuse from "fuse.js";
import { HashLink } from "react-router-hash-link";
import {
  getPythonTypeIconFromNode,
  // extractTagFromNode,
  // getPythonTypeIconFromNode,
  parsePythonType,
} from "../../../utils";
import { GenericTable } from "../../common/GenericTable";
import { ToolTip } from "../../common/Tooltip";
import {
  Classification,
  CodeArtifact,
  NodeMetadataPythonType1,
  NodeTemplate,
  Project,
  getNodeOutputType,
  useCatalogView,
} from "../../../state/api/friendlyApi";
import { ErrorPage } from "../../common/Error";
import { Loading } from "../../common/Loading";
import {
  AiOutlineBarChart,
  AiOutlineFunction,
  AiOutlineTable,
} from "react-icons/ai";
import { NodeRunsView } from "./NodeRunExpansion";
import { getFunctionIdentifier } from "../Code/CodeExplorer";
import { useSearchParams } from "react-router-dom";
import {
  TagSelectorWithValues,
  selectedTagsToObj,
} from "../../common/TagSelector";

//eslint-disable-next-line @typescript-eslint/no-explicit-any
const displayTagValue = (value: any) => {
  if (typeof value === "string") {
    return value;
  }
  return JSON.stringify(value);
};
const TagDisplay: React.FC<{ tags: object; expanded: boolean }> = (props) => {
  const tagsToMap = props.expanded
    ? Object.entries(props.tags)
    : Object.entries(props.tags).slice(0, 1);
  return (
    <div className={`flex flex-col break-all overflow-clip`}>
      {tagsToMap.map(([key, value]) => {
        return (
          <div key={key} className="flex flex-row gap-1 items-baseline">
            <span className="font-semibold min-w-max">{key}</span>
            {displayTagValue(value)}
          </div>
        );
      })}
    </div>
  );
};

const DocumentationDisplay: React.FC<{
  documentation: string | undefined;
}> = (props) => {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="w-96">
      <pre
        onClick={(e) => {
          setExpanded(!expanded);
          e.stopPropagation();
        }}
        className={`${
          expanded ? "break-word whitespace-pre-wrap" : "truncate"
        }  text-gray-500 cursor-cell`}
      >
        {props.documentation}
      </pre>
    </div>
  );
};

const getNodeTypeAndColor = (node: NodeTemplate) => {
  // // TODO -- get this as node attributes from the DB
  // // const nodeType = node.userDefined
  // //   ? "input"
  // //   : extractTagFromNode(node, "hamilton.data_saver") === true ||
  // //     extractTagFromNode(node, "hamilton.data_loader") === true
  // //   ? "artifact"
  // //   : "transform";
  // const nodeType = "transform" as string;
  const classifications = node.classifications as Classification[];
  let nodeType = "transform";
  if (classifications.length > 0) {
    nodeType = classifications[0];
  }
  const bgColor =
    nodeType === "data_loader" || nodeType === "data_saver"
      ? "bg-dwdarkblue"
      : nodeType === "input"
      ? "bg-yellow-500"
      : "bg-green-500";
  const nodeTypeName = nodeType.replace("_", " ");
  return [nodeTypeName, bgColor];
};
const FeatureNameDisplay = (label: string, value: RowToDisplay) => {
  const node = value.node;
  // TODO -- get this as node attributes from the DB
  // const nodeType = node.userDefined
  //   ? "input"
  //   : extractTagFromNode(node, "hamilton.data_saver") === true ||
  //     extractTagFromNode(node, "hamilton.data_loader") === true
  //   ? "artifact"
  //   : "transform";
  const Icon = getPythonTypeIconFromNode(node);

  const [nodeType, bgColor] = getNodeTypeAndColor(node);
  const outputType = getNodeOutputType<NodeMetadataPythonType1>(
    node,
    "NodeMetadataPythonType1"
  );
  return (
    <div className="flex flex-row gap-2 break-all overflow-clip items-center cursor-default">
      {outputType ? (
        <ToolTip tooltip={parsePythonType(outputType)}>
          <Icon className="text-lg hover:scale-125 cursor-pointer"></Icon>
        </ToolTip>
      ) : null}
      <div className="">
        <div className="w-24 flex flex-row justify-end">
          <div
            className={`${bgColor} text-white p-1 rounded-lg flex w-24 justify-center font-normal`}
          >
            {nodeType}
          </div>
        </div>
      </div>
      <span className="font-semibold w-max">{node.name}</span>
    </div>
  );
};

export const getIconForCodeType = (code: CodeArtifact) => {
  if (code.type === "p_function") {
    return AiOutlineFunction;
  }
  return undefined;
};

export const FunctionDisplay = (props: {
  projectId: number;
  projectVersionId: number;
  code: CodeArtifact;
  justIcon?: boolean;
}) => {
  const { name, path } = props.code;

  if (path === undefined || name === undefined) {
    return <></>;
  }

  // const filename = path.split("/").slice(-1)[0];
  const fnIdentifier = getFunctionIdentifier(props.code);
  const url = `/dashboard/project/${props.projectId}/version/${props.projectVersionId}/code#${fnIdentifier}`;
  const Icon = getIconForCodeType(props.code);
  return (
    <div className="flex gap-2 flex-row">
      {Icon ? (
        <HashLink className="" to={url}>
          <Icon className="text-lg hover:scale-125"></Icon>
        </HashLink>
      ) : null}
      {!props.justIcon && (
        <div
          className="flex flex-row gap-2 break-all overflow-clip items-center hover:underline
    text-dwlightblue"
        >
          <HashLink className="" to={url}>
            {name.split(".").slice(-1).join(".")}
          </HashLink>
        </div>
      )}
    </div>
  );
};

interface FeatureSearchBoxProps {
  setSearch: (term: string) => void;
  term: string;
}

const FeatureSearchBox: React.FC<FeatureSearchBoxProps> = ({
  setSearch,
  term,
}) => {
  return (
    <div className="flex flex-col gap-2">
      {/* <div className="flex justify-center">
        <span className="px-3 py-1.5 rounded-2xl bg-dwred/60">
          This feature is under active development. Feedback &amp; comments
          appreciated.
        </span>
      </div> */}
      <input
        value={term}
        onChange={(e) => setSearch(e.target.value)}
        className="text-lg block w-full rounded-md border-dwlightblue/30 border shadow-sm focus:border-dwdarkblue focus:ring-dwdarkblue sm:text-sm py-2 px-2 bg-white z-50"
        placeholder="Search for nodes, functions, etc..."
      />
    </div>
  );
};

export type RowToDisplay = {
  node: NodeTemplate;
  key: string;
  dagTemplateId: number;
  projectVersionName: string;
  projectId: number;
  codeArtifact: CodeArtifact | undefined;
  // runInfo: {
  //   runId: number;
  //   duration: number | undefined;
  //   state: RunStatusType;
  // }[];
};

const extractTableData = (
  nodes: NodeTemplate[],
  codeArtifacts: CodeArtifact[],
  projectId: number
): RowToDisplay[] => {
  const codeArtifactsById = new Map<number, CodeArtifact>();
  codeArtifacts.forEach((ca) => {
    codeArtifactsById.set(ca.id as number, ca);
  });
  return nodes.map((node) => {
    return {
      node: node,
      key: node.name,
      dagTemplateId: node.dag_template as number,
      projectVersionName: "",
      projectId: projectId,
      codeArtifact: codeArtifactsById.get(node.code_artifacts?.[0]),
      // runInfo: [],
    };
  });
};

type QueryState = {
  searchTerm: string;
  selectedTags: Map<string, Set<string>>;
};
// TODO -- organize this with the one in RunSummary, there's some duplicated code
const useQueryState = () => {
  const [queryParams, setQueryParams] = useSearchParams();
  const searchTerm = queryParams.get("query") || "";
  const selectedTagsRaw = queryParams.get("tags");
  let selectedTags = new Map<string, Set<string>>();
  if (selectedTagsRaw !== null) {
    const parsed = JSON.parse(selectedTagsRaw);
    selectedTags = new Map(
      Object.entries(parsed).map(([key, value]) => [
        key,
        new Set(value as string[]),
      ])
    );
  }
  const setParams = (params: QueryState) => {
    const newParams = new URLSearchParams();
    if (params.searchTerm !== "") {
      newParams.set("query", params.searchTerm);
    }
    if (params.selectedTags.size > 0) {
      newParams.set(
        "tags",
        JSON.stringify(selectedTagsToObj(params.selectedTags))
      );
    }
    setQueryParams(newParams);
  };
  return [
    {
      searchTerm,
      selectedTags,
    },
    setParams,
  ] as const;
};

/**
 * Table with search bar for nodes in prior versions/runs
 * Note that this optionally comes with the ability to attach run data to it -- that will augment
 * it with runtime/links/etc...
 * @param props
 * @returns
 */
export const CatalogView: FC<{
  project: Project;
}> = (props) => {
  const projectId = props.project.id as number;
  const catalogData = useCatalogView({ projectId: projectId, limit: 10000 });

  const [{ searchTerm, selectedTags }, setQueryParams] = useQueryState();
  const [expandedRowsByKey, setExpandedRowsByKey] = useState<
    Map<string, "runtime-chart" | "table">
  >(new Map());
  const searchData = extractTableData(
    catalogData.data?.nodes || [],
    catalogData.data?.code_artifacts || [],
    props.project.id as number
  );
  const allTags = new Map<string, Set<string>>();
  searchData.forEach((row) => {
    Object.entries(row.node.tags || {}).forEach(([tag, value]) => {
      if (!allTags.has(tag)) {
        allTags.set(tag, new Set());
      }
      allTags.get(tag)?.add(value as string);
    });
  });
  const fuse = useMemo(
    () =>
      new Fuse(searchData, {
        keys: ["key"],
        threshold: 0.45,
      }),
    [searchData] // TODO -- determine how/if to invalidate this cache
  );
  if (
    catalogData.isLoading ||
    catalogData.isFetching ||
    catalogData.isUninitialized
  ) {
    return <Loading />;
  } else if (catalogData.isError) {
    return (
      <ErrorPage message={`Failed to load data for project=${projectId}`} />
    );
  }

  const cols = [
    {
      displayName: "Code",
      Render: (value: RowToDisplay) => {
        if (value.codeArtifact === undefined) {
          return <></>;
        }
        return (
          <FunctionDisplay
            projectId={value.projectId}
            projectVersionId={value.dagTemplateId}
            code={value.codeArtifact}
          />
        );
      },
    },
    {
      displayName: "Description",
      Render: (value: RowToDisplay) => {
        return (
          <DocumentationDisplay
            documentation={value.node.documentation as string}
          />
        );
      },
    },
    {
      displayName: "Tags",
      Render: (value: RowToDisplay) => {
        return <TagDisplay expanded={false} tags={value.node.tags as object} />;
      },
    },
    {
      displayName: "",
      Render: (value: RowToDisplay) => {
        const ChartIcon = AiOutlineBarChart;
        const TableIcon = AiOutlineTable;
        const setView = (view: "runtime-chart" | "table") => {
          const expandedValue = expandedRowsByKey.get(value.key);
          const newMap = new Map(expandedRowsByKey);
          if (expandedValue == undefined) {
            // If its not expanded, we should expand it
            newMap.set(value.key, view);
          } else if (expandedValue == view) {
            // If it is expanded, and it's the same view, we should collapse it
            newMap.delete(value.key);
          } else {
            // If it is expanded, and it's a different view, we should switch it
            newMap.set(value.key, view);
          }
          setExpandedRowsByKey(newMap);
        };
        return (
          <div className="flex flex-row items-center gap-2 cursor-pointer text-gray-400 text-2xl">
            <TableIcon
              title="View versions and run history"
              onClick={(e) => {
                e.stopPropagation();
                setView("table");
              }}
              className="hover:scale-125 cursor-pointer"
            />
            <ChartIcon
              title="View execution runtimes"
              onClick={(e) => {
                e.stopPropagation();
                setView("runtime-chart");
              }}
              className="hover:scale-125 cursor-pointer"
            />
          </div>
        );
      },
    },
  ];

  const shouldDisplay = (row: { item: RowToDisplay }) => {
    const node = row.item.node;
    let disp = true;
    disp &&= !Object.prototype.hasOwnProperty.call(
      node.tags,
      "hamilton.non_final_node"
    );
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const tags = node.tags as any;
    if (selectedTags.size > 0) {
      for (const [tag, values] of Array.from(selectedTags.entries())) {
        if (!values.has(tags[tag])) {
          disp = false;
          break;
        }
      }
    }
    return disp;
  };
  const getSearchResult = (term: string) => {
    if (searchTerm == "") {
      // This is a little messy cause it won't include all the search result fields necessarily...
      return searchData
        .map((data) => {
          return { item: data };
        })
        .sort((n1, n2) => {
          return n1.item.node.name.localeCompare(n2.item.node.name);
        });
    }
    return fuse.search(term);
  };

  const searchResults = getSearchResult(searchTerm).filter(shouldDisplay);
  return (
    <div className="px-4 sm:px-6 lg:px-8">
      <div className="sm:flex sm:items-center sticky top-0 bg-white z-50 px-5">
        <div className="w-full">
          <div className="pt-10 pb-10 flex flex-col gap-2">
            <FeatureSearchBox
              setSearch={(term) => {
                setQueryParams({ searchTerm: term, selectedTags });
              }}
              term={searchTerm}
            />
            <TagSelectorWithValues
              selectedTags={selectedTags}
              setSelectedTags={(tags) => {
                setQueryParams({ searchTerm, selectedTags: tags });
              }}
              allTags={allTags}
              placeholder="Filter by tags (select key/value pairs, multiple values is an OR query)"
            />
          </div>
        </div>
      </div>

      <GenericTable
        data={searchResults.map((result) => [
          result.item.node.name,
          result.item,
        ])}
        columns={cols}
        dataTypeName={""}
        dataTypeDisplay={FeatureNameDisplay}
        extraRowData={{
          Render: (props: { value: RowToDisplay }) => {
            return (
              <NodeRunsView
                value={props.value}
                view={expandedRowsByKey.get(props.value.key)}
              />
            );
          },
          shouldRender: (row) => {
            return expandedRowsByKey.has(row.key);
          },
        }}
      />
    </div>
  );
};
