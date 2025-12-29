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

import JsonView from "@uiw/react-json-view";
import {
  AttributeDict1,
  AttributeDict2,
} from "../../../../../state/api/friendlyApi";
import { GenericTable } from "../../../../common/GenericTable";

export const Dict1View = (props: {
  taskName: string;
  runIds: number[];
  values: AttributeDict1[];
}) => {
  return (
    <GenericTable
      data={props.runIds.map((runId, i) => {
        return [runId.toString(), props.values[i]];
      })}
      columns={[
        {
          displayName: "data",
          Render: (value) => {
            return <JsonView value={value} collapsed={2} />;
          },
        },
      ]}
      dataTypeName={"run"}
    ></GenericTable>
  );
};

export const Dict2View = (props: {
  taskName: string;
  runIds: number[];
  values: AttributeDict2[];
}) => {
  return (
    <GenericTable
      data={props.runIds.map((runId, i) => {
        return [runId.toString(), props.values[i].value];
      })}
      columns={[
        {
          displayName: "data",
          Render: (value) => {
            return <JsonView value={value} collapsed={2} />;
          },
        },
      ]}
      dataTypeName={"run"}
    ></GenericTable>
  );
};
