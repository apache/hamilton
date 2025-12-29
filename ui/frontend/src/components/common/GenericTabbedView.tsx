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

import { classNames } from "../../utils";
import { HiChevronDown, HiChevronUp } from "react-icons/hi";

export const Tabs = (props: {
  allTabs: { name: string; displayName: string }[];
  setCurrentTab: (tab: string) => void;
  currentTab: string;
  isMinimized: boolean;
  setIsMinimized: (minimized: boolean) => void | null;
  additionalElement?: JSX.Element;
}) => {
  const Icon = props.isMinimized ? HiChevronDown : HiChevronUp;
  return (
    <div>
      <div>
        <div className="sm:hidden">
          <label htmlFor="tabs" className="sr-only">
            Select a tab
          </label>
          {/* Use an "onChange" listener to redirect the user to the selected tab URL. */}
          <select
            id="tabs"
            name="tabs"
            className="block w-full rounded-md border-gray-300 py-2 pl-3 pr-10 text-base focus:border-dwdarkblue focus:outline-none focus:ring-dwdarkblue sm:text-sm"
            defaultValue={props.currentTab}
          >
            {props.allTabs.map((tab) => (
              <option key={tab.name}>{tab.displayName}</option>
            ))}
          </select>
        </div>
        <div className="hidden sm:block">
          <div className="border-b border-gray-200">
            <div className="flex flex-row justify-start">
              {props.setIsMinimized && (
                <div className="pt-4 pl-3 pr-5 text-2xl text-gray-500">
                  <Icon
                    className="hover:scale-125 hover:cursor-pointer"
                    onClick={() => props.setIsMinimized(!props.isMinimized)}
                  />
                </div>
              )}
              <nav className="-mb-px flex space-x-8" aria-label="Tabs">
                {props.allTabs.map((tab) => (
                  <div
                    onClick={() => {
                      props.setCurrentTab(tab.name);
                      props.setIsMinimized(false);
                    }}
                    key={tab.name}
                    className={classNames(
                      tab.name === props.currentTab
                        ? "border-dwdarkblue text-dwdarkblue"
                        : "border-transparent text-gray-400 hover:border-gray-300 hover:text-gray-700",
                      "whitespace-nowrap border-b-2 py-4 px-1 text-sm font-medium cursor-pointer"
                    )}
                    aria-current={
                      tab.name === props.currentTab ? "page" : undefined
                    }
                  >
                    {tab.displayName}
                  </div>
                ))}
              </nav>
              {props.additionalElement ? (
                <div className="py-4 px-1 text-sm font-medium cursor-pointer">
                  {props.additionalElement}
                </div>
              ) : (
                <></>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
