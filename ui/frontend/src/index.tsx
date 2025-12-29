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

import ReactDOM from "react-dom/client";
import "./index.css";
import { App } from "./App";
import reportWebVitals from "./reportWebVitals";
import { persistor, store } from "./state/store";
// import {store} from "./state/store"
import { Provider } from "react-redux";
// This is a weird bug: https://github.com/rt2zz/redux-persist/issues/1166
// eslint-disable-next-line @typescript-eslint/no-unused-vars
import { PersistGate } from "redux-persist/integration/react";
import { RequiredAuthProvider, RedirectToLogin } from "@propelauth/react";
import { Loading } from "./components/common/Loading";
import { PostHogProvider } from "posthog-js/react";
import TimeAgo from "javascript-time-ago";
import en from "javascript-time-ago/locale/en.json";
import { LocalLoginProvider } from "./auth/Login";

const posthogOptions = {
  api_host: process.env.REACT_APP_PUBLIC_POSTHOG_HOST,
};

const root = ReactDOM.createRoot(
  document.getElementById("root") as HTMLElement
);

const NoopTelemetryProvider = ({ children }: { children: React.ReactNode }) => {
  return <>{children}</>;
};

TimeAgo.addDefaultLocale(en);

const AuthProvider =
  process.env.REACT_APP_AUTH_MODE === "local"
    ? LocalLoginProvider
    : RequiredAuthProvider;

const TelemetryProvider =
  process.env.REACT_APP_USE_POSTHOG === "true"
    ? PostHogProvider
    : NoopTelemetryProvider;

root.render(
  // <React.StrictMode>
  <Provider store={store}>
    <PersistGate loading={<Loading />} persistor={persistor}>
      <AuthProvider
        authUrl={process.env.REACT_APP_AUTH_URL as string}
        displayWhileLoading={<Loading />}
        displayIfLoggedOut={<RedirectToLogin />}
      >
        <TelemetryProvider
          apiKey={process.env.REACT_APP_PUBLIC_POSTHOG_KEY}
          options={posthogOptions}
        >
          <App />
        </TelemetryProvider>
      </AuthProvider>
    </PersistGate>
  </Provider>
  // </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
