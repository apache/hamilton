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

import { XMarkIcon } from "@heroicons/react/20/solid";

export const DeleteButton = (props: {
  deleteMe: () => void;
  deleteType: string;
  canDelete: boolean;
}) => {
  if (!props.canDelete) return <></>;
  return (
    <button
      onClick={() => props.deleteMe()}
      type="button"
      className="inline-flex items-center gap-x-1.5 rounded-md
              bg-dwred py-2 px-3 text-sm font-semibold text-white shadow-sm
              hover:bg-dwred/80 focus-visible:outline focus-visible:outline-2
              focus-visible:outline-offset-2 focus-visible:outline-dwred"
    >
      <XMarkIcon className="-ml-0.5 h-5 w-5" aria-hidden="true" />
      {props.deleteType}
    </button>
  );
};
