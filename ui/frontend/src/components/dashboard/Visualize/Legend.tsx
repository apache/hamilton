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

export const Legend = () => {
  const legendItems = [
    { text: "Current", bgClass: "bg-green-500 text-white" },
    { text: "Upstream", bgClass: "bg-dwred text-white" },
    { text: "Downstream", bgClass: "bg-dwlightblue text-white" },
    { text: "Default", bgClass: "bg-dwdarkblue text-white" },
    { text: "Unrelated", bgClass: "bg-gray-400 text-white" },
    {
      text: "Input",
      bgClass: "bg-white text-dwdarkblue border-2 border-dwdarkblue",
    },
  ];

  return (
    <div className="flex flex-row gap-2">
      {legendItems.map((item, index) => (
        <div
          key={index}
          className={`px-3 py-1 shadow-sm flex flex-row items-center align-middle justify-center rounded-lg w-max text-sm ${item.bgClass}`}
        >
          {item.text}
        </div>
      ))}
    </div>
  );
};
