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

import { configureStore, ThunkAction, Action } from "@reduxjs/toolkit";
import {
  persistStore,
  persistReducer,
  FLUSH,
  REHYDRATE,
  PAUSE,
  PERSIST,
  PURGE,
  REGISTER,
} from "redux-persist";

import storage from "redux-persist/lib/storage";
import { backendApi } from "./api/backendApiRaw";
import { projectSlice } from "./projectSlice";
import { authSlice } from "./authSlice";

const persistConfig = {
  key: "root",
  storage,
};

/**
 * TODO -- determine what to persist and what not to persist
 * We also need caching invalidation here -- E.G. what happens
 * when a user logs out?
 */
const reducer = {
  backendApi: backendApi.reducer,
  auth: authSlice.reducer,
  project: persistReducer(persistConfig, projectSlice.reducer),
  // version: persistReducer(persistConfig, projectVersionSlice.reducer),
};
export const store = configureStore({
  devTools: process.env.NODE_ENV === "development",
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: [FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER],
        ignoreActions: true, // TODO -- don't ignore these
        ignoreState: true, // Instead, we should just be storing the state we need...
      },
    }).concat(backendApi.middleware),
  reducer: reducer,
});

export const persistor = persistStore(store);

export type AppDispatch = typeof store.dispatch;
export type RootState = ReturnType<typeof store.getState>;
export type AppThunk<ReturnType = void> = ThunkAction<
  ReturnType,
  RootState,
  unknown,
  Action<string>
>;
