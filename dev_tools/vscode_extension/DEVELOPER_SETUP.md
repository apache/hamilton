<!--
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.
-->

# Developer setup

## Development
Install the dependencies with

```sh
npm install
```

Edit the extension code and compile it

```sh
npm run compile
```

Alternatively, set it to auto rebuild on code changes with

```sh
npm run watch
```

Try the extension by pressing `F5` in VSCode. This will execute `npm run compile` and launch a temporary VSCode instance with the extension installed.

If you're using `npm run watch`, you use `CTRL+R` from the temporary VSCode instance to reload the extension, picking up the latest changes

## Release

The steps are detailed on the [official VSCode page](https://code.visualstudio.com/api/working-with-extensions/publishing-extension).

### Requirements
1. Install the `vsce` package using

    ```sh
    npm install -g @vscode/vsce
    ```

2. [Create a publisher account](https://code.visualstudio.com/api/working-with-extensions/publishing-extension#create-a-publisher) for the VSCode Marketplace


### Manual publishing
1. Increment the `version` field in `package.json`. You can't publish to the Azure marketplace otherwise
2. Compile the TypeScript extension into JavaScript files. They can be found under `out/`

    ```sh
    npm run compile
    ```

3. Package the VSCode extension. This will bundle the code under `out/` and the `resources/` directory into a `.vsix` file.

    ```sh
    vsce package
    ```

4. (Optional) From the VSCode interface, you can right-click the `.vsix` file and select `Install Extension VSIX` to install and test it locally, outside the development environment.

5. Go to the [VSCode Marketplace](https://marketplace.visualstudio.com/vscode) and select `Publish extension`.

6. Upload the `.vsix` file and enter the required metadata. It should take ~5-10 mins for the marketplace to scan the files and make it publicly available.



### Programmatic publishing
1. Register your VSCode Marketplace access token

    ```sh
    vsce login
    ```

2. [Autoincrement releases](https://code.visualstudio.com/api/working-with-extensions/publishing-extension#autoincrement-the-extension-version) and publish the extension.

    ```sh
    vsce publish [major|minor|patch] -p ACCESS_TOKEN
    ```
