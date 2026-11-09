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

const assert = require("assert").strict;
const fs = require("fs");
const Module = require("module");
const path = require("path");
const { transformSync } = require("esbuild");

const sourcePath = path.resolve(__dirname, "../src/pythonExecution.ts");
const source = fs.readFileSync(sourcePath, "utf8");
const { code } = transformSync(source, { loader: "ts", format: "cjs", target: "node16" });
const compiledModule = new Module(sourcePath, module);
compiledModule.filename = sourcePath;
compiledModule.paths = Module._nodeModulePaths(path.dirname(sourcePath));
compiledModule._compile(code, sourcePath);

const { buildPythonInvocation, checkPythonDependencies, installPythonDependency } = compiledModule.exports;

describe("Python interpreter command handling", () => {
  it("keeps executable paths with spaces separate from interpreter arguments", () => {
    const command = ["C:\\task fixture\\python.exe", "-I"];

    assert.deepEqual(buildPythonInvocation(command, ["-c", "import hamilton_lsp"]), {
      executable: "C:\\task fixture\\python.exe",
      args: ["-I", "-c", "import hamilton_lsp"],
    });
  });

  it("checks Hamilton LSP with the executable and arguments passed separately", () => {
    const calls = [];
    const command = ["C:\\task fixture\\python.exe", "-I"];

    assert.equal(
      checkPythonDependencies(command, (executable, args) => calls.push({ executable, args })),
      true,
    );
    assert.deepEqual(calls, [
      {
        executable: "C:\\task fixture\\python.exe",
        args: ["-I", "-c", "import hamilton_lsp"],
      },
    ]);
  });

  it("does not execute when there is no selected interpreter", () => {
    let called = false;

    assert.equal(
      checkPythonDependencies(undefined, () => {
        called = true;
      }),
      false,
    );
    assert.equal(called, false);
  });

  it("installs the LSP through the selected interpreter without shell parsing", () => {
    const calls = [];
    const command = ["C:\\task fixture\\python.exe", "-I"];

    assert.equal(
      installPythonDependency(command, (executable, args) => calls.push({ executable, args })),
      true,
    );
    assert.deepEqual(calls, [
      {
        executable: "C:\\task fixture\\python.exe",
        args: ["-I", "-m", "pip", "install", "apache-hamilton-lsp"],
      },
    ]);
  });

  it("reports a missing dependency when interpreter execution fails", () => {
    assert.equal(
      checkPythonDependencies(["C:\\task fixture\\python.exe"], () => {
        throw new Error("synthetic interpreter failure");
      }),
      false,
    );
  });
});
