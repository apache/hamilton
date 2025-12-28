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

---
title: Slack
description: dlt source for Slack API
keywords: [slack api, slack source, slack]
---


# Slack

[Slack](https://slack.com/) a messaging app for business that connects people to the information
they need.

Resources that can be loaded using this verified source are:

| Name             | Description                                                                                                                   |
| ---------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| conversations    | list the available conversations using the [conversations.list](https://api.slack.com/methods/conversations.list) endpoint.   |
| history          | get the conversation history using the [conversations.history](https://api.slack.com/methods/conversations.history) endpoint. |
| access_logs      | get the team logs for the channel using [team.accessLogs](https://api.slack.com/methods/team.accessLogs) endpoint.            |


## Initialize the pipeline

```bash
dlt init slack duckdb
```

Here, we chose duckdb as the destination. Alternatively, you can also choose redshift, bigquery, or
any of the other [destinations](https://dlthub.com/docs/dlt-ecosystem/destinations/).

## Add credentials

1. Get your Slack access token. The process is detailed in the [docs](https://api.slack.com/authentication).
   You need to give the right scopes to the token.
2. Open `.dlt/secrets.toml`.
3. Enter the API access token:

   ```toml
   [sources.slack]
   access_token="xoxp-*************-*************-*************-********************************"
    ```

4. Follow the instructions in the
   [destinations](https://dlthub.com/docs/dlt-ecosystem/destinations/) document to add credentials
   for your chosen destination.


## Run the pipeline

1. Install the necessary dependencies by running the following command:

   ```bash
   pip install -r requirements.txt
   ```

2. Now the pipeline can be run by using the command:

   ```bash
   python3 slack_pipeline.py
   ```

3. To make sure that everything is loaded as expected, use the command:

   ```bash
   dlt pipeline slack_pipeline show
   ```

## How to use

The slack source supports loading data from access_logs, conversations and history resources.

As access_logs is just available on paid accounts it needs to be manually enabled in the pipeline, as shown below.

```python
source = slack_source()
source.access_logs.selected = True
```

The conversations resource can be used to load the list of available conversations and will allways bring all
the available conversations.

The history resource can be used to load the history of a conversation. By default all the conversations will be
selected, but you can select only the ones you want using the `selected_channels` attribute.

```python

source = slack_source(selected_channels=["welcome", "general"])
```


💡 To explore additional customizations for this pipeline, we recommend referring to the official
`dlt` Chess documentation. It provides comprehensive information and guidance on how to further
customize and tailor the pipeline to suit your specific needs. You can find the `dlt` Chess
documentation in
[Setup Guide: Slack.](https://dlthub.com/docs/dlt-ecosystem/verified-sources/slack)
