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
import { DataflowWebviewFeature } from "./features/dataflowWebviewFeature";
import { LSPClientFeature } from "./features/lspClientFeature";
import { SupportLinksFeature } from "./features/supportLinksFeature";
import { checkPythonDependencies, installPythonDependency } from "./pythonExecution";
import type { PythonExecCommand } from "./pythonExecution";

function installDependenciesMessage(pythonCommand: readonly string[]) {
  const installLSP = "Install apache-hamilton[lsp]";

  vscode.window.showInformationMessage("Missing the Hamilton language server.", installLSP).then((selection) => {
    if (selection === installLSP) {
      installPythonDependency(pythonCommand);
      vscode.commands.executeCommand("workbench.action.reloadWindow");
    }
  });
}

let extensionFeatures: vscode.Disposable[] = [];

export async function activate(context: vscode.ExtensionContext) {
  const pythonExtension = vscode.extensions.getExtension("ms-python.python");
  const pythonCommand: PythonExecCommand = pythonExtension?.exports?.settings?.getExecutionDetails?.()?.execCommand;
  if (!pythonCommand?.length) {
    vscode.window.showInformationMessage("Select a Python interpreter to activate the Hamilton language server.");
    return;
  }

  const available = checkPythonDependencies(pythonCommand);
  if (available === false) {
    installDependenciesMessage(pythonCommand);
    return;
  }

  extensionFeatures = [
    new LSPClientFeature(context, pythonCommand),
    new DataflowWebviewFeature(context),
    new SupportLinksFeature(),
  ];
}

export function deactivate() {
  extensionFeatures.forEach((feature) => feature.dispose());
}
