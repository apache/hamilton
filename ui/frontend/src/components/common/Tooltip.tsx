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

import { ReactNode } from "react";

export const ToolTip: React.FC<{ children: ReactNode; tooltip?: string }> = (
  props
) => {
  return (
    <div className="group relative inline-block">
      {props.children}
      {/* This is a hack -- the overflow is hidden for the parent container, so we need to
         position it on the right of the icon.
         We'll need to redo it, just don't have the time now and this works... */}
      <span
        className="invisible group-hover:visible opacity-0 group-hover:opacity-100 transition
             bg-dwred text-white p-1 rounded absolute top-full -mt-5 mx-0 whitespace-nowrap z-50"
      >
        {props.tooltip}
      </span>
    </div>
  );
};
