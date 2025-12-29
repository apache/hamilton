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

export const DashboardItem = (props: {
  children: React.ReactNode;
  extraWide?: boolean;
}) => {
  return (
    <div className="flex flex-col bg-white rounded-md shadow-md m-3 max-w-full overflow-x-auto flex-grow">
      {props.children}
    </div>
  );
};
export const MetricDisplay = (props: {
  number: number;
  label: string | JSX.Element;
  textColorClass: string;
  isSubset: boolean;
  numberFormatter?: (num: number) => string;
}) => {
  const numberDisplay = props.numberFormatter
    ? props.numberFormatter(props.number)
    : props.number;
  return (
    <div className={`flex flex-col items-center p-3 max-w-xl`}>
      <div className={`text-5xl font-semibold ${props.textColorClass}`}>
        {`${numberDisplay}${props.isSubset ? "+" : ""}`}
      </div>
      <div className={`${props.textColorClass} font-light`}>{props.label}</div>
    </div>
  );
};
