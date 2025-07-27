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
import { useAuthInfo } from "@propelauth/react";

export type AuthData = ReturnType<typeof useAuthInfo>;

export type AuthState = {
  authData: AuthData | null;
  localUserName: string | null;
  localAPIKey: string | null;
};

const initialState = {
  authData: null,
  localUserName: null,
  localAPIKey: null,
} as AuthState;

/**
 * Store basic auth information from propelauth
 */
export const authSlice = createSlice({
  initialState,
  name: "auth",
  reducers: {
    setAuth: (state: AuthState, action: PayloadAction<AuthData>) => {
      state.authData = action.payload;
    },
    logout: (state: AuthState) => {
      state.authData = null;
    },
    setLocalUserName: (state: AuthState, action: PayloadAction<string>) => {
      state.localUserName = action.payload;
    },
    setLocalAPIKey: (state: AuthState, action: PayloadAction<string>) => {
      state.localAPIKey = action.payload;
    }
  },
});

export default authSlice.reducer;

export const { logout, setAuth, setLocalUserName, setLocalAPIKey } = authSlice.actions;
export const useAuthData = (state: RootState) => state.auth.authData;
