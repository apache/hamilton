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
import { getNonce, getUri } from "../utilities";

class DataflowWebviewProvider implements vscode.WebviewViewProvider {
  public static readonly viewId = "hamilton.dataflowWebview";
  private readonly _extensionUri: vscode.Uri;
  public _view?: vscode.WebviewView;

  constructor(context: vscode.ExtensionContext) {
    this._extensionUri = context.extensionUri;
  }

  public resolveWebviewView(
    webviewView: vscode.WebviewView,
    context: vscode.WebviewViewResolveContext,
    _token: vscode.CancellationToken,
  ): void | Thenable<void> {
    this._view = webviewView;

    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [this._extensionUri],
    };

    webviewView.onDidChangeVisibility(() => {
      vscode.commands.executeCommand("lsp-view-request", {});
    });

    webviewView.webview.html = this._getWebviewContent(webviewView.webview, this._extensionUri);
  }

  public postMessage(message: any) {
    if (this._view?.webview) {
      this._view?.webview.postMessage(message);
    }
  }

  public _getWebviewContent(webview: vscode.Webview, extensionUri: vscode.Uri) {
    const scriptUri = getUri(webview, extensionUri, ["out", "dataflowScript.js"]);

    const nonce = getNonce();
    return (
      /*html*/
      `
      <!DOCTYPE html>
      <meta charset="utf-8">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Hamilton: Dataflow Viewer</title>
        <style>
            #dataflow {
              width: 100%;
              height: 100%;
              position: absolute;
              top: 0px;
              left: 0px;
            }
        </style>
      </head>
      <body>
        <div id="dataflow"/>
        <script type="module" nonce="${nonce}" src="${scriptUri}"></script>
      </body>
      </html>
      `
    );
  }
}

export class DataflowWebviewFeature implements vscode.Disposable {
  private dataflowWebviewProvider: DataflowWebviewProvider;

  constructor(context: vscode.ExtensionContext) {
    this.dataflowWebviewProvider = new DataflowWebviewProvider(context);

    context.subscriptions.push(
      vscode.window.registerWebviewViewProvider(DataflowWebviewProvider.viewId, this.dataflowWebviewProvider),
      vscode.commands.registerCommand("hamilton.dataflowWebview.update", (response) => {
        this.dataflowWebviewProvider.postMessage({ command: "update", details: response });
      }),
      vscode.commands.registerCommand("hamilton.dataflowWebview.rotate", () => {
        vscode.commands.executeCommand("lsp-view-request", { rotate: true });
      }),
    );
  }

  public dispose(): any {
    return undefined;
  }
}
