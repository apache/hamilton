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

const { build } = require("esbuild");

const baseConfig = {
    bundle: true,
    minify: process.env.NODE_ENV === "production",
    sourcemap: process.env.NODE_ENV !== "production",
};

const extensionConfig = {
    ...baseConfig,
    platform: "node",
    mainFields: ["module", "main"],
    format: "cjs",
    entryPoints: ["./src/extension.ts"],
    outfile: "./out/extension.js",
    external: ["vscode"],
};

const watchConfig = {
  watch: {
    onRebuild(error, result) {
    console.log("[watch] build started");
    if (error) {
      error.errors.forEach(error =>
      console.error(`> ${error.location.file}:${error.location.line}:${error.location.column}: error: ${error.text}`)
      );
    } else {
      console.log("[watch] build finished");
    }
    },
  },
};


const dataflowWebviewConfig = {
  ...baseConfig,
  target: "es2020",
  format: "esm",
  entryPoints: ["./src/webview/dataflowScript.ts"],
  outfile: "./out/dataflowScript.js",
};


(async () => {
  const args = process.argv.slice(2);
  try {
    if (args.includes("--watch")) {
      console.log("[watch] build started");
      await build({...extensionConfig, ...watchConfig,});
      await build({...dataflowWebviewConfig, ...watchConfig,});
      console.log("[watch] build finished");
    } else {
      await build(extensionConfig);
      await build(dataflowWebviewConfig);
      console.log("build complete");
    }
  } catch (err) {
    process.stderr.write(err.stderr);
    process.exit(1);
  }
})();
