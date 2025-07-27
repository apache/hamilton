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

import { CodeArtifact, DAGTemplateWithData } from "../state/api/friendlyApi";

/**
 * Simple function to extract contents from code.
 * We have a list of files that we slurp up (these
 * are given to us currently on the server side, but in
 * the future we may need to fetch them directly from the blob store.
 * @param codeArtifact
 * @param projectVersion
 * @returns
 */
export const extractCodeContents = (
  codeArtifact: CodeArtifact,
  dagTemplate: DAGTemplateWithData | undefined
): string | undefined => {
  const { start, end, path } = codeArtifact;
  if (dagTemplate === undefined) {
    return undefined;
  }
  const availableFiles =
    dagTemplate.code?.files.filter((file) => file.path === path) || [];
  if (availableFiles.length === 0) {
    return undefined;
  }
  const fileContents = availableFiles[0].contents;
  const lines = fileContents.split("\n");
  if (end > lines.length) {
    return undefined;
  }
  return lines.slice(start, end).join("\n");
};

/**
 * This is inefficient, but its easy.
 * TODO -- make this do one pass, should be simple.
 * @param codeArtifacts
 * @param projectVersion
 * @returns
 */
export const extractAllCodeContents = (
  codeArtifacts: CodeArtifact[],
  projectVersion: DAGTemplateWithData | undefined
): (string | undefined)[] => {
  return codeArtifacts.map((codeArtifact) => {
    return extractCodeContents(codeArtifact, projectVersion);
  });
};
