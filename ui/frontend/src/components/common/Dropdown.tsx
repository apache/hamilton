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

import { Listbox, Transition } from "@headlessui/react";
import { CheckIcon, ChevronUpDownIcon } from "@heroicons/react/20/solid";
import React, { Fragment } from "react";
import { IconType } from "react-icons/lib";
import { classNames } from "../../utils";
import { HelpTooltip } from "./HelpTooltip";

type Selectable = {
  name: string;
  // eslint-disable-next-line
  value: any;
  icon?: IconType;
};

export const DropdownSelector: React.FC<{
  choices: Selectable[];
  setCurrentChoice: (choice: Selectable) => void;
  currentChoice: Selectable | null;
  title: string;
  description?: string;
}> = (props) => {
  return (
    <Listbox value={props.currentChoice} onChange={props.setCurrentChoice}>
      {({ open }) => (
        <>
          <Listbox.Label className="text-sm font-medium text-gray-700 flex flex-row items-center gap-2">
            {props.title}{" "}
            {props.description && (
              <span>
                <HelpTooltip description={props.description} />
              </span>
            )}
          </Listbox.Label>
          <div className="relative mt-1">
            <Listbox.Button className="relative w-full cursor-default rounded-md border border-gray-300 bg-white py-2 pl-3 pr-10 text-left shadow-sm focus:border-dwdarkblue focus:outline-none focus:ring-1 focus:ring-dwdarkblue sm:text-sm">
              {/* Hack to make the padding look good */}
              <span
                className={`block truncate ${
                  props.currentChoice?.name ? "" : "opacity-0"
                }`}
              >
                {props.currentChoice?.name ? props.currentChoice.name : "..."}
              </span>
              <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                <ChevronUpDownIcon
                  className="h-5 w-5 text-gray-400"
                  aria-hidden="true"
                />
              </span>
            </Listbox.Button>

            <Transition
              show={open}
              as={Fragment}
              leave="transition ease-in duration-100"
              leaveFrom="opacity-100"
              leaveTo="opacity-0"
            >
              <Listbox.Options className="absolute z-10 max-h-60 w-full overflow-auto rounded-md bg-white py-1 text-base shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm">
                {props.choices.map((config, index) => (
                  <Listbox.Option
                    key={index}
                    className={({ active }) =>
                      classNames(
                        active ? "text-white bg-dwlightblue" : "text-gray-900",
                        "relative cursor-default select-none py-2 pl-3 pr-9"
                      )
                    }
                    value={config}
                  >
                    {({ selected, active }) => (
                      <>
                        <span
                          className={classNames(
                            selected ? "font-semibold" : "font-normal",
                            "block truncate"
                          )}
                        >
                          {config.name}
                        </span>

                        {selected ? (
                          <span
                            className={classNames(
                              active ? "text-white" : "text-dwlightblue",
                              "absolute inset-y-0 right-0 flex items-center pr-4"
                            )}
                          >
                            <CheckIcon className="h-5 w-5" aria-hidden="true" />
                          </span>
                        ) : null}
                      </>
                    )}
                  </Listbox.Option>
                ))}
              </Listbox.Options>
            </Transition>
          </div>
        </>
      )}
    </Listbox>
  );
};
