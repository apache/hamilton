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

import ReactSelect from "react-select";

export const TagSelectorWithValues = (props: {
  setSelectedTags: (tags: Map<string, Set<string>>) => void;
  allTags: Map<string, Set<string>>; // Map of tag to potential values
  selectedTags: Map<string, Set<string>>;
  placeholder?: string;
}) => {
  // TODO -- get typing correct here
  const selectOptions = Array.from(props.allTags)
    // This is confusing -- we actually shouldn't have to filter out the already selected ones
    // But there seems to be a bug with the ID/uniquifying it so we're doing it manually for now
    // TODO -- figure out why we end up doing this
    .flatMap(([tag, value]) => {
      return Array.from(value)
        .sort()
        .map((v) => {
          if (
            props.selectedTags.has(tag) &&
            props.selectedTags.get(tag)?.has(v)
          ) {
            return null;
          }
          return {
            value: [tag, v],
            label: `${tag}=${v}`,
            id: `${tag}${v}`,
          };
        });
    })
    .filter((item) => item !== null) as {
    value: [string, string];
    label: string;
    id: string;
  }[];

  return (
    <div className="flex-1"
    >
      <ReactSelect
        onChange={(selected) => {
          const selectedTags = new Map<string, Set<string>>();
          selected.forEach(({ value }) => {
            const [tag, v] = value;
            if (!selectedTags.has(tag)) {
              selectedTags.set(tag, new Set());
            }
            selectedTags.get(tag)?.add(v);
          });
          props.setSelectedTags(selectedTags);
        }}
        options={selectOptions}
        isMulti
        className="text-lg sm:text-sm"
        placeholder={
          props.placeholder !== undefined
            ? props.placeholder
            : "Select tags to view..."
        }
        value={Array.from(props.selectedTags).flatMap(([tag, values]) => {
          return Array.from(values).map((value) => {
            return { value: [tag, value], label: `${tag}=${value}` };
          });
        })}
      />
    </div>
  );
};

export const selectedTagsToObj = (map: Map<string, Set<string>>): object => {
  const obj = Object.fromEntries(
    Array.from(map).map(([key, value]) => [key, Array.from(value)])
  );
  return obj;
};

export const objToSelectedTags = (obj: object): Map<string, Set<string>> => {
  return new Map(
    Object.entries(obj).map(([key, value]) => [key, new Set(value as string[])])
  );
};
