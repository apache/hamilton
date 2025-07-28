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

import * as vscode from "vscode";
import { execSync } from "child_process";
import { DataflowWebviewFeature } from "./features/dataflowWebviewFeature";
import { LSPClientFeature } from "./features/lspClientFeature";
import { SupportLinksFeature } from "./features/supportLinksFeature";


const checkPythonDependencies = (pythonPath: string) => {
  try{
    execSync(`${pythonPath} -c "import hamilton_lsp"`)
    return true
  } catch (error) {
    return false
  }
}

function installDependenciesMessage(pythonPath: string) {
  let installLSP = "Install sf-hamilton[lsp]"

  vscode.window.showInformationMessage("Missing the Hamilton language server.", installLSP)
    .then(selection => {
      if (selection === installLSP) {
        execSync(`${pythonPath} -m pip install 'sf-hamilton-lsp'`)
        vscode.commands.executeCommand("workbench.action.reloadWindow")
      }
    })
}



let extensionFeatures: any[];

export async function activate(context: vscode.ExtensionContext) {
  const pythonExtension = vscode.extensions.getExtension("ms-python.python");
  const pythonPath = pythonExtension?.exports.settings.getExecutionDetails().execCommand?.join("");

  const available = checkPythonDependencies(pythonPath)
  if (available === false) {
    installDependenciesMessage(pythonPath)
    return
  }

  extensionFeatures = [
    new LSPClientFeature(context, pythonPath),
    new DataflowWebviewFeature(context),
    new SupportLinksFeature()
  ];
}

export function deactivate() {
  extensionFeatures.forEach((feature) => feature.dispose());
}
