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

import { useLocation } from "react-router-dom";

interface LocationState {
  feature: string;
}
const notImplementedFeatures = new Map(
  Object.entries({
    signin_with_google: {
      title: "Signing in with google",
      state:
        "We are actively working on building out our authentication system.",
    },
    signup: {
      title: "Signing up",
      state:
        "We are actively working on building out our authentication system.",
    },
    signin_with_github: {
      title: "Signing in with github",
      state:
        "We are actively working on building out our authentication system.",
    },
  })
);

export const NotImplemented = () => {
  /**
   * Simple page for "Not implemented features"
   * We shouldn't have too many but its kind of nice to have a
   * placeholder for publishing, especially early on.
   * E.G. bells and whistles should probably make it to a
   * github ticket, whereas needed features will make it here
   * (and also to a github ticket)
   */
  const { feature } = useLocation().state as LocationState;
  const featureInfo = notImplementedFeatures.get(feature);
  if (featureInfo === undefined) {
    return <div>Feature {feature} has not yet been implemented.</div>;
  }
  return (
    <div>
      <h1>{featureInfo.title} has not yet been implemented.</h1>
      <p>{featureInfo.state}</p>
    </div>
  );
};
