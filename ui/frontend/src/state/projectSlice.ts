// Licensed to the Apache Software Foundation (ASF) under one
// or more contributor license agreements.  See the NOTICE file
// distributed with this work for additional information
// regarding copyright ownership.  The ASF licenses this file
// to you under the Apache License, Version 2.0 (the
// "License"); you may not use this file except in compliance
// with the License.  You may obtain a copy of the License at
//
//   http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing,
// software distributed under the License is distributed on an
// "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
// KIND, either express or implied.  See the License for the
// specific language governing permissions and limitations
// under the License.

import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { RootState } from "./store";

/**
 * Basic project state -- we store a
 * project that has enough information to
 * query for git code/whatnot
 * TBD
 */
interface ProjectState {
  currentProjectID: number | undefined;
  hasSelectedProject: boolean;
}

const initialState: ProjectState = {
  currentProjectID: undefined, // Nothing to start
  hasSelectedProject: false,
};

export const projectSlice = createSlice({
  initialState,
  name: "project",
  reducers: {
    setProjectID: (state: ProjectState, action: PayloadAction<number>) => {
      state.currentProjectID = action.payload;
      state.hasSelectedProject = true;
    },
    unsetProjectID: (state: ProjectState) => {
      state.currentProjectID = undefined;
      state.hasSelectedProject = false;
    },
  },
});

export default projectSlice.reducer;

export const { setProjectID } = projectSlice.actions;

export const selectProjectID = (state: RootState) =>
  state.project.currentProjectID;

export const selectUserHasChosenProject = (state: RootState): boolean =>
  state.project.hasSelectedProject;
