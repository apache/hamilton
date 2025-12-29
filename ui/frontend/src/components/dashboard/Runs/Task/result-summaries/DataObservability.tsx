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

import { useState } from "react";
import {
  AttributeDagworksDescribe3,
  AttributeDict1,
  AttributeDict2,
  AttributeHTML1,
  AttributePandasDescribe1,
  AttributePrimitive1,
  AttributeSchema1,
  AttributeUnsupported1,
} from "../../../../../state/api/backendApiRaw";
import {
  NodeRunAttribute,
  NodeRunWithAttributes,
  getNodeRunAttributes,
} from "../../../../../state/api/friendlyApi";
import { parsePythonType } from "../../../../../utils";
import {
  GenericGroupedTable,
  GenericTable,
} from "../../../../common/GenericTable";
import { RunLink } from "../../../../common/CommonLinks";
import { PandasDescribe1View } from "./PandasDescribe";
import { Dict1View, Dict2View } from "./DictView";
import { DAGWorksDescribe3View } from "./DAGWorksDescribe";
import { HTML1View } from "./HTMLView";
import { Schema1View } from "./SchemaView";
import { HiChevronDown, HiChevronUp } from "react-icons/hi";
import ReactDiffViewer from "react-diff-viewer-continued";
import { Field, Label, Switch } from "@headlessui/react";

const DiffView = (props: { oldValue: string; newValue: string }) => {
  const [splitView, setSplitView] = useState(false);
  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-row gap-1">
        <Field className="flex items-center">
          <Switch
            checked={splitView}
            onChange={setSplitView}
            onClick={(e) => {
              setSplitView(!splitView);
              e.stopPropagation();
            }}
            className="group relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent bg-gray-200 transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-dwdarkblue focus:ring-offset-2 data-[checked]:bg-dwdarkblue"
          >
            <span
              aria-hidden="true"
              className="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out group-data-[checked]:translate-x-5"
            />
          </Switch>
          <Label as="span" className="ml-3 text-sm">
            <span className="font-medium text-gray-500">Split view</span>{" "}
          </Label>
        </Field>
      </div>
      <ReactDiffViewer
        oldValue={props.oldValue}
        newValue={props.newValue}
        splitView={splitView}
        linesOffset={3}
        extraLinesSurroundingDiff={1}
        showDiffOnly={false}
        hideLineNumbers
        disableWordDiff
        styles={{
          diffContainer: {
            backgroundColor: "transparent",
          },
        }}
      />
    </div>
  );
};
const Primitive1View = (props: {
  taskName: string;
  runIds: number[];
  values: AttributePrimitive1[];
  projectId: number;
}) => {
  const valuesWithRunID = props.values.map((item, i) => {
    return { ...item, runId: props.runIds[i] };
  });
  return (
    <div className="m-8">
      <GenericGroupedTable
        data={valuesWithRunID.map((item) => {
          return ["", item];
        })}
        columns={[
          {
            displayName: "type",
            Render: (
              items: AttributePrimitive1[],
              isSummaryRow: boolean,
              isExpanded: boolean
            ) => {
              const uniqueTypes = Array.from(
                new Set(
                  items.map((item) => parsePythonType({ type_name: item.type }))
                )
              );
              return isSummaryRow && isExpanded ? (
                <></>
              ) : (
                <div className="flex flex-col">
                  {uniqueTypes.map((type, i) => {
                    return (
                      <div key={i}>
                        <code className="text-sm">{type}</code>
                      </div>
                    );
                  })}
                </div>
              );
            },
          },
          {
            displayName: "value",
            Render: (
              items: AttributePrimitive1[],
              isSummaryRow: boolean,
              isExpanded: boolean
            ) => {
              const [expanded, setExpanded] = useState(false);
              return (
                <div className="flex flex-col w-192">
                  {isSummaryRow && isExpanded ? (
                    <></>
                  ) : isSummaryRow && !isExpanded ? (
                    <DiffView
                      oldValue={items[0].value.toString()}
                      newValue={items[1].value.toString()}
                    />
                  ) : (
                    <pre
                      onClick={(e) => {
                        setExpanded(!expanded);
                        e.stopPropagation();
                      }}
                      className={`w- ${
                        expanded ? "break-word whitespace-pre-wrap" : "truncate"
                      }  text-gray-500 cursor-cell`}
                    >
                      {items[0].value.toString()}
                    </pre>
                  )}
                </div>
              );
            },
          },
          {
            displayName: "runs",
            Render: (
              value: AttributePrimitive1[],
              isSummaryRow: boolean,
              isExpanded: boolean
            ) => {
              if (isSummaryRow && isExpanded) {
                return <></>;
              }
              return (
                <div className="flex flex-row gap-1">
                  {props.runIds.map((taskRun, i) => (
                    <RunLink
                      runId={props.runIds[i]}
                      key={i}
                      projectId={1}
                      highlightedRun={null}
                      setHighlightedRun={() => void 0}
                    />
                  ))}
                </div>
              );
            },
          },
        ]}
        dataTypeName={"Run"}
      />
    </div>
  );
};

const Unsupported1View = (props: {
  taskName: string;
  runIds: number[];
  values: AttributeUnsupported1[];
}) => {
  return (
    <div className="flex flex-col m-20">
      <span className="text-lg text-gray-800">
        We currently do not capture data summaries for run(s){" "}
        <code>[{props.runIds.join(", ")}]</code>
        for <code>{props.taskName}</code>. We are working on adding support for
        everything -- reach out if you need it and we can prioritize!
      </span>
      <div className="m-8">
        <GenericTable
          data={props.values.map((item, i) => {
            return [props.runIds[i].toString() || "", item];
          })}
          columns={[
            {
              displayName: "type",
              Render: (item: AttributeUnsupported1) => {
                return (
                  <div className="flex flex-col">
                    <code className="text-sm">{item.unsupported_type}</code>
                  </div>
                );
              },
            },
            {
              displayName: "action",
              Render: (item: AttributeUnsupported1) => {
                return (
                  <div className="flex flex-col">
                    <span className="text-sm">{item.action}</span>
                  </div>
                );
              },
            },
          ]}
          dataTypeName={""}
        />
      </div>
    </div>
  );
};

export const snakeToTitle = (s: string) => {
  return s
    .split("_")
    .map((i, n) => (n === 0 ? i[0].toUpperCase() : i[0]) + i.slice(1))
    .join(" ");
};

export const MultiResultSummaryView = (props: {
  nodeRunData: (NodeRunWithAttributes | null)[];
  taskName: string | undefined;
  projectId: number;
  runIds: number[];
}) => {
  const [minimizedAttributes, setMinimizedAttributes] = useState<string[]>([]);
  const toggleExpanded = (attributeName: string) => {
    if (minimizedAttributes.includes(attributeName)) {
      setMinimizedAttributes(
        minimizedAttributes.filter((i) => i !== attributeName)
      );
    } else {
      setMinimizedAttributes([...minimizedAttributes, attributeName]);
    }
  };
  const attributes = props.nodeRunData.flatMap((i) => i?.attributes || []);
  const attributesGroupedByName = attributes.reduce((acc, item) => {
    if (acc[item.name]) {
      acc[item.name].push(item);
    } else {
      acc[item.name] = [item];
    }
    return acc;
  }, {} as { [key: string]: NodeRunAttribute[] });
  return (
    <div className="flex flex-col gap-2">
      {Object.entries(attributesGroupedByName).map(([key, value]) => {
        const isExpanded = !minimizedAttributes.includes(key);
        const Icon = isExpanded ? HiChevronUp : HiChevronDown;
        return (
          <div key={key}>
            <div className="flex flex-row gap-2">
              <h2 className="text-lg font-semibold text-gray-800">
                {snakeToTitle(key)}
              </h2>
              <Icon
                className="hover:scale-125 hover:cursor-pointer text-2xl text-gray-400 mr-1"
                onClick={() => {
                  toggleExpanded(key);
                }}
              />
            </div>
            {isExpanded && (
              <ResultsSummaryView
                runAttributes={value}
                taskName={props.taskName}
                projectId={props.projectId}
                runIds={props.runIds}
              />
            )}
          </div>
        );
      })}
    </div>
  );
};
export const ResultsSummaryView = (props: {
  // nodeRunData: (NodeRunWithAttributes | null)[];
  runAttributes: NodeRunAttribute[];
  taskName: string | undefined;
  projectId: number;
  runIds: number[];
}) => {
  const allViews = [];
  /**
   * We have to do this all manually (I think) due to type erasure -- not known at runtime
   * so we can't really do it in a for loop. I'm sure there's a way to but generating this
   * is quick enough.
   *
   * Thanks to chatGPT I could check my email while this code was getting written.
   *
   */

  const primitive1Views = getNodeRunAttributes<AttributePrimitive1>(
    props.runAttributes,
    props.runIds,
    "AttributePrimitive1"
  );
  if (primitive1Views.length > 0) {
    allViews.push(
      <Primitive1View
        taskName={props.taskName || ""}
        runIds={primitive1Views.map((i) => i.runId)}
        values={primitive1Views.map((i) => i.value)}
        projectId={props.projectId}
      />
    );
  }

  // ... [similar blocks for other attributes]

  // const error1Views = getNodeRunAttributes<AttributeError1>(
  //   props.runAttributes
  //   "AttributeError1"
  // );
  // if (error1Views.length > 0) {
  //   allViews.push(
  //     <Error1View
  //       taskName={props.taskName || ""}
  //       runIds={error1Views.map((i) => i.runId)}
  //       values={error1Views.map((i) => i.value)}
  //     />
  //   );
  // }

  const dict1Views = getNodeRunAttributes<AttributeDict1>(
    props.runAttributes,
    props.runIds,
    "AttributeDict1"
  );

  if (dict1Views.length > 0) {
    allViews.push(
      <Dict1View
        taskName={props.taskName || ""}
        runIds={dict1Views.map((i) => i.runId)}
        values={dict1Views.map((i) => i.value)}
      />
    );
  }

  const dict2Views = getNodeRunAttributes<AttributeDict2>(
    props.runAttributes,
    props.runIds,
    "AttributeDict2"
  );
  if (dict2Views.length > 0) {
    allViews.push(
      <Dict2View
        taskName={props.taskName || ""}
        runIds={dict2Views.map((i) => i.runId)}
        values={dict2Views.map((i) => i.value)}
      />
    );
  }

  const html1Views = getNodeRunAttributes<AttributeHTML1>(
    props.runAttributes,
    props.runIds,
    "AttributeHTML1"
  );
  if (html1Views.length > 0) {
    allViews.push(
      <HTML1View
        taskName={props.taskName || ""}
        runIds={html1Views.map((i) => i.runId)}
        values={html1Views.map((i) => i.value)}
      />
    );
  }

  const dagworksDescribe3Views =
    getNodeRunAttributes<AttributeDagworksDescribe3>(
      props.runAttributes,
      props.runIds,
      "AttributeDagworksDescribe3"
    );
  if (dagworksDescribe3Views.length > 0) {
    allViews.push(
      <DAGWorksDescribe3View
        taskName={props.taskName || ""}
        runIds={dagworksDescribe3Views.map((i) => i.runId)}
        values={dagworksDescribe3Views.map((i) => i.value)}
        projectId={props.projectId}
      />
    );
  }

  const pandasDescribe1View = getNodeRunAttributes<AttributePandasDescribe1>(
    props.runAttributes,
    props.runIds,
    "AttributePandasDescribe1"
  );

  if (pandasDescribe1View.length > 0) {
    allViews.push(
      <PandasDescribe1View
        taskName={props.taskName || ""}
        runIds={pandasDescribe1View.map((i) => i.runId)}
        values={pandasDescribe1View.map((i) => i.value)}
        projectId={props.projectId}
      />
    );
  }

  const schema1View = getNodeRunAttributes<AttributeSchema1>(
    props.runAttributes,
    props.runIds,
    "AttributeSchema1"
  );

  if (schema1View.length > 0) {
    allViews.push(
      <Schema1View
        attributeSchemas={schema1View.map((i) => i.value)}
        runIds={schema1View.map((i) => i.runId)}
        projectId={props.projectId}
      />
    );
  }

  const unsupportedViews = getNodeRunAttributes<AttributeUnsupported1>(
    props.runAttributes,
    props.runIds,
    "AttributeUnsupported1"
  );

  if (unsupportedViews.length > 0) {
    allViews.push(
      <Unsupported1View
        taskName={props.taskName || ""}
        runIds={unsupportedViews.map((i) => i.runId)}
        values={unsupportedViews.map((i) => i.value)}
      />
    );
  }

  return (
    <div className="flex flex-col border-l-8 my-2 border-gray-100 hover:bg-gray-100">
      {allViews.map((item, i) => {
        return <div key={i}>{item}</div>;
      })}
    </div>
  );
};
