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

import { AttributeSchema1 } from "../../../../../state/api/friendlyApi";
import { GenericGroupedTable } from "../../../../common/GenericTable";
import { ColSchema } from "../../../../../state/api/backendApiRaw";
import JsonView from "@uiw/react-json-view";
import { RunLink } from "../../../../common/CommonLinks";

interface Schema1ViewProps {
  attributeSchemas: AttributeSchema1[];
  runIds: number[];
  projectId: number;
}

type AttributeColumn = ColSchema & {
  runId: number;
  projectId: number;
};

export const Schema1View: React.FC<Schema1ViewProps> = ({
  attributeSchemas,
  runIds,
  projectId,
}) => {
  const attributeColumns: AttributeColumn[] = [];

  attributeSchemas.forEach((schema, i) => {
    const runId = runIds[i];
    Object.keys(schema).forEach((key) => {
      attributeColumns.push({
        runId: runId,
        projectId: projectId,
        ...schema[key],
      });
    });
  });

  const columns = [
    {
      displayName: "runs",
      Render: (
        value: { runId: number }[],
        isSummaryRow: boolean,
        isExpanded: boolean
      ) => {
        const runIds = value.map((item) => item.runId);
        if (isSummaryRow && isExpanded) {
          return <></>;
        }
        return (
          <div className="flex flex-row gap-1">
            {runIds.map((taskRun, i) => (
              <RunLink
                runId={runIds[i]}
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

    {
      displayName: "type",
      Render: (
        value: AttributeColumn[],
        isSummaryRow: boolean,
        isExpanded: boolean
      ) => {
        const toDisplay = Array.from(new Set(value.map((item) => item.type)));
        console.log(value);
        return !isSummaryRow || !isExpanded ? (
          <div className="flex flex-wrap gap-2">
            {toDisplay.map((item, i) => (
              <code key={i}>{item}</code>
            ))}
          </div>
        ) : (
          <></>
        );
      },
    },
    {
      displayName: "nullable",
      Render: (
        value: AttributeColumn[],
        isSummaryRow: boolean,
        isExpanded: boolean
      ) => {
        console.log(value);
        const allExpanded = value.map((item) => item.nullable);
        console.log(allExpanded);

        return !isSummaryRow || !isExpanded ? (
          <div className="flex flex-wrap gap-2">
            {allExpanded.map((item) => (item ? "✓" : "✗"))}
          </div>
        ) : (
          <></>
        );
      },
    },
    {
      displayName: "metadata",
      Render: (
        value: AttributeColumn[],
        isSummaryRow: boolean,
        isExpanded: boolean
      ) => {
        const toDisplay = Array.from(
          new Set(value.map((item) => item.metadata))
        );
        console.log(value);
        return !isSummaryRow || !isExpanded ? (
          <div className="flex flex-wrap gap-2">
            {toDisplay.map((item, i) => (
              <JsonView
                key={i}
                value={item}
                collapsed={2}
                enableClipboard={false}
              />
            ))}
          </div>
        ) : (
          <></>
        );
      },
    },
  ];
  return (
    <div className="py-10">
      <GenericGroupedTable
        dataTypeName="column"
        data={attributeColumns.map((col) => [col.name, col])}
        // description="Numeric columns in the dataset"
        columns={columns}
      />
    </div>
  );
};
