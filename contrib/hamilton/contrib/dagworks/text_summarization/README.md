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

# Purpose of this module

This module implements a universal dataflow to summarize text hitting the model of your choice (OpenAI, Cohere, etc).
By default it will hit an OpenAI endpoint, but you can configure it to hit any endpoint you want, by passing
in the model name `inputs={"llm_name": ...}` for the model you want to hit as part of the execution input.

You can pass in PDFs, or just plain text and it will get chunked and summarized by the model chosen.

# Configuration Options
This module can be configured with the following options:
 - {"file_type":  "pdf"} to read PDFs.
 - {"file_type":  "text"} to read a text file.
 - {} to have `raw_text` be passed in.

# Limitations

You need to include the respective LLM provider's API_KEY in your environment.
e.g. OPENAI_API_KEY for openai, COHERE_API_KEY for cohere, etc. and should be
accessible from your code by doing `os.environ["OPENAI_API_KEY"]`, `os.environ["COHERE_API_KEY"]`, etc.

The code does not check the context length, so it may fail if the context passed is too long.
