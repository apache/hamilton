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
This module provides a simple dataflow to generate an image using openAI DallE generation capabilities.

# Configuration Options
This module can be configured with the following options:
[list options]

- `base_prompt` -- prompt to generate from a string
- `style` -- string for the style of the image to generate, defaults to "realist"
- `size` -- string for the size of the image to generate, defaults to "1024x1024"
- `hd` -- Whether to use high definition, defaults to False

# Limitations

Pretty simple -- only exposes the above parameters.
